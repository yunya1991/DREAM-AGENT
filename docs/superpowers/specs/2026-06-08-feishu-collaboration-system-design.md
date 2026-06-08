---
id: FEISHU-COLLABORATION-SYSTEM-DESIGN
type: design
owner: governance-agent
depends:
  - OKR-DRIVEN-SKILL-DESIGN
  - CENTRAL-HUB-OKR-BINDING-DESIGN
  - FEISHU-BOSS-VIEW-OKR-MID-LINKAGE-DESIGN
version: 1
last_verified: 2026-06-08
---

# 飞书协作体系总纲设计

> 仓库：`DREAM-AGENT`
> 日期：`2026-06-08`
> 状态：draft
> 目标：构建一套以飞书为协作主界面、以 Git 为工程真源、以事件驱动为默认响应方式的协作体系，使 `OKR -> Base -> GitHub -> Approval -> Knowledge/Ops` 形成可持续维护、可追踪、可排障、可交接的统一系统。

## 1. 背景

当前仓库已经具备多条局部能力链路：

- `OKR-driven SKILL` 已完成第一版落地，证明“设计编排 + 确认后实操”是可行路径
- `目标推进表`、`老板视图（状态与阻塞）`、`workflow_signal` 已形成目标投影与管理界面
- GitHub 与飞书 Base、审批、上下文采集、状态回写脚本已经存在可复用底座
- runbook、handoff、知识库、FAQ、运维脚本并非空白，但目前分散在多个目录、多个历史仓和多个阶段性产物中

这说明当前真正缺失的不是某一个点状技能，而是一个能统一组织以下内容的上层体系：

- 统一 5 个核心 skill 的职责边界
- 统一变化触发后的协同响应机制
- 统一 skill、脚本、runbook、handoff 与知识沉淀的目录和真源
- 统一长期目标、短期执行、研发状态、审批治理和知识运维之间的闭环

## 2. 问题定义

本设计主要解决以下六类问题：

### 2.1 技能能力分散

当前已有能力分别落在：

- `docs` 中的设计与计划
- `github-actions` 中的执行脚本
- `.trae/skills` 或其他 skill 目录中的技能壳
- 多个历史仓和快照中的知识与排障材料

结果是材料很多，但入口不统一，维护成本高。

### 2.2 设计与实操未形成统一制度

用户明确要求所有核心 skill 都必须同时具备：

- 设计编排能力
- 真实执行能力

如果没有统一契约，不同 skill 会出现：

- 有的只有设计说明
- 有的只有自动化脚本
- 有的只有临时操作经验

这会导致体系无法复制和交接。

### 2.3 长期目标与短期动作容易漂移

体系的业务核心不是单个表单或单个流程，而是：

- `OKR-driven` 定义长期目标和方向
- `多维表格` 把目标拆成任务、进度与管理字段
- `GitHub-Feishu` 把研发真实状态反馈回管理界面
- `Approval` 在高风险变更时接管
- `Knowledge-Ops` 负责沉淀、运维和故障恢复

如果这些模块彼此割裂，目标会逐步漂移。

### 2.4 更新维护缺少协同响应

后期最容易出现的问题不是“没有能力”，而是：

- OKR 已更新，Base 和任务层未同步
- GitHub 已阻塞，老板视图仍显示推进中
- 审批已拒绝，但运行状态未回写
- 发生过故障，但知识库未沉淀排障结论

因此体系必须具备默认的协同响应机制。

### 2.5 真源不唯一

当前工作区中存在主仓、历史仓、快照、临时合并目录、备份目录，知识资产也分散在不同位置。若不先定义真源，将直接影响：

- 后续维护
- 交接效率
- runbook 准确性
- 审计与升级决策

### 2.6 知识库与运维未体系化

知识沉淀目前更像“有文档”，但还不是“有治理体系”：

- handoff 未完全制度化
- runbook 缺总索引
- evidence 缺统一归档结构
- 知识更新缺少自动入口

## 3. 设计目标

本设计的目标如下：

- 在 `DREAM-AGENT` 中建立一套统一的飞书协作体系
- 将 5 个核心 skill 纳入同一治理框架
- 固化“预演 -> 确认 -> 执行 -> 验证 -> handoff -> 知识回收”的统一操作模型
- 默认采用事件驱动响应，确保系统更新维护时的协同联动
- 建立统一的目录组织、调用管理、知识分类与运维入口
- 为后续逐个审计和建设剩余 4 个核心 skill 提供总纲基线

