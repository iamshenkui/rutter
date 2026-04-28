# PRD：Rutter Skill Accumulation Loop v0.1

## 简介

Rutter 现在已经成为长期 skill 内容的事实来源，但 Portolan 仍然缺少一个可落地的闭环，无法把真实执行中的失败持续沉淀为新 skill 或 skill 更新。长期目标中的架构会包含 checker 输出、reviewer verdict，以及 phase 级编排，但当前 `Quartermaster` 还不够成熟，暂时不适合作为主循环锚点。

因此，下一阶段应先聚焦一个更小但可用的闭环：

- 从 `meta-agent` 收集稳定的执行证据
- 用便宜模型总结重复出现的领域问题
- 用更强模型将这些问题整理成候选 skill 增量
- 在不直接修改 live registry 的前提下，把结果写入一个可审阅的 proposal surface

本文档定义的就是这条第一版 skill 积累闭环。

## 目标

- 从真实运行中捕获重复出现的领域失败模式
- 聚焦 skill 缺口或 skill 质量不足，而不是泛化的模型能力打分
- 支持使用低成本模型（如 MiniMax）做大规模初筛
- 支持使用更强模型（如 DeepSeek Pro）做高质量归纳与整理
- 在运行时证据与 registry 变更之间保留人工审阅
- 通过将工件保存在仓库内，使这条闭环能够跨机器继续开发

## 非目标

- 第一版不自动修改 live `registry/`
- v0.1 不依赖 `Quartermaster`
- 不试图给通用工具调用能力或底层编码能力打分
- 不要求捕获每一个 token 级或 tool 级的 agent 步骤
- 第一版不引入托管服务或常驻 daemon

## 产品定位

- **meta-agent：** 负责 run 执行、任务拆解与证据采集
- **Claude / 本地 worker 轨迹：** 在可用时提供更丰富的原始执行轨迹证据
- **Rutter：** 负责保存长期 skill proposal、校验逻辑，以及最终进入 live registry 的 promotion 流程
- **人工操作者：** 审核、编辑或拒绝候选 skill 更新

## 问题定义

最有价值的运行时学习信号，并不是泛化的编码失败，而是反复出现的领域缺口，例如：

- UI 迁移工作不断退化成通用网页布局
- 本应 source-first 的 Unity 资源分析被跳过
- 一个大型迁移任务在错误层级被拆解
- 验收标准遗漏了关键领域检查

当前 `.state` 中的工件已经足够支撑 run 级别的 reflection，但还不足以捕获 worker 的完整推理路径。同时，机器上又确实存在 Claude 本地历史，可以在条件允许时用于 richer evidence。

因此，这条闭环需要同时结合：

1. 来自 `meta-agent` 的稳定结构化 run 证据
2. 来自本地 Claude history 的可选增强型 worker 轨迹证据
3. Rutter 内部一个安全保存候选 skill 增量的 proposal surface

## 用户故事

### US-001：用低成本方式总结重复出现的领域失败
**描述：** 作为操作者，我希望用一个便宜模型扫描大量已完成的 runs，并归并重复出现的领域失败，以便尽早发现缺失的 skills。

**验收标准：**
- [ ] 系统能够读取 `runs.jsonl`、`decisions.jsonl` 与 `progress/log.jsonl`
- [ ] 输出为结构化 issue record，而不是只有自由文本总结
- [ ] issue 会被归类为与领域相关的类别，例如 `missing_domain_skill`、`needs_phase_split`、`weak_acceptance_contract`

### US-002：将 issues 整理为 skill proposals
**描述：** 作为 skill 作者，我希望用一个更强的模型把聚合后的 issues 转成候选 skill 新增或更新，从而把有价值的经验沉淀到 rutter。

**验收标准：**
- [ ] consolidation 步骤可以消费多条 issue record，并输出 proposal bundles
- [ ] proposal bundle 会标明目标 skill family 与建议动作
- [ ] 输出结果可供审阅，不会直接覆盖 live registry

### US-003：在可能时保留本地轨迹证据
**描述：** 作为操作者，我希望当本地 Claude history 能可靠关联到某次 run 时，这条闭环可以利用这些轨迹，从而更完整地解释领域失败。

**验收标准：**
- [ ] 设计支持将 `meta-agent` run ID 与本地 Claude session 关联起来
- [ ] 即便没有轨迹数据，闭环也不会中断
- [ ] 第一版实现只依赖 `.state` 数据也能运行

### US-004：支持跨机器继续开发
**描述：** 作为开发者，我希望把 plan 和拟议的 artifact shape 存进仓库里，这样换机器时也能继续实现，而不用重新回忆设计细节。

**验收标准：**
- [ ] 仓库内包含该闭环的设计文档
- [ ] 文档明确记录 scope、阶段、artifact shapes 与后续步骤
- [ ] 即使没有聊天记录，也足以继续实现

## 功能需求

