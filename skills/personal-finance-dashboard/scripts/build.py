#!/usr/bin/env python3
"""Build the publishable dashboard page from the source template.

Usage:
  python3 build.py [--name "Riya"] [--src ../assets/dashboard.core.html] [--out dashboard.html]

- Optionally puts the owner's name in the title and sidebar.
- Embeds the page's own source (base64) so "Download offline copy" works.
- Stamps the build time.
The output reads all figures from the page database (no data inside)."""
import argparse, base64, datetime, os, re, sys

here = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('--name', default='', help="Optional first name: title becomes \"<Name>'s Personal Finance\" (default \"My Personal Finance\")")
ap.add_argument('--src', default=os.path.join(here, '..', 'assets', 'dashboard.core.html'))
ap.add_argument('--out', default='dashboard.html')
ap.add_argument('--core-out', default=None, help='Also save the renamed source (keep it; it is what you edit next time)')
a = ap.parse_args()

src = open(a.src, encoding='utf-8').read()
name = a.name.strip()
if name and not re.fullmatch(r"[\w .\-]{1,40}", name):
    sys.exit('Use a plain name (letters, spaces, dots, hyphens).')
if name:
    src = src.replace("My Personal Finance (offline)", name + "\\'s Personal Finance (offline)").replace("My Personal Finance", name + "'s Personal Finance")
if a.core_out:
    open(a.core_out, 'w', encoding='utf-8').write(src)
b64 = base64.b64encode(src.encode('utf-8')).decode()
out = src.replace("const PAGE_BUILT = '';/*@@BUILT@@*/", "const PAGE_BUILT = '" + datetime.datetime.now(datetime.timezone.utc).isoformat() + "';")
pub = out.replace("const SELF_B64 = '';/*@@SELF@@*/", "const SELF_B64 = '" + b64 + "';")
if pub == out:
    sys.exit('SELF_B64 placeholder not found: is --src the unbuilt source?')
open(a.out, 'w', encoding='utf-8').write(pub)
script = re.findall(r'<script>(.*?)</script>', pub, re.S)[0]
open(os.path.splitext(a.out)[0] + '.check.js', 'w', encoding='utf-8').write(script)
print(f'Wrote {a.out} ({len(pub):,} bytes). Syntax check: node --check {os.path.splitext(a.out)[0]}.check.js')
