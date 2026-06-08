import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = ROOT / "docs" / "feishu-collab"
DOCS_README = ROOT / "docs" / "README.md"


class FeishuCollabDocsStructureTests(unittest.TestCase):
    def test_docs_entrypoints_exist_with_required_headings(self):
        expected = {
            DOCS_ROOT / "README.md": "# Feishu Collaboration",
            DOCS_ROOT / "SKILL_REGISTRY.md": "# Skill Registry",
            DOCS_ROOT / "RUNBOOK_INDEX.md": "# Runbook Index",
            DOCS_ROOT / "HANDOFF_INDEX.md": "# Handoff Index",
            DOCS_ROOT / "governance" / "system-map.md": "# System Map",
        }
        for path, heading in expected.items():
            self.assertTrue(path.exists(), str(path))
            self.assertIn(heading, path.read_text(encoding="utf-8"))

    def test_docs_readme_links_the_feishu_collaboration_entrypoint(self):
        text = DOCS_README.read_text(encoding="utf-8")
        pattern = re.compile(
            r"\[[^\]]*feishu-collab/README\.md[^\]]*\]\([^)]+feishu-collab/README\.md\)",
            re.IGNORECASE,
        )
        self.assertRegex(text, pattern)


if __name__ == "__main__":
    unittest.main()
