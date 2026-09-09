"""One small licensed world-atlas download; derive coastline coordinates locally."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.store import DATA,ROOT,write_json
from pipeline.acquire import get_bytes
raw=DATA/'world-atlas-110m.json'
if not raw.exists():raw.write_bytes(get_bytes('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json'))
top=json.loads(raw.read_text(encoding='utf8'));arcs=[]
for arc in top['arcs']:
    x=y=0;pts=[]
    for dx,dy in arc:
        x+=dx;y+=dy;pts.append([round(x*top['transform']['scale'][0]+top['transform']['translate'][0],3),round(y*top['transform']['scale'][1]+top['transform']['translate'][1],3)])
    arcs.append(pts)
write_json(ROOT/'docs/data/coastlines.json',dict(source='Natural Earth 4.1.0 via world-atlas 2 (ISC)',arcs=arcs))
print('Derived coastline bytes',(ROOT/'docs/data/coastlines.json').stat().st_size)
