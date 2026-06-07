---
id: 03-WORKFLOWS-AND-NORMS
type: workflow
owner: ledger-protocol-agent
depends:
  - 00-AGENT-CONSTITUTION
  - 01-COLLABORATION-PROTOCOL
  - 02-ARCHITECTURE
version: 4
last_verified: 2026-05-20
---

# Workflows & Norms

> Status: active  
> Default workspace: `7-ARTIFACT-HUB-V2/**`  
> Last updated: 2026-05-20

## 0. 两条协作线

协作系统包含两条互补的线：

- **分解线**（六步协作流）：任务从哪里来、怎么拆到前端模块级别
- **执行线**（Phase 0-8 生命周期）：任务怎么执行、怎么验收、怎么归档

分解线产出协作清单后，每个清单条目进入执行线按 Phase 流转。

## 1. 分解线：六步 UI-Driven 协作流

### Phase A: 技术文档

- Governance AGENT 将用户目标翻译为技术文档
- 必须包含：业务目标、用户需求、非功能约束（性能、安全、合规）
- PR 评论锚点：`[技术文档 / TECHNICAL_SPEC]`

### Phase B: 工程架构图

- 目的驱动架构图，核心展示"前端用户看到什么 → 背后需要什么服务"
- 必须保留数据流向：数据源 → 服务层 → 前端模块（垂直切片）
- 不必陷入实现路径细节，符合传统金融工程实践即可
- PR 评论锚点：`[架构评审 / ARCHITECTURE_REVIEW]`

### Phase C: 前端页面定义

- 定义页面结构、组件层级、交互流程
- 精确到组件级：每个组件的数据来源、触发条件、状态变化
- PR 评论锚点：`[前端页面定义 / FRONTEND_PAGES]`

### Phase D: 模块联动模拟

- 定义模块间契约：数据怎么流、状态怎么变、异常怎么处理
- 每个契约必须包含：上游输出格式、下游输入依赖、异常/降级路径、状态同步机制
- PR 评论锚点：`[模块契约 / MODULE_CONTRACT]`

### Phase D.5: 文档管理 + 任务拆解区块

Phase D 契约确定后，将抽象的契约和页面定义转化为**具象的模块文件夹 + 任务区块结构**。

- **工具**: `SKILLS/task-decompose-blocks/decompose.py` 或 `ledger_sync.py sync --block-output`
- **输入**: Phase C 前端页面定义 + Phase D 模块契约
- **产出**:
  1. 模块文件夹：`{workspace}/modules/{module-name}/`
  2. 任务区块：`{workspace}/modules/{module-name}/tasks/{N}-slug/BLOCK.md`（每个任务一个区块文件，自带 YAML 区块头）
  3. 子工程索引：`{workspace}/modules/{module-name}/INDEX.md`（模块级索引，汇总所有区块状态）
  4. 契约引用：`{workspace}/modules/{module-name}/contracts/phase-d.md`
  5. 总索引更新：`docs/file-registry.json` → `modules` 字段追加新模块引用

**区块头结构**（BLOCK.md 前 10 行）：
```yaml
---
id: 001-quote-fetcher        # 区块唯一 ID
module: market-quote         # 所属模块
block_index: 1               # 区块序号
type: parallel               # parallel | serial | shared-sync
owner: ""                    # 待分配
depends: []                  # 依赖的区块 ID 列表
acceptance_criteria: |       # 从 Phase F 继承
  1. ...
phase_d_contract: ../contracts/phase-d.md
ledger_task_id: ""           # 后续由 ledger_sync 填充
status: ready                # ready | in_progress | completed | blocked
version: 1
created_at: 2026-05-20
---
```

**Agent 开工时的查找路径**：
1. 读 `docs/file-registry.json` → 找到模块索引
2. 读 `modules/xxx/INDEX.md` → 找到任务区块列表
3. 读 `tasks/001-xxx/BLOCK.md` 前 10 行 → 知道 id/type/depends/owner/acceptance_criteria
4. 飞行前记忆查找 → 冲突门禁 → 开工

**挖矿类比**：每个区块自包含、自索引、自验证，工程索引只是指向区块的指针。

### Phase E: 按模块拆解协作清单

- 确认 Phase D.5 生成的模块文件夹结构已就位
- 为每个区块分配 `owner_agent`，标注依赖关系
- 每个条目必须标注：`parallel / serial / shared-sync` 执行类型
- PR 评论锚点：`[协作清单 / COLLAB_CHECKLIST]`

### Phase F: 验收标准

- 为每个区块定义可验证的完成标准，写入 BLOCK.md 的 `acceptance_criteria` 字段
- 验收标准必须：可执行（能跑命令/看页面验证）、可量化（有明确指标）、独立于实现路径
- PR 评论锚点：`[验收标准 / ACCEPTANCE_CRITERIA]`

### 七步流完成后 → 执行线交接

`[验收标准 / ACCEPTANCE_CRITERIA]` 锚点确认（Decision: CONFIRMED）后，Governance AGENT 执行交接：

1. 将协作清单条目写入 `ledger/tasks/index.json`，状态设为 `goal_received`
2. 为每个条目分配 `task_id`，标注 `owner_agent` 和 `validator_agent`
3. 交接信号：清单中每个条目的状态从 `planned` → `ready`，允许被声明
4. 区块结构已就绪：Agent 可直接读取 BLOCK.md 开工

