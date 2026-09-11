import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from pathlib import Path
from pipeline.dragon_operations import age, row, views


class OperationTests(unittest.TestCase):
    now = datetime(2026, 9, 11, 1, tzinfo=timezone.utc)

    def test_dates_do_not_become_zero_or_retrieval_success(self):
        self.assertIsNone(age('2026-09-11', self.now))
        self.assertIsNone(age('2026-09-12T00:00:00Z', self.now))
        self.assertEqual(age('2026-09-11T00:00:00Z', self.now), 1)
        base = ('x', 'X', 'C', 'https://example.com/', 24, self.now)
        self.assertEqual(row(*base, observed='2026-09-11')['status'], 'waiting')
        self.assertEqual(row(*base, retrieved='2026-09-09T00:00:00Z')['status'], 'stale')
        self.assertEqual(row(*base, retrieved='2026-09-11T00:00:00Z', error=True)['status'], 'error')

    def test_history_published_days_null_and_repeat_build(self):
        d = SimpleNamespace(resource=lambda _: Path('tests/nonexistent-operations-fixture'))
        dragon = dict(status='partial', as_of='2026-09-10', sections=[
            dict(type='relationlab', nodes=[dict(kind='company')], links=[]),
            dict(type='dragonfocus', items=[dict(id='A', hits=[1])]),
            dict(type='dragontriggers', items=[dict(id='A', hits=[1])]),
            dict(type='table', title='거시 데이터 원장', rows=[['CPI', 'CPI', 'FRED', '2026-07-01', 'index', '2026-09-10']])])
        previous = dict(sections=[dict(type='dragonstatus', history=[
            dict(date='2026-09-09', objects=1), dict(date='2026-09-11', objects=999), dict(date='2026-09-12', objects=999)])])
        objects = dict(dragonglass=dragon)
        views(d, objects, previous=previous, now=self.now)
        status = next(s for s in dragon['sections'] if s['type'] == 'dragonstatus')
        self.assertEqual([r['date'] for r in status['history']], ['2026-09-09', '2026-09-11'])
        self.assertEqual(status['counts']['signals'], 1)
        self.assertIsNone(status['counts']['insights'])
        self.assertEqual(status['counts']['countries'], 0)
        views(d, objects, previous=dragon, now=self.now)
        sources = next(s for s in dragon['sections'] if s['type'] == 'dragonsources')['items']
        self.assertEqual(next(r for r in sources if r['name'] == 'FRED')['series'][0]['observed_at'], '2026-07-01')
        self.assertEqual(len([s for s in dragon['sections'] if s['type'] == 'dragonstatus']), 1)

    def test_no_private_configuration_or_raw_payload_projection(self):
        from unittest.mock import patch
        from pipeline.dragon_operations import sources
        d = SimpleNamespace(resource=lambda _: Path(__file__))
        def raw(_):
            return dict(secret='DO-NOT-PUBLISH', local_path='C:/private', checked_at='2026-09-11T00:00:00Z')
        with patch('pipeline.dragon_operations.read', side_effect=raw):
            result = str(sources(d, {'sections': []}, self.now))
        self.assertNotIn('DO-NOT-PUBLISH', result)
        self.assertNotIn('C:/private', result)


if __name__ == '__main__':
    unittest.main()
