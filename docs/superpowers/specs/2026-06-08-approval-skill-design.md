---
id: APPROVAL-SKILL-DESIGN
type: design
owner: governance-agent
depends:
  - FEISHU-COLLABORATION-SYSTEM-DESIGN
  - OKR-DRIVEN-SKILL-DESIGN
  - BITABLE-SKILL-DESIGN
  - GITHUB-SYNC-SKILL-DESIGN
version: 1
last_verified: 2026-06-08
---

# Approval SKILL 设计

> 仓库：`DREAM-AGENT`
> 日期：`2026-06-08`
> 状态：draft
> 目标：构建一个以风险门控为入口、以飞书审批为执行介质、以协作状态回写为闭环目标的治理技能，使高风险动作能够在确认后完成审批实例创建、状态轮询、结果回写与交接沉淀。

## 1. 背景

当前主线已经具备四类关键基础：

- `OKR-driven SKILL` 已定义长期目标、任务候选与 workflow 候选
- `Bitable SKILL` 已把目标与任务、进度、视图投影纳入执行面
- `GitHub Sync SKILL` 已把工程真实状态稳定投影到飞书协作状态
- 现有审批底座已具备风险 gate、审批 API wrapper、真实 smoke、状态轮询和 Base 回写能力

这意味着当前缺失的不是“再做一套审批脚本”，而是一个位于飞书协作体系中的专门技能，用来回答下面的问题：

- 哪些变化必须进入审批闸门
- 为什么这次需要审批
- 将创建什么审批实例
- 超时、拒绝、读取失败后应如何降级或升级
- 审批结果应如何稳定回写到协作状态与知识资产

也就是说，`Approval SKILL` 的真实职责不是通用审批平台，而是“治理闸门”。

## 2. 问题定义

本设计主要解决以下五类问题：

### 2.1 高风险动作缺少统一治理入口

当前仓库已经能识别部分高风险场景并发起审批，但这些能力仍散落在脚本和 workflow 里，没有形成统一 skill 入口，结果容易出现：

- 高风险动作进入了不同脚本分支，而不是同一治理闸门
- 同样的风险在不同链路里得到不同兜底策略
- 审批是否必需、谁来接手、何时升级不够透明

### 2.2 底层能力存在，但缺少 preview-first 闭环

现有底层资产已经包括：

- 风险门控脚本
- 飞书审批 REST wrapper
- 审批编排与实例轮询
- Base 写回与目标聚合

但仍缺少：

- standalone skill package
- approval-specific execution checklist
- preview-first flow
- explicit escalation policy reference

结果是可以执行审批，却还不能成为体系化核心 skill。

### 2.3 审批参数与真实契约存在踩坑空间

真实 smoke 已证明两个关键细节会直接影响审批是否成功：

- `form` 必须以 JSON 字符串形式提交
- 申请人必须走 `open_id`，不能误塞到 `user_id`

如果 skill 层不把这些真实约束抽成显式对象和 preview 说明，后续扩展时容易再次踩坑。

### 2.4 审批结果与协作状态之间缺少标准投影层

审批不是终点，真正的治理价值在于结果被投影回协作状态。如果没有统一投影层，就会出现：

- 审批已通过，但任务仍显示 `pending`
- 审批已拒绝，但自动化状态没有正确暂停
- 审批超时，但没有保守续跑或暂停的明确说明

### 2.5 升级与知识沉淀不成体系

审批链路天然带有失败和超时场景，例如：

- 参数缺失
- 审批定义不可用
- 实例创建成功但轮询失败
- 状态回写完成但证据不全

如果没有统一的升级策略和知识输出，这些故障会停留在日志和临时记忆中，无法进入稳定运维闭环。

## 3. 设计目标

本设计的目标如下：

- 定义一个 `Approval SKILL`，作为飞书协作体系中的治理闸门
- 默认覆盖 `风险门控 + 发起 + 轮询`
- 坚持 `preview -> confirmation -> create/reuse -> poll -> writeback -> handoff`
- 将风险命中原因、超时策略和审批实例候选纳入 preview，而不是只输出最终审批状态
- 将升级策略、知识沉淀和失败分层纳入标准流程

成功标准：

