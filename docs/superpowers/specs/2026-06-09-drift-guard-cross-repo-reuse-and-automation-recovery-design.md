# Drift Guard 跨仓复用与自动化恢复 Design

**Goal:** 将 Dreambuddy-V2 中 vendor 的 `drift-guard` 收敛为跨仓复用 DREAM-AGENT 的 workflow/action 模块；并输出一份“自动化恢复策略”，把主线推进收敛到 GitHub Actions。

**Primary Outcome**
- Dreambuddy-V2 不再维护 `.github/actions/drift-guard/**` 的副本实现
- Dreambuddy-V2 的 `drift-guard` check 仍稳定（branch protection 不漂移）
- DREAM-AGENT 成为 drift-guard 的唯一实现源，并通过 tag 发布稳定版本
- 本地自动化任务的角色被明确：只读巡检 + 受控触发；禁止直接推进主线代码

---

## Background

### 为什么要跨仓复用
- vendor drift-guard 会导致实现分叉与版本漂移，长期维护成本高
- DREAM-AGENT 已经承载协作与自动化治理能力，适合作为模块中心

### 当前约束
- 需要保持 branch protection 的 required check 名称不变
- drift-guard 必须 fail-closed（缺配置、越界路径、无法 diff、缺必读文档等均 BLOCK）
- 主线推进必须从本地调度收敛到 GitHub Actions（PR + required checks）

---

## Non-Goals
- 不引入大模型判断（不接 LLM 判定质量）
- 不修改现有 `lifecycle-guard` 规则本身，仅通过协议/分支/PR 形态满足门禁
- 不在本阶段重构所有 workflow，仅完成 drift-guard 与受控触发的主干化

---

## Terminology

- **Drift Guard**：确定性门禁（路径范围、必读文档存在性与哈希、diff 可计算等），输出 `drift_report.json`/`drift_report.md`
- **Change Class**：变更分类（`mainline`/`integration`/`infra`），决定允许的模块范围
- **Modules**：功能模块路径集合（Dreambuddy-V2：`product_hub`/`trading`/`frontend_gateway`/`ci`）
- **Controlled Dispatch**：受控触发，只在门禁 PASS 时触发 allowlist workflow

---

## Target Architecture

### 1) DREAM-AGENT：模块中心（Source of Truth）

**提供内容**
- Composite action：`.github/actions/drift-guard/**`
- Reusable workflow（新增）：`.github/workflows/reusable-drift-guard.yml`
  - `on: workflow_call`
  - 内部调用 composite action
  - 负责产物上传（artifact）
  - 负责 PR 场景 BLOCK 回帖 `drift_report.md`

**版本策略（选定）**
- 使用 Git tag 发布：`drift-guard/v0.1.0`、`drift-guard/v0.1.1` …
- Dreambuddy-V2 只允许引用 tag（禁止 `@main`），防止无意升级导致门禁漂移

### 2) Dreambuddy-V2：薄壳接入（Stable Check Name）

**保留**
- `.workbuddy/drift-guard.json`：本仓模块/变更分类配置
- `.github/workflows/drift-guard.yml`：作为“稳定 check 名称”的薄壳入口

**删除**
- `.github/actions/drift-guard/**`（vendor copy）

**变更**
- Dreambuddy-V2 的 `.github/workflows/drift-guard.yml` 改为：
  - job 使用 `uses: yunya1991/DREAM-AGENT/.github/workflows/reusable-drift-guard.yml@drift-guard/v0.1.0`
  - 通过 inputs 传入：`change_class`、`config_path=.workbuddy/drift-guard.json`
  - PR diff 范围统一为 `origin/main..HEAD`（与现有实现一致）

### 3) 保持与 branch protection 对齐
- required checks 固定：
  - `drift-guard`
  - `lifecycle-guard`
- 只允许 PR 合并（禁止直接 push main）

---

## Drift Guard Contract (跨仓复用需要稳定的接口)

### Inputs (reusable workflow)
- `change_class`：`mainline|integration|infra`（default: `mainline`）
- `config_path`：default `.workbuddy/drift-guard.json`
- `comment_on_pr_block`：default `true`

### Outputs / Artifacts
- artifact name：`drift-guard-report-${{ github.run_id }}`
- files：
  - `drift_report.json`
  - `drift_report.md`

### Fail-Closed Rules (reason_codes)
- `CONFIG_MISSING` / `CONFIG_INVALID` / `CONFIG_UNSUPPORTED_FORMAT`
- `REQUIRED_DOC_MISSING`
- `UNKNOWN_PATH`
- `PATH_OUT_OF_SCOPE`
- `GIT_DIFF_FAILED`
- `MISSING_SHA`（仅在强制要求 sha 的模式下；当前设计使用 `origin/main..HEAD` 避免该问题）

---

## Automation Recovery Strategy

### 允许恢复（但必须“只读/受控触发”）
**本地自动化可以恢复的类型**
- 巡检型：只读扫描（git 状态/日志/产物目录增量/监控指标读取），输出报告到固定位置或发 GitHub comment/issue
- 触发型：仅执行 `gh workflow run` 触发 DREAM-AGENT 的 allowlist workflows；不得写仓库文件、不得 push

**推荐恢复方式**
- 统一把本地自动化的“执行”变成：
  - 生成 inputs（确定性 JSON）
  - 调用 GitHub Actions workflow_dispatch
  - 记录 run url / artifact url 作为留痕

### 永久下线（或保持长期 Paused）
**一律不允许再恢复的类型**
- 任意“本地定时会话直接推进主线代码”的任务（会与 main 分支保护冲突，且会制造脏工作区与不可追溯改动）
- 旧 PR9 专用 developer/validator/governance 定时链路（除非明确要继续维护 dreambuddy-v1 的 PR9）

### 你当前 list 的本地任务建议
- `Dream-Agent Hybrid Dispatch Executor`：保留为 Paused；若要恢复，改造成“只触发 controlled-dispatch + 只读巡检”
- `dream-acceptance-hourly`：可恢复为只读验收巡检，但需要把目标 repo/URL/基线更新到当前主线（避免引用过时路径）
- `Protocol Ledger Agent (dreambuddy-v1)`：与主线无关，建议长期 Paused
- `PR9 Developer/Validator/Governance`：建议长期 Paused

---

## Return to Mainline (自动化+GitHub+飞书+监控)

### 主线闭环建议（第一条）
1. Dreambuddy-V2 PR 合入（业务/中台/联通）
2. drift-guard + lifecycle-guard 作为强门禁
3. controlled-dispatch 触发：
   - 飞书写回（审批/多维表格/OKR）
   - 监控巡检（失败告警、健康度）
   - 产物归档/索引更新（可验证产物落盘）
4. 产出“可审计证据链”：PR + checks + artifacts + 飞书写回记录

### 产出约束
- 所有“推进动作”必须以 GitHub 为主链留痕（PR/Checks/Artifacts）
- 飞书为一级能力，但以“可回填”方式接入：失败不阻断 GitHub 主链

---

## Rollout Plan (高层步骤)

1. DREAM-AGENT 新增 `reusable-drift-guard.yml`
2. 打 tag：`drift-guard/v0.1.0`
3. Dreambuddy-V2 drift-guard workflow 切到跨仓 reusable workflow（pin tag）
4. 删除 Dreambuddy-V2 vendor action 目录
5. 验证：创建一个越界 PR，确认 drift-guard BLOCK 且回帖报告
6. 写入“自动化恢复策略”到 DREAM-AGENT docs（同时在 Dreambuddy-V2 引用/链接）

