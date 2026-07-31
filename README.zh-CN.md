# ZOC Research Workflow

[![Version](https://img.shields.io/badge/version-v0.1.0-blue)](https://github.com/zdzZDZ123/zotero-obsidian-codex-research-workflow/releases/tag/v0.1.0)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Validate](https://github.com/zdzZDZ123/zotero-obsidian-codex-research-workflow/actions/workflows/validate.yml/badge.svg)](https://github.com/zdzZDZ123/zotero-obsidian-codex-research-workflow/actions/workflows/validate.yml)

[English](README.md)

ZOC Research Workflow 是一套面向 Codex 的 Zotero–Obsidian 可追溯科研集成层。
它把文献事实源、长期个人知识库和智能科研执行环境连接起来，同时保持三者的职责边界，
也不会把某台电脑上的私人状态直接复制到另一台电脑。

本仓库以可复现配置和提示词套件的方式发布工作流，包括脱敏的 Obsidian Vault、
本地科研 Skills、无人值守部署提示词、审计脚本与完整性门禁。Zotero 私人文献库、
受许可限制的 PDF、账号凭据、Bearer Token 和第三方插件二进制均被明确排除。

```text
Zotero                         Obsidian                         Codex
  文献元数据                     项目控制                         检索
  PDF 与批注                     来源笔记与永久笔记               综合
  引文身份                       长期研究记忆                     写作与审稿
             \                    |                    /
              └──────── 可追溯证据交接层 ────────┘
```

## 三个系统之间的关系

本仓库不会替代 Zotero、Obsidian、Codex 或上游学术研究 Skills。

- 需要权威文献元数据、本地 PDF、批注和来源级子笔记时，使用 **Zotero**。
- 需要项目状态、可复用知识、研究日志、证据矩阵和长期输出时，使用 **Obsidian**。
- 需要科研任务路由、证据检索、综合、写作、审稿及跨系统受控写入时，使用 **Codex**。
- Codex 原生学术研究能力来自
  [`Imbad0202/academic-research-skills-codex`](https://github.com/Imbad0202/academic-research-skills-codex)。
  Vault 内的 `run-traceable-research` 负责补充本工作流特有的 Zotero 证据与
  Obsidian 交接契约。

本工作流不要求 Obsidian MCP。Codex 直接在 Vault 中工作，`llm-for-zotero`
负责提供带本机 Bearer 保护的 Zotero MCP 连接。

## 仓库结构

```text
obsidian/vault-template/
  AGENTS.md
  .agents/skills/
    capture-source/
    distill-knowledge/
    run-traceable-research/
    start-project/
    weekly-review/
  .obsidian/
  00-Inbox/ ... 99-Templates/
zotero/README.md
codex/README.md
prompts/01-setup-obsidian.md ... 04-run-first-research.md
docs/component-lock.json
docs/architecture.md
docs/security-model.md
scripts/validate-repo.ps1
scripts/Audit-ObsidianEnvironment.ps1
scripts/Audit-ObsidianEnvironment-macOS.command
```

## 版本策略

当前工作流版本为 `v0.1.0`。应用与插件基线独立记录在
[`docs/component-lock.json`](docs/component-lock.json) 中。

锁定版本代表经过验证的快照。如果目标系统无法安装同一版本，可以安装官方来源的最新兼容版本，
但必须记录版本偏差并重新执行端到端验收。版本号本身不等于运行证据。

## 安装工作流

在目标电脑克隆仓库：

```bash
git clone https://github.com/zdzZDZ123/zotero-obsidian-codex-research-workflow.git
cd zotero-obsidian-codex-research-workflow
```

随后依次把以下提示词交给 Codex：

1. [`prompts/01-setup-obsidian.md`](prompts/01-setup-obsidian.md)
2. [`prompts/02-setup-zotero.md`](prompts/02-setup-zotero.md)
3. [`prompts/03-connect-codex.md`](prompts/03-connect-codex.md)
4. [`prompts/04-run-first-research.md`](prompts/04-run-first-research.md)

这些提示词要求 Codex 检查真实操作系统、从官方来源查找应用和插件、保护已有用户数据、
配置本机运行环境并完成运行验证。不需要复刻 ZIP 或预打包安装程序。

## 安装学术研究引擎

本工作流依赖上游仓库提供的 Codex 原生 ARS 套件。安装时应遵循其当前说明；
若要精确复现本版本，则使用 `docs/component-lock.json` 中记录的基线。

安装后打开新的 Codex 对话，通过 `/skills` 确认出现
`academic-research-suite` 或 `ARS-Codex`。

## 使用方式

同时调用全局学术研究套件和 Vault 本地的可追溯交接层：

```text
使用 $academic-research-suite 和 $run-traceable-research。

目标：完成一份证据可追溯的文献综述。
证据来源：我的 Zotero 文献库及本地可读取 PDF。
知识输出：在当前 Vault 中生成来源笔记、永久笔记和证据矩阵。
约束：保留 Zotero 条目身份、全文状态及 PDF 页码位置。
停止条件：证据不足时标记为未验证，不得虚构引文或页码。
```

五个本地 Skills 分别负责：

| Skill | 适用任务 |
|---|---|
| `capture-source` | 把新来源捕获为可追溯的收件箱笔记 |
| `distill-knowledge` | 从来源材料中提炼原子化、可复用知识 |
| `start-project` | 建立带完成标准与下一步行动的科研项目 |
| `run-traceable-research` | Zotero 证据盘点、ARS 执行和 Obsidian 交接 |
| `weekly-review` | 对齐项目状态并实施一个可逆改进 |

## Codex 运行行为

- Zotero 始终是文献元数据与附件证据的事实源。
- Obsidian 始终是项目控制和长期知识存储层。
- Codex 把 Vault 作为工作区，并在写入前遵守 `AGENTS.md` 和本地 Skills。
- Claudian 可以在 Obsidian 侧栏中调用同一 Codex 运行时，但必须发现目标电脑自己的 CLI 路径。
- Zotero MCP 仅监听本机回环地址，每台电脑独立生成 Bearer Token。
- 只能读取元数据时，不得声称已经读取全文或获得页码证据。
- 无法核验的来源、页码、统计数据与引文必须明确标记，不能补造。

## 冒烟测试

只有配置文件存在并不代表安装成功。完整验收必须证明以下链路：

1. 搜索一个真实 Zotero 条目；
2. 从本地可用 PDF 中读取真实段落和页码或位置；
3. 向 Obsidian 写入包含来源和证据状态的来源笔记；
4. 创建一个明确标记的 Zotero 测试子笔记；
5. 再次读取该子笔记；
6. 在不暴露私人内容的情况下完成仓库与 Vault 结构校验。

预期结果是：每个重要论断都能回溯到真实来源，而且在开启新的 Codex 对话后，
工作流仍可依靠持久化知识继续运行，而不是依赖旧聊天记录。

### 灰度运行证据

2026-07-31 对本机已安装的桌面环境进行了隐私安全的实机检查：公开 Obsidian
Vault 成功打开，Claudian 2.0.34 已加载并显示 Codex 侧栏，Zotero 9.0.6 已加载
所需插件，`llm-for-zotero` 3.8.31 的实时 Codex 连接测试返回 `OK`，同一页面还
显示 Zotero MCP 已连接并注册 15 个工具。

| Obsidian 公开部署 | Zotero-Codex 实时测试 |
|---|---|
| ![Obsidian 公开 Vault 运行截图](docs/assets/runtime-evidence/obsidian-public-vault-runtime.png) | ![Zotero Codex 冒烟测试通过](docs/assets/runtime-evidence/zotero-codex-smoke-test-passed.png) |

完整的脱敏截图与证据边界见
[`docs/runtime-evidence.md`](docs/runtime-evidence.md)，原始 PNG 的 SHA-256 摘要见
[`docs/runtime-evidence-manifest.json`](docs/runtime-evidence-manifest.json)。这些截图
证明插件已实际加载且本地连接可用；上面的六步链路仍是来源可追溯性的发布级验收。

## 安全边界

不要提交 Zotero Profile、私人群组库、受许可限制的 PDF、个人笔记、未发表论文、
`.env`、OAuth 状态、Cookie、Codex 登录数据、API Key 或 `llm-for-zotero`
生成的 Bearer Token。

发布修改前运行：

```powershell
pwsh ./scripts/validate-repo.ps1
```

完整信任边界见 [`SECURITY.md`](SECURITY.md) 和
[`docs/security-model.md`](docs/security-model.md)。

## 第三方软件

本仓库只记录插件身份、验证版本、官方来源和脱敏设置，不重新分发应用或插件二进制。
详见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。

## 许可证

本仓库原创内容采用 [MIT License](LICENSE)。第三方产品继续遵循各自许可证和使用条款。
