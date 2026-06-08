---
id: FIVE-SKILL-INTEGRATION-REHEARSAL-DESIGN
type: design
owner: governance-agent
depends:
  - FEISHU-COLLABORATION-SYSTEM-DESIGN
  - BITABLE-SKILL-DESIGN
  - GITHUB-SYNC-SKILL-DESIGN
  - APPROVAL-SKILL-DESIGN
  - KNOWLEDGE-OPS-SKILL-DESIGN
version: 1
last_verified: 2026-06-08
---

# 五个 Skill 体系级联调与演练设计

> 仓库：`DREAM-AGENT`
> 日期：`2026-06-08`
> 状态：draft
> 目标：以核心目标为参考基线，新增一个可重复执行的五 skill 全链 rehearsal runner，并补齐统一状态口径，使 `OKR -> Bitable -> GitHub Sync -> Approval -> Knowledge-Ops` 能以 fixture-driven dry-run 方式完成系统级联调、断点暴露和交接沉淀。

## 1. 背景

当前五个核心 skill 已经具备单点或局部链路能力：

- `OKR-driven` 已形成目标编排样板
- `Bitable` 已具备 preview、materialize、verify 的 v1 闭环
- `GitHub Sync` 已形成 GitHub 到飞书协作字段与状态映射
- `Approval` 已具备风险门控、审批发起、轮询与结果投影
- `Knowledge-Ops` 已具备 intake、validation、check、materialize、verify

与此同时，系统层还缺少一层明确的联调骨架：

- 没有统一的五 skill rehearsal runner
- 没有统一的系统状态口径
- 没有把 skill 原生结果折叠成系统级结论的适配层
- 没有针对全链断点的统一分类和恢复提示

这导致目前虽然各 skill 都已进入 v1，但体系仍然主要停留在“单 skill 可验证、局部链路可验证”，尚未形成“整条协作主线可重复演练”的系统能力。

## 2. 问题定义

本设计主要解决以下四类问题：

### 2.1 缺少全链演练入口

当前已有 acceptance workflow、局部 dry-run 和 end-to-end contract tests，但缺少一个能够以核心目标为基线串起五个 skill 的统一入口。

### 2.2 状态语义不统一

总纲层已经定义：

- `observed`
- `synced`
- `confirmed`
- `blocked`
- `escalated`

而已实现 skill 的执行层大量使用：

- `confirmed`
- `degraded_success`
- `soft_block`
- `hard_block`
- `blocked`

如果不先统一系统口径，五个 skill 即便能串起来，也很难给出一致的系统级结果。

### 2.3 断点只能局部发现，不能系统归因

当前某个 skill 失败时，通常只能看到局部断点，缺少统一归因视角，例如：

- 是 contract 不匹配
- 是 fixture 数据不齐
- 是策略门控拦截
- 还是执行链路本身缺口

没有统一断点分类，就很难把系统级联调结果沉淀为 runbook 或 handoff。

### 2.4 联调结果难以沉淀为统一交付物

即便跑通多个片段，目前也缺少一个系统层报告对象，把以下内容统一输出：

- 演练概览
- 每步状态
- 断点列表
- 恢复提示
- handoff 摘要
- `KnowledgeUpdate` 候选

## 3. 设计目标

本设计的目标如下：

- 新增一个五 skill 体系级 rehearsal runner
- 新增一个 shared 语义适配层，用于统一状态与证据口径
- 以 fixture-driven dry-run 方式串起 `OKR -> Bitable -> GitHub Sync -> Approval -> Knowledge-Ops`
- 在不强改各 skill 现有原生状态的前提下，输出统一系统状态
- 对全链断点进行标准分类，并附带恢复提示
- 为后续 runbook、acceptance、workflow 编排提供统一的系统级演练基线

成功标准：

- 一条命令或一个入口可重复执行五 skill 全链演练
- runner 能输出系统级 `preview/result/verification/handoff` 摘要
- 每个 skill 原生状态都能映射为统一系统状态
- runner 能定位并输出链路断点、断点类型和恢复建议
- 全链 contract tests 能锁定状态映射与主链顺序

