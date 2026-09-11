"""위성·지구관측 public scene: reviewed facilities, observed events, model orbit elements."""
from .store import ROOT,read_json
from .events_data import read
from .acquire import stamp
from .sauron_data import QUAKES,STATIONS


def build(d):
    data={}
    for key in ['quakes','stations']:
        path=d.resource('sauron/'+key+'.json.gz');data[key]=read(path) if path.exists() else {}
    sites=read_json(ROOT/'config/satellite_sites.json')
    p=d.resource('sauron/collection.json.gz');collection=read(p) if p.exists() else {}
    return dict(type='sauron',group='위성·지구관측',title='위성·지구관측 · 3D 지구 관측',
        sites=sites['sites'],quakes=data['quakes'].get('data',{}).get('events',[]),
        quake_generated=data['quakes'].get('data',{}).get('generated_at'),
        elements=data['stations'].get('data',[]),stations_retrieved=data['stations'].get('retrieved_at'),
        collection=collection.get('sources',[]),sources=[QUAKES,STATIONS],
        config=dict(home=[30,18,26000000],min_magnitude=2.5,orbit_tick_ms=3000,max_epoch_age_days=7,
                    basemap='natural',osm_url='https://tile.openstreetmap.org/'))


def views(d,obj):
    obj['sections']=[s for s in obj['sections'] if s.get('group')!='위성·지구관측'];obj['sections'].append(build(d));obj['generated_at']=stamp()
    obj['missing']=[m for m in obj['missing'] if not m.startswith('위성·지구관측의')]
    obj['missing'].append('위성·지구관측의 Google 실사3D는 별도 키가 필요합니다. Wikipedia 지명은 문서 대표 좌표이며 주소 검색과 다릅니다. 지진은 PC 수집 시점의 관측이고 위성 위치는 궤도 모델 계산입니다.')
    return obj
