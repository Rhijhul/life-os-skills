#!/usr/bin/env python3
"""Check a dashboard dataset before seeding or embedding it.

Usage: python3 validate_data.py my-data.json
Exit code 1 when an error is found. Warnings do not fail."""
import json, sys, re
from collections import defaultdict

d = json.load(open(sys.argv[1], encoding='utf-8'))
E, W = [], []
err, warn = E.append, W.append
COLLS = ['months', 'targets', 'cards', 'actions', 'mf', 'loans', 'settings', 'ppf', 'nps', 'invest', 'perks', 'ccspend', 'insurance', 'trend', 'rewards', 'bank', 'tax']
for c in COLLS:
    if c not in d: warn(f'collection "{c}" missing (its section will show as not loaded)')
st = (d.get('settings') or {}).get('main')
if not st: err('settings/main is required')
else:
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(st.get('birth', ''))): err('settings.main.birth must be YYYY-MM-DD')
for k, m in (d.get('months') or {}).items():
    if not re.fullmatch(r'\d{4}-\d{2}', k): err(f'months/{k}: id must be YYYY-MM')
    for f in ('salary', 'card_net', 'free_cash'):
        if m.get(f) is not None and not isinstance(m[f], (int, float)): err(f'months/{k}.{f} must be a number')
    if 'rent' in m: warn(f'months/{k} uses "rent"; this template reads "other_income"')
loans = d.get('loans') or {}
if loans and 'home' not in loans: warn('no loans/home: home-loan tiles, prepayment table and EMI bill will be empty')
inv = d.get('invest') or {}
eq = (inv.get('equity') or {}).get('rows') or []
snap = inv.get('snapshot') or {}
comps = snap.get('components') or []
if comps:
    tot = sum(c.get('value') or 0 for c in comps)
    if abs(tot - (snap.get('total') or 0)) > 2: err(f'snapshot.total {snap.get("total")} != sum of components {round(tot)}')
    eqc = next((c for c in comps if c.get('key') == 'eq'), None)
    if eqc and eq and abs(eqc['value'] - sum(r.get('value') or 0 for r in eq)) > 2: err('snapshot eq component != sum of invest/equity rows')
nongold = [r for r in eq if r.get('ticker') != 'GOLDBEES']
if nongold:
    w = sum(r.get('weight') or 0 for r in nongold)
    if abs(w - 100) > 0.6: warn(f'stock weights add to {w:.2f}% (should be ~100%, excluding GoldBEES)')
for bid, b in (d.get('bank') or {}).items():
    if not b.get('name'): err(f'bank/{bid}: name is required')
    if b.get('need') not in (None, 'floor', 'float', 'target', 'emi', 'hold', 'locked'): err(f'bank/{bid}.need must be floor|float|target|emi|hold|locked|null')
    if b.get('need') == 'emi' and b.get('loan', 'home') not in loans: warn(f'bank/{bid}: loan "{b.get("loan", "home")}" not found in loans')
    if b.get('need') == 'target' and b.get('target', 'ef') not in (d.get('targets') or {}): warn(f'bank/{bid}: target "{b.get("target", "ef")}" not found in targets')
    if b.get('need') == 'hold' and b.get('keep') is None: warn(f'bank/{bid}: need "hold" without keep')
    if b.get('bal') is not None and not isinstance(b['bal'], (int, float)): err(f'bank/{bid}.bal must be a number')
if not any(b.get('need') == 'floor' for b in (d.get('bank') or {}).values()) and d.get('bank'): warn('no bank account has need "floor": Cash flow needs the salary account to draw its buffer')
for iid, e in (d.get('inflows') or {}).items():
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(e.get('date', ''))): err(f'inflows/{iid}.date must be YYYY-MM-DD')
    if not isinstance(e.get('amt'), (int, float)) or e['amt'] <= 0: err(f'inflows/{iid}.amt must be a positive number')
    if e.get('status') not in ('actual', 'expected'): err(f'inflows/{iid}.status must be actual|expected')
    if e.get('covers_card') and not re.fullmatch(r'\d{4}-\d{2}', str(e.get('pay_m', ''))): err(f'inflows/{iid}: covers_card needs pay_m YYYY-MM')
cf = (st or {}).get('cf') or {}
if cf.get('sip_step_from') and not re.fullmatch(r'\d{4}-\d{2}', str(cf['sip_step_from'])): err('settings.main.cf.sip_step_from must be YYYY-MM or empty')
for k in (cf.get('ovr') or {}):
    if not re.fullmatch(r'\d{4}-\d{2}', k): err(f'settings.main.cf.ovr: key {k} must be YYYY-MM')
for tid, t in (d.get('tax') or {}).items():
    if not re.fullmatch(r'fy\d{4}-\d{2}', tid): err(f'tax/{tid}: id must be fy<YYYY-YY>')
    if t.get('regime') not in ('new', 'old'): warn(f'tax/{tid}.regime should be new or old')
    if not isinstance((t.get('salary') or {}).get('ytd_gross'), (int, float)): warn(f'tax/{tid}.salary.ytd_gross missing')
for fid, f in (d.get('mf') or {}).items():
    if fid != 'usstocks' and f.get('bucket', 'equity') not in ('equity', 'mixed', 'debt', 'us'): err(f'mf/{fid}.bucket must be equity|mixed|debt|us')
cc = d.get('ccspend') or {}
meta = cc.get('meta') or {}
if cc and not meta: err('ccspend/meta missing')
sums = defaultdict(lambda: defaultdict(float))
for k, doc in cc.items():
    if not k.startswith('tx-'): continue
    m = re.fullmatch(r'tx-([a-z0-9_]+?)(?:-(\d{4}))?', k)
    if not m: err(f'ccspend/{k}: id must be tx-<card>-<YYYY>'); continue
    card, yr = m.group(1), m.group(2)
    if not yr: warn(f'ccspend/{k}: prefer one record per card per card-year (tx-{card}-<YYYY>)')
    for row in doc.get('rows', []):
        if len(row) != 5: err(f'ccspend/{k}: rows must be [date, merchant, catIndex, amount, billMonth]'); break
        dt = row[0]
        if yr:
            y, mo = int(dt[:4]), int(dt[5:7]); fy = y if mo >= 4 else y - 1
            if fy != int(yr): err(f'ccspend/{k}: {dt} belongs in tx-{card}-{fy}')
        sums[card][dt[:7]] += row[3]
for card, months in (meta.get('cards') or {}).items():
    for mo, v in (months.get('months') or {}).items():
        got = sums[card].get(mo, 0)
        if abs(got - v) > 1: warn(f'ccspend meta {card} {mo}: {v} vs transactions {round(got, 2)}')
for pid, p in (d.get('insurance') or {}).items():
    if p.get('kind') not in ('term', 'health'): err(f'insurance/{pid}.kind must be term|health')
    if p.get('scope') not in ('Personal', 'Work', 'Parents'): err(f'insurance/{pid}.scope must be Personal|Work|Parents')
print('\n'.join(['ERROR  ' + x for x in E] + ['warn   ' + x for x in W]) or 'OK')
print(f'{len(E)} error(s), {len(W)} warning(s)')
sys.exit(1 if E else 0)
