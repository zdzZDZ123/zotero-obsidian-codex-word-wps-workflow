# Evidence-grounded originality revision contract

## Boundary

`academic-research-suite` detects originality and integrity problems. Zotero is
the evidence source, Obsidian is the semantic manuscript source, and this skill
creates a separate, reviewable repair copy. `format-submission-manuscript` may
consume that copy only after the originality QA report says `qa_passed` and its
manuscript hash matches.

Similarity is a locator, not a plagiarism verdict. The system must never claim
that a low score proves originality or that a high score proves misconduct.

## Project contract

`originality.yaml` schema version 1 resolves every path relative to the YAML
file. Paths outside the project are rejected.

```yaml
schema_version: 1
manuscript: manuscript.md
bibliography: references.json
evidence_manifest: evidence.json
ars_integrity_report: integrity-report.md
similarity_reports:
  - reports/turnitin-export.pdf
languages: [zh, en]
protected:
  terms: [CONSORT, Pittsburgh Sleep Quality Index]
  sections: [Results]
output_root: originality-output
revision_proposals: revision-proposals.json
recheck_results: recheck-results.json
review:
  require_human_approval: true
  block_severities: [CRITICAL, SERIOUS, MODERATE]
```

The evidence manifest is deliberately small and may be generated from Zotero
notes or a research ledger:

```json
{
  "schema_version": 1,
  "sources": [
    {
      "citation_key": "smith2024",
      "verified": true,
      "locators": ["p. 14", "pp. 14-15"]
    }
  ]
}
```

Each revision proposal must identify the original paragraph, all match IDs,
the meaning memo, replacement text, verified source evidence, declared citation
additions, and an `unchanged` conclusion direction. Existing citation keys may
not be removed. New keys are allowed only when explicitly declared and present
in the bibliography and evidence manifest.

`recheck-results.json` must identify the ARS integrity stage (`2.5` or `4.5`),
the reviewer, the check timestamp, and the revised paragraph hash. Every
required paragraph records `PASS` independently for Phase D, citation, data,
and facts.

## QA states

- `qa_pending_recheck`: the review copy exists, but changed paragraphs have not
  completed the ARS Phase D/citation/data/fact recheck.
- `qa_pending_human_approval`: deterministic and ARS rechecks passed, but the
  author has not explicitly approved the copy.
- `qa_failed`: a protected invariant changed, evidence is missing, or a blocking
  issue remains.
- `qa_passed`: every changed paragraph was rechecked, no blocking issue remains,
  and a named reviewer explicitly approved the copy.

The QA report records the SHA-256 of both manuscripts. It does not record an
official vendor verdict or promise a target similarity score.

Generated review copies contain an inert
`<!-- originality-review: manifest-required -->` marker. The publication
formatter refuses that copy when `originality_manifest` is omitted; editing the
copy after approval also invalidates the manifest hash.
