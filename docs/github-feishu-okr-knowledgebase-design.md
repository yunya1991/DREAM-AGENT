---
id: GITHUB-FEISHU-OKR-KNOWLEDGEBASE-DESIGN
type: design
owner: ledger-protocol-agent
depends:
  - ACCEPTANCE-ORCHESTRATION-V2-DESIGN
  - 03-WORKFLOWS-AND-NORMS
  - 06-SKILLS-INVENTORY
version: 1
last_verified: 2026-06-07
---

# GitHub x 飞书 OKR 打通与知识库建设设计

> 仓库：`DREAM-AGENT`
> 日期：2026-06-07
> 状态：v1 候选稿
> 目标：在已打通 GitHub x 飞书 Base bot E2E 的基础上，补齐 OKR 真链路，并建立可持续运营的知识库与技能演进机制。

## 0. 背景

当前仓库已经完成以下关键能力：

- 飞书开发者应用 / bot 已创建并接入 GitHub Actions；
- `tenant_access_token` 已能在 runner 中稳定 mint；
- `lark-cli --as bot` 已能读取真实 Base record；
- `ACCEPTANCE_REQUEST -> acceptance_cycle -> VALIDATION_RESULT` 已完成真实 E2E 闭环；
- `github-feishu-bot-bootstrap` 技能已沉淀出首版 bot 搭建与联调流程。

但仍存在两个结构性空缺：

1. `OKR` 相关能力虽然已有代码接线与测试模型，但尚未形成“真实权限 + 真实对象 + 真实 E2E”闭环；
2. 当前沉淀以仓库文档和 PR 评论为主，缺少一个可持续运营、便于复用、便于非开发角色参与的知识库层。

此外，随着后续 GitHub 与飞书协作链路增加，不会只停留在当前一个 bot。技能如果不演进，最终会退化成一次性的操作记录，而不是真正可复用的工程能力。

## 1. 设计目标

本设计聚焦三个目标：

1. 将 `OKR` 上下文从“代码已接线”提升到“真实可验证”；
2. 建立 GitHub 与飞书双层知识库结构，支撑长期运营；
3. 将 `github-feishu-bot-bootstrap` 定义为可持续补全的演进型技能，而不是一次性技能。

## 2. 非目标

本设计不包含以下内容：

- 不在本轮中直接实施完整知识库内容迁移；
- 不在本轮中引入新的并行 bot 编排框架；
- 不把飞书知识库变成工程真源；
- 不在本轮中一次性覆盖所有飞书对象类型；
- 不在本轮中把所有历史联调记录完全结构化回补。

## 3. 当前状态判断

### 3.1 Base 链路

Base 链路已经属于真实打通状态：

- bot 权限可用；
- runner 可稳定读取真实 Base record；
- `VALIDATION_RESULT` 已能回写真实 `work_item_title`。

### 3.2 OKR 链路

OKR 链路当前属于“部分打通”状态：

- 已完成：
  - `collect_lark_context.py` 中 `objective` / `key_result` 读取逻辑；
  - 单元测试中的 OKR mock 覆盖；
  - 设计文档中对 `Objective / KR` 作为上游上下文的正式定义；
  - `7089809` 对应真实 run `27085868440` 已验证 PR 评论渲染逻辑可随部署生效。
- 未完成：
  - bot 的真实 OKR 权限确认；
  - 真实 `Objective ID / KR ID` 对象读取；
  - 带 OKR 的真实 E2E 联调；
  - 在最终 PR 评论或产物中明确体现 OKR 摘要。

补充说明：

- 上述真实 run 虽成功，但当前验收请求绑定的真实 Base record 仍未提供可读的 `Objective ID / KR ID`，因此评论中未出现 OKR 摘要字段；
- 后续诊断 run `27086007210` 已进一步验证：即使评论渲染逻辑回退到直接输出 work item 上的原始 `Objective ID / KR ID` 字段，真实评论仍无对应行；
- 这表明当前 blocker 已从“代码能力缺失”转为“真实数据与权限尚未补齐”。

结论：

- Base 已真实闭环；
- OKR 仍需补“最后一跳”的真实验证。

## 4. 核心设计结论

### 4.1 先补 OKR 真链路，再建设知识库内容层

本设计建议先完成 OKR 真链路闭环，再建设知识库内容层。原因如下：

- 知识库必须沉淀真实、稳定的流程，而不是沉淀尚未打通的假设；
- 如果 OKR 仍未真实打通，知识库中的接入说明会很快过时；
- `github-feishu-bot-bootstrap` 的升级，也需要建立在真实 OKR 成功样本之上。

### 4.2 知识库采用双层结构

知识库不建议只放在单一载体中，而应采用双层结构：

- **工程真源层**：仓库内 `docs/`、`SKILLS/`、workflow、测试、PR 评论记录
- **运营消费层**：飞书 Wiki / Docs，用于跨角色阅读、上手、值班和复盘

职责分工如下：

- GitHub / 仓库负责“准”
- 飞书知识库负责“用”

### 4.3 `github-feishu-bot-bootstrap` 必须变成演进型技能

该技能不应仅记录“如何创建一个 bot”，而应承担以下职责：

- 记录当前最佳接线方式；
- 收纳真实联调中发现的新故障模型；
- 为每个新 bot 场景补充新的输入、权限、验证步骤；
- 持续升级为 GitHub x 飞书集成的标准引导技能。

