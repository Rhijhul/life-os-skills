# Personal Finance Dashboard — SOP and Technical Specification

Companion to `assets/sample-dashboard.html` (source: `assets/dashboard.core.html`, data: `assets/sample-data.json`), which shows the dashboard filled with a sample profile. Where this document gives a value, it is either a design constant of the code or a sample value; replace sample values with your own during onboarding.

**Ground rule for any LLM using this document:** the template HTML is the source of truth for code. When this document and the code disagree, follow the code and note the difference.

---

## 1. System and database architecture

### 1.1 The three layers

| Layer | What it is | Where it lives | Changes how often |
|---|---|---|---|
| UI layer | One self-contained HTML file: markup, CSS and JavaScript inline. No build step, no framework. | Published as a claude.ai artifact (or opened as a local file) | Only when the design changes |
| Data layer | A document database: collections of JSON documents ("records"). | The artifact's built-in database (`db` capability) on claude.ai; or `window.__SNAPSHOT__` inside an offline file | Every refresh |
| Record of truth (optional) | Notion pages (holdings, funds, insurance, decisions) | Notion | Weekly |

The page never contains hard-coded personal figures. It reads everything from the database at load time. A monthly or weekly update therefore writes only the changed records; the HTML is never regenerated for a data update.

### 1.2 How the page loads data

1. On load the script checks `window.__SNAPSHOT__`.
   - **Present (offline file or the template):** each collection is read from it (`S[c] = window.__SNAPSHOT__[c] || {}`), the body gets class `offline`, and the page renders once. Write actions are disabled, except a few browser-only conveniences kept in `localStorage` (income edits, home value, bill/EMI/benefit ticks, to-do ticks, view preferences).
   - **Absent (published on claude.ai):** the script calls `await window.claude.use('db')`. For each collection in `COLLS` it subscribes with `db.collection(name).onSnapshot(cb)`; each snapshot replaces `S[name]` with `{ [doc.id]: doc.data() }`. Rendering is batched with `requestAnimationFrame` and re-runs whenever any collection updates.
2. The collection list is fixed in code:
   ```js
   const COLLS = ['months', 'targets', 'cards', 'actions', 'mf', 'corpus', 'trend', 'loans', 'settings', 'ppf', 'nps', 'invest', 'perks', 'ccspend', 'insurance', 'rewards', 'bank', 'tax'];
   ```
   `corpus` is reserved (unused in the sample). A new collection needs one line here plus a render function.
3. Data from claude.ai arrives **deep-frozen**. Code must never mutate `S.*` objects; it builds copies (`Object.assign({}, doc, changes)`).
4. Each render function (`renderOverview`, `renderPlan`, `renderInvest`, `renderCards`, `renderInsurance` and so on) runs inside its own `try/catch`, so one bad record cannot blank the page.
5. Writes made from the page (ticking a bill, editing a target) use `db.doc('collection/docId').update({...})`. A viewer without edit rights sees inputs disabled.

### 1.3 Capabilities the published page declares

Declare these when publishing on claude.ai:

```json
{ "db": {}, "downloads": true, "user": {},
  "mcp": { "servers": [ { "server": "Notion", "tools": ["notion-create-pages"] } ] } }
```

- `db` is required.
- `downloads` is needed for the "Download offline copy" button.
- `user` is used to tell the owner (edit rights) from viewers.
- `mcp` is optional and only powers "Save this month to Notion". Drop it if you don't use Notion.

### 1.4 Offline download: how the file embeds a copy of itself

- `build.py` base64-encodes the page source and writes it into the constant `SELF_B64` (placeholder `const SELF_B64 = '';/*@@SELF@@*/`). It also stamps `PAGE_BUILT` with the build time. The published page is the output of `build.py`, never the raw source.
- On "Download offline copy" the page:
  1. decodes `SELF_B64` to recover its own source;
  2. serialises the current state `S` to JSON (escaping `</`);
  3. clones the rendered `<main>` so the file previews even where scripts can't run, and adds a short note at its top;
  4. writes a new HTML document of the form `<script>window.__SNAPSHOT__=…;window.__SNAPSHOT_DATE__="…";window.__HIDE__=…</script>` + the source;
  5. saves it as `Personal-Finance-Dashboard-YYYY-MM-DD.html`. On claude.ai it uses the `downloads` capability; in a normal browser it falls back to a Blob link.
- The privacy toggle (eye icon) state is carried in `window.__HIDE__`.
- **Parity rule:** every feature must behave identically online and offline. The offline file re-runs the same code over the snapshot.
- The template file is an offline file with `window.__TEMPLATE__=true`, which keeps its download button visible.

### 1.5 External resources

- **Fonts (Google Fonts, one stylesheet):** Source Serif 4 (400, 600; optical sizes 8–60), Bricolage Grotesque (500, 700), IBM Plex Mono (400, 500), IBM Plex Sans (400, 500, 600), with `display=swap`. Each family has a system fallback stack, so the page still works offline.
- **No JavaScript libraries.** All charts are hand-built inline SVG.
- **No network calls at runtime** apart from the font stylesheet, plus the optional Notion call when the user presses "Save this month".

### 1.6 Build and test workflow (for the maintaining LLM)

1. Edit the source file (any name works, for example `dashboard.core.html`).
2. Run `python3 scripts/build.py --name <Name>`. This embeds `SELF_B64` and writes the publishable HTML plus `<out>.check.js` (the extracted script).
3. Run `node --check <out>.check.js` (syntax).
4. Run a headless browser test: load the page with a fake `window.claude.use('db')` that serves frozen data, collections arriving at staggered times, with card statements last. Assert no page errors. Then download the offline copy and assert the same sections render.
5. Publish to the **same** artifact URL so the link and database are kept.
6. Keep one backup of the source per version (`core.vNN.html`).

---

## 2. Complete database schema

Conventions:

- Collection names are lowercase.
- Document ids are short lowercase slugs (`regalia`, `home`, `ppfas`) or dates (`2026-11`, `2026-11-13`, `2026-27`).
- Money is in rupees as numbers (not strings), two decimals at most.
- Dates are ISO `YYYY-MM-DD`; months are `YYYY-MM`.
- `null` means "unknown / not applicable"; the page shows "—".
- Text fields shown on screen should be short: one line, plain language.

### 2.1 `settings/main` (one document)

| Key | Type | Meaning |
|---|---|---|
| birth | string `YYYY-MM-DD` | Date of birth; retirement month = birth year + 60, same month |
| bank_floor | number | Minimum salary-account balance after bills (default 50000) |
| crash_floor | number | Lower floor allowed during a market crash (default 40000) |
| axis_float | number | Petty cash kept in the running account (also covers card auto-debits) |
| emi_topup_day | number | Day the EMI money must reach the EMI account (default 3); before it the EMI account is not flagged as short |
| sbi_locker | `{amt, fund_by 'MM-DD', until 'MM-DD', note}` | Optional yearly locker fee held in the EMI account from `fund_by` until `until` (or until `months/<YYYY-MM>.locker_debited`) |
| regular_threshold | number | Free cash needed at month start before regular stock buying |
| regular_max | number | Monthly cap for regular stock buying |
| dip_max | number | Monthly cap when buying a market dip |
| rule_from | `YYYY-MM` | Month from which the buying rules apply |
| emi_day | number | Day of month the home-loan EMI debits |
| ctc_fixed | number | Fixed annual CTC (for employer life cover) |
| employer_cover_multiple | number | Employer term cover = multiple × ctc_fixed |
| life_cover_personal | number | Personal term cover |
| life_cover | number | Optional stored total (the page recomputes it) |
| epf_monthly | number | Monthly EPF contribution (you + employer, excluding EPS) |
| epf_pension | number | EPS pension share inside the EPF balance (excluded from the corpus) |
| home_value | number | Your estimate of the home's market value (editable in the Net worth panel and under Facts) |
| loan_original | number | Original home-loan principal (fallback if `loans/home.original` is missing) |
| stock_buy_yearly, us_buy_yearly | number | Yearly Indian / US direct-stock buying used by the retirement model |
| us_target_pct | number | Comparison point for the US share of retirement equity |
| lounges | `{v, note}` | Lounge-access summary tile text |
| card_note | string | Short note on the Cards section |
| notion_parent | string | Notion page id for "Save this month" (optional) |
| last_updated | ISO timestamp | Shown in the sidebar; set by every refresh |
| last_updated_by | string | "weekly refresh", "monthly update", etc. |
| cf | object | Cash flow assumptions and overrides: `hike_pct`, `hike_month` (1–12, month the raised pay is for), `net_share` (share of a gross raise that reaches take-home, default 0.64), `sip_step_pct`, `sip_step_from` (`YYYY-MM`, empty = with the raise), `stock_default` (future stock buys per month), `avg_n` (months averaged for card spend), `rent_until` (optional end date for other income), `ovr` `{YYYY-MM: {salary, other_income, sip, stocks}}` (one forecast month only), `saved` `{YYYY-MM: {at, rows[{k, inn, out, me}]}}` (dated forecast copies). Offline: `localStorage` `pf-cf` |

### 2.2 `months/<YYYY-MM>` (one per month)

| Key | Type | Meaning |
|---|---|---|
| label | string | "Nov 2026" |
| status | `open` \| `closed` | Closed months are final |
| salary, other_income | number | Income received that month (other income = rent, interest, freelance, etc.) |
| sip | number | Total mutual-fund SIPs that month |
| direct_equity | number | Stock buying that month (India + US) |
| emi, emi_interest, emi_principal | number | Home-loan EMI and its split |
| emi_paid | boolean | EMI debited |
| card_gross | number | Sum of card bills paid this month |
| card_net | number | Own card spend (gross minus money others paid back) |
| ef_add, travel_add | number | Added to the emergency fund / travel fund this month |
| emergency_fund, travel_fund | number | Balances after the additions |
| free_cash | number | Salary-account balance after this month's bills, EMI and transfers |
| other_credits | object | `{label: amount}` money received from others (optional) |
| other_credits_meta | object | `{label: {date, desc, type, account, status, covers_card, pay_m}}` details for those receipts, written when one is edited on the Cash flow page (optional) |
| sip_src, direct_equity_src | string | Where an edited `sip` / `direct_equity` came from (e.g. "Edited in Cash flow · 18 Nov 2026") |
| stock_buys | array | `[{date, ticker, qty, price}]` (optional; feeds the stock budget) |
| note | string | One or two sentences of context |

