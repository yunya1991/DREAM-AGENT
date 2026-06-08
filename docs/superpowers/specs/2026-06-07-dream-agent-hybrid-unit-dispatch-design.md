---
id: DREAM-AGENT-HYBRID-UNIT-DISPATCH-DESIGN
type: design
owner: governance-agent
depends:
  - AGENT-COLLABORATION-SYSTEM-V1-DESIGN
  - GITHUB-FEISHU-OKR-KNOWLEDGEBASE-DESIGN
version: 1
last_verified: 2026-06-07
---

# Dream-Agent 混合单元编排设计

> 仓库：`DREAM-AGENT`
> 日期：`2026-06-07`
> 状态：draft
> 目标：在复用现有 `Dream-Agent` 协作底座的前提下，为“策略主线”构建一套以混合单元为核心、支持 GitHub 与飞书双链协作的统一编排入口。

## 0. 文档元信息

本文档面向以下读者：

- 负责定义任务、拆分单元、维护依赖与收口的 `governance agent`
- 负责具体实现前端承接与中台能力接线的 `developer agent`
- 负责契约校验、链路验收与质量裁决的 `validator agent`
- 负责 acceptance、ledger、治理回写的协作自动化维护者
- 负责目标确认与优先级选择的用户

一句话定义如下：

> `Dream-Agent 混合单元编排` 是一套建立在现有 Dream-Agent 协作底座之上的统一调度模型，用最小可跑的混合单元来驱动 GitHub 执行主链与飞书协作资产主链协同推进。

## 1. 背景与问题定义

当前 `DREAM-AGENT` 已具备较完整的协作底座：

- 已有基于 GitHub 的 `developer / validator / acceptance / governance` 角色流转
- 已有生命周期门禁、PR 评论协议、acceptance cycle、governance ledger
- 已有 GitHub x 飞书 Base / OKR / 知识库的真实联调经验与 runbook

这些基础说明当前问题不再是“有没有 agent 编排”，而是“如何把已有编排能力收口成面向业务建设的统一任务入口”。

当前仍存在以下缺口：

- 现有 Dream-Agent 更像协作底座，而不是面向业务交付的统一入口
- 多个 workflow 已存在，但缺少一个面向“最小功能单元”的统一 dispatch 模型
- 业务建设中的前端承接、中台能力、验证回写经常分散在不同任务中，交接成本高
- 飞书 CLI 虽已具备 Base / OKR / Docs / Wiki 能力，但在系统设计中还没有被提升为一级正式能力
- 飞书侧存在权限、资源写入、平台提示噪音等真实卡点，因此需要正式定义降级与回填策略

用户当前目标不是重建 Dream-Agent，而是：

1. 复用现有 Dream-Agent 协作底座
2. 先完善协作系统与任务编排
3. 再设置自动化任务与多 agent 协作推进
4. 最终让“策略主线”进入真实、可跑的构建流程

## 2. 设计目标

本设计的目标如下：

- 定义 Dream-Agent 的统一业务任务入口：`Hybrid Unit Dispatch`
- 以 `混合单元` 作为最小协作与交付单元，而不是以大模块或单纯代码任务为单位
- 让每个单元同时覆盖前端承接、中台能力、验证回写、协作资产四个面
- 将 GitHub 明确为执行主链，将飞书明确为协作资产主链
- 将飞书 CLI 提升为一级正式能力，而不是可有可无的附录能力
- 明确定义飞书侧不可用时的降级机制，确保 GitHub 主链不断
- 建立混合单元级别的版本管理与回滚机制，防止 AI 错误在早期阶段放大
- 为“策略主线”提供第一批可直接接入的样板单元
- 为后续自动化任务分发、多 agent 续跑、ledger 收口提供统一数据模型

成功标准如下：

- 任意一个混合单元都能被唯一标识、分派、执行、验收与回写
- agent 不再对“大模块”工作，而是对可跑闭环单元工作
- GitHub 主链可独立跑通，不因飞书侧阻塞而整体停工
- 飞书协作资产能在可用时真实联动，在不可用时进入正式回填路径
- 任意单元在出现错误实现、错误编排或错误资产写入时，都有明确回滚锚点
- 第一条 `策略主线` 样板单元可作为后续自动化编排模板复用

## 3. 非目标与边界

本设计明确不做以下事项：

- 不重建一套新的 Dream-Agent 协作系统
- 不替代现有 GitHub Actions / lifecycle guard / acceptance / governance 机制
- 不要求飞书 CLI 在所有时刻都成为硬阻塞依赖
- 不在本阶段覆盖所有策略主线节点
- 不在本阶段解决跨仓库、跨租户、跨组织的统一调度问题
- 不把飞书 Base / OKR / Docs 的全部能力都纳入首轮自动化

