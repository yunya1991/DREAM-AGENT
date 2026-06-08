---
id: BITABLE-SKILL-DESIGN
type: design
owner: governance-agent
depends:
  - FEISHU-COLLABORATION-SYSTEM-DESIGN
  - OKR-DRIVEN-SKILL-DESIGN
  - FEISHU-BOSS-VIEW-OKR-MID-LINKAGE-DESIGN
version: 1
last_verified: 2026-06-08
---

# Bitable SKILL 设计

> 仓库：`DREAM-AGENT`
> 日期：`2026-06-08`
> 状态：draft
> 目标：将 `OKR-driven` 输出的长期目标编排结果稳定投影到飞书 Base 的任务层、进度层和视图层，使长期与短期、规划与落地、目标与执行持续对齐，并在确认后完成真实写回与验证。

## 1. 背景

当前主线已经明确：

- `OKR-driven SKILL` 负责把 `spec + plan` 编译为 Objective/KR、目标推进记录、任务候选与 workflow 候选
- `目标推进表` 和 `老板视图（状态与阻塞）` 已经证明 Base 可以承担管理投影层
- `build_goal_progress_record.py` 已经形成稳定的目标聚合语义
- `build_central_hub_okr_binding_payload.py` 已经形成稳定的 OKR 锚点写回语义

这意味着当前缺失的不是“再做一个表格工具”，而是一个处于 `OKR-driven` 下游、专门负责执行面投影的技能：

- 把长期目标拆为短期任务
- 把任务状态翻译为可治理的进度字段
- 把目标、任务、进度持续投影到老板视图和管理视图
- 在发现字段、状态、视图漂移时主动暴露而不是静默失败

也就是说，`Bitable SKILL` 的真正职责是“防漂移的执行面编排器”，而不是一个泛化的 Base 管理平台。

## 2. 问题定义

本设计主要解决以下五类问题：

### 2.1 长期目标到短期动作缺少稳定投影层

`OKR-driven` 可以定义目标、KR 和目标推进记录，但如果没有一个中间层持续负责 Base 执行面投影，就会出现：

- 任务与 KR 失联
- 任务与目标记录断链
- 目标已经变化，短期动作仍停留在旧定义

### 2.2 Base 执行面容易退化成手工维护

若任务、状态、风险、阻塞、下一步动作靠手工回写，系统会快速出现：

- 字段语义不一致
- 状态定义不统一
- 目标推进与任务推进相互矛盾

### 2.3 老板视图和执行视图缺少持续治理

Base 的价值不只是记录数据，而是承担管理界面。如果没有稳定投影与验证：

- 老板视图会看到过时字段
- 视图依赖字段会缺失
- 视图配置和记录投影会逐步漂移

### 2.4 失败缺少分层处理

如果 Base 写回逻辑一出错就整体失败，维护成本会很高；如果静默降级，又会放大管理风险。因此需要明确：

- 什么情况必须硬阻断
- 什么情况允许部分成功
- 什么情况应标记为降级成功并生成后续待办

### 2.5 测试和知识沉淀不成体系

若只验证“脚本能跑”，就无法确认：

- preview 是否合理
- 任务与目标是否正确关联
- 漂移是否被识别
- 知识更新是否完整

## 3. 设计目标

本设计的目标如下：

- 定义一个 `Bitable SKILL`，作为 `OKR-driven` 的最近落地层
- 默认覆盖 `任务 + 进度 + 视图` 三层
- 坚持 `preview -> confirmation -> writeback -> verify -> handoff`
- 将 Base 字段治理纳入 preview，而不是事后补救
- 将漂移识别、失败分级、知识回收纳入标准流程

成功标准：

- 能清晰消费 `OKR-driven` 的结果而不重新定义目标
- 能稳定产出任务候选、进度候选、目标投影候选和视图投影候选
- 能在写回前显式暴露 Base 字段、状态和视图漂移
- 能在写回后给出可验证的执行结果与 handoff

## 4. 范围与非目标

### 4.1 本设计覆盖

- 任务层
- 进度层
- 视图层
- 字段治理 preview
- 写回验证
- handoff 与 `KnowledgeUpdate`

### 4.2 本设计不覆盖

- 全量 Base 套件平台化治理
- 任意跨表计算引擎
- 通用 BI 报表平台
- 独立于 `OKR-driven` 的目标规划入口
- v1 内直接深度自动化复杂视图配置

