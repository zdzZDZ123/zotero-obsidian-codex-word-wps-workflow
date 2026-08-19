# Diary: Mac originality deployment prompt

This task packages the validated originality-revision feature as a single
copy-and-paste prompt for a Mac that already has the rest of the research
workflow connected.

## Step 1: create a source-pinned incremental deployment prompt

### Prompt Context

**Verbatim prompt:** 你现在把你已经在这个电脑上完成的新功能降重，写一个提示词脚本,我需要把它复制粘贴到我的Mac电脑的Codex上面去,然后让Codex根据这个提示词完成你所有现在已经完成的所有工作。
**Interpretation:** Create a self-contained prompt that instructs Codex on another Mac to reproduce the complete version 1.2.0 originality-revision installation and validation performed on this Windows computer.
**Inferred intent:** Allow the user to paste one prompt into Mac Codex and obtain the same evidence-grounded revision, 10% release gate, stale-approval invalidation, report freshness, and Word/WPS blocking behavior without reinstalling the already connected workflow.

### What I did

I created `/prompts/07-macos-sync-originality-v1.2.zh-CN.md` and linked it from both READMEs. The prompt instructs Mac Codex to inspect the live environment, preserve Zotero/Obsidian/Word/WPS and existing skills, obtain only the public GitHub source, verify minimum commit `e599ec9`, run the idempotent macOS installer, use the isolated runtime, execute the full originality suite, verify formatter gating, create a private starter outside the repository, and report exact evidence.

### Why

The existing cross-platform prompt assumes a cloned repository and gives only high-level requirements. The user needs a one-paste incremental handoff that can locate or fetch the source itself and prove parity with all current hardening behavior on a Mac whose base workflow already exists.

### What worked

The repository already contained separate idempotent macOS install and command wrappers, so the new prompt reuses maintained code rather than embedding a second installer. Pinning a minimum public commit prevents an older clone from passing only superficial version checks.

### What didn't work

No implementation failure occurred while creating the prompt.

### What I learned

A deployment prompt needs explicit negative scope as much as commands: preserving existing application settings, refusing destructive Git operations on a dirty checkout, avoiding real manuscript data in tests, and distinguishing a required Codex restart from dynamic skill discovery are essential for reproducible handoff.

### What was tricky

The target Mac may have a clean clone, a dirty user checkout, no clone, or temporary GitHub connectivity failure. The prompt defines safe branches for each case and permits only the official GitHub ZIP as fallback, without assuming a fixed user path.

### What warrants review

Review the minimum commit, private starter destination, Homebrew boundary, and acceptance checklist. On the Mac, confirm actual Word/WPS automation separately when the formatter test marks an editor backend `not_checked`.

### Future work

Run repository validation, commit and publish the prompt, then provide the exact copyable text and public file link to the user.

## Step 2: validate and publish the Mac handoff

### Prompt Context

**Verbatim prompt:** 你现在把你已经在这个电脑上完成的新功能降重，写一个提示词脚本,我需要把它复制粘贴到我的Mac电脑的Codex上面去,然后让Codex根据这个提示词完成你所有现在已经完成的所有工作。
**Interpretation:** Verify that the prompt is privacy-safe and make it directly accessible to the target Mac.
**Inferred intent:** Deliver one authoritative prompt whose pasted copy and public-repository copy are identical.

### What I did

I ran `/scripts/validate-repo.ps1`, checked the Markdown diff, confirmed GitHub CLI authentication and the intended four-file scope, committed the prompt as `4c79251`, pushed `main`, and compared local and remote hashes.

### Why

The prompt tells Mac Codex to trust the public repository and minimum baseline. Publishing the prompt itself makes the handoff inspectable and avoids drift between chat text and maintained instructions.

### What worked

Repository validation passed with 152 files, 5 local skills, and no forbidden artifacts or obvious secrets. GitHub accepted the commit, and local and remote both resolved to `4c79251f77e074bbabdb5970a777495741406378`.

### What didn't work

No validation or publication failure occurred.

### What I learned

The safest copy-paste artifact is still a repository-maintained prompt: users can paste it immediately while another Codex instance can independently verify its origin and minimum implementation commit.

### What was tricky

The prompt must authorize useful autonomous progress without broadening authority to overwrite a dirty checkout, install Homebrew, expose private vault content, or claim editor tests passed when macOS marks them `not_checked`.

### What warrants review

On the target Mac, verify that Codex reports the exact source commit, installed skill hash, test count, private starter location, and any Word/WPS backend marked `not_checked`.

### Future work

No repository work remains. Paste the published prompt into Mac Codex and let it execute the acceptance checklist.
