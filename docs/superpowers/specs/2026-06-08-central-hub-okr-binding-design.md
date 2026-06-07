---
id: CENTRAL-HUB-OKR-BINDING-DESIGN
type: design
owner: governance-agent
depends:
  - FEISHU-BOSS-VIEW-OKR-MID-LINKAGE-DESIGN
version: 1
last_verified: 2026-06-08
---

# 中台能力 Objective/KR 绑定与目标驱动推进设计

> 仓库：`DREAM-AGENT`
> 日期：`2026-06-08`
> 状态：draft
> 目标：把“中台与前端联动验证能力打通”从一条 Base 目标记录，提升为真实飞书 OKR 的 `Objective + KR`，并与 `目标推进表`、任务层、workflow 形成目标驱动推进闭环。

## 1. 背景

当前已经完成以下基础落地：

- `目标推进表` 已在线落地，并已有 `老板视图（状态与阻塞）`
- `中台与前端联动验证能力打通` 已作为真实目标记录写入 Base
- OKR 联动锚点字段已存在：
  - `OKR对齐`
  - `okr_objective_id`
  - `okr_objective_title`
  - `okr_owner`
  - `okr_sync_status`
  - `okr_last_sync_at`
- 目标推进相关 workflow 已可运行

但当前仍有一个关键缺口：

- 这条业务目标还只是 `目标推进表` 中的一条记录
- 还没有绑定到真实飞书 `Objective`
- 更没有将中台架构图、spec、实施计划拆成可持续推进的 `KR`

因此，用户虽然已经能在老板视图里看到“中台与前端联动验证能力打通”，但还看不到一个真正承载“目标驱动构建中台”的飞书 OKR 结构。

## 2. 问题定义

本设计要解决的不是“给一条记录填一个 `okr_objective_id`”，而是三层问题：

### 2.1 目标层缺真实 OKR

当前目标记录的 `OKR对齐=待补OKR`，说明这条业务目标尚未完成正式 Objective 绑定。

### 2.2 能力层和任务层还没分层

中台建设涉及：

- 架构图中的能力边界
- spec 中的目标与约束
- implementation plan 中的推进步骤
- ledger / 任务里的实现动作

如果这些内容直接平铺到 OKR，会导致：

- KR 退化成任务列表
- OKR 过于细碎
- 老板视图、任务层、OKR 三套表达相互打架

### 2.3 尚未形成真正的目标驱动推进机制

目标驱动推进需要清楚区分：

- `Objective / KR`：为什么做、做到什么程度
- `目标推进表`：现在做到哪、卡在哪里
- `任务层`：具体怎么做

当前这套机制已经有雏形，但还没完成真实 Objective/KR 绑定。

## 3. 设计目标

本设计的目标如下：

- 把“中台与前端联动验证能力打通”绑定为真实飞书 `Objective`
- 在该 Objective 下创建一组可持续推进的 `KR`
- 明确 `KR` 与功能包、任务层之间的边界
- 将 `目标推进表` 与真实 Objective 建立稳定锚点关系
- 为后续把这套经验沉淀成 `OKR-driven SKILL` 做准备，但不在本设计中直接实现该 skill

成功标准如下：

- Base 中该目标记录从 `待补OKR` 变成 `已对齐`
- 能明确回答每个 `KR` 对应的能力结果，而不是实现碎片
- 老板视图、目标推进表、任务层、workflow 不发生职责冲突
- 后续可以围绕这套模型稳定迭代，而不是继续手工拼装

## 4. 范围与非目标

### 4.1 本轮范围

本轮只覆盖 `子项目 A`：

- 真实 Objective/KR 建模
- 与 `目标推进表` 的绑定方式
- 与任务层、workflow 的边界
- 绑定后的最小字段联动

### 4.2 明确不做

本轮不做以下事项：

- 不直接实现 `OKR-driven SKILL`
- 不把所有功能点都做成 KR
- 不在本轮重做老板视图架构
- 不把 Base 变成 OKR 主系统
- 不把任务系统并入 OKR

`OKR-driven SKILL` 将作为后续独立子项目处理。

## 5. 设计原则

### 5.1 Objective 代表目标，不代表任务集合

真实 Objective 必须表达“中台能力建设的目标结果”，不能只是“把若干任务串起来”。

### 5.2 KR 代表结果性能力，不代表代码动作

KR 可以表达：

- 实时桥接能力是否可运行
- 前端联动验证是否完成
- 闭环机制是否建立

但不应该直接表达：

- 写一个接口
- 改一个页面
- 修一个脚本

这些内容继续保留在任务层。

### 5.3 Base 管推进，OKR 管目标

- 飞书 OKR 管：
  - Objective
  - KR
  - owner
  - 目标层对齐关系
- `目标推进表` 管：
  - 当前状态
  - blocker
  - 下一步动作
  - 风险等级
  - 最近决策摘要

### 5.4 先绑定真实 Objective，再考虑沉淀方法论 Skill

只有先把真实 Objective/KR 绑定链路跑通，后续的 `OKR-driven SKILL` 才能沉淀在稳定流程之上。

## 6. 推荐建模方案

### 6.1 方案结论

采用：

- `1 个 Objective + 多个 KR`
- `KR` 采用“能力结果 + 推进机制”的混合型拆法

