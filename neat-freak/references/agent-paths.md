# Claude / Codex 路径、加载和体量速查

平台机制会变。先探测当前环境和本机规则；涉及写入或尺寸上限时，优先核对当前官方文档或本机工具输出，不把这张表当永远不变的事实。

## 通用原则

- 区分三类文件：人工维护的规则、Agent 自动记忆、机器生成的历史/索引。它们不能共用同一套写入规则。
- `MEMORY.md` 只是文件名，不代表跨平台语义相同。尺寸阈值必须绑定平台和文件类型。
- 规则真身可能是 CLAUDE.md、AGENTS.md、override、导入或软链；以当前工作空间声明和实际加载链为准。
- 发现多个平台目录不等于每个平台都在使用。只审当前运行平台和用户明确纳入的安装面。

## Claude Code

| 用途 | 常见路径 / 规则 |
|---|---|
| 用户指令 | `~/.claude/CLAUDE.md` |
| 项目指令 | `./CLAUDE.md`、`./.claude/CLAUDE.md`、`CLAUDE.local.md` |
| 路径规则 | `.claude/rules/**/*.md` |
| 自动记忆 | `~/.claude/projects/<project>/memory/` |
| 自动记忆索引 | 上述目录的 `MEMORY.md` |
| Skills | `~/.claude/skills/<name>/SKILL.md` 或项目 `.claude/skills/` |

当前官方口径：

- CLAUDE.md 全量加载，但建议目标少于约 200 行；越长越消耗注意力并降低遵守度。这是质量预算，不是硬截断线。
- Claude 自动记忆 `MEMORY.md` 在会话启动时只加载前 200 行或 25KB（先到者）；主题文件按需读取。这个硬限制只属于 Claude 自动记忆，不适用于 Codex 生成记忆。
- Claude 原生读 CLAUDE.md。已有 AGENTS.md 的项目可用导入或软链同源；方向由项目规则决定，不擅自翻转。

## OpenAI Codex

| 用途 | 常见路径 / 规则 |
|---|---|
| Codex home | `$CODEX_HOME`，默认 `~/.codex` |
| 全局指令 | `$CODEX_HOME/AGENTS.override.md`，不存在时读 `AGENTS.md` |
| 项目指令 | 从项目根到当前目录逐级找 `AGENTS.override.md`、`AGENTS.md`、配置的 fallback |
| 全局 Skills | `$CODEX_HOME/skills/<name>/SKILL.md` |
| 项目 Skills | 项目 `.codex/skills/<name>/`（以当前 Codex 版本和环境为准） |

当前官方口径：项目指令链合并后默认最多 32KiB，由 `project_doc_max_bytes` 控制；越靠近当前目录的指令越晚加载。检查 override 和 fallback，不能只找根目录 AGENTS.md。

某些 Codex 环境还提供 `~/.codex/memories/`、rollout summaries 或 Chronicle 派生索引。这类文件可能由宿主管线生成：

- 先读当前环境给出的 memory instructions；没有明确授权时只读。
- 不直接改生成的 `MEMORY.md`、`memory_summary.md`、`raw_memories.md` 或 rollout summary。
- 用户明确要求更新记忆且环境允许时，只使用该 Codex 环境规定的 correction input，或通过官方 `/memories`、设置和 `memories.*` 配置控制生成与使用，再等待宿主 consolidation；不要自设文件尺寸目标、compact candidate 或项目级生成记忆门禁。

发现 `TEAM_GUIDE.md`、`.agents.md` 等文件时，只有它们出现在 Codex fallback 配置中才把它们当指令文件。

## 其他 Agent Skills 平台（Qoder、Kimi Code、iFlow、CodeBuddy、Cursor、Gemini CLI 等）

Agent Skills 是开放标准（2025-12 由 Anthropic 开放），已有约 40 个产品兼容本 skill 的分发格式。Claude Code 和 Codex 之外的平台不逐一维护速查表，用通用探测法：

