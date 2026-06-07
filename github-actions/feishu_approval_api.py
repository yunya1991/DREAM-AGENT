import json
import urllib.request


APPROVAL_BASE_URL = "https://open.feishu.cn/open-apis/approval/v4"


def build_create_instance_body(approval_code, user_id, instance_external_id, form):
    return {
        "approval_code": approval_code,
        "user_id": user_id,
        "instance_external_id": instance_external_id,
        "form": form,
    }


def request_json(url, method, token, body=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method=method,
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def create_instance(tenant_access_token, body):
    return request_json(
        f"{APPROVAL_BASE_URL}/instances",
        "POST",
        tenant_access_token,
        body=body,
    )


def get_instance(tenant_access_token, instance_code):
    return request_json(
        f"{APPROVAL_BASE_URL}/instances/{instance_code}",
        "GET",
        tenant_access_token,
    )


def resolve_instance_status(instance, decision_id):
    status = instance.get("status", "PENDING")
    if status == "APPROVED":
        return {
            "approval_status": "approved",
            "automation_status": "running",
            "decision_summary": f"approved:{decision_id}",
        }
    if status == "REJECTED":
        return {
            "approval_status": "rejected",
            "automation_status": "paused",
            "decision_summary": f"rejected:{decision_id}",
        }
    return {
        "approval_status": "pending",
        "automation_status": "paused",
        "decision_summary": f"pending:{decision_id}",
    }


def build_status_projection(instance, decision_id, instance_code):
    resolved = resolve_instance_status(instance, decision_id)
    resolved["approval_instance_code"] = instance_code
    return resolved