## 4. 范围与非目标

### 4.1 本设计覆盖

- 五 skill 全链 rehearsal runner
- shared 语义适配层
- fixture-driven dry-run 场景
- 统一系统状态口径
- 断点分类与恢复提示
- 系统级报告与 handoff 摘要
- 全链 contract tests

### 4.2 本设计不覆盖

- 立即把五个 skill 改造成统一内部实现
- 立即接入所有真实线上写回
- 立即把 rehearsal runner 合并进正式 workflow 编排
- 立即重写总纲中的系统闭环状态定义

本轮优先目标是通过“适配层 + runner”拿到系统级联调能力，而不是一次性重构所有既有 skill。

## 5. 核心原则

### 5.1 保留 skill 原生边界

本轮不把 runner 设计成新的超级 skill。五个 skill 仍保留原生 preview、materialize、verify 逻辑，runner 只负责串联、归一和报告。

### 5.2 适配优先于重写

统一状态口径优先通过 shared adapter 实现，不优先大面积改写现有 skill 的内部状态语义。

### 5.3 演练先于真实写回

本轮联调以 fixture-driven dry-run 为主，优先验证链路一致性、状态映射和断点归因，再决定是否延伸到真实 workflow。

### 5.4 系统结果必须可交接

runner 的输出不只是“跑过”，还必须形成：

- 系统级结果摘要
- 断点与恢复提示
- handoff 摘要
- `KnowledgeUpdate` 候选

否则不算完成闭环。

## 6. 推荐方案

推荐采用：

- `语义适配层 + 全链 rehearsal runner`

原因：

- 能最小改动复用现有五个 skill
- 能先解决当前最大的系统级问题，即状态语义不统一
- 能在不绑定真实线上写回的前提下快速得到可重复演练入口
- 能为后续 workflow 编排和 integration readiness 扩展提供稳定底座

不推荐：

- 先直接做 workflow 级真实编排
- 先全面回写所有 skill 的内部状态定义
- 先只补 runbook 和场景矩阵，不拿可执行链路

## 7. 总体架构

本设计新增一条系统级演练层，位于 `shared contracts` 之上、五个 skill 之旁，用于统一串联。

### 7.1 关键组件

#### `scenario_loader`

负责：

- 装载核心目标基线
- 装载五 skill fixtures
- 组装本次 rehearsal 的输入上下文

输出：

- `rehearsal_context`
- `scenario_manifest`

#### `state_adapter`

负责：

- 读取各 skill 的原生状态
- 归一状态、断点类型和证据摘要
- 为 reporter 提供统一系统语义

输出：

- `normalized_skill_result`

#### `chain_orchestrator`

负责：

- 按固定顺序执行五 skill 演练步骤
- 传递跨 skill 上下文
- 收集每一步的原生结果和归一结果
- 在链路中途记录断点和中断原因

输出：

- `rehearsal_steps`
- `breakpoints`

#### `rehearsal_reporter`

负责：

- 汇总系统级结果
- 输出 handoff 摘要
- 生成 `KnowledgeUpdate` 候选
- 为 runbook 和后续审计提供标准报告对象

输出：

- `system_preview`
- `system_result`
- `verification_summary`
- `handoff`
- `knowledge_update`

### 7.2 级联顺序

固定主链为：

1. `OKR-driven`
2. `Bitable`
3. `GitHub Sync`
4. `Approval`
5. `Knowledge-Ops`

顺序理由：

- 保持与总纲主线一致
- 先建立目标层
- 再建立任务和进度投影
- 再引入工程真实状态
- 再在高风险路径上应用治理门控
- 最后沉淀系统级 knowledge 与 handoff

## 8. 数据流与结果模型

### 8.1 输入

runner 至少接收：

- 核心目标基线
- 五 skill 对应 fixtures
- 本次演练的 scenario 标识

