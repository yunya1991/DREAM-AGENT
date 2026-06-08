---
id: FIVE-SKILL-REHEARSAL-WORKFLOW-DESIGN
type: design
owner: governance-agent
depends:
  - FIVE-SKILL-INTEGRATION-REHEARSAL-DESIGN
  - FEISHU-COLLABORATION-SYSTEM-DESIGN
version: 1
last_verified: 2026-06-08
---

# 五 Skill Rehearsal Workflow 设计

> 仓库：`DREAM-AGENT`
> 日期：`2026-06-08`
> 状态：draft
> 目标：把现有五个 skill 的本地 rehearsal runner 正式接入 `.github/workflows`，形成一个可手动触发、可上传 artifacts、可渲染 Job Summary、并以系统状态驱动 workflow 成败的真实 workflow 级系统演练入口。

## 1. 背景

当前仓库已经具备一条可本地运行的五 skill 系统演练链路：

- `github-actions/run_five_skill_integration_rehearsal.py` 已可运行核心场景
- `github-actions/feishu_collab/integration/` 已具备 scenario loader、chain orchestrator、reporter
- 本地 dry-run 已可输出：
  - `scenario_manifest`
  - `step_results`
  - `breakpoints`
  - `system_status`
  - `handoff`
  - `knowledge_update`
- `docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md` 已给出 operator 级运行手册

但它仍然主要停留在“本地 runner 可执行”的阶段，还没有真正进入仓库的 workflow 层。

这意味着：

- 还没有 GitHub Actions 级系统演练入口
- 还没有 workflow 级 summary 呈现
- 还没有 artifact 化的系统报告
- 还没有把系统状态转换成 workflow 成败语义

因此，本轮要把 rehearsal 从“本地系统级演练”升级为“workflow 级系统演练”。

## 2. 问题定义

本设计主要解决以下四类问题：

### 2.1 缺少真实 workflow 入口

当前虽然已有：

- `collab-acceptance-agent.yml`
- approval smoke 路径
- 五 skill 本地 rehearsal runner

但没有一个专门承载五 skill 系统演练的 workflow 入口。

### 2.2 结果只存在于本地 JSON，不利于 GitHub 侧消费

本地 runner 已输出完整 JSON，但在 GitHub Actions 语境里，operator 往往先看：

- Job Summary
- workflow 通过/失败
- artifacts

如果不把这三层接起来，系统演练仍然偏工程内部使用，而不是仓库协作入口。

### 2.3 workflow 成败语义还未绑定系统状态

当前 `system_status` 已定义：

- `pass`
- `warn`
- `fail`
- `blocked`

但 workflow 还没有明确规则说明：

- 哪些状态视为 job success
- 哪些状态视为 job failure
- 失败时 artifacts 是否必须保留

### 2.4 现有 acceptance workflow 不适合直接承载 v1

`collab-acceptance-agent.yml` 已经承担：

- acceptance 请求解析
- PR 场景处理
- Lark token
- lark context
- acceptance cycle
- approval smoke

如果直接把五 skill rehearsal 硬塞进去，会让既有 workflow 进一步变重，也会放大回归风险。

## 3. 设计目标

本设计的目标如下：

- 新增一个独立的五 skill rehearsal workflow
- 只支持 `workflow_dispatch` 作为 v1 触发方式
- 复用现有 Python runner，而不是在 YAML 内重写级联逻辑
- 将演练结果同时输出到 JSON artifact 和 GitHub Job Summary
- 明确 `system_status` 到 workflow 成败的映射
- 与现有 `collab-acceptance-agent` 并行共存，不相互依赖

成功标准：

- `.github/workflows` 中存在正式的 rehearsal workflow 文件
- workflow 能通过手动触发运行五 skill 演练
- workflow 能上传完整 JSON 报告 artifact
- workflow 能在 Job Summary 中渲染系统级概览
- workflow 能依据 `system_status` 给出一致的 success/failure 结果

## 4. 范围与非目标

### 4.1 本设计覆盖

- 独立 rehearsal workflow
- `workflow_dispatch` 触发
- Python runner 的 workflow 接入
- JSON artifact 输出
- Job Summary 渲染
- `system_status` 到 workflow 成败语义映射
- 基础 workflow 契约测试

### 4.2 本设计不覆盖

- 定时巡检触发
- PR comment 自动触发
- Lark 回写
- 与 `collab-acceptance-agent` 的联动编排
- 多 scenario 选择矩阵

本轮优先把 workflow 级入口和结果语义做稳，不追求一次性并入更重的协作流。

## 5. 核心原则

### 5.1 薄工作流

workflow 只负责：

- checkout
- 运行 Python runner
- 生成 summary
- 上传 artifacts
- 按系统状态决定退出语义

不在 YAML 内重写五 skill 的编排逻辑。

### 5.2 Python runner 仍是编排真源

五 skill 的系统级级联、状态归一、断点收集仍由现有 Python integration 层负责。workflow 只是承载壳，而不是第二套编排引擎。