- 能把高风险上下文编译成可读的 `ExecutionPreview`
- 能稳定产出审批请求候选、状态投影候选和升级策略
- 能在执行前显式暴露风险命中原因、超时策略与参数缺口
- 能在执行后输出 `ExecutionResult`、`KnowledgeUpdate` 和 handoff
- 能作为下一步实施计划与真实落地的统一设计基线

## 4. 范围与非目标

### 4.1 本设计覆盖

- 风险门控判定
- 审批实例创建或复用
- 审批状态轮询
- 审批状态投影回协作字段
- 超时与升级策略
- handoff 与 `KnowledgeUpdate`

### 4.2 本设计不覆盖

- 通用审批运营平台
- webhook 订阅与长期事件总线
- 审批后台报表或运营面板
- 与审批无关的通知平台重构
- 全量审批数据仓或审计中心

v1 的重点是：

- 让高风险动作稳定进入审批闸门
- 让审批实例和结果有统一对象语义
- 让审批结果稳定回写到协作状态
- 让超时、拒绝、失败都能被清晰升级和交接

而不是一开始就构建全量审批运营面。

## 5. 核心原则

### 5.1 治理闸门原则

`Approval` 的核心不是“多建一个流程”，而是在高风险动作进入真实执行前，提供统一治理边界。

### 5.2 预演优先原则

所有审批发起前必须先输出 preview，并显式展示：

- 为什么命中审批
- 将创建什么实例
- 会回写哪些字段
- 若超时会采用什么兜底策略

### 5.3 状态投影原则

审批价值不止于实例创建成功，还必须把实例状态稳定投影到：

- `approval_status`
- `decision_summary`
- `automation_status`
- 相关 goal / task 协作字段

### 5.4 分层失败原则

失败必须区分：

- `hard_block`
- `soft_block`
- `degraded_success`
- `confirmed`

不能跳过审批，也不能把参数缺口和轮询缺口伪装成成功。

### 5.5 知识回收原则

每次审批执行结束必须生成：

- `ExecutionResult`
- `KnowledgeUpdate`
- handoff

否则视为未闭环。

## 6. 角色定位与主从关系

### 6.1 `OKR-driven` 的职责

负责回答：

- 为什么要做
- 哪个目标正在发生变化
- 哪类目标切换或高风险动作需要治理约束

### 6.2 `Bitable` 的职责

负责回答：

- 审批结果如何落到任务和进度字段
- 管理视图现在应该显示什么状态

### 6.3 `GitHub Sync` 的职责

负责回答：

- 哪个工程动作或工程状态变化触发了审批需求
- 当前工程真实状态是什么

### 6.4 `Approval` 的职责

负责回答：

- 当前动作是否必须审批
- 将发起什么审批实例
- 审批结果如何影响自动化状态和协作状态
- 若拒绝、超时或失败，下一步由谁接手

### 6.5 固定主从关系

必须固定为：

- `OKR-driven` 提供目标层约束
- `Bitable` 提供任务/进度字段承接
- `GitHub Sync` 提供工程动作来源和风险信号
- `Approval` 负责高风险动作的治理闸门
- `Knowledge-Ops` 负责审批证据、交接与复盘沉淀

## 7. 推荐方案

推荐采用：

- `方案 A：闸门编排型`

其核心做法是：

- 以风险门控作为唯一入口
- 统一生成审批 preview、审批请求候选、状态投影与升级策略
- 复用现有 API wrapper、编排脚本和轮询脚本作为底层执行器
- 让 skill 层负责说明“为什么审批、如何审批、审批后怎么回写”

不推荐：

- 把 v1 设计成通用审批 API 工具箱
- 把重点放到 workflow 细节堆叠，而忽略 skill 级对象与闭环
- 在没有 preview/result contract 的前提下继续扩散审批脚本

## 8. 对象模型

### 8.1 `RiskGateSpec`

表示风险闸门对象，最少包含：

- `risk_level`
- `trigger_reason`
- `risk_scope`
- `recommended_action`
- `requires_approval`
- `timeout_policy`

### 8.2 `ApprovalRequestSpec`

表示审批请求候选，最少包含：

- `approval_code`
- `applicant_open_id`
- `instance_external_id`
- `form_payload`
- `source_refs`
- `target_object_id`

