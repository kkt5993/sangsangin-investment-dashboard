import unittest
import numpy as np
import pandas as pd
from pipeline.discovery import technical, combine, bucket


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.index=pd.bdate_range('2024-01-01',periods=500)
        x=np.arange(500)
        self.price=pd.Series(100*np.exp(.001*x+.02*np.sin(x/17)),index=self.index)
        self.bench=pd.Series(100*np.exp(.0005*x),index=self.index)
        self.volume=pd.Series(1000,index=self.index)

    def test_units_scale_and_missing_volume(self):
        a=technical(self.price,self.bench,self.volume);b=technical(self.price*1000,self.bench*3,self.volume*50)
        self.assertAlmostEqual(a['score'],b['score'],places=6)
        self.assertEqual(a['metrics'],b['metrics'])
        self.assertTrue(a['stage'])
        self.assertTrue(-3<=a['score']<=3)
        m=technical(self.price,self.bench,self.volume*0)
        self.assertIsNone(m['metrics']['vsurge']);self.assertNotIn('거래량',m['components'])

    def test_short_or_bad_prices_quarantined(self):
        self.assertIsNone(technical(self.price.tail(300),self.bench,self.volume))
        bad=self.price.copy();bad.iloc[-1]*=2
        self.assertIsNone(technical(bad,self.bench,self.volume))

    def test_partial_composition_does_not_become_zero(self):
        self.assertEqual(combine('KR',1,None,None),1)
        self.assertIsNone(combine('US',1,None,2))
        self.assertIsNone(combine('US',1,2,None))
        self.assertEqual(combine('US',1,2,3),1.8)
        self.assertEqual(combine('US',0,0,0),0)

    def test_mutually_exclusive_bucket_priority(self):
        t=dict(overheat=False,recapture=True,rs_cross=False,stage=True,metrics=dict(accel=1,r3m=10,r1m=1,rs_z=1))
        self.assertEqual(bucket(t,2,10),'초기 변곡')
        t['recapture']=False;self.assertEqual(bucket(t,2,10),'스마트머니')
        self.assertEqual(bucket(t,None,None),'추세 확인')
        t['overheat']=True;self.assertEqual(bucket(t,2,10),'리서치 워치리스트')


if __name__=='__main__':unittest.main()