1. **规则文件**：在项目根和上级目录找 `AGENTS.md`（跨平台事实标准）、`CLAUDE.md`，以及平台专属形态（如 `.cursor/rules/`、`.cursorrules`、平台设置里的项目指令）。哪份实际被加载，以当前平台文档和诊断入口为准，不猜。
2. **三分法归类**：把发现的每个知识文件归入三类之一——人工维护的规则、Agent 自动记忆、机器生成的历史/索引。归类不明时按机器生成处理（最保守）。
3. **记忆边界**：未知平台的记忆机制找不到官方控制面时默认只读；不把任何其他平台的尺寸阈值或写入规则套过来。
4. **降级用法**：宿主不支持 Agent Skills 时本 skill 仍可用——把 SKILL.md 全文作为规则文件或对话指令交给 Agent，references 内容按需跟进；执行边界不变。

## 共存检查

1. 列出实际存在的平台目录和 skill realpath。
2. 核对同名 skill 是否软链到同一真身、复制安装、或由更高优先级版本覆盖。
3. 只改权威真身；复制安装需要明确同步机制，不能假设会自动更新。
4. 软链在 Windows 或受限环境可能不可用，允许项目采用导入或生成镜像，只要现场规则明确且有一致性门禁。
5. 验证加载而不是只验证文件存在：使用平台提供的 instruction/skill list、`/memory`、status 或等价诊断入口。

## 官方复核入口

- Agent Skills specification: <https://agentskills.io/specification>
- Agent Skills 兼容产品名录: <https://agentskills.io>（showcase）
- Claude Code memory and CLAUDE.md: <https://code.claude.com/docs/en/memory>
- OpenAI Codex AGENTS.md: <https://developers.openai.com/codex/guides/agents-md/>
- OpenAI Codex Memories: <https://learn.chatgpt.com/docs/customization/memories>

## 规则归类决策矩阵（Hermes / 跨平台通用）

遇到一条新规则或一条看起来"位置错"的现有条款，先按四问分类，再决定写/移/删：

| 规则类型 | 判定问题 | 写入位置 | 不要做的事 |
|---|---|---|---|
| **项目特定边界/约束** | 删了 → 下次 Agent 在**这个项目**会犯错 | `AGENTS.md` / `CLAUDE.md` / `.claude/rules/` | 不要塞进 docs（Agent 不会读 docs 学规则） |
| **跨项目操作纪律**（LLM 编码卫生、调试工作流） | 删了 → **任何项目**的 Agent 都会犯错 | Hermes skill（`skill_manage` create）或 user memory | 不要塞进 AGENTS.md（污染项目特定文件） |
| **事实/偏好**（"用户偏好精简回复"、"用户工作风格"） | 是事实，不是流程 | Hermes user memory（`MEMORY.md` / `USER.md`） | 不要写成 skill（memory 适合事实，skill 适合流程） |
| **人或下游要读的现役答案**（架构、API 合同、运维） | 读者不是 Agent | `README.md` / `docs/` | 不要塞进 AGENTS.md（Agent 触发而非用户触发） |
| **历史/单次事件** | 时间性内容 | git / changelog / incident docs | 不要塞进 AGENTS.md（占用注意力预算） |

### AGENTS.md 漂移处理流程（洁癖专项）

发现 AGENTS.md 里有"看起来多余"的小节（用户上一次追加的、复制自其它项目的、与现有条款重复的），按顺序处理：

1. **先用上面决策矩阵分类**——不靠直觉。
2. **跨项目操作纪律** → 不删，建议升格到 Hermes skill 或并入 user memory。删除 = 丢失用户已经表达的强制约束。
3. **与现有 AGENTS.md 内同层级条款重复**（如 LLM 编码卫生 vs 已有"奥卡姆剃刀/KISS/YAGNI"）→ 合并或互链，**不直接删**。同一个文件内出现两份并行规则会触发规则冲突。
4. **项目特定但已过时** → 改写到 `docs/coding_rules.md` 或直接移除，保留 git diff 作为去向证据。
5. **分类不明** → 标 `pending`，不要在洁癖收尾里强行处置。

> 反面教训：用户曾问"这条规则编码时一定要用，难道不放 AGENTS.md？那放哪里？"——答"删掉"是错的判断。该规则属于跨项目操作纪律，正确路径是升格到 Hermes skill，不是删除。
