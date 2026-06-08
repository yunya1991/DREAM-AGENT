import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "shared" / "contracts.py"
SPEC = importlib.util.spec_from_file_location("feishu_collab_contracts", MODULE_PATH)


class FeishuCollabContractsTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_event_envelope_serializes_required_fields(self):
        module = self.load_module()
        event = module.EventEnvelope(
            event_id="evt-001",
            event_type="okr.changed",
            source_system="feishu",
            source_object_id="objective-123",
            changed_fields=["title"],
            risk_hint="medium",
            related_goal_id="goal-001",
            occurred_at="2026-06-08T12:00:00+00:00",
        )
        payload = event.to_dict()
        self.assertEqual(payload["event_type"], "okr.changed")
        self.assertEqual(payload["related_goal_id"], "goal-001")

    def test_execution_preview_requires_confirmation_by_default(self):
        module = self.load_module()
        preview = module.ExecutionPreview(
            intent_id="intent-001",
            impacted_modules=["OKR", "Base"],
            actions=["refresh_projection"],
        )
        self.assertEqual(preview.requires_confirmation, True)
        self.assertEqual(preview.to_dict()["impacted_modules"], ["OKR", "Base"])

    def test_knowledge_update_keeps_evidence_refs_as_list(self):
        module = self.load_module()
        update = module.KnowledgeUpdate(
            asset_type="operations",
            title="approval timeout runbook",
            summary="Capture timeout mitigation",
            evidence_refs=["approval-instance-1", "log://worker"],
        )
        self.assertEqual(update.to_dict()["evidence_refs"][1], "log://worker")


if __name__ == "__main__":
    unittest.main()
