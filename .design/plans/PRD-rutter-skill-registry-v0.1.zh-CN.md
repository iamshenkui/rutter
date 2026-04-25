# PRD：Rutter Skill Registry 与 Query Layer v0.1

## 简介

Rutter 当前仍以单体 Markdown 文档的方式保存 game-migration 规则。Meta-agent 已经具备自己的原子 skill 注入机制（`meta_agent/skills/core.py`），但两者之间还没有稳定的发现接口：rutter 中编写的 skill 还不能作为一等资产被索引，meta-agent、Claude Code 这类 agent 客户端也无法通过统一协议来查询这些 skill。

本 PRD 的目标，是把 rutter 从静态文档仓库升级为一个**由 git 托管的 skill registry，并提供 MCP 友好的查询层**，从而支持 skill 拆分、索引生成、校验，以及面向 agent 的检索与读取。

Rutter 继续作为 skill 内容与元数据的事实来源。MCP 只承担发现与读取的访问层职责，而不是 skill 内容创作和持久化的承载层。

## 目标

- 提供一种标准 YAML 格式，用于表示与 meta-agent `AtomicSkill` schema 1:1 对齐的原子 skill
- 支持将单体 Markdown skill 拆分为细粒度的 atomic skill family
- 维护一个中心化 registry 索引，记录所有 skill family 的版本、依赖和元数据
- 通过 MCP 友好的只读工具，为 agent 客户端提供稳定的查询接口
- 支持通过 URL 或本地路径将第三方 skill 导入 registry

## 产品定位

- **Rutter registry：** 负责维护 skill 内容、manifest、版本、依赖元数据与校验规则。
- **Rutter query layer：** 通过 MCP 或等价的本地工具适配层，为 agent 暴露检索与读取能力。
- **Meta-agent：** 负责 skill planning、resolution、injection 与运行时选择。
- **Claude Code 及其他 agent：** 消费 skill 搜索与读取接口，但不直接修改 registry 内部状态。

## 用户故事

### US-001：将单体 skill 拆分为 atomic skills
**描述：** 作为 skill 作者，我希望将一个大型 Markdown skill 拆分成多个 YAML skill，以便 meta-agent 能根据任务需求有选择地注入。

**验收标准：**
- [ ] 一个单体 Markdown skill 可以拆分成多个 YAML 文件，每个文件表示一个 `AtomicSkill`
- [ ] 每个 YAML 文件都能通过 rutter skill schema 校验
- [ ] 拆分结果能保留原有 incremental rules 和元数据

### US-002：在中心 registry 中索引 skills
**描述：** 作为 skill 使用者，我希望能通过中心索引浏览可用技能，以便稳定地发现并读取所需 skill。

**验收标准：**
- [ ] `registry/index.yaml` 列出所有 skill family 的名称、版本、描述和标签
- [ ] 每个 skill family 都包含一个 `manifest.yaml`，用于描述其 atomic skills 和依赖关系
- [ ] 该索引同时具备机器可读性和人工可浏览性

### US-003：通过 MCP 查询 skills
**描述：** 作为 agent 客户端，我希望能通过兼容 MCP 的工具查询 rutter，从而在不理解仓库目录结构的情况下搜索和读取相关 skill。

**验收标准：**
- [ ] Rutter 提供只读查询操作，用于列出 family、搜索 skill、读取 manifest 或 atomic skill payload
- [ ] 查询结果包含足够元数据，以便 agent 进行排序或选择
- [ ] 查询层直接基于 registry 作为事实来源，不要求 patch meta-agent 源码文件

### US-004：导入第三方 skills
**描述：** 作为团队负责人，我希望把外部 skill 导入 rutter，以便团队能复用社区或内部共享的 skill。

**验收标准：**
- [ ] `rutter add <url>` 可以从 GitHub 仓库或本地路径导入 skill
- [ ] 导入后的 skill 能通过 rutter schema 校验
- [ ] 导入完成后，skill 会出现在 index 中并可被查询

### US-005：校验 skill registry 完整性
**描述：** 作为 CI 流水线，我希望能校验整个 skill registry，以便在部署前发现损坏或格式错误的 skill。

**验收标准：**
- [ ] `rutter validate` 会检查所有 YAML 文件是否符合 schema
- [ ] 校验结果会报告缺失依赖、重复 ID 和格式错误的规则
- [ ] 校验失败时，CI 以非零状态退出

### US-006：将 rutter 注册为外部 skill source
**描述：** 作为 meta-agent 开发者，我希望把 rutter 挂载为外部 skill source，使运行时注入能力能够演进，而不需要 rutter 去修改 meta-agent 内部实现。

**验收标准：**
- [ ] Meta-agent 可以通过本地路径或仓库 URL 注册一个 rutter source
- [ ] Source 注册不需要修改 `meta_agent/skills/core.py`
- [ ] 在外部 source 加载能力完成前，内置 skills 仍作为 fallback 可用

