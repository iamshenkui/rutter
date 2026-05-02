# PRD：Rutter Skill Accumulation Loop v0.1

## 简介

本 PRD 只定义 `rutter` 在 skill accumulation loop 中负责的部分：提供 proposal review surface、独立 validator，以及将已接受 proposal 转换为 registry patch 或 promotion instructions 的工具。

`rutter` 不负责运行态证据提取，也不负责多 run issue extraction；这些由 `meta-agent` 提供。

## 目标

- 为候选 skill 增量提供仓库内、可审阅、可版本化的 review surface
- 提供独立于 `meta-agent` 的 proposal schema validation
- 保持 live `registry/` 只通过人工审核后的 promotion 进入变更
- 让 proposal validation 与 promotion tooling 能在 CI 或本地独立运行

## 非目标

- 不在 `rutter` 内实现 `.state` 扫描或 issue extraction
- 不让 proposal 直接覆盖 live `registry/`
- 不把 review surface 混入 live `registry/`
- 不依赖 `Quartermaster` 或常驻服务

## 产品边界

- `rutter` 拥有 `SkillProposalBundle@v1` schema、proposal validation、review surface 与 promotion tooling
- `rutter` validator 必须能在没有 `meta-agent` 的情况下独立校验 proposal bundle
- `rutter` 接收来自 `meta-agent` 的 proposal bundles，但不依赖其内部实现

## 用户故事

### US-001：提供 proposal review surface

**描述：** 作为 skill 维护者，我希望 Rutter 仓库里有一个专门的 proposal review surface，用来保存可审阅的 skill proposals，而不是直接改 live registry。

**验收标准：**
- [ ] proposal bundles 存放在专门目录下，例如 `proposals/`
- [ ] review surface 可提交、可审阅、可跨机器同步
- [ ] review surface 不与 live `registry/` 混淆

### US-002：独立校验 proposal bundles

**描述：** 作为维护者，我希望 `rutter validate-proposals` 能独立校验 proposal bundles 的 shape、枚举值和 registry 引用合法性。

**验收标准：**
- [ ] YAML root 必须是 mapping
- [ ] `schema_version` 必须为 `1`
- [ ] `status`、`action`、`target_family`、`supporting_issues` 等字段必须合法
- [ ] `target_family` 必须存在于当前 registry
- [ ] `action=update_existing_skill` 时 `target_skill_id` 必须存在
- [ ] `action=create_new_skill` 时 `new_skill_id` 必须非空且不得与现有 skill 冲突

### US-003：生成人工审阅导向的 promotion 输出

**描述：** 作为仓库维护者，我希望 `rutter promote-proposal` 把已接受 proposal 转换为 registry patch 或 human-readable instructions，而不是自动写 live registry。

**验收标准：**
- [ ] 只处理 `accepted` proposal
- [ ] 默认输出 patch 或 instructions
- [ ] v0.1 不自动写 live `registry/`
- [ ] 输出可被人工审核并纳入正常提交流程

### US-004：通过 fixtures 固化跨仓库契约

**描述：** 作为开发者，我希望 Rutter 侧有 valid/invalid proposal fixtures 和 focused tests，确保与 `meta-agent` 的输出契约稳定。

**验收标准：**
- [ ] 提供 valid/invalid proposal fixtures
- [ ] validator 在没有 `meta-agent` 依赖的情况下可单独测试
- [ ] contract tests 覆盖 schema、枚举值、family 引用与 skill id 冲突

## 功能需求

- **FR-1：** Rutter 必须提供专用 proposal review surface，例如 `proposals/`
- **FR-2：** Rutter 必须提供 `validate-proposals` 命令，并支持本地与 CI 独立运行
- **FR-3：** proposal schema 必须使用 `SkillProposalBundle@v1`
- **FR-4：** validator 必须校验 `schema_version`、`status`、`action`、`target_family`、`supporting_issues`、`evidence_refs` 等必填字段
- **FR-5：** validator 必须校验 registry family / skill 引用合法性
- **FR-6：** Rutter 必须提供 `promote-proposal` 命令，将 accepted proposal 转换为 patch 或 instructions
- **FR-7：** promotion 在 v0.1 不得自动写入 live `registry/`

## 命令面

### `rutter validate-proposals`

```text
rutter validate-proposals \
  --path <path-to-rutter> \
  [--proposal-dir proposals] \
  [--json]
```

### `rutter promote-proposal`

```text
rutter promote-proposal \
  --path <path-to-rutter> \
  --bundle-id <bundle_id> \
  --dry-run
```

## 共享契约依赖

- 输入 proposal bundle 使用 `SkillProposalBundle@v1`
- `schema_version` 固定为 `1`
- 允许的 `status` 为 `proposed`、`needs_revision`、`accepted`、`rejected`、`promoted`
- 允许的 `action` 为 `create_new_skill`、`update_existing_skill`、`split_existing_skill`、`deprecate_skill`、`metadata_only`、`no_action`
- `EvidenceRef` shape 与 `meta-agent` 输出保持兼容

## 成功标准

- `rutter` 的拆解结果只包含 review surface、validator、promotion tooling 与 fixtures/tests
- 不再把 `.state` 扫描、taxonomy adapter、run-to-session linking 当作 `rutter` 主任务
- 从 split PRD 导入后，任务列表不再出现 `Phase`、`Slice`、阻塞说明等非可执行项