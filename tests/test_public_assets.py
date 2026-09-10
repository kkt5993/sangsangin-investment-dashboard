import json,tempfile,unittest
from pathlib import Path
from pipeline.public_assets import pdf_assets,ocr_assets
from pipeline.store import ROOT

class PublicAssetTests(unittest.TestCase):
    def test_ocr_models_are_only_hash_verified_binary_assets(self):
        binary=ocr_assets(ROOT/'docs',ROOT/'config/ocr_vendor.json')
        self.assertEqual({p.name for p in binary},{'eng.traineddata.gz','kor.traineddata.gz'})

    def test_missing_or_unlisted_ocr_stops_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'pdf-ocr.js').write_text('loader')
            with self.assertRaisesRegex(ValueError,'Missing'):ocr_assets(root,ROOT/'config/ocr_vendor.json')
            vendor=root/'vendor/ocr';vendor.mkdir(parents=True);(vendor/'unknown.gz').write_bytes(b'not a model')
            with self.assertRaisesRegex(ValueError,'unlisted'):ocr_assets(root,ROOT/'config/ocr_vendor.json')

    def test_shipped_pdf_files_have_pinned_hashes_and_binary_allowlist(self):
        binary=pdf_assets(ROOT/'docs',ROOT/'config/pdfjs_vendor.json')
        self.assertEqual(len(binary),182)
        self.assertEqual({p.suffix for p in binary},{'.bcmap','.pfb','.ttf'})

    def test_missing_or_changed_parser_stops_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'pdf-text.js').write_text('loader')
            with self.assertRaisesRegex(ValueError,'Missing'):pdf_assets(root,ROOT/'config/pdfjs_vendor.json')
            vendor=root/'vendor/pdfjs';vendor.mkdir(parents=True);(vendor/'extra.mjs').write_text('changed')
            with self.assertRaisesRegex(ValueError,'unlisted'):pdf_assets(root,ROOT/'config/pdfjs_vendor.json')

if __name__=='__main__':unittest.main()