## 功能需求

- **FR-1：** Rutter 的 atomic skill YAML payload 必须兼容 meta-agent `AtomicSkill` 的运行时字段：`id`、`name`、`description`、`category`、`incremental_rules`、`dependencies`
- **FR-2：** Skill family 以 `registry/<family-name>/<version>/` 的形式命名空间化
- **FR-3：** 每个 skill family 都必须包含 `manifest.yaml`，记录 family 元数据及其 atomic skill 列表
- **FR-4：** `registry/index.yaml` 必须由 manifest 自动生成，不能手工编辑
- **FR-5：** Manifest 元数据必须包含面向查询的字段，例如 family 名称、版本、描述、标签、关键词与别名
- **FR-6：** 第三方 skill 导入必须同时支持 Git URL（`https://github.com/...`）和本地文件系统路径
- **FR-7：** 所有 atomic skill ID 在整个 registry 中必须全局唯一；family 的版本演进不能依赖 patch 既有 ID
- **FR-8：** Skill 之间禁止循环依赖，并且必须在校验阶段检测出来
- **FR-9：** Rutter 必须提供兼容 MCP 的只读工具接口，用于列出、搜索和读取 skills
- **FR-10：** 在相同 registry revision 下，查询结果必须是确定性的
- **FR-11：** 在 v0.1 范围内，Rutter 不得修改 meta-agent 源代码

## 非目标

- 不提供 Web UI 或托管式 registry 服务；rutter 仍保持为基于 git 的文件系统 registry
- 不直接修改 meta-agent 内置 skill 表的运行时状态
- 不支持超出语义化版本字符串之外的复杂版本管理或依赖解析能力
- 不把旧版单体 Markdown 格式继续作为运行时格式；Markdown 仍可作为拆分来源
- v0.1 不通过 MCP 提供写接口，只提供查询接口

## 分阶段交付

### Phase 1：Registry Foundation

- 定义 atomic skill YAML payload schema 和 family manifest schema
- 将 `game-migration` family 拆分并迁移为 registry 资产
- 生成 `registry/index.yaml`
- 实现 `rutter validate`

### Phase 2：Query Layer

- 在 registry 之上暴露 MCP 友好的只读工具
- 支持 list、search、fetch 和依赖检查等操作
- 确保查询结果与生成的 index 和 manifests 保持一致

### Phase 3：External Source Integration

- 扩展 meta-agent，使其可以把 rutter 挂载为外部 skill source
- 允许 meta-agent 在不 patch 源码的情况下解析和注入外部 skills
- 在迁移期间保留 built-in fallback skills

## 设计考量

- **Registry 布局：** 在 `registry/` 下采用扁平 family 命名空间，并在目录层级中引入版本号，允许同一 family 的多个版本共存。
- **Skill ID 约定：** 使用带 family 前缀的 `snake_case`，避免冲突，例如 `game_migration_migrate`。
- **两层 schema：** Manifest 元数据面向 registry 与 query 用例；atomic skill payload 尽量贴近 runtime schema。
- **查询模型：** MCP 返回紧凑元数据用于发现，返回完整 skill payload 用于注入或本地渲染。
- **Resolver 边界：** Rutter 返回候选 skill 与元数据；最终选择和 prompt injection 仍由 meta-agent 负责。

## 技术考量

- Rutter CLI 可使用 Python 脚本实现，结合 `pyyaml` 与 `pydantic` 做 schema 校验
- MCP 支持可以实现为 registry index 与 manifest loader 上的一层轻量适配器
- Meta-agent 应扩展为支持从注册的 source 加载外部 skills，以消除 patch 源码的需求
- Registry index 应通过 pre-commit hook 或 CI 步骤生成，以避免漂移

## MCP 查询接口

第一版兼容 MCP 的查询接口应保持只读，并至少覆盖：

- `list_skill_families`
- `search_skills(query, tags, category, keywords)`
- `get_skill_family(name, version?)`
- `get_skill(skill_id)`
- `get_skill_dependencies(skill_id)`
- `validate_registry()`

## 成功指标

- `game-migration` skill family 已完整迁移为 rutter registry 格式
- agent 客户端能够通过 query layer 发现并读取 `game-migration` skills，而不需要了解仓库路径结构
- `rutter validate` 以零错误通过
- 一个第三方 skill 能在 3 条 CLI 命令内完成导入、索引与查询

## 开放问题

- Rutter CLI 应该作为独立 Python package 发布，还是作为仓库内脚本维护？
- MCP 应该以内置命令 `rutter serve --mcp` 的形式提供，还是作为复用同一 registry 的轻量 companion package？
- Meta-agent 为了消费 rutter，需要的最小 source-registry contract 是什么，才能避免重复实现 resolver 逻辑？
- Rutter v0.1 需要支持的最小 meta-agent 版本是什么？