#!/usr/bin/env python3
"""freelance-gig-scout: score freelance gigs against your profile, offline.

Pattern source (pattern only, original code): career-ops-hq/career-ops --
scan postings, score each 1-5 against a profile, return a ranked shortlist.
Here the profile is a freelancer's skill set + budget floor + exclusions,
and the postings are gigs from any marketplace (Karlancer, Ponisha, ...).

Scoring (max 5.0):
  skill match   up to 2.0  (fraction of profile skills present, x2)
  budget fit    up to 1.5  (0 below floor, scaled up to target, full above)
  recency       up to 0.5  (fresh postings first)
  clarity       up to 1.0  (0.5 description + 0.5 stated budget)
Exclusion rule: any excluded keyword (EN/FA) in title/description
  -> score 0.0 and the gig is flagged, never ranked. This is the guardrail
  for work the freelancer refuses (fake reviews, scraping, in-person, ...).

Usage:
  python3 gig_scout.py --gigs gigs.json --profile profile.json [--top 5]
  python3 gig_scout.py --gigs gigs.json --profile profile.json --format md
  python3 gig_scout.py --demo            # score the bundled examples

Input files are plain JSON; see gigs.example.json / profile.example.json.
No network, no keys, no dependencies beyond the Python standard library.
"""

import argparse
import json
import re
import sys

# Default exclusions: work categories the user refuses. Extend via profile.
DEFAULT_EXCLUDED = [
    "fake review", "fake reviews", "نظرات جعلی", "نظرات فیک",
    "spam", "اسپم", "scraping", "اسکرپ", "divar scraping", "دیوار",
    "in-person", "حضوری", "on-site", "door-to-door",
]

_WORD = re.compile(r"[\w\u0600-\u06FF]+")


def _words(text):
    """Lower-cased word tokens, Persian + Latin alike."""
    return set(_WORD.findall((text or "").lower()))


def _norm(text):
    return (text or "").lower()


def score_gig(gig, profile):
    """Return (score, reasons) for one gig dict against one profile dict."""
    title = gig.get("title", "")
    desc = gig.get("description", "")
    blob = _norm(title + " " + desc)
    reasons = []

    # Exclusion guardrail: refused work never ranks, whatever it scores.
    excluded = list(profile.get("excluded_keywords", [])) or DEFAULT_EXCLUDED
    for kw in excluded:
        if kw and _norm(kw) in blob:
            return 0.0, ["excluded: matches refused keyword %r" % kw]

    skills = [s.lower() for s in profile.get("skills", [])]
    gig_words = _words(title) | _words(desc)
    gig_skills = set(gig.get("skills", []))
    gig_skills = {s.lower() for s in gig_skills}
    matched = [s for s in skills if s in gig_words or s in gig_skills]
    skill_score = 2.0 * (len(matched) / len(skills)) if skills else 0.0
    reasons.append("skills %d/%d matched: %s"
                   % (len(matched), len(skills), ", ".join(matched) or "-"))

    budget = gig.get("budget")
    floor = profile.get("min_budget", 0) or 0
    target = profile.get("target_budget", floor) or floor
    if budget is None:
        budget_score = 0.0
        reasons.append("no stated budget")
    elif budget < floor:
        budget_score = 0.0
        reasons.append("budget %s below floor %s" % (budget, floor))
    elif target > floor and budget < target:
        budget_score = 1.5 * (budget - floor) / (target - floor)
        reasons.append("budget %s between floor and target" % budget)
    else:
        budget_score = 1.5
        reasons.append("budget %s meets target" % budget)

    days = gig.get("posted_days_ago")
    if days is None:
        recency = 0.0
    elif days <= 3:
        recency = 0.5
    elif days <= 7:
        recency = 0.3
    elif days <= 14:
        recency = 0.15
    else:
        recency = 0.0
    reasons.append("posted %s days ago" % days)

    clarity = (0.5 if len(desc.strip()) >= 50 else 0.0) \
        + (0.5 if budget is not None else 0.0)

    total = round(min(5.0, skill_score + budget_score + recency + clarity), 1)
    return total, reasons


def rank_gigs(gigs, profile, top=None):
    """Score every gig, drop excluded ones to the bottom, sort desc."""
    scored = []
    for gig in gigs:
        score, reasons = score_gig(gig, profile)
        scored.append({"gig": gig, "score": score, "reasons": reasons})
    scored.sort(key=lambda r: (-r["score"], r["gig"].get("title", "")))
    return scored[:top] if top else scored


def render_table(ranked):
    lines = ["#  score  platform  title",
             "--  -----  --------  -----"]
    for i, item in enumerate(ranked, 1):
        gig = item["gig"]
        lines.append("%d.  %.1f  %s  %s"
                     % (i, item["score"],
                        gig.get("platform", "-"), gig.get("title", "-")))
    return "\n".join(lines)


def render_md(ranked):
    lines = ["# Gig shortlist", "",
             "| # | Score | Platform | Title | Why |",
             "|---|-------|----------|-------|-----|"]
    for i, item in enumerate(ranked, 1):
        gig = item["gig"]
        lines.append("| %d | %.1f | %s | %s | %s |"
                     % (i, item["score"], gig.get("platform", "-"),
                        gig.get("title", "-"), "; ".join(item["reasons"])))
    return "\n".join(lines)


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Score freelance gigs vs profile")
    ap.add_argument("--gigs", help="JSON list of gigs")
    ap.add_argument("--profile", help="JSON freelancer profile")
    ap.add_argument("--top", type=int, default=0, help="keep only top N")
    ap.add_argument("--format", choices=["table", "md", "json"],
                    default="table")
    ap.add_argument("--demo", action="store_true",
                    help="score the bundled example files")
    args = ap.parse_args(argv)

    if args.demo:
        import os
        here = os.path.dirname(os.path.abspath(__file__))
        gigs = _load(os.path.join(here, "gigs.example.json"))
        profile = _load(os.path.join(here, "profile.example.json"))
    else:
        if not args.gigs or not args.profile:
            ap.error("--gigs and --profile are required (or use --demo)")
        gigs = _load(args.gigs)
        profile = _load(args.profile)

    ranked = rank_gigs(gigs, profile, top=args.top or None)
    if args.format == "json":
        print(json.dumps(ranked, ensure_ascii=False, indent=2))
    elif args.format == "md":
        print(render_md(ranked))
    else:
        print(render_table(ranked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
