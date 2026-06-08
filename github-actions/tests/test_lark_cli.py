import importlib.util
import os
import subprocess
import unittest
from pathlib import Path
from unittest import mock


LARK_CLI_PATH = Path(__file__).resolve().parents[1] / "lark_cli.py"
LARK_CLI_SPEC = importlib.util.spec_from_file_location("lark_cli", LARK_CLI_PATH)
LARK_CLI = importlib.util.module_from_spec(LARK_CLI_SPEC)
LARK_CLI_SPEC.loader.exec_module(LARK_CLI)


class LarkCliTests(unittest.TestCase):
    def test_get_lark_identity_defaults_to_user(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            self.assertEqual(LARK_CLI.get_lark_identity(), "user")

    def test_get_lark_identity_reads_environment_override(self):
        with mock.patch.dict(os.environ, {"LARK_IDENTITY": "bot"}, clear=False):
            self.assertEqual(LARK_CLI.get_lark_identity(), "bot")

    def test_build_command_appends_identity_and_json_output(self):
        argv = LARK_CLI.build_lark_command(
            ["base", "+record-get", "--base-token", "app123"],
            identity="user",
        )

        self.assertEqual(argv[:3], ["lark-cli", "base", "+record-get"])
        self.assertIn("--as", argv)
        self.assertEqual(argv[-2:], ["--format", "json"])

    @mock.patch.object(LARK_CLI.subprocess, "run")
    def test_ensure_lark_auth_uses_plain_auth_status_and_allows_external_provided_credentials(
        self, mock_run
    ):
        mock_run.side_effect = subprocess.CalledProcessError(
            1,
            ["lark-cli", "auth", "status"],
            output="",
            stderr="credentials are provided externally",
        )

        LARK_CLI.ensure_lark_auth(identity="user")

        mock_run.assert_called_once_with(
            ["lark-cli", "auth", "status"],
            check=True,
            capture_output=True,
            text=True,
        )

    @mock.patch.object(LARK_CLI.subprocess, "run")
    def test_ensure_lark_auth_allows_external_management_exit_code_without_message(
        self, mock_run
    ):
        mock_run.side_effect = subprocess.CalledProcessError(
            3,
            ["lark-cli", "auth", "status"],
            output="",
            stderr="",
        )

        LARK_CLI.ensure_lark_auth(identity="user")

    @mock.patch.object(LARK_CLI.subprocess, "run")
    def test_ensure_lark_auth_allows_external_management_exit_code_with_unexpected_output(
        self, mock_run
    ):
        mock_run.side_effect = subprocess.CalledProcessError(
            3,
            ["lark-cli", "auth", "status"],
            output='{"ok": false}',
            stderr="runner-managed credentials",
        )

        LARK_CLI.ensure_lark_auth(identity="user")

    @mock.patch.object(LARK_CLI.subprocess, "run")
    def test_ensure_lark_auth_skips_status_when_bot_env_credentials_exist(self, mock_run):
        with mock.patch.dict(
            os.environ,
            {
                "LARKSUITE_CLI_APP_ID": "cli_123",
                "LARKSUITE_CLI_APP_SECRET": "secret_123",
            },
            clear=False,
        ):
            LARK_CLI.ensure_lark_auth(identity="bot")

        mock_run.assert_not_called()

    @mock.patch.object(LARK_CLI.subprocess, "run")
    def test_ensure_lark_auth_skips_status_when_bot_env_token_exists(self, mock_run):
        with mock.patch.dict(
            os.environ,
            {
                "LARKSUITE_CLI_APP_ID": "cli_123",
                "LARKSUITE_CLI_TENANT_ACCESS_TOKEN": "tat_123",
            },
            clear=False,
        ):
            LARK_CLI.ensure_lark_auth(identity="bot")

        mock_run.assert_not_called()

    @mock.patch.object(LARK_CLI.subprocess, "run")
    def test_run_lark_json_surfaces_stdout_and_stderr_on_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(
            3,
            ["lark-cli", "base", "+record-upsert"],
            output='{"hint":"stdout"}',
            stderr="permission denied",
        )

        with self.assertRaisesRegex(RuntimeError, "permission denied"):
            LARK_CLI.run_lark_json(["base", "+record-upsert"], identity="bot")


if __name__ == "__main__":
    unittest.main()
