---
id: OKR-DRIVEN-SKILL-DESIGN
type: design
owner: governance-agent
depends:
  - CENTRAL-HUB-OKR-BINDING-DESIGN
  - FEISHU-BOSS-VIEW-OKR-MID-LINKAGE-DESIGN
version: 1
last_verified: 2026-06-08
---

# OKR-driven SKILL 设计

> 仓库：`DREAM-AGENT`
> 日期：`2026-06-08`
> 状态：draft
> 目标：将已经验证过的“`spec + plan -> OKR + Base + 任务 + workflow + projection`”方法沉淀为一个可复用的 `OKR-driven SKILL`，既能做设计编排，也能在确认后执行线上实操。

## 1. 背景

当前仓库已经完成一条真实链路的打通：

- `目标推进表` 已落地，并存在 `老板视图（状态与阻塞）`
- `中台与前端联动验证能力打通` 已作为真实业务目标写入 Base
- 真实 Feishu Objective 与 4 条 KR 已成功创建并发布
- `OKR对齐`、`okr_objective_id`、`okr_objective_title`、`okr_owner` 等锚点字段已成功回写
- `goal payload` 已可重建并回写 `workflow_signal`
- workflow bootstrapper 已完成多轮 live schema 收口并通过 smoke

这说明当前已经不再缺“单点能力”，而是缺一个更高层的稳定技能：

- 读取 `spec + plan`
- 自动抽取目标、KR、推进记录、任务与 workflow 候选
- 给出一份可靠的预演结果
- 经确认后，真实创建或更新 `OKR + Base + 任务 + workflow`
- 最后自动完成 projection refresh、老板视图验证与 handoff

也就是说，用户真正要沉淀的不是“再做一次绑定”，而是一套可持续复用的“目标驱动编排 + 实操技能”。

## 2. 问题定义

本设计要解决的是以下四类问题：

### 2.1 设计与执行断裂

当前 `spec`、`plan` 与线上对象之间仍存在人工断层：

- 设计已经确认
- 计划已经拆出
- 但真正落地到 OKR / Base / workflow 时，仍需要手工判断和操作

这会导致：

- 每次新项目都重复人工编排
- 同样的问题被重复排查
- 难以把经验沉淀成可复用流程

### 2.2 目标层、推进层、任务层、提醒层缺少统一编排入口

当前已经明确分层：

- `Objective / KR` 表示目标
- `目标推进表` 表示推进状态
- `任务层` 表示实现动作
- `workflow` 表示提醒与校验

但仍然缺少一个上层 orchestrator，把它们从同一组输入中统一生成、统一预演、统一执行。

### 2.3 线上实操摩擦过高

这次真实 OKR 落地中，真正耗时的并不是文案，而是：

- 找到真实 owner 下当前周期的可写 `okr_id`
- 处理 Feishu OKR draft / publish 机制
- 处理 19 位 ID 的精度问题
- 识别 `draft_version`、`token`、`connUuid` 等运行时参数
- 用正确 payload 形状创建 Objective/KR
- 回写 Base 锚点
- 再刷新 `goal payload / workflow_signal / 老板视图`

如果这些步骤不被系统化，skill 只会停留在“设计助手”，而不会成为真正有价值的核心技能。

### 2.4 需要支持“先预演后执行”

因为首批对象涉及真实线上资源：

- OKR
- Base
- 任务层
- workflow

所以 skill 不能默认无确认直接写线上对象，而必须：

- 先输出预演结果
- 再让用户确认
- 最后执行

## 3. 设计目标

本设计的目标如下：

- 沉淀一个 `OKR-driven SKILL`
- v1 默认输入为 `spec + plan`
- 同时支持两种核心能力：
  - 设计编排
  - 确认后执行线上实操
- 首批自动执行对象覆盖：
  - `OKR`
  - `Base`
  - `任务层`
  - `workflow`
- 将这次已验证过的 live 实操经验固化为稳定 adapter 和验证闭环

成功标准如下：

- 能从 `spec + plan` 产出结构化编排结果
- 能输出可靠的预演结果与差异清单
- 用户确认后能真实落地 `OKR + Base + 任务 + workflow`
- 执行后能自动刷新 `goal payload` 与 `workflow_signal`
- 能回读 `老板视图（状态与阻塞）` 验证最终状态
- 能生成可供后续子项目复用的 handoff baseline

## 4. 范围与非目标

### 4.1 本轮范围

`OKR-driven SKILL` v1 仅覆盖以下范围：

