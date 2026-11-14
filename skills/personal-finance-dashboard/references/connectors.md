# Data sources and connectors

Every module works from documents the user uploads. Connectors (MCP servers or app integrations) only save effort.

Before the interview:
1. Check which connectors the current agent has.
2. Offer the useful ones.
3. Fall back to documents for anything else.

Connectors read data. They never send email, place orders or change accounts as part of this skill.

## By module

| Module | Best source | Connector options (if available) | Document fallback |
|---|---|---|---|
| Indian stocks | Broker holdings plus tradebook | Broker MCP (e.g. Zerodha Kite: holdings, trades); portfolio aggregator (e.g. INDmoney: holdings, prices) | Holdings export (CSV/XLSX) and tradebook from the broker console |
| Stock prices, 1Y/3M change, 52-week range | Market data | Broker or aggregator quote and OHLC tools; web search | Ask the user for the latest close (last resort) |
| Mutual funds | Consolidated account statement (CAS) | Aggregator MF holdings and fund details (returns, rank); fund-platform MCP (e.g. Groww) | CAMS + KFintech CAS PDF; platform holdings export |
| US stocks | Platform holdings plus order history | Aggregator US holdings and US OHLC | Order confirmation emails; holdings screenshot |
| EPF / PPF / NPS | Passbook and statements | Aggregator (EPF, PPF, NPS asset types) | EPF passbook PDF; bank PPF statement; NPS CRA statement |
| Credit cards | Monthly statements | Mail connector (e.g. Gmail) to find statement and "bill generated" emails, read-only; Drive connector for saved statements | Statement PDFs (often password-protected; ask the user for unlocked copies or app exports) |
| Salary and bank | Salary slip; account balances | Mail connector for salary-credit alerts | Salary slip; balance screenshots |
| Loans | Loan statement | Mail connector for EMI and statement emails | Latest loan statement |
| Insurance | Policy schedule; renewal receipts | Mail connector or Drive for policy PDFs | Policy schedule PDFs and premium receipts |
| Notes, record of truth (optional) | The user's notes app | Notion MCP: read pages, create the monthly "Save this month" page | Not needed |
| Scheduling (optional) | Agent's scheduler | Scheduled-task tools, for the weekly refresh | A checklist the user pastes each week |

## Connector rules

- **Read first.** Use connector data only after confirming that the account belongs to the user.
- **Never store credentials, account numbers or card numbers** in the dashboard. A card's last 4 digits are the most that may be shown, and only if the user wants them.
- **Mail connectors:** search narrowly, by sender plus subject plus date range. Never send mail. If anything has to go out, create a draft for the user.
- **Respect rate limits.** For example, OHLC calls often count double. Batch and pause.
- **When a connector fails,** keep the previous value, mark it stale with its date in that record's `asof` or `note`, and say so in the summary.
- **Platform calls:** when the page itself calls a connector (only "Save this month to Notion" does), declare it in the page's capabilities with the exact tool name.

## Page capabilities (hosted on claude.ai)

```json
{ "db": {}, "downloads": true, "user": {},
  "mcp": { "servers": [ { "server": "Notion", "tools": ["notion-create-pages"] } ] } }
```

- Drop `mcp` if the user doesn't use Notion.
- On other hosts, provide the same three things:
  - a document store the page can read and write: `collection(name).onSnapshot(cb)` and `doc(path).update(patch)` (see SOP section 1.2);
  - a way to save a file;
  - an owner check.
- Otherwise use the offline file (`scripts/make_offline.py`).
