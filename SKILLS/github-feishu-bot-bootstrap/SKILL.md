---
name: github-feishu-bot-bootstrap
description: GitHub x 飞书长期入口技能。统一处理 Base / OKR / Wiki 接入、bot 权限、workflow 接线、E2E 联调与故障回补。Invoke when 需要新建、扩展或排障 GitHub 与 Feishu 协作链路。
version: "2.0"
created: "2026-06-07"
status: "draft"
---

# GitHub Feishu Bot Bootstrap

## 定位

本技能不是一次性“建 bot 操作记录”，而是 GitHub x 飞书协作的长期入口技能。它负责：

- 为新场景选择正确接入路径
- 统一 Base / OKR / Wiki 三类资源的接线方法
- 统一 bot 权限、workflow 环境变量和 E2E 验证标准
- 吸收真实案例中的新故障模型
- 把工程结论回补到仓库文档、技能和 PR 评论

## 技能地图

使用本技能时，优先判断当前任务属于哪一类：

1. `Base 接入`
2. `OKR 接入`
3. `知识库 / Wiki 接入`
4. `workflow / bot 接线`
5. `E2E 验证`
6. `故障排查`

如果任务同时跨多个模块，默认顺序为：

1. 先 `workflow / bot 接线`
2. 再 `Base 接入`
3. 再 `OKR 接入`
4. 再 `知识库 / Wiki 接入`
5. 最后 `E2E 验证`

## 适用场景

当出现以下需求时触发本技能：

- 需要新建一个飞书开发者应用 / bot
- 需要让 GitHub Actions 读取飞书 Base / OKR / 云文档
- 需要把现有 `lark-cli --as user` 流程切换到 `--as bot`
- 需要排查 runner 中飞书调用失败、身份不稳定、token 缺失的问题
- 需要扩展更多 GitHub x 飞书协作 bot
- 需要把真实联调结论沉淀成长期知识资产

## 输入

- GitHub 仓库地址
- 目标 workflow 文件路径
- 飞书目标资源：
  - Base URL
  - Table ID
  - Record ID
  - 可选 Objective / KR 标识
- 飞书开发者应用信息：
  - `App ID`
  - `App Secret`

## 输出

- 可用的飞书开发者应用 / bot
- 已开通的应用身份权限
- 已写入的 GitHub secrets
- 已接线的 workflow
- 至少一条成功的真实 E2E run 记录
- 若涉及 OKR，则 `VALIDATION_RESULT` 中可见对应 objective / key result 摘要

## 仓库真源

执行本技能时，优先参考以下仓库文档：

- `docs/github-feishu-integration-handbook.md`
- `docs/github-feishu-troubleshooting.md`
- `docs/github-feishu-e2e-case-index.md`
- `docs/github-feishu-okr-knowledgebase-design.md`

这些文档负责沉淀规范、故障和案例；本技能负责把它们转成实际执行路径。

## 标准入口流程

每次执行本技能，都先做以下判断：

1. 当前目标资源是 Base、OKR 还是 Wiki
2. 当前执行环境是本地 `user` 还是 GitHub Actions `bot`
3. 当前任务是“首次接入”“扩展现有链路”还是“排障”
4. 当前任务是否要求真实 E2E 证据

然后按下面的模块流程分流。

## 模块 A. Base 接入

适用于：

- 接 workflow 到 Base record
- 补 work item 字段
- 排查 record 读取、字段结构和写权限问题

最小要求：

- 能定位真实 Base URL、Base token、table id、record id
- `collect_lark_context.py` 能读取真实 record
- `context_summary` 兼容 `任务`
- `VALIDATION_RESULT` 至少出现 `work_item_title`

若要作为 OKR 上下文入口，还必须存在：

- `Objective ID`
- `KR ID`

## 模块 B. OKR 接入

适用于：

- 通过 `Objective ID / KR ID` 挂接 Objective / Key Result
- 验证评论中能否出现 OKR 摘要

判断顺序：

1. 先确认 Base record 是否存在 `Objective ID / KR ID`
2. 再确认对应 OKR 对象真实存在
3. 再确认 bot 是否对这些对象有读取权限
4. 最后再看评论渲染是否正确

成功标准：

- `Context Snapshot` 中出现：
  - `objective_id`
  - `objective_title`
  - `key_result_id`
  - `key_result_title`

## 模块 C. 知识库 / Wiki 接入

适用于：

