import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pipeline.events_data import read,save


class EventStorageTests(unittest.TestCase):
    def test_transient_replace_denial_retries_without_changing_old_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'collection.json.gz';save(path,{'old':True})
            replace=Path.replace;calls=[]
            def locked_then_replace(source,target):
                calls.append(source)
                self.assertEqual(read(path),{'old':True})
                if len(calls)<3:raise PermissionError('busy reader')
                return replace(source,target)
            with patch.object(Path,'replace',locked_then_replace),patch('pipeline.events_data.time.sleep') as sleep:
                save(path,{'new':True})
            self.assertEqual(read(path),{'new':True});self.assertEqual(sleep.call_count,2)

    def test_persistent_denial_raises_and_preserves_both_versions(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'collection.json.gz';save(path,{'old':True})
            with patch.object(Path,'replace',side_effect=PermissionError('denied')) as replace,patch('pipeline.events_data.time.sleep'):
                with self.assertRaises(PermissionError):save(path,{'new':True})
            self.assertEqual(replace.call_count,6)
            self.assertEqual(read(path),{'old':True})
            self.assertEqual(read(path.with_suffix('.tmp')),{'new':True})

    def test_other_filesystem_error_is_not_retried(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(Path,'replace',side_effect=OSError('disk failure')) as replace,patch('pipeline.events_data.time.sleep') as sleep:
                with self.assertRaises(OSError):save(Path(folder)/'collection.json.gz',{})
            self.assertEqual(replace.call_count,1);sleep.assert_not_called()


if __name__=='__main__':unittest.main()
