---
id: LIFECYCLE-GUARD-COMPATIBILITY-V2-DESIGN
type: design
owner: ledger-protocol-agent
depends:
  - 01-COLLABORATION-PROTOCOL
  - 03-WORKFLOWS-AND-NORMS
  - ACCEPTANCE-REQUEST-PROTOCOL-DESIGN
version: 1
last_verified: 2026-06-07
---

# Agent Lifecycle Guard Compatibility V2 设计

> 仓库：`DREAM-AGENT`
> 日期：2026-06-07
> 状态：v1 候选稿
> 目标：让 `Agent Lifecycle Guard` 在保留旧交付流的同时，正式兼容 `ACCEPTANCE_REQUEST -> VALIDATION_RESULT` 新验收流，避免旧 guard 对新协议持续误报。

## 0. 背景

当前 `DREAM-AGENT` 中已经存在一条旧的生命周期监督链：

- `STARTED`
- `UPDATED`
- `BLOCKED`
- `DESIGN_REVIEW`
- `TEST_REPORT`
- `DONE`

这条链由以下部件支撑：

- [agent-lifecycle-guard.yml](file:///Users/zhangjiangtao/WorkBuddy/DREAM-AGENT/.github/workflows/agent-lifecycle-guard.yml)
- [build_agent_lifecycle_payload.py](file:///Users/zhangjiangtao/WorkBuddy/DREAM-AGENT/github-actions/build_agent_lifecycle_payload.py)
- [check_agent_lifecycle.py](file:///Users/zhangjiangtao/WorkBuddy/DREAM-AGENT/github-actions/check_agent_lifecycle.py)
- [rules.json](file:///Users/zhangjiangtao/WorkBuddy/DREAM-AGENT/SKILLS/agent-collab-supervisor/rules.json)

同时，仓库刚刚新增了新的专项验收协议：

- `ACCEPTANCE_REQUEST`
- `VALIDATION_RESULT`

该协议的目的是把“提交后专项验收”从旧的交付流中拆出来，使：

- `DONE != ACCEPTED`
- `ACCEPTANCE_REQUEST` 成为专项验收真源
- `VALIDATION_RESULT` 成为正式验收结论

问题在于：当前 `Agent Lifecycle Guard` 只理解旧锚点，不理解新锚点。

因此，当 PR 采用新验收协议推进时，guard 仍会把它当作“缺少 STARTED / DONE / DESIGN_REVIEW / TEST_REPORT”的违规流程，并持续发送失败通知。

这不是新协议本身失败，而是旧 guard 尚未兼容新协议。

## 1. 设计目标

本次设计目标如下：

- 让 `Agent Lifecycle Guard` 同时支持两条合法协作流：
  - `Legacy Delivery Flow`
  - `Acceptance Flow`
- 首版判定逻辑采用：
  - 满足任一合法流即通过
- 保留一组共同底线检查，避免兼容升级变成完全放开
- 放宽分支策略，使当前真实使用中的 `design/`、`acceptance/`、`protocol/` 分支合法
- 尽量以增量方式改造现有 payload builder / checker / rules，而不是推翻重写

## 2. 非目标

本次设计明确不包含以下内容：

- 不废弃旧交付流
- 不要求所有 PR 立刻切换为新验收流
- 不在本次中引入多 agent 编排系统
- 不把 lifecycle guard 和 acceptance workflow 合并成单一巨型 workflow
- 不要求 lifecycle guard 自身执行复杂业务测试

## 3. 核心结论

### 3.1 双轨兼容，而不是替换

首版选择：

- 旧交付流继续可用
- 新验收流也成为合法路径
- guard 只要识别到“共同底线通过 + 任一合法流通过”，就判定通过

这是最稳的升级路径，因为：

- 可以避免旧协作任务全部返工
- 可以让新验收协议逐步接入
- 不会因为一次协议升级把所有现有协作流程打断

### 3.2 `DONE` 与 `ACCEPTED` 必须继续分离

兼容升级不能回退 `DONE != ACCEPTED` 这一原则。

因此：

- `DONE` 仍代表开发交付完成
- `VALIDATION_RESULT` 仍代表验收结论
- `ACCEPTANCE_REQUEST -> VALIDATION_RESULT` 必须被视为一条独立的合法链路

### 3.3 Guard 首版的判定应当简洁可解释

首版不要做“加权评分 + 多层 fallback + 隐式推断”。

推荐判定方式：

1. 先检查共同底线
2. 再检查旧交付流
3. 再检查新验收流
4. 若共同底线通过，且 `legacy_flow_pass == true` 或 `acceptance_flow_pass == true`，则总体通过
5. 若都不通过，则返回清晰 reason codes

## 4. 共同底线

以下规则建议保留为所有流共享的底线：

### 4.1 Task Card 必须存在

保留：

- `RULE_001_TASK_CARD_REQUIRED`

原因：

- 无论走哪条流，PR 都必须有明确任务上下文。

### 4.2 Shared Files Declaration 必须存在

保留：

- `RULE_010_SHARED_FILE_DECLARATION`

原因：

- 这属于协作透明度要求，不应因采用新验收流而取消。

### 4.3 Branch Policy 放宽但继续保留

现有实现只允许：

- `agent/`
- `milestone/`

这与当前实际使用不符。首版改为允许：

- `agent/`
- `milestone/`
- `design/`
- `acceptance/`
- `protocol/`

这样既保留分支规则，又避免对现实分支命名误报。

## 5. Legacy Delivery Flow

旧交付流保持现有语义，适用于传统开发交付型 PR。

建议保留以下要求：

- `STARTED`
- `DESIGN_REVIEW`
- `TEST_REPORT`
- `DONE`
- `REVIEW_BY_NON_OWNER`
- scope change / blocked announcement 规则

也就是说，旧流仍然是：

- 开工声明
- 设计评审
- 测试报告
- 完成回报
- 非 owner review

它的价值没有消失，只是不再是唯一合法路径。

## 6. Acceptance Flow

新增一条合法协作流：

- `ACCEPTANCE_REQUEST -> VALIDATION_RESULT`

### 6.1 Acceptance Flow 的最小通过条件

首版建议最小条件如下：

- 存在结构化 `ACCEPTANCE_REQUEST`
- 存在结构化 `VALIDATION_RESULT`
- `VALIDATION_RESULT` 的 `Decision` 不是阻塞态

首版不要求：

- acceptance flow 必须同时存在 `STARTED`
- acceptance flow 必须同时存在 `DONE`
- acceptance flow 必须同时存在旧式 `TEST_REPORT`

因为这会把新流重新绑回旧流，失去引入新协议的意义。

### 6.2 Acceptance Flow 的语义

Acceptance Flow 不是“没有流程约束的宽松模式”。

它依然要求：

- 有明确验收对象
- 有明确验收范围
- 有明确重点验收项
- 有结构化结论

只是它强调的是“专项验收闭环”，而不是“传统交付生命周期广播”。

## 7. Payload Builder 升级方向

当前 [build_agent_lifecycle_payload.py](file:///Users/zhangjiangtao/WorkBuddy/DREAM-AGENT/github-actions/build_agent_lifecycle_payload.py) 只识别旧评论头：

- `STARTED`
- `UPDATED`
- `BLOCKED`
- `DONE`
- `DESIGN_REVIEW`
- `TEST_REPORT`

首版升级建议：

### 7.1 新增头部映射

新增：

- `[验收委托 / ACCEPTANCE_REQUEST]` -> `ACCEPTANCE_REQUEST`
- `[验证结论 / VALIDATION_RESULT]` -> `VALIDATION_RESULT`

### 7.2 新增 payload 字段

建议新增：

- `acceptance_request_present`
- `validation_result_present`
- `validation_decision`
- `validation_mode`
- `acceptance_flow_closed`
- `legacy_flow_present`
- `acceptance_flow_present`

### 7.3 保留旧字段

现有字段继续保留，避免破坏旧规则：

- `design_review_present`
- `test_report_present`
- `comments`
- `owner_agent`
- `shared_files_declared`

## 8. Checker 升级方向

当前 [check_agent_lifecycle.py](file:///Users/zhangjiangtao/WorkBuddy/DREAM-AGENT/github-actions/check_agent_lifecycle.py) 的结构是：

- 逐条旧规则检查
- 任一失败即 `BLOCK`

首版建议重构为三段式：

### 8.1 Common Baseline

检查：

- `task_card_present`
- `shared_files_declared`
- `branch_policy_valid`

### 8.2 Legacy Delivery Flow

检查：

- `started_comment_present`
- `design_review_present`
- `test_report_present`
- `done_comment_present`
- `non_owner_review_present`
- `scope/block` 相关规则

### 8.3 Acceptance Flow

检查：

- `acceptance_request_present`
- `validation_result_present`
- `validation_decision` 非阻塞

### 8.4 最终判定

建议伪逻辑：

```text
if not common_baseline_pass:
    BLOCK
elif legacy_flow_pass or acceptance_flow_pass:
    PASS
else:
    BLOCK
```

这样能保证：

- 不破坏旧流
- 新流独立成立
- 共用底线仍存在

## 9. Rules 迁移策略

现有 [rules.json](file:///Users/zhangjiangtao/WorkBuddy/DREAM-AGENT/SKILLS/agent-collab-supervisor/rules.json) 是“单规则数组”模型。

首版不建议继续把所有兼容逻辑硬塞进原来的单层 rule 列表。

推荐升级为以下两种方式之一：

### 9.1 轻量方案

- 继续保留 `rules.json`
- 但将“流判定”从 `rules.json` 挪到 Python checker 里完成
- `rules.json` 只保留共同底线和旧兼容说明

这是首版推荐方案，因为变更最小。

### 9.2 结构化方案

- 将规则拆为：
  - `common_rules`
  - `legacy_flow_rules`
  - `acceptance_flow_rules`

这更清晰，但会带来更大迁移面，不适合首版。

## 10. Reason Codes 升级方向

首版建议新增以下 reason codes：

- `RULE_ACCEPTANCE_REQUEST_REQUIRED`
- `RULE_VALIDATION_RESULT_REQUIRED`
- `RULE_ACCEPTANCE_FLOW_NOT_CLOSED`
- `RULE_ACCEPTANCE_VALIDATION_BLOCKED`
- `RULE_BRANCH_POLICY_NOT_ALLOWED`

同时保留旧 reason codes，以便兼容旧审计记录。

## 11. Review 规则如何兼容

最敏感的一条是：

- `RULE_007_REVIEW_BY_NON_OWNER`

在旧流里，它要求存在非 owner 的 `DESIGN_REVIEW`。

在新流里，这条规则需要重构为：

- 旧流：仍要求非 owner `DESIGN_REVIEW`
- 新流：允许非 owner 的验收 reviewer 或外部 validator 结论作为等价 review evidence

但首版为了避免过大范围，可以先采用更保守的策略：

- 当走 acceptance flow 时，暂不强制这条规则
- 在 `Acceptance Orchestration V2` 再把多 agent reviewer 机制正式接进来

## 12. 为什么当前 PR 会误报

本设计需要直接回应当前问题。

PR #5 中，旧 guard 失败的根因不是代码坏，而是协议不兼容：

- `STARTED` 没有用旧评论格式发出
- `DONE` 没有用旧评论格式发出
- `DESIGN_REVIEW` / `TEST_REPORT` 只出现在 PR body，不在旧 guard 认可的结构化评论里
- 分支前缀 `design/` 不在旧 branch policy 白名单里
- `ACCEPTANCE_REQUEST` / `VALIDATION_RESULT` 尚未被旧 guard 识别

因此兼容升级的目标，就是消除这类“新流被旧 guard 误报”的问题。

## 13. 风险与缓解

### 13.1 风险：兼容逻辑过于复杂

缓解：

- 首版只做“共同底线 + 任一合法流通过”
- 不做复杂评分体系

### 13.2 风险：旧流被误伤

缓解：

- 保持旧流规则和旧评论头不变
- 通过单元测试锁定旧流行为

### 13.3 风险：新流过于宽松

缓解：

- 要求必须存在 `ACCEPTANCE_REQUEST` 和 `VALIDATION_RESULT`
- 要求 `VALIDATION_RESULT` 不是阻塞结论
- 继续保留共同底线规则

## 14. 成功标准

兼容升级首版视为成功，需要满足：

- `Agent Lifecycle Guard` 不再对合法的新验收流 PR 误报失败
- 旧交付流 PR 仍然可以按旧规则通过
- `design/`、`acceptance/`、`protocol/` 分支不再被误判为非法
- payload builder 能识别 `ACCEPTANCE_REQUEST` 和 `VALIDATION_RESULT`
- checker 能正确做出“双轨兼容”判定

## 15. 最终结论

本次兼容升级设计的最终结论是：

- 首版采用双轨兼容，而不是替换旧流
- 判定策略采用“共同底线通过 + 任一合法流通过”
- branch policy 放宽为多前缀合法
- `ACCEPTANCE_REQUEST -> VALIDATION_RESULT` 正式成为 lifecycle guard 认可的合法协作路径
- 多 agent 验收协作的进一步强化，不放在本次首版里，而留给 `Acceptance Orchestration V2`
