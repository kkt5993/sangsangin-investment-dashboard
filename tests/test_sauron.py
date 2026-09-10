import copy
import json
import tempfile
import unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from pipeline import sauron_data as s
from pipeline.events_data import save,read
from pipeline.public_assets import globe_assets
from pipeline.store import ROOT


class SauronTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,9,10,9,tzinfo=timezone.utc)
        self.omm=json.loads((ROOT/'tests/fixtures/sauron-orbits.json').read_text())['records'][0]['omm']

    def feed(self,mag=3):
        ms=int(self.now.timestamp()*1000)
        return dict(type='FeatureCollection',metadata=dict(status=200,count=1,generated=ms),features=[dict(id='test1',
            geometry=dict(type='Point',coordinates=[128,36,12.5]),properties=dict(mag=mag,type='earthquake',time=ms-60000,
            updated=ms,place='Example',url='https://earthquake.usgs.gov/earthquakes/eventpage/test1',magType='ml',status='reviewed'))])

    def test_raw_threshold_and_empty_feed(self):
        self.assertEqual(s.quakes(self.feed(2.45),self.now)['events'],[])
        self.assertEqual(s.quakes(self.feed(2.5),self.now)['events'][0]['mag'],2.5)
        f=self.feed();f['features']=[];f['metadata']['count']=0
        self.assertEqual(s.quakes(f,self.now)['events'],[])

    def test_invalid_observations_and_feed_scope(self):
        for value in [None,True,float('nan'),float('inf'),11]:
            with self.subTest(value=value),self.assertRaises(ValueError):s.quakes(self.feed(value),self.now)
        for key,value in [('count',2),('status',404),('generated',0)]:
            f=self.feed();f['metadata'][key]=value
            with self.assertRaises(ValueError):s.quakes(f,self.now)
        f=self.feed();f['features'][0]['geometry']['coordinates'][0]=181
        with self.assertRaises(ValueError):s.quakes(f,self.now)

    def test_quake_times_url_and_duplicate_conflict(self):
        for key,value in [('time',0),('updated',0),('url','https://example.com/')]:
            f=self.feed();f['features'][0]['properties'][key]=value
            with self.assertRaises(ValueError):s.quakes(f,self.now)
        f=self.feed();f['features'].append(copy.deepcopy(f['features'][0]));f['metadata']['count']=2
        self.assertEqual(len(s.quakes(f,self.now)['events']),1)
        f['features'][1]['properties']['mag']=4
        with self.assertRaises(ValueError):s.quakes(f,self.now)

    def test_omm_precision_utc_and_six_digit(self):
        p={**self.omm,'NORAD_CAT_ID':123456,'BSTAR':0.0000000123456789}
        row=s.stations([p],self.now)[0]
        self.assertEqual(row['NORAD_CAT_ID'],'123456');self.assertEqual(float(row['BSTAR']),p['BSTAR'])
        self.assertTrue(row['EPOCH'].endswith('Z'))
        offset={**p,'EPOCH':s.utc(p['EPOCH']).astimezone(timezone(timedelta(hours=9))).isoformat()}
        self.assertEqual(s.stations([offset],self.now),[row])

    def test_omm_rejects_bad_frames_fields_and_age(self):
        for key,value in [('REF_FRAME','GCRF'),('TIME_SYSTEM','TAI'),('CENTER_NAME','MARS'),('MEAN_ELEMENT_THEORY','OTHER'),
            ('MEAN_MOTION',0),('ECCENTRICITY',1),('INCLINATION',181),('RA_OF_ASC_NODE',360),('NORAD_CAT_ID',12.3),
            ('EPHEMERIS_TYPE',4),('ELEMENT_SET_NO',-1),('CLASSIFICATION_TYPE','C'),('BSTAR',None),('EPOCH','2020-01-01')]:
            with self.subTest(key=key),self.assertRaises(ValueError):s.stations([{**self.omm,key:value}],self.now)
        with self.assertRaises(ValueError):s.stations([],self.now)
        with self.assertRaises(ValueError):s.stations([self.omm,{**self.omm,'BSTAR':1}],self.now)

    def fixture(self,root):
        parent=root/'parent';base=root/'child';parent.mkdir();base.mkdir()
        d=SimpleNamespace(base=base,resource=lambda name:base/name if (base/name).exists() else parent/name)
        now=datetime.now(timezone.utc).isoformat();old=(datetime.now(timezone.utc)-timedelta(hours=10)).isoformat()
        save(parent/'sauron/quakes.json.gz',dict(checked_at=now,retrieved_at=old,data={'events':[]}))
        save(parent/'sauron/stations.json.gz',dict(checked_at=now,retrieved_at=old,data=[self.omm]))
        return d,parent

    def test_recent_cache_makes_no_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            d,_=self.fixture(Path(tmp))
            with patch.object(s,'download',side_effect=AssertionError('network')) as request:
                r=s.collect(d);request.assert_not_called()
            self.assertTrue(all(x['state']=='reused' and not x['requested'] for x in r['sources']))

    def test_celestrak_non200_halts_future_attempts_and_preserves_data(self):
        for status in [301,403,404,429,500]:
            with self.subTest(status=status),tempfile.TemporaryDirectory() as tmp:
                d,parent=self.fixture(Path(tmp));p=parent/'sauron/stations.json.gz';old=read(p);old['checked_at']='2026-01-01T00:00:00Z';save(p,old)
                error=RuntimeError('HTTP');error.http_status=status
                with patch.object(s,'download',side_effect=error) as request:
                    r=s.collect(d);s.collect(d);self.assertEqual(request.call_count,1)
                self.assertEqual(r['sources'][1]['state'],'halted');self.assertEqual(read(d.resource('sauron/stations.json.gz')),old)

    def test_invalid_payload_preserves_old_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            d,parent=self.fixture(Path(tmp));p=parent/'sauron/quakes.json.gz';old=read(p);old['checked_at']='2026-01-01T00:00:00Z';save(p,old)
            with patch.object(s,'download',return_value=({},2,'bad')):r=s.collect(d)
            self.assertEqual(r['sources'][0]['state'],'error');self.assertEqual(read(d.resource('sauron/quakes.json.gz')),old)

    def test_download_status_and_size_cap(self):
        class Reply:
            status_code=200
            def __enter__(self):return self
            def __exit__(self,*_):pass
            def iter_content(self,_):yield b'{"ok":true}'
        reply=Reply();session=SimpleNamespace(get=lambda *a,**k:reply)
        self.assertEqual(s.download('https://example.com',session)[0],{'ok':True})
        with patch.object(s,'LIMIT',3),self.assertRaises(ValueError):s.download('https://example.com',session)
        reply.status_code=301
        with self.assertRaises(RuntimeError) as result:s.download('https://example.com',session)
        self.assertEqual(result.exception.http_status,301)

    def test_vendor_manifest_and_tamper_gate(self):
        self.assertGreater(len(globe_assets(ROOT/'docs',ROOT/'config')),400)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'sauron-views.js').write_text('')
            with self.assertRaisesRegex(ValueError,'Missing'):globe_assets(root,ROOT/'config')
            (root/'vendor/cesium').mkdir(parents=True);(root/'vendor/cesium/extra.js').write_text('')
            with self.assertRaisesRegex(ValueError,'unlisted'):globe_assets(root,ROOT/'config')


if __name__=='__main__':unittest.main()
