---
id: REAL-APPROVAL-TRIGGER-DESIGN
type: design
owner: governance-agent
depends:
  - APPROVAL-SKILL-DESIGN
  - FIVE-SKILL-REHEARSAL-SCENARIO-SELECTION-DESIGN
  - FEISHU-COLLABORATION-SYSTEM-DESIGN
version: 1
last_verified: 2026-06-08
---

# 真实审批触发设计

> 仓库：`DREAM-AGENT`
> 日期：`2026-06-08`
> 状态：draft
> 目标：新增一条独立的真实审批触发 workflow，把现有审批能力从“脚本能力 + smoke 片段”升级为“可真实发起实例并查询状态的主线入口”，同时统一到 Python 脚本主线，避免继续保留 workflow 内联 HTTP 的双实现。

## 1. 背景

当前仓库已经具备若干审批相关能力：

- `feishu_approval_api.py` 已封装真实审批 REST 调用
- `run_goal_progress_approval_cycle.py` 已具备风险门控、审批实例创建、状态查询与结果投影能力
- `collab-acceptance-agent.yml` 已包含 `approval-smoke` 片段，可直接打到真实飞书审批 API
- rehearsal 主线和 scenario 治理层已经建好，但仍是“系统演练层”，不承载真实审批副作用

这些能力说明审批并不是“从零开始”，而是已经存在三个相互分离的入口：

- API 包装入口
- 脚本编排入口
- workflow smoke 入口

当前真正缺少的是：

- 一条明确的、可重复执行的、主线级的真实审批触发入口

## 2. 问题定义

本设计主要解决以下四类问题：

### 2.1 存在双实现

当前 workflow 侧真实审批 smoke 直接在 YAML 中内联 HTTP 请求，而脚本侧已经有：

- `feishu_approval_api.py`
- `run_goal_progress_approval_cycle.py`

这会带来：

- 逻辑重复
- 口径分裂
- 后续维护成本增加

### 2.2 缺少主线级真实入口

当前真实审批存在，但更像 smoke 验证，不像主线工作流：

- 没有独立 workflow
- 没有标准 artifact
- 没有稳定 Job Summary
- 没有统一成功/失败语义

### 2.3 当前闭环过重，不适合一步做到位

如果本轮直接把以下内容全部接入：

- 真实发起
- 轮询
- Base 回写
- 知识沉淀

那会同时引入多条真实副作用链，风险过高。

### 2.4 下一阶段扩展需要一条稳定真源

后续还会进入：

- 审批轮询回写
- 知识库沉淀

如果本轮不先把“真实发起 + 查询”收口为主线入口，后续只会继续沿着零散入口叠功能。

## 3. 设计目标

本设计的目标如下：

- 新增独立的真实审批触发 workflow
- 把 workflow 侧审批发起统一到 Python 脚本主线
- v1 只做：
  - 真实发起
  - 真实查询
- 输出标准 artifact 与 Job Summary
- 明确 workflow 成功/失败语义
- 为下一阶段“轮询回写”和“知识沉淀”保留扩展位

成功标准：

- 存在正式的真实审批 workflow 文件
- workflow 能真实创建审批实例
- workflow 能查询创建后的实例状态
- workflow 能输出实例码、审批状态、automation 状态与 decision summary
- workflow 失败时仍保留 artifact 与 summary

## 4. 范围与非目标

### 4.1 本设计覆盖

- 独立真实审批 workflow
- 真实审批实例创建
- 真实实例状态查询
- 标准 artifact
- Job Summary
- 统一成功/失败语义
- dispatcher/query 契约测试

### 4.2 本设计不覆盖

- 周期性轮询
- Base 回写
- knowledge materialization
- acceptance workflow 联动
- rehearsal scenario 中直接执行真实审批

本轮先把“真实审批触发主线”独立做稳，而不是把整个治理闭环一次做满。

## 5. 核心原则

### 5.1 统一脚本主线

workflow 不再直接内联 HTTP 请求创建审批实例，而应统一走：

- `feishu_approval_api.py`
- `run_goal_progress_approval_cycle.py`

这样 workflow 只是入口壳，Python 脚本才是审批主线真源。

### 5.2 证据优先失败

即使 workflow 最终失败，也必须尽量保留：

- 审批请求体快照
- 创建响应
- 查询响应
- Job Summary

### 5.3 先发起与查询，后轮询与回写

v1 只打通：

- 发起
- 单次查询

轮询和回写放到下一阶段。

### 5.4 与 rehearsal / acceptance 并行

本轮不把真实审批直接塞进：

- `five-skill-rehearsal.yml`
- `collab-acceptance-agent.yml`

先保持独立入口。

## 6. 推荐方案

推荐采用：

- `独立 approval workflow + 统一脚本主线`

原因：

