import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('checker', HERE / 'check_profile_readmes.py')
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
STYLE = (HERE.parent / 'references/lachlanchen-profile-readme-style.md').read_text()
PANEL = '<!-- support:start -->' + STYLE.split('<!-- support:start -->', 1)[1].split('<!-- support:end -->', 1)[0] + '<!-- support:end -->'
BANNER = '[![LazyingArt banner](https://lazying.art/media/brand/lazyingart-intro.gif)](https://lazying.art)'


class ProfileTests(unittest.TestCase):
    def good(self):
        return BANNER + '\n\n' + PANEL

    def test_approved_panel_and_banner(self):
        self.assertEqual(checker.brand_errors(self.good()), [])

    def test_image_file_is_not_click_destination(self):
        bad = self.good().replace('](https://lazying.art)', '](https://lazying.art/media/brand/lazyingart-intro.gif)')
        self.assertTrue(any('banner' in e for e in checker.brand_errors(bad)))

    def test_payment_qr_rejected_but_product_mentions_allowed(self):
        self.assertEqual(checker.brand_errors(self.good() + '\nWeChat integrations.'), [])
        self.assertTrue(any('QR' in e for e in checker.brand_errors(self.good() + '\n![Pay](figs/donate_alipay.png)')))

    def test_camo_and_personal_badge_labels_rejected(self):
        for old, new in [('https://img.shields.io/badge/', 'https://camo.githubusercontent.com/'), ('PayPal-Support-', 'PayPal-RongzhouChen-')]:
            self.assertTrue(checker.brand_errors(self.good().replace(old, new)))

    def test_destinations_cannot_change_silently(self):
        self.assertTrue(checker.brand_errors(self.good().replace('https://paypal.me/RongzhouChen', 'https://example.org')))

    def test_example_panel_does_not_satisfy_visible_requirement(self):
        self.assertTrue(checker.brand_errors('```md\n' + self.good() + '\n```'))

    def test_duplicate_panel_rejected(self):
        self.assertTrue(checker.brand_errors(self.good() + '\n\n' + PANEL))

    def test_full_document_set_and_plain_navigation(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'i18n').mkdir()
            (root / '.github').mkdir()
            (root / '.github/FUNDING.yml').write_text('github: [lachlanchen]\ncustom: ["https://github.com/sponsors/lachlanchen"]\n')
            (root / 'CITATION.cff').write_text('cff-version: 1.2.0\ntype: software\nrepository-code: https://example.org\n')
            suffix = '\n\n' + self.good() + '\n\n## Project\n\nA useful project. CITATION.cff\n\n```bibtex\n@software{example}\n```\n'
            (root / 'README.md').write_text(checker.ROOT_HEADER + suffix)
            for lang in checker.TRANSLATIONS:
                (root / 'i18n' / lang).write_text(checker.I18N_HEADER + suffix.replace('A useful project.', 'Un proyecto útil.'))
            self.assertEqual(checker.validate(root), [])
            (root / 'README.md').write_text('Language: ' + checker.ROOT_HEADER + suffix)
            self.assertTrue(any('11-language header' in e for e in checker.validate(root)))


if __name__ == '__main__':
    unittest.main()