因此，本技能应明确采用如下原则：

- 每次新增 GitHub x 飞书协作任务时，评估是否应回补到该技能；
- 若出现新的对象类型、权限模型、workflow 形态或故障模式，优先更新技能；
- 技能更新应与真实案例、文档结论和 E2E 证据绑定。

## 5. 目标架构

### 5.1 OKR 上下文架构

目标链路如下：

1. Base `work item` 提供任务主入口
2. `Objective ID` / `KR ID` 提供目标挂接
3. `collect_lark_context.py` 拉取：
   - `work_item`
   - `objective`
   - `key_result`
4. `run_acceptance_cycle.py` 读取上下文快照并生成正式验收结论
5. PR 评论中的 `VALIDATION_RESULT` 至少保留可读的 OKR 摘要信息

### 5.2 知识库架构

建议建立 4 个知识域：

1. **总览域**
   - GitHub x 飞书协作目标
   - 真源分层
   - bot 身份模型
2. **接入域**
   - bot 创建
   - 权限配置
   - secrets 注入
   - workflow 模板
3. **运维域**
   - 常见故障
   - strict mode
   - token mint
   - Base / OKR / Docs 对象排障
4. **案例域**
   - 成功 run
   - 对应提交
   - PR 评论样例
   - 经验结论

### 5.3 技能演进架构

`github-feishu-bot-bootstrap` 后续建议拆成以下内部章节能力：

- `Base 接入`
- `OKR 接入`
- `文档 / Wiki 接入`
- `tenant_access_token 模式`
- `多 bot 扩展模板`
- `E2E 验证模板`
- `故障排查手册`

这不意味着立刻拆成多个技能，而是先在一个技能内形成稳定目录结构，待内容增长后再拆分。

## 6. 分阶段实施建议

### Phase 1. OKR 真链路补齐

目标：

- 把 `objective` / `key_result` 从 mock 能力升级为真实 E2E 能力。

动作：

1. 确认飞书 bot 的 OKR 应用身份权限；
2. 准备一条带真实 `Objective ID / KR ID` 的 Base record；
3. 本地 bot 冒烟读取 OKR；
4. workflow 中复用当前 bot token 模式跑一轮带 OKR 的 E2E；
5. 在 `VALIDATION_RESULT` 或上下文产物中确认 OKR 信息可见。

验收标准：

- bot 能真实读取 `objective`
- bot 能真实读取 `key_result`
- 完整 workflow 成功结束

### Phase 2. 知识库骨架搭建

目标：

- 建立一个面向持续运营的知识库骨架。

动作：

1. 仓库侧补齐：
   - 总览文档
   - 接入规范
   - 故障手册
   - 成功案例索引
2. 飞书侧建立 Wiki / Docs 目录结构；
3. 明确“仓库真源、飞书消费”的同步边界。

验收标准：

- 仓库存在明确的知识入口
- 飞书存在对应目录结构
- 两边职责清晰，无重复真源冲突

### Phase 3. 技能升级为长期入口

目标：

- 让 `github-feishu-bot-bootstrap` 变成标准入口技能。

动作：

1. 将 OKR 接入流程写入技能；
2. 将知识库更新动作写入技能；
3. 为新 bot 场景定义增量补全规则；
4. 绑定“每次真实案例后必须回写技能”的要求。

验收标准：

- 技能能覆盖 Base + OKR + 知识库三类场景
- 技能包含标准输入、输出、验证与排障步骤

## 7. 文档与资产规划

### 7.1 仓库侧建议新增 / 持续维护资产

- `docs/github-feishu-okr-knowledgebase-design.md`
- GitHub x 飞书接入规范文档
- GitHub x 飞书故障排查文档
- 成功 E2E run 档案索引
- `SKILLS/github-feishu-bot-bootstrap/SKILL.md`

### 7.2 飞书侧建议目录

- `GitHub x 飞书协作总览`
- `Bot 接入手册`
- `Base / OKR 接入清单`
- `常见故障与值班手册`
- `E2E 成功案例`

## 8. 风险与约束

### 8.1 权限风险

- OKR 权限可能与 Base 权限不同，需要单独开通；
- bot 能读 Base 不代表能读 OKR。

### 8.2 漂移风险

- 如果知识库只更新飞书，不更新仓库技能和文档，会快速漂移；
- 如果只更新技能，不更新案例和 FAQ，后续复用成本仍高。

### 8.3 复杂度风险

- 若在本轮同时建设完整知识库内容，容易把“规划”变成“内容搬运工程”；
- 因此首轮应优先搭骨架，而不是追求大而全。

## 9. 推荐决策

建议采用以下顺序：

1. 先做 OKR 真链路补齐；
2. 再搭知识库骨架；
3. 再升级 `github-feishu-bot-bootstrap` 为长期入口技能；
4. 后续每新增一个 GitHub x 飞书协作任务，都按“真实案例 -> 文档结论 -> 技能补全”的顺序回补。

## 10. 成功标准

本方案完成后，应满足：

- OKR 相关能力完成真实 E2E 验证；
- 仓库与飞书形成双层知识库结构；
- `github-feishu-bot-bootstrap` 成为持续演进的标准技能入口；
- 后续新增 bot 场景时，不再从零开始摸索接入方式。
