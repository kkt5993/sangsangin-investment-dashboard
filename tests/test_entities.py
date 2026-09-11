import unittest
import numpy as np
import pandas as pd
from pipeline.entities import sensitivity


class EntityTests(unittest.TestCase):
    def test_beta_uses_common_observations_and_keeps_zero(self):
        dates = pd.bdate_range('2024-01-01', periods=350)
        returns = np.sin(np.arange(350)) * .01
        market = pd.Series(np.cumprod(1+returns), index=dates)
        stock = pd.Series(np.cumprod(1+2*returns), index=dates)
        result = sensitivity(stock, market)
        self.assertAlmostEqual(result['beta'], 2)
        self.assertAlmostEqual(result['r2'], 1)
        self.assertEqual(result['observations'], 252)
        self.assertEqual(result['end'], str(dates[-1].date()))
        # Both legs must have identical start/end dates when a quote is missing.
        sparse = market.drop(dates[-2])
        expected = pd.concat([stock, sparse], axis=1).pct_change(fill_method=None).dropna().tail(252)
        self.assertNotIn(dates[-1], expected.index)
        self.assertNotIn(dates[-2], expected.index)
        self.assertAlmostEqual(sensitivity(stock, sparse)['beta'], expected.iloc[:,0].cov(expected.iloc[:,1])/expected.iloc[:,1].var(), places=5)

    def test_missing_history_or_constant_benchmark(self):
        dates = pd.bdate_range('2024-01-01', periods=210)
        a = pd.Series(np.arange(210)+100., index=dates)
        self.assertIsNone(sensitivity(a.tail(199), a))
        self.assertIsNone(sensitivity(a, pd.Series(100., index=dates)))


if __name__ == '__main__':
    unittest.main()