成功标准：

- 能清晰回答每个核心 skill 的职责和边界
- 能定义任一关键对象变化后的响应路径
- 能明确文档、技能、脚本、runbook、handoff 的唯一真源与入口
- 能把知识沉淀和运维快速排障纳入体系，而非附属工作

## 4. 范围与非目标

### 4.1 本设计覆盖

- 飞书协作体系总纲
- 五个核心 skill 的边界、关系与推进顺序
- 统一协同响应架构
- 统一文件组织与调用管理
- 知识库-运维模型
- 后续审计与建设顺序

### 4.2 本设计不覆盖

- 立即实现其余 4 个核心 skill
- 一次性重构所有历史目录和历史仓
- 一次性收拢所有旧知识资产
- 立刻构建完整的全自动事件总线服务

本设计先定义总纲与治理基线，再逐个进入设计与实施。

## 5. 核心原则

### 5.1 体系优先于单点

每个 skill 的设计都必须服从整个体系的边界、调用协议与知识治理规则，而不是独立生长。

### 5.2 所有核心 skill 都必须双态运行

统一要求：

- 先做设计编排
- 再做真实执行

任何只停留在建议、说明、模板或零散脚本层的能力，都不算完成。

### 5.3 预演优先

所有会影响线上对象或管理真源的变更，必须先生成 `ExecutionPreview`，经过确认后再执行。

### 5.4 事件驱动为默认响应模式

系统默认不是依赖人工发现问题，而是关键对象一变化就进入统一响应流程。

### 5.5 知识沉淀与运维不是附属流程

执行结束后必须补齐：

- verification
- handoff
- knowledge update

否则视为未闭环。

### 5.6 单主仓、单主线、单真源

`DREAM-AGENT` 作为该体系的主干真源仓，其他历史目录只作为参考，不再作为主线设计输入。

## 6. 推荐总体架构

推荐采用五层架构：

### 6.1 L0 治理层

负责：

- 体系总纲
- 角色边界
- 责任分工
- 命名规范
- 真源定义
- 升级与升级响应策略

### 6.2 L1 编排层

负责：

- 事件入口
- 响应中枢
- 调用协议
- 预演、确认、执行、验证的统一流程

### 6.3 L2 领域技能层

包含五个核心 skill：

- `OKR-driven`
- `Bitable`
- `GitHub-Feishu`
- `Approval`
- `Knowledge-Ops`

### 6.4 L3 执行底座层

负责：

- `github-actions` 执行器
- Lark CLI 适配
- GitHub workflow 适配
- 浏览器 fallback
- 测试、fixtures、共享 builder

### 6.5 L4 知识与运维层

负责：

- handoff
- runbook
- FAQ
- evidence
- 变更记录
- 漂移检查
- 知识保鲜

## 7. 五个核心 skill 的职责边界

### 7.1 `OKR-driven`

职责：

- 从 `spec + plan` 编排长期目标
- 输出 Objective/KR、目标推进记录、任务候选、workflow 候选
- 在确认后执行目标层与锚点层操作

定位：

- 战略编排器
- 长期目标真源入口

### 7.2 `Bitable`

职责：

- 把目标层拆解到 Base 的任务、进度、状态、视图字段
- 保证目标、任务、进度之间持续对齐
- 负责“长期目标到短期动作”的落地面

定位：

- 执行面编排器
- 长短期对齐器

### 7.3 `GitHub-Feishu`

职责：

- 把 GitHub issue / PR / checks / merge 状态映射到飞书协作对象
- 回传研发真实进展与阻塞
- 缩短工程真相与管理视图之间的距离

定位：

- 状态同步器
- 工程与管理桥梁

### 7.4 `Approval`

职责：

- 风险门控
- 审批发起
- 审批状态轮询
- 结果回写与升级处理

定位：

- 治理闸门
- 高风险变更接管器

### 7.5 `Knowledge-Ops`

职责：

- 接收前四个 skill 的知识更新
- 管理 handoff、runbook、FAQ、evidence
- 提供故障排查入口和运维导航
- 做漂移检查、缺口检查和过期检查

