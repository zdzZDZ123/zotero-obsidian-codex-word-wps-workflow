# KnowledgeBase operating contract

This Obsidian vault is a working system, not a dumping ground. Use Chinese by default unless the source or user asks otherwise.

## Mission

Turn captured material into traceable knowledge, use that knowledge to complete projects, and feed useful outputs and lessons back into the vault.

## Lifecycle

`capture -> 00-Inbox -> distill -> 40-Knowledge -> apply in 10-Projects/50-Outputs -> review -> evolve 90-System`

## Rules

1. Preserve provenance. Every source-derived note must keep its URL/file reference, author when known, and capture date. Never invent missing metadata or claims.
2. Prefer atomic knowledge notes: one durable idea per file, written in the user's own words and linked back to source notes.
3. Connect before creating. Search for related notes and add meaningful Obsidian wiki links; do not create empty links for decoration.
4. Keep projects actionable. Each active project must have one concrete next action and explicit done criteria.
5. Update existing notes when the concept already exists. Avoid near-duplicates.
6. Treat `00-Inbox` as temporary. Distillation must mark the source note `status: processed` and list the notes it produced.
7. Never delete, overwrite source material, or bulk move/rename notes without the user's confirmation.
8. System evolution must be reversible. Record template, taxonomy, skill, or instruction changes in `90-System/Evolution Log.md` with the reason and expected effect.
9. Never store passwords, tokens, private keys, or authentication material in the vault.
10. On Windows PowerShell, read and write Markdown explicitly as UTF-8 (for example, `Get-Content -Encoding UTF8`) so Chinese text is not corrupted.

## Folder contract

- `00-Inbox`: unprocessed captures and rough notes
- `05-Daily`: daily notes and quick work logs
- `10-Projects`: finite outcomes with done criteria
- `20-Areas`: ongoing responsibilities without an end date
- `30-Resources`: reference collections and topic maps
- `40-Knowledge`: evergreen, reusable ideas
- `50-Outputs`: finished drafts, briefs, reports, and deliverables
- `90-System`: manuals, reviews, queues, and evolution history
- `98-Assets`: attachments
- `99-Templates`: note templates

## Definition of done

A knowledge task is done when the useful result is saved, its source is traceable, relevant links exist, the next action is clear where applicable, and any system change is logged.