- **FR-1：** 第一版闭环必须使用 `meta-agent` 的稳定 run 边界工件，尤其是 `runs.jsonl`、`decisions.jsonl` 与 `progress/log.jsonl`
- **FR-2：** 当存在可靠的 run-to-session link 时，闭环可以选择性地用本地 Claude session history 增强证据
- **FR-3：** 便宜模型的提取步骤必须输出结构化 issue records，而不是只产出 Markdown 总结
- **FR-4：** 结构化 issues 至少要区分这些类别：`missing_domain_skill`、`needs_phase_split`、`weak_acceptance_contract`、`checker_reviewer_gap`、`wrong_routing_or_context`
- **FR-5：** 强模型 consolidation 步骤必须输出可审阅的 proposal bundles，而不是直接修改 rutter registry
- **FR-6：** Proposal bundle 必须包含目标 family、建议动作、理由、证据引用，以及候选规则或元数据变更
- **FR-7：** Rutter 必须将 proposal bundles 存放在专门的 review surface 下，例如 `proposals/` 或 `registry_drafts/`
- **FR-8：** 从 proposal promotion 到 live registry 的动作，在 v0.1 中仍必须保留人工审阅
- **FR-9：** 这条闭环必须优先学习领域问题和拆解问题，而不是泛化的模型性能分数

## 证据来源

### 最小可行证据

- `meta-agent/.state/runs.jsonl`
- `meta-agent/.state/decisions.jsonl`
- `meta-agent/.state/progress/log.jsonl`

### 可选的增强证据

- `~/.claude/` 下的本地 Claude history
- 如果 `meta-agent` 之后显式记录 session pointer，则可读取 run-specific worker outputs

## 建议的 Artifact Shapes

### Structured issue record

```json
{
  "issue_id": "traj-20260429-001",
  "source": "meta-agent",
  "repo": "DDGC_newArch",
  "task_ids": ["US-101", "US-118"],
  "run_ids": ["run-a", "run-b"],
  "category": "missing_domain_skill",
  "summary": "UI migration repeatedly degraded into generic web layout",
  "evidence": [
    "decision=retry",
    "risk=visual fidelity regression",
    "failure_summary=layout drift"
  ],
  "candidate_skills": [
    "game_migration_ui_product_sense",
    "game_migration_unity_ui_recon"
  ],
  "confidence": 0.82
}
```

### Proposal bundle

```json
{
  "bundle_id": "skill-feedback-20260429-01",
  "target_family": "game-migration",
  "action": "update_existing_skill",
  "target_skill_id": "game_migration_ui_product_sense",
  "summary": "Strengthen UI migration review rules for game-screen fidelity",
  "why_now": "Repeated failure across multiple DDGC migration phases",
  "recommended_rules": [
    "Reject generic dashboard composition for game town screens",
    "Require landscape viewport verification for core loops"
  ],
  "supporting_issues": [
    "traj-20260429-001",
    "traj-20260429-004"
  ]
}
```

## 建议的工作流

### Phase 1：低成本提取

- 使用低成本模型（如 MiniMax）扫描新增或变化的运行时证据
- 产出标准化 issue records
- 对高度相似的 issues 进行去重

### Phase 2：强模型归纳

- 使用更强模型（如 DeepSeek Pro）处理 issue 集合
- 按 family、skill gap、decomposition gap 或 acceptance gap 分组
- 生成人工可审阅的 proposal bundles

### Phase 3：在 rutter 中保存 proposals

- 将 proposal bundles 写入可审阅的仓库 surface
- 用一个简单 CLI 校验 shape 和必填字段
- 通过 git 版本化 proposal，方便讨论和编辑

### Phase 4：人工 promotion

- 审核被接受的 proposals
- 将其转换为 registry 更新
- 重新生成 `registry/index.yaml`
- 在需要时更新 family 文档与 changelog

## 近期开发计划

### Slice A：meta-agent 证据导出

- 在 `meta-agent` 中增加 `reflect-skills` 命令
- 只读取稳定的 `.state` 工件
- 输出机器可读的 issue JSONL 文件

### Slice B：run-to-session linking

- 扩展 `meta-agent`，在可用时记录 worker session pointer
- 使后续能够用本地 Claude history 增强某次 run

### Slice C：rutter proposal surface

- 增加 `proposals/` 或 `registry_drafts/`
- 为 proposal bundles 定义一个小型 schema
- 增加 `rutter validate-proposals`

### Slice D：promotion tooling

- 增加一个辅助命令，把已接受的 proposal 转成 family 更新补丁
- live registry 的最终修改仍保持人工审阅

## 换机继续开发说明

在新机器上，按这个顺序继续：

1. Bootstrap Portolan 并初始化 submodules
2. 以 editable 方式安装 `meta-agent` 和 `rutter`
3. 从 `Slice A: meta-agent 证据导出` 开始
4. 在 `Quartermaster` contract 和 reviewer surface 更稳定之前，不把它接入主循环
5. 第一版实现始终只聚焦领域 skill 缺口和 phase 拆解问题

## 开放问题

- 将 `meta-agent` 的某次 run 与本地 Claude session 关联起来，最小可靠 key 应该是什么？
- Proposal bundles 应优先放在 `rutter/proposals/`，还是先放在 `.design/` 下？
- 拆解问题应转化为 skill proposal、planner policy proposal，还是两者都要？
- 当 `Quartermaster` 成熟后，`checker_reviewer_gap` 是否应该成为一个权重高于普通 runtime failure 的一级 issue category？