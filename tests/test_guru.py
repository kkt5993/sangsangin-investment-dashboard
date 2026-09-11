import copy,json,tempfile,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from pipeline import guru_data as g
from pipeline.guru_views import holdings,views

def meta(accession='0000000123-26-000001',form='13F-HR',accepted='2026-08-14T20:00:00+00:00'):
    return dict(cik='0000000123',accession=accession,form=form,report_date='2026-06-30',filing_date='2026-08-14',accepted_at=accepted,index_url='https://www.sec.gov/Archives/edgar/data/123/'+accession.replace('-','')+'/'+accession+'-index.html',unit='USD',mode='direct_xml')
def row(value=100,option='',cusip='123456789'):
    return g.row('TEST INC','COM',cusip,'',str(value),'20','SH',option,'SOLE','','20','0','0')
def report(**kwargs):return g.normalized(kwargs.pop('metadata',meta()),kwargs.pop('rows',[row()]),kwargs.pop('count',1),kwargs.pop('total',100),**kwargs)
def context(path):return SimpleNamespace(as_of='2026-09-10',base=path,resource=lambda name:path/name)

class GuruTests(unittest.TestCase):
    def test_xml_identity_dates_options_and_totals(self):
        cover=b'<edgarSubmission><submissionType>13F-HR</submissionType><filerInfo><filer><credentials><cik>123</cik></credentials></filer></filerInfo><coverPage><reportCalendarOrQuarter>06-30-2026</reportCalendarOrQuarter><isAmendment>false</isAmendment></coverPage><summaryPage><tableEntryTotal>1</tableEntryTotal><tableValueTotal>100</tableValueTotal></summaryPage></edgarSubmission>'
        table=b'<informationTable xmlns="urn:fixture"><infoTable><nameOfIssuer>TEST INC</nameOfIssuer><titleOfClass>COM</titleOfClass><cusip>123456789</cusip><value>100</value><shrsOrPrnAmt><sshPrnamt>20</sshPrnamt><sshPrnamtType>SH</sshPrnamtType></shrsOrPrnAmt><putCall>Put</putCall><investmentDiscretion>SOLE</investmentDiscretion><votingAuthority><Sole>0</Sole><Shared>0</Shared><None>0</None></votingAuthority></infoTable></informationTable>'
        r=g.parse_xml(cover,[table],meta());self.assertEqual(r['entries'][0]['option'],'PUT');self.assertEqual(r['table_sum'],100)
        for bad in [cover.replace(b'<cik>123',b'<cik>999'),cover.replace(b'06-30-2026',b'03-31-2026'),b'<!DOCTYPE x>'+cover]:
            with self.assertRaises(ValueError):g.parse_xml(bad,[table],meta())
    def test_count_mismatch_rejected_value_discrepancy_retained(self):
        with self.assertRaises(ValueError):report(count=2)
        r=report(total=104);self.assertEqual(r['reconciliation_difference'],-4);self.assertEqual(r['value_total'],104);self.assertEqual(holdings(r)[0]['weight'],100)
    def test_options_classes_and_manager_rows_do_not_merge_incorrectly(self):
        rows=[row(40),row(10),row(30,'PUT'),row(20,'CALL')];r=report(rows=rows,count=4)
        out=holdings(r);self.assertEqual(len(out),3);self.assertEqual(out[0]['value'],'50');self.assertEqual(out[0]['source_rows'],2);self.assertEqual(sum(h['weight'] for h in out),100)
        rows[1]['share_class']='PREFERRED';self.assertEqual(len(holdings(report(rows=rows,count=4))),4)
    def test_zero_placeholder_is_preserved_in_ledger_not_a_security(self):
        placeholder=g.row('NA','COM','000000000','','0','0','SH','','SOLE','','0','0','0')
        r=report(rows=[placeholder],total=0);self.assertEqual(r['entry_total'],1);self.assertEqual(holdings(r),[])
    def test_amendment_additions_restatements_future_and_missing_base(self):
        base=report();am=report(metadata=meta('0000000123-26-000002','13F-HR/A','2026-08-14T21:00:00+00:00'),rows=[row(50,'CALL')],total=50,amendment='NEW HOLDINGS')
        out=g.latest([am,base],'0000000123','2026-09-10');self.assertEqual(out['table_sum'],150);self.assertEqual(len(out['accessions']),2)
        newer=copy.deepcopy(am);newer.update(accession='0000000123-26-000003',accepted_at='2026-08-14T22:00:00+00:00')
        out=g.latest([am,newer],'0000000123','2026-09-10');self.assertEqual(out['resolution'],'amendment_base_missing')
        rest=copy.deepcopy(newer);rest['amendment']='RESTATEMENT';out=g.latest([base,am,rest],'0000000123','2026-09-10');self.assertEqual(out['table_sum'],50);self.assertEqual(len(out['entries']),1)
        self.assertIsNone(g.latest([base],'0000000123','2026-08-13'))
    def test_notice_is_not_zero_holdings(self):
        nt=g.normalized(meta(form='13F-NT'),[],0,0,other_reporting=[dict(name='PARENT',cik='0000000456')]);out=g.latest([nt],'0000000123','2026-09-10');self.assertEqual(out['resolution'],'notice');self.assertEqual(out['other_reporting'][0]['cik'],'0000000456')
    def test_reviewed_table_complete_schema_and_unit_required(self):
        text='(to the nearest dollar)\nL16: TEST | COM | 123456789 | | 100 | 20 | SH | Put | SOLE | | 0 | 0 | 0'
        r=g.parse_reviewed_table(text,meta(),1,100);self.assertEqual(r['mode'],'reviewed_sec_rendered');self.assertEqual(r['entries'][0]['option'],'PUT')
        for content,count in [(text,2),(text.replace('(to the nearest dollar)',''),1)]:
            with self.assertRaises(ValueError):g.parse_reviewed_table(content,meta(),count,100)
    def test_contact_missing_no_network_and_refusal_stops_and_caches(self):
        now=datetime(2026,9,11,tzinfo=timezone.utc);calls=[];session=SimpleNamespace(get=lambda *a,**k:(calls.append(a[0]) or SimpleNamespace(status_code=403)))
        with tempfile.TemporaryDirectory() as tmp:
            d=context(Path(tmp));g.save(d.base/g.FILE,dict(filings=[report()]))
            r=g.collect(d,contact='',session=session,now=now,pause=lambda _:None);self.assertEqual(r['requests'],0)
            r=g.collect(d,contact='fixture@example.org',session=session,now=now,pause=lambda _:None);self.assertEqual(r['status'],'access_refused');self.assertEqual(len(calls),1)
            again=g.collect(d,contact='fixture@example.org',session=session,now=now+timedelta(days=7),pause=lambda _:None);self.assertEqual(again['requests'],0);self.assertEqual(len(calls),1)
            packet=g.read(d.base/g.FILE);self.assertEqual(packet['filings'][0]['value_total'],100);self.assertNotIn('fixture@example.org',json.dumps(packet))
    def test_integer_precision_and_invalid_identity(self):
        r=row(9999999999999999);self.assertEqual(holdings(report(rows=[r],total=r['value']))[0]['value'],'9999999999999999')
        for change in [dict(unit='unknown'),dict(accepted_at='2026-08-14T20:00:00'),dict(report_date='2026-09-30')]:
            with self.assertRaises(ValueError):g.check_meta(dict(meta(),**change))
    def test_views_no_private_contact_and_asof_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=context(Path(tmp));g.save(d.base/g.FILE,dict(filings=[report()],collection=dict(status='needs_contact',contact_hash='private')))
            dragon=dict(sections=[],missing=[])
            with patch.object(__import__('pipeline.guru_views',fromlist=['settings']),'settings',return_value=[dict(id='fixture',cik='0000000123',name='Test',filer='TEST')]):views(d,dragon)
            s=dragon['sections'][0];self.assertNotIn('private',json.dumps(s));self.assertEqual(s['items'][0]['holdings'][0]['weight'],100);self.assertFalse(s['items'][0]['report']['latest_confirmed'])
