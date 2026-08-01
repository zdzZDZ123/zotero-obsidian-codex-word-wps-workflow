# Publication formatting contract

## Boundary

This skill is a source-aware formatting adapter. `academic-research-suite` owns research and manuscript content; Zotero/Better BibTeX owns bibliographic identity; Obsidian owns the semantic source; Pandoc citeproc owns citation rendering; the selected editor refreshes fields and exports a compatibility PDF.

The formatter may normalize styles, page geometry, fields, captions, table widths, image size, sections, headers, footers, and metadata. It must not edit scientific meaning or silently repair evidence.

## Submission contract

`submission.yaml` uses schema version 1. All paths resolve relative to the YAML file and must remain inside that project directory.

```yaml
schema_version: 1
manuscript: manuscript.md
title_page: title-page.md
bibliography: references.json
csl: styles/journal.csl
journal_profile: profiles/journal.yaml
editor: auto
variants: [anonymized, full]
outputs: [docx, pdf]
output_root: submission-output
open_after: false
desktop_copy: false
blind_terms: [Author Name, University Name]
supplementary: [assets/supplementary-table.docx]
```

Declare both `template` and `template_contract`, or neither. Run `distill` before first use and after every template change. The formatter fails closed when the retained template SHA-256 no longer matches.

## Profile provenance

An official profile records the official source URL, retrieval date, and any local template/CSL hashes. A compatibility profile must say that it is not verified against current publisher instructions. Never convert a local legacy layout into an unsupported claim of journal compliance.

## QA states

- `qa_pending_visual_inspection`: content, package, privacy, editor, and rasterization checks passed, but pages have not been explicitly inspected.
- `qa_passed`: every produced page was inspected and the run was finalized with a reviewer label and timestamp.
- `not_checked`: the backend is unavailable, unsupported, or not genuinely installed. This is never equivalent to passed.

Compare source semantics and DOCX structure across journal profiles. Heading, table, figure, and citation identities must stay constant. Direct formatting should be minimized; profile-level styles remain authoritative.
