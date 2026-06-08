---
id: GITHUB-FEISHU-COLLABORATION-CLOSURE-REPAIR-DESIGN
type: design
owner: governance-agent
depends:
  - DREAM-AGENT-HYBRID-UNIT-DISPATCH-DESIGN
version: 1
last_verified: 2026-06-07
---

# GitHub x 飞书协作闭环修复设计

> 仓库：`DREAM-AGENT`
> 日期：`2026-06-07`
> 状态：draft
> 目标：修复 Dream-Agent 自动化执行中的协作闭环问题，确保 GitHub checks 与治理结论一致，并通过飞书建立自动化任务的监控与远程干预闭环。

## 0. 文档元信息

本文档面向以下读者：

- 负责 Dream-Agent 协作执行与治理收口的 `governance agent`
- 负责 GitHub workflow、评论模板、状态同步的自动化维护者
- 负责飞书 Base / Docs / 监控资产设计与接入的维护者
- 负责远程查看和人工干预自动化执行的用户

一句话定义如下：

> `GitHub x 飞书协作闭环修复` 是在现有 Dream-Agent 协作底座上新增一套状态一致性与远程干预模型，使 GitHub 保持执行真源，飞书成为可见监控面与轻量控制面。

## 1. 背景与问题定义

当前 Dream-Agent 自动化已经具备以下能力：

- `Hybrid Unit Dispatch` 最小闭环已落地
- GitHub PR / workflow / 结构化评论 / governance handoff 已开始形成
- 飞书侧已有 Base / OKR / Docs / Wiki 联调基础

但当前仍存在两个核心问题：

### 1.1 GitHub checks 与治理结论冲突

已经发生过以下不一致现象：

- 本地实现与测试通过
- 结构化评论或 governance handoff 给出偏绿结论
- 但 `gh pr status` 仍显示 `checks failing`

这会导致：

- “实现状态”和“协作状态”被混写
- 下游 release 判断不可靠
- 评论锚点无法作为正式治理依据

### 1.2 缺少飞书侧的自动化进度监控与远程干预

当前用户希望不仅保留 GitHub x 飞书原有协作价值，还希望通过飞书：

- 查看自动化任务当前进度
- 远程暂停自动化
- 远程重试自动化

这意味着飞书不能只是知识资产面，还需要成为自动化任务的远程监控与轻量控制面。

## 2. 设计目标

本设计的目标如下：

- 建立 GitHub checks 与治理结论的强一致性规则
- 将当前单层“完成/未完成”表达拆成多层状态模型
- 建立一张飞书 Base 监控表，用于承接自动化任务状态
- 支持飞书侧的第一版远程干预动作：`查看 + 暂停 + 重试`
- 让 GitHub 继续作为执行真源，飞书作为监控与远程干预面
- 确保在恢复自动化前，协作闭环已经稳定

成功标准如下：

- PR checks failing 时，不再出现治理评论误判为 `GREEN / READY`
- 飞书 Base 可以看到自动化任务的当前状态
- 用户可在飞书触发 `pause / retry`
- 飞书状态与 GitHub 状态保持可追溯一致
- 自动化恢复后先以单任务方式运行，不直接扩成多 agent 并行

## 3. 非目标与边界

本设计明确不做以下事项：

- 不重建 Dream-Agent 执行底座
- 不把飞书升级成执行真源
- 不在本阶段引入复杂审批流
- 不在本阶段支持任意改优先级、任意改 prompt、任意改治理结论
- 不直接推进产物中台业务模块实现

本设计的边界如下：

- 只修协作闭环，不扩业务目标
- 只支持 `查看 + 暂停 + 重试`
- 只支持飞书 Base 作为第一版监控面
- 自动化恢复前，仍以单任务或单链路试运行为主

## 4. 设计原则

### 4.1 GitHub 是执行真源

GitHub 继续承载：

- PR
- checks
- workflow run
- 结构化评论
- governance handoff

所有平台状态必须以 GitHub 真实结果为准。

### 4.2 飞书是监控与远程干预面

飞书第一版承担：

- 自动化任务可视化监控
- 远程 `pause`
- 远程 `retry`

飞书不直接决定治理结论，也不替代 GitHub checks。

### 4.3 状态分层，不再混写

系统必须将以下状态分开：

- `implementation_status`
- `platform_status`
- `governance_status`
- `automation_status`

任何评论、handoff、监控表都必须按这一分层表达。

### 4.4 治理结论必须受平台状态约束

只有在：

- 实现已完成
- 必要测试已通过
- GitHub checks 为 green

时，治理状态才允许为 `ready` 或 `released`。

### 4.5 先可见，再可控

飞书第一版建设顺序必须是：

1. 先同步状态
2. 再支持干预

不能一上来先做复杂控制动作。

## 5. 状态模型

### 5.1 实现状态

`implementation_status` 用于表达实现与本地验证阶段：

- `planned`
- `in_progress`
- `implemented`
- `tested`

### 5.2 平台状态

`platform_status` 用于表达 GitHub 真正的执行平台状态：

- `no_pr`
- `checks_pending`
- `checks_green`
- `checks_failing`
- `workflow_failed`

### 5.3 治理状态

`governance_status` 用于表达治理层结论：

- `draft`
- `review_required`
- `blocked`
- `ready`
- `released`

### 5.4 自动化状态

`automation_status` 用于表达自动化调度与执行状态：

- `idle`
- `running`
- `paused`
- `retry_requested`
- `failed`

## 6. 状态一致性规则

必须遵守以下强规则：

### 6.1 checks pending

若：

- `implementation_status=tested`
- `platform_status=checks_pending`

则：

- `governance_status=review_required`
- 不允许写 `ready`
- 不允许 release downstream

### 6.2 checks failing

若：

