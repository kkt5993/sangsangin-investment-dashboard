"""One-command collect -> stage -> validate -> commit -> Vercel verification.

Credentials remain in existing local config/Git Credential Manager. A lock
prevents overlapping runs. Failed staging never replaces the published site.
"""
import argparse,contextlib,json,os,re,shutil,subprocess,sys,time
from datetime import datetime,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from .store import ROOT,DATA,read_json,write_json,digest
from .engine import Data
from .acquire import stamp

RUNTIME=DATA/'runtime'
def price_cutoff(now=None):
    now=now or datetime.now(ZoneInfo('Asia/Seoul'))
    if now.tzinfo is None:raise ValueError('Timezone-aware collection time required')
    now=now.astimezone(ZoneInfo('Asia/Seoul'))
    # The evening run may include today's completed Korean session. Each symbol
    # retains its own last completed exchange date; US prices are the prior day.
    day=now.date() if now.hour>=18 else now.date()-timedelta(days=1)
    return day.isoformat()

@contextlib.contextmanager
def lock():
    import msvcrt
    RUNTIME.mkdir(parents=True,exist_ok=True);file=RUNTIME/'refresh.lock'
    with file.open('a+b') as handle:
        handle.seek(0);handle.write(b'0');handle.flush();handle.seek(0)
        try:msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:raise RuntimeError('Another refresh is running')
        try:yield
        finally:handle.seek(0);msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)

def command(args,cwd,env,log):
    print('START',Path(args[0]).name,' '.join(args[1:3]),flush=True)
    p=subprocess.run(args,cwd=cwd,env=env,capture_output=True,text=True,encoding='utf8',errors='replace')
    # No command line or private config contents are written to the public site.
    with log.open('a',encoding='utf8') as f:f.write(p.stdout+'\n'+p.stderr+'\n')
    print('STEP',Path(args[0]).name,' '.join(args[1:3]),'exit',p.returncode,flush=True)
    if p.returncode:raise RuntimeError('Pipeline step failed; inspect local run log')
    return p.stdout.strip()

def due(parent,name,days):
    file=parent.resource(name)
    return not file.exists() or time.time()-file.stat().st_mtime>days*86400

def collect(parent,base,as_of,env,config,log):
    from .incremental import prices
    from .events_data import collect_news,collect_events
    run=lambda *args:command([sys.executable,'-m',*args,'--as-of',as_of],ROOT,env,log)
    if due(parent,'kr_largecap.json',7):
        run('pipeline.acquire','universes')
        if config.get('allow_krx_auth'):run('pipeline.krx_members','--allow-krx-auth')
    if due(parent,'us100_collection.json',7):run('pipeline.us100_data')
    members=Data(parent.as_of,base.name).members
    summary=prices(parent,base,as_of,members)
    run('pipeline.acquire','macro')
    if due(parent,'oecd_cli_collection.json',7):run('pipeline.oecd_data')
    if due(parent,'gpr_details.json.gz',7):
        from .gpr_data import collect as collect_gpr
        collect_gpr(base,as_of)
    if config.get('ecos_key_file'):run('pipeline.ecos_data','--key-file',config['ecos_key_file'])
    # Discard only this run's byte-identical generated copies, after hash check.
    mf=base/'macro/manifest.json'
    if mf.exists():
        m=read_json(mf)
        errors=sum(v.get('status')!='ok' for v in m['instruments'].values())
        if errors>max(3,len(m['instruments'])*.3):raise RuntimeError('Macro provider failure exceeds 30%; publication stopped')
        for key in list(m['instruments']):
            child=base/'macro'/(key+'.csv');prior=parent.resource('macro/'+key+'.csv')
            if child.exists() and prior.exists() and digest(child)==digest(prior):
                child.unlink();del m['instruments'][key]
        write_json(mf,m)
    if due(parent,'fundamentals',7):run('pipeline.acquire','fundamentals')
    if config.get('consensus_database') and due(parent,'local_consensus.json.gz',7):run('pipeline.local_consensus',config['consensus_database'])
    current=Data(as_of,base.name);collect_news(current)
    if due(parent,'events',3):collect_events(current,config.get('event_companies',60))
    run('pipeline.pead_data')
    if due(parent,'sec_collection.json.gz',1):run('pipeline.sec_ownership')
    if due(parent,'cot.json.gz',7):run('pipeline.cot_data')
    if due(parent,'release_calendar.json.gz',7):run('pipeline.calendar_data')
    if due(parent,'kr_release_calendar.json.gz',7):run('pipeline.kr_calendar')
    if due(parent,'satellite_collection.json.gz',7):run('pipeline.satellite_data')
    option_flags=['--allow-cboe-download'] if config.get('allow_cboe_automated_quotes') is True else []
    run('pipeline.options_data',*option_flags)
    run('pipeline.flows_data','--market','US',*option_flags)
    if config.get('allow_krx_auth'):run('pipeline.flows_data','--market','KR','--allow-krx-auth')
    if config.get('allow_krx_auth'):run('pipeline.kr_shortgamma_data','--allow-krx-auth')
    run('pipeline.risk_signals_data',*(['--allow-krx-auth'] if config.get('allow_krx_auth') else []))
    run('pipeline.trade_data')
    run('pipeline.sauron_data')
    run('pipeline.clinical_data')
    run('pipeline.guru_data')
    run('pipeline.guru_identifiers')
    run('pipeline.chain_data')
    if config.get('allow_krx_auth'):run('pipeline.krx_reconcile','--allow-krx-auth')
    current=Data(as_of,base.name)
    if len(current.frames)<len(parent.frames)*.97:raise RuntimeError('Fresh price coverage dropped more than 3%')
    return summary

