---
id: KNOWLEDGE-OPS-SKILL-DESIGN
type: design
owner: governance-agent
depends:
  - FEISHU-COLLABORATION-SYSTEM-DESIGN
  - OKR-DRIVEN-SKILL-DESIGN
  - BITABLE-SKILL-DESIGN
  - GITHUB-SYNC-SKILL-DESIGN
  - APPROVAL-SKILL-DESIGN
version: 1
last_verified: 2026-06-08
---

# Knowledge-Ops SKILL 设计

> 仓库：`DREAM-AGENT`
> 日期：`2026-06-08`
> 状态：draft
> 目标：构建一个以 `KnowledgeUpdate` 为统一入口、以资产校验与知识巡检为核心治理能力的知识技能，使前四个 skill 产出的 handoff、runbook、证据和治理记录能够被稳定接入、校验、落盘并持续检查。

## 1. 背景

当前主线已经具备五类关键基础：

- `OKR-driven SKILL` 已定义目标层上下文和长期治理语义
- `Bitable SKILL` 已稳定产出任务、进度与视图投影结果
- `GitHub Sync SKILL` 已稳定产出工程协作证据与交接信息
- `Approval SKILL` 已稳定产出审批证据、决策摘要和 handoff
- 知识体系基础设施已经具备最小路由、模板、索引和共享契约

这意味着当前缺失的不是“再建一套文档目录”，而是一个位于飞书协作体系中的专门技能，用来回答下面的问题：

- 上游 skill 产出的知识更新应该进入哪里
- 这份知识是否合格、完整、可落盘
- 当前资产是否已经漂移、存在缺口或过期
- 索引、模板和目标目录是否仍与治理约束一致
- 当知识资产不合格时，应如何降级、交接或修复

也就是说，`Knowledge-Ops SKILL` 的真实职责不是通用文档平台，而是“知识中枢 + 运维中枢”。

## 2. 问题定义

本设计主要解决以下五类问题：

### 2.1 上游知识输出缺少统一 intake

前四个 skill 已经能产出 `KnowledgeUpdate` 和 handoff，但当前知识接入还停留在最小四字段和路径解析层，结果容易出现：

- 知识更新能发出来，但没有规范化 intake 语义
- 同样类型的知识在不同 skill 中缺少统一校验标准
- 上游输出能路由，但不能被清楚判定为“合格资产”或“待修资产”

### 2.2 资产路由存在，但资产治理不足

现有底层资产已经包括：

- `KnowledgeUpdate` 共享契约
- runbook / handoff 模板
- 统一目录与索引
- 最小路径路由器

但仍缺少：

- canonical knowledge intake contract
- richer asset validation
- automated drift / gap / stale checks
- writeback-and-verify 闭环

结果是目录存在，但治理引擎尚未形成。

### 2.3 资产合格性与目标落点之间没有标准桥梁

当前 `KnowledgeUpdate` 只知道“类型 + 标题 + 摘要 + 证据”，但还不能稳定回答：

- 为什么要落到这个目录
- 应使用哪种模板
- 这个目标路径是否可写、是否冲突、是否允许覆盖
- 资产内容是否满足最小元数据与证据要求

如果没有标准桥梁，知识沉淀会很快从“可治理资产”退化成“堆文件”。

### 2.4 缺少知识巡检能力

当前体系已经明确要求做三类持续治理：

- `drift`
- `gap`
- `stale`

但目前只在个别 skill 内部存在局部漂移判断，尚无独立的 Knowledge-Ops 检查器来回答：

- 资产是否与模板或索引漂移
- 是否存在知识缺口
- 是否存在明显陈旧资产

### 2.5 交接与运维沉淀尚未形成治理闭环

handoff 和 runbook 模板已经存在，但如果没有统一的知识治理技能，就会出现：

- handoff 能写，但不一定能验证
- runbook 能建，但不一定能持续更新
- 索引存在，但不一定与资产目录对齐
- 证据链接存在，但不一定能进入后续治理流程

这会让 `Knowledge-Ops` 停留在“格式基线”，而不是“运维基线”。

## 3. 设计目标

本设计的目标如下：