本设计的边界如下：

- 只在 `DREAM-AGENT` 现有协作底座之上增加一层统一编排入口
- 只围绕 `混合单元` 这一最小闭环模型来做调度
- 只优先支持“策略主线”的首批样板单元
- 飞书 CLI 作为一级正式能力纳入架构，但必须允许降级

## 4. 设计原则

### 4.1 复用优先，不重建底座

`Dream-Agent` 已有编排能力，本设计只补“统一入口层”，不重写现有角色流与 workflow。

### 4.2 混合单元优先于大模块

agent 只能对最小可跑闭环单元工作，不直接对“整个策略主线”或“整个中台首页”工作。

### 4.3 链路可跑优先于界面完备

每个单元的最小验收标准是链路可跑，而不是页面精修或全量业务完备。

### 4.4 GitHub 是执行主链

代码实现、workflow 驱动、评论协议、acceptance、governance、ledger 回写全部以 GitHub 为主链承载。

### 4.5 飞书是协作资产主链

Base、OKR、Docs、Wiki、知识入口、外部协作可见资产都由飞书侧承接，并通过飞书 CLI 进入正式架构。

### 4.6 飞书能力正式纳入，但允许降级

飞书 CLI 是一级正式能力，但当权限、写入、身份或平台噪音阻断真实联动时，系统必须退回 GitHub 主链继续推进，并登记待回填事项。

### 4.7 自动化负责任务流转，不负责目标创造

自动化可以执行已确认单元，但不应自行创造业务目标或擅自扩大范围。

### 4.8 先可回滚，再放大自动化

在系统初期，任何自动化推进都必须建立在明确版本锚点与回滚路径之上。AI 可以提速，但不能以不可逆风险换速度。

## 5. 系统分层

整体系统分为四层：

### 5.1 编排内核层

由 Dream-Agent 现有底座承载：

- lifecycle guard
- developer / validator / acceptance / governance agent
- acceptance cycle
- governance ledger
- task / handoff / protocol checker

### 5.2 工程执行层

由 GitHub 承载：

- PR / comment 协议
- GitHub Actions workflow
- 代码实现、测试、验收
- ledger 与治理回写

### 5.3 协作资产层

由飞书及飞书 CLI 承载：

- Base 任务记录
- Objective / KR 关联
- Docs / Wiki / 知识入口
- 外部可见的协作文档与状态承接

### 5.4 业务主线层

由业务模块承载：

- 策略主线
- 前端承接界面
- 中台能力节点
- 结果回写与运营透视

## 6. 核心概念模型

### 6.1 混合单元

`混合单元` 是本设计中的最小协作与交付单元。

它不是纯前端任务，也不是纯中台能力任务，而是一个最小可跑闭环，必须同时覆盖四个面：

- `前端承接面`
- `中台能力面`
- `验证回写面`
- `协作资产面`

### 6.2 Hybrid Unit Dispatch

`Hybrid Unit Dispatch` 是新增的统一入口概念。

它不替代现有 workflow，而是负责把业务侧混合单元翻译成 Dream-Agent 可以执行的标准协作对象。

### 6.3 协作资产面

协作资产面是本设计新增的正式概念，用于描述单元是否需要：

- 写入飞书 Base
- 关联 Objective / KR
- 更新 Docs / Wiki
- 补充外部协作可见信息
- 记录失败后的回填计划

### 6.4 双链协作

本设计采用双链协作模型：

- `GitHub 执行主链`
- `飞书协作资产主链`

Dream-Agent 作为二者之间的编排内核。

## 7. 混合单元数据模型

每个混合单元至少包含以下字段：

- `unit_id`
- `unit_name`
- `track`
- `goal`
- `frontend_surface`
- `platform_capability`
- `execution_path`
- `acceptance_target`
- `collaboration_asset_surface`
- `dependencies`
- `suggested_agents`
- `handoff_contract`
- `fallback_strategy`
- `version_anchor`
- `rollback_strategy`
- `next_unit`

字段解释如下：

- `track`
  - 当前单元所属业务主线，例如 `strategy-mainline`
- `frontend_surface`
  - 单元在页面上的承接点、入口、状态视图或交互区域
- `platform_capability`
  - 单元实际调用或新增的中台能力
- `execution_path`
  - 从输入到处理到结果的最小运行路径
- `acceptance_target`
  - 用于判断链路是否跑通的最小验收目标
- `collaboration_asset_surface`
  - 飞书侧需要承接的 Base / OKR / Docs / Wiki 资产信息
- `suggested_agents`
  - 推荐参与的 agent 组合
- `handoff_contract`
  - 当前单元向下游单元或下一个 agent 交接的最小信息包