- 创建飞书侧长期入口文档
- 把仓库结论同步到运营消费层

飞书侧推荐最小目录：

- `GitHub x 飞书协作总览`
- `Bot 接入手册`
- `Base / OKR 接入清单`
- `常见故障与值班手册`
- `E2E 成功案例`

仓库侧对应真源：

- `docs/github-feishu-integration-handbook.md`
- `docs/github-feishu-troubleshooting.md`
- `docs/github-feishu-e2e-case-index.md`

## 模块 D. workflow / bot 接线

### Phase 1. 创建飞书开发者应用

1. 打开飞书开放平台 `open.feishu.cn`
2. 创建企业自建应用
3. 添加 `机器人` 能力
4. 记录 `App ID`
5. 生成并安全保存 `App Secret`

## Phase 2. 开通权限与资源访问

1. 进入 `权限管理`
2. 为 bot 开通应用身份权限
3. 至少确认以下权限：
   - `base:record:read`
4. 如 workflow 需要更多能力，再按需开通：
   - `base:record:retrieve`
   - `base:app:read`
   - `okr:objective:read`
   - `okr:key_result:read`
   - 其他文档权限
5. 在飞书侧确认目标 Base 已对该应用授权
6. 若需要读取 OKR，确认 bot 对目标 Objective / KR 所在对象也有访问权限

## Phase 3. GitHub Secrets 接线

在仓库中写入：

- `LARK_APP_ID`
- `LARK_APP_SECRET`

不要把密钥写入仓库文件或评论正文。

## Phase 4. Workflow 接线原则

优先使用 bot 身份，不依赖 runner 本地的交互式用户登录态。

推荐模式：

1. 在 workflow 中先调用：
   - `https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal`
2. 用 `App ID + App Secret` mint `tenant_access_token`
3. 将结果写入 `GITHUB_ENV`
4. 后续所有需要访问飞书的步骤统一继承：
   - `LARK_IDENTITY=bot`
   - `LARKSUITE_CLI_APP_ID`
   - `LARKSUITE_CLI_TENANT_ACCESS_TOKEN`
   - `LARKSUITE_CLI_STRICT_MODE=off`

## 模块 E. `lark-cli` 关键约束

- 不要假设 runner 上存在稳定的 `user` 登录态
- 不要把 `auth status` 作为 bot 外部凭据模式下的硬前置门禁
- 外部凭据模式下优先依赖环境变量
- 注意 `lark-cli` 真正识别的环境变量前缀是：
  - `LARKSUITE_CLI_*`

关键变量：

- `LARKSUITE_CLI_APP_ID`
- `LARKSUITE_CLI_APP_SECRET`
- `LARKSUITE_CLI_TENANT_ACCESS_TOKEN`
- `LARKSUITE_CLI_STRICT_MODE`

## 模块 F. E2E 验证清单

至少验证以下步骤全部成功：

1. `ACCEPTANCE_REQUEST` 能被解析
2. `acceptance_cycle` 能创建或加载
3. workflow 能 mint `tenant_access_token`
4. `collect_lark_context.py` 能读取真实 Base record
5. 如配置了 `Objective ID / KR ID`，bot 能读取真实 OKR 对象
6. `run_acceptance_cycle.py` 中再次读取飞书上下文时仍继承 bot 身份
7. PR 能收到正式 `VALIDATION_RESULT`
8. 如存在 OKR，上述评论的 `Context Snapshot` 中能看到 objective / key result 摘要

## 模块 G. 常见故障与修复

### 1. `strict mode is "user"`

原因：

- runner 或外部凭据环境把 CLI 约束在 `user`

修复：

- 在 workflow 步骤环境中显式注入：
  - `LARKSUITE_CLI_STRICT_MODE=off`
- 同时给所有飞书读取步骤传入统一 bot 环境变量

### 2. `no access token available for bot`

原因：

- 只传了 `App ID / App Secret`，但当前环境不会自动 mint token

修复：

- 在 workflow 中显式调用 `tenant_access_token/internal`
- 把返回的 `tenant_access_token` 注入 `LARKSUITE_CLI_TENANT_ACCESS_TOKEN`

### 3. Base 读取成功，但后续 orchestrator 又失败

原因：

- 前置 `Collect lark context` 步骤继承了 bot token
- 但 `Run acceptance cycle` 没继承同一组环境变量

修复：

- 所有会再次调用飞书的步骤必须继承同一组 bot 环境变量

### 4. `work_item_title` 为空