- 定义一个 `Knowledge-Ops SKILL`，作为飞书协作体系中的知识中枢和运维中枢
- 默认覆盖 `Intake + Validation + Check`
- 坚持 `intake -> preview -> confirmation -> materialize -> verify -> handoff`
- 将目标路径、校验报告和 `drift / gap / stale` 检查纳入 preview，而不是只输出最终落盘路径
- 将知识写回、索引对齐、资产校验和治理交接纳入标准流程

成功标准：

- 能把 `KnowledgeUpdate` 编译成可读的 `ExecutionPreview`
- 能稳定产出目标路径候选、校验报告和三类检查结果
- 能在执行前显式暴露未知类型、空标题、缺证据和过期提示
- 能在执行后输出 `ExecutionResult`、`KnowledgeUpdate` 回执和 handoff
- 能作为下一步实施计划与真实落地的统一设计基线

## 4. 范围与非目标

### 4.1 本设计覆盖

- `KnowledgeUpdate` 规范化 intake
- 目标路径与模板选择
- 资产校验
- `drift / gap / stale` 检查
- 资产落盘与索引对齐
- handoff 与 `KnowledgeUpdate` 回执

### 4.2 本设计不覆盖

- 知识运营后台或知识面板
- 自动重写历史资产
- 全量修复器或智能重构器
- 外部知识库同步平台
- 通用文档管理系统重构

v1 的重点是：

- 让前四个 skill 产出的知识更新稳定进入知识治理入口
- 让资产在落盘前被校验、被检查、被分类
- 让落盘结果可以被验证和交接
- 让知识资产具备最小持续治理能力

而不是一开始就构建知识运营平台。

## 5. 核心原则

### 5.1 知识治理原则

`Knowledge-Ops` 的核心不是“多写文档”，而是让知识资产进入可治理状态。

### 5.2 Intake 优先原则

所有知识写回前必须先做 intake 归一化，并显式展示：

- 这份知识来自哪里
- 属于什么资产类型
- 预计落到哪里
- 当前是否满足最小治理要求

### 5.3 校验优先原则

知识落盘前必须显式验证：

- 标题是否有效
- 类型是否有效
- 证据是否存在
- 模板与目标路径是否匹配

### 5.4 检查显式原则

`drift`、`gap`、`stale` 必须作为一等结果输出，而不是只记录在日志中。

### 5.5 交接闭环原则

每次知识治理执行结束必须生成：

- `ExecutionResult`
- `KnowledgeUpdate` 回执
- handoff

否则视为未闭环。

## 6. 角色定位与主从关系

### 6.1 `OKR-driven` 的职责

负责回答：

- 当前知识背后的目标背景是什么
- 哪些长期约束应被沉淀为知识

### 6.2 `Bitable` 的职责

负责回答：

- 任务、进度、视图投影产生了哪些交付知识
- 哪些字段治理信息应被转化为知识资产

### 6.3 `GitHub Sync` 的职责

负责回答：

- 工程协作过程产生了哪些交接、证据和执行结论

### 6.4 `Approval` 的职责

负责回答：

- 审批、升级和决策过程产生了哪些治理知识

### 6.5 `Knowledge-Ops` 的职责

负责回答：

- 这些知识应该进入哪个目录和模板
- 当前资产是否合格、是否完整、是否陈旧
- 索引和目录是否对齐
- 若资产存在治理问题，下一步由谁修复或接手

### 6.6 固定主从关系

必须固定为：

- `OKR-driven` 提供目标背景
- `Bitable` 提供交付投影与字段治理知识
- `GitHub Sync` 提供工程协作证据和交接
- `Approval` 提供决策与治理证据
- `Knowledge-Ops` 负责统一收编、校验、巡检和交接

## 7. 推荐方案

推荐采用：

- `方案 A：资产治理型`

其核心做法是：

- 以 `KnowledgeUpdate` 为统一 intake
- 统一生成目标路径候选、校验报告和三类检查结果
- 复用现有模板、索引和路径路由作为底层基础设施
- 让 skill 层负责说明“这份知识来自哪里、是否合格、应落到哪里、有哪些治理问题”

不推荐：

- 把 v1 做成简单的文档生成器
- 把重点放到巡检报表，而忽略 intake 和落盘闭环
- 在没有 preview/result contract 的前提下扩大量知识目录

