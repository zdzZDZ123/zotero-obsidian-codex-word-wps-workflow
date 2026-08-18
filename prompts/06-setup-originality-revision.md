# Add evidence-grounded originality revision

Inspect this cloned repository and the existing Zotero–Obsidian–Codex workflow.
Install only the repository's `revise-originality-with-evidence` skill and its
isolated Python runtime. Preserve all existing Zotero, Obsidian, Codex,
Microsoft Word, and WPS settings.

Requirements:

1. Detect the operating system and run the matching idempotent installer under
   `scripts/`.
2. Run `doctor --self-test` through the platform wrapper.
3. Copy `assets/project-starter` into a new private test directory, not into the
   public repository, and explain the required Zotero evidence fields.
4. Confirm that `/skills` can discover `revise-originality-with-evidence` after
   Codex restarts.
5. Do not configure commercial similarity accounts or APIs, upload a manuscript,
   scrape a report portal, or weaken the evidence and human-approval gates.
6. Report actual versions, commands, outputs, and any deviation. Do not claim
   installation complete if the self-test fails.
