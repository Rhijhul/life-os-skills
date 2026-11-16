# Changelog

Newest first. One entry per release: date, version, what changed.

## Personal Finance Dashboard v1.4 · 17-Nov-2026

- **Bills:** next month's card bills show under this month as soon as their statements arrive, with a Paid tick for paying early and reminders 3 days before each due date, across the month change.
- **Month picker:** the next month appears as "<Mon> · next" once its first bill is in (trial); the page still opens on the current month, and empty sections say when they start.
- **Overview:** Needs attention moved to the top of To-do, with a count badge on the To-do link, so the Overview is shorter.
- **Wealth:** "Where the money is" bar is interactive (hover/tap readout, card highlight, click to card); the Cash group has its own accent colour.
- **Layout:** sidebar spacing scales with window height so it never scrolls; action chips and labels stay on one line; GoldBEES row matches the stocks.
- **Docs:** SOP for the next-month bills, upcoming month, Needs attention placement, sidebar spacing and the interactive bar.

## Personal Finance Dashboard v1.3 · 17-Nov-2026

- **Savings accounts (new):** one slim card per bank with a click-to-edit balance and what it must hold (salary floor, petty cash, emergency fund, next EMI, a deposit held for someone, or nothing); Total / Earmarked / Available tiles and a share bar. New collection `bank/*`.
- **Overview:** first card is now "Spare cash": free money per account and a "Move ₹X to <salary account>" line; Needs attention pills (bills due, accounts short, low floor, stale balances, expiring points, renewals, review due, tax refund pending); Net worth tile; shorter tile text.
- **Net worth (new section):** financial assets + home − loans in a 50:50 card, interactive rows (hover detail, click through to Investments / Loans), editable home value, net worth by month columns with values. Savings balances now feed the emergency fund and a new "Other bank cash" line in the Cash class.
- **Tax (new):** tax-year estimate under the new regime (2026-27 slabs, 87A rebate, cess), capital-gains set-off and LTCG exemption meter, TDS by month, past returns, losses carried forward, refund alert. New collection `tax/fy*`.
- **Retirement:** "Today vs plan" on one concise line; tracked corpus chart on a real time axis.
- **Optional yearly charge** (e.g. a bank locker fee) held in the EMI account in season, with Bills ticks (`settings.sbi_locker`).
- **Docs and scripts:** SOP schema 2.15–2.16 and views 4.16–4.17, onboarding and monthly steps for balances and tax; SKILL rules 10–11; `validate_data.py` checks `bank` and `tax`.

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
