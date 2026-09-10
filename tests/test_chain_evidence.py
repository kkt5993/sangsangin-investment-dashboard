import copy
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from pipeline import chain_evidence as ce
from pipeline.chain_data import settings as universe
from pipeline.events_data import read, save

NOW = datetime(2026, 9, 10, 12, tzinfo=timezone.utc)


class EvidenceTests(unittest.TestCase):
    def test_official_city_override_and_provider_move(self):
        original = [dict(symbol='ITX.MC',city='Corunna',country='Spain',location=None)]
        result = ce.enrich(original)
        self.assertEqual(result[0]['location']['name'],'Arteixo')
        self.assertEqual(result[0]['official_address']['role'],'등기 주소')
        self.assertIsNone(original[0]['location'])
        moved = ce.enrich([dict(original[0],city='Madrid')])[0]
        self.assertIsNone(moved['location']);self.assertFalse(moved['address_profile_match'])
        other = ce.enrich([dict(original[0],country='Portugal')])[0]
        self.assertIsNone(other['location'])

    def test_administrative_point_and_roche_scope(self):
        c = ce.settings()
        self.assertEqual(c['places']['1832426']['scope'],'행정구역 대표점')
        self.assertEqual(c['places']['2624388']['country'],'DK')
        novo = [r for r in c['routes'] if r['owner']=='NVO']
        self.assertEqual({r['to_country'] for r in novo},{'US','IT','BE'})
        self.assertTrue(all(r['observed_on']=='2024-12-18' and not r['directed'] for r in novo))
        self.assertTrue(all('novo_completion' in r['source_ids'] for r in novo))

    def test_registry_rejects_false_coordinates_unknown_evidence_and_units(self):
        c = ce.settings();symbols={r['symbol'] for r in universe()['companies']}
        changes=[lambda x:x['places']['1832426'].update(lat=float('nan')),
                 lambda x:x['addresses'][0].update(source_ids=['unknown']),
                 lambda x:x['routes'][0].update(observed_on='2099-01-01'),
                 lambda x:x['routes'][0].update(quantity=dict(value=True,unit='대')),
                 lambda x:x['routes'][0].update(owner='NOT_A_COMPANY')]
        for change in changes:
            bad=copy.deepcopy(c);change(bad)
            with self.assertRaises(ValueError):ce.validate(bad,symbols)

    def cache(self,folder):
        base=Path(folder)/'child';parent=Path(folder)/'parent'
        d=SimpleNamespace(base=base,resource=lambda name:base/name if (base/name).exists() else parent/name)
        conf=dict(sources={'a':dict(url='https://example.org/a')})
        return d,conf

    def test_source_reuse_and_failed_refresh_keep_success(self):
        with tempfile.TemporaryDirectory() as folder:
            d,c=self.cache(folder)
            first=ce.collect(d,fetcher=lambda _:b'first',pause=lambda _:None,now=NOW,config=c)
            def never(_):self.fail('Fresh source requested')
            cached=ce.collect(d,fetcher=never,pause=lambda _:None,now=NOW+timedelta(days=29),config=c)
            self.assertFalse(cached['attempts'][0]['requested'])
            def fail(_):raise ValueError('HTTP 403')
            failed=ce.collect(d,fetcher=fail,pause=lambda _:None,now=NOW+timedelta(days=31),config=c)
            self.assertEqual(failed['sources']['a']['sha256'],first['sources']['a']['sha256'])
            self.assertEqual(failed['sources']['a']['checked_at'],first['sources']['a']['checked_at'])
            self.assertEqual(failed['sources']['a']['error_type'],'ValueError')

    def test_changed_document_never_becomes_new_semantic_review(self):
        with tempfile.TemporaryDirectory() as folder:
            d,c=self.cache(folder)
            ce.collect(d,fetcher=lambda _:b'first',pause=lambda _:None,now=NOW,config=c)
            second=ce.collect(d,fetcher=lambda _:b'changed',pause=lambda _:None,now=NOW+timedelta(days=31),config=c)
            self.assertTrue(second['sources']['a']['changed_since_review'])
            third=ce.collect(d,fetcher=lambda _:b'changed',pause=lambda _:None,now=NOW+timedelta(days=62),config=c)
            self.assertTrue(third['sources']['a']['changed_since_review'])
            self.assertEqual(third['sources']['a']['retrieved_at'],second['sources']['a']['retrieved_at'])

    def test_host_failure_stops_same_host_and_url_change_drops_old_success(self):
        with tempfile.TemporaryDirectory() as folder:
            d,c=self.cache(folder);c['sources']['b']=dict(url='https://example.org/b')
            calls=[]
            def fail(url):calls.append(url);raise ValueError('HTTP 403')
            result=ce.collect(d,fetcher=fail,pause=lambda _:None,now=NOW,config=c)
            self.assertEqual(len(calls),1);self.assertEqual(result['attempts'][1]['state'],'deferred')
            c['sources'].pop('b')
            ce.collect(d,fetcher=lambda _:b'ok',pause=lambda _:None,now=NOW+timedelta(days=31),config=c)
            c['sources']['a']['url']='https://example.net/new'
            changed=ce.collect(d,fetcher=fail,pause=lambda _:None,now=NOW+timedelta(days=32),config=c)
            self.assertNotIn('sha256',changed['sources']['a'])


if __name__=='__main__':unittest.main()
