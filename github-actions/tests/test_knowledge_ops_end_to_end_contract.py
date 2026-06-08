import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INTAKE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "intake.py"
VALIDATE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "validate_knowledge_asset.py"
CHECK_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "check_knowledge_assets.py"
MATERIALIZE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "materialize_knowledge_asset.py"
VERIFY_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "verify_knowledge_asset.py"


def load_module(module_path, name):
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class KnowledgeOpsEndToEndContractTests(unittest.TestCase):
    def test_end_to_end_payload_shapes_align(self):
        intake_module = load_module(INTAKE_PATH, "knowledge_intake")
        validate_module = load_module(VALIDATE_PATH, "validate_knowledge_asset")
        check_module = load_module(CHECK_PATH, "check_knowledge_assets")
        materialize_module = load_module(MATERIALIZE_PATH, "materialize_knowledge_asset")
        verify_module = load_module(VERIFY_PATH, "verify_knowledge_asset")

        intake = intake_module.normalize_knowledge_intake(
            knowledge_update={
                "asset_type": "operations",
                "title": "Approval timeout recovery",
                "summary": "Manual recovery path for timed-out approvals",
                "evidence_refs": ["task-approval-001"],
            },
            handoff_context={"source_skill": "feishu-collab-approval", "handoff_summary": "manual review"},
        )
        validation = validate_module.validate_knowledge_asset(intake)
        checks = check_module.check_knowledge_assets(
            intake=intake,
            validation_report=validation,
            existing_state={"index_contains_target": True, "stale_hint": False},
        )
        preview = {
            "intake_summary": intake,
            "asset_target_candidate": {
                "target_path": "docs/feishu-collab/runbooks/approval-timeout-recovery.md",
                "template_type": validation["template_type"],
                "index_target": "docs/feishu-collab/RUNBOOK_INDEX.md",
                "allow_overwrite": False,
            },
            "validation_report": validation,
            "check_report": checks,
            "risk_flags": validation["risk_flags"],
            "requires_confirmation": True,
        }
        execution = materialize_module.materialize_knowledge_asset(preview)
        verification = verify_module.verify_knowledge_asset(
            asset_target=execution["asset_target"],
            validation_report=execution["validation_report"],
            check_report=execution["check_report"],
            existing_state={"target_exists": True, "index_aligned": True},
        )

        self.assertEqual(execution["status"], "confirmed")
        self.assertEqual(verification["status"], "confirmed")


if __name__ == "__main__":
    unittest.main()