v1 的视图层重点是：

- 验证视图依赖字段是否齐备
- 验证投影字段是否可用
- 输出视图修复建议或验证标记

而不是一开始就把复杂视图配置完全自动化。

## 5. 核心原则

### 5.1 上游从属原则

`Bitable SKILL` 是 `OKR-driven` 的下游，不重新定义目标，只消费并投影目标。

### 5.2 三层投影原则

v1 必须同时覆盖：

- 任务层
- 进度层
- 视图层

否则无法真正承接“规划与落地、长期与短期对齐”的要求。

### 5.3 预演优先原则

所有写回前必须先输出 Base 执行面 preview，并显式暴露漂移和风险。

### 5.4 分层失败原则

失败必须分级，而不是一律整体失败或静默忽略。

### 5.5 知识回收原则

每次执行结束必须生成：

- `ExecutionResult`
- `KnowledgeUpdate`
- handoff

否则视为未闭环。

## 6. 角色定位与主从关系

### 6.1 `OKR-driven` 的职责

负责回答：

- 做什么
- 为什么做
- KR 是什么

### 6.2 `Bitable` 的职责

负责回答：

- 现在拆成哪些任务
- 每个任务处在什么进度
- 老板视图和执行视图现在应该显示什么

### 6.3 固定主从关系

必须固定为：

- `OKR-driven` 是上游
- `Bitable` 是下游
- `Bitable` 不重新定义目标，只消费目标并做执行面投影

## 7. 推荐方案

推荐采用：

- `方案 A：目标投影型`

其核心做法是：

- 输入 `OKR-driven` 产出的 `ExecutionPreview`
- 输出任务候选、进度状态字段、视图投影结果和漂移报告
- 把 `Bitable` 定位成“目标落地面”

不推荐：

- 把 `Bitable` 做成泛化 Base 治理工具
- 把 v1 扩成全量 Base 平台套件

## 8. 对象模型

### 8.1 `TaskRecordSpec`

表示真正要落到 Base 任务层的对象，最少包含：

- `task_id`
- `goal_ref`
- `objective_ref`
- `kr_ref`
- `title`
- `owner`
- `status`
- `risk_level`
- `blocker`
- `next_action`
- `deliverable`
- `source_refs`

### 8.2 `ProgressRecordSpec`

表示任务推进与目标推进之间的状态映射，最少包含：

- `goal_id`
- `task_ref`
- `progress_status`
- `governance_status`
- `approval_status`
- `risk_level`
- `blocker`
- `decision_summary`
- `last_sync_at`

### 8.3 `GoalProjectionSpec`

表示目标在 Base 中的主记录投影，最少包含：

- `goal_id`
- `goal_name`
- `okr_objective_id`
- `okr_objective_title`
- `okr_owner`
- `okr_sync_status`
- `goal_status`
- `goal_progress`
- `workflow_signal`
- `key_blocker`
- `next_milestone`
- `next_action`

### 8.4 `FieldGovernanceSpec`

表示字段治理结果而非单次写回，最少包含：

- `required_fields`
- `missing_fields`
- `stale_fields`
- `field_mapping`
- `writeback_scope`

### 8.5 `ViewProjectionSpec`

表示视图层投影，最少包含：

- `view_name`
- `view_type`
- `required_columns`
- `sort_keys`
- `filter_rules`
- `projection_fields`
- `consumer_role`

## 9. Preview 产物

`Bitable SKILL` 的 preview 建议固定输出：

- `task_record_candidates`
- `progress_record_candidates`
- `goal_projection_candidates`
- `field_governance_report`
- `view_projection_candidates`
- `drift_flags`
- `requires_confirmation`
- `writeback_order`

### 9.1 `drift_flags`

至少包括：

- `missing_required_fields`
- `task_goal_unlinked`
- `kr_goal_unlinked`
- `view_projection_incomplete`
- `progress_status_conflict`

### 9.2 `writeback_order`

建议固定为：

1. 字段检查
2. 任务层
3. 进度层
4. 目标主记录投影
5. 视图投影验证

## 10. 执行链路

统一执行链路为：

1. `preview`
2. `confirmation`
3. `writeback`
4. `verify`
5. `handoff`

### 10.1 Preview

只做三件事：

- 读取上游 `OKR-driven` 结果
- 读取当前 Base 现状
- 生成差异化投影结果

### 10.2 Confirmation

当存在以下情况时，必须要求确认：

