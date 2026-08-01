# Publication formatting layer

The publication layer turns an evidence-checked semantic manuscript into a reproducible submission package without changing scientific content.

```text
Zotero citation keys -> Obsidian semantic Markdown -> Codex formatter
                     -> immutable core DOCX
                     -> Word/WPS reviewed copy + PDF
                     -> LibreOffice/editor page renders -> explicit visual release
```

## What is deterministic

- Citation identity comes only from Better BibTeX plus Pandoc citeproc and the declared CSL.
- Journal rules live in versioned YAML profiles; official DOCX/DOTX files remain local and are bound by a distilled SHA-256 contract.
- Page geometry, named styles, headings, line numbers, table grid widths, figure limits, header/footer fields, and metadata scrubbing are applied by code.
- Every run has a unique directory, immutable source/core hashes, separate editor-reviewed copies, QA JSON, page PNGs, and a release state.

Changing journals means changing `journal_profile`, `csl`, and optionally the official template, then rebuilding from `manuscript.md`. Never restyle a reviewed DOCX in place.

## Install

Windows:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Install-PublicationFormatting.ps1
```

macOS:

```bash
chmod +x ./scripts/Install-PublicationFormatting-macOS.command
./scripts/Install-PublicationFormatting-macOS.command
```

The installers are idempotent. They install missing official Pandoc, LibreOffice, and WPS components, create an isolated Python runtime, and copy the Codex skill. They never install, activate, or bypass licensing for Microsoft Word.

## Start a manuscript project

Copy `codex/skills/format-submission-manuscript/assets/project-starter` to a private project directory. Copy the selected repository profile into that project's `profiles/` directory. Store official templates under a local ignored directory such as `templates-local/`.

Configure Better BibTeX automatic export to `references.json` or `references.bib`. Use relative figure paths under `assets/`.

```powershell
.\scripts\Format-ResearchManuscript.ps1 doctor --self-test
.\scripts\Format-ResearchManuscript.ps1 format --config .\submission.yaml --editor auto
```

The first command must distinguish genuine Word from a WPS-owned `Word.Application` registration. `auto` uses genuine Word first and otherwise WPS. When no verified editor exists, choose `none` to generate the core and LibreOffice PDF while recording editor QA as not applicable.

## Official templates

Prefer the publisher's current DOCX/DOTX and CSL. Record the publisher URL and retrieval date, then distill the template:

```powershell
.\scripts\Format-ResearchManuscript.ps1 distill `
  --template .\templates-local\journal.docx `
  --output-dir .\templates-local\journal-contract `
  --source-url https://publisher.example/author-instructions
```

The original template is read-only. The contract records every package part and verifies that the input SHA-256 has not changed. No publisher template is included in this repository.

## QA and release

`format` stops on unresolved evidence markers, missing citation keys, template drift, structural loss, privacy failures, editor automation failure, LibreOffice timeout, or rasterization failure. Successful formatting remains `qa_pending_visual_inspection`.

Inspect every PNG under the run's `qa/` directory at full resolution. Check page edges, overlaps, tables, figures, captions, page numbers, field results, font substitution, blank pages, and section breaks. Then release:

```powershell
.\scripts\Format-ResearchManuscript.ps1 finalize `
  --manifest .\submission-output\RUN\run-manifest.json `
  --reviewer "Codex visual QA" `
  --confirm-every-page
```

Only `finalize` can set `qa_passed`; it also performs a requested desktop copy. Genuine Word remains `not_checked` until `WINWORD.EXE` is detected and the same smoke test is run.

## Local compatibility sample

`ijns-local-baseline.yaml` migrates the previous hard-coded local IJNS generator into an explicit regression profile. It is intentionally labeled `local_compatibility_sample_not_current_official`. Replace it with a current official template/profile contract before claiming publisher compliance.
