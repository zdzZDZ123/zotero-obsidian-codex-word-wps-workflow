# Deploy and validate the publication formatting layer

Use `$format-submission-manuscript` and operate the actual target computer.

1. Run the platform installer in this repository. Install only missing official Pandoc, LibreOffice, and WPS components; do not install or bypass Microsoft Word licensing.
2. Run `doctor --self-test`. Distinguish genuine `WINWORD.EXE` from WPS taking over `Word.Application`.
3. Create a private manuscript project from the skill's `assets/project-starter`, and connect Better BibTeX automatic export to `references.json` or `references.bib`.
4. Prefer the journal's current official DOCX/DOTX and CSL. Keep protected templates local, distill a hash-bound contract, and record source URLs/dates.
5. Format a synthetic or user-authorized manuscript through citation, table, figure, anonymous metadata, WPS/Word field refresh, PDF export, LibreOffice rendering, and page PNG generation.
6. Inspect every rendered page. Do not finalize until clipping, overlap, overflow, font substitution, caption, page-number, and pagination checks pass.
7. Run repository validation, skill validation, unit tests, an idempotent second installer run, and report all version deviations. Do not expose private manuscripts, citation libraries, absolute home paths, tokens, or licensed assets.
