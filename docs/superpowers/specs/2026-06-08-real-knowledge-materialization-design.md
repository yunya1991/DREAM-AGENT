---
id: REAL-KNOWLEDGE-MATERIALIZATION-DESIGN
type: design
owner: governance-agent
depends:
  - FEISHU-COLLABORATION-SYSTEM-DESIGN
  - KNOWLEDGE-OPS-SKILL-DESIGN
  - APPROVAL-POLLING-WRITEBACK-DESIGN
version: 1
last_verified: 2026-06-08
---

# 真实知识库构建设计

> 仓库：`DREAM-AGENT`
> 日期：`2026-06-08`
> 状态：draft
> 目标：新增一条独立的真实知识物化 workflow，只消费 `approval / polling` 产物，把审批与回写结果稳定沉淀为真实 `runbook + handoff` 双文档，并同步更新索引，形成最小真实知识闭环。

## 1. 背景

当前主线已经完成了三类关键收口：

- `real approval trigger` 已完成真实审批实例创建验证
- `approval polling + writeback` 已完成 workflow、runbook、测试与真实 Base 写回验证
- `Knowledge-Ops SKILL` 已具备 intake、pathing、validation、check、materialize、verify 的最小契约骨架

其中，第三段的真实验证已经确认两件事实：

- 飞书真实审批实例已创建成功，实例码为 `7ED36C95-AACF-4921-84E1-3220557153E6`
- 真实 Base 写回已成功落地到：
  - task 表 `自动化任务监控`
  - goal 表 `目标推进表`

同时也暴露出一个现实差异：

- 本地以当前用户身份再次调用审批实例查询时，缺少 `approval:instance:read` scope

这说明当前真正缺失的不是“有没有知识治理设计”，而是：

- 一条独立、真实、可重跑、可索引的知识物化主线

## 2. 问题定义

本设计主要解决以下四类问题：

### 2.1 知识治理当前仍停留在“骨架已齐，真实落盘未闭环”

仓库已经具备：

- `docs/feishu-collab/runbooks/`
- `docs/feishu-collab/handoffs/`
- `RUNBOOK_INDEX.md`
- `HANDOFF_INDEX.md`
- 知识模板与路由规则

但当前 `Knowledge-Ops` 的 materialize 更偏“结果对象产出”，还没有把前一阶段真实产物稳定写成真实知识资产。

### 2.2 第三段产物仍停留在证据层

第三段已经能稳定输出：

- 审批侧证据
- 协作侧回写证据
- workflow summary

但这些结果仍主要停留在 JSON artifact 和 Base 字段里，尚未变成：

- operator 可直接阅读的 runbook
- 可交接的 handoff

### 2.3 如果把知识物化继续塞回审批链，职责会再次混乱

如果直接把知识落盘并回 `approval-polling-writeback`：

- 审批链会变成长链
- 失败定位会变差
- operator 会更难区分“状态写回失败”与“知识沉淀失败”

因此第四段需要独立主线，而不是继续拉长第三段。

### 2.4 真实知识资产必须支持重跑与索引对齐

知识物化不是一次性动作。后续审批状态从 `pending` 变为 `approved/rejected` 时，必须允许：

- 重写已有 runbook
- 重写已有 handoff
- 去重更新索引

否则知识资产会迅速碎片化。

## 3. 设计目标

本设计的目标如下：

- 新增独立 `knowledge-materialization` workflow
- 默认只消费 `approval / polling` 产物
- 默认生成 `runbook + handoff` 双文档
- 真正落盘到知识目录，而不是只返回结果对象
- 真正更新 `RUNBOOK_INDEX.md` 与 `HANDOFF_INDEX.md`
- 明确成功/失败语义与重跑规则

成功标准：

- 存在正式的知识物化 workflow 设计
- 能清晰说明与第三段审批链的输入输出边界
- 能稳定定义双文档落盘与索引更新顺序
- 能定义 `knowledge_materialization_result` 与失败保留策略
- 能作为下一步实施计划的统一设计基线

## 4. 范围与非目标

### 4.1 本设计覆盖

- 独立 knowledge workflow
- 只消费 `approval_status_result` 与 `approval_writeback_result`
- `runbook + handoff` 双文档真实落盘
- `RUNBOOK_INDEX.md` 与 `HANDOFF_INDEX.md` 更新
- artifact、summary 与失败证据

### 4.2 本设计不覆盖

