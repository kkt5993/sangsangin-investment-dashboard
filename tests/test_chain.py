import copy
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from pipeline import chain_data as cd
from pipeline.events_data import read, save
from pipeline import chain_geo as geo

NOW = datetime(2026, 9, 10, 10, tzinfo=timezone.utc)


def info(symbol='NVDA'):
    return dict(symbol=symbol,quoteType='EQUITY',longName='NVIDIA Corporation',country='United States',
                city='Santa Clara',state='CA',website='https://www.nvidia.com',marketCap=5000000000000,
                currency='USD',regularMarketTime=int((NOW-timedelta(hours=12)).timestamp()))


class ProfileTests(unittest.TestCase):
    def test_scope(self):
        c=cd.settings()
        self.assertEqual((len(c['groups']),len(c['sectors']),len(c['companies'])),(20,53,151))
        self.assertEqual(sum(len(s['symbols']) for s in c['sectors']),159)
        self.assertEqual([c['name'] for c in c['companies'] if c['symbol']=='NVO'],['Novo Nordisk'])
        roche=next(r for r in c['companies'] if r['name']=='Roche')
        self.assertEqual((roche['symbol'],roche['previous_symbol']),('ROP.SW','ROG.SW'))

    def test_city_identity_not_biggest_population(self):
        a=dict(id='1',name='Cambridge',primary={'cambridge'},aliases={'cambridge'},country='US',region='MA',lat=42,lon=-71)
        b=dict(a,id='2',name='Newton',primary={'newton'},aliases={'cambridge','newton'})
        c=dict(a,id='3',region='NY')
        profile=dict(country='United States',city='Cambridge',state='MA')
        self.assertEqual(geo.location(profile,[a,b,c])['id'],'1')
        self.assertIsNone(geo.location(profile,[a,dict(a,id='4')]))
        self.assertIsNone(geo.location(dict(profile,country='Unknown'),[a]))
        self.assertEqual(geo.key('Bagsværd'),geo.key('Bagsvaerd'))
        self.assertEqual(geo.key('São Paulo'),geo.key('Sao Paulo'))

    def test_identity_and_bad_values(self):
        for change in [dict(symbol='AMD'),dict(quoteType='ETF'),dict(country=None),dict(marketCap=True),
                       dict(marketCap=float('nan')),dict(regularMarketTime=NOW.timestamp()+301)]:
            with self.subTest(change=change),self.assertRaises(ValueError):
                cd.normalize('NVDA',dict(info(),**change),NOW)

    def test_missing_field_is_not_zero_or_inferred(self):
        row=cd.normalize('NVDA',dict(info(),marketCap=None,city=None,website='javascript:alert(1)'),NOW)
        self.assertIsNone(row['marketCap']);self.assertIsNone(row['city']);self.assertIsNone(row['website'])

    def test_timezones(self):
        self.assertEqual(cd.age_hours('2026-09-10T18:00:00+09:00',NOW),1)
        self.assertEqual(cd.age_hours('2026-09-10T11:00:00+00:00',NOW),float('inf'))
        self.assertEqual(cd.age_hours('2026-09-10T09:00:00',NOW),float('inf'))

    def setup_cache(self,folder):
        parent=Path(folder)/'parent';base=Path(folder)/'child'
        def resource(name):
            return base/name if (base/name).exists() else parent/name
        d=SimpleNamespace(base=base,resource=resource)
        old=dict(symbol='NVDA',data=cd.normalize('NVDA',info(),NOW),retrieved_at=(NOW-timedelta(days=3)).isoformat(),
                 checked_at=(NOW-timedelta(days=2)).isoformat())
        save(parent/cd.PROFILE,dict(companies={'NVDA':old}))
        return d,old

    @patch('pipeline.events_data.budget')
    def test_identical_response_and_fresh_cache(self,_):
        with tempfile.TemporaryDirectory() as folder:
            d,old=self.setup_cache(folder);conf=dict(companies=[dict(symbol='NVDA')])
            with patch.object(cd,'stamp',return_value=NOW.isoformat()):
                cd.collect(d,fetch=lambda _:info(),pause=lambda _:None,now=NOW,config=conf)
            packet=read(d.resource(cd.PROFILE))['companies']['NVDA']
            self.assertEqual(packet['retrieved_at'],old['retrieved_at'])
            def never(_):self.fail('Fresh profile requested')
            report=cd.collect(d,fetch=never,pause=lambda _:None,now=NOW+timedelta(hours=1),config=conf)
            self.assertFalse(report['companies'][0]['requested'])

    @patch('pipeline.events_data.budget')
    def test_failure_keeps_previous_success_and_rate_limit_stops(self,_):
        class YFRateLimitError(Exception):pass
        with tempfile.TemporaryDirectory() as folder:
            d,old=self.setup_cache(folder);before=copy.deepcopy(old);calls=[]
            def fail(s):calls.append(s);raise YFRateLimitError()
            conf=dict(companies=[dict(symbol=s) for s in ['NVDA','AMD','MSFT']])
            report=cd.collect(d,fetch=fail,pause=lambda _:None,now=NOW,config=conf)
            self.assertEqual(calls,['NVDA'])
            self.assertEqual([r['state'] for r in report['companies']],['error','deferred','deferred'])
            self.assertEqual(read(d.resource(cd.PROFILE))['companies']['NVDA'],before)

    @patch('pipeline.events_data.budget')
    def test_three_consecutive_errors_stop(self,_):
        with tempfile.TemporaryDirectory() as folder:
            d,_old=self.setup_cache(folder)
            def fail(s):raise ValueError('fixture')
            report=cd.collect(d,fetch=fail,pause=lambda _:None,now=NOW,
                              config=dict(companies=[dict(symbol=s) for s in ['A','B','C','D']]))
            self.assertEqual(sum(r['requested'] for r in report['companies']),3)
            self.assertEqual(report['companies'][-1]['state'],'deferred')


if __name__=='__main__':unittest.main()