### 8.3 `ApprovalStatusProjection`

表示审批实例状态投影到协作字段的结果，最少包含：

- `approval_status`
- `approval_decision_id`
- `approval_instance_code`
- `decision_summary`
- `automation_status`
- `approval_due_at`

### 8.4 `EscalationSpec`

表示升级策略对象，最少包含：

- `escalation_trigger`
- `next_owner`
- `fallback_action`
- `knowledge_required`
- `handoff_required`

### 8.5 `ApprovalEvidenceSpec`

表示审批证据对象，最少包含：

- `instance_code`
- `status_snapshot`
- `decision_summary`
- `evidence_refs`
- `writeback_refs`

## 9. Preview 产物

`Approval SKILL` 的 preview 建议固定输出：

- `risk_gate_summary`
- `approval_request_candidate`
- `status_projection_candidate`
- `risk_flags`
- `timeout_policy`
- `requires_confirmation`

### 9.1 `risk_gate_summary`

必须能回答：

- 为什么这次命中审批门槛
- 风险来自哪个对象变化
- 当前推荐动作是什么
- 不审批会带来什么治理风险

### 9.2 `risk_flags`

至少包括：

- `missing_approval_code`
- `missing_applicant_open_id`
- `approval_scope_conflict`
- `instance_lookup_failed`
- `timeout_policy_missing`
- `status_projection_gap`

### 9.3 `approval_request_candidate`

必须显式包含：

- 审批定义 code
- 申请人 open_id
- 实例外部 ID
- 表单 payload
- 关联的任务、目标或工程对象

### 9.4 `timeout_policy`

必须显式展示：

- 超时后是 `pause`
- 还是 `conservative_continue`
- 对应的 next owner 和跟进动作是什么

## 10. 执行链路

统一执行链路为：

1. `risk evaluate`
2. `preview`
3. `confirmation / policy check`
4. `approval create or reuse`
5. `poll and project`
6. `handoff`

### 10.1 Risk Evaluate

只做三件事：

- 读取风险上下文
- 判断是否需要审批
- 生成风险等级、触发原因和超时策略

### 10.2 Preview

只做四件事：

- 说明命中审批的原因
- 生成审批请求候选
- 生成状态投影候选
- 暴露参数缺口与升级风险

### 10.3 Confirmation / Policy Check

当存在以下情况时，必须要求确认或进入门禁：

- `requires_approval = true`
- `missing_approval_code`
- `missing_applicant_open_id`
- `approval_scope_conflict`
- 关键目标或任务关联缺失

### 10.4 Approval Create or Reuse

确认后按固定顺序执行：

1. `risk_gate_check`
2. `approval_request_writeback`
3. `approval_status_projection`
4. `automation_status_projection`
5. `approval_evidence_snapshot`

### 10.5 Poll and Project

验证至少分四层：

- 审批实例状态读取
- 审批状态字段投影
- 自动化状态投影
- 证据与升级缺口验证

### 10.6 Handoff

每次执行后必须生成：

- 成功或失败 handoff
- `ExecutionResult`
- `KnowledgeUpdate`

## 11. 适配器边界

建议将 `Approval SKILL` 设计为“薄 skill + 稳定适配器”。

### 11.1 `Risk Gate Adapter`

负责：

- 风险判断
- 推荐动作生成
- 超时策略确定

不负责：

- 审批 API 调用
- Base 写回

### 11.2 `Approval API Adapter`

负责：

- 审批定义读取
- 实例创建
- 实例查询

不负责：

- 风险决策
- 升级决策

### 11.3 `Status Projection Adapter`

负责：

- 把审批实例状态映射到 `approval_status`
- 生成 `decision_summary`
- 映射 `automation_status`

### 11.4 `Writeback Adapter`

负责：

- 把审批结果写回任务记录
- 把必要状态聚合到目标记录
- 记录写回回执

### 11.5 `Knowledge Adapter`

负责：

- 审批证据组装
- handoff 证据沉淀
- runbook / delivery 路由

### 11.6 Skill 本体职责

`Approval SKILL` 本身只负责：

- 读取输入
- 生成 preview
- 决定执行顺序
- 汇总验证结果
- 产出 handoff / knowledge update

## 12. 失败策略

