---
name: personal-finance-dashboard
description: Build and maintain an interactive Indian personal-finance dashboard (cards, spending, investments, retirement, loans, insurance) from a proven HTML template. Use when someone wants their own money dashboard, or a weekly or monthly refresh of one.
---

# Personal Finance Dashboard

This skill builds a personal-finance dashboard for one person, using their own data. It is one self-contained HTML page with a small database behind it. Every visual, chart and interaction comes from a tested template.

What the finished page covers:
- monthly cash flow and spare cash across your bank accounts (what each must hold, what to move)
- savings accounts, net worth (assets + home − loans) and a tax-year estimate
- card spending
- investments (Indian stocks, mutual funds, US stocks, EPF, PPF, NPS)
- a retirement-at-60 projection
- goals, bills, loans, insurance and to-dos
- card rewards: points wallet, redemptions, expiry and cashback

It also includes:
- each fund and US stock against its own benchmark (3M / 6M / 12M / since bought);
- a half-yearly retirement review that plots actual corpus against the saved plan;
- a privacy toggle that hides salary and investment figures;
- a Light / Dark switch (Light by default);
- a "Download offline copy" button.

The skill works with any agent that can read files and run Python. Hosting the page with a database is best (for example, a claude.ai artifact with the `db` capability). Without hosting, the skill produces a single offline HTML file instead.

## Files in this skill

| Path | What it is | When to read |
|---|---|---|
| `assets/sample-dashboard.html` | The finished dashboard with a sample profile. Open it in a browser to see every section. | First, to understand the goal |
| `assets/dashboard.core.html` | The template source: all markup, CSS and JS. No data inside. | When building or changing the page |
| `assets/sample-data.json` | The sample database, one key per collection. A worked example of every record shape. | When creating records |
| `references/sop-and-spec.md` | Full blueprint: architecture, schema, design tokens, every component and formula, refresh routine, onboarding interview. | Before building; keep it open |
| `references/connectors.md` | Data sources and optional connectors (MCP) per module, with fallbacks. | Before the interview |
| `scripts/build.py` | Sets the owner's name, embeds the page's own source for offline download, writes the publishable page. | Build step |
| `scripts/make_offline.py` | Embeds a dataset into a standalone offline HTML file. | No hosting, or a frozen copy to share |
| `scripts/validate_data.py` | Checks a dataset: required records, totals that must reconcile, card-year transaction records. | Before every seed or refresh |

## Non-negotiable rules

1. **The template is the source of truth.**
   - Keep the design and behaviour identical.
   - Change only the owner's name and the data.
   - Do not redesign, simplify or drop sections.
2. **Never put a person's data into the HTML source.**
   - Data goes into the database: one JSON object per collection and document.
   - Monthly updates write records only and never regenerate the page.
3. **Never ship real data in this skill or in shared files.**
   - This package contains only the sample profile.
   - When someone shares their dashboard or improves this skill, their database must not go into the package.
4. **Never invent numbers.**
   - Every figure comes from the user, a document they gave, a cited lookup, or a calculation on those.
   - Unknown values are `null` (the page shows "—"). List them as pending.
5. **Card transactions are stored one record per card per card-year from day one.**
   - Record id: `ccspend/tx-<card>-<YYYY>`, where YYYY is the year of the April that starts it.
   - The home loan's id is always `home`.
   - Each fund record carries `bucket`: `equity` | `mixed` | `debt` | `us`.
6. **Ask before anything irreversible**, and before changing targets or decisions the user set.
7. **Benchmarks are per fund.**
   - Compare every fund with its own official index, never a category average.
   - If an index has no data, rebuild it from component prices or use a labelled proxy, and say "approximate" in one line.
8. **Keep notes short.** Notes under charts are one or two lines; analyst notes are at most 8 one-line bullets.
9. **One row per points account.** Cards that earn into one rewards balance share one wallet row in `rewards/main`.
10. **Every bank account says what it must hold.** Each `bank/<id>` record has a `need` (floor, float, target, emi, hold or none); spare cash is everything above it. The emergency-fund account is never counted as spare.
11. **Tax is a tracker, not advice.** Build `tax/fy<YYYY-YY>` only from the user's payslip, AIS/TIS, capital-gains reports and filed returns; leave unknowns `null` and list them in `todo`.

## Workflow

### 1. Understand

- Open `assets/sample-dashboard.html` (or read it) and `references/sop-and-spec.md`.
- Tell the user in five lines or fewer what will be built, and which modules need data they may not have.

### 2. Interview in stages

Follow `references/sop-and-spec.md` section 6. The stages are:
1. Setup
2. Cards
3. Investments
4. Salary, savings accounts, tax, cash and loans
5. Insurance

How to run each stage:
- **[ASK]** items: ask the user.
- **[DOC]** items: request the document.
- **[LOOKUP]** and **[CALC]** items: do them yourself. Check `references/connectors.md` for connectors that can fetch data directly.
- Ask at most about eight short questions per message.
- End each stage with a summary table and wait for confirmation.

### 3. Create the records

- Build one JSON file shaped like `assets/sample-data.json`: `{collection: {docId: {...}}}`.
- Use the exact keys in SOP section 2 and the formulas in section 4: weights excluding GoldBEES, P&L, snapshot totals, card month totals, loan progress, XIRR cash flows.
- Run `python3 scripts/validate_data.py my-data.json`. Fix every ERROR. Explain any warning you leave.

### 4. Build and publish

```bash
python3 scripts/build.py --name "<FirstName>" --core-out my.core.html --out dashboard.html
node --check dashboard.check.js        # syntax check, if Node is available
```

**With page hosting and a database** (e.g. a claude.ai artifact):
1. Publish `dashboard.html`. Declare the capabilities `db`, `downloads` and `user`, plus the optional Notion connector, as in SOP section 1.3.
2. Seed the database from `my-data.json` in batches.
3. Keep `my.core.html`: it is what you edit and rebuild later.

**Without hosting:**
```bash
python3 scripts/make_offline.py --page dashboard.html --data my-data.json --out "<Name>-Personal-Finance.html" --title "<Name>'s Personal Finance"
```

### 5. Verify

Run the checklist in SOP section 7:
- no errors, and every section renders;
- the offline download behaves the same;
- no horizontal scroll at 400px;
- light and dark mode are both readable;
- the eye toggle hides salary and investment figures but not card spending or bills;
- totals reconcile across Overview, Net worth, Savings and Investments.

### 6. Set up the routine

Follow SOP section 5:
- weekly portfolio refresh;
- monthly cash-flow update with the documents list (including each bank balance and the payslip for Tax);
- yearly rollovers.

Every refresh writes only changed records, pinned to the version it read, in one batch. It updates `settings/main.last_updated` and never republishes the page. If the platform supports scheduled tasks, create the weekly one.

Every May and November, remind the user to record the half-yearly retirement review on the page. A refresh never writes `invest/planreview`.

## Changing the design (optional)

If the user asks for a design change:
1. Edit `my.core.html`.
2. Rebuild with `build.py`.
3. Test that the online page and the offline copy behave the same.
4. Republish to the same address, so the link and data are kept.

Never mutate loaded data objects in code; build copies, because hosted data can arrive frozen. Keep each render function wrapped in try/catch.
