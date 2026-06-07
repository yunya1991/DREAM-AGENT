---
id: GITHUB-FEISHU-TROUBLESHOOTING
type: runbook
owner: ledger-protocol-agent
depends:
  - GITHUB-FEISHU-INTEGRATION-HANDBOOK
  - 03-WORKFLOWS-AND-NORMS
  - 05-FAQ
version: 1
last_verified: 2026-06-07
---

# GitHub x 飞书故障排查手册

> 仓库：`DREAM-AGENT`
> 状态：active
> 用途：统一记录 GitHub x 飞书接入中的高频故障、判别信号与恢复动作

## 1. 故障分类原则

优先判断故障属于哪一层：

1. CLI / 平台提示层
2. 飞书资源权限层
3. workflow 环境继承层
4. 真实数据层
5. 评论渲染层

不要把所有失败都归因于“没有登录”。

## 2. 常见故障模型

### 2.1 平台弹出“Lark CLI 需要身份验证”

表现：

- 宿主环境弹出统一提示
- 但业务命令不一定真的失败

正确判断：

- 不再用 `auth status` / `config` 判断健康状态
- 改用真实业务命令判断，例如：
  - `base +base-get`
  - `base +field-list`
  - `base +record-get`

结论：

- 该提示可能只是平台对 `auth/config` 类命令的通用阻断，不等于真实掉鉴权

### 2.2 `91403 you don't have permission`

表现：

- 读 Base 成功
- 写字段或写记录失败

含义：

- 资源级写权限不足
- 不是 CLI 未授权

恢复：

- 打开对应 Base 的分享面板
- 为当前 `user` 身份开可编辑权限
- 或由人工手动创建目标字段

### 2.3 `strict mode is "user"` / bot 回退到 user

表现：

- 某一步能读 Base
- 下一步重新读取飞书上下文时失败

含义：

- workflow 的后续步骤没有继承 bot 环境变量

恢复：

- 在 `Collect lark context`
- 以及 `Run acceptance cycle`
- 两处都显式传入 bot 相关环境变量

### 2.4 `work_item_title` 为空

表现：

- `VALIDATION_RESULT` 中的 `work_item_title` 为空

含义：

- 真实 Base 字段名不是 `Title`

恢复：

- 摘要字段兼容顺序应支持：
  - `Title`
  - `任务`
  - `Name`
  - `名称`
  - 首个非空字符串字段

### 2.5 已部署 OKR 摘要逻辑，但评论没有 OKR 行

表现：

- run 成功
- 评论中只有 `work_item_title` / `pr_number`

优先判断：

1. Base record 是否真的有 `Objective ID / KR ID`
2. 对应 OKR 对象是否存在
3. bot 是否对 OKR 对象有读权限

已验证结论：

- 若连回退输出的原始 `objective_id` / `key_result_id` 都没有出现，优先判断为 Base record 未填写 OKR 字段

### 2.6 新建的是模板或副本，不是 workflow 使用的真实 Base

表现：

- 在某个新页面里能编辑
- 但 workflow 仍读取旧 Base / 旧 record

恢复：

- 先把 wiki / 页面链接解析为真实 Base token
- 确认实际 token、table id、record id
- 再决定是否切换 workflow 的输入源

## 3. 最小健康检查策略

为避免被平台提示干扰，推荐最小检查顺序：

1. `base +base-get`
2. `base +field-list`
3. `base +record-get`
4. 必要时才执行真实写操作

禁止默认使用：

- `lark-cli auth status`
- `lark-cli config ...`

因为它们在当前宿主环境里更容易触发与真实故障无关的通用提示。

## 4. 当前真实 blocker 模板

当出现“看起来像断了”的情况时，按以下模板判断：

- 若读命令成功：认证仍有效
- 若写命令报 `91403`：资源写权限不足
- 若 OKR 行缺失：先看 Base record 是否有 `Objective ID / KR ID`
- 若 workflow 成功但评论无 OKR：先看真实数据，再看权限，最后才看代码

## 5. 处理优先级

建议按以下顺序排障：

1. 资源是否正确
2. 读权限是否可用
3. 写权限是否可用
4. workflow 环境是否继承
5. 真实数据是否存在
6. 渲染逻辑是否部署

## 6. 与技能联动

出现新的故障模型后，必须同步回写：

- 本手册
- `SKILLS/github-feishu-bot-bootstrap/SKILL.md`
- 必要时回写 `03-WORKFLOWS-AND-NORMS.md`