- 审批实例创建
- 审批状态查询
- Base 回写
- OKR / Bitable / GitHub Sync 全量知识输入
- 通用 registry-driven 多来源知识入口
- 知识面板、知识搜索 UI

v1 的重点是：

- 先把审批主线的真实结果沉淀成真实知识资产

而不是一次性做成全量知识平台。

## 5. 核心原则

### 5.1 独立主线原则

知识物化必须使用独立 workflow，不并回审批长链。

### 5.2 双文档原则

v1 每次执行默认生成：

- 一份 runbook
- 一份 handoff

不采用“先只写一份聚合文档”的过渡方案。

### 5.3 真实落盘原则

materialize 不再停留在结果对象层，必须真正写文件、更新索引、保留结果证据。

### 5.4 索引一致原则

索引更新只能发生在文档成功落盘之后，避免空引用。

### 5.5 可重跑原则

同一个 `task_id` 再次物化时，应覆盖已有文档并去重更新索引，而不是制造重复资产。

## 6. 推荐方案

推荐采用：

- `方案 A：独立 knowledge workflow，消费 approval/polling artifacts`

其核心做法是：

- 新增独立 `knowledge-materialization.yml`
- 以第三段产物为唯一正式输入
- 真实生成 runbook 与 handoff Markdown
- 同步更新 runbook/handoff 索引
- 输出 `knowledge_materialization_result.json`

不推荐：

- 并入 `approval-polling-writeback.yml`
- 一次性做成多来源 registry 驱动入口
- 只生成单一聚合文档

## 7. 主从关系与边界

### 7.1 第三段职责

第三段负责：

- 创建审批状态证据
- 创建 Base 回写证据
- 保证协作状态一致

### 7.2 第四段职责

第四段负责：

- 消费第三段证据
- 生成可读 runbook
- 生成可交接 handoff
- 更新索引
- 保留知识物化证据

### 7.3 明确不回头

第四段不重新：

- 发起审批
- 查询审批实例
- 回写 Base

它只消费上游已稳定下来的结果。

## 8. 对象模型

### 8.1 `runbook_materialization_result`

最少包含：

- `target_path`
- `title`
- `source_instance_code`
- `source_task_id`
- `write_status`
- `index_status`

### 8.2 `handoff_materialization_result`

最少包含：

- `target_path`
- `title`
- `source_goal_id`
- `source_task_id`
- `write_status`
- `index_status`

### 8.3 `knowledge_materialization_result`

最少包含：

- `runbook`
- `handoff`
- `materialization_status`
- `evidence_refs`
- `failure_reason`

职责：

- 汇总单文档执行状态
- 表达整次知识构建是否完成
- 保留局部成功与失败证据

## 9. 命名与落盘规则

### 9.1 文档命名

推荐固定命名：

- runbook：`approval-<task_id>-runbook.md`
- handoff：`approval-<task_id>-handoff.md`

原因：

- 来源清楚
- 稳定可重跑
- 不依赖手工命名

### 9.2 落盘目录

固定使用现有目录：

- `docs/feishu-collab/runbooks/`
- `docs/feishu-collab/handoffs/`

### 9.3 索引文件

固定更新：

- `docs/feishu-collab/RUNBOOK_INDEX.md`
- `docs/feishu-collab/HANDOFF_INDEX.md`

## 10. 文档内容来源

### 10.1 Runbook 内容来源

主要吸收：

- `approval_status_result`
- `approval_writeback_result`
- workflow summary

runbook 重点回答：

- 发生了什么
- 审批实例是什么
- 当前协作状态是什么
- 如果失败该如何排查

### 10.2 Handoff 内容来源

主要吸收：

- 当前状态
- 已完成工作
- 剩余工作
- 下一步动作
- 风险与依赖
- 证据链接

handoff 重点回答：

- 现在交给下一个操作者时，需要知道什么

## 11. Workflow 结构

### 11.1 新增独立 workflow

新增独立 workflow，例如：

- `.github/workflows/knowledge-materialization.yml`

触发方式：

- `workflow_dispatch`

### 11.2 Job 结构

v1 建议保持单 job，顺序执行：

1. `resolve inputs`
2. `build knowledge payload`
3. `materialize runbook`
4. `materialize handoff`
5. `update indexes`
6. `render summary + upload artifacts`

不在本轮引入多 job 编排。

## 12. 输入模型

v1 最小输入集合建议固定为：

- `approval_status_result_json`
- `approval_writeback_result_json`
- `materialization_context_json`

其中：

