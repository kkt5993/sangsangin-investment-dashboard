"""Package only verified public files using Vercel Build Output API v3."""
import json,re,shutil,subprocess
from pathlib import Path
import requests
from .store import ROOT,write_json
from .acquire import budget

def cli(config):
    script=Path(config.get('vercel_cli',''))
    node=config.get('node_executable') or shutil.which('node')
    if not script.is_file() or not node:raise RuntimeError('Local Vercel CLI is not configured')
    return [node,str(script)]

def package_site(site,dest,project=None):
    site=Path(site).resolve();dest=Path(dest).resolve()
    if not (site/'index.html').exists():raise ValueError('Public site index is missing')
    from .public_assets import pdf_assets
    pdf_assets(site,ROOT/'config/pdfjs_vendor.json')
    files=[p for p in site.rglob('*') if p.is_file()]
    allowed={'.html','.css','.js','.mjs','.bcmap','.pfb','.ttf','.json','.svg','.png','.ico','.txt',''}
    for p in files:
        if p.is_symlink() or not p.resolve().is_relative_to(site) or p.suffix not in allowed or p.name.startswith('.env'):raise ValueError('Unexpected public file')
    budget(sum(p.stat().st_size for p in files))
    static=dest/'.vercel/output/static'
    if static.exists():raise ValueError('Deployment package already exists')
    shutil.copytree(site,static)
    write_json(dest/'.vercel/output/config.json',{'version':3,'routes':[{'src':'/data/(.*)','headers':{'Cache-Control':'public, max-age=0, must-revalidate'},'continue':True},{'handle':'filesystem'}]})
    if project is not None:
        p=Path(project)
        if not p.is_file():raise RuntimeError('Link this repository to a Vercel project first')
        shutil.copy2(p,dest/'.vercel/project.json')
    return dest

def deploy(site,dest,config,env,log):
    dest=Path(dest)
    command=cli(config)
    process_env={**env,'VERCEL_TELEMETRY_DISABLED':'1','NO_COLOR':'1','CI':'1'}
    # Resolve the CLI's saved session before its prebuilt upload path. In the
    # observed recovery, whoami succeeded and the identical upload then worked.
    # Let the CLI own renewal; never read or copy its credentials ourselves.
    auth=subprocess.run(command+['whoami'],cwd=ROOT,env=process_env,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=60)
    if auth.returncode:raise RuntimeError('Vercel authentication check failed; renew the local CLI login before publishing')
    if not (dest/'.vercel/output/static').exists():package_site(site,dest,ROOT/'.vercel/project.json')
    args=command+['deploy','--prebuilt','--prod','--yes','--cwd',str(dest)]
    p=subprocess.run(args,cwd=ROOT,env=process_env,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=300)
    with log.open('a',encoding='utf8') as f:f.write(p.stdout+'\n'+p.stderr+'\n')
    if p.returncode:raise RuntimeError('Vercel deployment failed; inspect local run log')
    urls=re.findall(r'https://[A-Za-z0-9.-]+\.vercel\.app',p.stdout)
    if not urls:raise RuntimeError('Vercel did not return a deployment URL')
    aliases=re.findall(r'Aliased:\s*(https://[A-Za-z0-9.-]+\.vercel\.app)',p.stdout+'\n'+p.stderr)
    return config.get('site_url') or (aliases[-1] if aliases else urls[-1])

def verify(url,expected):
    from urllib.parse import urlparse
    parsed=urlparse(url)
    if parsed.scheme!='https' or not parsed.hostname:raise ValueError('Invalid deployment URL')
    r=requests.get(url.rstrip('/')+'/data/refresh.json',timeout=25,headers={'Cache-Control':'no-cache'})
    return r.status_code==200 and r.content==expected
