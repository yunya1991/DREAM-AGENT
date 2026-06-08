---
id: APPROVAL-POLLING-WRITEBACK-DESIGN
type: design
owner: governance-agent
depends:
  - REAL-APPROVAL-TRIGGER-DESIGN
  - APPROVAL-SKILL-DESIGN
  - FEISHU-COLLABORATION-SYSTEM-DESIGN
version: 1
last_verified: 2026-06-08
---

# 审批轮询回写设计

> 仓库：`DREAM-AGENT`
> 日期：`2026-06-08`
> 状态：draft
> 目标：新增一条独立的审批轮询回写 workflow，把真实审批实例的状态查询、统一投影与 task/goal 回写收口为正式主线入口，在不引入知识物化的前提下形成稳定、可验证、可交接的协作状态闭环。

## 1. 背景

当前仓库已经完成了两类相关能力：

- `Approval SKILL` 设计已经把目标闭环定义为 `risk gate -> create/reuse -> poll -> writeback -> handoff`
- `real-approval-trigger.yml` 已经把真实审批发起与单次查询收口为独立 workflow

同时，仓库底层也已经存在若干轮询与回写资产：

- `query_real_approval_status.py` 已负责单次状态查询与标准状态投影
- `poll_feishu_approval_and_sync_base.py` 已具备查询审批实例并同步回写 Base 的底座能力
- `sync_github_to_feishu.py` 与 `build_goal_progress_record.py` 已具备 task/goal 字段投影能力

这说明当前缺失的不是“能不能查审批”，而是：

- 一条正式的、独立的、operator 可发现的审批轮询回写主线

## 2. 问题定义

本设计主要解决以下四类问题：

### 2.1 主线入口仍然停留在单次查询

当前 `real-approval-trigger.yml` 的职责已经明确收口为：

- 真实发起
- 单次查询
- artifact 和 summary 留存

它并不负责继续把审批状态稳定写回协作系统，因此真实审批结果和协作状态之间仍然存在断层。

### 2.2 底层有 polling/writeback，正式主线没有收口

当前仓库已经具备：

- 审批状态查询
- task 记录投影
- goal 聚合记录投影
- Base 回写

但这些能力仍停留在脚本级资产，没有形成独立 workflow、runbook、artifact 与统一成功语义。

### 2.3 审批结果与协作状态可能撕裂

如果没有固定的查询与回写顺序，容易出现：

- 审批已通过，但 task 仍停留在 `pending`
- task 已更新，但 goal 聚合未同步
- goal 先写成功，而 task 实际未更新

这会让 operator 看到不一致的系统状态。

### 2.4 第四段知识构建需要稳定输入

后续“真实知识库构建”需要消费稳定的审批证据和回写证据。如果第三段没有先把轮询回写收口为正式主线，第四段将只能继续从散落脚本里拼装输入。

## 3. 设计目标

本设计的目标如下：

- 新增独立的 `approval-polling-writeback` workflow
- 默认只覆盖：
  - 审批状态查询
  - task/goal 回写
- 固定统一状态口径与回写顺序
- 输出标准 artifact 与 Job Summary
- 明确成功/失败语义
- 为第四段“真实知识库构建”保留清晰输入边界

成功标准：

- 存在正式的 polling workflow 文件
- workflow 能读取审批实例状态并生成统一状态投影
- workflow 能完成 task/goal 回写
- workflow 能输出审批侧与协作侧两个标准 artifact
- workflow 失败时仍保留 summary 与回写证据

## 4. 范围与非目标

### 4.1 本设计覆盖

- 独立 polling workflow
- 审批实例状态查询
- 统一状态投影
- task record writeback
- goal record aggregation 与 writeback
- artifacts
- Job Summary
- runbook 与 workflow 契约测试

### 4.2 本设计不覆盖

- 真实审批实例创建
- 周期性后台轮询服务
- knowledge materialization
- handoff/runbook 文档自动落盘
- acceptance/rehearsal 联动
- 多 workflow orchestrator

本轮只把“审批状态稳定回到协作系统”做稳，不在第三段提前把知识沉淀并进来。

## 5. 核心原则

### 5.1 单一职责原则

`real-approval-trigger.yml` 继续负责：

- 真实发起
- 初次查询

新 workflow 只负责：

- 读取审批实例状态
- 统一投影
- task/goal 回写

两条 workflow 保持职责解耦。

### 5.2 状态统一原则

审批侧状态必须先统一投影，再进入回写，不允许在 workflow 里散落多份状态映射。