- 输入 `spec + plan`
- 抽取和标准化中间对象模型
- 输出 `ExecutionPreview`
- 用户确认后执行：
  - Objective / KR 创建或更新
  - Base 目标推进记录创建或更新
  - 任务层对象创建或更新
  - workflow 创建或更新
- 执行后做 projection refresh、老板视图验证与 handoff

### 4.2 明确不做

本轮不做以下事项：

- 不要求 `架构图` 成为 v1 必填输入
- 不支持“只给一句自然语言”就自动推导全套对象
- 不把 dashboard 纳入首批自动执行对象
- 不默认无确认直接执行
- 不把 skill 做成只适用于“中台与前端联动验证能力打通”的单一业务脚本
- 不要求 v1 先落成完整通用 DSL

## 5. 设计原则

### 5.1 先设计编排，再真实执行

skill 的默认执行模式是：

- `先预演后执行`

即：

- 先输出编排结果、差异清单、待执行 payload
- 经用户确认后再执行线上写操作

### 5.2 目标层、推进层、任务层、提醒层必须分离

必须始终保持如下分层：

- `Objective / KR`：为什么做、做到什么程度
- `目标推进表`：当前状态、阻塞、风险、下一步
- `任务层`：具体怎么做
- `workflow`：提醒与校验

skill 不能把这些层混成一个对象域。

### 5.3 执行层只能消费标准化对象，不直接消费文档原文

执行 adapter 不能直接读 `spec` 或 `plan` 原文决定线上动作。

必须先经过：

- 抽取
- 去重
- 去任务化
- 去歧义
- 建立引用关系

之后，执行层只吃中间对象模型。

### 5.4 v1 采用方案 A，但内部预留向方案 B 演进

v1 采用：

- 双阶段编排器

但内部必须保留稳定中间对象模型，以便后续自然演进为：

- 统一 DSL / 中间计划对象

### 5.5 skill 的核心价值在实操沉淀

本技能的核心价值不只是“写出一组 KR”，而是把高摩擦实操流程沉淀成稳定能力，包括：

- OKR 周期与 owner 下真实对象定位
- Objective/KR 的 draft / update / publish 链路
- Base 锚点回写
- payload refresh
- workflow schema 对齐
- 老板视图验证

## 6. 推荐方案

### 6.1 方案结论

采用：

- 方案 A：双阶段编排器
- 内部预留向方案 B：统一 DSL 驱动器演进的结构

### 6.2 方案说明

阶段 1：

- 从 `spec + plan` 抽取对象
- 生成 `ExecutionPreview`
- 输出差异清单、待执行计划、风险项

阶段 2：

- 用户确认
- 顺序执行 `OKR -> Base -> 任务 -> workflow -> projection`

### 6.3 为什么不直接选方案 B

方案 B 虽然长期扩展性更好，但 v1 如果先把完整 DSL 设计做重，会带来两个问题：

- 延迟首版落地
- 把精力过多放在编译结构，而不是首批最关键的实操 adapter

因此，v1 更适合先把中间对象模型稳定下来，后续再平滑提升为 DSL。

## 7. 技能边界与总体架构

### 7.1 技能目标

`OKR-driven SKILL` v1 要实现的是：

- 输入层读取 `spec + plan`
- 编排层抽取并组织：
  - `Objective`
  - `KR`
  - `goal records`
  - `tasks`
  - `workflows`
- 预演层生成候选对象、差异清单、执行顺序与 payload
- 执行层在用户确认后，真正创建或更新线上对象
- 回写层完成 projection refresh、老板视图验证与 handoff

### 7.2 内部分层

内部建议拆成 5 层：

- `Input Normalizer`
- `Planning Orchestrator`
- `Preview Engine`
- `Execution Adapters`
- `Projection & Verification`

### 7.3 固定执行顺序

执行顺序固定为：

1. `spec + plan -> 中间对象模型`
2. `中间对象模型 -> ExecutionPreview`
3. 用户确认
4. `OKR adapter`
5. `Base adapter`
6. `Task adapter`
7. `Workflow adapter`
8. `Projection & Verification`
9. 生成 handoff

## 8. 中间对象模型

### 8.1 对象类型

建议 skill 内部先稳定以下中间对象：

- `ObjectiveSpec`
- `KRSpec`
- `GoalRecordSpec`
- `TaskSpec`
- `WorkflowSpec`
- `ProjectionSpec`

### 8.2 最小字段

`ObjectiveSpec` 最少包含：

