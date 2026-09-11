import copy,tempfile,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from types import SimpleNamespace
from pipeline import power_relations as P
from pipeline.events_data import read

class PowerRelationsTest(unittest.TestCase):
    def data(self,base,asof='2026-09-10'):
        return SimpleNamespace(base=base,as_of=asof,resource=lambda name:base/name)
    def test_capacity_is_not_customer_allocation(self):
        c=P.settings();rows={r['id']:r for r in c['contracts']}
        self.assertIsNone(rows['nee_google']['contract_mw']);self.assertEqual(rows['nee_google']['facility_mw'],615)
        self.assertIsNone(rows['aes_msft']['term_years']);self.assertEqual(rows['vst_meta']['contract_mw'],2176+433)
        self.assertIn('2027',rows['ceg_msft']['schedule'])
    def test_cutoff_and_amendment(self):
        with tempfile.TemporaryDirectory() as t:
            d=self.data(Path(t),'2025-07-01');edges=P.links(d)
            self.assertEqual({e['contract']['id'] for e in edges},{'ceg_meta','aes_msft'})
            self.assertTrue(all(e['weight']==1 and e['relation']=='powers' for e in edges))
            self.assertFalse(any(e['contract']['id']=='ceg_msft' for e in edges),'Do not backfill a 2026 amendment into 2025')
    def test_validation(self):
        c=P.settings();c['contracts'][0]['contract_mw']=float('nan')
        with self.assertRaises(AssertionError):P.validate(c)
        c=P.settings();c['sources']['ceg_msft']['url']='https://user:password@example.com'
        with self.assertRaises(AssertionError):P.validate(c)
    def test_collector_namespace_cache_change_failure(self):
        now=datetime(2026,9,11,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as t:
            d=self.data(Path(t));calls=[]
            def fetch(url):calls.append(url);return b'initial document'
            first=P.collect(d,fetcher=fetch,pause=lambda _:None,now=now)
            self.assertEqual(len(calls),6);self.assertTrue((d.base/P.MANIFEST).exists())
            self.assertFalse((d.base/'chain/evidence_sources.json.gz').exists())
            P.collect(d,fetcher=fetch,pause=lambda _:None,now=now+timedelta(days=1));self.assertEqual(len(calls),6)
            changed=P.collect(d,fetcher=lambda _:b'changed document',pause=lambda _:None,now=now+timedelta(days=31))
            self.assertTrue(all(r['changed_since_review'] for r in changed['sources'].values()))
            def fail(_):raise TimeoutError()
            failed=P.collect(d,fetcher=fail,pause=lambda _:None,now=now+timedelta(days=62))
            for key,r in failed['sources'].items():self.assertEqual(r['sha256'],changed['sources'][key]['sha256'])
            e=P.links(d);P.verify(dict(links=e),d.as_of)
            self.assertTrue(any(s['error_type'] for r in e for s in r['contract']['sources']))
    def test_source_url_change_does_not_keep_old_check(self):
        with tempfile.TemporaryDirectory() as t:
            d=self.data(Path(t));P.collect(d,fetcher=lambda _:b'body',pause=lambda _:None)
            c=P.settings();c['sources']['ceg_meta']['url']='https://example.com/changed'
            e=next(r for r in P.links(d,c) if r['contract']['id']=='ceg_meta')
            self.assertIsNone(e['contract']['sources'][0]['checked_at'])
