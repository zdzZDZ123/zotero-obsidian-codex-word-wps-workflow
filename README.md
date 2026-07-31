# ZOC Research Workflow

[![Version](https://img.shields.io/badge/version-v0.1.0-blue)](https://github.com/zdzZDZ123/zotero-obsidian-codex-research-workflow/releases/tag/v0.1.0)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Validate](https://github.com/zdzZDZ123/zotero-obsidian-codex-research-workflow/actions/workflows/validate.yml/badge.svg)](https://github.com/zdzZDZ123/zotero-obsidian-codex-research-workflow/actions/workflows/validate.yml)

[简体中文](README.zh-CN.md)

ZOC Research Workflow is a Codex-native integration layer for traceable
Zotero–Obsidian academic research. It connects a literature source of truth,
a durable personal knowledge base, and an agentic research runtime without
merging their responsibilities or copying private state between machines.

This repository distributes the workflow as a reproducible configuration and
prompt suite. It includes a sanitized Obsidian Vault, local research skills,
deployment prompts, audit helpers, and integrity gates. Zotero libraries,
licensed PDFs, credentials, bearer tokens, and third-party plugin binaries are
intentionally excluded.

```text
Zotero                         Obsidian                         Codex
  literature metadata           project control                 retrieval
  PDFs and annotations          source and evergreen notes      synthesis
  bibliographic identity        durable research memory         drafting/review
             \                    |                    /
              └──── traceable evidence handoff ──────┘
```

## Relationship Between The Three Systems

This repository does not replace Zotero, Obsidian, Codex, or the upstream
academic-research skill suite.

- Use **Zotero** for authoritative bibliographic metadata, locally available
  PDFs, annotations, and source-linked child notes.
- Use **Obsidian** for project state, reusable knowledge, research logs,
  synthesis matrices, and durable outputs.
- Use **Codex** for research routing, evidence retrieval, synthesis, drafting,
  review, and controlled writes across the two stores.
- Use
  [`Imbad0202/academic-research-skills-codex`](https://github.com/Imbad0202/academic-research-skills-codex)
  as the Codex-native academic research engine. The Vault-local
  `run-traceable-research` skill adds this workflow's Zotero evidence and
  Obsidian handoff contract.

No Obsidian MCP server is required. Codex works directly in the Vault, while
`llm-for-zotero` provides the local bearer-protected Zotero MCP connection.

## Repository Layout

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

## Versioning

The current workflow release is `v0.1.0`. Application and plugin baselines are
recorded independently in [`docs/component-lock.json`](docs/component-lock.json).

Pinned versions represent a tested snapshot. When a pinned release is
unavailable or incompatible, install the latest compatible official version,
record the deviation, and rerun the end-to-end acceptance test. A version
number alone is never treated as runtime evidence.

## Install The Workflow

Clone the repository on the target computer:

```bash
git clone https://github.com/zdzZDZ123/zotero-obsidian-codex-research-workflow.git
cd zotero-obsidian-codex-research-workflow
```

Then give the deployment prompts to Codex in order:

1. [`prompts/01-setup-obsidian.md`](prompts/01-setup-obsidian.md)
2. [`prompts/02-setup-zotero.md`](prompts/02-setup-zotero.md)
3. [`prompts/03-connect-codex.md`](prompts/03-connect-codex.md)
4. [`prompts/04-run-first-research.md`](prompts/04-run-first-research.md)

The prompts instruct Codex to inspect the actual operating system, find each
official application/plugin source, preserve existing user data, configure the
local runtime, and validate the result. No replication ZIP or bundled installer
is required.

## Install The Academic Research Engine

This workflow expects the Codex-native ARS suite from the upstream repository.
Follow its current installation instructions, or use the baseline recorded in
`docs/component-lock.json` when reproducing this exact release.

After installation, open a new Codex conversation and verify that
`academic-research-suite` or `ARS-Codex` appears in `/skills`.

## Usage

Invoke the global academic research suite together with the Vault-local
traceability layer:

```text
Use $academic-research-suite together with $run-traceable-research.

Goal: build an evidence-traceable literature review.
Evidence source: my Zotero library and locally available PDFs.
Knowledge output: source notes, evergreen notes, and a synthesis matrix in this Vault.
Constraints: preserve item identity, full-text status, and PDF page locations.
Stop condition: mark unsupported claims instead of inventing citations or pages.
```

The local skills route recurring knowledge-work operations:

| Skill | Use when you need |
|---|---|
| `capture-source` | A traceable inbox note from a new source |
| `distill-knowledge` | Atomic, reusable notes derived from captured material |
| `start-project` | A research project with done criteria and a next action |
| `run-traceable-research` | Zotero evidence inventory, ARS execution, and Obsidian handoff |
| `weekly-review` | Project-state reconciliation and one reversible improvement |

## Runtime Behavior

- Zotero remains the bibliographic source of truth.
- Obsidian remains the durable project and knowledge store.
- Codex opens the Vault as its workspace and follows `AGENTS.md` plus local
  skills before writing.
- Claudian can expose the same Codex runtime in the Obsidian sidebar, but its
  machine-specific CLI path is discovered locally.
- The Zotero MCP endpoint remains on loopback and uses a bearer token generated
  independently on every computer.
- Metadata-only access is not treated as full-text or page-level evidence.
- Missing sources, pages, statistics, and citations remain explicitly
  unverified; the workflow never manufactures them.

## Smoke Test

Configuration presence is not sufficient. A successful installation proves the
complete trace:

1. search an existing Zotero item;
2. read a real locally available PDF passage with a page or location;
3. write an Obsidian source note containing provenance and evidence status;
4. create a clearly marked Zotero test child note;
5. read the child note back;
6. validate the repository/Vault structure without exposing private content.

Expected result: every material claim can be traced to a real source, and the
workflow survives a new Codex conversation without relying on chat history.

## Security

Do not commit Zotero profiles, private group libraries, licensed PDFs, personal
notes, unpublished manuscripts, `.env` files, OAuth state, cookies, Codex
authentication data, API keys, or the bearer token generated by
`llm-for-zotero`.

Run the public-repository gate before publishing changes:

```powershell
pwsh ./scripts/validate-repo.ps1
```

See [`SECURITY.md`](SECURITY.md) and
[`docs/security-model.md`](docs/security-model.md) for the full trust boundary.

## Third-Party Software

This repository records plugin identities, tested versions, official sources,
and sanitized settings. It does not redistribute application or plugin
binaries. See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## License

Original material in this repository is released under the
[MIT License](LICENSE). Third-party products remain governed by their own
licenses and terms.
