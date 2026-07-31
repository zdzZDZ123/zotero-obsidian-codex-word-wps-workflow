# Zotero configuration contract

## Baseline

- Zotero 9.0.6
- Chrome Zotero Connector 5.0.211
- Better BibTeX 9.0.47
- Notero 1.2.3
- Translate for Zotero 2.4.5
- LLM for Zotero 3.8.28

## Settings

### Better BibTeX

- Citation key formula: `auth.lower + shorttitle(3, 3) + year`
- Fill citation key after: `1`
- Journal abbreviation: automatic

### Translate for Zotero

- Target language: `zh-CN`
- Preferred source: `cnki`
- Dictionary: `bingdict`
- Annotation label: `翻译`
- Do not translate source languages: `zh`, `zh-CN`, `中文`

### Notero

- Sync notes: enabled
- OAuth, database ID, and collection mapping: personal state; configure per user and never publish

### LLM for Zotero

- Conversation system: Codex
- Codex App Server: enabled
- Model: `gpt-5.6-sol`
- Native approvals: enabled
- MCP endpoint: `http://127.0.0.1:23119/llm-for-zotero/mcp`
- Embedding baseline: Gemini / `gemini-embedding-001`; API key is optional private state and is not included

Use **Install/update Zotero MCP config** inside the plugin. The generated bearer token belongs only to that computer.

## Acceptance checks

- Browser Connector saves a test item with metadata and attachment where permitted.
- Better BibTeX produces a stable citation key.
- Codex can search the local Zotero library through MCP.
- Codex can read a real full-text passage and report its page/location.
- Codex can create a clearly marked test child note and read it back.