协作清单中的每个条目进入执行线（Phase 0-8），由对应 AGENT 按现有协议推进。

## 2. 执行线：标准 Workflow (PR-Based)

1. Run conflict gate (before editing).
2. Open PR on `agent/<agent_id>/*` branch.
3. Post `DESIGN_REVIEW` (include `Reviewer:`).
4. Post `STARTED` (declare workspace, scope, occupied boundaries).
5. Implement within scope.
6. If scope changes, post `UPDATED` first.
7. If ledger/task status changes, run `ledger_sync.py push-status` and post `LEDGER_SYNC`.
8. Post `TEST_REPORT` with evidence.
9. Post `DONE` with delivery summary.
10. If a task needs acceptance, post `ACCEPTANCE_REQUEST` after the delivery package is ready.
11. Validator posts `VALIDATION_RESULT` with score and decision.
12. Before continuing the next round of work, 先读取最近一次 `VALIDATION_RESULT`.
13. If `REWORK`, `BLOCK`, or `Must-Fix Items` exist, fix them before continuing mainline work.
14. Governance AGENT merges after all gates pass.

### 2.1 V2 串行验收链

1. `context-reader` 读取飞书 `work item` 和可选 `Objective / KR`
2. `protocol-checker` 校验 `ACCEPTANCE_REQUEST` 结构化完整性
3. `acceptance-validator` 形成当前轮次的验收判断
4. `result-synthesizer` 回写唯一正式 `VALIDATION_RESULT`

规则：

- GitHub `VALIDATION_RESULT` 是正式验收真源
- 飞书只允许回写摘要字段，不允许回写正式主结论字段

### 2.2 2026-06-07 真实 E2E 结论

`PR #7` 上已完成一轮真实 `workflow_dispatch` 联调，成功 run 为 `27085309457`，头提交为 `47d9432`。

本轮已真实打通以下链路：

1. `ACCEPTANCE_REQUEST` 解析
2. `acceptance_cycle` 创建 / 加载
3. 飞书开发者应用 / bot 方式 mint `tenant_access_token`
4. 使用 `lark-cli --as bot` 读取真实 Base record
5. 运行串行 4 角色 `acceptance cycle`
6. GitHub 回写正式 `VALIDATION_RESULT`

本轮收口出的运行约束：

- runner 中不得依赖交互式 `user` 登录态
- `lark-cli` 外部凭据模式必须通过环境变量注入
- workflow 需要先调用 `tenant_access_token/internal` 获取 `tenant_access_token`
- 所有会再次读取飞书上下文的步骤都必须继承同一组 bot 环境变量
- `work_item_title` 不得只依赖 `Title` 字段，需兼容真实多维表格中的 `任务` 字段

当前结论：

- GitHub 仍是正式验收真源
- 飞书 bot 已成为 runner 里的稳定上下文读取身份
- `Acceptance Orchestration V2` 已完成一次真实 PR 评论驱动 E2E 闭环验证

## 3. Role-Specific Norms

### 3.1 Ledger/Protocol AGENT

- Only changes:
  - `docs/**`
  - `ledger/**`
  - `docs/superpowers/contracts/**`
- Produces:
  - protocol updates, indices, FAQs, and contracts
  - PRs that remain strictly within the allowed scope

### 3.2 Governance AGENT

- 负责分解线：技术文档 → 架构图 → 前端页面定义 → 协作清单
- Owns: conflict resolution, merge gate compliance, final merge.
- If protocol/docs/ledger needs changes: request Ledger/Protocol AGENT to open a separate PR.

### 3.3 Developer AGENT

- Must not touch shared boundaries without declaration and strong-sync.
- Must not bypass gates by "silent commits"; protocol evidence is part of delivery.
- 在分解线完成后，按协作清单条目执行，每个条目对应一个明确的前端模块交付物。

### 3.4 Validator AGENT

- 负责分解线中的模块契约定义与验收标准制定
- Must publish `VALIDATION_RESULT` (PASS/REWORK/BLOCK + score).
- Must not accept without executable evidence.

## 4. 防漂移机制

AI 协作漂移的根本原因是缺乏明确的收敛锚点。本系统采用三级防漂移机制：

### 4.1 一级：前端页面锚点

每个任务的最终验收标准对应一个明确的前端页面/组件。"页面长什么样"就是收敛锚点，不是抽象的"API 返回 200"。

### 4.2 二级：模块契约约束

模块联动模拟定义了模块间的输入/输出/异常契约。AGENT 开发时必须遵守契约，不可自行扩展接口或改变数据格式。

### 4.3 三级：验收标准前置

在开工前（Phase F），每个清单条目的验收标准已经确定。AGENT 开发过程中始终对照验收标准，而不是开发完了再想"怎么验收"。

## 5. When Blocked: Lookup Table

- Gate failure reason codes: check `05-FAQ.md` then fix by posting missing protocol anchors.
- "Not sure where to edit": check `04-ENGINEERING-INDEX.md`.
- "Protocol conflict / allowed scope dispute": check `00-AGENT-CONSTITUTION.md`.
- "Which template to use": check `01-COLLABORATION-PROTOCOL.md` and `templates/`.
- "任务怎么拆": 回到六步协作流，确认是否已完成前端页面定义和模块契约。