### 2.3 `cards/<cardId>` (one per credit card)

| Key | Type | Meaning |
|---|---|---|
| name | string | "HDFC Regalia Gold" |
| order | number | Display order |
| fee | number \| null | Annual fee |
| waiver | number \| null | Spend needed in the card year to waive the fee |
| milestones | string \| null | Short milestone text |
| cycle_start | number | Statement cycle start day |
| due_day | number | Payment due day |
| due_days | object | Optional per-month override `{YYYY-MM: day}` |
| bills | object | `{YYYY-MM (due month): amount}` |
| paid | object | `{YYYY-MM: true}` |
| anniv_spend | number \| null | Optional override of spend this card year |

### 2.4 `perks/<cardId>` (benefits and targets per card; may include debit cards)

| Key | Type | Meaning |
|---|---|---|
| name, order, role | string / number / string | Card name, order, its job ("Daily driver, milestones") |
| lounge | string[] | Lounge rules, one per line |
| perks | string[] | Other benefits, one per line |
| targets | array | `[{id, period: 'month'\|'quarter'\|'year', threshold, reward, note?, expiry_days?}]` |
| year_start | `MM-DD` | Card-year anniversary (for yearly targets) |
| warn | string | Optional warning line |
| spend, unlocked, used | object | Ticks and overrides saved from the page |
| sources | string | Where the rules came from |

### 2.5 `ccspend` (card statements)

**`ccspend/meta`**

| Key | Type | Meaning |
|---|---|---|
| asof | date | Last statement loaded |
| from, to | `YYYY-MM` | Months covered |
| cats | string[] | Category names; transaction rows refer to them by index |
| source | string | How the data was compiled |
| cards | object | `{cardId: {name, months:{YYYY-MM: net spend}, bills:{YYYY-MM: bill}, coverage:{YYYY-MM: note}, last_stmt, tx, year_start:'MM-DD', year_basis, lifetime_free?}}` |

The 18 sample categories, in index order:

0. Investments (NPS)
1. Home & appliances
2. Electronics
3. Food delivery
4. Groceries
5. Dining out
6. Travel & stays
7. Cabs & fuel
8. Bills & utilities
9. Insurance
10. Health & wellness
11. Fashion & personal care
12. Gift cards & vouchers
13. Subscriptions & fun
14. Online shopping
15. Rent & wallet loads
16. UPI to shops & people
17. Other

**`ccspend/tx-<cardId>-<YYYY>`**: transactions, **one record per card per card-year**. Best practice from day one:

- `<YYYY>` is the calendar year of the **April** that starts the year. `tx-regalia-2026` holds 1 Apr 2026 – 31 Mar 2027 by transaction date.
- On 1 April each year a new document starts; old documents are never rewritten.
- This keeps every record small: a heavy card is about 20–30 KB a year.
- Shape: `{ rows: [[date 'YYYY-MM-DD', merchant string, categoryIndex number, amount number (refunds negative), billMonth 'YYYY-MM'], ...] }`.
- The page merges all `tx-<cardId>-*` documents for a card (`id = key.slice(3).replace(/-\d{4}$/, '')`). A legacy `tx-<cardId>` document without a year also works.
- Card-year **benefit** logic is separate. It uses each card's `year_start` anniversary from `perks`/`meta.cards`, not the April document split.

### 2.6 `loans/<loanId>`

| Key | Type | Meaning |
|---|---|---|
| loan | string | Display name |
| order | number | Display order |
| emi | number | Monthly EMI |
| outstanding | number | Principal left |
| original | number | Original principal (progress bar) |
| rate | string | "8.40% floating", or a short status text |
| ends | string | Year or month-year |
| status | `Active` \| `Closed` | Closed loans show as chips |
| emis_total, emis_left | number | For short EMI loans |
| paid_by | string | Someone else pays it; excluded from net worth |

The home loan must use id **`home`**. The overview tile, Facts, the prepayment calculator and Bills all read `loans/home`.

### 2.7 `targets/<goalId>`

| Key | Type | Meaning |
|---|---|---|
| label | string | Goal name |
| order | number | Display order |
| target | number | Goal amount |
| by | `YYYY-MM` \| null | Deadline |
| note | string | Short note |
| expected_inflow, inflow_label | number, string | Money expected before the deadline |
| in_kind | array | `[{label, value, note, received}]` vouchers that count toward the goal but aren't cash |
| current | number | Manual progress (with `manual: true`) |
| sale_car, sale_est | string, object | Car goal: sale estimate per car |

Built-in ids and how their progress is computed:

- `ef` → `months.emergency_fund`
- `travel` → `months.travel_fund`
- `networth` → latest `trend.total`
- `car` → sum of `mf` docs with `goal: 'Car'`
- `prepay` → `current`

Other ids use `current`.

### 2.8 `actions/<id>` (to-dos)

`{item, amount, due 'YYYY-MM-DD', month 'YYYY-MM', status 'To do'|'Done', done boolean}`

### 2.9 `mf/<fundId>` (one per fund, plus `usstocks`)

| Key | Type | Meaning |
|---|---|---|
| fund | string | Full scheme name |
| goal | string | "Retirement", "Car" or any label; "Retirement" funds enter the corpus |
| sip | number | Monthly SIP |
| invested, current | number | Cost and value |
| as_of | date | Value date |
| bucket | `equity` \| `mixed` \| `debt` \| `us` | Asset class for the wealth mix (default `equity`) |
| kind | string | `US mutual fund` for US funds; the `usstocks` doc uses `US stocks (…)` |

`mf/usstocks` mirrors the US direct-stock total so goals see it: `{fund, goal:'Retirement', sip:0, invested, current, kind:'US stocks (platform)'}`.

### 2.10 `ppf/<FY>` and `nps/<FY>` (FY id like `2026-27`)

- **PPF:** `{balance, balance_asof, contributed, limit 150000, min_yearly 500, target}`
- **NPS:** `{balance, balance_asof, contributed, min_yearly 1000, target, note}`

A new document starts each April.

### 2.11 `trend/<YYYY-MM-DD>`

`{date, total, source}` — one point per weekly refresh. `total` = `invest/snapshot.total`.

### 2.12 `insurance/<policyId>`

| Key | Type | Meaning |
|---|---|---|
| order | number | Display order |
| kind | `term` \| `health` | |
| scope | `Personal` \| `Work` \| `Parents` | |
| name, insurer | string | |
| policy | string \| null | Policy number, shown in full |
| cover | number | Sum assured / total sum insured |
| base, booster, safeguard | number | Health split (optional; draws the cover bar) |
| copay | string | Health note |
| start, end, pay_until, renews | date | `renews` drives "Coming up" |
| prem_now | number \| null | Current premium (null = paid upfront; see `prem_total`) |
| prem_freq | string | `Monthly`, `Yearly`, `Employer-paid`, or a free text like "2 years, paid upfront" |
| prem_day | number | Debit day for monthly premiums |
| prem_total | number | Upfront multi-year premium |
| prem_start | number | First annual premium incl. GST (term) |
| prem_start_freq | string | Frequency of `prem_start` |
| cover_prev, formula | number, string | Employer cover last year and its formula |
| members | string | Who is covered |
| nominee | string | "Name (100%)" |
| features | string[] | Up to 3 short lines |
| early_exit | `{from, to, policy_years}` | Return-of-premium window |
| since | date | Continuous cover since |
| history | array | `[{y, amt, gst, note}]` premium history for the chart. `y` is the financial year (`2025-26`). The first term and the first health policy that have a history feed the Combined chart (4.14). |

### 2.13 `invest/*` (investment documents)

