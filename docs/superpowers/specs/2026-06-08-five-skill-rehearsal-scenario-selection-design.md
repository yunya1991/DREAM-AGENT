---
id: FIVE-SKILL-REHEARSAL-SCENARIO-SELECTION-DESIGN
type: design
owner: governance-agent
depends:
  - FIVE-SKILL-REHEARSAL-WORKFLOW-DESIGN
  - FIVE-SKILL-INTEGRATION-REHEARSAL-DESIGN
version: 1
last_verified: 2026-06-08
---

# 五 Skill Rehearsal Scenario 选择设计

> 仓库：`DREAM-AGENT`
> 日期：`2026-06-08`
> 状态：draft
> 目标：为现有五 skill rehearsal workflow 增加受治理的 scenario 选择能力，使 workflow 和 runner 不再绑定单一默认 manifest，而是统一通过集中 registry 解析 `scenario_id` 并加载对应场景。

## 1. 背景

当前仓库已经具备：

- 独立 workflow：`.github/workflows/five-skill-rehearsal.yml`
- 顶层 runner：`github-actions/run_five_skill_integration_rehearsal.py`
- scenario loader：`github-actions/feishu_collab/integration/scenario_loader.py`
- integration fixture：`github-actions/tests/fixtures/integration/core_objective_baseline.json`

这条链路已经能跑通一个固定场景：

- `core-objective-baseline`

但目前场景选择能力仍然停留在“代码里写死默认 manifest”的状态：

- workflow 不接收场景参数
- runner 不接收受治理的 `scenario_id`
- loader 不理解场景注册表
- manifest 虽然存在 `skill_sequence`，但没有一个统一的场景真源对外暴露

这意味着现阶段的五 skill rehearsal 虽然可用，但还不能稳定扩展为“多场景系统演练入口”。

## 2. 问题定义

本设计主要解决以下四类问题：

### 2.1 场景真源分散

当前场景信息同时分布在：

- runner 的默认路径
- fixture 文件名
- workflow 内部命令

没有一个统一的 registry 作为场景真源。

### 2.2 workflow 无法选择场景

当前 workflow 只有：

- `workflow_dispatch`

但没有：

- `scenario_id` 输入

因此 operator 只能运行默认 baseline，无法显式选择不同系统演练场景。

### 2.3 runner 与 fixture 强耦合

当前 runner 直接依赖：

- `core_objective_baseline.json`

这会导致未来新增场景时，要同时改：

- workflow
- runner
- 文档

扩展成本高，且容易让场景定义失控。

### 2.4 下一阶段主线缺少治理基座

下一阶段要逐步纳入：

- 真实审批触发

如果在此之前没有统一的场景治理层，那么后续真实审批相关演练场景会继续散落在脚本、fixture 和 workflow 中，难以维护。

## 3. 设计目标

本设计的目标如下：

- 新增一个集中式 `scenario registry`
- 让 workflow 通过 `scenario_id` 选择场景
- 让 runner 先解析 registry，再加载 manifest
- 保留 `core-objective-baseline` 作为默认预注册场景
- 让未知 `scenario_id` 返回清晰错误并导致 workflow 失败
- 为下一阶段“真实审批触发”接入提供统一场景治理基座

成功标准：

- 仓库中存在正式的 `scenario registry`
- workflow 支持 `scenario_id` 输入
- runner 不再硬编码默认 manifest 路径
- `core-objective-baseline` 能继续无缝运行
- 未知 `scenario_id` 能输出明确错误并失败退出

## 4. 范围与非目标

### 4.1 本设计覆盖

- 预注册场景选择
- 集中 registry 文件
- `scenario_id -> manifest path` 解析
- workflow 输入扩展
- runner 参数扩展
- registry / runner / workflow 契约测试

### 4.2 本设计不覆盖

- 任意自定义 `scenario_path`
- 目录自动扫描发现
- 多 scenario 并发运行
- acceptance workflow 联动
- 真实审批触发本身

本轮先解决“怎么治理和选择场景”，不直接解决“场景里执行什么真实副作用”。

## 5. 核心原则

### 5.1 registry 是场景唯一真源

workflow、runner、fixture、文档都不再各自维护一套场景入口信息，统一从 registry 读取。

### 5.2 预注册优先于开放输入

v1 只接受已注册 `scenario_id`，不开放任意路径输入，以减少：

- 路径错误
- 结构漂移
- 治理失控

### 5.3 场景治理独立于业务主链

