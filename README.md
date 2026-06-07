---
id: README
type: entry
owner: ledger-protocol-agent
depends:
  - 00-AGENT-CONSTITUTION
  - 01-COLLABORATION-PROTOCOL
  - 02-ARCHITECTURE
version: 2
last_verified: 2026-05-20
---

# AGENT 协作工具

本目录存放 AGENT 协作所用的共同工具与规范（兼容双 AGENT 场景）。

## 目录结构

```

└── SKILLS/
    └── dual-agent-conflict-gate/   ← 冲突前置门禁 SKILL
        ├── SKILL.md                ← SKILL 规范文档
        ├── gatekeeper_config.json  ← 主责域 / 共享文件 / 契约配置
        └── conflict_gate.py        ← Python 实现（CLI 可直接调用）
```

## 生命周期工具栈

标准研发协作体系采用“1 个主流程 SKILL + 4 个子 SKILL + 1 个开工前门禁”的结构：

- `agent-standard-dev-lifecycle`：总控主流程，编排阶段流转
- `agent-design-review`：方案评审
- `agent-dev-execution`：开发执行
- `agent-quality-test`：测试验证
- `agent-collab-supervisor`：流程监督与 GitHub 规则映射
- `dual-agent-conflict-gate`：开工前技术门禁

## 协作流程

协作系统包含两条线：

### 分解线（UI-Driven，六步）

任务拆解与定义阶段，确保每个 AGENT 的交付物对应明确的前端模块：

1. `技术文档` — 业务目标、用户需求、非功能约束
2. `工程架构图` — 目的驱动 + 数据流向（垂直切片）
3. `前端页面定义` — 精确到组件级
4. `模块联动模拟` — 定义模块间契约
5. `协作清单拆解` — 按模块分配任务
6. `验收标准` — 每个清单条目附带可验证标准

### 执行线（Phase 0-8）

分解线完成后，每个协作清单条目进入标准生命周期：

1. `Phase 0` 任务登记
2. `Phase 1` 方案评审
3. `Phase 2` 实施计划
4. `Phase 3` 开工门禁
5. `Phase 4` 开发执行
6. `Phase 5` 测试验证
7. `Phase 6` PR 评审
8. `Phase 7` 合入监督
9. `Phase 8` 完成归档

## 主干文档

以下文档已作为全局 `AGENT` 协作主干迁入 `docs/`：

- `docs/README.md`：协作文档总入口
- `docs/00-AGENT-CONSTITUTION.md`：协作宪法（fail-closed）
- `docs/01-COLLABORATION-PROTOCOL.md`：协作协议（评论锚点 + 门禁）
- `docs/02-ARCHITECTURE.md`：系统架构（含 UI-Driven 分解流）
- `docs/03-WORKFLOWS-AND-NORMS.md`：工作流与规范（含防漂移机制）
- `docs/04-ENGINEERING-INDEX.md`：工程索引（改哪里/查哪里）
- `docs/05-FAQ.md`：FAQ（常见阻塞与修复）
- `docs/06-SKILLS-INVENTORY.md`：SKILL 工具清单
- `memory/README.md`：记忆与学习系统（五层记忆 + 回溯引擎 + 进化循环）
- `docs/dual-agent-collaboration-foundation-design.md`：双代理协作底座设计
- `docs/agent-standard-dev-lifecycle-design.md`：标准开发生命周期与协作监督体系设计
- `docs/agent-standard-dev-lifecycle-implementation-plan.md`：标准开发生命周期实施计划
- `docs/agent-efficient-collaboration-mode.md`：高效协作模式与默认执行策略
- `docs/agent-collaboration-system-v1-design.md`：AGENT协作系统 v1 设计
- `docs/agent-collaboration-system-v1-implementation-plan.md`：AGENT协作系统 v1 实施计划
- `docs/agent-collaboration-system-v1-governance-agent-implementation-plan.md`：治理 AGENT 增量实施计划
- [docs/agent-collaboration-system-v1-governance-cycle-implementation-plan.md](docs/agent-collaboration-system-v1-governance-cycle-implementation-plan.md)：治理账本最小闭环控制器实施计划
- `docs/superpowers/specs/2026-06-07-dream-agent-hybrid-unit-dispatch-design.md`：混合单元编排、飞书一级正式能力、回滚模型
- `docs/superpowers/plans/2026-06-07-dream-agent-hybrid-unit-dispatch-implementation.md`：对应实施计划

