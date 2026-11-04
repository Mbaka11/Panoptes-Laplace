"""Field-coverage audit of a SYNTHETIC Takeout-style activity export.

Synthetic only: the record shape is invented for this spike and is NOT a verified
provider schema. No network, persistence, ontology import, or security boundary.
Never infers dwell time from gaps between events or scroll depth from viewed-content
records. Issues use fixed codes and never echo untrusted values. See
account-export-audit.md.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable

MAX_BYTES = 4 * 1024 * 1024
MAX_RECORDS = 10_000
_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?"
    r"(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)\Z"
)
_SAFE_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,39}\Z")
KNOWN_FIELDS = {"header", "title", "titleUrl", "time", "products", "details", "description",
                "subtitles", "durationSeconds", "activityControls"}
# Synthetic title-prefix convention, a heuristic stand-in for source field meanings.
_PREFIXES = {
    "searched for": "searches", "watched": "viewed_content", "viewed": "viewed_content",
    "visited": "viewed_content", "liked": "interactions", "commented on": "interactions",
    "subscribed to": "interactions",
}
CATEGORIES = ("viewed_content", "searches", "interactions")
STATUS_FIELDS = CATEGORIES + ("timestamps", "duration")


class InputLimitError(ValueError):
    """The input cannot be safely inspected within this spike's bounds."""


@dataclass(frozen=True)
class Issue:
    record: int | None  # 0-based index in the top-level list
    line: int | None
    code: str


@dataclass(frozen=True)
class Record:
    index: int
    line: int
    value: dict[str, Any]
    category: str | None  # None means unclassified, not "none of these"
    time: datetime | None


@dataclass(frozen=True)
class Audit:
    sha256: str  # canonical content hash when parseable, else raw-bytes hash
    records: tuple[Record, ...]
    issues: tuple[Issue, ...]
    total_elements: int
    parse_complete: bool
    duplicate_of: str | None = None  # label of the first import with same content


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not _TIMESTAMP.match(value):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc)


def _classify(title: Any) -> str | None:
    if not isinstance(title, str):
        return None
    lowered = title.lstrip().lower()
    for prefix, category in _PREFIXES.items():
        if lowered.startswith(prefix + " ") or lowered == prefix:
            return category
    return None


