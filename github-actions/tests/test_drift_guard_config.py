import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


TOOL_ROOT = Path(__file__).resolve().parents[2]
DRIFT_GUARD_PATH = (
    TOOL_ROOT / ".github" / "actions" / "drift-guard" / "drift_guard.py"
)
DRIFT_GUARD_SPEC = importlib.util.spec_from_file_location("drift_guard", DRIFT_GUARD_PATH)
DRIFT_GUARD = importlib.util.module_from_spec(DRIFT_GUARD_SPEC)
DRIFT_GUARD_SPEC.loader.exec_module(DRIFT_GUARD)


class DriftGuardConfigTests(unittest.TestCase):
    def test_loads_json_config_and_evaluates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / "docs").mkdir(parents=True, exist_ok=True)
            (repo_root / "docs" / "plan.md").write_text("ok", encoding="utf-8")

            cfg = {
                "modules": {"product_hub": {"paths": ["7-产物中台/**"]}},
                "change_classes": {"mainline": {"allowed_modules": ["product_hub"]}},
                "required_docs": ["docs/plan.md"],
            }
            config_path = repo_root / "drift-guard.json"
            config_path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")

            verdict = DRIFT_GUARD.evaluate(
                repo_root=repo_root,
                config_path=config_path,
                mode="manual",
                change_class="mainline",
                base_sha=None,
                head_sha=None,
            )

            self.assertEqual(verdict.verdict, "PASS")
            self.assertEqual(verdict.reason_codes, [])

    def test_yaml_without_pyyaml_returns_unsupported(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "drift-guard.yml"
            config_path.write_text("modules: {}\nchange_classes: {}\nrequired_docs: []\n", encoding="utf-8")

            with mock.patch.object(
                DRIFT_GUARD.importlib,
                "import_module",
                side_effect=ModuleNotFoundError("yaml"),
            ):
                with self.assertRaises(DRIFT_GUARD.DriftGuardError) as ctx:
                    DRIFT_GUARD._load_config(config_path)

            self.assertEqual(ctx.exception.reason_code, "CONFIG_YAML_UNSUPPORTED")

    def test_diff_files_decodes_quoted_non_ascii_paths(self):
        escaped = '"7-\\344\\272\\247\\347\\211\\251\\344\\270\\255\\345\\217\\260/docs/FAQ.md"'

        with mock.patch.object(DRIFT_GUARD, "_run", return_value=escaped):
            changed_files = DRIFT_GUARD._diff_files("origin/main", "HEAD")

        self.assertEqual(changed_files, ["7-产物中台/docs/FAQ.md"])


if __name__ == "__main__":
    unittest.main()
