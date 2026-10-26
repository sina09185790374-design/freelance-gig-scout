"""Tests for gig_scout.py — run: python3 -m unittest discover -s tests -v"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gig_scout import rank_gigs, score_gig  # noqa: E402

PROFILE = {
    "skills": ["instagram", "telegram", "python"],
    "min_budget": 5000000,
    "target_budget": 20000000,
    "excluded_keywords": ["fake review", "نظرات جعلی", "spam"],
}


def gig(**kw):
    base = {"title": "Bot", "platform": "Ponisha", "description": "x" * 60,
            "posted_days_ago": 2}
    base.update(kw)
    return base


class TestScoring(unittest.TestCase):
    def test_perfect_gig_scores_five(self):
        score, _ = score_gig(
            gig(title="Telegram python bot", skills=["telegram", "python",
                                                     "instagram"],
                budget=25000000), PROFILE)
        self.assertEqual(score, 5.0)

    def test_excluded_keyword_scores_zero_english(self):
        score, reasons = score_gig(
            gig(title="Fake review job", budget=99999999), PROFILE)
        self.assertEqual(score, 0.0)
        self.assertIn("excluded", reasons[0])

    def test_excluded_keyword_scores_zero_persian(self):
        score, _ = score_gig(
            gig(title="ثبت نظرات جعلی", budget=99999999), PROFILE)
        self.assertEqual(score, 0.0)

    def test_budget_below_floor_loses_budget_points(self):
        score, _ = score_gig(
            gig(title="Telegram python bot", skills=["telegram", "python",
                                                     "instagram"],
                budget=1000000), PROFILE)
        self.assertLess(score, 5.0)
        self.assertGreaterEqual(score, 2.5)  # skills + recency + clarity stay

    def test_no_skills_no_skill_points(self):
        score, _ = score_gig(gig(budget=25000000), {**PROFILE, "skills": []})
        self.assertLessEqual(score, 3.0)

    def test_ranking_puts_best_first_and_excluded_last(self):
        ranked = rank_gigs([
            gig(title="Fake review job", budget=99999999),
            gig(title="Telegram python bot",
                skills=["telegram", "python", "instagram"],
                budget=25000000),
            gig(title="Old small job", budget=6000000, posted_days_ago=30),
        ], PROFILE)
        self.assertEqual(ranked[0]["score"], 5.0)
        self.assertEqual(ranked[-1]["score"], 0.0)

    def test_top_limits_results(self):
        ranked = rank_gigs([gig(title="A"), gig(title="B")], PROFILE, top=1)
        self.assertEqual(len(ranked), 1)


if __name__ == "__main__":
    unittest.main()