### 8.2 中间结果

每一步至少保留两类结果：

- `raw_result`：skill 原生输出
- `normalized_result`：经 adapter 映射后的系统级输出

这样可以同时满足：

- 保留领域语义
- 支持系统级报告
- 便于问题追溯

### 8.3 最终结果

runner 最终统一输出：

- `scenario_manifest`
- `step_results`
- `system_status`
- `breakpoints`
- `verification_summary`
- `handoff`
- `knowledge_update`

## 9. 统一状态口径

### 9.1 双层状态模型

本设计采用双层状态：

- Skill 层：保留各 skill 原生状态
- Runner 层：新增系统状态

Runner 层统一使用：

- `pass`
- `warn`
- `fail`
- `blocked`

### 9.2 默认映射

默认映射规则如下：

- `confirmed -> pass`
- `degraded_success -> warn`
- `soft_block -> fail`
- `hard_block -> blocked`
- `blocked -> blocked`

该映射不否定总纲中的闭环状态，而是作为“体系级联调”场景下的运行语义层。后续若要统一到总纲，可再做第二轮治理升级。

### 9.3 断点分类

runner 统一输出以下断点类型：

- `contract_gap`
- `data_gap`
- `policy_gap`
- `execution_gap`

含义分别为：

- `contract_gap`：上下游对象字段、状态或协议不一致
- `data_gap`：fixture、上下文或关键引用不完整
- `policy_gap`：治理门控、审批或规则阻断
- `execution_gap`：执行步骤、调用顺序或联调入口缺口

### 9.4 恢复提示

每个断点都必须输出：

- `breakpoint_type`
- `recovery_hint`

使联调结果可以直接转入 handoff 或 runbook。

## 10. 演练场景

v1 至少支持一个核心场景：

- `core-objective-baseline`

场景定义：

- 以核心目标为基线
- 使用现有五 skill fixtures 组装最小闭环
- 检查目标、任务、研发状态、审批结果和知识沉淀是否可串联

v1 不追求覆盖所有分支场景，但要保证该核心场景可重复运行、可稳定暴露系统断点。

## 11. 测试策略

本轮至少包含以下测试：

### 11.1 状态映射 contract tests

锁定 skill 原生状态到系统状态的映射规则，避免后续任一 skill 漂移后 silently break。

### 11.2 主链顺序 tests

锁定 `OKR -> Bitable -> GitHub Sync -> Approval -> Knowledge-Ops` 的主链顺序和中间结果传递。

### 11.3 核心场景 rehearsal tests

用 fixture-driven 方式跑通 `core-objective-baseline`，并断言：

- 有统一 `system_status`
- 有 `step_results`
- 有 `breakpoints`
- 有 `handoff`
- 有 `knowledge_update`

## 12. 风险与应对

### 12.1 风险：runner 成为新超级逻辑中心

应对：

- 把 runner 限定为演练编排与结果归一层
- 不吸收 skill 内部领域逻辑

### 12.2 风险：系统状态与总纲状态并存导致混淆

应对：

- 在 spec 和实现中显式区分 “skill 原生状态” 与 “runner 系统状态”
- 将 runner 状态限定为联调语义，不直接替代总纲闭环状态

### 12.3 风险：fixture 过轻，导致演练失真

应对：

- 明确场景基于核心目标基线
- 保留断点输出，而不是把所有异常都硬压成成功

### 12.4 风险：联调结果无法沉淀

应对：

- 强制输出 `handoff` 与 `knowledge_update`
- 把恢复提示纳入标准输出对象

## 13. 验收标准

本设计完成后，应满足以下验收标准：

- 存在正式的五 skill rehearsal 入口
- 该入口能以 fixture-driven 方式跑通核心目标基线场景
- 该入口能输出统一系统状态和逐步结果
- 该入口能输出断点类型与恢复提示
- 该入口能生成 handoff 摘要与 `KnowledgeUpdate` 候选
- contract tests 能锁定状态映射与主链顺序
