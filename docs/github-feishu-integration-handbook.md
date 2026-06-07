---
id: GITHUB-FEISHU-INTEGRATION-HANDBOOK
type: handbook
owner: ledger-protocol-agent
depends:
  - 03-WORKFLOWS-AND-NORMS
  - 06-SKILLS-INVENTORY
  - GITHUB-FEISHU-OKR-KNOWLEDGEBASE-DESIGN
version: 1
last_verified: 2026-06-07
---

# GitHub x 飞书接入规范

> 仓库：`DREAM-AGENT`
> 状态：active
> 用途：作为 GitHub Actions 接入飞书 Base / OKR / 知识库时的仓库真源规范

## 1. 适用范围

本规范适用于以下场景：

- 新建 GitHub x 飞书 bot 协作链路
- 将现有 workflow 接入飞书 Base record
- 在验收链路中补充 Objective / Key Result 上下文
- 建立飞书知识库侧的运营消费入口
- 为新场景回补 `github-feishu-bot-bootstrap`

## 2. 标准接入顺序

建议按以下顺序推进：

1. 创建或复用飞书开发者应用 / bot
2. 开通 Base 所需权限
3. 配置 GitHub secrets 与 runner 环境变量
4. 先完成 Base 真链路
5. 再补 OKR 真链路
6. 最后回写知识库与技能

## 3. 运行时身份模型

当前仓库存在两类身份：

- `user`：用于访问用户自己的飞书资源，适合日常读写和人工联调
- `bot`：用于 GitHub Actions 中的稳定自动化访问

约束如下：

- 本地人工探测优先 `user`
- GitHub Actions 远端联调优先 `bot`
- `bot` 能读 Base 不代表一定能读 OKR
- `user` 身份是否可写取决于具体资源的协作权限，而不是 CLI 是否已授权

## 4. GitHub 侧必备配置

至少要求：

- `LARK_APP_ID`
- `LARK_APP_SECRET`
- workflow 中显式 mint `tenant_access_token`
- 在读取飞书上下文和运行 acceptance cycle 时都继承 bot 相关环境变量

推荐最小环境变量集合：

```bash
LARK_IDENTITY=bot
LARKSUITE_CLI_APP_ID=<from secrets>
LARKSUITE_CLI_TENANT_ACCESS_TOKEN=<minted token>
LARKSUITE_CLI_STRICT_MODE=off
```

## 5. Base 接入规范

接入 Base 时至少保证：

- 真实 Base URL、Base token、table id、record id 可定位
- `collect_lark_context.py` 能稳定读取真实 record
- `context_summary` 不只依赖 `Title`，还要兼容 `任务`
- `VALIDATION_RESULT` 中至少出现：
  - `work_item_title`
  - `pr_number`

如需承载 OKR 关联，Base record 还应具备：

- `Objective ID`
- `KR ID`

这两个字段是 OKR 真链路的最小入口。

## 6. OKR 接入规范

OKR 接入分两层：

- 代码层：仓库已支持通过 `Objective ID / KR ID` 读取 `objective` 与 `key_result`
- 资源层：飞书侧必须真实存在可读的 Objective / KR 对象

验收标准：

- work item 上存在真实 `Objective ID / KR ID`
- bot 对对应 OKR 对象有读取权限
- `VALIDATION_RESULT` 的 `Context Snapshot` 中可见：
  - `objective_id`
  - `objective_title`
  - `key_result_id`
  - `key_result_title`

## 7. 知识库接入规范

知识库采用双层结构：

- 仓库 `docs/` 和 `SKILLS/`：工程真源
- 飞书 Wiki / Docs：运营消费层

最小目录建议：

- `GitHub x 飞书协作总览`
- `Bot 接入手册`
- `Base / OKR 接入清单`
- `常见故障与值班手册`
- `E2E 成功案例`

## 8. 文档回写要求

每次真实联调后，至少更新以下其中两类资产：

- 仓库规范文档
- 技能文档
- PR 评论结论
- 飞书知识库消费页

若出现新的对象类型、权限模型或故障模式，优先回补 `github-feishu-bot-bootstrap`。

## 9. 当前已验证结论

截至 `2026-06-07`：

- Base 真链路已完成真实 E2E
- `work_item_title` 空值问题已修复
- OKR 评论渲染逻辑已具备，但仍受真实数据与权限状态约束
- 飞书知识库入口文档已开始建立

## 10. 主线优先级

推荐执行顺序固定为：

1. Base 真链路
2. OKR 真链路
3. 知识库骨架
4. 技能持续回补
