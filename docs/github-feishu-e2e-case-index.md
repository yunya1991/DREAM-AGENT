---
id: GITHUB-FEISHU-E2E-CASE-INDEX
type: index
owner: ledger-protocol-agent
depends:
  - 03-WORKFLOWS-AND-NORMS
  - GITHUB-FEISHU-INTEGRATION-HANDBOOK
version: 1
last_verified: 2026-06-07
---

# GitHub x 飞书 E2E 案例索引

> 仓库：`DREAM-AGENT`
> 状态：active
> 用途：集中登记真实 GitHub x 飞书联调 run、提交、结论与后续动作

## 1. 使用规则

每次真实联调后，至少记录：

- GitHub run id
- 对应提交
- 核心结论
- 是否形成新故障模型
- 是否需要回写技能或规范

## 2. 真实案例

### Case 1. 首个远端完整 Base 闭环

- Run: `27085309457`
- Commit: `47d9432`
- 场景：修复 bot 环境继承后，完成真实 `workflow_dispatch` 全链路
- 结论：
  - `Collect lark context` 成功
  - `Run acceptance cycle` 成功
  - PR 评论成功回写 `VALIDATION_RESULT`
- 产出：
  - 证明 Base 真链路闭环可行

### Case 2. `work_item_title` 摘要修复验证

- Run: `27085416975`
- Commit: `09d5815`
- 场景：真实 Base 使用 `任务` 字段，修复 `work_item_title` 为空
- 结论：
  - `Context Snapshot` 已能回写真实标题
  - 摘要逻辑必须兼容 `任务`
- 产出：
  - 固化了真实字段兼容顺序

### Case 3. OKR 摘要渲染代码已上线

- Run: `27085868440`
- Commit: `7089809`
- 场景：将 `objective` / `key_result` 摘要加入 `VALIDATION_RESULT`
- 结论：
  - 渲染逻辑已随部署生效
  - 真实评论中仍未出现 OKR 行
- 推断：
  - blocker 已从代码能力缺失转向真实数据与权限

### Case 4. 原始 OKR ID 回退输出诊断

- Run: `27086007210`
- Commit: `1b999a2`
- 场景：即使 OKR 对象未取到，也尝试直接输出 work item 上原始 `Objective ID / KR ID`
- 结论：
  - 真实评论中仍无 `objective_id` / `key_result_id`
  - 当前 Base record 本身未挂 OKR 字段值
- 推断：
  - 真实 blocker 已进一步收敛到数据侧

## 3. 当前总判断

截至 `2026-06-07`：

- Base E2E：已真实闭环
- OKR 代码路径：已具备
- OKR 真实对象与 record 绑定：未完成
- 飞书知识库仓库侧骨架：进行中

## 4. 后续新增案例时的记录模板

新增案例时，按以下模板追加：

```md
### Case N. <标题>

- Run: `<github-run-id>`
- Commit: `<commit-sha>`
- 场景：<一句话描述>
- 结论：
  - <结论 1>
  - <结论 2>
- 推断：
  - <是否新增 blocker / 是否推进主线>
- 产出：
  - <文档、技能、评论、脚本等沉淀>
```

## 5. 联动更新要求

若案例带来新的工程结论，至少同步更新以下之一：

- `03-WORKFLOWS-AND-NORMS.md`
- `github-feishu-troubleshooting.md`
- `SKILLS/github-feishu-bot-bootstrap/SKILL.md`
