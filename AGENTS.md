# Repository agent contract

## Scope

This repository contains a public, privacy-safe replication contract for a Zotero, Obsidian, and Codex research workflow.

## Required behavior

- Preserve source provenance and the separation between Zotero evidence, Obsidian knowledge, and Codex orchestration.
- Never add personal Zotero data, copyrighted PDFs, credentials, OAuth state, cookies, MCP bearer tokens, or absolute user-home paths.
- Do not vendor third-party plugin binaries. Record IDs, versions, official sources, and sanitized settings instead.
- Keep deployment prompts cross-platform and idempotent. A rerun must detect existing installations before changing them.
- Treat page-level evidence as a hard gate: do not invent quotations, pages, DOI values, sample sizes, results, or citations.
- Run `scripts/validate-repo.ps1` before committing.
- Keep changes reversible and document version deviations.
