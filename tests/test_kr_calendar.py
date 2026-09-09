import copy,gzip,hashlib,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pandas as pd
from pipeline.kr_calendar import bok_statistics,bok_meetings,kostat_events,dated,event,unique,collect,raw_page
from pipeline.calendar_views import combine
from pipeline.events_data import read,save
from pipeline.store import write_json

URL='https://www.bok.or.kr/fixture'

def statistics():
    rows=''.join(f'<tr><td>2026-01-{i:02}</td><td>8:00</td><td><a onclick="schdulPop(\'{i}\')">통계 {i}</a></td><td></td></tr>' for i in range(1,21))
    return '<table><caption>월간통계공표일정 달력 2026년09월</caption></table><table><caption>월간통계공표일정 목록</caption><tbody>'+rows+'</tbody></table>'

def kostat():
    rows=''.join(f'<tr><td>01.{i:02}.( {"월화수목금토일"[pd.Timestamp(2026,1,i).dayofweek]} )</td><td>08:00</td><td>2025년 지역{i} 소비자물가동향</td><td>물가동향과</td><td></td></tr>' for i in range(1,21))
    rows+='<tr><td>01.22.( 목 )</td><td>12:00</td><td>2026년 통계 유공 포상</td><td>기획</td><td></td></tr>'
    return '<h3>2026년 전체 보도계획</h3><table><caption>보도계획 보도일자 등</caption><tbody>'+rows+'</tbody></table>'

def policy():return '<select name="pYear"><option selected value="2026">2026년</option></select><table><caption>통화정책방향 회의</caption><tbody><tr><th scope="row">10월 22일(목)</th><td></td></tr></tbody></table>'

class KoreanCalendarTests(unittest.TestCase):
    def test_bok_annual_table_not_visible_month_grid(self):
        rows,total=bok_statistics(statistics(),2026,URL);self.assertEqual(total,20);self.assertEqual(rows[-1]['date'],'2026-01-20');self.assertEqual(rows[0]['at'],'2026-01-01T08:00:00+09:00')
        with self.assertRaises(ValueError):bok_statistics(statistics(),2027,URL)
        with self.assertRaises(ValueError):bok_statistics(statistics().replace('8:00','8:75'),2026,URL)

    def test_kostat_reference_year_is_not_publication_year(self):
        rows,total=kostat_events(kostat(),2026);self.assertEqual(len(rows),20);self.assertEqual(total,21)
        self.assertTrue(all(r['date'].startswith('2026') and r['name'].startswith('2025') for r in rows))
        self.assertTrue(all(r['category']=='물가' for r in rows))
        with self.assertRaises(ValueError):kostat_events(kostat(),2027)

    def test_policy_date_is_not_an_invented_announcement_time(self):
        rows,total=bok_meetings(policy(),2026,URL);self.assertEqual(total,1);self.assertEqual(rows[0]['date'],'2026-10-22');self.assertIsNone(rows[0]['at']);self.assertEqual(rows[0]['category'],'정책회의')
        with self.assertRaises(ValueError):bok_meetings(policy().replace('22일(목)','22일(금)'),2026,URL)

    def test_weekday_invalid_dates_and_duplicate_identity(self):
        with self.assertRaises(ValueError):dated(2026,2,30)
        with self.assertRaises(ValueError):dated(2026,1,1,'01.01.(금)')
        r=event('통계','2026-01-01','','x',URL,'BOK')
        with self.assertRaises(ValueError):unique([r,r])
        with self.assertRaises(ValueError):event('통계','2026-01-01','오전','x',URL,'BOK')

    def test_us_dst_date_rollover_and_inclusive_horizon(self):
        us=dict(retrieved_at='2026-10-01T00:00:00Z',sources=[dict(name='BEA',status='ok',count=4,url=URL)],items=[dict(name='Release'+str(i),date=date,at=at,source='BEA 공식 발표 일정',url='https://www.bea.gov/news/schedule') for i,(date,at) in enumerate([('2026-10-01','2026-10-01T16:00:00-04:00'),('2026-11-05','2026-11-05T08:30:00-05:00'),('2026-12-29','2026-12-29T00:00:00+09:00'),('2026-12-30','2026-12-30T00:00:00+09:00')])])
        s=combine(us,None,'2026-09-30');self.assertEqual(s['to_date'],'2026-12-29');self.assertEqual(len(s['items']),3)
        self.assertEqual(s['items'][0]['display_date'],'2026-10-02');self.assertEqual(s['items'][1]['kst_at'][11:16],'22:30')
        us['items'][0]['at']='2026-10-01T16:00:00'
        with self.assertRaises(ValueError):combine(us,None,'2026-09-30')

    def test_date_only_us_meeting_keeps_local_date(self):
        us=dict(retrieved_at='2026-09-01T00:00:00Z',sources=[dict(name='FOMC',status='ok',count=1,url=URL)],items=[dict(name='FOMC',date='2026-09-16',at=None,source='Fed 공식 FOMC 일정',url=URL)])
        r=combine(us,None,'2026-08-31')['items'][0];self.assertIsNone(r['kst_at']);self.assertEqual(r['display_date'],'2026-09-16');self.assertEqual(r['date_basis'],'미국 현지 날짜')

    def test_raw_cache_hash_check_without_network(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);p=base/'calendar_raw/x.html.gz';p.parent.mkdir();p.write_bytes(gzip.compress(b'calendar'))
            meta=p.with_suffix('.meta.json');write_json(meta,dict(sha256=hashlib.sha256(b'calendar').hexdigest(),url=URL))
            with patch('pipeline.kr_calendar.requests.get') as get:
                self.assertEqual(raw_page(base,'x',URL)[0],b'calendar');get.assert_not_called()
                p.write_bytes(gzip.compress(b'changed'))
                with self.assertRaises(ValueError):raw_page(base,'x',URL)

    def test_source_failure_preserves_previous_dates_and_success_time(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);prior=base/'previous.json.gz'
            item=event('2026년 통계','2026-09-20','08:00','bok_statistics:2026',URL,'한국은행');item['observed_at']='2026-09-01T00:00:00Z'
            save(prior,dict(items=[item],sources=[dict(id='bok_statistics:2026',last_success_at=item['observed_at'])]))
            d=SimpleNamespace(base=base/'new',resource=lambda name:prior)
            with patch('pipeline.kr_calendar.raw_page',side_effect=ValueError('layout changed')) as fetch,patch('pipeline.kr_calendar.stamp',return_value='2026-09-10T00:00:00Z'):
                r=collect(d,'2026-09-10T08:00:00+09:00');self.assertEqual(fetch.call_count,3)
                self.assertEqual(collect(d,'2026-09-10T08:00:00+09:00'),r);self.assertEqual(fetch.call_count,3)
            self.assertEqual(r['status'],'partial');self.assertEqual(r['sources'][0]['status'],'stale');self.assertEqual(r['items'][0]['observed_at'],item['observed_at']);self.assertEqual(r['sources'][0]['last_success_at'],item['observed_at'])
            view=combine(None,r,'2026-09-08');self.assertEqual(view['items'][0]['source_status'],'stale');self.assertGreater(view['items'][0]['age_days'],7)

if __name__=='__main__':unittest.main()
