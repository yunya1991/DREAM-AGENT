import json
import os
import subprocess


def get_lark_identity(default: str = "user") -> str:
    value = os.environ.get("LARK_IDENTITY", default).strip()
    return value or default


def build_lark_command(args: list[str], identity: str | None = None) -> list[str]:
    identity = identity or get_lark_identity()
    return ["lark-cli", *args, "--as", identity, "--format", "json"]


def run_lark_json(args: list[str], identity: str | None = None) -> dict:
    result = subprocess.run(
        build_lark_command(args, identity=identity),
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def ensure_lark_auth(identity: str = "user") -> None:
    if (
        identity == "bot"
        and os.environ.get("LARKSUITE_CLI_APP_ID")
        and (
            os.environ.get("LARKSUITE_CLI_APP_SECRET")
            or os.environ.get("LARKSUITE_CLI_TENANT_ACCESS_TOKEN")
        )
    ):
        return
    try:
        subprocess.run(
            ["lark-cli", "auth", "status"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        output = f"{exc.output or ''}\n{exc.stderr or ''}".lower()
        if exc.returncode in (2, 3):
            return
        if (
            "external credentials" not in output
            and "credentials are provided externally" not in output
            and "provided externally" not in output
            and "do not support interactive management" not in output
        ):
            raise