原因：

- 代码只读取 `Title` 字段
- 真实多维表格字段名可能是 `任务`

修复：

- 读取顺序应兼容：
  - `Title`
  - `任务`
  - `Name`
  - `名称`
  - 最后兜底首个非空字符串字段

### 5. 已部署 OKR 摘要渲染，但 PR 评论里仍看不到 OKR 行

原因：

- 当前真实 Base record 没有可读的 `Objective ID` / `KR ID`
- 或 bot 对对应 OKR 对象没有读取权限

修复：

- 先确认验收记录中真实存在 `Objective ID` / `KR ID`
- 再确认 bot 已开通 `okr:objective:read` 与 `okr:key_result:read`
- 然后重跑 workflow，检查 `Context Snapshot` 是否出现：
  - `objective_id`
  - `objective_title`
  - `key_result_id`
  - `key_result_title`
- 如果连回退输出的原始 `objective_id` / `key_result_id` 都没有出现，优先判断为 Base record 本身未填写 OKR 关联字段，而不是代码渲染失败

### 6. 平台弹出“Lark CLI 需要身份验证”

原因：

- 平台可能对 `auth/config` 类命令做统一拦截
- 不等于真实掉鉴权

修复：

- 不要把 `auth status` / `config` 当作主路径探活
- 优先用真实业务命令判断：
  - `base +base-get`
  - `base +field-list`
  - `base +record-get`

### 7. 新建的是模板或副本，不是 workflow 使用的真实 Base

原因：

- 只拿到了页面链接，没有解析成真实 Base token

修复：

- 先解析 wiki / 页面链接
- 确认真实 `base token`、`table id`、`record id`
- 再决定是否切换 workflow 输入源

## 推荐验证命令

### 本地冒烟

```bash
TOKEN=$(python3 - <<'PY'
import json, urllib.request
payload=json.dumps({"app_id":"<APP_ID>","app_secret":"<APP_SECRET>"}).encode("utf-8")
req=urllib.request.Request(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    data=payload,
    headers={"Content-Type":"application/json; charset=utf-8"},
    method="POST",
)
with urllib.request.urlopen(req) as resp:
    result=json.loads(resp.read().decode("utf-8"))
print(result["tenant_access_token"])
PY
)

LARKSUITE_CLI_APP_ID="<APP_ID>" \
LARKSUITE_CLI_TENANT_ACCESS_TOKEN="$TOKEN" \
LARKSUITE_CLI_STRICT_MODE="off" \
lark-cli base +record-get \
  --base-token <BASE_TOKEN> \
  --table-id <TABLE_ID> \
  --record-id <RECORD_ID> \
  --as bot \
  --format json
```

### 远端触发

```bash
gh workflow run collab-acceptance-agent.yml \
  --ref <branch> \
  -f pr_number=<PR_NUMBER> \
  -f acceptance_request_id=<AR_ID>
```

## 成功标准

- 至少一条真实 GitHub Actions run 成功结束
- run 日志显示：
  - `Mint lark tenant access token` 成功
  - `Collect lark context` 成功
  - `Run acceptance cycle` 成功
  - `Post VALIDATION_RESULT comment` 成功
- PR 中出现正式 `VALIDATION_RESULT`
- 如联调场景包含 OKR，`VALIDATION_RESULT` 的 `Context Snapshot` 中能看到 `objective_id` / `key_result_id` 与可读标题

## 产出沉淀要求

每次完成真实联调后，至少回写两类沉淀：

1. 文档结论：
   - 哪个 run 成功
   - 哪个提交成功
   - 哪些环境变量 / 权限是关键
2. PR 评论结论：
   - 本轮目标
   - 已打通链路
   - 仍待优化项

## 技能演进规则

每次出现新的 GitHub x 飞书协作任务后，都应评估是否把新增能力回补到本技能。最少遵守以下规则：

1. 新对象类型接入后，补输入清单、权限清单、验证命令
2. 新 workflow 形态接入后，补标准环境变量和步骤继承要求
3. 新故障模式出现后，补“常见故障与修复”
4. 新真实 E2E 成功后，补文档结论、案例编号与验证标准

补充要求：

- 若仓库侧新增了规范、故障手册或案例索引，本技能要把这些文档纳入“仓库真源”
- 若飞书侧新增了新的运营消费入口，本技能要补最小目录与同步边界
- 若未来内容增长，再拆多个技能；拆分前先保持本技能作为总入口
