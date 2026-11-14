#!/usr/bin/env python3
"""Make a standalone, offline HTML file: built page + data embedded as window.__SNAPSHOT__.

Usage:
  python3 make_offline.py --page dashboard.html --data my-data.json --out My-Finance.html [--title "Riya's Personal Finance"] [--template]

Use this when the assistant cannot host a page with a database, or to share a frozen copy.
--template keeps the "Download offline copy" button visible (as in the sample)."""
import argparse, json, re
ap = argparse.ArgumentParser()
ap.add_argument('--page', required=True, help='Output of build.py')
ap.add_argument('--data', required=True, help='JSON: {collection: {docId: {...}}}')
ap.add_argument('--out', required=True)
ap.add_argument('--title', default='Personal Finance')
ap.add_argument('--label', default='saved copy', help='Shown as "Snapshot saved <label>"')
ap.add_argument('--template', action='store_true')
a = ap.parse_args()
page = re.sub(r'<title>[\s\S]*?</title>', '', open(a.page, encoding='utf-8').read(), count=1)
data = json.load(open(a.data, encoding='utf-8'))
snap = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
flags = 'window.__HIDE__=false;' + ('window.__TEMPLATE__=true;' if a.template else '')
doc = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
       '<title>' + a.title.replace('<', '') + '</title><style>html{color-scheme:light}body{margin:0;font-size:14px}img{max-width:100%}[hidden]{display:none!important}</style></head><body>\n'
       '<script>window.__SNAPSHOT__=' + snap + ';window.__SNAPSHOT_DATE__=' + json.dumps(a.label) + ';' + flags + '</script>\n' + page + '\n</body></html>')
open(a.out, 'w', encoding='utf-8').write(doc)
print(f'Wrote {a.out} ({len(doc):,} bytes)')