- `missing_required_fields`
- `task_goal_unlinked`
- `progress_status_conflict`
- `view_projection_incomplete`

### 10.3 Writeback

确认后按固定顺序写回：

1. `field governance check`
2. `task writeback`
3. `progress writeback`
4. `goal projection writeback`
5. `view verification markers`

### 10.4 Verify

验证至少分三层：

- 任务层验证
- 进度层验证
- 目标层验证

### 10.5 Handoff

每次执行后必须生成：

- 成功 handoff 或失败 handoff
- `ExecutionResult`
- `KnowledgeUpdate`

## 11. 适配器边界

建议将 `Bitable SKILL` 设计为“薄 skill + 稳定适配器”。

### 11.1 `Task Adapter`

负责：

- 任务记录的创建
- 去重
- 更新
- 关联

### 11.2 `Progress Adapter`

负责：

- 推进状态回写
- 风险回写
- 阻塞回写
- 下一步动作回写

### 11.3 `Goal Projection Adapter`

负责：

- 把任务与目标聚合结果投影回目标主记录
- 优先复用 `build_goal_progress_record.py` 的语义

### 11.4 `View Validation Adapter`

负责：

- 检查视图依赖字段
- 检查视图消费字段
- 检查投影完整性

v1 不强求做复杂自动配置，但必须能明确报出缺失和冲突。

### 11.5 Skill 本体职责

`Bitable SKILL` 本身只负责：

- 读取输入
- 生成 preview
- 决定执行顺序
- 汇总验证结果
- 产出 handoff / knowledge update

## 12. 失败策略

建议固定三类失败：

### 12.1 `hard_block`

例如：

- 关键字段缺失
- `goal_id` 无法定位
- 任务无法关联 KR

结果：

- 停止执行
- 必须人工确认

### 12.2 `soft_block`

例如：

- 任务层可写
- 但视图投影不完整

结果：

- 允许部分成功
- 但必须在结果中标记 `blocked`

### 12.3 `degraded_success`

例如：

- 任务和进度已写回
- 视图层只完成验证未修复

结果：

- 执行成功但降级
- 必须生成后续待办

## 13. 漂移策略

建议至少识别四类漂移：

### 13.1 `目标漂移`

Base 中任务已经不再对应当前 Objective/KR。

### 13.2 `状态漂移`

任务状态与目标推进状态冲突。

### 13.3 `字段漂移`

必需字段缺失、命名变化或语义变化。

### 13.4 `视图漂移`

老板视图或执行视图依赖字段缺失，或排序过滤规则失效。

其中：

- 目标漂移、字段漂移属于高优先级
- 状态漂移、视图漂移允许局部降级，但不能静默忽略

## 14. 测试策略

建议测试固定为四层：

### 14.1 Preview Tests

验证：

- 任务候选
- 进度候选
- 字段治理报告
- 视图投影报告

### 14.2 Adapter Tests

分别测试：

- `Task Adapter`
- `Progress Adapter`
- `Goal Projection Adapter`
- `View Validation Adapter`

### 14.3 Failure-Mode Tests

验证：

- `hard_block`
- `soft_block`
- `degraded_success`

### 14.4 Contract Tests

验证：

- 是否正确消费 `OKR-driven` 输出
- 是否正确产出 `KnowledgeUpdate`

## 15. 风险与应对

### 15.1 风险：边界过宽，退化成泛化 Base 平台

应对：

- 固定 v1 只覆盖 `任务 + 进度 + 视图`
- 不新增独立规划入口

### 15.2 风险：视图自动化做得过重

应对：

- v1 只做视图验证和修复建议
- 不强行深度自动配置复杂视图

### 15.3 风险：写回成功但语义漂移未被发现

应对：

- 强制漂移检测
- 强制分层验证

### 15.4 风险：失败后无法交接与排障

应对：

- 固定输出 `ExecutionResult`
- 固定输出 `KnowledgeUpdate`
- 固定 handoff 模板

## 16. 验收标准

本设计完成后，应满足以下验收标准：

- 能清晰说明 `Bitable SKILL` 与 `OKR-driven` 的固定主从关系
- 能定义 v1 的任务层、进度层、视图层边界
- 能说明对象模型、preview 产物和写回顺序
- 能说明适配器边界、失败分级与漂移策略
- 能说明测试策略和知识回收机制
- 能作为下一步实施计划与真实落地的统一设计基线
