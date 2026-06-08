---
id: GITHUB-FEISHU-NEW-BASE-E2E-RUNBOOK
type: runbook
owner: ledger-protocol-agent
depends:
  - GITHUB-FEISHU-INTEGRATION-HANDBOOK
  - GITHUB-FEISHU-TROUBLESHOOTING
  - GITHUB-FEISHU-E2E-CASE-INDEX
version: 1
last_verified: 2026-06-07
---

# 新 Base 接入真实 E2E 执行清单

> 仓库：`DREAM-AGENT`
> 状态：active
> 用途：将新的飞书 Base 接入现有 `collab-acceptance-agent` 真实 E2E 链路，并验证 OKR 上下文可见

## 1. 适用时机

当出现以下任一情况时，使用本 runbook：

- 旧 Base 无法写入，需切换到新 Base
- 新建了可编辑的 Base / Wiki 页面，需要接入真实 E2E
- OKR 真链路要在新的 work item 上重新验证

## 2. 当前已探明的新 Base

以下信息已在本轮排查中确认：

- 新 Wiki 链接：`https://ncncuthnf6xe.feishu.cn/wiki/CXcvww2sUiP9s4kVBa9coa0hnkc`
- 真实 Base token：`SjCHbDasHarEcFsJjXwc5JZgnUr`
- 真实 table id：`tblQF4dbH4oaMiYq`

当前已知字段状态：

- `任务`
- `Objective ID`
- `KR ID`

说明：

- 该页面不是模板占位页
- 已可解析为真实 Base 对象
- 后续所有命令均应基于上述 `base token` 和 `table id`

## 3. 执行原则

执行本 runbook 时，遵守以下原则：

1. 不使用 `lark-cli auth status`
2. 不使用 `lark-cli config ...`
3. 只用真实业务命令探活
4. 先确认真实资源，再做写操作
5. 先准备 Base record，再触发 GitHub workflow

## 4. 阶段 A：确认新 Base 状态

### 4.1 读取 Base 本体

```bash
lark-cli base +base-get \
  --base-token SjCHbDasHarEcFsJjXwc5JZgnUr \
  --as user \
  --format json
```

通过标准：

- 命令成功返回 Base 信息

### 4.2 读取表列表

```bash
lark-cli base +table-list \
  --base-token SjCHbDasHarEcFsJjXwc5JZgnUr \
  --offset 0 \
  --limit 50 \
  --as user \
  --format json
```

通过标准：

- `tblQF4dbH4oaMiYq` 存在

### 4.3 读取字段列表

```bash
lark-cli base +field-list \
  --base-token SjCHbDasHarEcFsJjXwc5JZgnUr \
  --table-id tblQF4dbH4oaMiYq \
  --offset 0 \
  --limit 100 \
  --as user \
  --format json
```

通过标准：

- 字段中存在：
  - `任务`
  - `Objective ID`
  - `KR ID`

若缺字段：

- 由人工在飞书 UI 中补齐
- 或在当前 user 身份可写时用 `field-create` 补齐

## 5. 阶段 B：准备真实 work item

### 5.1 查看现有记录

```bash
lark-cli base +record-list \
  --base-token SjCHbDasHarEcFsJjXwc5JZgnUr \
  --table-id tblQF4dbH4oaMiYq \
  --offset 0 \
  --limit 20 \
  --as user \
  --format json
```

目标：

- 找到一条可用作验收的 record
- 或确认需要新建一条 record

### 5.2 准备记录字段值

目标记录至少应具备：

- `任务`：可读的 work item 标题
- `Objective ID`：真实 Objective id
- `KR ID`：真实 Key Result id

如果已经有记录，可直接更新：

```bash
lark-cli base +record-upsert \
  --base-token SjCHbDasHarEcFsJjXwc5JZgnUr \
  --table-id tblQF4dbH4oaMiYq \
  --record-id <NEW_RECORD_ID> \
  --json '{"任务":"<work item title>","Objective ID":"<objective-id>","KR ID":"<kr-id>"}' \
  --as user \
  --format json
```

