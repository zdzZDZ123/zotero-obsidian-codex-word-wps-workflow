# Prompt 01 — Configure Obsidian on another computer

Copy the prompt below into Codex on the target computer.

---

You are deploying the Obsidian side of an open Zotero–Obsidian–Codex research workflow. Work autonomously and finish the runtime validation; do not stop at a written plan.

Repository: this cloned repository. Read `README.zh-CN.md`, `docs/component-lock.json`, `docs/security-model.md`, and `obsidian/vault-template/AGENTS.md` first.

Requirements:

1. Detect the operating system, architecture, existing Obsidian installation, existing Vaults, Codex CLI, and Git. Preserve existing user data. Do not delete or overwrite an existing Vault without making a reversible backup and reporting the action.
2. Do not look for or require a replication ZIP/installer package. Install Obsidian from its official source if missing.
3. Create a new research Vault from `obsidian/vault-template`, or merge only missing workflow files into the user-selected empty/test Vault. Preserve dot-directories such as `.obsidian`, `.agents`, and `.claudian`.
4. Install the 11 community plugins listed in `docs/component-lock.json` from the official Obsidian registry or each plugin's official release source. Prefer the pinned versions. If a pinned release is incompatible or unavailable, install the latest compatible official version and record the deviation. Never download plugin binaries from an unverified bundle.
5. Verify the supplied settings: new notes `00-Inbox`, attachments `98-Assets`, templates `99-Templates`, daily notes `05-Daily` with `YYYY-MM-DD`, Monday calendar start, Dataview inline queries enabled and JavaScript queries disabled, local Git snapshot interval 30 minutes with push/pull disabled by default, and Claudian configured for Codex.
6. Discover the actual Codex executable path on this computer. Configure Claudian provider `codex`, model `gpt-5.6-sol`, reasoning effort `high`, permission mode `normal`, safe mode `workspace-write`, locale `zh-CN`, and right-sidebar placement. Do not copy an absolute path from another computer.
7. Open the Vault, enable the supplied CSS snippet, confirm the Home page and dashboards render, create one disposable capture note from a template, and verify the five local Skills are readable.
8. Run the OS-appropriate audit script from `scripts/`. Report installed versions, deviations, missing items, and validation results. Do not print credentials or private note contents.

Success means Obsidian opens the new Vault, all required plugins load, templates and local Skills are present, and Claudian can invoke the local Codex CLI in this Vault.
