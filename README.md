# freelance-gig-scout

Score freelance gigs against your profile and get a ranked shortlist — offline, stdlib-only, no API keys.

Pattern (pattern only, original code): scan → score 1–5 against a profile → ranked shortlist, as popularized by job-search agents. Here the profile is a freelancer's skills + budget floor + refused-work keywords, and the postings are gigs from any marketplace (Karlancer, Ponisha, …).

## Scoring (max 5.0)

| Component | Points | Rule |
|---|---|---|
| Skill match | 2.0 | share of profile skills found in the gig |
| Budget fit | 1.5 | 0 below floor, scaled to target, full above target |
| Recency | 0.5 | ≤3d full, ≤7d 0.3, ≤14d 0.15 |
| Clarity | 1.0 | 0.5 description + 0.5 stated budget |

**Exclusion guardrail:** any refused keyword (EN/FA: fake reviews, spam, scraping, in-person work, …) in the title/description scores the gig **0** and drops it to the bottom — refused work never ranks, whatever it pays.

## Usage

```bash
python3 gig_scout.py --demo
python3 gig_scout.py --gigs gigs.json --profile profile.json --top 5
python3 gig_scout.py --gigs gigs.json --profile profile.json --format md
```

See `gigs.example.json` / `profile.example.json` for the input format. No network, no keys (see `.env.example`), no dependencies.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

---

# freelance-gig-scout (فارسی)

ابزار امتیازدهی به پروژه‌های فریلنسری بر اساس پروفایل شما — آفلاین، فقط با کتابخانه استاندارد پایتون، بدون نیاز به کلید API.

**الگو:** اسکن آگهی‌ها ← امتیاز ۱ تا ۵ بر اساس پروفایل ← فهرست رتبه‌بندی‌شده.

**قانون مهم:** هر آگهی که شامل کلمات کاریِ مردود باشد (نظرات جعلی، اسپم، اسکرپ، کار حضوری و…) امتیاز **صفر** می‌گیرد و به انتهای فهرست می‌رود — هرچقدر هم که پولش خوب باشد.

## اجرا

```bash
python3 gig_scout.py --demo
python3 gig_scout.py --gigs gigs.json --profile profile.json --top 5
```

## تست

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT — see `LICENSE`.
