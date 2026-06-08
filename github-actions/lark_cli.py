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
    command = build_lark_command(args, identity=identity)
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        details = []
        if exc.stdout:
            details.append(f"stdout: {exc.stdout.strip()}")
        if exc.stderr:
            details.append(f"stderr: {exc.stderr.strip()}")
        detail_text = "; ".join(details) if details else "no output captured"
        raise RuntimeError(
            f"lark-cli command failed ({exc.returncode}): {' '.join(command)}; {detail_text}"
        ) from exc
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
