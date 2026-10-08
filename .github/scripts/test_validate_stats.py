import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from validate_stats import main, validate_card


class CardValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.path = self.directory / "card.svg"

    def write_card(self, content):
        self.path.write_text(content, encoding="utf-8")

    def test_valid_svg_with_leading_whitespace(self):
        self.write_card('\n <svg xmlns="http://www.w3.org/2000/svg">'
                        '<text data-testid="stars">0</text></svg>')
        validate_card(self.path, ("stars",))

    def test_error_svg_is_rejected(self):
        self.write_card('<svg xmlns="http://www.w3.org/2000/svg">'
                        '<text data-testid="message"><tspan>Resource not accessible '
                        'by integration</tspan><tspan>FORBIDDEN</tspan></text></svg>')
        with self.assertRaisesRegex(ValueError, "FORBIDDEN"):
            validate_card(self.path, ("stars",))

    def test_missing_or_empty_content_is_rejected(self):
        for content in ('', '<text data-testid="stars"> </text>'):
            with self.subTest(content=content):
                self.write_card(f'<svg xmlns="http://www.w3.org/2000/svg">{content}</svg>')
                with self.assertRaisesRegex(ValueError, "missing card content"):
                    validate_card(self.path, ("stars",))

    def test_malformed_or_non_svg_document_is_rejected(self):
        for content in ('', '<svg', '<html>Server error</html>'):
            with self.subTest(content=content):
                self.write_card(content)
                with self.assertRaises((ET.ParseError, ValueError)):
                    validate_card(self.path, ("stars",))

    def test_all_four_cards_are_required(self):
        for theme in ("light", "dark"):
            for card, ids in (("stats", ("stars", "commits", "prs", "issues", "contribs")),
                              ("top-langs", ("lang-name",))):
                body = ''.join(f'<text data-testid="{key}">1</text>' for key in ids)
                (self.directory / f"{card}-{theme}.svg").write_text(
                    f'<svg xmlns="http://www.w3.org/2000/svg">{body}</svg>', encoding="utf-8")
        self.assertEqual(main(self.directory), 0)
        (self.directory / "stats-dark.svg").unlink()
        self.assertEqual(main(self.directory), 1)


if __name__ == "__main__":
    unittest.main()