def inspect_bytes(data: bytes) -> Audit:
    if len(data) > MAX_BYTES:
        raise InputLimitError("input_too_large")
    issues: list[Issue] = []
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return Audit(hashlib.sha256(data).hexdigest(), (), (Issue(None, None, "invalid_utf8"),), 0, False)
    decoder = json.JSONDecoder()
    pos = len(text) - len(text.lstrip())
    if not text[pos:pos + 1] == "[":
        return Audit(hashlib.sha256(data).hexdigest(), (), (Issue(None, 1, "not_a_json_list"),), 0, False)
    pos += 1
    elements: list[tuple[int, int, Any]] = []  # index, line, value
    complete = False
    ws = " \t\r\n"
    while True:
        while pos < len(text) and text[pos] in ws:
            pos += 1
        if pos >= len(text):
            issues.append(Issue(None, _line_of(text, pos), "truncated_list"))
            break
        if text[pos] == "]":
            complete = True
            break
        if len(elements) >= MAX_RECORDS:
            raise InputLimitError("too_many_records")
        try:
            value, end = decoder.raw_decode(text, pos)
        except json.JSONDecodeError:
            issues.append(Issue(len(elements), _line_of(text, pos), "malformed_json_stop"))
            break
        elements.append((len(elements), _line_of(text, pos), value))
        pos = end
        while pos < len(text) and text[pos] in ws:
            pos += 1
        if pos < len(text) and text[pos] == ",":
            pos += 1
        elif pos < len(text) and text[pos] == "]":
            continue
        else:
            issues.append(Issue(len(elements), _line_of(text, pos), "malformed_json_stop"))
            break
    if complete and text[pos + 1:].strip():
        issues.append(Issue(None, _line_of(text, pos + 1), "trailing_content"))
        complete = False
    records: list[Record] = []
    for index, line, value in elements:
        if not isinstance(value, dict):
            issues.append(Issue(index, line, "record_not_object"))
            continue
        parsed_time = _parse_time(value.get("time")) if "time" in value else None
        if "time" not in value:
            issues.append(Issue(index, line, "missing_time"))
        elif parsed_time is None:
            issues.append(Issue(index, line, "invalid_time"))
        category = _classify(value.get("title"))
        if "title" not in value:
            issues.append(Issue(index, line, "missing_title"))
        elif category is None:
            issues.append(Issue(index, line, "unclassified_title"))
        if "products" in value and not (
            isinstance(value["products"], list) and all(isinstance(p, str) for p in value["products"])
        ):
            issues.append(Issue(index, line, "invalid_products"))
        if "durationSeconds" in value:
            d = value["durationSeconds"]
            if isinstance(d, bool) or not isinstance(d, (int, float)) or d < 0 or d != d:
                issues.append(Issue(index, line, "invalid_duration"))
        if set(value) - KNOWN_FIELDS:
            issues.append(Issue(index, line, "unknown_fields"))
        records.append(Record(index, line, value, category, parsed_time))
    if complete:
        canon = json.dumps([e[2] for e in elements], sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    else:
        digest = hashlib.sha256(data).hexdigest()
    return Audit(digest, tuple(records), tuple(issues), len(elements), complete)


def inspect_imports(named: Iterable[tuple[str, bytes]]) -> list[tuple[str, Audit]]:
    """Inspect several imports; a repeat of earlier content is flagged, not re-counted."""
    seen: dict[str, str] = {}
    out: list[tuple[str, Audit]] = []
    for label, data in named:
        audit = inspect_bytes(data)
        first = seen.get(audit.sha256)
        if first is not None:
            audit = Audit(audit.sha256, audit.records, audit.issues + (Issue(None, None, "duplicate_import"),),
                          audit.total_elements, audit.parse_complete, duplicate_of=first)
        else:
            seen[audit.sha256] = label
        out.append((label, audit))
    return out


def _has_duration(record: Record) -> bool:
    d = record.value.get("durationSeconds")
    return not isinstance(d, bool) and isinstance(d, (int, float)) and d >= 0 and d == d


def coverage(audits: list[Audit]) -> dict[str, Any]:
    """Coverage over non-duplicate imports only. Duplicates are listed, never counted."""
    counted = [a for a in audits if a.duplicate_of is None]
    records = [r for a in counted for r in a.records]
    issue_codes = Counter(i.code for a in audits for i in a.issues
                          if a.duplicate_of is None or i.code == "duplicate_import")
    n = len(records)
    cats = Counter(r.category for r in records if r.category)
    times = [r.time for r in records if r.time]
    durations = sum(1 for r in records if _has_duration(r))

    def status(count: int, classifiable: bool = True) -> str:
        if n == 0 or not classifiable:
            return "unknown"
        return "present" if count else "absent"

    unclassified = sum(1 for r in records if r.category is None)
    # A category absent while unclassified records exist is only "absent among classified".
    fields: dict[str, Any] = {}
    for cat in CATEGORIES:
        st = status(cats[cat])
        if st == "absent" and unclassified:
            st = "unknown"
        fields[cat] = {"status": st, "records": cats[cat]}
    fields["timestamps"] = {"status": status(len(times)), "records": len(times)}
    fields["duration"] = {"status": status(durations), "records": durations,
                          "source": "explicit durationSeconds field only; never derived from gaps"}
    missing: Counter[str] = Counter()
    unknown_names: Counter[str] = Counter()
    for r in records:
        for f in ("title", "time", "products", "titleUrl", "durationSeconds"):
            if f not in r.value or r.value[f] in (None, "", []) or (f == "time" and r.time is None):
                missing[f] += 1  # time counts as missing when absent or unparseable
        for k in set(r.value) - KNOWN_FIELDS:
            unknown_names[k if _SAFE_NAME.match(k) else "<redacted>"] += 1
    return {
        "synthetic_only": True,
        "schema_status": "invented synthetic shape; real provider schema unverified",
        "imports": len(list(audits)) if not isinstance(audits, list) else len(audits),
        "duplicate_imports": sum(1 for a in audits if a.duplicate_of is not None),
        "records_counted": n,
        "unclassified_records": unclassified,
        "fields": fields,
        "missingness": {f: missing[f] for f in ("title", "time", "products", "titleUrl", "durationSeconds")},
        "unknown_field_names": dict(sorted(unknown_names.items())),
        "timestamp_min": min(times).isoformat() if times else None,
        "timestamp_max": max(times).isoformat() if times else None,
        "issues": dict(sorted(issue_codes.items())),
        "parse_complete": all(a.parse_complete for a in counted) if counted else None,
        "dwell_time_inferred": False,
        "scroll_depth_inferred": False,
        "collection_window": "unknown",
        "export_completeness": "unknown",
    }


def provenance(audit: Audit) -> list[dict[str, Any]]:
    """Issue provenance only (record index and line); no source values."""
    return [{"record": i.record, "line": i.line, "code": i.code} for i in audit.issues]


def _demo_inputs() -> list[tuple[str, bytes]]:
    root = Path(__file__).resolve().parent / "fixtures" / "account_export"
    return [(n, (root / n).read_bytes())
            for n in ("activity.json", "activity_reformatted_copy.json")]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", required=True,
                        help="read only the bundled synthetic fixtures")
    parser.add_argument("--provenance", action="store_true", help="include issue line provenance")
    args = parser.parse_args(argv)
    results = inspect_imports(_demo_inputs())
    report = coverage([a for _, a in results])
    if args.provenance:
        report["provenance"] = {label: provenance(a) for label, a in results}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