定位：

- 记忆中枢
- 运维中枢

## 8. 统一协同响应架构

### 8.1 统一事件入口

所有变化统一抽象为事件，不允许模块之间零散互调。

推荐事件类型：

- `okr.changed`
- `bitable.record.changed`
- `github.issue.changed`
- `github.pr.changed`
- `approval.status.changed`
- `knowledge.asset.changed`

统一事件包最少包含：

- `event_id`
- `event_type`
- `source_system`
- `source_object_id`
- `changed_fields`
- `risk_hint`
- `related_goal_id`
- `occurred_at`

### 8.2 响应中枢

响应中枢不是“大一统超级 skill”，而是统一协调器，负责：

- `impact_analysis`
- `policy_check`
- `dispatch`
- `closure`

也就是：

- 判断影响哪些模块
- 判断能否自动处理
- 决定调用哪个 skill
- 判断是否闭环，否则升级

### 8.3 响应级别

建议固定四级响应：

- `P0 自动阻断`
- `P1 自动联动`
- `P2 知识维护`
- `P3 观测记录`

其中：

- P0 对应高风险和一致性破坏
- P1 对应常规状态变更与回写
- P2 对应知识资产补齐与运维沉淀
- P3 对应低风险观测与证据记录

### 8.4 闭环状态

每次响应必须落在以下状态之一：

- `observed`
- `synced`
- `confirmed`
- `blocked`
- `escalated`

任何只跑过脚本却没有闭环状态的操作，都不算完成。

### 8.5 标准响应记录

每次响应必须能输出：

- `event`
- `impacted_modules`
- `actions_taken`
- `writebacks`
- `verification_result`
- `next_owner`
- `knowledge_update_required`

## 9. 统一文件组织与调用管理

### 9.1 文档组织

建议新增统一体系目录：

- `docs/feishu-collab/governance/`
- `docs/feishu-collab/specs/`
- `docs/feishu-collab/plans/`
- `docs/feishu-collab/runbooks/`
- `docs/feishu-collab/handoffs/`

这些目录分别承担：

- 治理规则
- 设计文档
- 实施计划
- 运维与故障手册
- 标准交接资产

### 9.2 skill 挂载规范

建议所有核心 skill 统一收口到 `.trae/skills/`：

- `.trae/skills/feishu-collab-okr-driven/`
- `.trae/skills/feishu-collab-bitable/`
- `.trae/skills/feishu-collab-github-sync/`
- `.trae/skills/feishu-collab-approval/`
- `.trae/skills/feishu-collab-knowledge-ops/`

每个 skill 固定包含：

- `SKILL.md`
- `references/execution-checklist.md`
- `references/data-contracts.md`
- `references/escalation-policy.md`

### 9.3 执行器组织

建议将飞书协作体系执行器按领域归档：

- `github-actions/feishu_collab/okr/`
- `github-actions/feishu_collab/bitable/`
- `github-actions/feishu_collab/github_sync/`
- `github-actions/feishu_collab/approval/`
- `github-actions/feishu_collab/knowledge_ops/`
- `github-actions/feishu_collab/shared/`

其中 `shared/` 保存：

- 统一事件模型
- 统一日志与 tracing
- Lark/GitHub 客户端适配
- 认证、时间、ID 处理
- 通用 preview/result builder

### 9.4 调用协议

建议统一四类调用对象：

- `ExecutionIntent`
- `ExecutionPreview`
- `ExecutionResult`
- `KnowledgeUpdate`

含义分别为：

- 我要做什么
- 准备怎么做、影响什么
- 实际做了什么、结果如何
- 需要沉淀哪些知识资产

### 9.5 统一入口

建议建立四个总索引文件：

- `docs/feishu-collab/README.md`
- `docs/feishu-collab/SKILL_REGISTRY.md`
- `docs/feishu-collab/RUNBOOK_INDEX.md`
- `docs/feishu-collab/HANDOFF_INDEX.md`

作用是：

- 给新成员固定阅读入口
- 给维护者固定检索入口
- 给系统演进固定注册表

## 10. 知识库-运维模型

### 10.1 知识资产五层分类

建议统一为五类：

- `Policy`
- `Architecture`
- `Delivery`
- `Operations`
- `Evidence`

分别承载：

