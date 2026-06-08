import importlib.util
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent


def load_module(name, file_name):
    path = HERE / file_name
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


APPROVAL_API = load_module("feishu_approval_api", "feishu_approval_api.py")


def build_status_result(instance, decision_id, instance_code):
    result = APPROVAL_API.build_status_projection(instance, decision_id, instance_code)
    result["approval_instance_code"] = instance_code
    return result


def main():
    payload = json.load(sys.stdin)
    instance = APPROVAL_API.get_instance(
        payload.get("tenant_access_token", ""),
        payload.get("approval_instance_code", ""),
    )
    result = build_status_result(
        instance=instance,
        decision_id=payload.get("decision_id", ""),
        instance_code=payload.get("approval_instance_code", ""),
    )
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