### 5.3 顺序一致原则

回写顺序必须固定，避免 task 与 goal 状态撕裂。

### 5.4 证据优先失败原则

即使 workflow 判定失败，也必须尽量保留：

- 审批状态结果
- task 回写结果
- goal 回写结果
- summary

### 5.5 与知识构建解耦原则

第三段只负责把结果写回协作状态，不直接生成知识资产。第四段再消费本阶段 artifact 与 summary 进行知识沉淀。

## 6. 推荐方案

推荐采用：

- `方案 A：独立 polling workflow，复用现有脚本底座`

其核心做法是：

- 保持 `real-approval-trigger.yml` 轻入口不变
- 新增独立 `approval-polling-writeback.yml`
- 复用现有 query、polling、task/goal 投影脚本
- 用 workflow + summary + runbook 把脚本资产收口为正式主线

不推荐：

- 把 polling/writeback 直接并回 `real-approval-trigger.yml`
- 一步并入知识物化
- 直接引入长时间等待或后台轮询服务

## 7. 角色定位与主从关系

### 7.1 `real-approval-trigger`

负责：

- 创建真实审批实例
- 给出初次查询结果
- 留下实例级证据

### 7.2 `approval-polling-writeback`

负责：

- 根据 `approval_instance_code` 查询最新审批状态
- 生成统一状态投影
- 回写 task 记录
- 聚合并回写 goal 记录
- 输出审批侧和回写侧证据

### 7.3 与第四段知识构建的边界

第四段只消费第三段输出的 artifact 与 summary，例如：

- `approval_status_result.json`
- `approval_writeback_result.json`

而不要求第三段直接生成知识文档。

## 8. 对象模型

### 8.1 `approval_status_result`

表示审批系统侧的标准状态结果，最少包含：

- `approval_instance_code`
- `approval_status`
- `automation_status`
- `decision_summary`
- `decision_id`
- `raw_status`

职责：

- 记录真实审批实例当前状态
- 提供统一后的审批语义
- 为后续回写和第四段知识构建提供稳定输入

### 8.2 `approval_writeback_result`

表示协作系统侧的回写结果，最少包含：

- `task_id`
- `goal_id`
- `task_record`
- `goal_record`
- `task_writeback_status`
- `goal_writeback_status`
- `writeback_receipts`

职责：

- 记录 task/goal 是否已稳定进入协作状态
- 保留局部成功与局部失败的证据

## 9. 状态口径

### 9.1 审批状态

统一沿用已有审批链状态语义：

- `pending`
- `approved`
- `rejected`
- `not_required`

### 9.2 自动化状态

统一沿用已有自动化状态语义：

- `paused`
- `proceed`
- `blocked`
- `review_required`

### 9.3 映射原则

推荐固定以下映射：

- `pending -> paused`
- `approved -> proceed`
- `rejected -> blocked`
- `not_required -> proceed`

若 Feishu 返回更底层状态，则：

- 先保留到 `raw_status`
- 再投影到统一状态字段

workflow 不直接承载原始状态映射逻辑。

## 10. 回写顺序

统一回写顺序固定为：

1. `approval status projection`
2. `task record writeback`
3. `goal record aggregation`
4. `goal record writeback`
5. `writeback receipt capture`

原因：

- 先得到稳定审批结论
- 再更新 task
- 再基于最新 task 重新聚合 goal
- 最后记录回写证据

不允许：

- goal 领先于 task 写入
- receipt 提前于真实回写生成

## 11. Workflow 结构

### 11.1 新增独立 workflow

新增独立 workflow，例如：

- `.github/workflows/approval-polling-writeback.yml`

触发方式：

- `workflow_dispatch`

### 11.2 Job 结构

v1 建议保持单 job，顺序执行以下步骤：

1. `resolve inputs`
2. `query approval status`
3. `write back task/goal`
4. `render summary + upload artifacts`

不在本轮拆成多 job，避免把第三段范围扩展为复杂编排。

## 12. 输入模型

v1 最小输入集合建议固定为：

- `approval_instance_code`
- `decision_id`
- `task_payload_json`
- `goal_payload_json`

其中：

- `approval_instance_code` 必填，是轮询主键
- `decision_id` 选填，但建议保留，用于决策关联和状态投影
- `task_payload_json` 必填，用于 task 回写上下文
- `goal_payload_json` 必填，用于 goal 聚合与回写上下文

认证相关输入：

- `tenant_access_token` 不作为 workflow input 暴露
- 仍通过 runtime mint 或 secrets 注入

