import copy,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import pandas as pd
from pipeline.sec_ownership import accepted_utc,parse_ownership,collect,records,AccessRefused
from pipeline.ownership_views import eligible_filings,comparison,provider_candidates
from pipeline.events_data import read,save
from pipeline.store import ROOT,read_json

def transaction(code='P',kind='nonDerivative',side='A',date='2026-08-31'):
    return f'''<{kind}Transaction><securityTitle><value>Common</value></securityTitle>
    <transactionDate><value>{date}</value></transactionDate><transactionCoding><transactionCode>{code}</transactionCode></transactionCoding>
    <transactionAmounts><transactionShares><value>12</value></transactionShares><transactionPricePerShare><value>10.125</value><footnoteId id="F1"/></transactionPricePerShare>
    <transactionAcquiredDisposedCode><value>{side}</value></transactionAcquiredDisposedCode></transactionAmounts>
    <ownershipNature><directOrIndirectOwnership><value>I</value></directOrIndirectOwnership></ownershipNature></{kind}Transaction>'''

def xml():
    return ('''<ownershipDocument xmlns="urn:fixture"><documentType>4</documentType><issuer><issuerCik>123</issuerCik><issuerName>Fixture</issuerName><issuerTradingSymbol>TEST</issuerTradingSymbol></issuer>
    <reportingOwner><reportingOwnerId><rptOwnerCik>456</rptOwnerCik><rptOwnerName>Doe Jane</rptOwnerName></reportingOwnerId><reportingOwnerRelationship><isDirector>1</isDirector></reportingOwnerRelationship><reportingOwnerAddress><rptOwnerStreet1>PRIVATE STREET</rptOwnerStreet1></reportingOwnerAddress></reportingOwner>
    <nonDerivativeTable>'''+''.join(transaction(c) for c in ['P','S','M','A'])+transaction(side='D')+'''<nonDerivativeHolding><postTransactionAmounts><sharesOwnedFollowingTransaction><value>999999</value></sharesOwnedFollowingTransaction></postTransactionAmounts></nonDerivativeHolding></nonDerivativeTable>
    <derivativeTable>'''+transaction(kind='derivative')+'''</derivativeTable><footnotes><footnote id="F1">Reported weighted average price</footnote></footnotes></ownershipDocument>''').encode()

def metadata():return dict(accession='0000000456-26-000001',issuer_cik='0000000123',accepted_at='2026-09-01T20:15:00Z',filing_date='2026-09-01',source_url='https://www.sec.gov/fixture.xml',retrieved_at='2026-09-02T00:00:00Z')

