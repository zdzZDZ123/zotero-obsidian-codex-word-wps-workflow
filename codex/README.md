# Codex integration contract

## Connections

- **Codex → Zotero:** the local `llm-for-zotero` MCP server. Let the Zotero plugin install/update the configuration so the bearer token never enters this repository.
- **Codex → Obsidian:** open the Vault as the Codex project/workspace. Codex reads and writes Markdown directly under the Vault contract in `AGENTS.md`.
- **Obsidian → Codex:** Claudian uses the local Codex CLI executable and opens its view in the right sidebar.

## Research skills

Install `academic-research-suite` from the pinned source/tag in `docs/component-lock.json` into the user's Codex skills directory. The Vault already contains five project-local skills under `.agents/skills`; `run-traceable-research` is the handoff layer between general academic research capabilities, Zotero evidence, and Obsidian storage.

Do not silently replace the requested research suite with an unrelated repository. If the pinned tag cannot be installed, report the access or compatibility problem and use the smallest verified fallback.

## Runtime defaults

- Preferred model: `gpt-5.6-sol`
- Reasoning effort: high
- Claudian permission mode: normal
- Claudian safe mode: `workspace-write`
- Locale: `zh-CN`
- View: right sidebar

Machine-specific CLI paths and all authentication state are intentionally blank in the template.

## Definition of done

Configuration presence is not enough. Complete a real trace:

1. search an existing Zotero item;
2. read an actual PDF passage with a page/location;
3. write an Obsidian source note containing provenance and evidence status;
4. create a marked Zotero test child note;
5. read the child note back;
6. report every version deviation without exposing secrets.
