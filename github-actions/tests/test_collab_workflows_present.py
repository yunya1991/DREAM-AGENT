import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class CollabWorkflowPresenceTests(unittest.TestCase):
    def test_collab_workflows_exist(self):
        workflows = REPO_ROOT / ".github" / "workflows"
        required = [
            "collab-developer-agent.yml",
            "collab-validator-agent.yml",
            "collab-governance-agent.yml",
        ]
        for name in required:
            self.assertTrue((workflows / name).exists(), str(workflows / name))


class AcceptanceWorkflowPresenceTests(unittest.TestCase):
    def test_acceptance_workflow_exists(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "collab-acceptance-agent.yml"
        self.assertTrue(workflow.exists(), str(workflow))


class GovernanceWorkflowContractTests(unittest.TestCase):
    def test_governance_workflow_runs_closure_builder_and_checker(self):
        text = (
            REPO_ROOT / ".github" / "workflows" / "collab-governance-agent.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("Build collaboration closure payload", text)
        self.assertIn(
            "python3 github-actions/build_collaboration_closure_payload.py",
            text,
        )
        self.assertIn("Check collaboration closure", text)
        self.assertIn("python3 github-actions/check_collaboration_closure.py", text)


class AcceptanceWorkflowContractTests(unittest.TestCase):
    def test_acceptance_workflow_uses_cycle_and_lark_scripts(self):
        text = (
            REPO_ROOT / ".github" / "workflows" / "collab-acceptance-agent.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("python3 github-actions/manage_acceptance_cycle.py", text)
        self.assertIn("python3 github-actions/collect_lark_context.py", text)
        self.assertIn("python3 github-actions/run_acceptance_cycle.py", text)

    def test_acceptance_workflow_does_not_pin_checkout_to_main(self):
        text = (
            REPO_ROOT / ".github" / "workflows" / "collab-acceptance-agent.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("uses: actions/checkout@v4", text)
        self.assertNotIn("ref: main", text)

    def test_acceptance_workflow_injects_bot_lark_credentials(self):
        text = (
            REPO_ROOT / ".github" / "workflows" / "collab-acceptance-agent.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("LARK_IDENTITY: bot", text)
        self.assertIn("LARKSUITE_CLI_APP_ID: ${{ secrets.LARK_APP_ID }}", text)
        self.assertIn("LARKSUITE_CLI_TENANT_ACCESS_TOKEN: ${{ env.LARK_TENANT_ACCESS_TOKEN }}", text)
        self.assertIn("LARKSUITE_CLI_STRICT_MODE: off", text)
        self.assertIn("tenant_access_token/internal", text)
        self.assertIn(
            'python3 github-actions/run_acceptance_cycle.py acceptance_cycle.json > acceptance_run.json',
            text,
        )
        self.assertIn(
            "      - name: Run acceptance cycle\n        env:\n          LARK_IDENTITY: bot\n          LARKSUITE_CLI_APP_ID: ${{ secrets.LARK_APP_ID }}\n          LARKSUITE_CLI_TENANT_ACCESS_TOKEN: ${{ env.LARK_TENANT_ACCESS_TOKEN }}\n          LARKSUITE_CLI_STRICT_MODE: off",
            text,
        )

    def test_acceptance_workflow_supports_approval_smoke_mode(self):
        text = (
            REPO_ROOT / ".github" / "workflows" / "collab-acceptance-agent.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("smoke_action:", text)
        self.assertIn("approval-smoke", text)
        self.assertIn("Fetch approval definition and create instance", text)
        self.assertIn("approval_definition.json", text)
        self.assertIn("approval_instance_create.json", text)

    def test_approval_smoke_serializes_form_as_json_string(self):
        text = (
            REPO_ROOT / ".github" / "workflows" / "collab-acceptance-agent.yml"
        ).read_text(encoding="utf-8")
        self.assertIn('"form": json.dumps([])', text)
        self.assertNotIn('"form": [],', text)

    def test_approval_smoke_fails_on_http_errors(self):
        text = (
            REPO_ROOT / ".github" / "workflows" / "collab-acceptance-agent.yml"
        ).read_text(encoding="utf-8")
        self.assertIn('if created.get("http_status") or created.get("code") not in (0, None):', text)


if __name__ == "__main__":
    unittest.main()