原 `docs/superpowers/` 下的对应文档当前保留兼容壳，用于承接历史链接与旧 PR 讨论。

## 高效协作模式

当前协作体系采用“生命周期强门禁 + 默认并行执行”的组合策略：

- 生命周期阶段仍然保留，用于方案评审、测试验证、PR 评审与合入监督
- 默认执行策略切换为“owner 目录内并行开发”，不再要求为每个微小动作逐步等待
- 对错误导出、伪测试、导入路径、局部类型与构建依赖这类确定性问题，允许白名单直接接管
- 只有在共享文件、冻结契约、边界变更、主分支合并等关键节点才强制同步

详细规则见：`docs/agent-efficient-collaboration-mode.md`

## 角色拆分（账本协议 / 治理）

为降低冲突处置与协议维护互相干扰，协作角色拆分为：

- 账本协议AGENT：维护任务清单与协议文档（不负责合并与冲突）
- 治理AGENT：负责合并门禁与冲突收口（不维护任务清单与协议字段）

详见：`docs/agent-ledger-protocol-vs-governance-short-spec.md`

## 使用规则

1. **先走分解线，再进执行线**：六步协作流完成后，协作清单条目才可进入 Phase 0-8
2. **不可跳步**：技术文档 → 架构图 → 前端页面 → 模块契约 → 协作清单 → 验收标准，每步必须留下结构化评论锚点
3. **每次任务开始前**，参与任务的 AGENT 必须运行冲突门禁检查
4. 输出 `BLOCK` 时任务**必须暂停**，不得绕过
5. 门禁结果为 `SAFE` 或 `WARNING` 后，必须先在当前协作 PR 发 `STARTED` 评论，再开始修改文件
6. `STARTED / UPDATED / BLOCKED / DONE` 仍为强制广播层，但默认按阶段广播，不要求为每个微小动作单独评论
7. `gatekeeper_config.json` 是协作共同维护的边界协议，变更需经相关 owner 确认
8. 当前协作以 `7-ARTIFACT-HUB-V2` 为核心工作区，默认占用范围为 `7-ARTIFACT-HUB-V2/**`，每个 AGENT 自建 `agent/*` 分支并提独立 PR
9. 允许少量例外文件用于支撑 `7-ARTIFACT-HUB-V2` 的 build/test/运行，但必须在 `STARTED/UPDATED` 显式声明例外范围
10. owner 目录内默认并行开发；白名单直接接管项允许修复方直接接手，修后广播结果
11. 角色拆分与硬约束以主干短规范为准：`docs/agent-ledger-protocol-vs-governance-short-spec.md`
10. 遇到阻塞先查文档再行动（作为 AGENT 记忆固定引用）：
    - 允许/禁止/裁决：`docs/00-AGENT-CONSTITUTION.md`
    - 评论字段/模板/门禁：`docs/01-COLLABORATION-PROTOCOL.md`
    - 改哪里/查哪里：`docs/04-ENGINEERING-INDEX.md`
    - 常见失败：`docs/05-FAQ.md`
    - SKILL 使用：`docs/06-SKILLS-INVENTORY.md`

## 快速使用

```bash
python3 SKILLS/dual-agent-conflict-gate/conflict_gate.py \
  --agent <agent_id> \
  --task "你的任务名称" \
  --files "计划修改的文件,逗号分隔" \
  --contracts "依赖的契约名"
```

## PR 评论协作模板

### STARTED

```md
[协作开工声明 / STARTED]

Agent: <agent_id>
任务: <任务名称>
分支: <agent/* 分支>
计划修改:
- <文件或目录 1>
- <文件或目录 2>

预期产出:
- <产出 1>
- <产出 2>

占用范围:
- <当前请勿并行修改的文件或目录>

冲突门禁结果:
- decision: SAFE | WARNING
- reason_codes: <如无可写 []>

状态: STARTED
说明: 在我发 DONE 评论前，请不要并行修改上述范围。
```

### DONE

```md
[协作完成回报 / DONE]

Agent: <agent_id>
任务: <任务名称>
提交: <commit sha>
已完成:
- <完成项 1>
- <完成项 2>
状态: DONE
说明: 另一代理可以基于最新 PR head 继续。
```
