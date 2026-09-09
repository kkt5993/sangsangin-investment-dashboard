"""Validate the public allowlist and static links without accessing any network."""
from pathlib import Path
import json
import re
from html.parser import HTMLParser

ROOT=Path(__file__).resolve().parents[1]
errors=[]
class Links(HTMLParser):
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key in ('src','href') and value and not value.startswith(('http:','https:','#','data:','mailto:')):
                if not (ROOT/'docs'/value.split('#')[0]).is_file():errors.append('Missing asset '+value)

Links().feed((ROOT/'docs/index.html').read_text(encoding='utf-8'))
payload=(ROOT/'docs/modules.js').read_text(encoding='utf-8')
mods=json.loads(payload.removeprefix('const MODULES = ').rstrip().removesuffix(';'))
assert len(mods)==26
assert len({m['id'] for m in mods})==26
for m in mods:
    assert m['purpose'] and m['build'] and m['checks'] and m['gap']
    assert (ROOT/'research/modules'/f"{m['id']}.md").is_file()
for path in ROOT.rglob('*'):
    if not path.is_file() or '.git' in path.parts or '__pycache__' in path.parts:continue
    assert path.suffix not in {'.pdf','.mp4','.duckdb','.key','.pem'},str(path)
    text=path.read_text(encoding='utf-8')
    for pattern in [r'AIza[\w-]{30,}',r'gh[pousr]_[A-Za-z0-9]{20,}',r'github_pat_[A-Za-z0-9_]{20,}',r'C:\\Users\\',r'127\.0\.0\.1:8799']:
        if re.search(pattern,text):errors.append('Disallowed content in '+str(path.relative_to(ROOT)))
    if path.suffix=='.md':
        for link in re.findall(r'\]\(([^)]+)\)',text):
            if not link.startswith(('http:','https:','#','mailto:')) and not (path.parent/link.split('#')[0]).exists():errors.append('Broken Markdown link '+str(path.relative_to(ROOT))+' -> '+link)
if errors:raise SystemExit('\n'.join(errors))
print('PASS: 26 modules, all local links, public file/content checks; no network calls.')