### 5.3 证据优先于表面成败

即使 workflow 最终失败，也必须尽量保留：

- JSON 报告
- Job Summary
- 断点和恢复提示

不能因为失败而丢失证据。

### 5.4 并行接入，不扰动 acceptance 主线

v1 与 `collab-acceptance-agent` 平行存在，避免在本轮扩大 acceptance 回归面。

## 6. 推荐方案

推荐采用：

- `独立 workflow + 薄工作流方案`

原因：

- 与现有 acceptance workflow 边界最清晰
- 能最大限度复用已完成的 Python runner
- YAML 复杂度最低
- 后续若要加 cron、PR comment 或 acceptance 转发，也有稳定独立入口可扩展

不推荐：

- 直接扩展 `collab-acceptance-agent.yml`
- 在 YAML 内重写状态汇总和 summary 逻辑
- 先做 workflow 与 Lark 双向联动

## 7. 总体架构

### 7.1 新增 workflow

新增独立 workflow，例如：

- `.github/workflows/five-skill-rehearsal.yml`

职责：

- 提供 `workflow_dispatch`
- 运行现有 rehearsal runner
- 调用一个很小的 summary/render helper
- 上传 artifacts
- 根据系统状态决定 workflow success/failure

### 7.2 新增最小 workflow helper

新增一个 workflow 专用的轻量 helper，用于：

- 读取 runner 输出 JSON
- 生成 `GITHUB_STEP_SUMMARY`
- 生成 workflow exit code

注意：

- 该 helper 只做工作流出口转换
- 不承载五 skill 级联逻辑

### 7.3 数据流

workflow 级数据流如下：

1. `workflow_dispatch`
2. checkout 仓库
3. 执行 `run_five_skill_integration_rehearsal.py`
4. 将 JSON 结果写入工作目录
5. helper 读取 JSON 并渲染 Job Summary
6. 上传 JSON 报告为 artifact
7. helper 按 `system_status` 决定最终退出码

## 8. 结果模型

### 8.1 Artifact

workflow 至少上传一个 JSON artifact，例如：

- `five-skill-rehearsal-report.json`

内容直接来自 Python runner 输出。

### 8.2 Job Summary

Job Summary 至少展示：

- `scenario_id`
- `system_status`
- `step_count`
- `step_order`
- `breakpoint_count`
- 每一步的 `raw_status -> system_status`

若存在断点，还需展示：

- `breakpoint_type`
- `recovery_hint`

### 8.3 Workflow 退出语义

统一规则如下：

- `pass` -> workflow success
- `warn` -> workflow failure
- `fail` -> workflow failure
- `blocked` -> workflow failure

这样定义的原因是：

- workflow 级系统演练以“健康基线”作为目标
- 只要不是 `pass`，都意味着需要人工介入或继续修复

## 9. 与现有 workflow 的关系

### 9.1 与 `collab-acceptance-agent` 并行

本轮不把 rehearsal 接入：

- acceptance job
- approval-smoke job
- PR comment 流

只保持并行存在。

### 9.2 后续扩展预留

后续若需要：

- acceptance workflow 内转发调用 rehearsal
- PR comment 触发 rehearsal
- 定时巡检

都基于本轮新增的独立 workflow 扩展，而不是重来。

## 10. 测试策略

本轮至少包含以下三类测试：

### 10.1 workflow 存在性测试

锁定：

- rehearsal workflow 文件存在
- 触发方式为 `workflow_dispatch`
- 关键 step 存在

### 10.2 summary/render helper 测试

锁定：

- JSON 报告能转换为 summary 文本
- `system_status` 能转换为正确退出码
- `warn/fail/blocked` 时仍保留 artifact 所需输出

### 10.3 workflow 入口契约测试

锁定：

- workflow 调用的 runner 路径正确
- 默认场景为 `core-objective-baseline`
- 上传 artifact 的文件名和位置稳定

## 11. 风险与应对

### 11.1 风险：workflow 与 Python runner 出现双重真源

应对：

- 把 workflow 逻辑压到最薄
- 只允许 helper 做出口转换，不允许 workflow 内重写编排逻辑

### 11.2 风险：workflow 失败时丢失证据

应对：

- artifact 上传步骤使用 `if: always()`
- summary 渲染在失败前执行

### 11.3 风险：未来扩展时再次侵入 acceptance workflow

应对：

- 先建立独立入口
- 后续若需联动，优先做“转发/调用”，而不是把逻辑搬进 acceptance workflow

## 12. 验收标准

本设计完成后，应满足以下验收标准：

- 存在正式的五 skill rehearsal workflow 文件
- 该 workflow 能通过 `workflow_dispatch` 触发
- 该 workflow 能执行现有五 skill rehearsal runner
- 该 workflow 能输出 JSON artifact 和 Job Summary
- 该 workflow 能按 `system_status` 转换 workflow success/failure
- 相关 workflow 契约测试通过
