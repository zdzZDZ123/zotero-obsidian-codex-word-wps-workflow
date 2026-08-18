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
release_policy:
  enabled: true
  max_overall_similarity_percent: 10
  require_vendor_recheck: true
  max_report_age_days: 30
  require_report_after_revision: true
  accepted_vendors: [cnki, turnitin, ithenticate]
  attestation: similarity-release-attestation.json
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

When `release_policy` is enabled, `similarity-release-attestation.json` binds
the exact revised manuscript hash to one or more user-exported post-revision
vendor reports. Each report entry records its project-relative path, SHA-256,
vendor, generation time, and timestamp source. The helper reads only an explicitly labelled whole-document score
such as `Overall Similarity` or `总文字复制比`; a per-match percentage cannot
satisfy this gate. Every attested accepted-vendor score must be at or below the
configured maximum. Missing, stale, ambiguous, unsupported, or higher-scoring
reports keep the QA state failed and therefore block Word/WPS formatting.
The default contract also rejects reports older than 30 days or generated
before the current revised manuscript. Re-attesting the same vendor replaces
its prior report and invalidates any earlier manuscript approval immediately.

This is a publication policy gate, not a prediction or guarantee. The report
remains the user's vendor-exported evidence, and a later database or settings
change can produce a different score.

Use `attest-release` after `revise` to populate the attestation safely. The
command refuses reports outside the private project, unsupported vendors,
missing or conflicting vendor markers, missing whole-document labels, and
stale revised-manuscript artifacts. If `--report-generated-at` is omitted, the
report file modification time is recorded explicitly as `file_mtime`.

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
  issue remains, including a failed configured release-similarity policy.
- `qa_passed`: every changed paragraph was rechecked, no blocking issue remains,
  and a named reviewer explicitly approved the copy.

The QA report records the SHA-256 of both manuscripts. It does not record an
official vendor verdict or promise a target similarity score.

Generated review copies contain an inert
`<!-- originality-review: manifest-required -->` marker. The publication
formatter refuses that copy when `originality_manifest` is omitted; editing the
copy after approval also invalidates the manifest hash.