这是用户已确认的推荐方案。

### 6.2 Objective 建议文案

建议真实 Objective 使用如下文案：

> 中台与前端联动验证能力打通，并形成可持续的目标驱动建设机制

这一定义同时覆盖：

- 当前中台与前端联动验证目标
- 后续按架构图 / spec / 实施计划持续推进中台建设的长期方向

### 6.3 KR 建议文案

建议创建以下 4 个 KR：

- `KR1`：Hub 到 Trading 的实时桥接能力可运行，摆脱前端代理和目录投递的临时链路
- `KR2`：前端关键页面完成实时联动验证，能直接反映交易链路状态变化
- `KR3`：审批、目标推进、workflow 提醒与老板视图形成运行闭环
- `KR4`：架构图、spec、实施计划中的核心功能项被拆解进持续推进机制并可跟踪

这 4 个 KR 的分工如下：

- `KR1` / `KR2`：偏业务与技术能力
- `KR3`：偏治理与执行闭环
- `KR4`：偏方法论落地与持续推进

## 7. KR 与功能实现的分层

### 7.1 OKR 层

飞书 OKR 里只放：

- `Objective`
- `KR`

这一层表达的是：

- 为什么做
- 做到什么程度

### 7.2 功能包层

每个 KR 下面再关联一组“功能包”，但功能包默认不直接做成 KR。

例如：

`KR1` 对应功能包：

- Hub 侧 `/api/trading/*` 直连桥接
- Python 进程 / 子进程调用能力
- Trading 信号 -> Hub 决策 -> 执行闭环

`KR2` 对应功能包：

- `/dashboard` 实时状态联动
- `/chain` 双工作流联动
- 其他关键前端页面联动验证

`KR3` 对应功能包：

- 审批结果回写 `目标推进表`
- workflow 提醒稳定运行
- 老板视图与目标状态投影一致

`KR4` 对应功能包：

- 从架构图提取功能清单
- 从 spec / implementation plan 提取里程碑
- 建立持续同步机制

### 7.3 任务层

具体实现动作继续留在任务层，例如：

- 新增某个 Hub route
- 修改某个前端页面
- 增加某条 workflow 条件
- 修某个同步脚本

这一层表达的是：

- 具体怎么做

## 8. 目标推进表与 Objective/KR 的联动

### 8.1 目标记录绑定

当前目标记录：

- `goal_id = goal-trading-hub-connectivity-20260519`
- `目标名称 = 中台与前端联动验证能力打通`

应绑定到上述真实 Objective。

### 8.2 首批联动字段

本轮最小联动只要求以下字段完成绑定：

- `OKR对齐`：从 `待补OKR` 切换为 `已对齐`
- `okr_objective_id`
- `okr_objective_title`
- `okr_owner`

必要时同步：

- `okr_sync_status`
- `okr_last_sync_at`

### 8.3 可选后续字段

为了后续更好表达 KR 汇总状态，可在第二阶段考虑新增：

- `okr_kr_summary`
- `okr_kr_status_rollup`

但这两个字段不作为本轮必需项。

## 9. 与 workflow 的关系

现有 workflow 不负责创建或修改 OKR 核心对象。

其作用是：

- 当目标推进异常时提醒负责人
- 当审批结束时推动目标更新
- 当 OKR 未对齐时提示补绑

在 Objective/KR 绑定完成后，workflow 继续保持这一职责边界，不应越权改写真实 OKR。

## 10. 与后续 OKR-driven SKILL 的关系

本轮不实现 `OKR-driven SKILL`，但应把其输入输出边界设计清楚。

后续该 skill 应沉淀的是：

- 如何从架构图 / spec / plan 提取 Objective / KR 候选
- 如何把 Objective / KR 与 `目标推进表`、任务表、workflow 建立联动
- 如何随着过程演进持续更新

因此，`OKR-driven SKILL` 依赖于本轮先把真实 Objective/KR 绑定链路走通。

## 11. 实施建议

建议按以下顺序推进：

1. 在飞书 OKR 中创建真实 Objective
2. 在 Objective 下创建 4 个 KR
3. 将 `goal-trading-hub-connectivity-20260519` 绑定到 Objective
4. 回写 `目标推进表` 的 OKR 锚点字段
5. 验证 `老板视图` 中该目标从 `待补OKR` 变成 `已对齐`
6. 补一份后续子项目：`OKR-driven SKILL` 的单独 spec

## 12. 风险与控制

主要风险：

- 把 KR 做得过细，退化成任务列表
- Base 与 OKR 双写，造成真相源冲突
- 把尚未稳定的方法过早封装成 skill

控制策略：

- KR 只保留结果性表达
- Base 只做推进与驾驶舱，不做目标真源
- `OKR-driven SKILL` 延后到本轮绑定稳定后再做

## 13. 验收标准

完成后应满足：

- 真实飞书 OKR 中存在该 Objective
- Objective 下存在 4 个 KR
- `目标推进表` 中该业务目标记录已绑定 Objective
- `OKR对齐 = 已对齐`
- 老板视图仍聚焦 `状态 + 阻塞`，不被 KR 细节污染
- 后续可以基于这一链路继续沉淀 `OKR-driven SKILL`
