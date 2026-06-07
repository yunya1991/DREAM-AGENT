---
name: github-feishu-bot-bootstrap
description: 统一 GitHub x 飞书 bot 搭建、权限开通、workflow 接线与 E2E 联调。Invoke when 需要新建或扩展 GitHub 与 Feishu 的 bot 协作链路。
version: "1.0"
created: "2026-06-07"
status: "draft"
---

# GitHub Feishu Bot Bootstrap

## 目标

把 GitHub Actions 与飞书开发者应用 / bot 稳定接到同一条自动化链路上，支持：

1. 从 GitHub workflow 读取飞书 Base / OKR 上下文
2. 用 bot 身份代替不稳定的 `user` 登录态
3. 以 `tenant_access_token` 为中心完成 runner 侧鉴权
4. 将真实 E2E 联调过程沉淀为可复用操作模板

## 适用场景

当出现以下需求时触发本技能：

- 需要新建一个飞书开发者应用 / bot
- 需要让 GitHub Actions 读取飞书 Base / OKR / 云文档
- 需要把现有 `lark-cli --as user` 流程切换到 `--as bot`
- 需要排查 runner 中飞书调用失败、身份不稳定、token 缺失的问题
- 需要扩展更多 GitHub x 飞书协作 bot

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

## 标准流程

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
   - 其他 OKR / 文档权限
5. 在飞书侧确认目标 Base 已对该应用授权

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

## Phase 5. `lark-cli` 关键约束

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

## Phase 6. E2E 验证清单

至少验证以下步骤全部成功：

1. `ACCEPTANCE_REQUEST` 能被解析
2. `acceptance_cycle` 能创建或加载
3. workflow 能 mint `tenant_access_token`
4. `collect_lark_context.py` 能读取真实 Base record
5. `run_acceptance_cycle.py` 中再次读取飞书上下文时仍继承 bot 身份
6. PR 能收到正式 `VALIDATION_RESULT`

## 常见故障与修复

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