- `title`
- `owner`
- `period_hint`
- `source_spec_refs`
- `source_plan_refs`

`KRSpec` 最少包含：

- `title`
- `objective_ref`
- `acceptance_signal`
- `source_refs`

`GoalRecordSpec` 最少包含：

- `goal_id`
- `goal_name`
- `goal_owner`
- `goal_status`
- `risk_level`
- `blocker`
- `next_action`
- `okr_anchor_ref`

`TaskSpec` 最少包含：

- `task_id`
- `title`
- `goal_ref`
- `kr_ref`
- `owner`
- `status`
- `deliverable`

`WorkflowSpec` 最少包含：

- `name`
- `trigger_kind`
- `conditions`
- `receivers`
- `expected_signal`

`ProjectionSpec` 最少包含：

- `base_record_updates`
- `boss_view_checks`
- `handoff_items`

### 8.3 对象关系

- 一个 `ObjectiveSpec` 对应多个 `KRSpec`
- 一个 `GoalRecordSpec` 通常锚定一个主 `ObjectiveSpec`
- 一个 `KRSpec` 可映射多个 `TaskSpec`
- 一个 `GoalRecordSpec` 可关联多个 `WorkflowSpec`
- `ProjectionSpec` 不承载业务语义，只负责投影与验证

## 9. 从 spec + plan 到中间对象模型的抽取规则

### 9.1 输入标准化

v1 默认入口只接受：

- `spec`
- `plan`

skill 需要先将输入标准化为：

- `design source`
- `execution source`

### 9.2 spec 的职责

`spec` 主要提供：

- 为什么做
- 目标边界
- 成功标准
- 分层原则
- 非目标

因此主要从 `spec` 抽取：

- `ObjectiveSpec`
- `KRSpec`
- `GoalRecordSpec` 的目标语义部分
- `WorkflowSpec` 的职责边界

### 9.3 plan 的职责

`plan` 主要提供：

- 做哪些步骤
- 先后顺序
- 文件与对象落点
- 可执行动作
- 验证方式

因此主要从 `plan` 抽取：

- `TaskSpec`
- `ProjectionSpec`
- `WorkflowSpec` 的执行顺序与落地点
- `GoalRecordSpec` 的推进动作部分

### 9.4 抽取规则

`ObjectiveSpec`：

- 优先从 `设计目标 / 方案结论 / Objective 建议文案` 抽取

`KRSpec`：

- 优先从 `KR 建议文案 / KR 与功能实现分层` 抽取
- 只保留结果型表达
- 丢弃实现动作型句子

`GoalRecordSpec`：

- 从 `spec` 抽目标定位
- 从 `plan` 抽 blocker、risk、next action、milestone、owner

`TaskSpec`：

- 从 `plan` 的步骤、文件落点、执行任务中抽取
- 每个任务必须能映射到某个 `KRSpec` 或 `GoalRecordSpec`

`WorkflowSpec`：

- 从 `spec` 的职责边界和 `plan` 的执行链路中抽取
- 只保留提醒型 / 校验型 workflow

### 9.5 标准化治理

进入预演层之前，必须先完成：

- 去重
- 去任务化
- 去歧义
- 建立引用关系

### 9.6 失败与降级

如果：

- 无法抽出明确 Objective
  - 停在预演前，报“目标定义不足”
- KR 混入大量任务动作
  - 输出“KR 去任务化建议”，不直接执行
- plan 不足以支撑任务层或 workflow 层
  - 允许降级为 `OKR + Base`
  - 但预演中必须显式标记 `TaskSpec / WorkflowSpec incomplete`

## 10. ExecutionPreview 设计

### 10.1 预演产物

v1 建议固定输出 5 类预演结果：

- `对象清单`
- `差异清单`
- `执行顺序`
- `待执行 payload`
- `风险提示`

### 10.2 最小结构

建议内部统一产出一个 `ExecutionPreview`：

- `objective_candidates`
- `kr_candidates`
- `goal_record_candidates`
- `task_candidates`
- `workflow_candidates`
- `upsert_plan`
- `risk_flags`
- `requires_confirmation = true`

### 10.3 作用

`ExecutionPreview` 的作用不是“展示几条建议”，而是：

- 明确将创建什么
- 明确将更新什么
- 明确哪些对象已经存在
- 明确关键 anchor 如何变化
- 明确执行风险与缺口

## 11. 执行适配器设计

### 11.1 OKR adapter

负责：

