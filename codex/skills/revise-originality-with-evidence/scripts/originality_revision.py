#!/usr/bin/env python3
"""Local, evidence-grounded originality revision workflow.

The helper normalizes similarity reports, anchors findings to stable Markdown
paragraphs, applies explicitly authored revision proposals to a copy, and
enforces deterministic integrity gates. Semantic rewriting and source reading
remain Codex/author tasks; this module never calls an external model or vendor.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import platform
import re
import sys
from typing import Any, Iterable

import yaml


SCHEMA_VERSION = 1
CLASSIFICATIONS = {"VERBATIM", "CLOSE_MATCH", "SELF_REUSE", "BOILERPLATE"}
SEVERITIES = {"CRITICAL", "SERIOUS", "MODERATE", "MINOR"}
DEFAULT_BLOCK_SEVERITIES = {"CRITICAL", "SERIOUS", "MODERATE"}
REQUIRED_RECHECKS = ("phase_d", "citation", "data", "facts")
ORIGINALITY_GATE_MARKER = "<!-- originality-review: manifest-required -->"
ZERO_WIDTH = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff]")
CITATION_RE = re.compile(r"@([A-Za-z0-9_:.+/-]+)")


class OriginalityError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_dump(value: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def strict_keys(value: dict[str, Any], allowed: set[str], label: str) -> None:
    extra = sorted(set(value) - allowed)
    if extra:
        raise OriginalityError(f"Unsupported {label} field(s): {', '.join(extra)}")


def resolve_inside(base: Path, value: str | None, label: str, *, required: bool = False) -> Path | None:
    if value is None or str(value).strip() == "":
        if required:
            raise OriginalityError(f"Missing required path: {label}")
        return None
    candidate = (base / str(value)).resolve()
    if candidate != base and base not in candidate.parents:
        raise OriginalityError(f"{label} escapes the manuscript project: {value}")
    if required and not candidate.is_file():
        raise OriginalityError(f"Required file is missing: {label} ({value})")
    return candidate


def load_config(config_path: Path) -> tuple[dict[str, Any], Path]:
    config_path = config_path.resolve()
    try:
        value = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise OriginalityError(f"Cannot read originality config: {exc}") from exc
    if not isinstance(value, dict):
        raise OriginalityError("originality.yaml must contain a mapping")
    allowed = {
        "schema_version", "manuscript", "bibliography", "evidence_manifest",
        "ars_integrity_report", "similarity_reports", "languages", "protected",
        "output_root", "revision_proposals", "recheck_results", "review",
        "release_policy",
    }
    strict_keys(value, allowed, "originality config")
    for key in ("schema_version", "manuscript", "bibliography", "evidence_manifest"):
        if key not in value:
            raise OriginalityError(f"Originality contract missing required field: {key}")
    if value["schema_version"] != SCHEMA_VERSION:
        raise OriginalityError(f"Unsupported originality schema_version: {value['schema_version']}")
    languages = value.get("languages", ["zh", "en"])
    if not isinstance(languages, list) or not languages or any(item not in {"zh", "en"} for item in languages):
        raise OriginalityError("languages must contain zh and/or en")
    reports = value.get("similarity_reports", [])
    if not isinstance(reports, list):
        raise OriginalityError("similarity_reports must be a list")
    protected = value.get("protected", {})
    if not isinstance(protected, dict):
        raise OriginalityError("protected must be a mapping")
    strict_keys(protected, {"terms", "sections"}, "protected")
    if any(not isinstance(protected.get(key, []), list) for key in ("terms", "sections")):
        raise OriginalityError("protected.terms and protected.sections must be lists")
    review = value.get("review", {})
    if not isinstance(review, dict):
        raise OriginalityError("review must be a mapping")
    strict_keys(review, {"require_human_approval", "block_severities"}, "review")
    if review.get("require_human_approval", True) is not True:
        raise OriginalityError("Human approval cannot be disabled for originality revision")
    severities = review.get("block_severities", sorted(DEFAULT_BLOCK_SEVERITIES))
    if not isinstance(severities, list) or any(item not in SEVERITIES for item in severities):
        raise OriginalityError("review.block_severities contains an unsupported value")
    release_policy = value.get("release_policy")
    if release_policy is not None:
        if not isinstance(release_policy, dict):
            raise OriginalityError("release_policy must be a mapping")
        strict_keys(
            release_policy,
            {"enabled", "max_overall_similarity_percent", "require_vendor_recheck", "accepted_vendors", "attestation"},
            "release_policy",
        )
        if not isinstance(release_policy.get("enabled", True), bool):
            raise OriginalityError("release_policy.enabled must be true or false")
        maximum = release_policy.get("max_overall_similarity_percent", 10)
        if not isinstance(maximum, (int, float)) or isinstance(maximum, bool) or not 0 <= float(maximum) <= 100:
            raise OriginalityError("release_policy.max_overall_similarity_percent must be between 0 and 100")
        if not isinstance(release_policy.get("require_vendor_recheck", True), bool):
            raise OriginalityError("release_policy.require_vendor_recheck must be true or false")
        vendors = release_policy.get("accepted_vendors", ["cnki", "turnitin", "ithenticate"])
        if not isinstance(vendors, list) or not vendors or any(item not in {"cnki", "turnitin", "ithenticate"} for item in vendors):
            raise OriginalityError("release_policy.accepted_vendors must contain cnki, turnitin, and/or ithenticate")
        if release_policy.get("enabled", True) and release_policy.get("require_vendor_recheck", True):
            if not str(release_policy.get("attestation", "")).strip():
                raise OriginalityError("release_policy.attestation is required when the vendor recheck gate is enabled")
    return value, config_path.parent


class _HTMLText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.suppressed = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.suppressed += 1
        elif tag in {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self.suppressed:
            self.suppressed -= 1
        elif tag in {"p", "div", "li", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.suppressed:
            self.parts.append(data)

    def text(self) -> str:
        return re.sub(r"\n{3,}", "\n\n", "".join(self.parts))


def extract_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise OriginalityError("pypdf is required to import PDF similarity reports") from exc
    try:
        reader = PdfReader(str(path))
        pages: list[str] = []
        for index, page in enumerate(reader.pages, start=1):
            pages.append(f"[REPORT_PAGE {index}]\n{page.extract_text() or ''}")
    except Exception as exc:  # pypdf exposes several parser-specific exceptions
        raise OriginalityError(f"Cannot extract text from PDF report: {exc}") from exc
    text = "\n".join(pages).strip()
    if not text:
        raise OriginalityError("PDF report has no extractable text layer; export HTML/CSV or use the generic template")
    return text


def read_text_report(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf_text(path)
    if suffix in {".html", ".htm"}:
        parser = _HTMLText()
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        return parser.text()
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="replace")
    raise OriginalityError(f"Unsupported text report extension: {suffix}")


FIELD_ALIASES = {
    "matched_excerpt": {"matched_excerpt", "matched text", "text", "excerpt", "匹配片段", "疑似文字", "原文内容"},
    "matched_source": {"matched_source", "source", "source title", "url", "来源", "相似来源"},
    "score": {"score", "similarity", "similarity score", "相似度", "文字复制比"},
    "report_page": {"report_page", "page", "report page", "报告页码", "页码"},
    "paragraph_id": {"paragraph_id", "paragraph id", "段落id", "段落编号"},
    "classification": {"classification", "type", "类型", "判定"},
    "severity": {"severity", "level", "严重度", "等级"},
    "citation_key": {"citation_key", "citation key", "zotero key", "引文键"},
}


def canonical_field(name: str) -> str | None:
    cleaned = re.sub(r"\s+", " ", str(name).strip().lower())
    for canonical, aliases in FIELD_ALIASES.items():
        if cleaned in {alias.lower() for alias in aliases}:
            return canonical
    return None


def detect_vendor(text: str, requested: str = "auto") -> str:
    if requested != "auto":
        return requested
    folded = text.casefold()
    if "ithenticate" in folded:
        return "ithenticate"
    if "turnitin" in folded:
        return "turnitin"
    if "中国知网" in text or "知网" in text or "总文字复制比" in text or "cnki" in folded:
        return "cnki"
    return "generic"


def normalize_classification(value: Any) -> str:
    folded = str(value or "").strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "EXACT": "VERBATIM", "原文照抄": "VERBATIM", "逐字": "VERBATIM",
        "SIMILAR": "CLOSE_MATCH", "近似": "CLOSE_MATCH", "疑似剽窃文字表述": "CLOSE_MATCH",
        "SELF": "SELF_REUSE", "SELF_PLAGIARISM": "SELF_REUSE", "自我重复": "SELF_REUSE",
        "COMMON": "BOILERPLATE", "COMMON_KNOWLEDGE": "BOILERPLATE", "通用表述": "BOILERPLATE",
    }
    result = aliases.get(folded, folded)
    return result if result in CLASSIFICATIONS else "CLOSE_MATCH"


def default_severity(classification: str) -> str:
    return {
        "VERBATIM": "CRITICAL",
        "CLOSE_MATCH": "SERIOUS",
        "SELF_REUSE": "MODERATE",
        "BOILERPLATE": "MINOR",
    }[classification]


def normalize_severity(value: Any, classification: str) -> str:
    folded = str(value or "").strip().upper()
    aliases = {"严重": "SERIOUS", "中等": "MODERATE", "轻微": "MINOR", "致命": "CRITICAL"}
    result = aliases.get(folded, folded)
    return result if result in SEVERITIES else default_severity(classification)


def parse_score(value: Any) -> float | None:
    if value in (None, ""):
        return None
    match = re.search(r"\d+(?:\.\d+)?", str(value))
    return float(match.group(0)) if match else None


OVERALL_SIMILARITY_PATTERNS = (
    re.compile(r"总文字复制比\s*[:：]?\s*(\d{1,3}(?:\.\d+)?)\s*%", flags=re.I),
    re.compile(r"总体相似度\s*[:：]?\s*(\d{1,3}(?:\.\d+)?)\s*%", flags=re.I),
    re.compile(r"overall\s+similarity(?:\s+(?:score|index))?\s*[:：]?\s*(\d{1,3}(?:\.\d+)?)\s*%", flags=re.I),
    re.compile(r"similarity\s+index\s*[:：]?\s*(\d{1,3}(?:\.\d+)?)\s*%", flags=re.I),
)


def extract_overall_similarity(text: str) -> float | None:
    """Extract an explicitly labelled whole-document score, never a match score."""
    found: set[float] = set()
    for pattern in OVERALL_SIMILARITY_PATTERNS:
        for match in pattern.finditer(text):
            value = float(match.group(1))
            if not 0 <= value <= 100:
                raise OriginalityError(f"Overall similarity percentage is outside 0-100: {value}")
            found.add(value)
    if len(found) > 1:
        raise OriginalityError(f"Report contains ambiguous overall similarity values: {sorted(found)}")
    return next(iter(found)) if found else None


def report_summary(path: Path, requested_vendor: str = "auto") -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        raw_text = path.read_text(encoding="utf-8", errors="replace")
        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise OriginalityError(f"Cannot read JSON similarity report: {exc}") from exc
        vendor = detect_vendor(str(payload.get("vendor", "")) if isinstance(payload, dict) else raw_text, requested_vendor)
        explicit = payload.get("overall_similarity_percent") if isinstance(payload, dict) else None
        overall = parse_score(explicit) if explicit is not None else extract_overall_similarity(raw_text)
    else:
        raw_text = path.read_text(encoding="utf-8-sig", errors="replace") if suffix == ".csv" else read_text_report(path)
        vendor = detect_vendor(raw_text, requested_vendor)
        overall = extract_overall_similarity(raw_text)
    if overall is not None and not 0 <= overall <= 100:
        raise OriginalityError(f"Overall similarity percentage is outside 0-100: {overall}")
    return {
        "vendor": vendor,
        "source_report": path.name,
        "source_sha256": sha256_file(path),
        "overall_similarity_percent": overall,
    }


def stable_match_id(vendor: str, record: dict[str, Any]) -> str:
    identity = "\x1f".join(str(record.get(key) or "") for key in (
        "matched_excerpt", "matched_source", "report_page", "paragraph_id", "classification"
    ))
    return f"{vendor}-{sha256_text(identity)[:12]}"


def normalize_record(raw: dict[str, Any], vendor: str) -> dict[str, Any]:
    mapped: dict[str, Any] = {}
    for key, value in raw.items():
        canonical = canonical_field(key) or (key if key in FIELD_ALIASES else None)
        if canonical and value not in (None, ""):
            mapped[canonical] = str(value).strip() if not isinstance(value, (int, float)) else value
    classification = normalize_classification(mapped.get("classification"))
    severity = normalize_severity(mapped.get("severity"), classification)
    record: dict[str, Any] = {
        "vendor": vendor,
        "matched_excerpt": str(mapped.get("matched_excerpt", "")).strip(),
        "matched_source": str(mapped.get("matched_source", "")).strip(),
        "score": parse_score(mapped.get("score")),
        "report_page": str(mapped.get("report_page", "")).strip() or None,
        "paragraph_id": str(mapped.get("paragraph_id", "")).strip() or None,
        "classification": classification,
        "severity": severity,
        "citation_key": str(mapped.get("citation_key", "")).strip() or None,
    }
    record["match_id"] = stable_match_id(vendor, record)
    return record


def parse_json_records(path: Path, vendor: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OriginalityError(f"Cannot read JSON similarity report: {exc}") from exc
    if isinstance(payload, dict):
        vendor = detect_vendor(str(payload.get("vendor", "")), vendor)
        payload = payload.get("matches")
    if not isinstance(payload, list) or any(not isinstance(item, dict) for item in payload):
        raise OriginalityError("JSON report must be a list or an object containing a matches list")
    return [normalize_record(item, vendor) for item in payload]


def parse_csv_records(path: Path, vendor: str) -> list[dict[str, Any]]:
    try:
        text = path.read_text(encoding="utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(text)))
    except (OSError, csv.Error) as exc:
        raise OriginalityError(f"Cannot read CSV similarity report: {exc}") from exc
    if not rows:
        raise OriginalityError("CSV similarity report contains no rows")
    return [normalize_record(row, vendor) for row in rows]


LABEL_PATTERN = re.compile(
    r"^(matched\s*text|excerpt|text|source|similarity(?:\s*score)?|score|page|paragraph\s*id|classification|type|severity|citation\s*key|"
    r"匹配片段|疑似文字|原文内容|来源|相似度|文字复制比|页码|报告页码|段落id|段落编号|类型|判定|严重度|等级|引文键)\s*[:：]\s*(.*)$",
    flags=re.I,
)


def parse_structured_text(text: str, vendor: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    report_page: str | None = None

    def flush() -> None:
        nonlocal current
        if current and any(current.get(key) for key in ("matched_excerpt", "matched_source", "paragraph_id")):
            if report_page and not current.get("report_page"):
                current["report_page"] = report_page
            records.append(normalize_record(current, vendor))
        current = {}

    for raw_line in text.splitlines():
        line = raw_line.strip()
        page_match = re.fullmatch(r"\[REPORT_PAGE\s+(\d+)\]", line, flags=re.I)
        if page_match:
            report_page = page_match.group(1)
            continue
        if re.match(r"^(?:match|匹配)\s*#?\d+\b", line, flags=re.I):
            flush()
            continue
        label = LABEL_PATTERN.match(line)
        if not label:
            continue
        key = canonical_field(label.group(1))
        if key:
            if key == "matched_excerpt" and current.get("matched_excerpt"):
                flush()
            current[key] = label.group(2).strip()
    flush()

    if records:
        return records

    # Vendor summary lines are retained as blocked source-only records. An
    # overall score alone is deliberately ignored because it cannot identify a
    # manuscript paragraph.
    for line in text.splitlines():
        match = re.match(r"^\s*(\d{1,3})\s+(\d{1,3}(?:\.\d+)?)%\s+(.{3,240})$", line)
        if match:
            records.append(normalize_record({"score": match.group(2), "source": match.group(3)}, vendor))
    return records


def import_report_data(path: Path, requested_vendor: str = "auto") -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        raw_text = path.read_text(encoding="utf-8", errors="replace")
        vendor = detect_vendor(raw_text, requested_vendor)
        records = parse_json_records(path, vendor)
    elif suffix == ".csv":
        raw_text = path.read_text(encoding="utf-8-sig", errors="replace")
        vendor = detect_vendor(raw_text, requested_vendor)
        records = parse_csv_records(path, vendor)
    else:
        raw_text = read_text_report(path)
        vendor = detect_vendor(raw_text, requested_vendor)
        records = parse_structured_text(raw_text, vendor)
    if not records:
        raise OriginalityError(
            f"No unambiguous match records were found in {path.name}; this report layout is unsupported. "
            "Use the generic CSV/JSON template instead."
        )
    for record in records:
        record["source_report"] = path.name
    summary = report_summary(path, requested_vendor)
    return {
        "schema_version": SCHEMA_VERSION,
        "vendor": vendor,
        "source_report": path.name,
        "source_sha256": sha256_file(path),
        "overall_similarity_percent": summary["overall_similarity_percent"],
        "matches": records,
        "limitations": [
            "Imported locally from user-exported material",
            "Similarity is a locator, not a plagiarism verdict",
            "Vendor score is preserved only as metadata",
        ],
    }


@dataclass(frozen=True)
class Paragraph:
    paragraph_id: str
    index: int
    start: int
    end: int
    text: str
    sha256: str
    section: str | None
    language: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "paragraph_id": self.paragraph_id,
            "index": self.index,
            "start": self.start,
            "end": self.end,
            "text": self.text,
            "sha256": self.sha256,
            "section": self.section,
            "language": self.language,
        }


def detect_language(text: str) -> str:
    cjk = len(re.findall(r"[\u3400-\u9fff]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    if cjk and latin and min(cjk, latin) / max(cjk, latin) > 0.15:
        return "mixed"
    return "zh" if cjk > latin else "en"


def parse_markdown_paragraphs(text: str) -> list[Paragraph]:
    paragraphs: list[Paragraph] = []
    section: str | None = None
    for match in re.finditer(r"(?ms)(?:\A|(?<=\n\n))(?P<block>\S.*?)(?=\n[ \t]*\n|\Z)", text):
        block = match.group("block")
        stripped = block.strip()
        if not stripped:
            continue
        heading = re.fullmatch(r"#{1,6}\s+(.+)", stripped)
        if heading:
            section = re.sub(r"\s+#+\s*$", "", heading.group(1)).strip()
            continue
        prefix = text[: match.start("block")]
        if (prefix.count("```") % 2) or (prefix.count("~~~") % 2):
            continue
        first = stripped.splitlines()[0].lstrip()
        if first.startswith(("---", "```", "~~~", ">", "|", "![", "<!--")):
            continue
        if re.search(r"^\s*\|?(?:\s*:?-+:?\s*\|){1,}", stripped, flags=re.M):
            continue
        normalized = re.sub(r"\s+", " ", stripped)
        if len(normalized) < 20:
            continue
        digest = sha256_text(normalized)
        index = len(paragraphs) + 1
        paragraphs.append(Paragraph(
            paragraph_id=f"p{index:04d}-{digest[:10]}",
            index=index,
            start=match.start("block"),
            end=match.end("block"),
            text=block,
            sha256=digest,
            section=section,
            language=detect_language(block),
        ))
    return paragraphs


def comparison_text(text: str) -> str:
    text = CITATION_RE.sub("", text).casefold()
    return re.sub(r"[^a-z0-9\u3400-\u9fff]+", "", text)


def ngrams(text: str, size: int = 3) -> set[str]:
    if len(text) <= size:
        return {text} if text else set()
    return {text[index:index + size] for index in range(len(text) - size + 1)}


def lexical_similarity(left: str, right: str) -> float:
    a, b = comparison_text(left), comparison_text(right)
    if not a or not b:
        return 0.0
    sequence = SequenceMatcher(None, a, b, autojunk=False).ratio()
    ga, gb = ngrams(a), ngrams(b)
    jaccard = len(ga & gb) / len(ga | gb) if ga | gb else 0.0
    return max(sequence, jaccard)


def map_match(record: dict[str, Any], paragraphs: list[Paragraph]) -> dict[str, Any]:
    result = dict(record)
    by_id = {paragraph.paragraph_id: paragraph for paragraph in paragraphs}
    requested = record.get("paragraph_id")
    if requested:
        if requested not in by_id:
            result.update({"mapping_status": "invalid_paragraph_id", "requires_semantic_review": True})
        else:
            result.update({"mapping_status": "mapped", "mapping_confidence": 1.0, "requires_semantic_review": False})
        return result
    excerpt = str(record.get("matched_excerpt") or "").strip()
    if not excerpt:
        result.update({"mapping_status": "missing_excerpt", "requires_semantic_review": True})
        return result
    excerpt_language = detect_language(excerpt)
    candidates = [paragraph for paragraph in paragraphs if paragraph.language in {excerpt_language, "mixed"}]
    if not candidates:
        result.update({"mapping_status": "cross_language_requires_semantic_review", "requires_semantic_review": True})
        return result
    ranked = sorted(((lexical_similarity(excerpt, item.text), item) for item in candidates), reverse=True, key=lambda pair: pair[0])
    best_score, best = ranked[0]
    runner_up = ranked[1][0] if len(ranked) > 1 else 0.0
    if best_score < 0.45 or best_score - runner_up < 0.05:
        result.update({
            "mapping_status": "low_or_ambiguous_similarity",
            "mapping_confidence": round(best_score, 4),
            "requires_semantic_review": True,
        })
        return result
    result.update({
        "paragraph_id": best.paragraph_id,
        "mapping_status": "mapped",
        "mapping_confidence": round(best_score, 4),
        "requires_semantic_review": False,
    })
    return result


def parse_ars_integrity_report(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    records: list[dict[str, Any]] = []
    for line in text.splitlines():
        if "|" not in line:
            continue
        severity_match = re.search(r"\b(CRITICAL|SERIOUS|MODERATE|MINOR)\b", line, flags=re.I)
        class_match = re.search(r"\b(VERBATIM|CLOSE_MATCH|SELF[-_ ]?(?:REUSE|PLAGIARISM)|BOILERPLATE)\b", line, flags=re.I)
        if not severity_match or not class_match:
            continue
        paragraph_match = re.search(r"\b(p\d{4}-[0-9a-f]{10})\b", line, flags=re.I)
        url_match = re.search(r"https?://[^\s|>]+", line)
        quoted_match = re.search(r"“([^”]{10,})”|\"([^\"]{20,})\"", line)
        raw = {
            "classification": class_match.group(1),
            "severity": severity_match.group(1),
            "paragraph_id": paragraph_match.group(1) if paragraph_match else "",
            "source": url_match.group(0) if url_match else "ARS Phase D",
            "text": (quoted_match.group(1) or quoted_match.group(2)) if quoted_match else "",
        }
        record = normalize_record(raw, "ars-phase-d")
        record["source_report"] = path.name
        records.append(record)
    return records


def config_paths(config: dict[str, Any], base: Path) -> dict[str, Path | None]:
    return {
        "manuscript": resolve_inside(base, config["manuscript"], "manuscript", required=True),
        "bibliography": resolve_inside(base, config["bibliography"], "bibliography", required=True),
        "evidence": resolve_inside(base, config["evidence_manifest"], "evidence_manifest", required=True),
        "ars": resolve_inside(base, config.get("ars_integrity_report"), "ars_integrity_report", required=bool(config.get("ars_integrity_report"))),
        "proposals": resolve_inside(base, config.get("revision_proposals", "revision-proposals.json"), "revision_proposals", required=False),
        "recheck": resolve_inside(base, config.get("recheck_results", "recheck-results.json"), "recheck_results", required=False),
        "output": resolve_inside(base, config.get("output_root", "originality-output"), "output_root", required=False),
    }


def evaluate_release_policy(config: dict[str, Any], base: Path, revised_path: Path) -> dict[str, Any]:
    policy = config.get("release_policy")
    if not isinstance(policy, dict) or not policy.get("enabled", True):
        return {"status": "not_configured", "enforced": False, "failures": [], "reports": []}

    maximum = float(policy.get("max_overall_similarity_percent", 10))
    require_recheck = policy.get("require_vendor_recheck", True)
    accepted = set(policy.get("accepted_vendors", ["cnki", "turnitin", "ithenticate"]))
    result: dict[str, Any] = {
        "status": "failed",
        "enforced": True,
        "rule": "all_attested_vendor_scores_lte_maximum",
        "max_overall_similarity_percent": maximum,
        "require_vendor_recheck": require_recheck,
        "accepted_vendors": sorted(accepted),
        "reports": [],
        "failures": [],
        "limitations": [
            "Scores are read from user-exported reports and are not generated by this workflow",
            "Passing this policy does not prove originality or guarantee a future vendor score",
        ],
    }
    if not require_recheck:
        result["status"] = "passed"
        return result

    attestation_path = resolve_inside(base, policy.get("attestation"), "release_policy.attestation", required=True)
    assert attestation_path
    attestation = load_json_object(attestation_path, "similarity release attestation")
    strict_keys(attestation, {"schema_version", "manuscript_sha256", "reviewer", "checked_at", "reports"}, "similarity release attestation")
    if attestation.get("schema_version") != SCHEMA_VERSION:
        result["failures"].append("similarity release attestation must use schema_version 1")
    if attestation.get("manuscript_sha256") != sha256_file(revised_path):
        result["failures"].append("similarity release attestation does not match the revised manuscript hash")
    if not str(attestation.get("reviewer", "")).strip():
        result["failures"].append("similarity release attestation reviewer is missing")
    if not str(attestation.get("checked_at", "")).strip():
        result["failures"].append("similarity release attestation timestamp is missing")
    reports = attestation.get("reports")
    if not isinstance(reports, list) or not reports:
        result["failures"].append("similarity release attestation must contain at least one report")
        reports = []
    for index, item in enumerate(reports):
        if not isinstance(item, dict):
            result["failures"].append(f"attested report {index} must be an object")
            continue
        try:
            strict_keys(item, {"path", "sha256", "vendor"}, f"attested report {index}")
            report_path = resolve_inside(base, item.get("path"), f"attested report {index}.path", required=True)
            assert report_path
            actual_hash = sha256_file(report_path)
            if item.get("sha256") != actual_hash:
                result["failures"].append(f"attested report hash mismatch: {report_path.name}")
                continue
            requested_vendor = str(item.get("vendor", "auto")).strip().lower() or "auto"
            if requested_vendor not in accepted:
                result["failures"].append(f"attested report vendor is not accepted: {requested_vendor}")
                continue
            summary = report_summary(report_path, requested_vendor)
            if summary["vendor"] not in accepted:
                result["failures"].append(f"detected report vendor is not accepted: {summary['vendor']}")
                continue
            score = summary["overall_similarity_percent"]
            result["reports"].append({
                "path": str(item.get("path")),
                "sha256": actual_hash,
                "vendor": summary["vendor"],
                "overall_similarity_percent": score,
                "within_policy": score is not None and score <= maximum,
            })
            if score is None:
                result["failures"].append(f"no explicit whole-document similarity score found: {report_path.name}")
            elif score > maximum:
                result["failures"].append(
                    f"attested vendor recheck score {score:g}% exceeds the configured maximum {maximum:g}%: {report_path.name}"
                )
        except OriginalityError as exc:
            result["failures"].append(str(exc))
    if not result["failures"]:
        result["status"] = "passed"
    result["attestation"] = {
        "path": str(policy.get("attestation")),
        "sha256": sha256_file(attestation_path),
        "reviewer": attestation.get("reviewer"),
        "checked_at": attestation.get("checked_at"),
    }
    return result


def attest_release(config_path: Path, report_value: Path, vendor: str, reviewer: str) -> dict[str, Any]:
    config, base = load_config(config_path)
    policy = config.get("release_policy")
    if not isinstance(policy, dict) or not policy.get("enabled", True):
        raise OriginalityError("release_policy is not enabled in originality.yaml")
    if not reviewer.strip():
        raise OriginalityError("--reviewer must be non-empty")
    accepted = set(policy.get("accepted_vendors", ["cnki", "turnitin", "ithenticate"]))
    if vendor not in accepted:
        raise OriginalityError(f"Vendor is not accepted by release_policy: {vendor}")
    output = resolve_inside(base, config.get("output_root", "originality-output"), "output_root", required=False)
    assert output
    revised_path = output / "manuscript-originality-reviewed.md"
    manifest_path = output / "revision-manifest.json"
    if not revised_path.is_file() or not manifest_path.is_file():
        raise OriginalityError("Revision artifacts are missing; run revise before attesting a post-revision report")
    manifest = load_json_object(manifest_path, "revision manifest")
    if manifest.get("revised_manuscript_sha256") != sha256_file(revised_path):
        raise OriginalityError("Revised manuscript changed after the deterministic revision step")
    report_path = report_value.resolve() if report_value.is_absolute() else (base / report_value).resolve()
    if report_path != base and base not in report_path.parents:
        raise OriginalityError(f"release report escapes the manuscript project: {report_value}")
    if not report_path.is_file():
        raise OriginalityError(f"Release report is missing: {report_value}")
    summary = report_summary(report_path, vendor)
    score = summary["overall_similarity_percent"]
    if score is None:
        raise OriginalityError("Release report has no explicit whole-document similarity score")
    attestation_path = resolve_inside(base, policy.get("attestation"), "release_policy.attestation", required=False)
    assert attestation_path
    relative_report = report_path.relative_to(base).as_posix()
    report_item = {"path": relative_report, "sha256": sha256_file(report_path), "vendor": vendor}
    existing: dict[str, Any] = {}
    if attestation_path.is_file():
        existing = load_json_object(attestation_path, "similarity release attestation")
    existing_reports = existing.get("reports", []) if isinstance(existing.get("reports", []), list) else []
    report_index = {
        str(item.get("path")): item
        for item in existing_reports
        if isinstance(item, dict) and str(item.get("path", "")).strip()
    }
    report_index[relative_report] = report_item
    manuscript_hash = sha256_file(revised_path)
    stable_existing = (
        existing.get("manuscript_sha256") == manuscript_hash
        and existing.get("reviewer") == reviewer.strip()
        and report_index == {
            str(item.get("path")): item
            for item in existing_reports
            if isinstance(item, dict) and str(item.get("path", "")).strip()
        }
    )
    attestation = {
        "schema_version": SCHEMA_VERSION,
        "manuscript_sha256": manuscript_hash,
        "reviewer": reviewer.strip(),
        "checked_at": existing.get("checked_at") if stable_existing and existing.get("checked_at") else utc_now(),
        "reports": [report_index[key] for key in sorted(report_index)],
    }
    json_dump(attestation, attestation_path)
    maximum = float(policy.get("max_overall_similarity_percent", 10))
    return {
        "status": "attested",
        "attestation": str(attestation_path),
        "report": relative_report,
        "vendor": vendor,
        "overall_similarity_percent": score,
        "max_overall_similarity_percent": maximum,
        "within_policy": score <= maximum,
    }


def analyze(config_path: Path) -> dict[str, Any]:
    config, base = load_config(config_path)
    paths = config_paths(config, base)
    manuscript = paths["manuscript"]
    output = paths["output"]
    assert manuscript and output
    output.mkdir(parents=True, exist_ok=True)
    manuscript_text = manuscript.read_text(encoding="utf-8")
    paragraphs = parse_markdown_paragraphs(manuscript_text)
    if not paragraphs:
        raise OriginalityError("No eligible narrative paragraphs were found in manuscript.md")

    records: list[dict[str, Any]] = []
    for index, value in enumerate(config.get("similarity_reports", [])):
        report = resolve_inside(base, value, f"similarity_reports[{index}]", required=True)
        assert report
        records.extend(import_report_data(report)["matches"])
    if paths["ars"]:
        records.extend(parse_ars_integrity_report(paths["ars"]))
    deduplicated = {record["match_id"]: record for record in records}
    mapped = [map_match(record, paragraphs) for record in deduplicated.values()]
    paragraph_lookup = {paragraph.paragraph_id: paragraph for paragraph in paragraphs}
    protected_sections = {str(value).casefold() for value in config.get("protected", {}).get("sections", [])}
    for item in mapped:
        paragraph = paragraph_lookup.get(str(item.get("paragraph_id")))
        item["protected_section"] = bool(
            paragraph and paragraph.section and paragraph.section.casefold() in protected_sections
        )
    mapped.sort(key=lambda item: item["match_id"])
    block = set(config.get("review", {}).get("block_severities", DEFAULT_BLOCK_SEVERITIES))
    blocking = [item for item in mapped if item["severity"] in block]
    unresolved = [item["match_id"] for item in blocking if item.get("mapping_status") != "mapped"]
    analysis_value = {
        "schema_version": SCHEMA_VERSION,
        "status": "blocking_issues" if blocking else "clean",
        "manuscript": manuscript.name,
        "manuscript_sha256": sha256_file(manuscript),
        "paragraphs": [paragraph.as_dict() for paragraph in paragraphs],
        "matches": mapped,
        "blocking_match_ids": [item["match_id"] for item in blocking],
        "unresolved_mapping_ids": unresolved,
        "limitations": [
            "Lexical mapping does not establish cross-language plagiarism",
            "All blocking revisions require verified Zotero evidence and ARS recheck",
        ],
    }
    json_dump(analysis_value, output / "analysis.json")
    json_dump({
        "schema_version": SCHEMA_VERSION,
        "matches": mapped,
    }, output / "normalized-matches.json")

    proposal_template = []
    for item in blocking:
        proposal_template.append({
            "proposal_id": f"proposal-{item['match_id']}",
            "paragraph_id": item.get("paragraph_id") or "REQUIRES_SEMANTIC_MAPPING",
            "match_ids": [item["match_id"]],
            "action": "rewrite",
            "meaning_memo": "",
            "replacement": "",
            "source_evidence": [],
            "citation_actions": {"add": [], "remove": []},
            "conclusion_direction": "unchanged",
        })
    json_dump({"schema_version": SCHEMA_VERSION, "proposals": proposal_template}, output / "revision-proposals.template.json")

    rows = ["# Originality rewrite plan", "", f"- Status: `{analysis_value['status']}`", f"- Blocking matches: {len(blocking)}", f"- Unresolved mappings: {len(unresolved)}", ""]
    rows.extend(["| Match | Severity | Class | Paragraph | Mapping |", "|---|---|---|---|---|"])
    for item in mapped:
        rows.append(f"| `{item['match_id']}` | {item['severity']} | {item['classification']} | {item.get('paragraph_id') or 'unmapped'} | {item.get('mapping_status')} |")
    (output / "rewrite-plan.md").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    return {
        "status": analysis_value["status"],
        "analysis": str(output / "analysis.json"),
        "normalized_matches": str(output / "normalized-matches.json"),
        "proposal_template": str(output / "revision-proposals.template.json"),
        "blocking_matches": len(blocking),
        "unresolved_mappings": len(unresolved),
    }


def bibliography_keys(path: Path) -> set[str]:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        items = payload if isinstance(payload, list) else payload.get("items", []) if isinstance(payload, dict) else []
        return {str(item.get("id")) for item in items if isinstance(item, dict) and item.get("id")}
    if path.suffix.lower() == ".bib":
        return set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", path.read_text(encoding="utf-8", errors="replace"), flags=re.I))
    raise OriginalityError("bibliography must be Better BibTeX JSON or BibTeX")


def evidence_index(path: Path) -> dict[str, dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OriginalityError(f"Cannot read evidence manifest: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION or not isinstance(payload.get("sources"), list):
        raise OriginalityError("evidence manifest must use schema_version 1 and contain a sources list")
    result: dict[str, dict[str, Any]] = {}
    for item in payload["sources"]:
        if isinstance(item, dict) and item.get("citation_key"):
            result[str(item["citation_key"])] = item
    return result


def extract_citations(text: str) -> Counter[str]:
    return Counter(CITATION_RE.findall(text))


def extract_numbers(text: str) -> Counter[str]:
    return Counter(re.findall(r"(?<![A-Za-z])[-+]?\d+(?:[.,]\d+)*(?:%|‰)?", text))


def extract_measurements(text: str) -> Counter[str]:
    pattern = r"(?<![A-Za-z0-9])[-+]?\d+(?:[.,]\d+)*\s*(?:%|‰|[A-Za-zµμ°]{1,10}(?:/[A-Za-zµμ°0-9^.-]+)?)\b"
    return Counter(re.sub(r"\s+", "", value).casefold() for value in re.findall(pattern, text))


def extract_cross_refs(text: str) -> Counter[str]:
    return Counter(match.casefold() for match in re.findall(r"\b(?:Table|Figure)\s+\d+[A-Za-z]?|[表图]\s*\d+[A-Za-z]?", text, flags=re.I))


def extract_headings(text: str) -> list[str]:
    return re.findall(r"^#{1,6}\s+.+$", text, flags=re.M)


def extract_images(text: str) -> list[str]:
    return re.findall(r"!\[[^\]]*\]\([^)]+\)", text)


def extract_curly_quotes(text: str) -> Counter[str]:
    return Counter(re.findall(r"“[^”]+”|‘[^’]+’", text))


def assert_equal(label: str, before: Any, after: Any) -> None:
    if before != after:
        raise OriginalityError(f"Protected invariant changed: {label}")


PROPOSAL_KEYS = {
    "proposal_id", "paragraph_id", "match_ids", "action", "meaning_memo",
    "replacement", "source_evidence", "citation_actions", "conclusion_direction",
    "retain_rationale",
}


def validate_source_evidence(items: Any, evidence: dict[str, dict[str, Any]], bib_keys: set[str]) -> list[dict[str, str]]:
    if not isinstance(items, list) or not items:
        raise OriginalityError("Every blocking proposal requires source_evidence")
    normalized: list[dict[str, str]] = []
    for raw in items:
        if not isinstance(raw, dict):
            raise OriginalityError("source_evidence entries must be objects")
        strict_keys(raw, {"citation_key", "locator"}, "source_evidence")
        key = str(raw.get("citation_key", "")).strip()
        locator = str(raw.get("locator", "")).strip()
        if not key or not locator:
            raise OriginalityError("source_evidence requires citation_key and page/location")
        if key not in bib_keys:
            raise OriginalityError(f"Evidence citation key is missing from bibliography: {key}")
        item = evidence.get(key)
        if not item or item.get("verified") is not True:
            raise OriginalityError(f"Zotero evidence is not verified: {key}")
        locators = [str(value).strip() for value in item.get("locators", [])]
        if not locators or locator not in locators:
            raise OriginalityError(f"Evidence locator is not present in the verified manifest: {key} {locator}")
        normalized.append({"citation_key": key, "locator": locator})
    return normalized


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OriginalityError(f"Cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise OriginalityError(f"{label} must be a JSON object")
    return value


def revise(config_path: Path) -> dict[str, Any]:
    config, base = load_config(config_path)
    paths = config_paths(config, base)
    manuscript, bibliography, evidence_path, proposals_path, output = (
        paths["manuscript"], paths["bibliography"], paths["evidence"], paths["proposals"], paths["output"]
    )
    assert manuscript and bibliography and evidence_path and proposals_path and output
    analysis_path = output / "analysis.json"
    if not analysis_path.is_file():
        raise OriginalityError("analysis.json is missing; run analyze first")
    if not proposals_path.is_file():
        raise OriginalityError("revision proposals are missing; complete the generated template first")
    analysis_value = load_json_object(analysis_path, "analysis.json")
    if analysis_value.get("manuscript_sha256") != sha256_file(manuscript):
        raise OriginalityError("manuscript.md changed after analysis; rerun analyze")
    proposals_value = load_json_object(proposals_path, "revision proposals")
    if proposals_value.get("schema_version") != SCHEMA_VERSION or not isinstance(proposals_value.get("proposals"), list):
        raise OriginalityError("revision proposals must use schema_version 1 and contain a proposals list")

    match_index = {item["match_id"]: item for item in analysis_value.get("matches", [])}
    paragraph_index = {item["paragraph_id"]: item for item in analysis_value.get("paragraphs", [])}
    blocking_ids = set(analysis_value.get("blocking_match_ids", []))
    bib_keys = bibliography_keys(bibliography)
    evidence = evidence_index(evidence_path)
    protected_terms = [str(value) for value in config.get("protected", {}).get("terms", [])]
    original_text = manuscript.read_text(encoding="utf-8")
    replacements: list[tuple[int, int, str]] = []
    ledger: list[dict[str, Any]] = []
    covered: set[str] = set()
    seen_paragraphs: set[str] = set()
    declared_additions: Counter[str] = Counter()

    for raw in proposals_value["proposals"]:
        if not isinstance(raw, dict):
            raise OriginalityError("Each revision proposal must be an object")
        strict_keys(raw, PROPOSAL_KEYS, "revision proposal")
        proposal_id = str(raw.get("proposal_id", "")).strip()
        paragraph_id = str(raw.get("paragraph_id", "")).strip()
        match_ids = raw.get("match_ids")
        action = str(raw.get("action", "rewrite")).strip()
        if not proposal_id or paragraph_id not in paragraph_index:
            raise OriginalityError(f"Proposal has an invalid paragraph mapping: {proposal_id or '<unnamed>'}")
        if paragraph_id in seen_paragraphs:
            raise OriginalityError(f"Multiple proposals target the same paragraph: {paragraph_id}")
        seen_paragraphs.add(paragraph_id)
        if not isinstance(match_ids, list) or not match_ids or any(item not in match_index for item in match_ids):
            raise OriginalityError(f"Proposal references an unknown or empty match set: {proposal_id}")
        covered.update(match_ids)
        if action not in {"rewrite", "quote", "retain"}:
            raise OriginalityError(f"Unsupported proposal action: {action}")
        if str(raw.get("conclusion_direction", "")) != "unchanged":
            raise OriginalityError(f"Proposal must attest unchanged conclusion direction: {proposal_id}")
        meaning_memo = str(raw.get("meaning_memo", "")).strip()
        if len(meaning_memo) < 10:
            raise OriginalityError(f"Proposal meaning_memo is missing or too short: {proposal_id}")
        sources = validate_source_evidence(raw.get("source_evidence"), evidence, bib_keys)

        paragraph = paragraph_index[paragraph_id]
        original = original_text[int(paragraph["start"]):int(paragraph["end"])]
        if sha256_text(re.sub(r"\s+", " ", original.strip())) != paragraph["sha256"]:
            raise OriginalityError(f"Paragraph hash changed after analysis: {paragraph_id}")
        replacement = str(raw.get("replacement", ""))
        if action == "retain":
            classes = {match_index[item]["classification"] for item in match_ids}
            if not classes <= {"SELF_REUSE", "BOILERPLATE"}:
                raise OriginalityError("retain is allowed only for contextual self-reuse or boilerplate findings")
            if len(str(raw.get("retain_rationale", "")).strip()) < 10:
                raise OriginalityError(f"Retained text requires a rationale: {proposal_id}")
            replacement = original
        elif not replacement.strip() or replacement.strip() == original.strip():
            raise OriginalityError(f"Rewrite/quote proposal does not provide a changed replacement: {proposal_id}")
        if ZERO_WIDTH.search(replacement):
            raise OriginalityError(f"Zero-width or bidirectional control characters are prohibited: {proposal_id}")
        if re.search(r"\n[ \t]*\n", replacement):
            raise OriginalityError(f"A proposal must replace exactly one semantic paragraph: {proposal_id}")
        for match_id in match_ids:
            excerpt = str(match_index[match_id].get("matched_excerpt") or "")
            if action == "rewrite" and excerpt and lexical_similarity(replacement, excerpt) >= 0.90:
                raise OriginalityError(f"Replacement remains too close to the matched wording: {proposal_id}")
            if excerpt and len(comparison_text(meaning_memo)) >= 30 and lexical_similarity(meaning_memo, excerpt) >= 0.90:
                raise OriginalityError(f"meaning_memo appears copied from the matched wording: {proposal_id}")

        citation_actions = raw.get("citation_actions", {"add": [], "remove": []})
        if not isinstance(citation_actions, dict):
            raise OriginalityError(f"citation_actions must be an object: {proposal_id}")
        strict_keys(citation_actions, {"add", "remove"}, "citation_actions")
        add = citation_actions.get("add", [])
        remove = citation_actions.get("remove", [])
        if not isinstance(add, list) or not isinstance(remove, list):
            raise OriginalityError("citation_actions.add/remove must be lists")
        if remove:
            raise OriginalityError("Existing citation keys cannot be removed by originality revision")
        for key in add:
            if key not in bib_keys or key not in evidence or evidence[key].get("verified") is not True:
                raise OriginalityError(f"Declared citation addition lacks verified evidence: {key}")
            declared_additions[str(key)] += 1

        assert_equal(f"numbers in {paragraph_id}", extract_numbers(original), extract_numbers(replacement))
        assert_equal(f"measurements/units in {paragraph_id}", extract_measurements(original), extract_measurements(replacement))
        assert_equal(f"table/figure references in {paragraph_id}", extract_cross_refs(original), extract_cross_refs(replacement))
        if action != "quote":
            assert_equal(f"curly-quoted text in {paragraph_id}", extract_curly_quotes(original), extract_curly_quotes(replacement))
        elif not re.search(r"[“”‘’\"']", replacement):
            raise OriginalityError(f"quote action requires visibly quoted text: {proposal_id}")
        for term in protected_terms:
            assert_equal(f"protected term '{term}' in {paragraph_id}", original.count(term), replacement.count(term))
        if not (extract_citations(original) <= extract_citations(replacement)):
            raise OriginalityError(f"Existing citation key was removed from {paragraph_id}")
        if action != "retain":
            replacements.append((int(paragraph["start"]), int(paragraph["end"]), replacement.strip()))
        ledger.append({
            "proposal_id": proposal_id,
            "paragraph_id": paragraph_id,
            "match_ids": match_ids,
            "action": action,
            "original": original,
            "replacement": replacement,
            "meaning_memo": meaning_memo,
            "source_evidence": sources,
            "citation_actions": {"add": add, "remove": []},
            "retain_rationale": str(raw.get("retain_rationale", "")).strip() or None,
        })

    missing = sorted(blocking_ids - covered)
    if missing:
        raise OriginalityError("Blocking matches are not covered by revision proposals: " + ", ".join(missing))

    revised_text = original_text
    for start, end, replacement in sorted(replacements, reverse=True):
        revised_text = revised_text[:start] + replacement + revised_text[end:]
    assert_equal("headings", extract_headings(original_text), extract_headings(revised_text))
    assert_equal("images", extract_images(original_text), extract_images(revised_text))
    assert_equal("all numbers", extract_numbers(original_text), extract_numbers(revised_text))
    assert_equal("all measurements/units", extract_measurements(original_text), extract_measurements(revised_text))
    assert_equal("all table/figure references", extract_cross_refs(original_text), extract_cross_refs(revised_text))
    for term in protected_terms:
        assert_equal(f"protected term '{term}'", original_text.count(term), revised_text.count(term))
    before_citations = extract_citations(original_text)
    after_citations = extract_citations(revised_text)
    if after_citations != before_citations + declared_additions:
        raise OriginalityError("Citation changes do not match declared citation additions")

    output.mkdir(parents=True, exist_ok=True)
    revised_path = output / "manuscript-originality-reviewed.md"
    released_text = ORIGINALITY_GATE_MARKER + "\n\n" + revised_text
    revised_path.write_text(released_text, encoding="utf-8", newline="\n")
    json_dump({"schema_version": SCHEMA_VERSION, "changes": ledger}, output / "change-ledger.json")
    ledger_md = ["# Originality revision ledger", ""]
    for item in ledger:
        evidence_label = ", ".join(
            f"{source['citation_key']} {source['locator']}" for source in item["source_evidence"]
        )
        ledger_md.extend([
            f"## {item['proposal_id']} — `{item['paragraph_id']}`",
            "",
            f"- Action: `{item['action']}`",
            f"- Matches: {', '.join(f'`{value}`' for value in item['match_ids'])}",
            f"- Evidence: {evidence_label}",
            f"- Meaning memo: {item['meaning_memo']}",
            "",
            "**Before**",
            "",
            item["original"].strip(),
            "",
            "**After**",
            "",
            item["replacement"].strip(),
            "",
        ])
    (output / "change-ledger.md").write_text("\n".join(ledger_md), encoding="utf-8", newline="\n")

    reviewed_paragraphs = []
    revised_paragraphs = parse_markdown_paragraphs(revised_text)
    for item in ledger:
        original_para = paragraph_index[item["paragraph_id"]]
        # Paragraph order and headings are protected, so the ordinal remains a
        # safe bridge even though the content-derived ID changes.
        revised_para = revised_paragraphs[int(original_para["index"]) - 1]
        reviewed_paragraphs.append({
            "paragraph_id": item["paragraph_id"],
            "revised_paragraph_id": revised_para.paragraph_id,
            "revised_sha256": revised_para.sha256,
            "action": item["action"],
            "required_checks": list(REQUIRED_RECHECKS),
        })
    json_dump({
        "schema_version": SCHEMA_VERSION,
        "paragraphs": reviewed_paragraphs,
        "unresolved_issues": [],
    }, output / "recheck-request.json")

    revision_manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": "qa_pending_recheck",
        "source_manuscript": manuscript.name,
        "source_manuscript_sha256": sha256_file(manuscript),
        "revised_manuscript": revised_path.name,
        "revised_manuscript_sha256": sha256_file(revised_path),
        "reviewed_paragraphs": reviewed_paragraphs,
        "covered_match_ids": sorted(covered),
        "blocking_match_ids": sorted(blocking_ids),
    }
    json_dump(revision_manifest, output / "revision-manifest.json")
    qa = {
        "schema_version": SCHEMA_VERSION,
        "status": "qa_pending_recheck",
        "manuscript": revised_path.name,
        "manuscript_sha256": revision_manifest["revised_manuscript_sha256"],
        "checks": {"deterministic_invariants": "passed", "ars_recheck": "pending", "human_approval": "pending"},
    }
    json_dump(qa, output / "originality-qa-report.json")
    disclosure = (
        "# Draft AI-use disclosure\n\n"
        "Codex assisted with evidence-grounded language revision of identified originality findings. "
        "The authors reviewed the source evidence, retained responsibility for accuracy, originality, citations, "
        "and conclusions, and approved the final manuscript. Adapt this draft to the target journal's current policy.\n"
    )
    (output / "ai-use-disclosure-draft.md").write_text(disclosure, encoding="utf-8", newline="\n")
    json_dump({
        "schema_version": SCHEMA_VERSION,
        "files": {
            manuscript.name: sha256_file(manuscript),
            revised_path.name: sha256_file(revised_path),
            "analysis.json": sha256_file(analysis_path),
            proposals_path.name: sha256_file(proposals_path),
            evidence_path.name: sha256_file(evidence_path),
            bibliography.name: sha256_file(bibliography),
        },
    }, output / "sha256-manifest.json")
    return {
        "status": "qa_pending_recheck",
        "manuscript": str(revised_path),
        "ledger": str(output / "change-ledger.json"),
        "recheck_request": str(output / "recheck-request.json"),
        "qa_report": str(output / "originality-qa-report.json"),
    }


def verify(config_path: Path, *, approve: bool = False, reviewer: str | None = None) -> dict[str, Any]:
    config, base = load_config(config_path)
    paths = config_paths(config, base)
    output, recheck_path = paths["output"], paths["recheck"]
    assert output and recheck_path
    manifest_path = output / "revision-manifest.json"
    revised_path = output / "manuscript-originality-reviewed.md"
    if not manifest_path.is_file() or not revised_path.is_file():
        raise OriginalityError("Revision artifacts are missing; run revise first")
    manifest = load_json_object(manifest_path, "revision manifest")
    if manifest.get("revised_manuscript_sha256") != sha256_file(revised_path):
        raise OriginalityError("Revised manuscript changed after the deterministic revision step")
    if not recheck_path.is_file():
        raise OriginalityError("recheck-results.json is missing; re-run ARS checks on every requested paragraph")
    recheck = load_json_object(recheck_path, "recheck results")
    if recheck.get("schema_version") != SCHEMA_VERSION or not isinstance(recheck.get("paragraphs"), list):
        raise OriginalityError("recheck results must use schema_version 1 and contain a paragraphs list")
    result_index = {str(item.get("paragraph_id")): item for item in recheck["paragraphs"] if isinstance(item, dict)}
    failures: list[str] = []
    if not str(recheck.get("reviewer", "")).strip():
        failures.append("recheck reviewer is missing")
    if not str(recheck.get("checked_at", "")).strip():
        failures.append("recheck timestamp is missing")
    if str(recheck.get("integrity_stage", "")) not in {"2.5", "4.5"}:
        failures.append("recheck integrity_stage must be 2.5 or 4.5")
    for required in manifest.get("reviewed_paragraphs", []):
        paragraph_id = required["paragraph_id"]
        actual = result_index.get(paragraph_id)
        if not actual:
            failures.append(f"missing recheck for {paragraph_id}")
            continue
        if actual.get("revised_sha256") != required.get("revised_sha256"):
            failures.append(f"stale recheck hash for {paragraph_id}")
        for check in REQUIRED_RECHECKS:
            if str(actual.get(check, "")).upper() != "PASS":
                failures.append(f"{check} did not pass for {paragraph_id}")
    block_severities = set(config.get("review", {}).get("block_severities", DEFAULT_BLOCK_SEVERITIES))
    for issue in recheck.get("unresolved_issues", []):
        if isinstance(issue, dict):
            severity = str(issue.get("severity", "SERIOUS")).upper()
            if severity in block_severities:
                failures.append(f"unresolved {severity} issue: {issue.get('id') or issue.get('description') or 'unknown'}")
        elif issue:
            failures.append(f"unresolved issue: {issue}")

    release_policy = evaluate_release_policy(config, base, revised_path)
    failures.extend(f"release policy: {item}" for item in release_policy.get("failures", []))

    status = "qa_failed" if failures else "qa_pending_human_approval"
    approval: dict[str, Any] | None = None
    if approve:
        if failures:
            raise OriginalityError("Cannot approve a revision with failed rechecks: " + "; ".join(failures))
        if not reviewer or not reviewer.strip():
            raise OriginalityError("--approve requires a non-empty --reviewer")
        status = "qa_passed"
        approval = {"reviewer": reviewer.strip(), "approved_at": utc_now(), "explicit": True}
    qa = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "manuscript": revised_path.name,
        "manuscript_sha256": sha256_file(revised_path),
        "source_manuscript_sha256": manifest.get("source_manuscript_sha256"),
        "checks": {
            "deterministic_invariants": "passed",
            "ars_recheck": "failed" if failures else "passed",
            "rechecked_paragraphs": len(manifest.get("reviewed_paragraphs", [])),
            "human_approval": "passed" if approval else "pending",
            "release_similarity_policy": release_policy["status"],
        },
        "recheck_attestation": {
            "reviewer": recheck.get("reviewer"),
            "checked_at": recheck.get("checked_at"),
            "integrity_stage": recheck.get("integrity_stage"),
        },
        "failures": failures,
        "approval": approval,
        "release_policy": release_policy,
        "limitations": [
            "This is not an official CNKI, Turnitin, or iThenticate verdict",
            "The configured percentage is a release gate over an attested vendor report, not a promised or optimized score",
        ],
    }
    json_dump(qa, output / "originality-qa-report.json")
    manifest["status"] = status
    manifest["qa_report"] = "originality-qa-report.json"
    manifest["approval"] = approval
    manifest["release_policy"] = release_policy
    json_dump(manifest, manifest_path)
    return qa


def doctor(self_test: bool = False) -> dict[str, Any]:
    dependencies: dict[str, Any] = {"pyyaml": {"available": True, "version": getattr(yaml, "__version__", "unknown")}}
    try:
        import pypdf
        dependencies["pypdf"] = {"available": True, "version": getattr(pypdf, "__version__", "unknown")}
    except ImportError:
        dependencies["pypdf"] = {"available": False, "version": None}
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "python": {"version": platform.python_version(), "path": sys.executable},
        "dependencies": dependencies,
        "report_adapters": ["cnki", "turnitin", "ithenticate", "generic-json", "generic-csv"],
        "languages": ["zh", "en"],
        "local_only": True,
        "commercial_api_integration": False,
        "self_test": "not_requested",
    }
    if self_test:
        sample = """Turnitin\nMatch 1\nMatched text: Nursing students reported lower stress after the intervention.\nSource: Example source\nSimilarity: 18%\nClassification: CLOSE_MATCH\n"""
        records = parse_structured_text(sample, "turnitin")
        paragraphs = parse_markdown_paragraphs("# Title\n\nNursing students reported lower stress after the intervention [@example2026].\n")
        passed = len(records) == 1 and len(paragraphs) == 1 and map_match(records[0], paragraphs).get("mapping_status") == "mapped"
        result["self_test"] = {"status": "passed" if passed else "failed"}
    result["passed"] = all(item["available"] for item in dependencies.values()) and result["self_test"] != {"status": "failed"}
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local evidence-grounded academic originality revision")
    sub = parser.add_subparsers(dest="command", required=True)
    doctor_cmd = sub.add_parser("doctor", help="Check local report and revision capabilities")
    doctor_cmd.add_argument("--self-test", action="store_true")
    doctor_cmd.add_argument("--json", action="store_true", dest="as_json")
    import_cmd = sub.add_parser("import-report", help="Normalize a user-exported similarity report")
    import_cmd.add_argument("--input", required=True, type=Path)
    import_cmd.add_argument("--vendor", choices=["auto", "cnki", "turnitin", "ithenticate", "generic"], default="auto")
    import_cmd.add_argument("--output", required=True, type=Path)
    analyze_cmd = sub.add_parser("analyze", help="Combine report findings and map them to manuscript paragraphs")
    analyze_cmd.add_argument("--config", required=True, type=Path)
    revise_cmd = sub.add_parser("revise", help="Apply evidence-grounded proposals to a review copy")
    revise_cmd.add_argument("--config", required=True, type=Path)
    attest_cmd = sub.add_parser("attest-release", help="Bind a post-revision vendor report to the revised manuscript")
    attest_cmd.add_argument("--config", required=True, type=Path)
    attest_cmd.add_argument("--report", required=True, type=Path)
    attest_cmd.add_argument("--vendor", required=True, choices=["cnki", "turnitin", "ithenticate"])
    attest_cmd.add_argument("--reviewer", required=True)
    verify_cmd = sub.add_parser("verify", help="Verify ARS rechecks and explicit human approval")
    verify_cmd.add_argument("--config", required=True, type=Path)
    verify_cmd.add_argument("--approve", action="store_true")
    verify_cmd.add_argument("--reviewer")
    return parser


def print_doctor(report: dict[str, Any]) -> None:
    print("Originality revision doctor")
    print(f"- Python: {report['python']['version']} ({report['python']['path']})")
    for name, item in report["dependencies"].items():
        print(f"- {name}: {'available' if item['available'] else 'missing'}" + (f" ({item['version']})" if item.get("version") else ""))
    print("- report adapters: " + ", ".join(report["report_adapters"]))
    print("- processing: local only; no commercial API integration")
    if isinstance(report["self_test"], dict):
        print(f"- self-test: {report['self_test']['status']}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "doctor":
            result = doctor(args.self_test)
            print(json.dumps(result, ensure_ascii=False, indent=2) if args.as_json else "", end="" if args.as_json else "")
            if not args.as_json:
                print_doctor(result)
            return 0 if result["passed"] else 2
        if args.command == "import-report":
            input_path = args.input.resolve()
            if not input_path.is_file():
                raise OriginalityError(f"Report file is missing: {input_path}")
            result = import_report_data(input_path, args.vendor)
            json_dump(result, args.output.resolve())
            print(json.dumps({
                "output": str(args.output.resolve()),
                "vendor": result["vendor"],
                "matches": len(result["matches"]),
                "overall_similarity_percent": result["overall_similarity_percent"],
            }, ensure_ascii=False))
            return 0
        if args.command == "analyze":
            result = analyze(args.config)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if args.command == "revise":
            result = revise(args.config)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if args.command == "attest-release":
            result = attest_release(args.config, args.report, args.vendor, args.reviewer)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["within_policy"] else 4
        if args.command == "verify":
            result = verify(args.config, approve=args.approve, reviewer=args.reviewer)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["status"] == "qa_passed" else (2 if result["status"] == "qa_failed" else 3)
    except (OriginalityError, OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
