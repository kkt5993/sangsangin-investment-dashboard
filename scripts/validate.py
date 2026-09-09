"""Validate the public allowlist and static links without accessing any network."""
from pathlib import Path
import json
import re
import math
from datetime import date
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
assert len(mods)==25
assert len({m['id'] for m in mods})==25
for m in mods:
    assert m['purpose'] and m['build'] and m['checks'] and m['gap']
    assert (ROOT/'research/modules'/f"{m['id']}.md").is_file()
for path in ROOT.rglob('*'):
    if not path.is_file() or any(p in path.parts for p in ['.git','__pycache__','.venv','node_modules']):continue
    assert path.suffix not in {'.pdf','.mp4','.duckdb','.key','.pem'},str(path)
    text=path.read_text(encoding='utf-8')
    for pattern in [r'AIza[\w-]{30,}',r'gh[pousr]_[A-Za-z0-9]{20,}',r'github_pat_[A-Za-z0-9_]{20,}',r'C:\\Users\\',r'127\.0\.0\.1:8799']:
        if re.search(pattern,text):errors.append('Disallowed content in '+str(path.relative_to(ROOT)))
    if path.suffix=='.md':
        for link in re.findall(r'\]\(([^)]+)\)',text):
            if not link.startswith(('http:','https:','#','mailto:')) and not (path.parent/link.split('#')[0]).exists():errors.append('Broken Markdown link '+str(path.relative_to(ROOT))+' -> '+link)
data_dir=ROOT/'docs/data'
def strict_load(path):
    def bad(value):raise ValueError('Invalid JSON numeric constant '+value)
    return json.loads(path.read_text(encoding='utf-8'),parse_constant=bad)

def verify_points(series,as_of):
    points=series['points']
    dates=[p[0] for p in points]
    assert dates==sorted(set(dates)), 'Unordered or duplicate chart dates'
    assert all(date.fromisoformat(d)<=date.fromisoformat(as_of) for d in dates), 'Future chart point'
    assert all(isinstance(p[1],(int,float)) and math.isfinite(p[1]) for p in points), 'Nonfinite chart point'
    if dates:
        assert series['start']<=dates[0]<=dates[-1]<=series['end']

rs=strict_load(data_dir/'rs.json')
momentum=strict_load(data_dir/'momentum.json')
assert rs['as_of']==momentum['as_of']
assert len(rs['pairs'])==35 and len({p['id'] for p in rs['pairs']})==35
assert sum(p['z'] is not None for p in rs['pairs'])==rs['coverage']['pairs']
for p in rs['pairs']:
    if p['z'] is None:assert p['reason']
    else:
        assert math.isfinite(p['z']) and p['as_of']<=rs['as_of']
        s=rs['series'][p['id']]
        verify_points(s,rs['as_of'])
        assert s['guides']==[-2,-1,0,1,2]
        assert abs(s['points'][-1][1]-p['z'])<.00001
assert len(momentum['assets'])==32 and len(momentum['sectors'])==24
assert sum(a['returns']['3M'] is not None for a in momentum['assets'])==momentum['coverage']['assets']
assert len(set(a['as_of'] for a in momentum['assets'] if a['as_of']))<=1
assert len(momentum['chart_pairs'])<=16 and len(set(momentum['chart_pairs']))==len(momentum['chart_pairs'])
for pair in momentum['chart_pairs']:
    for horizon in ['3','6']:
        s=momentum['curves'][pair][horizon]
        verify_points(s,momentum['as_of'])
        assert s['guides']==[0]
        assert s['points'][0][1]==0 and abs(s['points'][-1][1]-s['last'])<.00001
for d in [rs,momentum]:
    assert d['schema_version']==1 and d['status']=='partial'
    assert all(re.fullmatch('[a-f0-9]{64}',q['sha256']) for q in d['quality'] if q['status']=='ok')
assert sum(p.stat().st_size for p in data_dir.iterdir() if p.is_file()) < 6*1024*1024,'Public snapshot budget exceeded'
if errors:raise SystemExit('\n'.join(errors))
print('PASS: 25 guides, links, public content, strict JSON, coverage, date alignment, curve anchors, hashes and size; offline.')