- 定位 owner 下当前周期真实 `okr_id`
- 创建或更新 Objective
- 创建或更新 KR
- 发布 draft
- 回读真实 `objective_id / kr_ids / owner / title`

必须沉淀的经验规则：

- 19 位 ID 一律按字符串处理
- 先读真实 owner/cycle 对象，不只信页面 URL
- Objective/KR 创建分三步：
  - 创建草稿壳
  - 更新富文本内容
  - 发布
- 成功结果必须回写为稳定 anchor

### 11.2 Base adapter

负责：

- 创建或更新 `目标推进表` 记录
- 回写 boss fields
- 回写 OKR anchor
- 回写 `decision_summary / workflow_signal / approval_status`
- 读取老板视图做最终验证

必须沉淀的经验规则：

- Base 只做投影，不做真源
- `OKR对齐`、`okr_objective_*`、`workflow_signal` 通过统一 payload builder 生成
- 验证不仅看 record，还要尽量按 view 可见字段检查

### 11.3 Task adapter

负责：

- 将 plan 中动作落成任务对象
- 为任务建立：
  - `goal_ref`
  - `kr_ref`
  - `owner`
  - `deliverable`
  - `status`

必须沉淀的经验规则：

- 任务不能悬空存在
- 任务标题是动作，KR 标题是结果
- 输入不完整时允许降级，但必须显式标记

### 11.4 Workflow adapter

负责：

- 生成或更新提醒型 / 校验型 workflow
- 保证 workflow 与 live Base schema 对齐
- 做最小 enable / disable / verify

必须沉淀的经验规则：

- workflow 不越权修改 OKR 真源
- schema 必须以 live 可接受格式生成
- 固化这次已验证过的 schema 要点：
  - `condition_list`
  - `trigger_control_list`
  - receiver 引用
  - smoke / validate 逻辑

## 12. 预演后执行与失败策略

### 12.1 执行模式

确认后的默认执行顺序固定为：

1. `OKR adapter`
2. `Base adapter`
3. `Task adapter`
4. `Workflow adapter`
5. `Projection & Verification`

### 12.2 失败策略

`OKR adapter` 失败：

- 后续默认停止

`Base adapter` 失败：

- 最终必须标记“驾驶舱未完成”

`Task adapter` 失败：

- 允许保留 `OKR + Base + workflow`
- 但 handoff 必须标记任务层不完整

`Workflow adapter` 失败：

- 不影响 OKR/Base 主体成功
- 但必须标记“提醒闭环未完成”

### 12.3 设计原则

skill 可以部分成功，但不能伪装成完整闭环已经达成。

## 13. Projection 与验证

### 13.1 Projection

执行后必须至少刷新以下内容：

- `OKR对齐`
- `okr_objective_id`
- `okr_objective_title`
- `okr_owner`
- `okr_sync_status`
- `okr_last_sync_at`
- `最近决策摘要`
- `workflow_signal`

### 13.2 验证层

执行后必须跑三类验证：

- `对象验证`
  - Objective / KR / Base record / task / workflow 是否真实存在
- `投影验证`
  - projection 字段是否与线上对象一致
- `闭环验证`
  - 老板视图是否可读
  - handoff 是否可被下游子项目直接复用

## 14. 最终交付物

每次 skill 执行后，至少产出：

- `execution summary`
- `created / updated object ids`
- `boss view verification`
- `projection payload snapshot`
- `handoff baseline`

高摩擦场景下，额外保留：

- `objective_id`
- `record_id`
- `workflow_signal`
- `blocker`
- `next_action`

## 15. 风险与控制

主要风险如下：

- 输入文档不足，抽取不稳定
- KR 退化成任务列表
- OKR 与 Base 双写冲突
- 线上 adapter 再次遭遇 schema / permission / draft 漂移
- 执行成功但 projection 与老板视图未同步

控制策略：

- 固定 `spec + plan` 作为 v1 输入
- 预演前做标准化治理
- Base 只做投影
- adapter 只消费中间对象，不直接消费文档原文
- 强制保留 Projection & Verification 收尾

## 16. 验收标准

完成后应满足：

- `OKR-driven SKILL` 有明确输入、预演、执行、验证边界
- v1 支持从 `spec + plan` 生成中间对象模型
- 能输出 `ExecutionPreview`
- 经确认后可真实落地：
  - `OKR`
  - `Base`
  - `任务层`
  - `workflow`
- 能自动刷新 goal projection
- 能回读老板视图
- 能生成 handoff baseline
- 内部结构允许后续平滑演进到统一 DSL 方案