class OwnershipTests(unittest.TestCase):
    def filing(self):return parse_ownership(xml(),metadata())

    def test_xml_codes_holdings_namespace_and_private_fields(self):
        f=self.filing();self.assertEqual(len(f['transactions']),6);self.assertEqual(f['issuer_cik'],'0000000123')
        self.assertTrue(f['transactions'][0]['weighted_price']);self.assertTrue(f['owners'][0]['director']);self.assertIsNone(f['plan10b5'])
        self.assertNotIn('PRIVATE STREET',json.dumps(f));valid,pending=eligible_filings([f],'2026-09-08')
        self.assertFalse(pending);self.assertEqual(len(valid[0]['transactions']),1);self.assertEqual(valid[0]['transactions'][0]['amount'],121.5)

    def test_xml_invalid_issuer_entity_owner_and_size(self):
        cases=[(xml(),dict(metadata(),issuer_cik='999')),(b'<!DOCTYPE x>'+xml(),metadata()),(xml().replace(b'<rptOwnerCik>456</rptOwnerCik>',b''),metadata())]
        for body,meta in cases:
            with self.assertRaises(ValueError):parse_ownership(body,meta)

    def test_acceptance_timezone_and_naive_rejection(self):
        self.assertEqual(accepted_utc('2026-08-12 16:04:39',True),'2026-08-12T20:04:39+00:00')
        self.assertEqual(accepted_utc('2026-01-12 16:04:39',True),'2026-01-12T21:04:39+00:00')
        self.assertIsNone(accepted_utc('2026-08-12 16:04:39'));self.assertIsNone(accepted_utc('NaT'));self.assertIsNone(accepted_utc('bad',True))

    def test_inclusive_90_days_and_invalid_transaction_dates(self):
        f=self.filing();row=f['transactions'][0];start=(pd.Timestamp('2026-09-08')-pd.Timedelta(days=89)).date().isoformat()
        f['transactions']=[dict(row,date=t) for t in [start,'2026-06-10','2026-09-09','2026-08-99','20260831']]
        valid,pending=eligible_filings([f],'2026-09-08');self.assertEqual([r['date'] for r in valid[0]['transactions']],[start]);self.assertFalse(pending)

    def test_future_missing_acceptance_and_transaction_after_acceptance(self):
        for at,why in [(None,'접수 시각'),('2026-09-09T04:00:00Z','기준일 이후'),('2026-08-30T20:00:00Z','거래일')]:
            f=self.filing();f['accepted_at']=at;valid,pending=eligible_filings([f],'2026-09-08');self.assertFalse(valid);self.assertTrue(any(why in r for r in pending[0]['reasons']))
        f=self.filing();f['accepted_at']='2026-09-09T03:59:59Z';self.assertEqual(len(eligible_filings([f],'2026-09-08')[0]),1)

    def test_amendment_quarantine_and_accession_dedup(self):
        f=self.filing();am=copy.deepcopy(f);am.update(accession='0000000456-26-000002',form='4/A',original_filing_date=f['filing_date'])
        valid,pending=eligible_filings([f,f,am],'2026-09-08');self.assertFalse(valid);self.assertEqual(len(pending),2)
        f['filing_date']=None;am['original_filing_date']=None;am['transactions'][0]['date']='2026-08-29';am['transactions']=am['transactions'][:1]
        self.assertEqual(len(eligible_filings([f,am],'2026-09-08')[0]),1)
        self.assertEqual(len(eligible_filings([f,f],'2026-09-08')[0]),1)

    def test_provider_matches_multiple_sec_trade_dates_and_rounding(self):
        f=self.filing();f['transactions']=[dict(f['transactions'][0],date=t) for t in ['2026-08-31','2026-09-01']]
        valid,_=eligible_filings([f],'2026-09-08');c=dict(symbol='TEST',date='2026-09-01',name='DOE, JANE',shares=24,amount=243.3)
        match=comparison([c],valid)[0];self.assertEqual(match['sec_rows'],2);self.assertEqual(match['sec_start'],'2026-08-31');self.assertAlmostEqual(match['amount_delta'],-.3);self.assertEqual(match['status'],'원문·접수 확인')
        self.assertEqual(comparison([dict(c,amount=230)],valid)[0]['status'],'금액 차이 검토')
        self.assertIsNone(comparison([dict(c,shares=25)],valid)[0]['accession'])

    def test_provider_purchase_only_and_bad_date(self):
        f=pd.DataFrame([['2026-08-31','Purchase',12,121,'Doe'],['2026-08-31','Stock Award',12,121,'Doe'],['bad','Purchase',12,121,'Doe'],['2026-09-09','Purchase',12,121,'Doe']],columns=['Start Date','Text','Shares','Value','Insider'])
        events={'TEST':dict(insider=json.loads(f.to_json(orient='split')),retrieved_at='2026-09-09T12:00:00Z')}
        self.assertEqual(len(provider_candidates(events,'2026-09-08')),1)

    def test_collection_403_stops_and_daily_guard(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);d=SimpleNamespace(base=base,bases=[base],as_of='2026-09-08',resource=lambda name:base/name)
            session=Mock();session.get.return_value.status_code=403
            with patch('pipeline.sec_ownership.requests.Session',return_value=session),patch('pipeline.sec_ownership.time.sleep'),patch('pipeline.sec_ownership.candidate_symbols',return_value=['TEST']):
                r=collect(d);self.assertEqual(r['status'],'access_refused');self.assertEqual(session.get.call_count,1);self.assertEqual(r['documents'],0)
                self.assertEqual(collect(d),r);self.assertEqual(session.get.call_count,1)
            self.assertEqual(read(base/'sec_collection.json.gz')['status'],'access_refused')

    def test_collection_flags_truncated_recent_window(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);d=SimpleNamespace(base=base,bases=[base],as_of='2026-09-08',resource=lambda name:base/name)
            bodies=[json.dumps({'0':dict(ticker='TEST',cik_str=123)}).encode(),json.dumps(dict(filings=dict(recent=dict(form=['10-Q'],filingDate=['2026-08-01'])))).encode()]
            with patch('pipeline.sec_ownership.fetch',side_effect=bodies),patch('pipeline.sec_ownership.candidate_symbols',return_value=['TEST']):r=collect(d)
            self.assertEqual(r['status'],'partial');self.assertFalse(r['issuers'][0]['recent_window_complete'])

    def test_collection_rejects_invalid_accession_before_raw_path(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);d=SimpleNamespace(base=base,bases=[base],as_of='2026-09-08',resource=lambda name:base/name)
            recent=dict(form=['4'],filingDate=['2026-08-31'],acceptanceDateTime=['2026-08-31T20:30:00Z'],accessionNumber=['../outside'],primaryDocument=['ownership.xml'])
            bodies=[json.dumps({'0':dict(ticker='TEST',cik_str=123)}).encode(),json.dumps(dict(filings=dict(recent=recent))).encode()]
            with patch('pipeline.sec_ownership.fetch',side_effect=bodies) as fetch,patch('pipeline.sec_ownership.candidate_symbols',return_value=['TEST']):r=collect(d)
            self.assertEqual(fetch.call_count,2);self.assertEqual(r['documents'],0);self.assertTrue(any(e['error']=='Invalid accession' for e in r['errors']))

    def test_reviewed_sources_and_no_duplicate_api_record(self):
        facts=read_json(ROOT/'config/sec_ownership_reviews.json')['filings'];valid,pending=eligible_filings(facts,'2026-09-08')
        self.assertEqual(len(facts),8);self.assertEqual(len(valid),7);self.assertEqual(sum(len(f['transactions']) for f in valid),9);self.assertEqual([r['symbol'] for r in pending],['AVGO'])
        for f in facts:self.assertTrue(f['source_url'].startswith('https://www.sec.gov/Archives/'));self.assertEqual(f['mode'],'source_review')
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);f=dict(facts[0],mode='direct_xml');save(base/'sec/parsed/x.json.gz',f);merged=records(SimpleNamespace(bases=[base]))
            self.assertEqual(len(merged),8);self.assertEqual(next(r for r in merged if r['accession']==f['accession'])['mode'],'direct_xml')

if __name__=='__main__':unittest.main()
