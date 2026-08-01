# WPS acceptance evidence

This page records the privacy-safe runtime evidence used before publishing the
ZOCW Word/WPS update. It validates the formatting mechanism; it does not claim
that a synthetic fixture is an official journal template.

## Environment

| Component | Observed result on 2026-08-01 |
|---|---|
| WPS Writer | `12.1.0.28032`, `KWPS.Application`, available |
| Microsoft Word | `not_checked`; `Word.Application` was served by WPS, not `WINWORD.EXE` |
| LibreOffice | `26.2.4.2`, available |
| Pandoc | `3.10`, available |
| PDF page renderer | Poppler `pdftoppm`, available |

## Acceptance manuscript

The fixture was a synthetic nursing manuscript with 15 semantic headings, two
CSL citation keys, one table, one figure, separate anonymous and title-page
content, and explicit privacy terms. It contained no private Zotero records,
patient data, licensed article text, or publisher-owned template.

Two formatting routes were exercised from the same semantic source:

| Route | WPS manuscript pages | LibreOffice manuscript pages | Title-page renders | Result |
|---|---:|---:|---:|---|
| User-defined YAML profile | 4 | 4 | 2 | `qa_passed` |
| Authorized synthetic uploaded DOCX, `template_authoritative` | 3 | 3 | 2 | `qa_passed` |

All 18 final rendered pages were inspected at page resolution. No clipping,
overlap, table overflow, figure overflow, unreadable caption, missing page
number, or unexpected font substitution was accepted.

## What was verified

- WPS created a separate reviewed DOCX, exported PDF, closed the document,
  reopened the reviewed copy, and preserved 60 paragraphs and one table.
- Pandoc citeproc resolved both Zotero-style citation keys from CSL JSON.
- The semantic manifest preserved all headings, the table, the figure, and the
  reference list in both formatting routes.
- Anonymous outputs contained none of the declared author, email, or uploaded
  reference identity terms and contained no comments or tracked changes.
- The retained uploaded reference remained read-only; its prose and private
  header/footer text were not copied into the generated manuscript.
- The uploaded-reference core and WPS-reviewed copy both matched the distilled
  page geometry, semantic theme-font mappings, and the named Normal, Title,
  Heading 1–3, and Caption styles.
- Two complete formatting jobs ran consecutively through WPS after the bridge
  was changed to clean up only automation-owned WPS processes.
- WPS and LibreOffice PDFs were independently rasterized and visually reviewed
  before the manifests were explicitly finalized as `qa_passed`.

## Failures found before release

The acceptance process initially found and blocked three defects:

1. an invalid custom alignment value produced a low-level error instead of a
   clear profile-validation message;
2. back-to-back WPS jobs could collide with a lingering automation process;
3. WPS normalized explicit style fonts to equivalent theme fonts, requiring a
   semantic theme comparison instead of a byte-for-byte XML comparison.

These cases are now handled by explicit validation, owned-process cleanup, and
post-WPS semantic template-fidelity checks. A real uploaded journal template
must still be authorized by the user, distilled locally, and visually reviewed;
the workflow will not label a result officially compliant without current
publisher evidence.
