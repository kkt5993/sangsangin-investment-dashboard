import unittest
import pandas as pd
from pipeline.valuation import monthly_fundamental
from pipeline.ecos_data import period_date
from pipeline.calendar_data import fred_events,bea_events

class ValuationTests(unittest.TestCase):
    def test_profit_starts_at_period_end_no_backfill(self):
        annual=pd.Series([100,120],index=pd.to_datetime(['2023-01-01','2024-01-01']))
        index=pd.to_datetime(['2023-06-30','2023-12-31','2024-06-30','2024-12-31','2025-01-31'])
        v,periods=monthly_fundamental(annual,'Y',index)
        self.assertTrue(pd.isna(v.iloc[0]));self.assertEqual(v.iloc[1:].tolist(),[100,100,120,120]);self.assertEqual(periods.iloc[-1],'2024-12-31')
        self.assertEqual(period_date('2024','A'),pd.Timestamp('2024-01-01'))

    def test_calendar_dst_and_unknown_time(self):
        html='<table><tr><td>Friday September 11, 2026 Updated</td></tr><tr><td>7:30 am</td><td><a href="/release?rid=10">CPI</a></td></tr><tr><td>N/A</td><td><a href="/release?rid=50">Unknown</a></td></tr></table>'
        summer=fred_events(html,'https://fred.stlouisfed.org/releases/calendar');self.assertEqual(pd.Timestamp(summer[0]['at']).tz_convert('Asia/Seoul').hour,21);self.assertIsNone(summer[1]['at'])
        winter=fred_events(html.replace('Friday September 11','Wednesday November 11'),'https://fred.stlouisfed.org/releases/calendar');self.assertEqual(pd.Timestamp(winter[0]['at']).tz_convert('Asia/Seoul').hour,22)

    def test_bea_year_header_and_eastern_time(self):
        html='<table><thead><tr><th>Year 2027</th></tr></thead><tr><td><div class="release-date">January 28</div><small>8:30 AM</small></td><td class="release-title">GDP</td></tr></table>'
        r=bea_events(html,'https://www.bea.gov/news/schedule',2026)[0];self.assertEqual(r['date'],'2027-01-28');self.assertEqual(pd.Timestamp(r['at']).tz_convert('Asia/Seoul').hour,22)

if __name__=='__main__':unittest.main()
