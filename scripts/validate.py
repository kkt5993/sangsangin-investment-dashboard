"""Validate the public allowlist and static links without accessing any network."""
from pathlib import Path
import json
import re
import math
import html
import unicodedata
import sys
from urllib.parse import unquote,urlsplit
from datetime import date
from html.parser import HTMLParser

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pipeline.public_assets import pdf_assets,ocr_assets,globe_assets,font_assets
pdf_binary=pdf_assets(ROOT/'docs',ROOT/'config/pdfjs_vendor.json')|ocr_assets(ROOT/'docs',ROOT/'config/ocr_vendor.json')|globe_assets(ROOT/'docs',ROOT/'config')
font_binary=font_assets(ROOT/'docs',ROOT/'config/ui_font_vendor.json')
errors=[]
class Links(HTMLParser):
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key in ('src','href') and value and not value.startswith(('http:','https:','#','data:','mailto:')):
                if not (ROOT/'docs'/unquote(urlsplit(value).path)).is_file():errors.append('Missing asset '+value)

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
    if path in pdf_binary or path in font_binary:continue
    if path.suffix=='.png':
        from PIL import Image
        assert path.parent==ROOT/'docs/data/satellite' and re.fullmatch(r'ST_[A-Z_]+-(rgb|ndvi)\.png',path.name)
        with Image.open(path) as image:
            assert image.format=='PNG' and image.mode=='RGBA' and image.size==(400,400)
            assert not image.info,'Satellite PNG must not contain ancillary metadata'
            image.verify()
        continue
    text=path.read_text(encoding='utf-8')
    if path.is_relative_to(ROOT/'docs'):
        public_text=unicodedata.normalize('NFKC',html.unescape(unquote(text)))
        public_text=re.sub(r'\\u([0-9a-fA-F]{4})',lambda m:chr(int(m[1],16)),public_text)
        if re.search(r'lee[\s_-]*chang[\s_-]*woo|chang[\s_-]*woo[\s_-]*lee|이\s*창\s*우|aragorn-investium\.pages\.dev',public_text,re.I):
            errors.append('Excluded reference-creator attribution in '+str(path.relative_to(ROOT)))
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
highs=momentum['new_highs']
assert highs['as_of']==momentum['as_of'] and [g['universe'] for g in highs['groups']]==['us100','kospi200']
for g in highs['groups']:
    assert g['selected']==len(g['rows']) and len({r['symbol'] for r in g['rows']})==g['selected']
    if g['status']=='missing':
        assert not g['rows'] and g['reason'];continue
    assert g['membership_as_of']<=highs['as_of'] and len(g['members'])==g['eligible']
    assert g['high_eligible']==sum(r['reason'] is None for r in g['members'])
    assert set(r['symbol'] for r in g['members'])|set(r['symbol'] for r in g['excluded'])
    assert len(set(r['symbol'] for r in g['members'])|set(r['symbol'] for r in g['excluded']))==g['expected']
    for r in g['rows']:
        assert 65<=r['rs']<=99 and -5<=r['from_high']<=.00001 and r['high52']>=r['price']-.00001
        assert abs(r['from_high']-(r['price']/r['high52']-1)*100)<.0001
        assert r['high_window_start']<=r['high_date']<=r['as_of']<=highs['as_of']
        assert len(r['spark'])==44 and r['spark'][-1]==[r['as_of'],r['price']]
        assert [p[0] for p in r['spark']]==sorted({p[0] for p in r['spark']})
        assert r['high_window_start']<=r['spark'][0][0] and all(math.isfinite(p[1]) and p[1]>0 for p in r['spark'])
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
if errors:raise SystemExit('\n'.join(errors))
print('PASS: 25 guides, links, public content, strict JSON, coverage, date alignment, curve anchors, hashes and size; offline.')