| Doc | Shape |
|---|---|
| `equity` | `{asof, note, rows:[{ticker, sector, mcap, sleeve 'Core'\|'Satellite'\|'Specials'\|'Gold', shares, avg, ltp, invested, value, pnl_pct, weight (ex-GoldBEES %), chg_1y, chg_3m, high52, low52, from_high, target '10–12%', qvgm '16/20', action, order, note}]}` |
| `us` | `{asof, usdinr, perf_asof, bench:{name, chg_3m, chg_6m, chg_1y}, rows:[{ticker, name, order, invested, value, invested_usd, value_usd, last_usd, pnl_pct, pnl_pct_usd, chg_1y, chg_6m, chg_3m, bsince, weight}]}` (bench = Nasdaq 100 / QQQ in USD; bsince = Nasdaq 100 bought on the same dates, %) |
| `mfret` | `{asof, bench_note, rows:{fundId:{category, r1y, r6m, r3m, r3y, rank 'n of N', flag, bname, b3m, b6m, b1y, bsince}}}` (b* = the fund's own benchmark; bsince = same buys into the benchmark, %) |
| `planreview` | `{reviews:[{date, actual, next:{date, value}, proj60, need, end, spend, path[₹ thousands per month to 60]}]}` (written only by the page's "Record this review") |
| `meta` | `{asof, source, eq_invested, eq_value, nifty1y, nifty3m, qqq1y, qqq3m, notes_eq[], notes_mf[], notes_us[], review:{done, next, order[tickers], summary}}` |
| `snapshot` | `{asof, source, total, components:[{key 'eq'\|'mf'\|'usmf'\|'us'\|'epf'\|'ppf'\|'hm'\|'ef'\|'nps', label, group 'Market-linked'\|'Retirement, locked'\|'Cash for goals', invested\|null, value, note, tab\|null, asof}], notes[4]}` |
| `results` | `{asof, season 'Q2 FY27', total, declared, pending[], review[], rows:[{ticker, stock, date, verdict 'Strong'\|'Solid'\|'Mixed'\|'Weak', action, note}], source}` |
| `earnings` | `{method, per:{TICKER:{rev, pat, m, dm, mtype, mom}}, momentum:{up, down, same, new, down_list[]}, notes[], quarters:[{q, status, n, cov, strong, solid, mixed, weak, avg_rev, med_rev, avg_pat, med_pat, avg_m, med_m, avg_dm, breadth, breadthp, pat20, pat20p, patdec}]}` |
| `watch` | `{asof, source, research_note, reports:[{date, title, take}], rows:[{ticker, name, sector, qvgm, lo, hi, ltp, status, note}]}` |
| `returns` | `{asof, mf_asof, basis, basis_mf, lots:{TICKER:[[date, qty, price]]}, us:{basis, lots:{TICKER:[[date, usd_amount, usd_price]]}}, mf:{fundId:{cfs:[[date, -amount]], cost, mv}}, nps:{basis, cfs}, mf_lifetime:{label, xirr}, rates:{epf:{label, rate}, ppf:{…}, ef:{…}, hm:{…}}, pending:[{what, qty_or_amount, seen}]}` |
| `flows` | `{asof, from 'YYYY-MM', stocks_from, stocks_note, basis, note, cols:['stock_buy','stock_sell','mf_buy','mf_sell','us_buy'], months:{YYYY-MM:[5 numbers]}}` |

### 2.14 `rewards/main` (card points and cashback; one document)

| Key | Type | Meaning |
|---|---|---|
| asof, source, note | string | Freshness line and one note under the wallet |
| programs | array | One per points programme: `{id, card, short, unit 'RP'\|'MR'\|…, bal, asof, src, rule (expiry rule, one line), route (default route id), routes:[{id, label, v (₹ per point)}], expiring:[{date, pts, est}]}`. Cards that earn into one points account get ONE row. Partner programmes added by a transfer carry `partner: true`. |
| redemptions | array | `{id, date, card (program id), pts, kind 'voucher'\|'transfer'\|'credit'\|'booking'\|'other', partner, ppts, pid, value, useby}`. Written by the page's "Record a redemption" form; the card balance goes down by itself. |
| routing | array | "Which card for which spend": `{spend, card, ret}` |
| watch | string[] | Short reminders (expiry traps, where to check) |
| points | object | Statement-by-statement history for the main points card: `{label, note, rows:[{m, date, open, earned, bonus, red, adj, close}]}`. `adj` = points removed (refund reversals, EMI conversions, lapses); explain large removals in `note`. |
| cashback | object | `{note, series:[{key, label}], rows:[{m, <key>: ₹}]}`, one series per cashback card |

### 2.15 `bank/<accountId>` (savings accounts; one per bank account)

| Key | Type | Meaning |
|---|---|---|
| name, role, tag, order | string / number | Bank name, one-line role, short pill text, display order |
| need | `'floor'` \| `'float'` \| `'target'` \| `'emi'` \| `'hold'` \| `'locked'` \| null | What the account must hold: floor = goal reserve + `bank_floor` (salary account); float = `axis_float` (petty cash); target = a `targets` goal (emergency fund, whole balance earmarked); emi = next EMI of `loan` (+ locker fee in season); hold = `keep` (e.g. a tenant's deposit); locked = the whole balance (a fixed deposit under lien, not spare cash); null = all free |
| target, loan | string | `targets` id for need `target`; `loans` id for need `emi` |
| keep, keep_note | number, string | Amount and reason for need `hold` (editable on the page) |
| bal, asof, src | number, date, string | Current balance, date, source ("Typed in" when edited on the page) |
| hist | `{YYYY-MM: balance}` | Month-end balances (the page writes the current month when you type a balance) |
| note | string | One line shown in the detail row |

### 2.16 `tax/fy<YYYY-YY>` (one per tax year, e.g. `fy2026-27`)

| Key | Type | Meaning |
|---|---|---|
| fy, label, regime, asof, src | string | Tax year, label, `new` or `old`, freshness and sources |
| salary | `{ytd_gross, ytd_to 'YYYY-MM', monthly, extras_note, bonus, pt_ytd, epf_ytd}` | Payslip April-to-date gross, monthly gross for the rest of the year, bonus (typed on the page) |
| tds | `{months:{YYYY-MM: ₹}, monthly_next, src}` | TDS deducted per month and the expected monthly figure to March |
| cg | array | `{id, src, asof, stcg_eq, ltcg_eq, stcg_other, stcg_other_loss, ltcg_other, note}` per source (mutual funds, Indian stocks, US stocks) |
| spec | `{cy, src}` | Intraday (speculative) profit or loss this year |
| other | `{div_in, div_us, us_tax_withheld, interest_sb}` | Dividends, US tax withheld, savings interest (typed on the page) |
| losses_cf | array | `{ay, kind, amt, last_ay}` losses carried forward |
| lrs | `{ytd}` | Money sent abroad this year (TCS context) |
| returns | array, newest first | `{ay, fy, form, filed, regime, income, tax, tds, adv_tax, sa_tax, tcs, refund, refund_got}` past returns; missing values show "—" |
| todo | string[] | Documents still needed this year |

Rules:

- The `returns` cash flows are negative for money put in and positive for money taken out.
- `flows` holds monthly gross amounts (positive numbers).

### 2.17 `inflows/<id>` (other money in; one per receipt)

| Key | Type | Meaning |
|---|---|---|
| date, m | date, `YYYY-MM` | Receipt date and its month |
| amt | number | Amount |
| desc, type | string | Description; type: Family reimbursement, Employer reimbursement, Flex claim, Tax refund, Gift, Other |
| account | string | `bank` id it landed in |
| status | `actual` \| `expected` | Expected receipts count in forecast months only; in a recorded month they are listed but not counted until marked actual |
| covers_card, pay_m | boolean, `YYYY-MM` | The receipt repays a card payment made in month `pay_m`; that month's card payments rise by the same amount, so the two net out while keeping timing differences |
| added, edited | date | Audit dates |

Offline, entries and edits are kept in `localStorage` `pf-inflows`. Receipts already in `months.other_credits` are shown alongside and edited in place (each receipt counts once).

---

## 3. Design system and visual tokens

The live look is **"Navy & gold, left sidebar"**. Its scope `:root[data-look="new"]` is set by script on load. The base tokens below are overridden by it; both sets are listed.

### 3.1 Color tokens: active look (light)

| Token | Hex | Use |
|---|---|---|
| `--bg` | #f5f2ec | Page background (warm paper) |
| `--surface` | #ffffff | Panels, tiles, cards |
| `--ink` | #1c2333 | Primary text |
| `--muted` | #636a7d | Secondary text, labels |
| `--line` | #e7e2d6 | Borders, dividers |
| `--track` | #ece7da | Meter tracks, hover fills |
| `--accent` | #27407a | Navy: primary series, links, active states |
| `--accent-soft` | #f1eadb | Soft fill behind accent chips |
| `--saffron` | #9d7422 | Gold: shares/percentages (`.shr`), second series |
| `--saffron-soft` | #f6edd6 | Tips, soft highlights |
| `--good` | #2b6a46 | Gains, "on target" |
| `--warn` | #96600a | Warnings |
| `--bad` | #b3261e | Losses, overdue, over cap |
| `--c3` | #2f8f86 | Teal series |
| `--c4` | #8a8f98 | Grey series / "other" |
| `--c5` | #8a5a8f | Plum series |
| `--c6` | #2a83a8 | Blue series |
| `--c7` | #b04e78 | Rose series |
| `--side` | #111a2e | Sidebar background |
| `--side-ink` | #c9cfdd | Sidebar links |
| `--side-mut` | #7f89a1 | Sidebar group headers |
| `--side-ctl` | #1c2742 | Sidebar controls |
| `--side-line` | #2b3757 | Sidebar borders |
| `--gold` | #c39a4b | Active nav marker, meters in Money moments |
| `--gold-ink` | #e7c888 | Active nav text, month arrows |
| `--hero` | #111a2e | Hero "floor" card background |
| `--hero-num` | #f0d9a6 | Hero big number |
| `--tip` | #111a2e | Tooltip background |

### 3.2 Dark mode (active look)

Applied by `:root[data-look="new"][data-theme="dark"]` when the sidebar switch is set to Dark. The page sets `data-theme="light"` by default, so the `prefers-color-scheme` rules only matter if that attribute is removed:

| Token | Dark value |
|---|---|
| bg | #0c111d |
| surface | #141b2c |
| ink | #e8ebf2 |
| muted | #99a2b6 |
| line | #263049 |
| track | #1f2940 |
| accent | #9db8f2 |
| accent-soft | #1e2a47 |
| saffron | #d9b266 |
| saffron-soft | #3a2f17 |
| good | #5cc488 |
| warn | #e3a64c |
| bad | #f2786d |
| c3 | #5fc4b8 |
| c4 | #7d8696 |
| c5 | #c49ac8 |
| c6 | #6cc0e0 |
| c7 | #e38fb4 |
| side | #080c15 |
| side-ctl | #151d31 |
| side-line | #263049 |
| hero | #18233f |
| tip | #2a3657 |

### 3.3 Base ("classic") tokens, still defined underneath

| Token | Light | Dark |
|---|---|---|
| bg | #f4f6f4 | #0e1412 |
| surface | #ffffff | #151d1a |
| ink | #16201c | #e5ece8 |
| muted | #5a6963 | #94a49d |
| line | #dce3df | #26312d |
| track | #e6ece8 | #212c28 |
| accent | #0c6a5c | #4cc0ab |
| accent-soft | #d9efe9 | #163a33 |
| saffron | #b8700c | #e5a645 |
| saffron-soft | #f8ead3 | #3a2c14 |
| good | #1c7a48 | #5cc488 |
| warn | #9a5c00 | #e3a64c |
| bad | #b3261e | #f2786d |
| c3 | #3d5fa8 | #8aa6e6 |
| c4 | #8a8f8c | #7d8682 |
| c5 | #8a5a8f | #c49ac8 |
| c6 | #2a83a8 | #6cc0e0 |
| c7 | #b04e78 | #e38fb4 |

### 3.4 Status chips and badges

- `.chip`: inline-flex, 0.75rem/600, padding 2px 8px, radius 999px, with a 6px dot (`::before`, `currentColor`).
- Variants:
  - `good`: text `--good` on `color-mix(--good 14%, transparent)`
  - `warn`: 16% mix
  - `bad`: 14% mix
  - `info`: text `--accent` on `--accent-soft`
- `.feepill`: 0.66rem/600, padding 1px 7px, radius 999px, `--track` background, `--muted` text. `.feepill.paid` uses `--saffron-soft`.
- Tooltip `.ctip`:
  - Box: `--tip` background, white text, radius 8px, padding 6px 10px, shadow `0 3px 12px #0003`, max-width 250px, font .76rem, line-height 1.3.
  - Contents: title `strong` .95rem tabular-nums; sub `small` .68rem.
- Two-tone value rule:
  - Amounts (`.amt`) use `--ink`, weight 600.
  - Shares and percentages (`.shr`) use `--saffron`, weight 500.
  - Gains and losses use `--good` / `--bad`.

### 3.5 Typography

- **Fonts:**

  | Variable | Family | Fallback stack |
  |---|---|---|
  | `--display` | Source Serif 4 | Georgia, "Times New Roman", serif |
  | `--body` | IBM Plex Sans | "Segoe UI", system-ui, sans-serif |
  | `--mono` | IBM Plex Sans in the active look | (base look uses IBM Plex Mono) |

- **Body:** `15px/1.5 var(--body)`; the active look sets `font-variant-numeric: tabular-nums lining-nums` on body.
- **Headings** use `--display`, `text-wrap: balance`, letter-spacing −0.01em:

  | Element | Font | Size | Weight / line-height |
  |---|---|---|---|
  | H1 (sidebar brand) | display | 1.12rem | 400, line-height 1.15, white |
  | H2 (section page head) | display | `clamp(1.4rem, 3vw, 1.75rem)` | 400, line-height 1.15 |
  | H2 elsewhere | display | 1.3rem | 400 |
  | H3 (panel titles) | display | 1.08rem | 400 |

- **KPI values** (`.tile .v`, `.moment .v`, snapshot groups, components): display 400, 1.32rem, line-height 1.2; `.moment .v` 1.22rem.
- **Hero number:** display 400, `clamp(2.2rem, 6vw, 3.4rem)`, line-height 1, color `--hero-num`.
- **Labels** (`.label`): 0.72rem, uppercase, letter-spacing 0.06em, weight 600, `--muted`.
- **Small text** (`.small`): 0.82rem.
- **Nav links:** .86rem, padding 5px 10px.
- **Nav group headers** (`.ng`): .64rem, uppercase, letter-spacing .09em, `--side-mut`.
- **Tables:** body text .82–.88rem; numbers right-aligned, tabular.

### 3.6 Layout

- Page wrapper `.wrap`:
  - Base: max-width 1180px, flex column, gap 28px, side padding `max(16px, env(safe-area-inset-left|right))`, bottom padding 48px.
  - Active look: max-width 1240px, gap 22px, padding-top 16px.
- **Desktop (≥960px):**
  - Body `padding-left: 222px`.
  - Sidebar `.bar-top` is `position: fixed`, 222px wide, full height, scrolls.
  - Nav is a vertical list in five groups, ordered with flex `order` classes `.n1`–`.n5`:
    1. Today: Overview, Bills, To-do
    2. Money in & out: Income, Cards, Trends
    3. Wealth: Wealth mix, Retirement, Investments, PPF & NPS
    4. Plans: Targets, Loans, Insurance
    5. Facts
- **Phone (<960px):** sticky top bar; a "Menu" button opens the nav as a grid `repeat(auto-fill, minmax(8.5rem, 1fr))`.
- **Panels** (`.panel`):
  - `--surface` background, 1px `--line` border, radius `--r` (12px in the active look), padding 16px 18px (14px 16px at narrow widths), flex column, gap 12px, `min-width: 0`.
  - Active-look shadow: `0 1px 2px rgba(17, 26, 46, .05)`.
- **Tiles** (`.tile`): same surface, padding 12px 14px, gap 4px.
- **Money-moment cards** (`.moment`): padding 10px 12px, gap 3px. Grid of 4 columns on desktop; 2 columns, then 1 on phones.
- **Hero:** grid `minmax(0, 1.25fr) minmax(0, 1fr)`, gap 16px. The floor card has padding 22px 24px and gap 10px.
- **Meters:** height 8px (6px inside moments), radius 99px, `--track` background.
- **Section heads** (`.pagehead`): flex row, baseline-aligned, 1px bottom border, `margin: 0 0 6px`, `padding-bottom: 6px`.
- **Inputs and buttons:** radius 7px, 1px `--line` border, padding 5px 8px (buttons 5px 10px). Focus ring 2px `--accent`, offset 2px (gold inside the sidebar).
- **Hover selection scheme** (used everywhere): hovering one row, bar or card dims its siblings to opacity .45–.55. Charts dim non-selected bars the same way.
- **Responsive rule:** no horizontal page scroll at 400px; wide tables scroll inside `.tbl { overflow-x: auto }`.

### 3.7 Charts (all inline SVG, no library)

| Helper | What it draws |
|---|---|
| `svgStack(el, rows, series, xlab, o)` | Stacked bars; `o.values` prints totals on top; `o.pick` / `o.onClick` pin a bar |
| `svgBars` | Single-series bars with value labels |
| `svgLines` | Multi-line chart |
| `svgNet(el, rows, xlab, o)` | Positive/negative bars; `o.trend` adds an inline "\| ±x%" year-on-year label |
| `hbarList`, `divBars` | Horizontal bar lists; `.div-bars` uses CSS subgrid so labels align |
| Donut | Insurance tiles: SVG circles with `stroke-dasharray`, 68px |

Every chart goes through `scrub(svg, …)`:

- Hovering, tapping or using the arrow keys moves a readout line (`.chart-read`) below the chart.
- A tooltip (`.ctip`) follows the pointer.
- When the pointer leaves, the readout returns to the latest or pinned item.
- Interactive SVGs get `tabindex=0`, class `scrubbable` and `cursor: crosshair` (`pointer` where a click pins).

### 3.8 Privacy toggle (eye icon)

- Hides salary and investment figures only; card spending and bills stay visible.
- A MutationObserver (`window.__mask`) replaces digits in text nodes with "••".
- Number inputs get a dotted overlay.
- Sections excluded from masking: `#cards`, `#bills`, `#insurance` (except elements with class `.ins-priv`, such as the employer cover, which reveals CTC), and `.ins-pub` tiles.
- The state is kept in `localStorage` key `md-hide`.

---

## 4. Component-by-component blueprint and formulas

Sections top to bottom (each is `<section id>` with a `.pagehead`):

### 4.1 Sidebar

- Brand (H1) and eye toggle.
- Month picker: prev/next buttons, a month `<select>` and a year `<select>`, over all `months` docs. Years come from the month records; the next year is listed greyed "<year> (Jan)" until its first month record exists. The next calendar month is listed as "<Mon> · next" as soon as a card bill for it exists (no `months` record needed). The page opens on the current calendar month (a saved choice wins).
- "Updated …" line from `settings.main.last_updated`.
- Status chip (month open/closed).
- Nav (five groups). The To-do link shows a count badge of Needs attention items, coloured by the most urgent; hidden when there are none.
- The nav fills the full sidebar height (groups spread top to bottom). Spacing scales with window height (`clamp()` on link padding, group-label padding and gaps) so the whole sidebar fits without scrolling from about 680px tall; below 730px tall links use 1px padding.
- "Download offline copy" button.
- Theme switch at the bottom: a minimal sun / moon pill. Light is the default whatever the device setting; the choice is kept per browser (`localStorage` `pf-theme`) and works offline. On phones it sits inside the open Sections menu.
- The active nav link is highlighted by a scroll spy (top threshold 80px). A clicked link stays lit until the user scrolls with wheel, touch or keys.

### 4.2 Overview (`#overview`)

**Hero card ("Spare cash"):**

- Big number = Σ over all `bank` accounts except need `target` (emergency fund) of `max(0, bal − what it must hold)`, with the latest balance date.
- One compact row per account: name · free ₹ · why (above the floor / above petty cash / EMI held or "top up by <date>" / above the deposit / all free). The salary-account row turns amber under ₹10K above the floor and red below it. Rows open Savings.
- A highlighted line: "Move ₹X to <salary account>", listing the free money sitting in other accounts.
- Tap the card for the floor breakdown: `floor = goal reserve (travel_fund) + bank_floor`, `crash = travel_fund + crash_floor`.

**Needs attention** (shown at the top of To-do, not on the Overview; red, then amber, then blue; tap opens the section): card bills / EMI overdue or due in 3 days; savings accounts short of what they must hold (the EMI account only from `emi_topup_day`); salary account under ₹10K above its floor; balances older than 35 days; points expiring in 60 days, vouchers in 30; insurance renewals in 30 days; half-yearly review due; tax refund not received 45 days after filing; locker fee to move in the next 5 days.

**Tiles:**

- **Stock budget · buy next:** `deploy = free_cash − bank_floor − axis_float`. "Used" = this month's `stock_buys` total. Lists the next names in `invest/meta.review.order`.
  - Checks for a planned buy amount `amt`, where `before = free_cash − bought` and `after = before − amt`:
    - **Regular mode:** `free_cash ≥ regular_threshold`; `bought + amt ≤ regular_max`; `after ≥ bank_floor + axis_float`.
    - **Dip mode:** `bought + amt ≤ dip_max`; `after ≥ bank_floor`.
    - **Crash mode:** `after ≥ crash_floor + axis_float`.
- **Net worth:** financial assets + `home_value` − active loans (loans with `paid_by` left out), change vs last month; tap opens the Net worth section.
- **Card spend:** `card_net`, with the change vs the previous month.
- **Net invested** (FY Apr–Mar or calendar Jan–Dec toggle): see 4.6.

**Money moments** (8 cards):

- **Retirement on track:** `forecast − required` from the Retirement model. Tag "Enough by about age X" = first age where the projected balance ≥ need.
- **Next milestone:** next value in `[25L, 50L, 75L, 1Cr, 1.5Cr, 2Cr, 3Cr, 5Cr, 10Cr]` above the latest `trend.total`.
  - Months to it at the average monthly increase.
  - Progress meter = (latest − previous milestone) / (next − previous).
- **Freedom runway:** `latest total / (monthly spend setting × 12)` years. Tagged "Asset coverage · not liquid cash".
- **Compounding at work:** growth share = `1 − contributions / forecast` at 60, with contributions = opening balance + all deposits.
- **Home loan paid off:** `(original − outstanding) / original`. "Estimated end" = `loans/home.ends`. Links to the prepayment calculator.
- **Wealth added this month:** latest `trend.total` − total at the end of the previous month.
- **Term life cover:** a stacked split bar of term policies with a one-line legend (Personal / Employer).
  - Total = Σ cover of `insurance` docs with `kind: 'term'`.
  - Line under the legend: total ÷ `loans/home.outstanding` as "N× the home loan left" (kept below the legend so both insurance bars line up).
  - Employer figure is masked by the eye toggle.
- **Health cover for you:** split bar of Base / Booster / Safeguard / GMC with a compact legend. Parents' cover is not shown on the card.
- Every card is clickable (and Enter on keyboard) and opens its section: Retirement and Compounding → Retirement at 60; Milestone → Targets; Runway and Wealth added → Wealth mix; Home loan → Loans; Term and Health → Insurance. Links inside a card keep their own target.

### 4.3 Income (`#income`)

- Salary and other-income inputs (editable; offline edits stay in the browser).
- **Split of income** (stacked bar and legend):

  | Part | Formula |
  |---|---|
  | Invested | `sip + direct_equity` |
  | Saved | `ef_add + travel_add` |
  | EMI | `emi` (all loan EMIs) |
  | Spent | `card_net` |
  | Left in bank | `income − (invested + saved + EMI + spent)` |

  Percentages are of income (salary + other income). A red note appears when the left-in-bank part is negative.
- **Month by month:** stacked bars of the same five parts for all months. Click a month to open it.
- **What changed this month:** card spend, investments, saved and income vs the previous month, with arrows.
  - "What drove the spending change": category deltas between the last two statement months, from `ccspend` (collapsible).
  - "One-off items": transactions over ₹10K.

### 4.3b Cash flow ahead (`#cashflow`)

Money in and out per month: recorded months from `months/*`, then a forecast to the financial-year end (31 March). Salary, other income, mutual funds and stocks are the **same fields** the Income and Investments sections use, so an edit in either place shows everywhere.

- **Header:** date range, year select (record years + next year greyed), 3M / 6M / YTD history window (default 3M; `localStorage` `pf-cf-win`). 3M = the selected month and two before; YTD = January to the selected month. Months before the first record are dropped; missing months show "no record". Months after the selected one stay recorded until the latest record, then the live forecast runs to 31 March. A past financial year shows its records and the newest forecast saved in that year, with its date.
- **Summary cards** (buffer = salary-account balance − goal reserve; minimum = `bank_floor`):

  | Card | Formula | Click |
  |---|---|---|
  | Restore minimum buffer | `max(0, minimum − latest verified buffer)`, dated; "Minimum maintained · ₹X above" when 0 | Opens Savings and flashes the salary account |
  | Monthly adjustment needed | `max(0, −Σ forecast nets ÷ n)` over the forecast months shown; positive → "Average monthly surplus"; 0 → "Balanced on average"; none → "No forecast available". Excludes today's top-up | Opens Adjust assumptions |
  | Extra spending room | `max(0, lowest of {latest verified buffer, projected month-end buffers shown} − minimum)`. A monthly deficit alone does not make it 0. Month-end balances only; daily dips are not checked | Selects the limiting month and opens its calculation |

  "Needs reconciliation" when the account balance or a forecast month-end is missing. An "i" on each card explains it (hover or tap).
- **Monthly surplus / shortfall:** one bar per month (money in − money out), Recorded band blue, Forecast band gold, year boundaries marked, current month labelled "(Now)". Hover dims the others and shows "in − out = net" under the chart; click or Enter selects the month.
- **Salary-account buffer line:** recorded after-bills figures (`months.free_cash`), a diamond for the latest bank balance (from `bank`, need `floor`), dashed forecast month-ends carried forward from it (`previous + in − out`; nothing in that balance is deducted twice), the minimum as a dashed line. One point per month: in the bank balance's month the diamond replaces the after-bills point (the saved figure and the difference are in its tooltip). Hover shows a guide line and a readout; click selects.
- **Side panel (selected month):** Money in (salary, other income, other money in with ✎ per receipt and "+ Add money in"), Money out (card payments = own spend + card payments repaid by others, EMI, mutual funds, stocks, goal savings, one-offs), Monthly surplus/shortfall, "View entries & calculation". Recorded months write to `months/<YYYY-MM>`; forecast months save an override for that month only (`cf.ovr`); an empty box returns to the default; 0 is allowed.
- **Forecast defaults:** salary = latest record (+ approx. net raise from the month after `hike_month`: gross monthly × `hike_pct` × `net_share`); other income = latest record (until `rent_until` if set); mutual funds = SIP schedule (Σ `mf.sip` excluding US stocks), stepped up by `sip_step_pct` from `sip_step_from` (or the raise); stocks = `stock_default`; cards = average own spend of the last `avg_n` months; EMI = active loans not paid by others; goal savings = latest month; one-offs = locker fee (if set) and the PPF yearly minimum in March.
- **Adjust assumptions** (side drawer): raise month and %, SIP step-up % and start month, future stocks, averaging window; live preview; Apply saves `settings.cf` and a dated forecast copy; Reset; Esc closes. The footer lists the links (Income & Investments), the SIP schedule, the stock default, a raise that lands after the window, and "Save this forecast".

### 4.4 Net worth (`#wealth`)

**Net worth card** (top of the section; two equal halves split by a thin line):

- Left: net worth (big) and change vs last month; then three ruled rows, label left and full-rupee value right: Financial assets, + Home (editable, same field as Facts), − Home loan (red).
- Rows are interactive: hover, focus or tap highlights the row, dims the others and fills a detail line (share of what you own and monthly change; share of the home still on loan and the equity; EMI, rate and end year). Financial assets opens Investments, Home loan opens Loans, Home focuses the value. Default line: "Net worth = financial assets + home − home loan".
- Right: "Net worth by month" columns (one per month, value on top, latest solid, hover/tap readout). Earlier months use today's home value and loan.
- Phones: the chart moves under the rows.

**Savings → wealth link:** at render time (never in the database) the emergency fund = the `target` account's balance; "Other bank cash" = all balances − goal reserve − emergency fund − `hold` amounts; Cash class = goal reserve + emergency + other bank cash. The latest `trend` point gets the same difference.

**Tracked corpus over time:**

- Line chart of `trend` with range (6M/1Y/All) and view (Weekly/Monthly).
- Hover readout; "Snapshots & data entry" opens `invest/snapshot`.

**Where the money is** (snapshot): group cards (Market-linked, Ring-fenced debt, Retirement locked, Cash for goals, Cash) each with a left accent; a stacked bar of every holding — hover/tap a segment to light it and outline its card, with a line under the bar (holding · ₹ · % of total · its group ₹ and %); click jumps to the card; hovering a card lights its segment; arrow keys when focused. Component cards carry a top accent in their group colour.

**Tracked holdings by class:**

| Class | Formula |
|---|---|
| Equity | `eq + mf + usmf + us − GoldBEES − mixed MFs − debt MFs` |
| Debt | `EPF + PPF + debt MFs` |
| GoldBEES | GoldBEES value |
| Cash | `travel + emergency` |
| Hybrid | `mixed MFs + NPS` |

- Fund classes come from `mf.bucket`.
- Return per class is the XIRR of its cash flows. The debt XIRR is blended with EPF and PPF rates by value; cash uses the savings rate from `returns.rates`.
- "View holdings by account" lists every snapshot component with its XIRR. It is expanded by default.

**India and US retirement equity:**

- India = retirement equity − US. US = US funds + US stocks.
- Explore box: amount needed to reach a chosen US % with new money only = `(target × equity − US) / (1 − target)`, shown spread over 18 and 24 months.

**Whole retirement corpus:**

- Corpus = Indian direct stocks incl. GoldBEES + `mf` docs with goal "Retirement" (India and US) + US stocks + EPF − `epf_pension` + PPF + NPS.
- **Gold share:** `GoldBEES / corpus`, on a 0–10% scale with a tick at the 5% goal and a red tick at the 10% ceiling. "To reach 5%" = `0.05 × corpus − GoldBEES`, also shown per month over a year.

### 4.5 Retirement at 60 (`#plan`)

The model uses nine buckets. Each starts at today's value and has a default return and yearly step-up:

| # | Bucket | Return % / yr | Step-up % / yr | Deposit |
|---|---|---|---|---|
| 0 | India stocks | 12 | 5 | `stock_buy_yearly` ÷ 12 |
| 1 | India MFs | 12 | 7.5 | Σ retirement SIPs (non-US) |
| 2 | US stocks | 12 | 5 | `us_buy_yearly` ÷ 12 |
| 3 | US MFs | 12 | 7.5 | Σ US fund SIPs |
| 4 | GoldBEES | 8 | 0 | 0 |
| 5 | EPF | 8.25 | 7 | `epf_monthly` |
| 6 | PPF | 7.1 | 0 | 0 |
| 7 | NPS | 10 | 0 | 0 |
| 8 | Debt MFs | 7 | 0 | 0 |

Projection steps:

- Monthly factor = `(1 + g)^(1/12)`.
- Deposit in month m = `deposit × (1 + step)^floor((m − 1) / 12)`; the step-up applies after every 12 payments.
- An optional one-time inflow can be added in a chosen month to a chosen bucket.
- Every input is editable and saved per viewer.
- Months left = retirement month (birth + 60 years) − current month.

Need at retirement:

- Inflation factor `F = (1 + infl)^(years left)`.
- Real monthly rate `r = ((1 + post) / (1 + infl))^(1/12) − 1`, where post = growth after 60, default 8%.
- Annuity factor for ages 60 → end (paid in advance) = `(1 − (1 + r)^(−n)) / r × (1 + r)`, with n = (end − 60) × 12.
- `required = monthly spend today × F × annuity factor`. Defaults: spend ₹1,50,000/month, inflation 6%, end age 85 (80/85/90 selectable).

Outputs:

- Projected at 60, also in today's rupees (÷ F).
- Needed through the end age.
- Ahead/short.
- "Supports about ₹X/month in today's rupees".
- The curve fills the panel width (the SVG viewBox width follows the container and redraws on resize). It has dashed need lines for ages 80/85/90 and a hover/tap/arrow-key readout per month.
- Layout is tight: one line under the totals ("Pays ≈₹X/month in today's ₹ … · Needed: To 80 · To 85 · To 90"); the hover hint sits at the end of the legend.
- Settings: four buttons in one row (Corpus today · Investment settings · Spending & inflation · Projection details). On wide screens each opens on its own into a strip under the row, so the other buttons never move; on phones they stack.

**Half-yearly check** (`invest/planreview`):

- Reviews happen every May and November. "Record this review" (online only, one per month) saves `{date, actual, next:{date, value}, proj60, need, end, spend, path}`, where `actual` = today's corpus, `next.value` = the plan's corpus 6 months ahead, and `path` = the monthly projected corpus in ₹ thousands from that month to 60.
- On the curve: a dashed grey line = the plan saved at the first review (its `path`); green dots joined by a line = the actual corpus at each review (plus today). The x-axis starts at the first review.
- Panel: a "Today vs plan" box on one line, "Today vs <date> plan – ₹corpus | Plan ₹X · ahead/behind ₹Y (%) · at 60: ₹A Cr vs ₹B Cr needed" (actual vs the last review's path interpolated to today; full width until the beat/miss columns exist), plan-vs-actual columns for the last 4 reviews (green beat / red miss, gap above, tap for numbers), and a table (actual, plan expected, gap, projected at 60, needed, expect next, status On track / Behind path / Short at 60).
- A chip shows "Next review <date>" or "Review due now".

### 4.6 Investments (`#invest`)

Tabs: Overview, By goal, Indian direct equity, My mutual funds, US direct stocks, Results, Watchlist & research.

**Overview tab:**

- Total financial assets (`snapshot.total`).
- Group tiles (Market-linked, Retirement locked, Cash for goals), each as % of total.
- A stacked strip of all components.
- One card per component: value, gain on cost, % of total, XIRR, benchmark (Nifty 1Y / Nasdaq-100 1Y), note.

**New money invested, by year** (from `invest/flows` plus later lots):

- Gross = buys. Net = buys − sells − redemptions (rebalancing doesn't count as new money).
- Year mode: FY (Apr–Mar) or calendar.
- Investment filter: all / Indian stocks / mutual funds / US stocks.
- Range buttons: 3 yrs / 5 yrs / All.
- Year bars carry an inline "| ±x%" change vs the previous year. Click a year to see its months.
- Years before `stocks_from` are marked † (stock sales not available).

**Indian direct equity:**

- KPI tiles: invested, value, P&L %, XIRR from `returns.lots`, 1Y and 3M value-weighted change vs Nifty.
- Sortable holdings table (ticker, sector, mcap, sleeve, shares, avg, LTP, value, weight, P&L, 1Y, 3M, vs 52-week high, QVGM, plan).
- Period switch (1Y / 3M / P&L) for the bar chart.
- Sector and sleeve mix.
- Analyst read (`meta.notes_eq`) at the bottom.

**Performance vs benchmark** (My mutual funds and US direct stocks):

- Buttons 3M / 6M / 12M / Since bought (choice remembered per browser). One row per holding: holding bar vs benchmark bar, benchmark name under the holding. Hover or tap a row for "X vs benchmark Y → ahead/behind by Z pts".
- Each fund is compared with its own official index, never a category average. Where index data is not published, rebuild it from component prices (composite funds by their official weights) or use a labelled proxy, and say "approximate" in one short note (`mfret.bench_note`).
- US stocks: change in USD vs the Nasdaq 100 (`us.bench`, QQQ) as a dashed row.
- Since bought: the same buys (dates and amounts from `invest/returns`) put into the benchmark on the same dates; FIFO cost where units were sold. Fund side = gain on amount invested; US side = USD gain on average buy price.
- Notes under charts: one or two short lines only.

**Mutual funds:**

- By category bars, then (dotted separator) an **Equity vs debt** donut: Equity / Debt / Hybrid (multi-asset) from `mf.bucket`; tap a slice for its funds.
- Table with fund, goal, invested, current, gain, SIP, 1Y/3M/3Y, rank.
- Per-fund XIRR from `returns.mf[id].cfs` plus `mv`.
- Lifetime XIRR (`returns.mf_lifetime`).

**US direct stocks:** INR and USD values, P&L in both currencies, weights, XIRR in ₹.

**Results:**

- Season tile ("12 of 12 declared"), verdict buckets (Strong / Solid / Mixed / Weak), result rows with filter.
- Earnings aggregates per quarter: mean and median revenue and PAT growth, margin, breadth, % with PAT ≥ 20%, PAT declines.
- Momentum vs the prior quarter.

**Watchlist & research:** rows with entry zone `lo–hi` vs LTP; status chip (In zone / Near zone / Wait); reports list.

**XIRR:** solved on dated cash flows (money in negative, current value positive at the as-of date). Holdings under a year show the plain gain instead.

### 4.7 Bills (`#bills`)

- This month's card bills (by due day), the home-loan EMI (`loans/home.emi` on `emi_day`), and each monthly insurance premium (`insurance` docs with `prem_freq: 'Monthly'`, on `prem_day`). The premium uses the same tile and tick even when it is debited from a card; it is kept out of the outstanding total because it is already inside the card bill.
- Each row has a tick (`cards.paid[YYYY-MM]`, `months.emi_paid`, `months.ins_<policyId>_paid`).
- Any unpaid item past its due day turns the sidebar status to "Bill overdue"; within 2 days, "Bill due soon".
- Chips: Paid / Due in N days / Overdue N days.
- Header: outstanding total and the total of issued bills plus EMI.
- Offline, ticks save to `localStorage` (`pf-off-ticks`).
- **Due next month:** card bills whose due month is next month (statements that arrived this month) show in a block under this month's bills until next month's record exists: due-in-days chip, "Paid early" chip, ₹ still to pay, and a Paid tick that writes `cards/<id>.paid[<next month>]`. Needs attention warns 3 days before each such due date, across the month change.
- **Upcoming month:** when the next month is picked before its record exists, status reads "Upcoming", Bills shows its card bills (ticks work; EMI and premium ticks open on the 1st), Stock budget and Card spend read "Starts in <Mon>", Income shows a note instead of an empty split; saving income or month ticks waits for the month record.

### 4.8 Targets (`#targets`)

**Goal cards** (collapsible):

- Progress % and meter.
- Months left to `by`.
- Monthly need = gap ÷ months left; a second line shows the need after `expected_inflow`.
- Chips: Reached / Date passed.
- In-kind vouchers count toward the goal but not toward cash.
- Car goal: a sale-estimate input shows "still to save".
- Prepayment goal: a computed table of what ₹6,000 / ₹12,000 once or yearly saves on the home loan (monthly amortisation with the EMI unchanged: months saved and interest saved).
- Editable when online with edit rights.

**Stock weights vs target:**

- Weight = value ÷ direct-stock value excluding GoldBEES.
- Target range parsed from strings like "10–12%".
- Status: Below (weight < low), On target (inside the range or within ±0.25 pt), Above (> high).
- "Add ~" = `low% × total − value`; "₹X over" = `value − high% × total`.
- Filters (All / Core / Satellite / Specials / Gold) and sort (Action first / Weight / Sleeve).
- The order badge comes from `meta.review.order`.
- GoldBEES sits in its own block, scaled to the retirement corpus (see 4.4).

### 4.9 PPF & NPS (`#ppf`)

- The section is always open. Each financial-year card shows its progress bar, value vs target and the yearly-minimum chip (PPF ₹500, NPS ₹1,000).
- "Details & edit" (collapsed per card) holds amount to go, contributed vs limit (PPF ₹1,50,000), the rule note (deposit PPF by the 5th to earn that month's interest) and the input fields.

### 4.10 Cards (`#cards`)

Five views: Spending, All cards, Card detail, Benefits & targets, Rewards.

Card statements update the Cards section the day they arrive: a month still collecting statements is marked "so far", and rolling totals use complete months only.

**Spending view:**

- Period selector (last 12 statements, financial years) and card filter.
- KPI tiles: total, per month, biggest card, biggest category, heaviest month.
- Stacked bars by statement month and card (top 7 cards by spend plus "Other cards"). Click a month to filter.
- "Where the money went": category bars.
- Biggest purchases.
- Transaction list with search, list / by-merchant / by-month views, 25/50/All, and card and category chips. Merchants are normalised by a regex list (`MERCH`).

**Card years, fee waivers and milestones:**

- Card year = from the `year_start` anniversary to the day before the next one.
- Spend this card year = Σ transactions in that window up to the last statement.
- Each yearly target shows a progress meter, amount to go, days left, needed per month = `to go ÷ months left`, and last year's figure.

**Quarterly benefits:** calendar quarters by transaction date. Green = met; amber = quarter still open.

**Amex monthly bonus:** a month counts when ≥₹20,000 and ≥4 transactions of ₹1,500+ post in that calendar month.

**Benefits & targets:** lounges, perks, ticks for unlocked or used benefits (saved to `perks`, or to `localStorage` offline).

**Rewards** (`rewards/main`):

- KPI tiles: points worth (at the redemption picked per card), next expiry, redeemed this calendar year, cashback over the last 12 statements, points removed on the main points card.
- Points wallet: one row per points account with an editable balance, a "Redeem as" picker (₹ per point; the pick is remembered in the browser), worth with a mini bar, and when/where the balance was last updated.
- Redemptions: "Record a redemption" form (date, card, points, what you got, partner and partner points for transfers, ₹ value, use-by). Saving lowers the card balance; a transfer adds or tops up a partner row. Remove reverses it.
- Coming up to expire: points from `expiring` plus vouchers with a use-by date; estimated monthly lots after the first two are grouped.
- Which card for which spend (`routing`) and reminders (`watch`).
- Charts: points by statement (base vs bonus; tooltip with redeemed, removed and balance) and cashback by statement (one colour per `cashback.series`).
- Offline, balance edits and redemptions are kept in this browser only.

### 4.11 Trends (`#trends`)

- Month-over-month lines and bars across `months` (income, card spend, invested, saved, free cash).
- Goal balances over time (travel + vouchers, emergency).
- Interactive readouts.

### 4.12 To-do (`#todo`)

- `actions` for the selected month, sorted by due date, with amount.
- Ticking writes `actions/<id>.done` (offline: `localStorage`).
- Needs attention sits in its own box above the list (see 4.2): live checks, not records, so they clear by themselves.

### 4.13 Loans (`#loans`)

- One card per active loan: outstanding, EMI, ends, progress meter, and a status line from `rate`.
- The home-loan meter is gold.
- Closed loans appear as chips.
- Header: count active, total owed, total EMIs a month.

### 4.14 Insurance (`#insurance`)

- **Header:** policy count · life cover (Σ term cover) · health cover for you (Σ health cover excluding Parents) · what you pay a year (monthly × 12 + yearly).
- **Coming up:** next monthly term debit (from `prem_day`) and the next `renews` dates (max 4). Click a chip to scroll to and outline its card.
- **Policy cards:** cover, premium (/mo, /yr, /2 yrs, or ₹0 employer), pay-until or renews, and the card's main bar (term payment progress; health base/booster/safeguard split with legend). Everything else (notes, tips, members, nominee, features) sits under a collapsed "Details" link per card, which opens independently and stays open across re-renders.
- **Personal term card:**
  - Progress bar = premiums paid so far ÷ total premiums. Monthly count = months from the start to today, inclusive of this month's debit if past the debit day; total = (pay_until year − start year + 1) × 12.
  - "Began yearly ₹X incl. GST · now ₹Y/yr, no GST".
  - Tip when yearly payment would be cheaper. Yearly cost ≈ `prem_start / 1.18` (GST removed); saving = monthly × 12 − that.
  - Early-exit window line.
- **Health card:** split bar of base / booster / safeguard.
- **Premiums by year:** Health · Term · Combined buttons. Health and Term stack premium and GST; Combined stacks health + term (incl. GST) by financial year. Term `history` uses financial-year keys (e.g. year-1 annual, then monthly with 18% GST until GST was removed on 22 Sep 2025); a year with no term record is flagged, never guessed. Click a bar to pin it.
- Hovering a card dims the others.

### 4.15 Facts (`#facts`)

- Emergency-fund days = `emergency_fund ÷ ((card_net + emi) / 30)`.
- Travel-fund note.
- Net worth incl. home = latest total + `home_value` − `loans/home.outstanding`. Loans with `paid_by` are excluded, with a note.
- Editable home value.
- Life cover = `life_cover_personal + employer_cover_multiple × ctc_fixed` (CTC editable; kept per browser).

### 4.16 Savings accounts (`#savings`)

- Tiles: Total balance · Earmarked (what each account must hold; the whole emergency-fund balance) · Available balance (total − earmarked).
- Share bar: one segment per bank (hover/tap tooltip with ₹ and %); the legend shows ₹ and % and jumps to the card.
- One slim card per account (same soft tint for all): bank name and balance (borderless; click to edit, Enter saves), then the need label and one chip: "₹X above", "Short ₹X", "% · ₹X to go", "Top up by <date>", "All free". Tap the name for the detail line (need breakdown, updated date, change vs last month, note; `keep` edited there).
- EMI account: holds the next EMI from `emi_topup_day` until it is paid; optional locker fee (`settings.sbi_locker`) from `fund_by` until `until`. Bills shows "Locker fee: move to the EMI account" (tick `locker_paid`) and "Locker fee debited" (tick `locker_debited`).
- Locked accounts (need `locked`, e.g. a fixed deposit under a lien) count as earmarked and never as spare cash.
- Online, a typed balance saves to `bank/<id>` (bal, asof today, src "Typed in", hist for the month); offline it stays in the browser.

### 4.17 Tax (`#tax`)

- Uses the latest `tax/fy*` document. New regime (tax year 2026-27): salary for the year = `ytd_gross + monthly × months left + bonus` − ₹75,000 standard deduction; slab income adds dividends, savings interest and net non-equity short-term gains. Slabs 0–4L nil, then 5% steps per 4L to 24L, 30% above; 87A rebate to ₹12L; 4% cess.
- Capital gains: short-term losses set off first against slab-rate gains, then 20% equity STCG, then LTCG; LTCG 12.5% above ₹1.25L (meter of the exemption used and left). Intraday losses stay apart.
- KPIs: tax for the year, TDS so far (and by March), likely to pay / refund (advance tax flagged above ₹10K), last return refund. TDS-by-month bars (actual solid, expected striped). Past returns table, losses carried forward, "Still needed" list.
- Bonus and savings interest are editable (online to the tax doc, offline to the browser). The eye toggle masks the section. A tracker, not tax advice.

---

## 5. Refresh and maintenance SOP

### 5.1 Principles

1. Write data, never regenerate the page. A refresh only calls `ArtifactData` `set`/`update` (or the `db` API) on changed documents.
2. Pin every write to the version you read (`if_version`). On a conflict, re-read and redo; never overwrite.
3. Never invent numbers. If a source fails, keep the old value and add "(stale since …)" to that doc's `asof` or note.
4. Batch writes: one `batch` per refresh (up to 50 writes).
5. Update `settings/main.last_updated` and `last_updated_by` in the same batch.
6. Keep text short. Analyst notes are 3–7 plain sentences each.

### 5.2 Weekly portfolio refresh (Saturday or Sunday)

1. Read `invest/equity`, `us`, `mfret`, `meta`, `snapshot`, `results`, `earnings`, `watch`, `returns`, all `mf` docs, the latest `trend` doc and `settings/main`.
2. Pull holdings: broker for share counts and averages; fund platform or CAS for units and NAVs; US platform for US stocks; EPF, PPF and NPS balances.
3. Prices:
   - Last close for each stock (on Saturday/Sunday use Friday's close and say so).
   - 1Y change = latest close ÷ open of the monthly candle 12 months back − 1.
   - 3M change = latest close ÷ close 3 months back − 1.
   - 52-week high/low.
   - Nifty 50 and Nasdaq-100 (QQQ) the same way.
   - Fund 1Y/6M/3M/3Y returns and category rank; each fund's own benchmark 3M/6M/12M (`b3m`, `b6m`, `b1y`). Rebuild composite or unpublished benchmarks from component prices; keep `bname` and `bench_note`.
   - US stocks 3M/6M/1Y in USD and `us.bench` from QQQ.
   - Since-bought benchmarks (`bsince`): put each buy from `returns` into the benchmark on its own date; if that is not possible, keep the stored value.
4. Recompute:
   - Each stock: `value = shares × ltp`; `invested = shares × avg`; `pnl_pct`.
   - Weight = value ÷ direct-stock value excluding GoldBEES.
   - Totals and `meta.eq_value`.
   - US rows in INR and USD.
   - `mf` current and invested.
   - Snapshot components and `total`.
5. New buys or sells: append lots to `returns.lots` / `us.lots` and fund cash flows to `returns.mf[id].cfs`.
   - Dates and prices only from trade records (contract notes, order emails, allotment emails).
   - Unmatched changes go to `returns.pending`.
6. Results season: add newly declared results to `invest/results`, and recompute `earnings` for the current quarter only.
7. Rewrite `meta.notes_eq`, `notes_mf`, `notes_us` and `snapshot.notes` from the new numbers: at most 8 bullets each, one line (about 25 words) each, numbers first, no method talk.
8. Add `trend/<today>` = `{date, total, source: 'weekly refresh'}`.
9. Never write `invest/planreview` (only the page's "Record this review" does) and never drop a field you could not refresh.
10. Write everything in one batch; report total and change, equity vs Nifty, top movers, gaps vs targets, gold % of corpus, anything stale.

### 5.3 Monthly cash-flow update (after salary and statements)

1. Create or update `months/<YYYY-MM>`:
   - salary, other_income, sip, direct_equity
   - emi plus its interest/principal split (from the loan statement)
   - card_gross (bills paid), card_net (minus money others paid back), `other_credits`
   - ef_add, travel_add and the new balances
   - free_cash (salary-account balance after all bills)
   - status `open`; set the previous month to `closed`
   - one-line note
2. **Card statements:** for each new statement, append rows to `ccspend/tx-<card>-<FY>` with category indexes. Update `ccspend/meta.cards[card].months/bills/last_stmt/tx`, and `meta.to`/`asof`. Then update `cards/<card>.bills[due month]`.
3. **Loans:** update `outstanding` (and `emis_left`) after each EMI.
4. **Rewards:** add the new statement to `rewards/main.points.rows` and `cashback.rows`; update each programme's `bal`, `asof`, `src` and `expiring`. Keep redemptions the page recorded.
5. **Actions:** add next month's to-dos; mark done ones.
6. **Savings:** type each balance on the Savings page (or write `bank/<id>` bal, asof, src, hist). The emergency-fund account should match `months.emergency_fund`.
7. **Tax:** from the payslip update `tax/fy*` salary (`ytd_gross`, `ytd_to`) and `tds.months`; after any sale add capital-gains rows; once a year add the filed return to `returns` and set `refund_got` when it arrives.
8. State the bank floor in the summary: `travel_fund + bank_floor`, plus the crash figure `travel_fund + crash_floor`.

### 5.4 Documents to collect each month

- Credit-card statements, or exports from the card apps.
- Salary slip.
- Savings-account balances (one per account).
- Broker tradebook and tax P&L (after any sale).
- AIS/TIS once a quarter (dividends, TDS); last year's filed return once a year.
- Mutual-fund CAS (CAMS + KFintech).
- Home-loan statement.

Occasionally: EPF passbook, PPF/NPS statements, insurance renewal notices.

### 5.5 Annual rollovers

| When | Action |
|---|---|
| 1 April | Start `ccspend/tx-<card>-<new YYYY>` for every card. Start `ppf/<FY>` and `nps/<FY>` documents. The FY view of "invested by year" rolls automatically. |
| Each card anniversary (`year_start`) | Nothing to write; the page restarts that card's year itself. Check fee waivers. |
| Insurance renewal | Update `renews`, `prem_now`, `cover`, and add a `history` row with that year's premium and GST. |
| Salary revision | Update `ctc_fixed`, `epf_monthly`; the employer term cover follows. |
| Results season (quarterly) | New `invest/results.season`; move last quarter to `earnings.quarters` as Final. |
| Formal portfolio review | Update `equity.rows[].target`/`action`, `meta.review` (done, next, order, summary). Only with the owner's approval. |
| May and November | Half-yearly retirement review: after that week's refresh, open Retirement at 60, check "Today vs plan", and tap "Record this review" (one per month). |

### 5.6 What a refresh must never do

- Republish or edit the HTML.
- Change targets, decisions or SIP schedules without the owner's approval.
- Send email.
- Double-count US funds inside Indian MFs.

---

## 6. Friend onboarding and data intake protocol

The LLM runs this as a staged interview. Ask one stage at a time, confirm a summary at the end of each stage, then write that stage's records.

**Legend:**

- **[ASK]** the user must provide it.
- **[DOC]** ask for a document and extract it.
- **[CALC]** the LLM computes it; don't ask.
- **[LOOKUP]** the LLM looks it up (web/market data) and cites the source.

### Stage 0 — Setup and preferences

1. [ASK] Name to show in the title ("<Name>'s Personal Finance").
2. [ASK] Date of birth (for the retirement date). Retirement age, if not 60: this needs a code change.
3. [ASK] City (for context only) and preferred financial-year view (Apr–Mar or calendar).
4. [ASK] Which modules to use: Cards, Investments, Retirement, Insurance, Loans, Goals. Unused modules get empty collections, and their sections show "not loaded".
5. [ASK] Whether Notion is the record of truth (enables "Save this month" and weekly Notion sync) or the dashboard database alone.
6. [CALC] Create `settings/main` with defaults; fill as answers arrive.

### Stage 1 — Cards and spending

1. [ASK] List every credit card (bank + product).
2. [ASK] For each card: annual fee, fee-waiver spend, card anniversary month and day, statement cycle start day, payment due day, lifetime free (yes/no).
3. [LOOKUP] For each product: milestone rewards, lounge rules, quarterly/monthly bonus rules. Confirm with the user, since rules change often.
4. [DOC] Last 12 months of statements (PDF or app exports).
5. [CALC] Parse transactions into `[date, merchant, categoryIndex, amount, billMonth]`, with refunds negative. Exclude payments, cashback, fees, interest and EMI principal.
6. [CALC] Categorise with the 18-category list. Ask only about merchants you can't place.
7. [CALC] Write `ccspend/tx-<card>-<FY>` (April split), `ccspend/meta`, `cards/<id>` (bills by due month), and `perks/<id>` (targets from step 3).
8. [ASK] Which card spends are paid back by someone else (so own spend = net).
9. [ASK] Points balances and expiry per programme (from each card app), and how they like to redeem. [LOOKUP] ₹ per point for each redemption route. [CALC] Write `rewards/main`; cards that earn into one points account get one row.

### Stage 2 — Investments

1. [ASK] Broker(s) for Indian stocks; [DOC] holdings export plus tradebook (as far back as available).
2. [ASK] Mutual-fund platform(s); [DOC] consolidated account statement (CAS, from CAMS + KFintech).
3. [ASK] For each fund: goal (Retirement / Car / other), monthly SIP and SIP date.
4. [ASK] US stocks platform; [DOC] holdings plus order history (USD amounts and prices).
5. [ASK] EPF balance (and the EPS pension share from the passbook), PPF balance and yearly deposits, NPS balance and contributions.
6. [ASK] Stock targets: does the user have target weights / sleeves (Core, Satellite, Specials)? If not, leave targets "—" and skip the targets view.
7. [LOOKUP] Prices, 1Y/3M changes, 52-week high/low, fund returns and ranks, Nifty and Nasdaq-100.
8. [CALC] Build `invest/equity`, `us`, `mf`, `mfret`, `snapshot`, `returns` (lots and cash flows), `flows` (monthly buys/sells from the tradebook and CAS), `meta`, `ppf`, `nps`, and the first `trend` point.
9. [CALC] Set `mf.bucket` per fund: equity, mixed (multi-asset / hybrid), debt, or us.

### Stage 3 — Salary, cash and loans

1. [ASK] Monthly take-home salary and other income (rent, interest, freelance; if any).
2. [ASK] Fixed annual CTC (for the employer life cover) and the employer cover multiple (often 3×).
3. [ASK] Monthly EPF contribution (you + employer, excluding EPS).
4. [ASK] Savings accounts: for each bank account, its role and what it must hold (salary floor, petty cash, emergency fund, EMI money, a deposit held for someone, or nothing), plus the current balance. Any yearly charge (e.g. a locker fee) and when it is debited. → `bank/*`, `settings.axis_float`, `settings.emi_topup_day`, `settings.sbi_locker`.
4a. [DOC] Tax: latest payslip (April-to-date gross and TDS), AIS/TIS, capital-gains reports, last filed returns. [CALC] Write `tax/fy<YYYY-YY>`.
4b. [ASK] Cash flow: expected raise (% and the month it is for), any SIP step-up and from when, planned monthly stock buying, and whether other income has an end date. → `settings.cf`.
5. [ASK] Bank floor (minimum balance after bills), crash floor, small card float.
6. [ASK] Stock-buying rules, if any: regular threshold, regular monthly cap, dip cap. Defaults are offered if none.
7. [ASK] Loans: for each, name, lender, original amount, outstanding, EMI, rate, end, and who pays it. [DOC] Latest home-loan statement.
8. [ASK] Home market value estimate (optional).
9. [ASK] Goals: name, amount, deadline, where the money sits, expected inflows, vouchers.
10. [CALC] Write `months/<current>` (and past months if statements allow), `loans/*` (home loan id `home`), `targets/*`, the `settings/main` fields, and starting `actions`.

### Stage 4 — Insurance

1. [ASK] Term policies (personal): insurer, plan, policy number, cover, start date, premium-paying term, premium and frequency, debit day, nominee(s) with shares, riders. [DOC] Policy schedule.
2. [ASK] Employer term cover: formula (× CTC), current cover, policy year, nominee(s).
3. [ASK] Health policies (self/family): insurer, plan, policy number, base sum insured plus boosters, co-pay/room rules, renewal date, premium, members. [DOC] Policy schedule plus past renewal receipts (for premium history and GST).
4. [ASK] Employer group medical: cover, members, renewal month, any top-up.
5. [ASK] Parents' policies: cover, renewal, premium, who pays.
6. [CALC] Write `insurance/*` with `history` rows (premium and GST per year). Compute the "switch to yearly" saving when a monthly mode has a known annual premium.

### Stage 5 — Build, verify and hand over

1. [CALC] Seed the database, publish the page from the template code (name changed, no `__SNAPSHOT__` script), and declare capabilities (section 1.3).
2. [CALC] Verify:
   - snapshot total = Σ components;
   - equity value = Σ rows;
   - card meta months = Σ transactions per month;
   - loan outstanding matches the statement;
   - the page loads with no errors;
   - the offline download renders the same.
3. [ASK] Walk the user through each section; collect corrections.
4. [CALC] Set up the weekly and monthly refresh routines (section 5) as scheduled tasks, if the platform supports it.

---

## 7. Checklist before calling a build done

- [ ] Every section renders with real data and with empty collections (no crashes).
- [ ] The offline download opens and behaves the same: charts, tabs, ticks, eye toggle.
- [ ] Phone width (400px): no horizontal scroll; sidebar becomes the Menu button.
- [ ] Light and dark mode are both readable.
- [ ] The eye toggle hides salary and investment figures, but not card spending or bills.
- [ ] Charts respond to hover, tap and arrow keys; readouts update.
- [ ] Totals reconcile across Overview, Wealth mix and Investments.
- [ ] Theme switch: Light by default, Dark readable, choice remembered.
- [ ] Performance vs benchmark: every fund has its own index; the 3M / 6M / 12M / Since bought buttons all draw.
- [ ] Half-yearly check renders with no reviews, one review and several; the Retirement panel does not scroll sideways at 400px.
- [ ] Spare cash = Σ free money per account; the "Move to" line lists only accounts with free money; the Savings tiles and Net worth card agree with it.
- [ ] Tax: totals match a hand calculation for the sample; editing bonus or interest updates the estimate; works offline.
- [ ] Cash flow: a salary or other-income edit in Cash flow shows in Income and back; a forecast-month override changes that month only; adding, editing and deleting a receipt works online and offline; a top-up of the "Restore minimum buffer" amount clears that card and lifts every projection; a positive average can show ₹0 spending room when one month breaches the minimum.
- [ ] Rewards: wallet total = Σ worth; recording and removing a redemption moves the balance both ways.
