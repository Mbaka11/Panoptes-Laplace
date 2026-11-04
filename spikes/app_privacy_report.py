"""Inspect the documented App Privacy Report subset using synthetic data only.

No device access, network I/O, persistence, ontology import, or security boundary.
The CLI only reads the bundled demonstration fixtures. In-memory records preserve
source values; summary() deliberately excludes them. The opt-in coverage report
includes source timestamps, not identifiers or raw lines. See app-privacy-report.md.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any, Iterable

MAX_SNAPSHOT_BYTES = 4 * 1024 * 1024
MAX_TOTAL_BYTES = 16 * 1024 * 1024
MAX_LINE_BYTES = 64 * 1024
MAX_LINES = 10_000
MAX_SNAPSHOTS = 16
# Reject finer-than-microsecond values rather than silently truncating them.
_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?"
    r"(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)\Z"
)
_ACCESS_FIELDS = {"type", "accessor", "broadcaster", "category", "identifier", "kind", "timeStamp"}
_NETWORK_FIELDS = {
    "type", "domain", "firstTimeStamp", "context", "timeStamp", "domainType",
    "initiatedType", "hits", "domainOwner", "bundleID",
}


class InputLimitError(ValueError):
    """The input cannot be safely inspected within this spike's bounds."""


@dataclass(frozen=True)
class Issue:
    line: int | None
    code: str
    severity: str  # Fixed codes only: never echo untrusted source values.


@dataclass(frozen=True)
class Record:
    line: int
    raw_line: str
    value: dict[str, Any] | None
    status: str  # supported, invalid, unsupported


@dataclass(frozen=True)
class AccessInterval:
    source_lines: tuple[int, ...]
    status: str  # complete, missing_begin, missing_end, ambiguous, reversed
    start: datetime | None = None
    end: datetime | None = None

    @property
    def duration_seconds(self) -> float | None:
        if self.status == "complete" and self.start is not None and self.end is not None:
            return (self.end - self.start).total_seconds()
        return None


@dataclass(frozen=True)
class Snapshot:
    sha256: str
    raw_bytes: bytes
    records: tuple[Record, ...]
    intervals: tuple[AccessInterval, ...]
    issues: tuple[Issue, ...]
    physical_lines: int
    blank_lines: int

    @property
    def network_aggregates(self) -> tuple[Record, ...]:
        return tuple(
            record for record in self.records
            if record.status == "supported" and record.value is not None
            and record.value.get("type") == "networkActivity"
        )

    def summary(self) -> dict[str, Any]:
        """Counts and fixed diagnostics only; not a de-identification guarantee."""
        return {
            "physical_lines": self.physical_lines,
            "blank_lines": self.blank_lines,
            "record_status_counts": dict(Counter(r.status for r in self.records)),
            "access_interval_status_counts": dict(Counter(i.status for i in self.intervals)),
            "network_aggregate_records": len(self.network_aggregates),
            "issues": [
                {"line": issue.line, "code": issue.code, "severity": issue.severity}
                for issue in self.issues
            ],
        }

    def coverage(self) -> dict[str, Any]:
        """Describe this synthetic artifact, not device support or completeness.

        Unlike summary(), this includes timestamps and durations. Source line
        references are scoped to this snapshot; no intervals are combined.
        """
        lines_by_status = {
            status: [record.line for record in self.records if record.status == status]
            for status in ("supported", "invalid", "unsupported")
        }
        access = tuple(
            record for record in self.records
            if record.status == "supported" and record.value is not None
            and record.value.get("type") == "access"
        )
        network = self.network_aggregates
        severities = {issue.severity for issue in self.issues}
        diagnostic_state = (
            "errors_present" if "error" in severities
            else "warnings_present" if "warning" in severities else "none_reported"
        )
        data_state = (
            "no_nonblank_records" if not self.records
            else "supported_subset_present" if lines_by_status["supported"]
            else "no_supported_records"
        )
        return {
            **self.summary(),
            "data_state": data_state,
            "diagnostic_state": diagnostic_state,
            "record_lines_by_status": lines_by_status,
            "access": {
                "counting_unit": "source_boundary_records_not_user_actions",
                "granularity": "interval_boundaries",
                "supported_record_count": len(access),
                "source_lines": [record.line for record in access],
                "timestamp_extent": _timestamp_extent(access, ("timeStamp",)),
                "intervals": [
                    {"source_lines": list(interval.source_lines), "status": interval.status,
                     "duration_seconds": interval.duration_seconds}
                    for interval in self.intervals
                ],
            },
            "network_activity": {
                "counting_unit": "source_aggregate_records_not_requests",
                "granularity": "aggregate",
                "supported_record_count": len(network),
                "source_lines": [record.line for record in network],
                "timestamp_extent": _timestamp_extent(network, ("firstTimeStamp", "timeStamp")),
            },
        }