def stage_project(dest):
    for name in ['docs','research','pipeline','scripts','tests','config']:
        shutil.copytree(ROOT/name,dest/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for name in ['AGENTS.md','README.md','HANDOFF.md','requirements.txt']:
        shutil.copy2(ROOT/name,dest/name)

def prune_staging(keep=2):
    """Remove only old disposable code copies; immutable raw vintages remain."""
    directory=RUNTIME/'staging';root=directory.resolve()
    if not root.exists():return
    if root.parent!=RUNTIME.resolve() or directory.is_symlink() or directory.is_junction():raise ValueError('Unexpected staging root')
    # Other folders can hold manual QA or user files; they are not dated runs.
    folders=sorted((p for p in root.iterdir() if p.is_dir() and re.fullmatch(r'\d{8}(?:T\d{6}Z)?',p.name)),key=lambda p:p.name,reverse=True)
    removed=0
    for folder in folders[keep:]:
        target=folder.resolve()
        if target.parent!=root or folder.is_symlink() or folder.is_junction():raise ValueError('Unexpected staging path')
        shutil.rmtree(target);removed+=1
    return removed

def validate(stage,env,log):
    env={**env,'PYTHON_EXECUTABLE':sys.executable}
    steps=[[sys.executable,'-m','unittest','discover','-s','tests'],[sys.executable,'scripts/validate.py'],[sys.executable,'scripts/validate_extended.py']]
    steps += [['node','scripts/'+s] for s in ['test_charts.cjs','test_dashboard.cjs','test_extended.cjs']]
    steps += [['node','--check',str(p)] for p in (stage/'docs').rglob('*') if p.suffix in {'.js','.mjs'}]
    for step in steps:command(step,stage,env,log)

def publish(stage,env,log,config=None):
    config=config or {}
    dirty=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)
    if dirty.strip():raise RuntimeError('Working tree has changes; validated staging retained, publication stopped')
    # Copy only generated public outputs. Code and user files are never committed
    # by the recurring refresh. Vercel receives this validated public output.
    for p in (stage/'docs/data').glob('*.json'):shutil.copy2(p,ROOT/'docs/data'/p.name)
    copy_satellite_outputs(stage)
    shutil.copy2(stage/'docs/status.js',ROOT/'docs/status.js')
    generated=['research/IMPLEMENTATION_STATUS.md','research/CHART_PARITY.md','research/SUBVIEWS.md']
    generated += [str(p.relative_to(stage)).replace('\\','/') for p in (stage/'research/modules').glob('*.md')]
    for name in generated:shutil.copy2(stage/name,ROOT/name)
    command(['git','add','--','docs/data','docs/status.js',*generated],ROOT,env,log)
    if subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode==0:return None
    command(['git','commit','-m','Refresh validated research snapshots'],ROOT,env,log)
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    snapshot=read_json(stage/'docs/data/refresh.json')
    pending=dict(commit=head,as_of=snapshot['as_of'],vintage=snapshot['vintage'],run_id=snapshot['run_id'],target=config.get('publish_target','vercel'))
    write_json(RUNTIME/'pending_publish.json',pending)
    return complete_publication(pending,env,log,config)

def copy_satellite_outputs(stage,destination=ROOT):
    """Validated raster outputs must follow their JSON into the public checkout."""
    import re
    source=Path(stage)/'docs/data/satellite';target=Path(destination)/'docs/data/satellite'
    files=list(source.glob('*.png'))
    for p in files:
        if p.is_symlink() or not re.fullmatch(r'ST_[A-Z_]+-(rgb|ndvi)\.png',p.name):
            raise ValueError('Unexpected generated satellite image')
    if files:target.mkdir(parents=True,exist_ok=True)
    for p in files:
        temporary=target/(p.name+'.tmp');shutil.copy2(p,temporary);temporary.replace(target/p.name)


def complete_publication(pending,env,log,config=None):
    config=config or {}
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if head!=pending['commit']:raise RuntimeError('Pending publication commit changed; review local state')
    command(['git','-c','credential.interactive=never','push','origin','main'],ROOT,env,log)
    if pending.get('target')=='vercel':
        from .vercel_deploy import deploy,verify
        if not pending.get('deployment_url'):
            package=RUNTIME/'staging'/pending['run_id']/'vercel-deploy'
            pending['deployment_url']=deploy(ROOT/'docs',package,config,env,log)
            write_json(RUNTIME/'pending_publish.json',pending)
        url=config.get('site_url') or pending['deployment_url']
        expected=(ROOT/'docs/data/refresh.json').read_bytes()
        for _ in range(12):
            try:
                if verify(url,expected):
                    pending['site_url']=url;write_json(RUNTIME/'state.json',pending)
                    (RUNTIME/'pending_publish.json').unlink(missing_ok=True)
                    try:prune_staging()
                    except (OSError,ValueError):print('Published successfully; staging cleanup needs local review',flush=True)
                    print('VERCEL VERIFIED',url,flush=True);return head
            except Exception:pass
            time.sleep(10)
        raise RuntimeError('Vercel deployment created; public URL verification pending')
    raise RuntimeError('Only Vercel publication is configured')

