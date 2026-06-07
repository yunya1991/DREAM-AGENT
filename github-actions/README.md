# Agent Lifecycle Guard

本目录存放 GitHub Actions 侧使用的校验脚本与说明。

## 当前脚本

- `build_agent_lifecycle_payload.py`：把 PR 正文和结构化评论解析为标准 lifecycle payload
- `check_agent_lifecycle.py`：根据 PR 事件载荷检查任务卡、评审、评论、测试与分支规则是否齐全
- `manage_acceptance_cycle.py`：创建和推进 `acceptance_cycle` ledger 记录
- `lark_cli.py`：`lark-cli` 安全包装器
- `collect_lark_context.py`：拉取 Base / OKR 上下文快照
- `run_acceptance_cycle.py`：执行串行 4 角色验收编排
- `build_goal_progress_record.py`：把任务状态聚合成目标推进记录
- `evaluate_risk_approval_gate.py`：判断任务是否需要风险审批
- `feishu_approval_api.py`：创建和查询飞书审批实例
- `run_goal_progress_approval_cycle.py`：串起目标推进与风险审批周期

## 输入载荷字段

- `pr_body`
- `branch`
- `comments`
- `review_count`
