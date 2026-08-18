# Diary: add an attested similarity release policy

This task adds a fail-closed publication gate after evidence-grounded revision
and before Word/WPS formatting. The gate reads a user-exported vendor report;
it does not generate, predict, or guarantee a similarity score.

## Step 1: implement the policy contract and verifier

### Prompt Context

**Verbatim prompt:** 允许
**Interpretation:** The user authorized the previously proposed rule that a user-exported official report above 10% blocks publication formatting.
**Inferred intent:** Make the workflow refuse Word/WPS release until an attested post-revision whole-document score is no higher than 10%, while preserving the academic-integrity boundary.

### What I did

I extended `/codex/skills/revise-originality-with-evidence/scripts/originality_revision.py` with explicit whole-document score parsing, a hash-bound post-revision report attestation, accepted-vendor checks, and a configurable release policy. I also updated the JSON schema, starter project, workflow contract, skill instructions, English and Chinese documentation, and added a starter attestation file.

### Why

The previous QA gate proved evidence traceability and semantic integrity but did not enforce a user-defined submission threshold from a post-revision vendor report. The new contract closes that release gap without treating a match-level percentage as a whole-document result.

### What worked

The existing QA manifest already formed the single gate consumed by the formatter, so the policy could remain inside originality verification. Word/WPS continues to accept only `qa_passed` and needs no score-specific logic.

### What didn't work

The first `apply_patch` call attempted two update operations against the same Python file and failed with `apply_patch verification failed: invalid patch: multiple operations target ...originality_revision.py`. I combined the hunks into one update operation and the patch applied cleanly. A later documentation patch used an incorrect wrapped context line and failed without changing files; retrying with the exact adjacent lines succeeded.

The first test command used bundled Codex Python and failed during collection
with `ModuleNotFoundError: No module named 'yaml'`. The command used the bundled
`<CODEX_RUNTIME>/python.exe -m unittest discover -s codex/skills/revise-originality-with-evidence/tests -v` entry point.
I reran the suite with the feature's installed isolated runtime at
`<CODEX_HOME>/runtimes/originality-revision/Scripts/python.exe`,
which contains the pinned dependencies.

The first repository validation then failed with
`Private absolute path pattern in: docs/diary/2026-08-19-similarity-release-policy.md`
because those diagnostic paths contained the local Windows account name. I
replaced them with portable runtime placeholders before rerunning validation.

### What I learned

The synthetic 21% CNKI fixture is a match-level value labelled `相似度`, not a whole-document `总文字复制比`. Whole-document parsing must therefore require an unambiguous summary label so the two cannot be conflated.

### What was tricky

The gate has to bind a mutable external report to the exact revised manuscript even though commercial report formats do not expose a portable manuscript hash. A local attestation records both SHA-256 values and a named reviewer while keeping the report private and out of the public repository.

### What warrants review

Review score-label patterns, the `release_policy` schema, `evaluate_release_policy`, and tests covering a 21% block and 9.8% pass. Confirm that legacy projects without `release_policy` remain backward compatible.

### Future work

Vendor layouts can change. Add a new explicit whole-document label only after validating it against a lawfully exported, privacy-safe fixture; ambiguous layouts must continue to fail closed.

## Step 2: validate the release gate and installed workflow

### Prompt Context

**Verbatim prompt:** 允许
**Interpretation:** Complete and validate the authorized 10% release gate in the live local workflow.
**Inferred intent:** Ensure that the policy genuinely blocks a high post-revision score before Word/WPS and remains usable through the installed command wrappers.

### What I did

I added an idempotent `attest-release` command so users do not manually calculate hashes. It binds the revised manuscript, vendor report, reviewer, and timestamp; returns exit code `4` when a validly recorded report exceeds policy; and leaves `verify` unable to emit `qa_passed`. I ran the originality suite, the formatter integration suite, the skill validator, repository validation, the idempotent Windows installer, and the installed `doctor --self-test` command.

### Why

A configuration field alone would be easy to misuse. Observable blocked and passing cases, a safe attestation command, installed-runtime validation, and the existing formatter gate together demonstrate the actual transition from report evidence to Word/WPS eligibility.

### What worked

All 15 originality tests passed, including a 21% block, a 9.8% pass, whole-document-versus-match-score separation, attestation idempotence, stale hash protection, and existing scientific invariants. All 9 publication-formatting tests passed, including the WPS-backed end-to-end path. `quick_validate.py` reported `Skill is valid!`; repository validation reported 149 files, 5 local skills, and no forbidden artifacts or obvious secrets. The installed doctor self-test passed with Python 3.12.13, PyYAML 6.0.3, and pypdf 6.16.1, and the installed helper hash matched the repository helper.

### What didn't work

Before the successful formatter run, I guessed the runtime directory as `submission-formatting`; PowerShell failed with `Formatting runtime missing: <CODEX_HOME>/runtimes/submission-formatting/Scripts/python.exe`. Inspecting the installed runtimes showed the correct directory was `publication-formatting`, after which all 9 tests passed.

The first skill validation attempt failed with `UnicodeDecodeError: 'gbk' codec can't decode byte 0xae in position 4876: illegal multibyte sequence` because the validator used the Windows locale default. Setting `PYTHONUTF8=1` made the same validator read the bilingual skill correctly and it passed.

GitHub CLI authentication and repository discovery succeeded, but publication
was blocked by the network. Two ordinary `git push origin main` attempts failed
with `Recv failure: Connection was reset`; a final HTTP/1.1 attempt failed with
`Failed to connect to github.com port 443 after 21064 ms: Could not connect to server`.
No remote ref changed, so the validated commits remain local and the branch is
two commits ahead of `origin/main`.

