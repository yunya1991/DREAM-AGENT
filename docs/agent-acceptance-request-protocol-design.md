---
id: ACCEPTANCE-REQUEST-PROTOCOL-DESIGN
type: design
owner: ledger-protocol-agent
depends:
  - 01-COLLABORATION-PROTOCOL
  - 03-WORKFLOWS-AND-NORMS
version: 1
last_verified: 2026-06-07
---

# ACCEPTANCE_REQUEST 协议扩容设计

> 仓库：`DREAM-AGENT`
> 日期：2026-06-07
> 状态：v1 候选稿
> 目标：在不推翻现有协作协议的前提下，把“提交后专项验收”纳入现有 PR 评论与 validator 流程，使验收请求、验收结论和下次开发前置读取形成标准闭环。

## 0. 背景

当前 `DREAM-AGENT` 已经具备一套以 PR 评论为锚点的协作协议，核心执行线锚点包括：

- `[协作开工声明 / STARTED]`
- `[协作状态更新 / UPDATED]`
- `[协作阻塞通知 / BLOCKED]`
- `[方案评审记录 / DESIGN_REVIEW]`
- `[测试报告 / TEST_REPORT]`
- `[验证结论 / VALIDATION_RESULT]`
- `[协作完成回报 / DONE]`

同时，现有工作流已经支持“评论触发 validator 并回写 `VALIDATION_RESULT`”这一类行为，例如：

- `collab-validator-agent.yml`
- `pr9-validator-agent.yml`

但现有协议默认更偏向“开发完成后的验证”，主要链路是：

- `DONE -> VALIDATION_RESULT`

这会带来三个不足：

1. 验收关注点往往只能事后从提交记录、聊天记录、PR 描述中反推，缺少统一真源。
2. `DONE` 很容易被误解为“已验收通过”，而不是“开发交付完成”。
3. 下次继续开发前，没有一个固定的“先读上次验收结论”的前置门禁。

因此，需要在现有协议中新增一个专门服务于“提交后专项验收”的评论锚点：

- `[验收委托 / ACCEPTANCE_REQUEST]`

并将现有 `VALIDATION_RESULT` 从“泛化的验证结果”增强为“可服务于专项验收与后续开发前置读取”的正式结论锚点。

## 1. 设计目标

本次设计只做协议中枢扩容，不做业务仓库自动化改造。

v1 目标如下：

- 在 `DREAM-AGENT` 中正式引入 `ACCEPTANCE_REQUEST` 评论模板；
- 让 `VALIDATION_RESULT` 可表达专项验收结果，而不仅是 build/test 成败；
- 明确 `DONE != ACCEPTED`，拆开“开发交付完成”与“验收通过”；
- 建立“下一次开发开始前，先读取最近 `VALIDATION_RESULT`”的前置规则；
- 保持与现有 `STARTED / UPDATED / BLOCKED / DONE / VALIDATION_RESULT` 协议兼容。

## 2. 非目标

本次设计明确不包含以下内容：

- 不在 v1 中改造业务仓库自动化执行复杂验收；
- 不在 v1 中引入跨仓库自动调度器；
- 不在 v1 中要求 validator 直接完成真实浏览器交互、真实后端联调或复杂集成测试；
- 不将 `DREAM-AGENT` 改造成业务执行仓库；
- 不废弃现有 `DONE`、`TEST_REPORT` 或 `VALIDATION_RESULT` 模板。

## 3. 核心决策

### 3.1 保留 PR 评论作为唯一协作接口

延续现有原则：

- 结构化 PR 评论是 canonical collaboration interface。

新增的 `ACCEPTANCE_REQUEST` 也必须遵循这一原则。

这意味着：

- 本次专项验收的目标、范围、重点项、基线链接，应以该评论为唯一真源；
- validator 不再优先从聊天记录、提交记录或 PR 描述中猜测验收目标；
- 如评论未给出关键字段，视为协议不完整，而不是让 validator 自行补全。

### 3.2 新增独立锚点：ACCEPTANCE_REQUEST

在现有执行线锚点中新增：

- `[验收委托 / ACCEPTANCE_REQUEST]`

该锚点的职责是：

- 宣告“本次需要专项验收”；
- 明确说明“验什么、不验什么、对照什么基线验”；
- 为 validator 提供稳定、结构化的输入源。

