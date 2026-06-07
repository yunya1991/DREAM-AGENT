import json
import subprocess


def build_lark_command(args: list[str], identity: str = "user") -> list[str]:
    return ["lark-cli", *args, "--as", identity, "--format", "json"]


def run_lark_json(args: list[str], identity: str = "user") -> dict:
    result = subprocess.run(
        build_lark_command(args, identity=identity),
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def ensure_lark_auth(identity: str = "user") -> None:
    try:
        subprocess.run(
            ["lark-cli", "auth", "status"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        output = f"{exc.output or ''}\n{exc.stderr or ''}".lower()
        if exc.returncode in (2, 3) and not output.strip():
            return
        if (
            "external credentials" not in output
            and "credentials are provided externally" not in output
            and "provided externally" not in output
            and "do not support interactive management" not in output
        ):
            raise
