---
id: PROJECT-PROGRESS-APPROVAL-DEFINITION
type: runbook
owner: collab-protocol-agent
version: 1
last_verified: 2026-06-10
---

# 项目进度审批（OKR + 多维表格驱动）定义与用法

## 1. 目标

把“审批”从通用的物品领用类单据，升级为贴近主线协作的“项目/模块进度审批”，确保审批单天然包含：

- 审什么：Goal/Task/模块/变更范围
- 为什么审：触发原因、风险等级、影响面
- 审批建议：推荐选项、回滚与下一步动作

并且能被自动化链路自动填充，避免人工重复录入。

## 2. 权限与身份（强约束）

### 2.1 user_access_token（用户身份）

用于操作者手工核验与排查：

- `approval:instance:read`：读取审批实例详情
- `approval:task:read`：读取“我的待办/已办”任务列表（定位你刚收到的审批类型非常关键）

注意：

- 仅“后台开通 scope”不够，必须让系统重新签发包含新 scope 的 `user_access_token`。
- 若当前运行环境不支持交互式 `auth login`，必须通过“连接器重新授权 + 重启会话/Agent”刷新注入的 user token。

### 2.2 tenant_access_token（应用/租户身份）

用于 GitHub Actions 中的真实链路执行（创建/查询审批实例、写回 Base），不依赖用户 token。

## 3. 审批定义（飞书审批后台配置）

在飞书审批后台新建一个审批定义，推荐命名：

- 名称：`项目进度审批`
- 分组：`研发协作`
- 适用：用于 Dreambuddy-V2 主线的 Gate A/B 与高风险变更 gate

### 3.1 表单控件（建议最小集）

建议至少包含以下控件（控件类型仅供参考，可按团队习惯调整）：

- `decision_id`（单行文本）：对应 `task_id`，用于链路决策主键
- `goal_id`（单行文本）：对应 `goal_id`
- `okr_objective_id`（单行文本）
- `okr_objective_title`（多行文本/只读文本）
- `module_key`（单行文本）
- `module_paths`（多行文本）：repo 相对路径列表
- `spec_doc`（单行文本/链接）：Spec 文档路径/链接
- `plan_doc`（单行文本/链接）：Plan 文档路径/链接
- `risk_level`（单选）：low/medium/high/critical
- `change_scope`（单选/单行文本）：release_handoff/rollback/goal_switch/…
- `trigger_reason`（多行文本）：为什么需要审批（由 gate 计算）
- `recommended_option`（多行文本）：审批建议（推荐选项 + 依据）
- `rollback_plan`（多行文本）：回滚/止损方案
- `next_action`（多行文本）：通过/拒绝后的下一步动作

### 3.2 控件 ID 获取（必须做，禁止猜）

我们调用审批 API 时，`form` 里的 `id` 必须匹配审批定义中的真实控件 ID，否则会出现类似：

`审批定义中未找到表单控件 … ID=<xxx>`

获取方式（任选其一）：

1) 在审批后台查看控件详情里的控件 ID（若 UI 支持展示）
2) 手工发起一张该审批定义的测试单，拿到 `instance_code`，再用 `instances.get` 读取 `form` 并解析出控件 id 列表

## 4. 自动化填单约定（工作流输入）

GitHub Actions 的真实审批触发支持在 task payload 中传入 `approval_form`（数组），用于把字段精准写入审批表单：

```json
{
  "task_id": "task-xxx",
  "goal_id": "goal-xxx",
  "approval_form": [
    {"id":"decision_id","type":"textarea","value":"task-xxx"},
    {"id":"goal_id","type":"textarea","value":"goal-xxx"},
    {"id":"trigger_reason","type":"textarea","value":"high_risk_scope:release_handoff"},
    {"id":"recommended_option","type":"textarea","value":"建议：暂停并等待人工确认；依据：发布交接属于高风险变更"},
    {"id":"next_action","type":"textarea","value":"审批通过后切换模块任务到 in_progress"}
  ]
}
```

要求：

- `approval_form[*].id` 必须来自“3.2 控件 ID 获取”的真实结果
- `value` 由 OKR + Base 字段映射生成，Agent 只需要改内容，不需要改结构

## 5. 与 OKR / Base 的映射（最小必须可复述）

### 5.1 审什么

- `goal_id`（目标推进表）
- `task_id`（模块任务表）
- `okr_objective_id/okr_objective_title`（目标推进表 OKR 对齐字段）
- `module_key/module_paths/spec_doc/plan_doc`（模块任务表）

### 5.2 为什么审

由 gate 计算并写入：

- `risk_level`
- `change_scope`
- `trigger_reason`

### 5.3 审批建议

由 gate 给出并写入：

- `recommended_option`
- `rollback_plan`
- `next_action`

## 6. 验证标准（跑一次完整链路）

一次完整链路至少包含：

1) 创建审批实例成功，产物里拿到非空 `approval_instance_code`
2) `approval_status_result.json` 可读到当前状态（pending/approved/rejected）
3) polling/writeback 成功写回 Base 三表
4) 回读 Base 三表记录，与审批状态一致