- 制度与边界
- 架构与协议
- 设计、计划、handoff、变更
- runbook、巡检、恢复
- 审批、日志、截图、验证结果、PR 链接

### 10.2 知识更新机制

前四个核心 skill 在执行结束后必须输出 `KnowledgeUpdate`，交由 `Knowledge-Ops` 分类沉淀。

这意味着：

- `OKR-driven` 负责回写目标编排与验证结论
- `Bitable` 负责回写任务拆解和字段对齐变更
- `GitHub-Feishu` 负责回写同步结果和差异证据
- `Approval` 负责回写审批轨迹、风险判断和结果投影

### 10.3 handoff 制度化

handoff 不再是临时备注，而是标准资产。

每份 handoff 至少包含：

- `背景`
- `当前状态`
- `已完成`
- `未完成`
- `当前阻塞`
- `下一步动作`
- `依赖对象`
- `风险提示`
- `证据链接`
- `接手人关注点`

handoff 分为：

- `阶段 handoff`
- `故障 handoff`

### 10.4 runbook 模型

建议 runbook 按场景分类：

- `变更 runbook`
- `联动 runbook`
- `故障 runbook`
- `恢复 runbook`

不再按个人经验或零散 skill reference 存放。

### 10.5 持续维护动作

`Knowledge-Ops` 负责三类持续治理动作：

- `漂移检查`
- `缺口检查`
- `过期检查`

这使其成为动态治理能力，而非静态文档仓。

## 11. 系统更新维护与协同响应

### 11.1 默认模式

本体系默认采用 `事件驱动`。

即：

- 关键对象变化时立即触发联动分析
- 不是等定时任务或人工发现后再补救

### 11.2 维护时的协同路径

任一关键变化发生后，统一走以下路径：

1. 事件产生
2. 进入响应中枢
3. 分析影响面
4. 调用相关 skill
5. 写回结果
6. 进行验证
7. 生成 handoff / knowledge update

### 11.3 漏账兜底

v1 默认主模式是事件驱动，但总纲预留后续补充轻量巡检能力，用于：

- reconciliation
- 一致性复查
- 知识补齐扫描

也就是说：

- 主流程靠事件驱动保证及时性
- 后续可增加轻量巡检保证不漏账

## 12. 推荐落地方案

推荐方案为：

- `总纲先行，五个核心 skill 逐个纳入`

原因：

- 当前最急需的是统一治理，而不是继续增加零散能力
- `OKR-driven` 已经具备样板作用，可以作为其余 skill 的模板
- 其余 4 个核心 skill 最缺的是边界收口和统一协议

不推荐：

- 先做超级总 skill
- 先做重型调用中枢而忽略治理与知识体系

## 13. 建设顺序

推荐顺序如下：

1. 写本总纲设计
2. 基于总纲审计剩余 4 个核心 skill
3. 先做 `Bitable`
4. 再做 `GitHub-Feishu`
5. 再做 `Approval`
6. 最后做 `Knowledge-Ops`

排序原因：

- `Bitable` 是 `OKR-driven` 的最近落地层
- `GitHub-Feishu` 决定工程真实状态如何回传
- `Approval` 决定治理门控
- `Knowledge-Ops` 负责最终稳定化与长期维护

## 14. 风险与应对

### 14.1 风险：仍沿用旧目录与旧入口

应对：

- 在总纲实施时明确新入口
- 对旧目录只保留引用，不继续扩散主线资产

### 14.2 风险：skill 只补文档，不补执行

应对：

- 统一要求每个核心 skill 同时具备 preview 与 execute

### 14.3 风险：知识库继续被动维护

应对：

- 强制前四个 skill 输出 `KnowledgeUpdate`
- 由 `Knowledge-Ops` 接管沉淀

### 14.4 风险：系统维护只靠人工记忆

应对：

- 使用事件驱动响应
- 补标准响应记录与闭环状态

## 15. 验收标准

本总纲完成后，应满足以下验收标准：

- 能清晰说明 5 个核心 skill 的职责和调用顺序
- 能说明任意关键对象变化后如何触发联动响应
- 能说明体系级文档、技能、执行器、runbook、handoff 的统一归口
- 能说明知识库-运维如何保证沉淀、排障与持续维护
- 能作为后续 4 个 skill 审计和设计的统一输入基线
