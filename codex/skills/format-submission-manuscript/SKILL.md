---
name: format-submission-manuscript
description: Convert a semantic Markdown manuscript with Zotero citation keys into a deterministic, privacy-checked journal DOCX/PDF submission package. Use when changing journal formats, distilling an official DOCX/DOTX template, validating anonymous manuscripts, refreshing Word/WPS fields, or rendering every page for publication QA.
---

# Format Submission Manuscript

Treat formatting as Phase 7 of the research workflow. Preserve the manuscript's claims, findings, citations, author facts, and conclusions. Change layout only.

## Required inputs

Keep all declared paths inside one manuscript project:

- `manuscript.md`: semantic headings, tables, figures, and Pandoc/Zotero citation keys such as `[@smith2024]`.
- `references.json` or `references.bib`: Better BibTeX automatic export.
- `submission.yaml`: profile, template, variants, outputs, editor, and release options.
- `assets/`: figures and supplementary files referenced by the manuscript.

Read [references/workflow-contract.md](references/workflow-contract.md) before formatting. Use [assets/project-starter](assets/project-starter) as the smallest safe scaffold.

## Workflow

1. Run `doctor --self-test`. Report genuine Microsoft Word as available only when `Word.Application` resolves to `WINWORD.EXE`; never count WPS as Word.
2. If an official DOCX/DOTX exists, retain it locally and run `distill`. Keep its SHA-256 and source URL. Do not commit copyrighted templates.
3. Inspect `submission.yaml`. Prefer the official distilled template; otherwise use a versioned profile whose source and validation status are explicit.
4. Run `format`. Stop if citation evidence markers remain, a citation key is missing, a declared file is absent, or a template hash changed.
5. Inspect every LibreOffice-rendered page and every Word/WPS PDF-rendered page at full resolution. Check clipping, overlaps, table overflow, figure scale, caption placement, font substitution, page numbers, and pagination.
6. Run `finalize --confirm-every-page` only after the inspection passes. This is the only transition from `qa_pending_visual_inspection` to `qa_passed` and the only point at which a requested desktop copy is made.

## Commands

Use the skill's `scripts/submission_formatter.py` with the runtime Python installed by the repository helper.

```text
submission_formatter.py doctor --self-test
submission_formatter.py distill --template template.docx --output-dir templates-local/journal --source-url URL
submission_formatter.py format --config submission.yaml --editor auto
submission_formatter.py verify --docx output.docx --render-dir qa/render
submission_formatter.py finalize --manifest submission-output/RUN/run-manifest.json --reviewer "Codex visual QA" --confirm-every-page
```

On Windows, `auto` prefers genuine Word and otherwise uses `KWPS.Application`. On macOS, generate and render the immutable core; record editor automation as `not_checked` unless a verified interface is available.

## Non-negotiable gates

- Use Pandoc citeproc plus the declared bibliography and CSL. Never hand-rewrite references or infer citation style.
- Preserve a separate immutable core DOCX. Let Word/WPS save only a reviewed copy.
- Generate a new run directory for every journal switch. Never restyle a previously reviewed artifact in place.
- Scrub author metadata, custom properties, revision identifiers, comments, and tracked changes from anonymous output.
- Do not claim visual completion from structure checks alone. A failed or timed-out LibreOffice render is a failed run.
- Do not install or bypass Microsoft Word licensing. Mark Word `not_checked` until genuine Word is present.
- Do not commit manuscripts, Zotero libraries, PDFs, commercial fonts, application installers, or third-party journal templates.

## Natural-language routing

For requests such as “把这篇论文改成 International Journal of Nursing Studies 的投稿格式并用 WPS 打开,” locate the project contract, verify its profile/template provenance, run the workflow above, and return the `qa_passed` package. If no current official template or verified profile exists, state that limitation and do not label the result officially compliant.