本轮只增加“如何选场景”的治理层，不改动五 skill 本身的领域逻辑。

### 5.4 为下一阶段保留扩展位

“真实审批触发”将在下一阶段纳入主线，但它应直接复用本轮新增的场景治理能力，而不是另起一套输入体系。

## 6. 推荐方案

推荐采用：

- `集中 registry 文件 + scenario_id 输入`

原因：

- 比目录扫描更适合治理、审计和显式注册
- 比 workflow 硬编码选项更容易扩展
- 能保证 workflow、runner、fixture 共用同一场景真源

不推荐：

- 直接支持 `scenario_path`
- 目录扫描自动发现
- 在 YAML 里写死多个场景分支

## 7. 总体架构

### 7.1 新增 registry 文件

新增集中式 registry，例如：

- `github-actions/tests/fixtures/integration/scenario_registry.json`

至少包含：

- `scenario_id`
- `manifest_path`
- `description`
- `status`

### 7.2 新增 registry 解析层

新增一个轻量解析模块，例如：

- `github-actions/feishu_collab/integration/scenario_registry.py`

职责：

- 读取 registry
- 校验 `scenario_id`
- 返回目标 manifest 路径

注意：

- 它只负责场景解析
- 不负责读取具体 skill 输入

### 7.3 扩展 runner

`run_five_skill_integration_rehearsal.py` 扩展为：

- 接收 `scenario_id`
- 调用 registry 解析目标 manifest
- 再调用现有 loader / orchestrator / reporter

这一步之后，runner 不再直接硬编码 `core_objective_baseline.json`。

### 7.4 扩展 workflow

`.github/workflows/five-skill-rehearsal.yml` 扩展为：

- `workflow_dispatch.inputs.scenario_id`
- 将 `scenario_id` 传给 runner

workflow 本身仍然保持薄，不解析 registry。

## 8. 数据流

场景选择的数据流如下：

1. operator 在 `workflow_dispatch` 中提供 `scenario_id`
2. workflow 把 `scenario_id` 传给 runner
3. runner 调用 registry 解析层
4. registry 返回 manifest 路径
5. loader 读取 manifest 并组装输入
6. orchestrator 执行五 skill 链路
7. reporter 输出最终报告

## 9. 错误语义

### 9.1 未知场景

若 `scenario_id` 未注册：

- runner 输出明确错误信息
- workflow 失败退出
- 不尝试 fallback 到任意默认路径

### 9.2 保留默认基线

v1 必须继续保留：

- `core-objective-baseline`

作为预注册且可用的默认系统演练场景。

## 10. 测试策略

本轮至少包含以下三类测试：

### 10.1 registry 解析测试

锁定：

- 已知 `scenario_id` 能解析到正确 manifest
- 未知 `scenario_id` 抛出明确错误

### 10.2 runner 参数契约测试

锁定：

- runner 可接收 `scenario_id`
- 默认场景仍是 `core-objective-baseline`
- 报告中的 `scenario_manifest` 与输入场景一致

### 10.3 workflow 输入契约测试

锁定：

- workflow 存在 `scenario_id` 输入
- workflow 会把 `scenario_id` 传递给 runner
- workflow 不直接硬编码多个 manifest 路径

## 11. 风险与应对

### 11.1 风险：registry 与 runner 再次双重维护

应对：

- 移除 runner 中对具体 manifest 文件的硬编码依赖
- 所有场景都通过 registry 解析

### 11.2 风险：新增场景后文档不同步

应对：

- runbook 统一引用 `scenario_id`
- 文档只解释如何选场景，不解释具体硬编码路径

### 11.3 风险：下一阶段真实审批又绕开场景治理

应对：

- 在下一阶段设计里把审批相关演练场景直接建在本轮 registry 之上
- 不再另起独立输入体系

## 12. 与下一阶段的关系

本轮完成后，下一阶段将进入：

- `真实审批触发`

但该阶段应直接复用本轮新增能力：

- `scenario_id`
- `scenario registry`
- workflow 输入口径

这样后续审批场景可以以“受治理场景”而不是“零散脚本入口”的方式进入主线。

## 13. 验收标准

本设计完成后，应满足以下验收标准：

- 存在正式的 `scenario registry`
- workflow 支持 `scenario_id`
- runner 通过 registry 选择场景
- `core-objective-baseline` 仍可运行
- 未知 `scenario_id` 会明确失败
- 相关 registry / runner / workflow 契约测试通过