### What I learned

The publication formatter needs no threshold-specific branch: it already refuses every originality manifest whose state is not `qa_passed`. Keeping score policy in the originality layer preserves the content-versus-formatting boundary and makes Word and WPS behavior identical.

### What was tricky

Calling a report “official” would overstate what local code can authenticate. The final contract therefore calls it an attested, user-exported vendor report and records this limitation in QA output while still enforcing the configured numeric threshold.

### What warrants review

Review the accepted whole-document label patterns and the default `<= 10%` policy. For a real manuscript, confirm the exported report belongs to the exact reviewed Markdown represented by the attested hash before giving named approval.

### Future work

No implementation work remains for this gate. Push the two local commits after
GitHub connectivity returns. New vendor formats should be added only with
privacy-safe fixtures and explicit whole-document labels.

## Step 3: harden report replacement and stale-approval behavior

### Prompt Context

**Verbatim prompt:** 继续完善
**Interpretation:** Continue improving the implemented release gate without weakening its academic-integrity boundary.
**Inferred intent:** Make the 10% policy reliable under repeated real-world rechecks, report replacement, stale files, and previously approved manuscripts.

### What I did

I audited the approval and attestation state transitions, then updated `/codex/skills/revise-originality-with-evidence/scripts/originality_revision.py`. A new attestation now clears any prior approval before returning, replaces the prior report from the same vendor, verifies that the report's internal vendor marker matches the declaration, and records a report generation timestamp. The verifier rejects reports older than the configured age or generated before the current revision, persists rejected approval attempts as `qa_failed`, separates ARS failures from release-policy failures, and emits machine-readable next actions. I expanded the schema, starter, skill contract, report-import guidance, bilingual documentation, component lock, and privacy-safe fixtures.

### Why

The first release-gate version could leave an already-written `qa_passed` file on disk when a direct approval attempt failed after swapping reports. It also accumulated old and new reports from the same vendor and trusted the declared vendor without checking the report marker. Those behaviors could either block legitimate progress or let a stale formatter approval survive longer than intended.

### What worked

All 19 originality tests passed. They now cover atomic invalidation after a previously passed 8% report is replaced by a 21% report, same-vendor replacement, CNKI `总文字复制比`, conflicting summary scores, vendor-marker mismatch, stale report rejection, persisted rejected approval, attestation idempotence, and all earlier evidence and scientific-invariant checks.

### What didn't work

The first config patch included an unrelated `utc_now` context hunk in the wrong location and failed with `apply_patch verification failed: Failed to find expected lines ... def utc_now() -> str`. No file changed. I split the patch into focused config and helper updates, which applied successfully.

### What I learned

The most important safety property is not the numeric comparison itself but immediate revocation: every change to the report evidence must invalidate the formatter-facing approval synchronously. Vendor identity and report age also need to be evidence fields, not assumptions derived from filenames.

### What was tricky

Report export timestamps are not consistently embedded in vendor documents. The CLI accepts an explicit ISO-8601 time and otherwise records file modification time with `timestamp_source: file_mtime`, making the weaker provenance visible instead of silently presenting it as vendor metadata.

### What warrants review

Review the 30-day default, whether a specific institution requires a shorter window, and whether file modification time is acceptable when `--report-generated-at` is omitted. Confirm that the formatter continues to reject the immediately invalidated manifest before any WPS or Word automation starts.

### Future work

Run the complete formatter/WPS regression, sync skill version 1.2.0 into the local Codex installation, validate the public repository, commit, and retry GitHub publication once.

## Step 4: validate version 1.2.0 across the installed pipeline

### Prompt Context

**Verbatim prompt:** 继续完善
**Interpretation:** Finish the hardening pass with runtime and cross-layer verification.
**Inferred intent:** Prove that stricter originality state transitions do not break Word/WPS submission formatting or local installation.

### What I did

I ran the 19-test originality suite, validated all JSON contracts, ran `quick_validate.py`, executed all 9 publication-formatting tests including the WPS backend, ran the repository privacy validator, reinstalled the skill idempotently, executed the installed `doctor --self-test`, and compared the installed helper SHA-256 with the repository source.

### Why

The release policy is consumed indirectly by Word/WPS through `qa_passed`. Cross-layer tests are therefore required to show that immediate approval invalidation blocks stale output while valid manifests still reach the existing editor backend.

### What worked

All 19 originality tests and all 9 formatting tests passed. The skill validator reported `Skill is valid!`; repository validation reported 150 files, 5 local skills, and no forbidden artifacts or obvious secrets. The installed doctor passed with Python 3.12.13, PyYAML 6.0.3, and pypdf 6.16.1. The installed helper hash exactly matched the version 1.2.0 repository helper.

### What didn't work

No new runtime, validation, or integration failures occurred in this step.

### What I learned

The existing formatter contract remains a useful narrow boundary: it does not need to understand percentages, vendors, or timestamps because the originality layer now revokes `qa_passed` atomically whenever report evidence changes.

### What was tricky

The public fixture needed to prove Chinese whole-document parsing without resembling a private manuscript or copyrighted report. A minimal synthetic HTML file contains only a vendor marker and `总文字复制比`.

### What warrants review

Review `/codex/skills/revise-originality-with-evidence/tests/test_originality_revision.py` for state-transition coverage and `/docs/originality-revision.md` for the operator-facing timestamp guidance.

### Future work

Commit this hardening pass and attempt one bounded GitHub push. If network access fails again, preserve a clean local branch and report the exact blocker.