## 13. 结果模型

### 13.1 Artifacts

workflow 最小 artifact 集合固定为：

- `approval_status_result.json`
- `approval_writeback_result.json`

其中：

- `approval_status_result.json` 表达审批侧证据
- `approval_writeback_result.json` 表达协作侧证据

### 13.2 Job Summary

summary 至少展示：

- `approval_instance_code`
- `approval_status`
- `automation_status`
- `task_id`
- `goal_id`
- `task_writeback_status`
- `goal_writeback_status`
- `decision_summary`

### 13.3 成功语义

workflow 成功条件为：

- 查询成功
- task 回写成功
- goal 回写成功

### 13.4 失败语义

workflow 失败条件包括：

- 查询失败
- task 回写失败
- goal 回写失败

即使失败，也必须：

- 上传 artifacts
- 输出 summary
- 保留已完成步骤的回写 receipt

## 14. 最小失败策略

### 14.1 查询失败

处理方式：

- 直接停止后续回写
- 输出 `approval_status_result` 的失败证据

### 14.2 Task 回写失败

处理方式：

- 停止 goal 回写
- 避免 goal 领先于 task

### 14.3 Goal 回写失败

处理方式：

- 保留已成功的 task 回写结果
- workflow 标记失败
- artifact 必须显式说明“task 已写，goal 未写”

## 15. 适配器边界

### 15.1 Query Adapter

负责：

- 读取审批实例
- 生成标准状态投影

复用：

- `query_real_approval_status.py`
- `feishu_approval_api.py`

### 15.2 Writeback Adapter

负责：

- 任务记录投影与回写
- 目标记录聚合与回写
- receipt 记录

复用：

- `poll_feishu_approval_and_sync_base.py`
- `sync_github_to_feishu.py`
- `build_goal_progress_record.py`

### 15.3 Summary Adapter

负责：

- 汇总审批状态和回写结果
- 渲染 Job Summary
- 给出 workflow exit code

### 15.4 Workflow 本体职责

workflow 本体只负责：

- 读取输入
- 编排 query 与 writeback
- 上传 artifacts
- 输出 summary

不负责承载复杂业务映射逻辑。

## 16. 测试策略

建议固定四层测试：

### 16.1 单元层

验证：

- 状态投影结构
- `approval_status -> automation_status` 映射
- `approval_writeback_result` 结构

### 16.2 脚本层

验证以下三类场景：

- 查询成功且 task/goal 双写成功
- task 写失败
- task 成功但 goal 写失败

### 16.3 Workflow 层

验证：

- workflow 文件存在
- inputs 存在
- artifacts 上传存在
- summary helper 被调用

### 16.4 文档层

验证：

- runbook 已创建
- `RUNBOOK_INDEX.md` 已纳入该入口

## 17. Runbook 与 Operator 路径

本轮新增独立 runbook，例如：

- `docs/feishu-collab/runbooks/approval-polling-writeback.md`

至少覆盖：

- workflow 入口
- 必填 inputs
- artifacts 说明
- 成功/失败判定
- 常见故障排查

并纳入：

- `docs/feishu-collab/RUNBOOK_INDEX.md`

以保证 operator 能清晰区分：

- `real-approval-trigger`
- `approval-polling-writeback`

## 18. 与下一阶段的关系

本轮完成后，第四段“真实知识库构建”将消费本轮产物，例如：

- `approval_status_result.json`
- `approval_writeback_result.json`
- workflow summary

第三段解决的是：

- 系统状态一致

第四段再解决：

- 知识资产沉淀

## 19. 风险与应对

### 19.1 风险：职责重新混回 trigger workflow

应对：

- 保持独立 polling workflow
- 明确禁止把长链轮询回写并回 `real-approval-trigger.yml`

### 19.2 风险：回写局部成功被误判为成功

应对：

- 只要 task 或 goal 任一失败，workflow 即判失败
- 但必须保留局部成功证据

### 19.3 风险：第三段提前卷入第四段

应对：

- spec 和 plan 中明确排除 knowledge materialization
- 第三段只输出 artifact 与 summary，不直接写知识文档

## 20. 验收标准

本设计完成后，应满足以下验收标准：

- 存在正式的 `approval-polling-writeback` workflow 设计
- 能清晰说明与 `real-approval-trigger` 的职责边界
- 能定义统一状态口径与固定回写顺序
- 能定义 artifacts、summary 与成功/失败语义
- 能说明测试策略、runbook 路径与第四段衔接边界
- 能作为下一步实施计划的统一设计基线
