from __future__ import annotations

import json
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class _AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.images: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "img":
            values = dict(attrs)
            if values.get("src"):
                self.images.append(str(values["src"]))


class RepositoryTests(unittest.TestCase):
    def test_no_username_placeholders_remain(self) -> None:
        for relative_path in ("README.md", "docs/index.html"):
            text = (ROOT / relative_path).read_text(encoding="utf-8")
            self.assertNotIn("<your-username>", text)
            self.assertNotIn("github.com/USERNAME", text)

    def test_pages_assets_exist(self) -> None:
        parser = _AssetParser()
        parser.feed((ROOT / "docs" / "index.html").read_text(encoding="utf-8"))
        self.assertGreater(len(parser.images), 0)
        for source in parser.images:
            self.assertTrue((ROOT / "docs" / source).is_file(), source)

    def test_notebook_is_executed_without_errors(self) -> None:
        notebook = json.loads(
            (ROOT / "notebooks" / "01_experiment_design.ipynb").read_text(
                encoding="utf-8"
            )
        )
        code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
        self.assertEqual(
            [cell["execution_count"] for cell in code_cells],
            list(range(1, len(code_cells) + 1)),
        )
        errors = [
            output
            for cell in code_cells
            for output in cell.get("outputs", [])
            if output.get("output_type") == "error"
        ]
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
