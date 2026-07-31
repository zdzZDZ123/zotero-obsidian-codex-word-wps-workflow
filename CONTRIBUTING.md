# Contributing

Contributions are welcome when they improve reproducibility, traceability, privacy, or cross-platform behavior.

1. Keep third-party binaries and personal research data out of the repository.
2. Update `docs/component-lock.json` and `docs/plugin-matrix.md` together when changing a component.
3. If a version changes, state whether the end-to-end acceptance test still passes.
4. Run `pwsh ./scripts/validate-repo.ps1`.
5. Describe the systems tested and any deviations in the pull request.

For workflow changes, the strongest evidence is a sanitized runtime trace showing: Zotero item lookup → real full-text/page read → Obsidian provenance note → Zotero child-note write/readback.