@dataclass(frozen=True)
class Inspection:
    snapshots: tuple[Snapshot, ...]
    # One-based input positions (duplicate input, first identical input).
    duplicate_inputs: tuple[tuple[int, int], ...]
    # First input position for each unique snapshot, in snapshot order.
    snapshot_input_positions: tuple[int, ...]

    def summary(self) -> dict[str, Any]:
        return {
            "scope": "synthetic_app_privacy_report_spike",
            "unique_snapshot_count": len(self.snapshots),
            "duplicate_inputs": [list(pair) for pair in self.duplicate_inputs],
            "network_policy": "preserve_each_snapshot_no_cross_snapshot_sum_or_delta",
            "collection_window": "unknown_unless_supplied_by_source_not_inferred_from_contact_times",
            "snapshots": [snapshot.summary() for snapshot in self.snapshots],
        }

    def coverage_report(self) -> dict[str, Any]:
        """Opt-in synthetic source-quality view; not a production report schema."""
        return {
            "scope": "synthetic_app_privacy_report_coverage",
            "report_version": "synthetic-coverage-v1",
            "evidence_class": "synthetic_input_only_not_device_evidence",
            "unique_snapshot_count": len(self.snapshots),
            "duplicate_inputs": [list(pair) for pair in self.duplicate_inputs],
            "network_policy": "preserve_each_snapshot_no_cross_snapshot_sum_or_delta",
            "timestamp_policy": "supported_source_times_only_not_collection_window_or_freshness",
            "empty_result_policy": "no_records_does_not_prove_no_activity_or_denied_access",
            "unmeasured": {
                "device_support": "not_tested", "provisioning": "not_tested",
                "os_authorization": "not_observed", "participant_scope": "not_applicable_synthetic_only",
                "source_export_success": "not_tested", "recording_enabled_at": "unknown",
                "collection_window": "unknown", "source_generated_at": "unknown",
                "missing_periods": "unknown", "freshness": "not_evaluated",
            },
            "snapshots": [
                {"snapshot_index": index, "first_input_position": position, **snapshot.coverage()}
                for index, (position, snapshot) in enumerate(
                    zip(self.snapshot_input_positions, self.snapshots, strict=True), 1
                )
            ],
        }


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not _TIMESTAMP.fullmatch(value):
        return None
    # -00:00 denotes an unknown local offset in RFC 3339, not known UTC.
    if value.endswith("-00:00"):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        # A legal local year can still overflow Python's UTC range after its
        # offset is applied. Reject that unsupported instant before reporting.
        parsed.astimezone(timezone.utc)
        return parsed
    except (ValueError, OverflowError):
        return None


def _timestamp_extent(records: tuple[Record, ...], fields: tuple[str, ...]) -> dict[str, Any]:
    """UTC extrema of supported source fields, retaining every tied reference.

    These describe only the supplied records, never a report window, collection
    completeness, device freshness, or the timing of individual network hits.
    """
    points: list[tuple[datetime, int, str]] = []
    for record in records:
        if record.status != "supported" or record.value is None:
            continue
        for field in fields:
            stamp = _timestamp(record.value.get(field))
            if stamp is not None:
                points.append((stamp.astimezone(timezone.utc), record.line, field))
    if not points:
        return {"earliest": None, "latest": None}

    def endpoint(stamp: datetime) -> dict[str, Any]:
        return {
            "utc": stamp.isoformat().replace("+00:00", "Z"),
            "source_refs": [
                {"line": line, "field": field}
                for instant, line, field in points if instant == stamp
            ],
        }

    return {
        "earliest": endpoint(min(point[0] for point in points)),
        "latest": endpoint(max(point[0] for point in points)),
    }


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise ValueError("nonfinite_json_number")


def _parse_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError("nonfinite_json_number")
    return parsed


def _parse_int(value: str) -> int:
    if len(value.lstrip("-")) > 64:
        raise ValueError("integer_precision_limit")
    return int(value)