### 3.3 DONE 不再隐含通过

必须明确：

- `DONE` 表示开发交付完成；
- `VALIDATION_RESULT` 表示验收结论；
- `DONE != ACCEPTED`

这样做的目的是避免“自己做、自己说完成、流程就默认算通过”的隐性漂移。

### 3.4 v1 只改协议中枢

本次只在 `DREAM-AGENT` 中完成以下内容：

- 评论模板定义；
- 协议文档扩展；
- workflow 触发与解析规则设计；
- 开发前置读取规则设计。

业务仓库在 v1 继续手动配合试点：

- 手动发送 `ACCEPTANCE_REQUEST`
- 手动回写 `VALIDATION_RESULT`
- 手动在下一轮开发前读取上一轮验收结果

## 4. 新的协作流

### 4.1 现有主流

当前更常见的路径是：

1. `STARTED`
2. 开发
3. `TEST_REPORT`
4. `DONE`
5. `VALIDATION_RESULT`

### 4.2 扩容后的专项验收流

引入 `ACCEPTANCE_REQUEST` 后，专项验收流调整为：

1. 开发者完成一次提交或一段阶段性交付
2. 在 PR 下发布 `[验收委托 / ACCEPTANCE_REQUEST]`
3. validator 只读取最新有效 `ACCEPTANCE_REQUEST`
4. validator 输出 `[验证结论 / VALIDATION_RESULT]`
5. 下一次开发继续前，先读取最近一次 `VALIDATION_RESULT`
6. 若存在 `must-fix / REWORK / BLOCK`，先修补再继续主线

### 4.3 结果语义

- `ACCEPTANCE_REQUEST`：定义本次验收任务
- `VALIDATION_RESULT`：定义本次验收结论
- `DONE`：保留为交付完成汇报，但不再作为专项验收的输入源

## 5. ACCEPTANCE_REQUEST 模板设计

### 5.1 模板职责

`ACCEPTANCE_REQUEST` 的职责不是总结工作，而是定义本轮验收指令。

它必须允许 validator 无需猜测即可回答：

- 验什么？
- 不验什么？
- 依据什么验？
- 重点项是什么？
- 期望回写成什么结构？

### 5.2 最小必填字段

建议最小必填字段如下：

- `Acceptance Request ID`
- `Request Type`
- `Request Mode`
- `Source of Truth`
- `Target PR`
- `验收对象`
- `验收范围`
- `业务上下文映射`
- `重点验收项`
- `本轮不要求`
- `期望回写格式`

### 5.3 示例结构

```md
[验收委托 / ACCEPTANCE_REQUEST]

Acceptance Request ID: ar-20260607-001
Request Type: feature | phase-gate | pilot
Request Mode: manual | auto
Source of Truth: PR comment
Target PR: #123

## 验收对象
- ...

## 验收范围
- ...

## 业务上下文映射
- 架构图基线: ...
- 前端承接基线: ...

## 重点验收项
- ...

## 本轮不要求
- ...

## 期望回写格式
- ...
```

## 6. VALIDATION_RESULT 扩展设计

### 6.1 保留现有硬门禁字段

现有模板中的这些字段继续保留：

- `Validator`
- `Hard Gate Result`
- `Score`
- `Decision`
- `Reason Codes`
- `Reward Multiplier`
- `Ledger Update`
- `Governance Handoff`

### 6.2 新增专项验收字段

为了服务专项验收，建议在模板中新增以下可选字段：

- `Validation Mode: delivery | acceptance`
- `Acceptance Request ID: request id | none`
- `Protocol Read Result: PASS | PARTIAL | FAIL`
- `Source of Truth Verdict: usable | ambiguous | invalid`
- `Must-Fix Items:`
- `Next Step Recommendation:`
- `Acceptance Conclusion: trial_pass | trial_partial | trial_fail | accepted | rework | blocked`

### 6.3 为什么不直接替换旧模板

不直接替换旧模板的原因是兼容性：

- 现有 validator 流已经依赖旧字段；
- 旧的 build/test 型 `VALIDATION_RESULT` 仍然有价值；
- v1 更适合“在现有模板上增量扩展”，而不是一次性替换。

## 7. Workflow 设计

### 7.1 方案选择

v1 选择：

- 在现有协议上扩容验收流
- `DREAM-AGENT` 作为协议中枢
- 先只改 `DREAM-AGENT`

