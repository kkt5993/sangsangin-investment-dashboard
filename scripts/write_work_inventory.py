"""Generate a source-linked inventory of unresolved Markdown statements.

This is an index, not a completion claim: historical handoff entries can be
superseded by code, so each row must be revalidated before it is worked or
closed.  Keeping the exact source line makes the remaining implementation
scope auditable rather than relying on an informal, shrinking checklist.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'research/WORK_INVENTORY.md'
INCLUDE = [ROOT / 'HANDOFF.md', ROOT / 'README.md', *sorted((ROOT / 'research').rglob('*.md'))]
SKIP = {OUTPUT.resolve()}
PATTERN = re.compile(r'미완|미확보|남은 범위|후속|추가 구현|추가 대상|계속 대상|대기|\bTODO\b|\bunresolved\b', re.I)

# The parity table, roadmap and contracts describe the intended current scope.
# Generated status reports and handoffs are still indexed, but must not create
# duplicate checklist work or turn completed historical notes into open tasks.
CANONICAL = {
    'research/REFERENCE_PARITY.md',
    'research/ROADMAP.md',
}

def entries(path):
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        text = line.strip()
        if PATTERN.search(text):
            yield number, re.sub(r'\s+', ' ', text)


def tier(name):
    if name == 'HANDOFF.md':
        return 'historical'
    if name in CANONICAL or name.endswith('_CONTRACT.md'):
        return 'canonical'
    if name == 'README.md':
        return 'operational'
    return 'derived'

def main():
    groups = {key: [] for key in ('canonical', 'operational', 'derived', 'historical')}
    for path in INCLUDE:
        if not path.exists() or path.resolve() in SKIP:
            continue
        found = list(entries(path))
        if found:
            name = path.relative_to(ROOT).as_posix()
            groups[tier(name)].append((name, found))
    total = sum(len(items) for files in groups.values() for _, items in files)
    lines=[
        '# Markdown 작업 인벤토리',
        '',
        '이 문서는 `scripts/write_work_inventory.py`가 생성한다. Markdown에 남은 미완료·후속 표현을 출처 줄과 함께 전수 색인한다.',
        '체크박스는 현재 정본(패리티 표·로드맵·계약)의 실행 후보에만 사용한다. 운영·생성 문서는 중복·현황 증거이며, `HANDOFF.md`는 역사 인계 증거다. 어느 행도 코드·원자료·검증 결과 재확인 없이는 미완료 또는 완료로 단정하지 않는다.',
        '',
        f'출처 파일 {sum(len(files) for files in groups.values())}개 · 표현 {total}개',
        '',
        '## 분류',
        '',
        f'- 현재 정본 실행 후보: {sum(len(items) for _, items in groups["canonical"])}개',
        f'- 운영 문서 증거: {sum(len(items) for _, items in groups["operational"])}개',
        f'- 생성·파생 문서 증거: {sum(len(items) for _, items in groups["derived"])}개',
        f'- 역사 인계 증거: {sum(len(items) for _, items in groups["historical"])}개',
        '',
    ]
    headings = {
        'canonical': '현재 정본 실행 후보',
        'operational': '운영 문서 증거',
        'derived': '생성·파생 문서 증거',
        'historical': '역사 인계 증거',
    }
    for key in ('canonical', 'operational', 'derived', 'historical'):
        lines.extend([f'## {headings[key]}', ''])
        if not groups[key]:
            lines.extend(['- 해당 없음', ''])
            continue
        for name, items in groups[key]:
            lines.extend([f'### `{name}`', ''])
            marker = '- [ ]' if key == 'canonical' else '-'
            lines.extend(f'{marker} [{name}:{number}](../{name}#L{number}) — {text}' for number, text in items)
            lines.append('')
    OUTPUT.write_text('\n'.join(lines), encoding='utf-8')

if __name__=='__main__':
    main()
