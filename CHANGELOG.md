# Changelog

Newest first. One entry per release: date, version, what changed.

## Personal Finance Dashboard v1.2 · 16-Nov-2026

- **Cards → Rewards:** points wallet with ₹ per point for each redemption route, one row per points account, editable balances, a "Record a redemption" form (vouchers, transfers to partners, statement credit), expiry list, which-card-for-which-spend, points by statement and cashback by statement. New collection `rewards/main`.
- **Insurance:** Combined view works with any insurer (uses the first term and health policy that have a history).
- **Fixes:** Retirement panel no longer scrolls sideways on phones; card colours and names fall back cleanly for any card id; the term cover tile names the insurer from the data.
- **Docs:** SOP schema 2.14 (`rewards/main`), Rewards view, monthly rewards step, onboarding question for points; SKILL rule "one row per points account".

## Personal Finance Dashboard v1.1 · 15-Nov-2026

- **Performance vs benchmark** for mutual funds and US stocks: 3M / 6M / 12M / Since bought, one row per holding against its own index; "since bought" puts the same buys into the index on the same dates.
- **Retirement at 60:** chart fills the panel; half-yearly check (every May and Nov) with saved plan line, actual dots, beat/miss columns and a review table (`invest/planreview`); tighter layout; settings open independently.
- **Mutual funds:** Equity vs debt donut under By category.
- **Bills:** monthly insurance premium gets a tick; any overdue item flips the month status.
- **Insurance:** Combined premiums view; card details collapsed; financial-year premium history.
- **Money moments:** donuts replaced by split bars; every card opens its section.
- **Layout:** Light / Dark switch (Light default), PPF & NPS bars always visible, dotted separators between stacked charts, holdings by account expanded.
- **Docs:** SOP and SKILL rules for per-fund benchmarks and short notes; refresh steps for the new fields.

## Personal Finance Dashboard v1.0 · 14-Nov-2026

- First public release.