- `approval_status_result_json` 提供审批状态证据
- `approval_writeback_result_json` 提供协作写回证据
- `materialization_context_json` 提供标题、来源 workflow、操作者说明等补充上下文

v1 不要求 workflow 自己去下载上游 artifact。

## 13. 结果模型

### 13.1 文档结果

最少输出：

- 生成后的 runbook 文件
- 生成后的 handoff 文件

### 13.2 Artifact

最小 artifact 集合建议固定为：

- `knowledge_materialization_result.json`
- runbook 文件副本
- handoff 文件副本

### 13.3 Job Summary

summary 至少展示：

- `task_id`
- `goal_id`
- `approval_instance_code`
- `runbook_path`
- `handoff_path`
- `materialization_status`
- `index_update_status`

### 13.4 成功语义

workflow 成功条件为：

- runbook 成功落盘
- handoff 成功落盘
- `RUNBOOK_INDEX.md` 成功更新
- `HANDOFF_INDEX.md` 成功更新

### 13.5 失败语义

workflow 失败条件包括：

- 任一文档落盘失败
- 任一索引更新失败

即使失败，也必须：

- 保留已生成文档
- 上传 artifact
- 输出 summary

## 14. 索引更新顺序

固定顺序建议为：

1. 写 runbook
2. 写 handoff
3. 更新 `RUNBOOK_INDEX.md`
4. 更新 `HANDOFF_INDEX.md`
5. 写 `knowledge_materialization_result`

原因：

- 避免索引先更新、文档还未落盘
- 避免 handoff 成功但 runbook 失败时出现半索引状态

## 15. 最小失败恢复策略

### 15.1 Runbook 落盘失败

处理方式：

- 直接停止
- 不继续 handoff
- 输出失败证据

### 15.2 Handoff 落盘失败

处理方式：

- 保留已成功的 runbook
- 不更新 `HANDOFF_INDEX.md`
- 总结果判失败

### 15.3 索引更新失败

处理方式：

- 保留已落盘文档
- summary 与结果对象显式标出索引未同步
- 总结果判失败

## 16. 可重跑策略

同一个 `task_id` 再次执行时：

- 覆盖已有 runbook/handoff 内容
- 索引更新去重
- 保持路径稳定

不采用“每次生成新文件”的策略。

## 17. 适配器边界

### 17.1 Payload Builder

负责：

- 读取第三段结果
- 归一化知识输入
- 生成 runbook/handoff 的内容草案

### 17.2 Runbook Materializer

负责：

- 生成 runbook 正文
- 写入目标路径

### 17.3 Handoff Materializer

负责：

- 生成 handoff 正文
- 写入目标路径

### 17.4 Index Updater

负责：

- 更新 `RUNBOOK_INDEX.md`
- 更新 `HANDOFF_INDEX.md`
- 去重并保持索引一致性

### 17.5 Summary Adapter

负责：

- 汇总文档落盘和索引更新结果
- 输出 Job Summary
- 计算 workflow exit code

## 18. 测试策略

建议固定四层测试：

### 18.1 Materialization Runner Tests

验证：

- runbook 结果结构
- handoff 结果结构
- 总结果对象结构

### 18.2 Index Updater Tests

验证：

- 索引插入
- 索引去重
- 索引更新顺序

### 18.3 Workflow Contract Tests

验证：

- workflow 文件存在
- inputs 完整
- helper 调用链完整
- artifact 上传存在

### 18.4 Docs / Index End-to-End Tests

验证：

- 文档真实落盘
- 索引真实可发现
- 重跑不会生成重复索引项

## 19. 风险与应对

### 19.1 风险：又退化成模拟 materialize

应对：

- v1 明确要求真实文件落盘
- 不接受只返回结果对象

### 19.2 风险：审批链和知识链重新耦合

应对：

- 使用独立 workflow
- 只消费第三段产物，不回头查审批和回写 Base

### 19.3 风险：索引与文档继续脱节

应对：

- 固定落盘后更新索引
- 固定索引失败即整体失败

### 19.4 风险：同一 task 重跑产生重复知识资产

应对：

- 稳定文件命名
- 索引去重
- 覆盖式更新

## 20. 验收标准

本设计完成后，应满足以下验收标准：

- 能清晰说明第四段与第三段的职责边界
- 能定义独立 knowledge workflow 的输入、输出与顺序
- 能定义 `runbook + handoff` 双文档真实落盘规则
- 能定义索引更新顺序、失败恢复与可重跑策略
- 能定义 artifact、summary 与测试策略
- 能作为下一步 implementation plan 的统一设计基线