如果没有记录，可先新建，再记下新的 `record_id`。

通过标准：

- 目标 record 中可读到三项字段值

## 6. 阶段 C：确认 OKR 对象

### 6.1 最小目标

新 Base record 上的：

- `Objective ID`
- `KR ID`

必须都指向真实存在的飞书 OKR 对象。

### 6.2 成功定义

不要求本地一定先完整浏览 OKR，只要求：

- `Objective ID` 不是空值
- `KR ID` 不是空值
- 后续 workflow 跑起来后，bot 能读取对应对象

## 7. 阶段 D：生成新的验收请求

当前 workflow 的触发方式为：

- `workflow_dispatch`
- 输入 `pr_number`
- 输入 `acceptance_request_id`

因此需要一条新的 `ACCEPTANCE_REQUEST`，且其 locator 指向新 Base。

验收请求正文必须至少包含：

- `Acceptance Request ID`
- `Acceptance Cycle ID`
- `Work Item ID`
- `Target PR`
- `Lark Base URL`
- `Lark Table ID`
- `Lark Record ID`

建议直接沿用既有格式生成一条新的 PR 评论，确保：

- `Lark Base URL` 指向新 Base 页面
- `Lark Table ID` 为 `tblQF4dbH4oaMiYq`
- `Lark Record ID` 为新记录的真实 `record_id`

## 8. 阶段 E：触发真实 workflow

在新的 `ACCEPTANCE_REQUEST` 写好后，执行：

```bash
gh workflow run collab-acceptance-agent.yml \
  --ref pilot/acceptance-orchestration-v2-e2e-20260607 \
  -f pr_number=7 \
  -f acceptance_request_id=<NEW_ACCEPTANCE_REQUEST_ID>
```

通过标准：

- workflow 成功进入 `acceptance` job
- `Collect lark context` 成功
- `Run acceptance cycle` 成功
- `Post VALIDATION_RESULT comment` 成功

## 9. 阶段 F：验收评论结果

成功 run 后，检查 `PR #7` 最新 `VALIDATION_RESULT`。

### 9.1 Base 最低验收

评论中至少应有：

- `work_item_title=<任务字段值>`
- `pr_number=7`

### 9.2 OKR 真链路验收

如新 record 已正确挂 OKR，评论中还应出现：

- `objective_id=<真实 objective id>`
- `objective_title=<可读标题>`
- `key_result_id=<真实 kr id>`
- `key_result_title=<可读标题>`

## 10. 失败分流

### 10.1 读命令成功，写命令报 `91403`

结论：

- 新 Base 仍无写权限

动作：

- 人工在 UI 中补 record / 字段
- 然后直接从“阶段 D”继续

### 10.2 workflow 成功，但评论无 OKR 行

优先判断：

1. 新 record 是否真的写入了 `Objective ID / KR ID`
2. 这些 id 是否是真实 OKR 对象
3. bot 是否对这些 OKR 有读权限

### 10.3 评论里有 `objective_id`，但没有标题

结论：

- Base record 已挂 OKR id
- 但 OKR 对象读取仍不完整

动作：

- 优先检查 OKR 对象权限

## 11. 收尾要求

一旦新 Base 真实 E2E 成功，至少同步回写：

- `docs/github-feishu-e2e-case-index.md`
- `docs/github-feishu-troubleshooting.md`（若出现新故障）
- `SKILLS/github-feishu-bot-bootstrap/SKILL.md`（若出现新经验）
- `PR #7` 跟进评论

## 12. 执行完成标准

本 runbook 只有在以下全部满足时才算完成：

1. 新 Base 已被 workflow 真实读取
2. 新 record 已参与真实 acceptance cycle
3. `VALIDATION_RESULT` 中出现 Base 摘要
4. 若已挂 OKR，则评论中出现 OKR 摘要
5. 案例与结论已回写仓库真源
