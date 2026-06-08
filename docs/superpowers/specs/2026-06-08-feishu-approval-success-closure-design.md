---
id: FEISHU-APPROVAL-SUCCESS-CLOSURE-DESIGN
type: design
owner: governance-agent
depends:
  - FEISHU-GOAL-DRIVEN-PROGRESS-AND-RISK-APPROVAL-DESIGN
version: 1
last_verified: 2026-06-08
---

# 飞书审批真实成功闭环设计

> 仓库：`DREAM-AGENT`
> 日期：`2026-06-08`
> 状态：draft
> 目标：在飞书审批权限真实开通并完成 smoke 成功后，把“成功留痕、审批状态回读、Base 回写、运行环境告警收口、技能沉淀”补成一次完整闭环。

## 1. 背景

前一阶段已经完成以下关键动作：

- 飞书开放平台应用已开通 `approval:approval` 与 `approval:instance`
- GitHub Actions `approval-smoke` 已能真实读取审批定义并创建审批实例
- 真实 smoke 已返回成功实例：
  - `instance_code = 188BD557-48FE-460E-8728-BD987112E7D0`

这说明“权限层 blocker”已经被排除，但当前仓库里仍缺少最后几步协作收口：

- PR 下缺少一条针对本次真实成功的结构化留痕评论
- 审批实例虽然创建成功，但还没有形成“回读实例 -> 投影状态 -> 回写 Base/监控表”的最小闭环
- workflow 仍存在 Node 20 弃用告警
- 本地 SKILL 与仓库文档尚未沉淀这次真实联调中的关键坑点

## 2. 设计目标

本次增量设计只解决以下 4 件事：

- 在 `PR #7` 下补一条结构化 `UPDATED` 评论，明确记录审批真实 smoke 成功
- 增加一个最小审批回读入口，把审批实例状态投影回任务记录与目标记录
- 处理当前相关 workflow 的 Node 20 弃用告警，降低后续运行噪声
- 同步更新本地 SKILL 与仓库内文档，沉淀真实联调经验

## 3. 非目标

本次不做以下事项：

- 不重构现有审批编排总设计
- 不把 smoke workflow 扩成长期编排入口
- 不引入新的飞书数据模型或新的 Base 表
- 不在本轮完成审批事件订阅或 webhook 推送闭环
- 不扩大到所有 workflow 的运行时统一升级，只处理当前明确告警的协作 workflow

## 4. 总体方案

### 4.1 PR 留痕

复用现有 `UPDATED` 评论风格，不新增评论体系。

评论至少包含：

- 本次成功 run 链接
- 已开通并验证生效的权限
- 成功创建的审批实例 `instance_code`
- 当前结论：权限问题已排除，真实审批创建链路已打通
- 下一步：回读审批结果并写回飞书监控面

### 4.2 审批回读与 Base 回写

优先复用现有模块：

- `github-actions/feishu_approval_api.py`
- `github-actions/run_goal_progress_approval_cycle.py`
- `github-actions/sync_github_to_feishu.py`

新增一个最小“真实回读投影”入口，职责如下：

- 输入：
  - `tenant_access_token`
  - `approval_instance_code`
  - `task_payload`
  - `goal_payload`
  - `sibling_tasks`
- 行为：
  - 调用审批实例查询接口读取当前实例状态
  - 复用已有状态解析逻辑，将返回体映射到：
    - `approval_status`
    - `automation_status`
    - `decision_summary`
    - `approval_instance_code`
  - 生成：
    - 可写入飞书任务监控表的 `task_record`
    - 聚合后的 `goal_record`

本轮只要求实现“查询后形成可写回 payload”，不强制绑定到定时任务或 webhook。

### 4.3 Node 20 告警处理

采用最小风险方案：

- 为当前明确触发告警的相关 workflow 注入 `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true`

原因：

- 不需要立即升级 action major 版本
- 不改变现有 workflow 逻辑
- 可以先消除 runner 侧已知弃用告警

### 4.4 SKILL 与仓库文档沉淀

本地 SKILL 更新：

- 在本地相关 Skill 文档中补“飞书审批真实联调 checklist”
- 明确记录两个已踩坑点：
  - 创建审批实例时 `form` 必须是 JSON 数组压缩后转义成字符串
  - 传审批发起人 `open_id` 时必须使用请求体字段 `open_id`，不能塞到 `user_id`

仓库文档更新：

- README / 工程索引 / 相关设计入口补充本次成功结论
- 标注真实 smoke 成功 run 与 `instance_code`
- 记录 Node 24 运行时兼容处理

## 5. 变更边界

建议变更范围限制在以下区域：

- `.github/workflows/collab-acceptance-agent.yml`
- 可能涉及的其他协作 workflow
- `github-actions/feishu_approval_api.py`
- `github-actions/run_goal_progress_approval_cycle.py`
- 新增最小审批回读脚本
- `github-actions/tests/*`
- `README.md`
- `docs/04-ENGINEERING-INDEX.md`
- 本地 `~/.trae/skills/**/SKILL.md` 或相关 references

## 6. 验收标准

本轮完成后应满足：

- `PR #7` 下存在一条针对真实审批成功的结构化 `UPDATED` 评论
- 能通过脚本输入 `instance_code` 回读审批实例状态，并生成任务/目标写回记录
- 至少一条 Base/监控表写回路径能消费该记录结构
- 相关 workflow 不再出现 Node 20 弃用告警
- 本地 Skill 与仓库文档都包含这次真实联调的关键结论与排障经验

## 7. 风险与控制

主要风险如下：

- 若把回读逻辑直接塞进 smoke workflow，会导致 smoke 职责膨胀
- 若直接升级 action 版本，可能引入额外兼容性问题
- 若文档与技能只改一侧，经验沉淀仍然不完整

对应控制策略：

- smoke 保持“定义读取 + 实例创建”最小职责
- 审批回读通过独立最小入口承载
- Node 24 先用运行时开关处理
- Skill 与仓库文档同步更新

## 8. 实施建议

建议按以下顺序实施：

1. 先补 PR 成功留痕评论
2. 再实现审批回读最小入口与测试
3. 再把投影结果回写到 Base/监控表
4. 再处理 Node 24 告警
5. 最后更新本地 Skill 与仓库文档

这样可以优先完成“可见成功留痕”，同时避免把外部集成、基础设施处理和知识沉淀混在一起造成回归面扩大。
