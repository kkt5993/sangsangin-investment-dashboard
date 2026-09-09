import unittest
from pipeline.calendar_data import fomc_events


class FOMCTests(unittest.TestCase):
    def test_final_day_cross_month_and_unknown_time(self):
        html='''<div class="panel"><div class="panel-heading">2026 FOMC Meetings</div>
        <div class="fomc-meeting"><span class="fomc-meeting__month">Apr/May</span><span class="fomc-meeting__date">30-1*</span></div>
        <div class="fomc-meeting"><span class="fomc-meeting__month">September</span><span class="fomc-meeting__date">15-16*</span></div>
        <div class="fomc-meeting"><span class="fomc-meeting__month">August</span><span class="fomc-meeting__date">22 (notation vote)</span></div></div>'''
        rows=fomc_events(html);self.assertEqual([r['date'] for r in rows],['2026-05-01','2026-09-16'])
        self.assertTrue(all(r['at'] is None for r in rows));self.assertIn('SEP',rows[0]['name'])

    def test_missing_or_duplicate_schedule_rejected(self):
        with self.assertRaises(ValueError):fomc_events('<html>Maintenance</html>')
        row='<div class="fomc-meeting"><span class="fomc-meeting__month">June</span><span class="fomc-meeting__date">16-17</span></div>'
        with self.assertRaises(ValueError):fomc_events('<div class="panel"><div class="panel-heading">2026 FOMC Meetings</div>'+row+row+'</div>')


if __name__=='__main__':unittest.main()