def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of');p.add_argument('--offline',action='store_true');p.add_argument('--publish',action='store_true');p.add_argument('--force-models',action='store_true');p.add_argument('--resume-run');a=p.parse_args()
    config_file=RUNTIME/'config.json';config=read_json(config_file) if config_file.exists() else {}
    state_file=RUNTIME/'state.json';state=read_json(state_file) if state_file.exists() else read_json(ROOT/'docs/data/status.json')
    parent_vintage=state.get('vintage') or state['as_of'];as_of=a.as_of or price_cutoff();run_id=datetime.now(ZoneInfo('UTC')).strftime('%Y%m%dT%H%M%SZ')
    with lock():
        log=RUNTIME/(run_id+'.log');report=dict(run_id=run_id,started_at=stamp(),as_of=as_of,status='running',mode='offline' if a.offline else 'online',schedule='평일 08:00·18:00 Asia/Seoul')
        try:
            if not a.offline and (as_of>price_cutoff() or as_of<state['as_of']):raise ValueError('Requested date is outside the completed refresh range')
            if a.publish and subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise RuntimeError('Working tree has changes')
            if a.publish and (RUNTIME/'pending_publish.json').exists():
                head=complete_publication(read_json(RUNTIME/'pending_publish.json'),os.environ.copy(),log,config)
                print(json.dumps(dict(status='published',resumed=True,commit=head)),flush=True);return
            prune_staging()
            parent=Data(state['as_of'],parent_vintage)
            if a.resume_run:
                from .cache import chain
                chain(DATA,a.resume_run);vintage=a.resume_run;base=DATA/'expanded'/vintage
                resumed=read_json(base/'parent.json')
                if resumed['vintage']!=parent_vintage:raise ValueError('Resume run belongs to another published parent')
                as_of=resumed['as_of'];report['as_of']=as_of
            elif a.offline:vintage=parent_vintage;as_of=state['as_of'];report['as_of']=as_of
            else:
                vintage=run_id;base=DATA/'expanded'/vintage;base.mkdir(parents=True);write_json(base/'parent.json',dict(vintage=parent_vintage,as_of=as_of))
            env={**os.environ,'SANGSANGIN_DATA_DIR':str(DATA),'SANGSANGIN_VINTAGE':vintage,'PYTHONIOENCODING':'utf-8','GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'}
            if not a.offline:report['collection']=collect(parent,base,as_of,env,config,log)
            # Keep recent reviewable staging copies; no site mutation on failure.
            stage=RUNTIME/'staging'/run_id;stage.mkdir(parents=True);stage_project(stage)
            run=lambda mod:command([sys.executable,'-m',mod,'--as-of',as_of],stage,env,log)
            model=read_json(ROOT/'docs/data/ml.json');model_age=(datetime.fromisoformat(as_of)-datetime.fromisoformat(model['as_of'])).days
            model_due=a.force_models or model_age>=7 or as_of[:7]!=model['as_of'][:7]
            if model_due or model.get('model_spec')!=2:run('pipeline.ml_models')
            if model_due or read_json(ROOT/'docs/data/maximus.json').get('model_spec')!=1:run('pipeline.maximus_model')
            from .events_data import read as read_gzip
            from .allocation_model import MODEL_SPEC
            current=Data(as_of,vintage=vintage);allocation=current.resource('allocation_model.json.gz')
            if a.force_models or not allocation.exists() or read_gzip(allocation).get('model_spec')!=MODEL_SPEC or read_gzip(allocation).get('origin')!=str(current.monthly('SPY').index[-1].date()):run('pipeline.allocation_model')
            run('pipeline.build_all');report.update(status='validated',vintage=vintage,completed_at=stamp())
            write_json(stage/'docs/data/refresh.json',report)
            command([sys.executable,'scripts/write_status_docs.py'],stage,env,log);validate(stage,env,log)
            if a.publish:
                report['commit']=publish(stage,env,log,config);report['status']='published'
            write_json(RUNTIME/(run_id+'.json'),report)
            print(json.dumps(dict(status=report['status'],run_id=run_id,as_of=as_of,vintage=vintage,commit=report.get('commit')),ensure_ascii=False),flush=True)
        except Exception as e:
            report.update(status='failed',error_type=type(e).__name__,reason=str(e),completed_at=stamp());write_json(RUNTIME/(run_id+'.json'),report)
            print('REFRESH FAILED:',str(e),flush=True);raise SystemExit(1)
if __name__=='__main__':main()
