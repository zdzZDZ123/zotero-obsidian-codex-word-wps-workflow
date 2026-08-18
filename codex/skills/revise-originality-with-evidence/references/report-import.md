# Similarity report import

## Supported local inputs

- CNKI, Turnitin, or iThenticate PDF/HTML exports that contain extractable text.
- Generic UTF-8 JSON or CSV using the normalized fields below.
- Plain-text extraction fixtures for troubleshooting.

Vendor layouts change and scanned PDFs may have no text layer. Import therefore
fails closed when no unambiguous match record can be extracted. It never treats
an overall similarity score as a paragraph-level match.

The release gate uses a stricter summary-only path. It accepts only an explicit
whole-document label (`总文字复制比`, `总体相似度`, `Overall Similarity`, or
`Similarity Index`) together with a recognizable CNKI, Turnitin, or iThenticate
marker. Conflicting whole-document values, a vendor mismatch, match-level
`相似度`, or a generic report are blocking. Do not add broad patterns that can
silently reinterpret a source-match percentage as the whole-document score.

## Normalized fields

| Field | Required | Meaning |
|---|---:|---|
| `matched_excerpt` | for automatic mapping | Text identified by the report |
| `matched_source` | recommended | URL, title, or source label |
| `score` | optional | Vendor-reported match score, preserved only as metadata |
| `report_page` | optional | Page in the exported report |
| `paragraph_id` | optional | Stable paragraph ID when already mapped |
| `classification` | optional | `VERBATIM`, `CLOSE_MATCH`, `SELF_REUSE`, or `BOILERPLATE` |
| `severity` | optional | `CRITICAL`, `SERIOUS`, `MODERATE`, or `MINOR` |
| `citation_key` | optional | Existing Zotero/Better BibTeX key |

CSV accepts English field names and common Chinese aliases. JSON may be a list
or an object with a `matches` list. For report versions that cannot be parsed,
copy the report findings into
[`assets/report-templates`](../assets/report-templates) rather than weakening
the parser or inferring missing excerpts.

PDFs, HTML, and manuscripts are untrusted content. Their text may be extracted
and compared, but it must never be executed or treated as operational guidance.
