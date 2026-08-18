# Evidence-grounded originality revision

This layer repairs originality findings without turning the workflow into a
similarity-score game. It is a local remediation loop between ARS integrity
verification and publication formatting:

```text
Zotero evidence -> Obsidian semantic manuscript -> ARS Phase D screening
                -> evidence-grounded originality revision
                -> 100% changed-paragraph recheck + named approval
                -> deterministic DOCX -> Word/WPS + page QA
```

## Research basis

The implementation follows the shared method demonstrated by several
high-engagement or institutionally produced tutorials:

- [Scribbr: How to Paraphrase in 5 Easy Steps](https://www.youtube.com/watch?v=oiM0x0ApVL8)
- [Scribbr: How to Avoid Plagiarism with 3 Simple Tricks](https://www.youtube.com/watch?v=uQhVDH9p7aU)
- [QUT Library: How To Paraphrase](https://www.youtube.com/watch?v=SObGEcok06U)
- [Wordvice: How to Paraphrase in Research Papers](https://www.youtube.com/watch?v=1VACN6X2eF0)
- [Concordia University Library: How to Paraphrase](https://www.youtube.com/watch?v=0L3EiPzfzEo)

Their common method—understand the source, set the original wording aside,
write from meaning, compare for fidelity, and cite—also aligns with the
[Harvard Guide to Using Sources](https://usingsources.fas.harvard.edu/summarizing-paraphrasing-and-quoting)
and the [University of Leeds academic writing guidance](https://library.leeds.ac.uk/info/14011/writing/221/language_and_style/2).
Synonym substitution is intentionally rejected.

Similarity remains a signal, not a misconduct verdict. This follows
[Turnitin's own explanation](https://guides.turnitin.com/hc/en-us/articles/34400565079053-Turnitin-and-plagiarism).
Self-reuse is treated contextually following
[COPE text-recycling guidance](https://publicationethics.org/files/Web_A29298_COPE_Text_Recycling.pdf).
The generated disclosure draft reminds authors of the human responsibility and
disclosure principles in the
[ICMJE AI recommendations](https://www.icmje.org/recommendations/browse/artificial-intelligence/ai-use-by-authors.html).

## Install

Windows:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Install-OriginalityRevision.ps1
.\scripts\Revise-ResearchOriginality.ps1 doctor --self-test
```

macOS:

```bash
bash ./scripts/Install-OriginalityRevision-macOS.command
bash ./scripts/Revise-ResearchOriginality-macOS.command doctor --self-test
```

The installer creates an isolated Python runtime and copies the Codex skill. It
does not install, log in to, scrape, or bypass CNKI, Turnitin, iThenticate, or
any other commercial service.

## Start a private project

Copy
`codex/skills/revise-originality-with-evidence/assets/project-starter` to the
private manuscript directory. Replace its placeholder bibliography, evidence,
and ARS files. Do not commit a manuscript or exported similarity report to this
public repository.

Run:

```powershell
.\scripts\Revise-ResearchOriginality.ps1 analyze --config .\originality.yaml
.\scripts\Revise-ResearchOriginality.ps1 revise --config .\originality.yaml
.\scripts\Revise-ResearchOriginality.ps1 verify --config .\originality.yaml
.\scripts\Revise-ResearchOriginality.ps1 verify --config .\originality.yaml --approve --reviewer "Author review"
```

Before `revise`, Codex must read each cited Zotero source and location, complete
the generated proposal template, and keep unsupported or ambiguous claims
blocked. Before approval, ARS Phase D plus citation, data, and fact checks must
cover every paragraph listed in `recheck-request.json`.

## Report import

The importer accepts extractable PDF/HTML exports and deterministic generic
CSV/JSON. Vendor layouts change; scanned or unsupported reports fail closed and
must be transcribed into the generic template. An overall score without a
paragraph excerpt is never converted into a fabricated match.

Cross-language findings are supported through Codex's semantic review. The
deterministic mapper handles Chinese and English lexical matches, but explicitly
marks language-mismatched text for semantic mapping instead of pretending that
character overlap can detect translated reuse.

## Protected invariants and release states

The helper blocks lost citation keys, undeclared citation additions, changed
numbers, sample sizes, units, table/figure references, protected terms,
headings, images, and direct quotations. The author should list outcome scales,
intervention names, statistical methods, and reporting guidelines under
`protected.terms`.

- `qa_pending_recheck`: review copy exists; ARS recheck is incomplete.
- `qa_pending_human_approval`: all checks passed; named approval is missing.
- `qa_failed`: a blocking issue or invariant failure remains.
- `qa_passed`: every required check passed and a named reviewer explicitly
  approved the exact manuscript hash.

Add the QA path to the publication contract:

```yaml
manuscript: originality-output/manuscript-originality-reviewed.md
originality_manifest: originality-output/originality-qa-report.json
```

The formatter refuses a pending manifest, changed hash, or missing approval.
The generated Markdown also carries an inert manifest-required marker so an
accidental omission is rejected before Pandoc or Word/WPS starts. Word and WPS
never perform the semantic revision themselves.