- `fallback_strategy`
  - 飞书侧或外部能力失败时的正式降级方案
- `version_anchor`
  - 当前单元对应的 Git 提交、PR 状态、workflow run、飞书资产写入前状态等版本锚点
- `rollback_strategy`
  - 当前单元失败时允许采用的回滚方式、触发条件与责任角色
- `next_unit`
  - 当前单元完成后推荐进入的下一个单元

## 8. Agent 编排规则

### 8.1 角色分工

- `governance agent`
  - 负责定义混合单元、维护依赖、决定是否释放执行
- `developer agent`
  - 负责实现前端承接与中台能力接线
- `validator agent`
  - 负责校验单元契约与链路完整性
- `acceptance agent`
  - 负责验证链路是否真的可跑，并输出验收结论
- `governance / ledger automation`
  - 负责收尾治理、回写与下一单元释放

### 8.2 执行顺序

推荐执行顺序如下：

1. `dispatch`
2. `developer`
3. `validator`
4. `acceptance`
5. `governance`
6. `ledger sync`
7. `next unit release`

### 8.3 自动化边界

自动化可以：

- 根据已确认单元生成任务卡
- 根据规则推荐 agent 组合
- 触发现有 Dream-Agent workflow
- 回写执行状态、验收结论与 ledger 结果

自动化不可以：

- 自行创造新的业务目标
- 擅自扩大单元范围
- 在飞书 CLI 失败时直接中止 GitHub 主链
- 在没有版本锚点和回滚策略时自动放大发布或继续下一个高风险单元

## 9. 飞书 CLI 的正式定位

飞书 CLI 在本设计中是一级正式能力，而非二级扩展能力。

它承担以下正式职责：

- 飞书 Base 中的任务记录读写
- Objective / KR 的上下文挂接
- Docs / Wiki 的协作资产沉淀
- 外部协作可见状态的承接与补充
- GitHub 主链之外的协作上下文同步

本设计不把飞书 CLI 作为可选附录，而是将其纳入正式架构的“协作资产层”。

## 10. 版本管理与回滚机制

考虑到当前协作主体包含 AI agent，而系统又处于持续建设早期，必须把版本管理与回滚能力作为正式设计要求，而不是后补工程习惯。

### 10.1 设计目标

版本管理与回滚机制用于解决以下风险：

- AI 在单元实现中引入错误逻辑
- agent 错误理解任务边界并扩大改动范围
- workflow 在错误输入下推进到后续阶段
- 飞书侧写入了错误 Base / Docs / Wiki 资产
- 多 agent 并行推进时，某一单元失败导致下游单元建立在错误状态上

### 10.2 版本锚点

每个混合单元必须至少记录以下锚点中的一部分：

- `git_commit_before`
- `git_branch_or_pr_ref`
- `workflow_run_id`
- `acceptance_request_id`
- `ledger_checkpoint`
- `feishu_asset_before_snapshot`

其中：

- GitHub 锚点用于代码和 workflow 回退
- ledger checkpoint 用于治理状态恢复
- 飞书资产快照用于 Base / Docs / Wiki 的差异回补或人工回退

### 10.3 回滚层级

系统支持三层回滚：

1. `单元级回滚`
- 只回退当前混合单元的代码、状态、资产写入
- 是默认首选回滚方式

2. `链路级回滚`
- 回退当前单元及其尚未稳定的下游单元
- 用于错误已经穿透到后续执行链路时

3. `资产级回滚`
- 不回退 GitHub 主链代码
- 只对飞书 Base / Docs / Wiki / OKR 关联做修复、删除、覆盖或回填

### 10.4 回滚原则

- 优先局部回滚，不做整体系硬回退
- 优先新提交修复，不直接破坏性重写历史
- 不允许用不透明方式掩盖 AI 错误
- 回滚动作必须留下结构化记录
- 回滚后必须重新进入 validator / acceptance

### 10.5 责任分工

- `developer agent`
  - 提供当前单元的代码回滚建议与影响面说明
- `validator agent`
  - 判断是否需要触发回滚，以及是单元级还是链路级回滚
- `governance agent`
  - 负责冻结下游单元、更新任务状态、记录回滚原因与后续重启条件
- `feishu asset operator`
  - 负责飞书资产级回退、修复或补录

### 10.6 初期强约束

在系统建设初期，以下单元默认必须带版本锚点和回滚策略后才能释放执行：

- 第一批策略主线样板单元
- 任何会写入飞书 Base 的单元
- 任何会创建或更新 Docs / Wiki 的单元
- 任何会触发真实 workflow 自动推进后续 agent 的单元

### 10.7 禁止事项

禁止以下做法：

