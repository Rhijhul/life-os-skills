# Personal Finance Dashboard: skill package

A portable skill for building your own interactive personal-finance dashboard with an AI assistant. It covers cards, spending, investments, retirement, loans and insurance.

## How to use it

1. **Claude:** add the `personal-finance-dashboard` folder as a skill (Settings → Skills, upload the zip). Then say "Build my personal finance dashboard".
2. **Other assistants:** attach `SKILL.md` and the files it lists. Ask the assistant to follow `SKILL.md`.
3. **Preview:** open `assets/sample-dashboard.html` in Chrome or Safari to see the finished result with a sample profile.

The package holds only made-up sample data. Your own figures go into your own dashboard's database, never into this package.

## What the assistant will ask for

It works in five stages:

1. Setup
2. Cards: statements for the last 12 months
3. Investments: broker holdings and tradebook, mutual-fund statement (CAS), US holdings, EPF/PPF/NPS balances
4. Salary, cash and loans
5. Insurance: policy schedules

Connectors such as your broker, an investment aggregator, email or Notion can speed this up. They are optional.
