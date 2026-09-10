"""Offline scientific raster derivatives and the complete facility view contract."""
import hashlib
import io
import numpy as np
from .store import ROOT
from .satellite_data import unpack, registry, derived, site_signature, usable


def images(arrays, scene, rgb_max=.3):
    from PIL import Image
    from affine import Affine
    from rasterio.transform import array_bounds, from_bounds
    from rasterio.warp import transform_bounds, reproject, Resampling
    rgb, ndvi, stats = derived(arrays, scene['assets'])
    source_transform = Affine(*scene['transform'])
    native_bounds = array_bounds(scene['height'],scene['width'],source_transform)
    bounds = transform_bounds(scene['crs'],'EPSG:3857',*native_bounds,densify_pts=21)
    target_transform = from_bounds(*bounds,400,400)
    def project(data, method):
        target=np.full((data.shape[0],400,400),np.nan,np.float32)
        reproject(data,target,src_transform=source_transform,src_crs=scene['crs'],src_nodata=np.nan,
                  dst_transform=target_transform,dst_crs='EPSG:3857',dst_nodata=np.nan,resampling=method)
        return target
    # Nearest-neighbour preserves masked pixels and the fixed NDVI interpretation.
    rgb = project(rgb,Resampling.nearest); ndvi = project(ndvi[None],Resampling.nearest)[0]
    valid_rgb=np.isfinite(rgb).all(axis=0)
    if not .1 <= rgb_max <= 1:
        raise ValueError('Invalid fixed RGB display range')
    rgb8=(np.clip(np.nan_to_num(rgb,nan=0),0,rgb_max)/rgb_max)**(1/2.2)
    rgb8=np.moveaxis(np.rint(rgb8*255).astype(np.uint8),0,2)
    rgb8=np.dstack([rgb8,valid_rgb.astype(np.uint8)*255])
    stops=np.array([-1,0,.3,.6,1]); colors=np.array([[34,95,160],[211,195,165],[210,207,109],[92,150,72],[16,80,50]])
    nd=np.nan_to_num(ndvi,nan=0); nd8=np.stack([np.interp(nd,stops,colors[:,i]) for i in range(3)],axis=2).astype(np.uint8)
    nd8=np.dstack([nd8,np.isfinite(ndvi).astype(np.uint8)*255]); out={}
    for key,value in [('rgb',rgb8),('ndvi',nd8)]:
        buf=io.BytesIO();Image.fromarray(value).save(buf,format='PNG',optimize=True);out[key]=buf.getvalue()
    return out, list(bounds), stats


def satellite_views(d,obj):
    p=d.resource('satellite_collection.json.gz');raw=unpack(p) if p.exists() else {'sites':[],'retrieved_at':None,'observation_cutoff':None}
    observations={r['id']:r for r in raw['sites']};spec=registry();sites=[]
    entities={r['symbol']:r['id'] for s in obj['sections'] if s['type']=='entities' for r in s['entities']}
    for site in spec['sites']:
        observation=observations.get(site['id'],{});scene=observation.get('scene')
        s=dict(site,status=observation.get('status','not_collected'),scene=None,entity_id=entities.get(site['symbol']),
               checked_at=observation.get('checked_at'),attempt_count=len(observation.get('attempts',[])))
        if scene and site['location_status']=='reviewed' and scene['site_signature']==site_signature(site) and usable(scene):
            file=d.resource(scene['raw_file']);content=file.read_bytes()
            if hashlib.sha256(content).hexdigest()!=scene['sha256']:raise ValueError('Satellite raw checksum mismatch')
            with np.load(io.BytesIO(content),allow_pickle=False) as f:arrays={k:f[k] for k in f.files}
            rgb_max=site.get('rgb_reflectance_max',.3)
            output,bounds,stats=images(arrays,scene,rgb_max)
            public=dict(id=scene['id'],captured_at=scene['captured_at'],retrieved_at=scene['retrieved_at'],source=scene['source'],
                bounds_mercator=bounds,clear_fraction=scene['clear_fraction'],coverage=scene['coverage'],
                core_clear_fraction=scene['core_clear_fraction'],point_clear_fraction=scene['point_clear_fraction'],
                native_resolution_m=10,classification_resolution_m=20,rgb_reflectance_max=rgb_max,**stats,images={})
            for kind,content in output.items():
                relative='data/satellite/'+site['id']+'-'+kind+'.png';path=ROOT/'docs'/relative
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content)
                public['images'][kind]=dict(path=relative,sha256=hashlib.sha256(content).hexdigest(),bytes=len(content),width=400,height=400)
            s['scene']=public
        elif scene:s['status']='location_changed'
        sites.append(s)
    obj['sections']=[s for s in obj['sections'] if s['type'] not in ['satellite','facilitydetail']]
    index=next(i for i,s in enumerate(obj['sections']) if s['type']=='entities')
    obj['sections'].insert(index,dict(type='facilitydetail',title='시설 Entity · 위치와 관측 근거',group='Entity 360'))
    years=', '.join(sorted({s['scene']['captured_at'][:4] for s in sites if s['scene']}))
    obj['sections'].append(dict(type='satellite',title='위성 현장 · RGB / NDVI',group='위성 현장',sites=sites,
        retrieved_at=raw['retrieved_at'],observation_cutoff=raw['observation_cutoff'],registry_reviewed_at=spec['reviewed_at'],
        location_count=sum(s['location_status']=='reviewed' for s in sites),image_count=sum(s['scene'] is not None for s in sites),
        basemap=dict(provider='NASA GIBS',layer='BlueMarble_ShadedRelief_Bathymetry',observation_month='2004-08',native_resolution_m=500,max_native_zoom=8,source='https://worldview.earthdata.nasa.gov/',dynamic=False),
        attribution='Contains modified Copernicus Sentinel data ('+years+') · Earth Search / Element84 · © OpenStreetMap contributors (ODbL1.0) · Natural Earth · 위치별 추가 출처는 시설 상세 참조',
        note='각 시설 주변 4×4km의 최근60일·최대36개 후보 중 유효 화소70% 이상, 중심1km 맑은 화소85% 이상인 최신 확보 영상입니다. 촬영일은 시설마다 다릅니다. NDVI는 식생 지수로, 건설 진척률·가동률·실적 추정값이 아닙니다. 구름·그림자·눈·결측 화소는 제외합니다.'))
    obj['missing']=[x.replace('위성 시설 관측·','') for x in obj['missing'] if not x.startswith(('위성 지도 배경은','위성 배경은'))]
    pending=[s['name'] for s in sites if s['location_status']!='reviewed']
    if pending:obj['missing'].append('위성 관측 위치 대조 중: '+', '.join(pending)+'. 해당 시설 슬롯은 보존하며 미확인 좌표의 영상은 표시하지 않습니다.')
    missing=[s['name'] for s in sites if s['location_status']=='reviewed' and s['scene'] is None]
    if missing:obj['missing'].append('검증 위치 중 위성 영상 미확보: '+', '.join(missing)+'.')
    obj['missing'].append('위성 배경은 NASA Blue Marble 2004년 합성 영상입니다. 원본 Esri 고해상도 영상·지명 레이어는 이용권한 확인이 남아 있습니다. 시설 관측은 별도 촬영일의 Sentinel 자료이며 건설 진척·가동률을 추정하지 않습니다.')