- 能先消灭 workflow 内联 HTTP 与脚本逻辑并存的问题
- 能在不扰动 acceptance 与 rehearsal 的前提下建立稳定主线
- 能为后续轮询回写提供明确的扩展起点

不推荐：

- 继续沿用 workflow 内联 HTTP
- 直接把真实审批接进 rehearsal workflow
- 直接把真实审批塞回 acceptance workflow 主入口

## 7. 总体架构

### 7.1 新增独立 workflow

新增独立 workflow，例如：

- `.github/workflows/real-approval-trigger.yml`

职责：

- 接收审批发起必需输入
- 调用 Python dispatcher
- 调用 query 脚本
- 输出 artifact
- 渲染 Job Summary

### 7.2 新增 dispatcher 层

新增一个很小的 workflow 侧 dispatcher 包装，例如：

- `github-actions/run_real_approval_dispatch.py`

职责：

- 读取 workflow 输入
- 调用现有 `run_goal_progress_approval_cycle.py`
- 输出创建后的关键字段与原始响应

注意：

- 它不重写审批逻辑
- 它只是 workflow 与现有脚本主线之间的适配层

### 7.3 新增 query 层

新增一个很小的查询包装，例如：

- `github-actions/query_real_approval_status.py`

职责：

- 读取 `instance_code`
- 调用 `feishu_approval_api.get_instance()`
- 输出标准状态摘要

### 7.4 新增 workflow summary 层

新增一个 approval workflow 专用 summary helper，例如：

- `github-actions/render_real_approval_summary.py`

职责：

- 汇总：
  - `approval_instance_code`
  - `approval_status`
  - `automation_status`
  - `decision_summary`
- 渲染 Job Summary
- 决定 workflow exit code

## 8. 数据流

真实审批 workflow 的数据流如下：

1. operator 通过 `workflow_dispatch` 提供审批输入
2. workflow mint tenant token
3. workflow 调用 dispatcher
4. dispatcher 调用现有审批主线脚本，创建真实实例
5. workflow 调用 query 脚本查询最新状态
6. workflow 生成 artifact 与 Job Summary
7. summary helper 依据结果决定 workflow success/failure

## 9. 输入模型

v1 至少需要以下输入：

- `approval_code`
- `applicant_open_id`
- `task_payload`
- `goal_payload`

可选输入：

- `sibling_tasks`
- `approval_due_at`
- `timeout_fallback`

这些输入应先归一到一个明确的 `approval_request_profile`，再进入 dispatcher。

## 10. 结果模型

### 10.1 Artifact

workflow 至少输出：

- `approval_dispatch_result.json`
- `approval_status_result.json`

必要时也可补：

- `approval_request_body.json`

### 10.2 Job Summary

至少展示：

- `approval_code`
- `approval_instance_code`
- `approval_status`
- `automation_status`
- `decision_summary`
- `task_id`
- `goal_id`

### 10.3 Workflow 成功语义

v1 的 workflow success 条件为：

- 真实实例创建成功
- 查询返回有效审批状态

其余情况统一视为 failure，但保留 artifact 和 summary。

## 11. 测试策略

本轮至少包含以下三类测试：

### 11.1 workflow 输入与存在性测试

锁定：

- workflow 文件存在
- 必要输入存在
- workflow 调用了 dispatcher 与 query

### 11.2 dispatcher/query 契约测试

锁定：

- 真实审批发起请求体的字段口径
- `open_id` 与 JSON-string `form` 约束
- 查询结果的标准状态摘要

### 11.3 summary/result 契约测试

锁定：

- summary 含关键审批字段
- 成功/失败退出语义一致
- 失败时 artifacts 仍上传

## 12. 风险与应对

### 12.1 风险：workflow 与脚本再次形成双真源

应对：

- workflow 只调用包装脚本
- 真实审批逻辑只保留在 Python 主线

### 12.2 风险：真实调用失败后证据丢失

应对：

- artifacts 上传使用 `if: always()`
- summary 渲染在最终退出前执行

### 12.3 风险：本轮范围被拖入轮询回写

应对：

- spec 和 plan 明确把轮询回写放到下一阶段
- 本轮只查询一次，不引入周期性等待

## 13. 与下一阶段的关系

本轮完成后，下一阶段将继续纳入：

- 审批轮询回写
- 知识沉淀

但这两项都应建立在本轮新增的“真实审批触发主线”之上，而不是继续从 smoke 或 rehearsal 入口扩写。

## 14. 验收标准

本设计完成后，应满足以下验收标准：

- 存在正式的真实审批 workflow 文件
- workflow 能真实创建审批实例
- workflow 能查询实例状态
- workflow 能输出 artifact 与 Job Summary
- workflow 失败时仍保留证据
- 相关 workflow / dispatcher / summary 契约测试通过
