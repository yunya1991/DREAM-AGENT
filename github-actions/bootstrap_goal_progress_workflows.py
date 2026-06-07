import json
import sys
import time


REQUIRED_FIELDS = [
    "当前阻塞",
    "风险等级",
    "approval_status",
    "OKR对齐",
    "目标负责人",
    "OKR负责人",
]


def require_fields(field_ids):
    missing = [name for name in REQUIRED_FIELDS if name not in field_ids]
    if missing:
        raise ValueError(f"missing workflow fields: {', '.join(missing)}")


def build_ref(trigger_id, field_id):
    return f"$.{trigger_id}.{field_id}"


def build_typed_values(*values):
    return [{"value": value, "value_type": "text"} for value in values]


def build_condition(field_name, operator, value=None):
    if value is None:
        value = []
    return {"field_name": field_name, "operator": operator, "value": value}


def build_change_record_trigger(
    step_id, title, next_step, table_name, condition_list, trigger_control_list
):
    return {
        "id": step_id,
        "type": "ChangeRecordTrigger",
        "title": title,
        "next": next_step,
        "data": {
            "table_name": table_name,
            "condition_list": condition_list,
            "trigger_control_list": trigger_control_list,
        },
    }


def build_workflow_specs(table_name, field_ids):
    require_fields(field_ids)
    blocker_ref = build_ref("trigger_blocker", field_ids["目标负责人"])
    approval_ref = build_ref("trigger_approval", field_ids["目标负责人"])
    okr_owner_ref = build_ref("trigger_okr", field_ids["OKR负责人"])
    return [
        {
            "client_token": f"goal-blocker-{int(time.time())}",
            "title": "阻塞升级提醒",
            "steps": [
                build_change_record_trigger(
                    step_id="trigger_blocker",
                    title="监控高风险阻塞",
                    next_step="notify_goal_owner",
                    table_name=table_name,
                    condition_list=[
                        {
                            "conjunction": "and",
                            "conditions": [
                                build_condition("当前阻塞", "isNotEmpty"),
                                build_condition(
                                    "风险等级",
                                    "is",
                                    build_typed_values("high"),
                                ),
                            ],
                        },
                    ],
                    trigger_control_list=[
                        field_ids["当前阻塞"],
                        field_ids["风险等级"],
                    ],
                ),
                {
                    "id": "notify_goal_owner",
                    "type": "LarkMessageAction",
                    "title": "提醒目标负责人",
                    "next": None,
                    "data": {
                        "receiver": [{"value_type": "ref", "value": blocker_ref}],
                        "send_to_everyone": False,
                        "title": [{"value_type": "text", "value": "目标阻塞升级提醒"}],
                        "content": [
                            {
                                "value_type": "text",
                                "value": "当前目标存在高风险阻塞，请更新目标推进表。",
                            }
                        ],
                        "btn_list": [],
                    },
                },
            ],
        },
        {
            "client_token": f"goal-approval-{int(time.time()) + 1}",
            "title": "审批完成提醒更新目标",
            "steps": [
                build_change_record_trigger(
                    step_id="trigger_approval",
                    title="监控审批状态终态",
                    next_step="notify_after_approval",
                    table_name=table_name,
                    condition_list=[
                        {
                            "conjunction": "and",
                            "conditions": [
                                build_condition(
                                    "approval_status",
                                    "isAnyOf",
                                    build_typed_values("approved", "rejected"),
                                )
                            ],
                        }
                    ],
                    trigger_control_list=[field_ids["approval_status"]],
                ),
                {
                    "id": "notify_after_approval",
                    "type": "LarkMessageAction",
                    "title": "提醒更新目标状态",
                    "next": None,
                    "data": {
                        "receiver": [{"value_type": "ref", "value": approval_ref}],
                        "send_to_everyone": False,
                        "title": [{"value_type": "text", "value": "审批完成，请更新目标"}],
                        "content": [
                            {
                                "value_type": "text",
                                "value": "审批状态已变化，请同步当前状态、下一步动作与 OKR 对齐。",
                            }
                        ],
                        "btn_list": [],
                    },
                },
            ],
        },
        {
            "client_token": f"goal-okr-{int(time.time()) + 2}",
            "title": "OKR对齐缺失提醒",
            "steps": [
                build_change_record_trigger(
                    step_id="trigger_okr",
                    title="监控 OKR 对齐缺失",
                    next_step="notify_okr_owner",
                    table_name=table_name,
                    condition_list=[
                        {
                            "conjunction": "and",
                            "conditions": [
                                build_condition("OKR对齐", "isEmpty")
                            ],
                        }
                    ],
                    trigger_control_list=[field_ids["OKR对齐"]],
                ),
                {
                    "id": "notify_okr_owner",
                    "type": "LarkMessageAction",
                    "title": "提醒补齐 OKR",
                    "next": None,
                    "data": {
                        "receiver": [{"value_type": "ref", "value": okr_owner_ref}],
                        "send_to_everyone": False,
                        "title": [{"value_type": "text", "value": "目标尚未完成 OKR 对齐"}],
                        "content": [
                            {
                                "value_type": "text",
                                "value": "该目标已进入推进中，但仍未完成 OKR 对齐，请补齐 Objective 或说明异常。",
                            }
                        ],
                        "btn_list": [],
                    },
                },
            ],
        },
    ]


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        build_workflow_specs(payload["table_name"], payload["field_ids"]),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")