## 8. 对象模型

### 8.1 `KnowledgeIntakeSpec`

表示知识接入对象，最少包含：

- `asset_type`
- `title`
- `summary`
- `evidence_refs`
- `source_skill`
- `handoff_summary`

### 8.2 `AssetTargetSpec`

表示目标资产落点，最少包含：

- `target_path`
- `target_directory`
- `slug`
- `template_type`
- `index_target`
- `allow_overwrite`

### 8.3 `AssetValidationSpec`

表示资产校验结果，最少包含：

- `title_valid`
- `asset_type_valid`
- `evidence_valid`
- `template_match`
- `metadata_valid`
- `validation_notes`

### 8.4 `KnowledgeCheckSpec`

表示知识检查结果，最少包含：

- `drift_flags`
- `gap_flags`
- `stale_flags`
- `severity`
- `repair_suggestions`

### 8.5 `KnowledgeWritebackSpec`

表示知识落盘计划，最少包含：

- `asset_body`
- `index_updates`
- `writeback_notes`
- `writeback_targets`

## 9. Preview 产物

`Knowledge-Ops SKILL` 的 preview 建议固定输出：

- `intake_summary`
- `asset_target_candidate`
- `validation_report`
- `check_report`
- `risk_flags`
- `requires_confirmation`

### 9.1 `intake_summary`

必须能回答：

- 这份知识来自哪个 skill
- 当前属于什么资产类型
- 对应哪个目标、任务或执行结果
- 为什么现在要进行知识治理

### 9.2 `risk_flags`

至少包括：

- `unknown_asset_type`
- `empty_title`
- `missing_evidence_refs`
- `stale_source_hint`
- `template_missing`
- `index_alignment_gap`

### 9.3 `asset_target_candidate`

必须显式包含：

- 将要落到哪个目录
- 对应的文件名和 slug
- 使用什么模板
- 应更新哪个索引

### 9.4 `validation_report`

必须显式展示：

- 标题是否合法
- 类型是否合法
- 证据是否存在
- 模板与元数据是否匹配
- 当前是否允许覆盖已有资产

## 10. 执行链路

统一执行链路为：

1. `knowledge intake`
2. `preview`
3. `confirmation / policy check`
4. `materialize`
5. `verify`
6. `handoff`

### 10.1 Knowledge Intake

只做三件事：

- 读取 `KnowledgeUpdate` 和 handoff
- 归一化知识接入对象
- 提取最小来源元数据

### 10.2 Preview

只做四件事：

- 生成目标路径候选
- 生成校验报告
- 生成三类检查结果
- 暴露风险标记与覆盖风险

### 10.3 Confirmation / Policy Check

当存在以下情况时，必须要求确认或进入门禁：

- 目标资产已存在且可能覆盖
- `unknown_asset_type`
- `empty_title`
- `template_missing`
- 三类检查存在高优先级治理问题

### 10.4 Materialize

确认后按固定顺序执行：

1. `intake_normalization`
2. `asset_target_resolution`
3. `validation_snapshot`
4. `knowledge_asset_writeback`
5. `index_alignment_check`

### 10.5 Verify

验证至少分四层：

- 目标文件是否存在
- 内容结构是否与模板一致
- 索引是否对齐
- 检查结果是否被正确保留

### 10.6 Handoff

每次执行后必须生成：

- 成功或失败 handoff
- `ExecutionResult`
- `KnowledgeUpdate` 回执

## 11. 适配器边界

建议将 `Knowledge-Ops SKILL` 设计为“薄 skill + 稳定适配器”。

### 11.1 `Intake Adapter`

负责：

- 读取 `KnowledgeUpdate`
- 读取 handoff
- 归一化输入结构

不负责：

- 治理决策
- 路径策略

### 11.2 `Targeting Adapter`

负责：

- 路径解析
- slug 生成
- 模板选择
- 索引归属确定

### 11.3 `Validation Adapter`

负责：

- 标题校验
- 类型校验
- 证据校验
- 模板与元数据匹配校验

### 11.4 `Check Adapter`

负责：

- `drift` 检查
- `gap` 检查
- `stale` 检查

### 11.5 `Writeback Adapter`

负责：