建议固定四类执行状态：

### 12.1 `hard_block`

例如：

- 缺少 `approval_code`
- 缺少 `applicant_open_id`
- 目标或任务记录无法定位

结果：

- 停止执行
- 必须人工补齐参数或上下文

### 12.2 `soft_block`

例如：

- 风险已识别，但审批配置不完整
- 实例创建成功但轮询失败
- 状态映射存在歧义

结果：

- 允许输出 preview
- 不允许伪装成完全成功

### 12.3 `degraded_success`

例如：

- 审批状态已回写
- 但证据快照、次要投影或 writeback refs 未完整生成

结果：

- 执行成功但降级
- 必须生成 evidence gap 和后续动作

### 12.4 `confirmed`

表示：

- 审批实例已正确处理
- 审批状态与自动化状态回写完成
- handoff 与知识输出完整

## 13. 风险与升级策略

建议 v1 至少覆盖四类升级场景：

### 13.1 参数缺失升级

优先覆盖：

- `approval_code` 缺失
- `applicant_open_id` 缺失
- 风险对象主键缺失

### 13.2 实例创建升级

优先覆盖：

- 审批定义不可用
- 请求体字段冲突
- `open_id` / `form` 契约不满足

### 13.3 实例轮询升级

优先覆盖：

- 实例读取失败
- 状态未能映射
- 超时进入兜底

### 13.4 状态回写升级

优先覆盖：

- Base 写回失败
- goal 聚合未更新
- 证据快照缺失

对于：

- 超时
- 读取失败
- 证据不全

必须统一进入 `EscalationSpec`，而不是散落在日志里。

## 14. 漂移策略

建议至少识别四类漂移：

### 14.1 `风险规则漂移`

高风险动作已经发生，但风险 gate 规则未覆盖。

### 14.2 `审批契约漂移`

真实 API 契约变化，导致 `open_id`、`form_payload` 或状态解析不再成立。

### 14.3 `状态投影漂移`

审批实例状态已更新，但协作字段与 goal 聚合未同步。

### 14.4 `证据漂移`

审批实例存在，但 handoff、证据链接或决策摘要未被沉淀。

其中：

- 风险规则漂移、审批契约漂移属于高优先级
- 状态投影漂移、证据漂移允许局部降级，但不能静默忽略

## 15. 测试策略

建议测试固定为四层：

### 15.1 Gate Tests

验证：

- 风险等级判断
- 是否触发审批
- 超时策略选择

### 15.2 API / Projection Tests

分别验证：

- 审批实例请求体
- `open_id` 约束
- `form` 序列化
- 审批状态映射

### 15.3 Workflow Contract Tests

验证：

- `approval-smoke` 输入存在
- Node24 兼容开关存在
- `open_id` 和 `json.dumps([])` 契约不被破坏

### 15.4 Dry-Run Tests

验证：

- `risk evaluate -> create/reuse -> poll -> writeback -> handoff`
- `KnowledgeUpdate` 和 handoff 是否完整输出
- 超时与拒绝分支是否有清晰 fallback

## 16. 风险与应对

### 16.1 风险：退化成通用审批平台

应对：

- 固定 v1 只覆盖 `风险门控 + 发起 + 轮询`
- 不做审批运营后台

### 16.2 风险：只有 API，没有 skill 级治理语义

应对：

- 强制 preview-first
- 强制输出风险命中原因和超时策略

### 16.3 风险：真实契约再次踩坑

应对：

- 把 `open_id` 和 `form` 契约固定进对象模型和测试
- 优先复用真实 smoke 已验证的链路

### 16.4 风险：失败后无法交接与排障

应对：

- 固定输出 `ExecutionResult`
- 固定输出 `KnowledgeUpdate`
- 固定 escalation 与 handoff 记录

## 17. 验收标准

本设计完成后，应满足以下验收标准：

- 能清晰说明 `Approval` 在整个协作体系中的定位和主从关系
- 能定义 v1 的 `风险门控 + 发起 + 轮询` 边界
- 能说明对象模型、preview 产物和写回顺序
- 能说明适配器边界、失败分级、升级策略与漂移策略
- 能说明测试策略和知识回收机制
- 能作为下一步实施计划与真实落地的统一设计基线