def _validate(value: dict[str, Any], line: int, issues: list[Issue]) -> str:
    local: list[Issue] = []

    def error(code: str) -> None:
        local.append(Issue(line, code, "error"))

    def warning(code: str) -> None:
        local.append(Issue(line, code, "warning"))

    kind = value.get("type")
    if not _nonempty_string(kind):
        issues.append(Issue(line, "missing_or_invalid_record_type", "error"))
        return "invalid"
    if kind not in {"access", "networkActivity"}:
        issues.append(Issue(line, "unsupported_record_type", "warning"))
        return "unsupported"

    fields = _ACCESS_FIELDS if kind == "access" else _NETWORK_FIELDS
    if value.keys() - fields:
        warning("unknown_fields_preserved")

    if kind == "access":
        for name in ("category", "identifier"):
            if not _nonempty_string(value.get(name)):
                error("missing_or_invalid_" + name)
        if value.get("kind") not in ("intervalBegin", "intervalEnd"):
            error("unsupported_access_kind")
        if _timestamp(value.get("timeStamp")) is None:
            error("invalid_timestamp")
        for name in ("accessor", "broadcaster"):
            if name == "broadcaster" and name not in value:
                continue
            actor = value.get(name)
            if not isinstance(actor, dict) or not all(
                _nonempty_string(actor.get(field)) for field in ("identifier", "identifierType")
            ):
                error("invalid_" + name)
            elif actor.keys() - {"identifier", "identifierType"}:
                warning("unknown_nested_fields_preserved")
    else:
        for name in ("domain", "bundleID"):
            if not _nonempty_string(value.get(name)):
                error("missing_or_invalid_" + name)
        hits = value.get("hits")
        if type(hits) is not int or hits < 0:
            error("invalid_hits")
        first = _timestamp(value.get("firstTimeStamp"))
        last = _timestamp(value.get("timeStamp"))
        if first is None or last is None:
            error("invalid_timestamp")
        elif last < first:
            error("reversed_contact_timestamps")
        for name in ("context", "domainOwner", "initiatedType"):
            if name in value and not isinstance(value[name], str):
                error("invalid_optional_network_field")
        if "domainType" in value:
            if type(value["domainType"]) is not int:
                error("invalid_domain_type")
            elif value["domainType"] not in (1, 2):
                warning("unknown_domain_type_preserved")
        if "initiatedType" in value and value["initiatedType"] not in (
            "AppInitiated", "NonAppInitiated"
        ):
            warning("unknown_initiator_type_preserved")

    issues.extend(local)
    return "invalid" if any(issue.severity == "error" for issue in local) else "supported"


def _pair_intervals(records: list[Record], issues: list[Issue]) -> tuple[AccessInterval, ...]:
    groups: dict[str, list[Record]] = defaultdict(list)
    for record in records:
        value = record.value
        if value is not None and value.get("type") == "access":
            identifier = value.get("identifier")
            if _nonempty_string(identifier):
                groups[identifier].append(record)

    intervals: list[AccessInterval] = []
    for group in groups.values():
        lines = tuple(record.line for record in group)
        # Pair only within this snapshot and only when identity is unambiguous.
        identities = {
            json.dumps(
                [r.value.get("accessor"), r.value.get("category"), r.value.get("broadcaster")],
                sort_keys=True, ensure_ascii=True,
            )
            for r in group if r.value is not None
        }
        begins = [r for r in group if r.value is not None and r.value.get("kind") == "intervalBegin"]
        ends = [r for r in group if r.value is not None and r.value.get("kind") == "intervalEnd"]
        if (any(r.status != "supported" for r in group) or len(identities) != 1
                or len(begins) > 1 or len(ends) > 1):
            intervals.append(AccessInterval(lines, "ambiguous"))
            issues.append(Issue(lines[0], "ambiguous_interval", "error"))
            continue
        start = _timestamp(begins[0].value["timeStamp"]) if begins else None
        end = _timestamp(ends[0].value["timeStamp"]) if ends else None
        if start is None or end is None:
            status = "missing_begin" if start is None else "missing_end"
            issues.append(Issue(lines[0], "incomplete_interval", "warning"))
        elif end < start:
            status = "reversed"
            issues.append(Issue(lines[0], "reversed_interval", "error"))
        else:
            status = "complete"
        intervals.append(AccessInterval(lines, status, start, end))
    return tuple(intervals)