### 7.2 推荐实现路径

推荐新增独立 workflow：

- `collab-acceptance-agent.yml`

而不是在 v1 直接把 `collab-validator-agent.yml` 变成巨型混合工作流。

原因：

- `DONE` 验证和 `ACCEPTANCE_REQUEST` 验收的输入语义不同；
- 将两类流程硬塞进同一个 workflow，会让条件分支迅速膨胀；
- 独立 workflow 更利于后续引入多 agent 验收调度。

### 7.3 v1 触发方式

v1 支持两种触发：

1. `workflow_dispatch`
   - 手动指定 `pr_number` 与 `acceptance_request_id`
2. `issue_comment`
   - 当 PR 评论包含 `[验收委托 / ACCEPTANCE_REQUEST]` 时触发

### 7.4 v1 读取策略

首版只读取：

- 当前 PR 下最新一条有效 `ACCEPTANCE_REQUEST`

不混读以下来源：

- commit message
- PR description
- 聊天记录
- 本地 todo

### 7.5 v1 输出策略

输出一条标准化的 `[验证结论 / VALIDATION_RESULT]` 评论。

首版即便不执行真实业务测试，也至少要完成：

- 协议读取结果判断
- 结构化程度判断
- 唯一真源可用性判断
- 下一步建议

## 8. 开发前置读取规则

新增一条执行规范：

- 每次继续开发前，必须先读取最近一次 `VALIDATION_RESULT`

读取后的处理规则：

- 若 `Decision = BLOCK`，停止推进并优先修补；
- 若 `Decision = REWORK`，优先修补再继续；
- 若存在 `Must-Fix Items`，优先纳入下一轮任务；
- 若没有阻塞项，方可继续主线开发。

该规则的目的不是拖慢开发，而是避免带着已知验收问题持续漂移。

## 9. 文档与模板落点

v1 建议落点如下：

- 协议文档更新：
  - `docs/01-COLLABORATION-PROTOCOL.md`
  - `docs/03-WORKFLOWS-AND-NORMS.md`
- 新增模板：
  - `templates/pr-comment-acceptance-request.md`
- 扩展模板：
  - `templates/pr-comment-validation-result.md`
- 新增 workflow：
  - `.github/workflows/collab-acceptance-agent.yml`

## 10. 风险与缓解

### 10.1 风险：字段过多导致评论难写

缓解：

- 保持最小必填字段集合；
- 将可选字段和示例写入模板；
- 首版允许 validator 对缺失字段给出 `PARTIAL` 而不是直接协议失败。

### 10.2 风险：与现有 DONE 流混淆

缓解：

- 在文档中明确 `DONE != ACCEPTED`
- 将 `ACCEPTANCE_REQUEST` 和 `VALIDATION_RESULT` 的职责写成独立章节

### 10.3 风险：workflow 一开始过于复杂

缓解：

- v1 先做“协议读写链路”
- 不要求立刻执行复杂业务测试
- 真实功能验收依旧由业务仓库与 agent 手动协同完成

## 11. 成功标准

v1 视为成功，需要满足以下条件：

- `DREAM-AGENT` 中正式存在 `ACCEPTANCE_REQUEST` 模板；
- 协议文档中正式定义 `ACCEPTANCE_REQUEST` 的职责与必填字段；
- `VALIDATION_RESULT` 模板支持专项验收扩展字段；
- 至少有一条真实 PR 评论可作为 `ACCEPTANCE_REQUEST` 试点样本；
- 团队能够按规则执行：
  - 提交后发 `ACCEPTANCE_REQUEST`
  - 验收后回写 `VALIDATION_RESULT`
  - 下次开发前先读最近一次 `VALIDATION_RESULT`

## 12. 最终结论

本次设计的最终结论是：

- 不新起一套验收系统；
- 在现有 `DREAM-AGENT` 协议上增量扩容；
- 新增 `[验收委托 / ACCEPTANCE_REQUEST]` 作为专项验收真源；
- 将 `[验证结论 / VALIDATION_RESULT]` 扩展为专项验收正式结论；
- 明确 `DONE != ACCEPTED`；
- 在 v1 中，`DREAM-AGENT` 只做协议中枢，不直接吞掉业务执行；
- 业务仓库先手动配合试点，待协议稳定后再逐步自动化。
