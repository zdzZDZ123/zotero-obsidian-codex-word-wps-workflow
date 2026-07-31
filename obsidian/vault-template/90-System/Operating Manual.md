---
type: manual
status: active
updated: 2026-07-27
---

# 使用手册

## 系统地图

```text
输入 -> 00-Inbox -> 40-Knowledge -> 10-Projects / 50-Outputs
                 -> .agents/skills          |
                           ^                |
                           |-- 每周回流 -----|
```

文件夹职责见根目录 `AGENTS.md`。Codex 和 Claudian 都应遵守其中的来源、链接、项目和安全规则。

## 核心技能

- `$capture-source`：把 URL、文字、文件或灵感变成可追溯的收件箱笔记。
- `$distill-knowledge`：从收件箱提炼常青笔记，建立链接并回写处理状态。
- `$start-project`：把目标变成有完成标准、下一步和上下文的项目。
- `$weekly-review`：检查收件箱、项目与成果，记录摩擦并小步改进系统。
- `$run-traceable-research`：衔接 Zotero 证据、学术研究流程与 Obsidian 项目和成果归档。

## 推荐节奏

- 随时：快速收录，不在收录时纠结分类。
- 每天：确认进行中项目至少有一个下一步。
- 每周：运行 `$weekly-review`，处理积压并提出一项系统改进。
- 每月：合并重复概念，检查已完成项目是否留下可复用成果。

## Claudian 配置

- Provider：Codex
- Codex CLI：由安装脚本自动检测
- Vault：当前知识库根目录

插件只在主动对话或调用时把必要上下文交给 Codex；不要把密码、令牌或私密凭据写入仓库。