def inspect_snapshot(data: bytes) -> Snapshot:
    """Pure in-memory inspection of a synthetic UTF-8 NDJSON snapshot.

    Retains raw input and parsed values; callers must not log/serialize these as
    though sanitized. Invalid lines remain represented rather than being skipped.
    """
    if not isinstance(data, bytes):
        raise TypeError("snapshot input must be bytes")
    if len(data) > MAX_SNAPSHOT_BYTES:
        raise InputLimitError("snapshot_byte_limit")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputLimitError("invalid_utf8") from None
    # NDJSON is newline-delimited, not split on Unicode separators inside strings.
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    if len(lines) > MAX_LINES:
        raise InputLimitError("line_count_limit")
    if any(len(line.encode("utf-8")) > MAX_LINE_BYTES for line in lines):
        raise InputLimitError("line_byte_limit")

    records: list[Record] = []
    issues: list[Issue] = []
    blank_lines = 0
    for number, line in enumerate(lines, 1):
        if not line.strip(" \t\r"):
            blank_lines += 1
            continue
        try:
            value = json.loads(
                line, object_pairs_hook=_object_without_duplicate_keys,
                parse_constant=_reject_constant, parse_float=_parse_float,
                parse_int=_parse_int,
            )
        except (ValueError, RecursionError):
            records.append(Record(number, line, None, "invalid"))
            issues.append(Issue(number, "invalid_json", "error"))
            continue
        if not isinstance(value, dict):
            records.append(Record(number, line, None, "invalid"))
            issues.append(Issue(number, "non_object_record", "error"))
            continue
        status = _validate(value, number, issues)
        records.append(Record(number, line, value, status))

    intervals = _pair_intervals(records, issues)
    return Snapshot(
        hashlib.sha256(data).hexdigest(), data, tuple(records), intervals,
        tuple(issues), len(lines), blank_lines,
    )


def inspect_snapshots(inputs: Iterable[bytes]) -> Inspection:
    """Deduplicate identical artifacts within one call, never add rolling totals.

    Hashes are content identities, not authentication or proof of capture time.
    Separate calls share no state; this is not persistent import idempotency.
    """
    snapshots: list[Snapshot] = []
    duplicates: list[tuple[int, int]] = []
    positions: list[int] = []
    # Exact bytes determine equality, even in the event of a digest collision.
    # Keys retain references to the same bounded bytes, not additional copies.
    seen: dict[bytes, int] = {}
    total_bytes = 0
    for position, data in enumerate(inputs, 1):
        if position > MAX_SNAPSHOTS:
            raise InputLimitError("snapshot_count_limit")
        if not isinstance(data, bytes):
            raise TypeError("snapshot input must be bytes")
        total_bytes += len(data)
        if len(data) > MAX_SNAPSHOT_BYTES:
            raise InputLimitError("snapshot_byte_limit")
        if total_bytes > MAX_TOTAL_BYTES:
            raise InputLimitError("total_byte_limit")
        if data in seen:
            duplicates.append((position, seen[data]))
            continue
        snapshots.append(inspect_snapshot(data))
        positions.append(position)
        seen[data] = position
    return Inspection(tuple(snapshots), tuple(duplicates), tuple(positions))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Synthetic-only App Privacy Report inspection demo.")
    parser.add_argument("--demo", action="store_true", help="read only the bundled synthetic fixtures")
    parser.add_argument("--coverage", action="store_true",
                        help="include source timestamps and line provenance; requires --demo")
    args = parser.parse_args(argv)
    if args.coverage and not args.demo:
        parser.error("--coverage requires --demo")
    if not args.demo:
        parser.print_help()
        return 0
    directory = Path(__file__).parent / "fixtures" / "app_privacy_report"
    try:
        inputs = []
        for name in ("snapshot-a.ndjson", "snapshot-b.ndjson"):
            with (directory / name).open("rb") as handle:
                inputs.append(handle.read(MAX_SNAPSHOT_BYTES + 1))
        # Include a repeated artifact to demonstrate duplicate reporting.
        inspection = inspect_snapshots([*inputs, inputs[0]])
    except (OSError, InputLimitError):
        print("Synthetic fixture inspection failed; check fixture availability and input bounds.")
        return 2
    output = inspection.coverage_report() if args.coverage else inspection.summary()
    print(json.dumps(output, indent=2, sort_keys=True))
    return 1 if any(i.severity == "error" for s in inspection.snapshots for i in s.issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