- 在没有锚点的情况下自动续跑高风险单元
- 在未记录影响面的情况下直接手工覆盖飞书资产
- 将“修复成功”当成“不需要回滚记录”
- 用模糊表述替代回滚结论

## 11. 飞书降级与回填机制

考虑到当前已发生过以下真实问题：

- Base 资源写权限不足
- OKR 对象发现链路不稳定
- 用户身份 / bot 身份与 scope 组合复杂
- 平台对 auth/config 类命令存在提示噪音

因此必须定义正式降级机制。

### 11.1 降级原则

当飞书 CLI 发生阻塞时：

- GitHub 执行主链继续推进
- 不把飞书卡点误判为整体停工
- 当前混合单元进入 `GitHub-only with Feishu backfill` 模式
- 将待补 Base / OKR / Docs / Wiki 项登记进 runbook 或 handoff

### 11.2 可降级场景

以下场景允许降级：

- Base 读成功但写失败
- OKR 自动发现失败
- Docs / Wiki 资源创建失败但不影响主链执行
- 平台出现 auth/config 类噪音提示，但业务命令仍可继续

### 11.3 不可忽略场景

以下场景不得被静默忽略：

- GitHub 主链所需的关键上下文完全依赖飞书，且无法从 GitHub 获取替代值
- 单元的验收目标本身要求飞书侧真实回写成功
- 飞书侧失败会导致下一个单元拿不到必要输入

此时应将单元标记为 `blocked-by-feishu-asset`，而不是假装完成。

### 11.4 回填要求

若单元在降级模式下完成，必须补充：

- 待回填资产列表
- 回填前置条件
- 推荐执行人或 agent
- 回填后需要重新触发的 acceptance / governance 动作

## 12. 策略主线的首批样板单元

本设计推荐只先落一个样板单元，用于验证编排模型，而不是一次性展开整条策略主线。

### 12.1 样板单元

- `unit_name`: `策略设置成功 -> 生成策略任务单`

### 12.2 前端承接面

- 页面上出现“策略设置成功”状态
- 页面上可见“策略任务单已生成”或可生成入口
- 后续可接入 UI-Map / 策略入口页 / 状态卡片

### 12.3 中台能力面

- 接收策略设置结果
- 生成标准化任务单对象
- 产出可追踪的任务单 ID 与状态

### 12.4 验证回写面

- acceptance 能验证任务单对象已经生成
- governance 能回写该单元完成与下一单元建议
- ledger 能记录该单元的正式收口结果

### 12.5 协作资产面

- 飞书 Base 可记录该任务单
- 若可用，挂接 Objective / KR
- 若不可用，至少登记待回填任务单与协作资产入口

### 12.6 版本与回滚面

- 生成任务单前记录 Git 锚点
- 若真实 workflow 已触发，则记录 `workflow_run_id`
- 若飞书 Base 已写入，则保留写入前后快照或最小字段对比
- 若单元验收失败，默认优先执行单元级回滚，并冻结下游单元

## 13. 统一入口输出模型

`Hybrid Unit Dispatch` 在处理一个单元后，应输出标准协作包：

- `dispatch_decision`
- `assigned_agents`
- `execution_order`
- `required_comments`
- `acceptance_mode`
- `ledger_update_mode`
- `feishu_asset_mode`
- `next_unit_hint`

其中：

- `feishu_asset_mode` 至少支持：
  - `full-sync`
  - `degraded-with-backfill`
  - `blocked-by-feishu-asset`

## 14. 失败分流

### 14.1 编排失败

若当前单元无法明确：

- 输入
- 输出
- 验收目标
- handoff

则不得释放给 developer agent，应回退 governance 重新定义单元。

### 14.2 验收失败

若链路未跑通：

- validator / acceptance 应输出缺失环节
- 不得仅以“代码存在”判定单元完成

### 14.3 飞书侧失败

若飞书业务命令失败：

- 先判断能否降级
- 能降级则保持 GitHub 主链推进
- 不能降级则显式标记 `blocked-by-feishu-asset`

### 14.4 需要回滚

若出现以下任一情况，应进入正式回滚判断：

- 当前单元实现已被 validator 判定为方向错误
- acceptance 证明链路已跑错并污染后续状态
- 飞书资产写入了错误对象，且不能通过普通补写修正
- 自动化任务错误释放了下游单元

## 15. 设计完成标准

本设计只有在以下条件同时满足时才算完成：

1. 已明确 Dream-Agent 复用而非重建
2. 已定义混合单元作为最小编排单元
3. 已定义统一入口 `Hybrid Unit Dispatch`
4. 已将飞书 CLI 提升为一级正式能力
5. 已定义版本管理与回滚机制
6. 已定义飞书降级与回填机制
7. 已确定策略主线的首个样板单元