- `implementation_status=tested`
- `platform_status=checks_failing`

则：

- `governance_status=blocked`
- 不允许写 `GREEN`
- 不允许写 `ready`
- 不允许 release downstream

### 6.3 checks green

若：

- `implementation_status=tested`
- `platform_status=checks_green`

则：

- `governance_status` 才允许为 `ready`

### 6.4 released

只有在显式放行下游后，才允许：

- `governance_status=released`

## 7. 评论模板与治理输出规则

本设计保留四类结构化评论：

- `STARTED`
- `UPDATED`
- `VALIDATION_RESULT`
- `GOVERNANCE_HANDOFF`

### 7.1 STARTED

必须包含：

- `task_id`
- `repo`
- `branch`
- `pr_number`
- `execution_scope`
- `version_anchor`
- `planned_next_step`

### 7.2 UPDATED

必须包含：

- 本轮工作内容
- `implementation_status`
- `platform_status`
- `governance_status`
- 关键 commit
- 测试命令与结果
- blocker
- 下一步建议
- 是否需要 governance 接手

`UPDATED` 不允许越权给出最终治理放行结论。

### 7.3 VALIDATION_RESULT

必须按分层输出：

- `Implementation Status`
- `Platform Status`
- `Validation Decision`
- `Governance Recommendation`

`VALIDATION_RESULT` 允许给“验证通过”，但不允许直接代替治理放行。

### 7.4 GOVERNANCE_HANDOFF

必须至少包含：

- `implementation_status`
- `platform_status`
- `governance_status`
- `automation_status`
- `release_decision`
- `blocker`
- `required_next_action`

当 `platform_status != checks_green` 时：

- `governance_status` 不能为 `ready` 或 `released`
- `release_decision` 只能是：
  - `hold`
  - `review_required`
  - `blocked`

## 8. 飞书监控 Base 契约

第一版建议建立一张“自动化任务监控 Base”，最少字段如下：

- `task_id`
- `task_name`
- `repo`
- `branch`
- `pr_number`
- `workflow_name`
- `workflow_run_id`
- `implementation_status`
- `platform_status`
- `governance_status`
- `automation_status`
- `last_comment_anchor`
- `last_commit`
- `blocker`
- `next_action`
- `remote_action`
- `remote_action_result`
- `updated_at`

### 8.1 字段约束

- `remote_action` 只允许：
  - `none`
  - `pause`
  - `retry`
- `remote_action` 是一次性动作字段
- 动作消费后必须回写为 `none`
- `platform_status` 必须来自 GitHub 真源，不允许人工随意修改
- `governance_status` 不能在飞书侧直接人工写死

## 9. GitHub x 飞书桥接机制

系统新增一个轻量 bridge，负责两类动作：

### 9.1 GitHub -> 飞书同步

bridge 读取：

- PR 状态
- checks 状态
- workflow run 状态
- 最新结构化评论
- 最近 commit

然后：

- 计算四层状态
- 回写到飞书 Base

### 9.2 飞书 -> GitHub 控制

bridge 轮询飞书 Base 中的 `remote_action`，并执行：

- `pause`
- `retry`

随后回写：

- `remote_action_result`
- `automation_status`
- `updated_at`

最后将 `remote_action` 重置为 `none`

## 10. 远程干预动作定义

### 10.1 pause

作用：

- 暂停 scheduled task
- 阻止下一轮自动续跑

成功后回写：

- `automation_status=paused`
- `remote_action_result=pause_applied`

### 10.2 retry

作用：

- 对最近失败 workflow 执行重试
- 或重新触发一次调度

成功后回写：

- `automation_status=running`
- `remote_action_result=retry_triggered`

### 10.3 错误处理

若动作执行失败：

- 不覆盖原有 GitHub 真状态
- `remote_action_result=failed:<reason>`
- `automation_status` 保持原值或转为 `failed`

## 11. 实施顺序

本设计推荐按以下顺序落地：

1. 修 governance 判定逻辑，使 checks 状态进入治理结论计算
2. 修结构化评论模板，使状态表达统一分层
3. 建立飞书 Base 监控表结构
4. 先做 GitHub -> 飞书 单向同步
5. 再做 `pause`
6. 再做 `retry`
7. 最后以单任务方式恢复自动化试跑

## 12. 验收标准

第一版修复完成，必须同时满足：

### 12.1 GitHub 侧

- PR checks failing 时，不再出现治理结论误绿
- `GOVERNANCE_HANDOFF` 与 `gh pr status` 一致
- 评论字段完整、可追溯

### 12.2 飞书侧

- 飞书 Base 能看到自动化任务记录
- 至少展示：
  - `implementation_status`
  - `platform_status`
  - `governance_status`
  - `automation_status`
  - `blocker`
  - `next_action`

### 12.3 远程干预

- 飞书侧设置 `pause` 后，自动化可暂停
- 飞书侧设置 `retry` 后，自动化可重试
- 动作结果可在飞书中看到

### 12.4 状态一致性

- GitHub 与飞书显示的关键状态一致
- 不允许出现：
  - GitHub failing，但飞书 ready
  - 飞书 paused，但 GitHub 仍继续自动续跑

## 13. 完成后的系统形态

本设计完成后，系统应达到以下形态：

- GitHub 是执行真源
- 飞书是自动化监控与轻量干预面
- Dream-Agent 是桥接与治理内核
- 自动化可恢复，但仍先以单任务或单链路试运行

## 14. 非法状态与禁止事项

禁止以下情况：

- `checks_failing` 时写出 `GREEN / READY / RELEASED`
- 在飞书中人工改写 GitHub 真状态
- 在未建立状态同步前直接开放远程控制
- 在恢复自动化后直接扩成多 agent 并行
- 用评论语义掩盖真实平台状态
