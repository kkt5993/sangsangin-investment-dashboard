"""Research catalog built from reviewed public evidence, with no new requests."""
import hashlib
from urllib.parse import urlparse
from .store import ROOT,read_json
from .platform_modules import LIBRARY


def catalog(graph):
    sources=read_json(ROOT/'config/relation_evidence.json')['sources']
    from .power_relations import settings as power_settings
    sources={**sources,**power_settings()['sources']}
    by_url={v['url']:v for v in sources.values()}
    nodes={r['id']:r for r in graph['nodes']};documents={}
    edges=list(graph['links'])
    for edge in graph['links']:
        for source in edge.get('contract',{}).get('sources',[])[1:]:
            edges.append(dict(edge,url=source['url']))
    for edge in edges:
        url=edge.get('url','');parsed=urlparse(url)
        if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password:continue
        source=by_url.get(url,{})
        item=documents.setdefault(url,dict(id='source:'+hashlib.sha256(url.encode()).hexdigest()[:16],
            kind='official',title=source.get('title') or parsed.hostname+' · 사업·관계 근거',
            source=parsed.hostname,date=edge.get('reviewed_at'),date_kind='근거 검토일',
            published_on=source.get('published_on'),period_end=source.get('period_end'),url=url,targets=[],evidence=[],core='',direction='',horizon='',confidence=None))
        for id in [edge['source'],edge['target']]:
            node=nodes.get(id)
            if node and not any(t['id']==id for t in item['targets']):
                item['targets'].append(dict(id=id,name=node['name'],entity=bool(node.get('entity'))))
        if edge.get('basis') and edge['basis'] not in item['evidence']:item['evidence'].append(edge['basis'])
        dates=[x for x in [item['date'],edge.get('reviewed_at')] if x]
        item['date']=min(dates) if dates else None
    for item in documents.values():
        item['targets'].sort(key=lambda r:r['id']);item['core']='공식 문서에서 확인한 사업·관계 근거입니다. 문서의 발행일·수정일이 확인되지 않으면 검토일만 표시합니다.'
        item['evidence'].sort()
        if item['url'] not in by_url and item['evidence']:item['title']=item['source']+' · '+item['evidence'][0]
    result=sorted(documents.values(),key=lambda r:(r['date'] or '',r['id']),reverse=True)
    for i,row in enumerate(LIBRARY):
        result.append(dict(id='team:'+str(i),kind='team',title=row['title'],source=row['source'],date=row['date'],date_kind='작성일',
            url=row.get('url',''),targets=[],evidence=[row['evidence']],core=row['core'],direction='',horizon='',confidence=None))
    return result


def views(d,obj):
    graph=next(s for s in obj['sections'] if s['type']=='relationlab')
    rows=catalog(graph)
    position=next((i for i,s in enumerate(obj['sections']) if s.get('group')=='리서치'),len(obj['sections']))
    obj['sections']=[s for s in obj['sections'] if not(s.get('group')=='리서치' and s['type'] in ['library','dragonresearch'])]
    obj['sections'].insert(position,dict(type='dragonresearch',title='리서치 · 공식 근거와 팀 기록',group='리서치',items=rows,
        scope='공식 원문은 링크와 검토한 근거를 연결합니다. 개인 리서치 자료실 기록·첨부는 사용자가 불러올 때 이 브라우저에서만 읽습니다. 검토일은 발표일이나 자동 갱신일이 아닙니다.',
        coverage=dict(official=sum(r['kind']=='official' for r in rows),team=sum(r['kind']=='team' for r in rows),linked=sum(bool(r['targets']) for r in rows))))
    gap='리서치 카탈로그는 팀의 공개 검토 자료와 이 브라우저의 리서치 자료실 기록을 연결합니다. 원본의 비공개 리포트·투자 기대수익과 전체 167편을 복제하지 않으며, 자동 투자뷰 추론·팀 공유 저장소는 미연결입니다.'
    if gap not in obj['missing']:obj['missing'].append(gap)
