# Component and plugin matrix

The exact baseline is machine-readable in [`component-lock.json`](component-lock.json). Versions are a tested snapshot, not an instruction to download binaries from this repository.

## Obsidian

| Plugin ID | Baseline | Function |
|---|---:|---|
| `realclaudian` | 2.0.34 | Runs Codex in the Obsidian sidebar |
| `obsidian-git` | 2.38.6 | Local Vault commits; remote sync remains opt-in |
| `obsidian-icon-folder` | 2.14.7 | Folder visual organization |
| `obsidian-kanban` | 2.0.51 | Project board |
| `obsidian-style-settings` | 1.0.9 | Theme/snippet settings |
| `obsidian-tasks-plugin` | 8.2.2 | Queryable tasks |
| `calendar` | 1.5.10 | Daily-note navigation |
| `table-editor-obsidian` | 0.23.2 | Markdown table editing |
| `obsidian-excalidraw-plugin` | 2.25.3 | Research diagrams |
| `dataview` | 0.5.68 | Knowledge-base dashboards |
| `templater-obsidian` | 2.20.6 | Note templates |

Install by ID through Obsidian's Community Plugins interface or the official registry. The repository includes only sanitized `data.json` settings, not plugin code.

## Zotero

| Plugin | Baseline | Function |
|---|---:|---|
| Better BibTeX | 9.0.47 | Stable citation keys and bibliography export |
| Notero | 1.2.3 | Optional Notion interoperability; notes sync enabled |
| Translate for Zotero | 2.4.5 | English/other-language reading assistance to zh-CN |
| LLM for Zotero | 3.8.28 | Codex App Server and local bearer-protected Zotero MCP |

Download each plugin from its official release page listed in [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md). Do not trust a third-party bundle solely because its filename matches.

## Codex

The global research capability comes from `academic-research-suite` in [`Imbad0202/academic-research-skills-codex`](https://github.com/Imbad0202/academic-research-skills-codex), baseline tag `v0.1.18`. The Vault-local `run-traceable-research` skill adds the narrow Zotero evidence and Obsidian handoff contract.