- 资产落盘
- 索引更新
- 写回结果记录

### 11.6 Skill 本体职责

`Knowledge-Ops SKILL` 本身只负责：

- 读取输入
- 生成 preview
- 决定执行顺序
- 汇总验证结果
- 产出 handoff / knowledge update 回执

## 12. 失败策略

建议固定四类执行状态：

### 12.1 `hard_block`

例如：

- `asset_type` 缺失或未知
- 标题为空
- 模板缺失
- 目标路径无法解析

结果：

- 停止执行
- 必须人工补齐或修正输入

### 12.2 `soft_block`

例如：

- 目标可解析，但证据不足
- 索引不对齐
- 检查结果存在明显 gap

结果：

- 允许输出 preview
- 不允许伪装成完全成功

### 12.3 `degraded_success`

例如：

- 资产已落盘
- 但索引、证据或元数据仍不完整

结果：

- 执行成功但降级
- 必须生成 check report 和后续动作

### 12.4 `confirmed`

表示：

- 资产已落盘
- 校验与检查通过
- 索引与目录对齐
- handoff 与知识回执完整

## 13. 检查与治理策略

建议 v1 至少覆盖三类检查：

### 13.1 `drift` 检查

优先覆盖：

- 模板结构漂移
- 索引与目录漂移
- 元数据与目标路径漂移

### 13.2 `gap` 检查

优先覆盖：

- 缺少证据引用
- 缺少目标索引项
- 缺少必要元数据或 handoff 信息

### 13.3 `stale` 检查

优先覆盖：

- 明显陈旧的来源提示
- 过时资产标记
- 未更新的运行文档或交接文档线索

对于：

- 漂移
- 缺口
- 陈旧

必须统一进入 `KnowledgeCheckSpec`，而不是散落在输出日志里。

## 14. 漂移策略

建议至少识别四类漂移：

### 14.1 `目标路径漂移`

知识类型和目标路径不再一致。

### 14.2 `模板漂移`

资产内容与标准模板结构不再一致。

### 14.3 `索引漂移`

资产存在，但索引中缺失或索引仍指向旧资产。

### 14.4 `元数据漂移`

标题、证据、来源摘要与当前资产内容不匹配。

其中：

- 目标路径漂移、模板漂移属于高优先级
- 索引漂移、元数据漂移允许局部降级，但不能静默忽略

## 15. 测试策略

建议测试固定为四层：

### 15.1 Intake / Targeting Tests

验证：

- intake 归一化
- 路径解析
- slug 生成
- 模板选择

### 15.2 Validation Tests

分别验证：

- 空标题
- 未知资产类型
- 缺证据
- 模板缺失

### 15.3 Asset / Index Tests

验证：

- 模板存在
- 目录存在
- 索引结构正确
- 落盘路径与索引归属一致

### 15.4 Dry-Run Tests

验证：

- `intake -> validate -> check -> writeback -> verify -> handoff`
- `KnowledgeUpdate` 回执与 handoff 是否完整输出
- `drift / gap / stale` 是否作为一等结果返回

## 16. 风险与应对

### 16.1 风险：退化成文档生成器

应对：

- 固定 v1 覆盖 `Intake + Validation + Check`
- 不做知识面板

### 16.2 风险：只有路径路由，没有治理语义

应对：

- 强制 preview-first
- 强制输出校验报告和检查结果

### 16.3 风险：知识资产继续失控增长

应对：

- 把类型、标题、证据和模板约束固定进对象模型和测试
- 优先复用现有模板和索引，不新增无约束目录

### 16.4 风险：问题只能留在日志中

应对：

- 固定输出 `ExecutionResult`
- 固定输出 `KnowledgeUpdate` 回执
- 固定保留 `drift / gap / stale` 结果和 handoff 记录

## 17. 验收标准

本设计完成后，应满足以下验收标准：

- 能清晰说明 `Knowledge-Ops` 在整个协作体系中的定位和主从关系
- 能定义 v1 的 `Intake + Validation + Check` 边界
- 能说明对象模型、preview 产物和写回顺序
- 能说明适配器边界、失败分级、检查策略与漂移策略
- 能说明测试策略和知识回收机制
- 能作为下一步实施计划与真实落地的统一设计基线
