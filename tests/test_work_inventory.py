import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'write_work_inventory.py'
SPEC = importlib.util.spec_from_file_location('write_work_inventory', SCRIPT)
WORK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WORK)


class WorkInventoryTests(unittest.TestCase):
    def test_indexes_unresolved_statements_but_not_section_titles(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'sample.md'
            source.write_text(
                '# 검증과 남은 범위\n\n## 후속 작업\n\n- 실제 미확보 항목\n',
                encoding='utf-8',
            )
            self.assertEqual(list(WORK.entries(source)), [(5, '- 실제 미확보 항목')])

    def test_normalizes_nested_markdown_link_in_statement(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'sample.md'
            source.write_text('남은 범위: [계약](nested/contract.md) 확인\n', encoding='utf-8')
            self.assertEqual(list(WORK.entries(source)), [(1, '남은 범위: 계약 확인')])


if __name__ == '__main__':
    unittest.main()
