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
import os
from pathlib import Path
import re
import tempfile
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


# --- SYN-04: explicit import ledger (digests, times, counts only) -------------

LEDGER_VERSION = "synthetic-import-ledger-v1"
MAX_LEDGER_ENTRIES = 4096
MAX_LEDGER_BYTES = 1024 * 1024
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_LEDGER_ENTRY_FIELDS = {
    "sha256", "imported_at", "byte_count", "physical_lines",
    "supported_records", "invalid_records", "unsupported_records",
}


class LedgerError(ValueError):
    """Ledger path or content is unusable. Messages are fixed codes."""


class ImportLedger:
    """Caller-supplied record of artifact digests already imported.

    Holds only SHA-256 digests, import time and counts; never record values,
    identifiers or domains. path=None keeps it in memory. A path must be chosen
    by the caller and must not be inside this repository. A matching digest is
    treated as the same artifact (a content identity, not authentication); the
    ledger is not tamper-evident, access-controlled, or a workspace boundary.
    """

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        self._entries: dict[str, dict[str, Any]] = {}
        self._path: Path | None = None
        if path is not None:
            resolved = Path(path).resolve()
            if resolved == _REPO_ROOT or _REPO_ROOT in resolved.parents:
                raise LedgerError("ledger_path_inside_repository")
            self._path = resolved
            if resolved.exists():
                self._load(resolved)

    def _load(self, path: Path) -> None:
        try:
            if path.stat().st_size > MAX_LEDGER_BYTES:
                raise LedgerError("ledger_too_large")
            document = json.loads(
                path.read_bytes().decode("utf-8"),
                object_pairs_hook=_object_without_duplicate_keys,
            )
        except LedgerError:
            raise
        except (OSError, ValueError, RecursionError):
            raise LedgerError("ledger_unreadable_or_invalid") from None
        if (not isinstance(document, dict) or document.keys() != {"ledger_version", "entries"}
                or document["ledger_version"] != LEDGER_VERSION
                or not isinstance(document["entries"], list)
                or len(document["entries"]) > MAX_LEDGER_ENTRIES):
            raise LedgerError("ledger_invalid_structure")
        for entry in document["entries"]:
            if (not isinstance(entry, dict) or entry.keys() != _LEDGER_ENTRY_FIELDS
                    or not isinstance(entry["sha256"], str) or not _SHA256.match(entry["sha256"])
                    or _timestamp(entry["imported_at"]) is None
                    or entry["sha256"] in self._entries
                    or any(type(entry[k]) is not int or entry[k] < 0
                           for k in _LEDGER_ENTRY_FIELDS - {"sha256", "imported_at"})):
                raise LedgerError("ledger_invalid_entry")
            self._entries[entry["sha256"]] = dict(entry)

    def __contains__(self, digest: str) -> bool:
        return digest in self._entries

    def __len__(self) -> int:
        return len(self._entries)

    def entries(self) -> list[dict[str, Any]]:
        return [dict(self._entries[key]) for key in sorted(self._entries)]

    def record(self, snapshot: Snapshot, imported_at: datetime) -> None:
        if len(self._entries) >= MAX_LEDGER_ENTRIES and snapshot.sha256 not in self._entries:
            raise LedgerError("ledger_entry_limit")
        counts = Counter(r.status for r in snapshot.records)
        self._entries.setdefault(snapshot.sha256, {
            "sha256": snapshot.sha256,
            "imported_at": imported_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "byte_count": len(snapshot.raw_bytes),
            "physical_lines": snapshot.physical_lines,
            "supported_records": counts["supported"],
            "invalid_records": counts["invalid"],
            "unsupported_records": counts["unsupported"],
        })

    def save(self) -> None:
        """Atomically persist when a path was supplied; no-op in memory."""
        if self._path is None:
            return
        document = {"ledger_version": LEDGER_VERSION, "entries": self.entries()}
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            handle, temporary = tempfile.mkstemp(dir=self._path.parent, suffix=".tmp")
            try:
                with os.fdopen(handle, "w", encoding="utf-8") as stream:
                    json.dump(document, stream, indent=2, sort_keys=True)
                os.replace(temporary, self._path)
            except BaseException:
                try:
                    os.unlink(temporary)
                except OSError:
                    pass
                raise
        except OSError:
            raise LedgerError("ledger_write_failed") from None


@dataclass(frozen=True)
class ImportResult:
    inspection: Inspection  # newly imported artifacts only; positions are original inputs
    already_imported: tuple[tuple[int, str], ...]  # (one-based input position, sha256)

    def summary(self) -> dict[str, Any]:
        return {
            "scope": "synthetic_import_ledger_result",
            "already_imported": [
                {"input_position": position, "sha256": digest}
                for position, digest in self.already_imported
            ],
            "new_import": self.inspection.summary(),
            "activity_policy": "already_imported_artifacts_contribute_no_records_or_counts",
        }


def import_snapshots(
    inputs: Iterable[bytes], ledger: ImportLedger, now: datetime | None = None
) -> ImportResult:
    """Inspect only artifacts whose digest the ledger has not seen, then record them.

    Previously imported artifacts (from earlier calls or processes) are reported
    and contribute no records. Within-call identical repeats are handled by
    inspect_snapshots. The ledger is updated only after every new artifact
    inspected successfully; any limit error leaves it unchanged. now must be
    timezone-aware if supplied (injectable for tests).
    """
    stamp = now if now is not None else datetime.now(timezone.utc)
    if stamp.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    items = list(inputs)
    if len(items) > MAX_SNAPSHOTS:
        raise InputLimitError("snapshot_count_limit")
    fresh: list[bytes] = []
    original: list[int] = []
    already: list[tuple[int, str]] = []
    for position, data in enumerate(items, 1):
        if not isinstance(data, bytes):
            raise TypeError("snapshot input must be bytes")
        digest = hashlib.sha256(data).hexdigest()
        if digest in ledger:
            already.append((position, digest))
        else:
            fresh.append(data)
            original.append(position)
    inspection = inspect_snapshots(fresh)
    remapped = Inspection(
        inspection.snapshots,
        tuple((original[dup - 1], original[first - 1]) for dup, first in inspection.duplicate_inputs),
        tuple(original[pos - 1] for pos in inspection.snapshot_input_positions),
    )
    for snapshot in remapped.snapshots:
        ledger.record(snapshot, stamp)
    ledger.save()
    return ImportResult(remapped, tuple(already))


# --- SYN-03: cross-snapshot network aggregate reconciliation ------------------

def _utc_text(stamp: datetime) -> str:
    return stamp.isoformat().replace("+00:00", "Z")


def _ref(observation: dict[str, Any]) -> dict[str, Any]:
    return {"snapshot_index": observation["snapshot_index"],
            "first_input_position": observation["first_input_position"],
            "line": observation["line"], "reported_total": observation["hits"]}


def reconcile_network_aggregates(inspection: Inspection) -> dict[str, Any]:
    """Per (app, domain) provenance view across snapshots, never a sum or delta.

    Snapshots are ordered per aggregate by the source's own last-contact
    timestamp, not by file order or wall-clock. The latest observed total is one
    snapshot's reported count, not unique traffic. A lower later count is
    flagged as inconsistent/possible window rollover; no negative delta (or any
    delta) is computed. Source identifiers appear here, unlike summary().
    """
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for index, (position, snapshot) in enumerate(
        zip(inspection.snapshot_input_positions, inspection.snapshots, strict=True), 1
    ):
        for record in snapshot.network_aggregates:
            value = record.value
            assert value is not None
            first = _timestamp(value["firstTimeStamp"])
            last = _timestamp(value["timeStamp"])
            assert first is not None and last is not None
            groups[(value["bundleID"], value["domain"])].append({
                "snapshot_index": index, "first_input_position": position,
                "line": record.line, "hits": value["hits"],
                "_first": first.astimezone(timezone.utc), "_last": last.astimezone(timezone.utc),
            })

    aggregates = []
    for (app, domain), observations in sorted(groups.items()):
        observations.sort(key=lambda o: (o["_last"], o["snapshot_index"], o["line"]))
        flags: list[dict[str, Any]] = []
        per_snapshot = Counter(o["snapshot_index"] for o in observations)
        if any(count > 1 for count in per_snapshot.values()):
            flags.append({"code": "multiple_records_in_snapshot_not_combined"})
        for earlier, later in zip(observations, observations[1:]):
            if earlier["snapshot_index"] == later["snapshot_index"]:
                continue
            ref = {"earlier": _ref(earlier), "later": _ref(later)}
            if later["_last"] == earlier["_last"] and later["hits"] != earlier["hits"]:
                flags.append({"code": "same_last_timestamp_different_totals", **ref})
            elif later["hits"] < earlier["hits"]:
                flags.append({"code": "count_decreased_possible_window_rollover", **ref})
            if later["_first"] > earlier["_first"]:
                flags.append({"code": "first_timestamp_advanced_possible_window_rollover", **ref})
        latest = observations[-1]
        tied = [o for o in observations if o["_last"] == latest["_last"]]
        ambiguous_latest = len({o["hits"] for o in tied}) > 1 or len(
            {o["snapshot_index"] for o in tied}) < len(tied)
        aggregates.append({
            "app": app, "domain": domain,
            "observations": [
                {**_ref(o), "first_timestamp_utc": _utc_text(o["_first"]),
                 "last_timestamp_utc": _utc_text(o["_last"])}
                for o in observations
            ],
            "latest_observed": None if ambiguous_latest else {
                **_ref(latest), "last_timestamp_utc": _utc_text(latest["_last"])},
            "first_timestamp_utc": _utc_text(min(o["_first"] for o in observations)),
            "last_timestamp_utc": _utc_text(max(o["_last"] for o in observations)),
            "flags": flags,
            "consistent": not flags,
        })
    return {
        "scope": "synthetic_network_reconciliation",
        "report_version": "synthetic-reconciliation-v1",
        "evidence_class": "synthetic_input_only_not_device_evidence",
        "policy": "per_snapshot_provenance_latest_observed_total_no_sum_no_delta_no_events",
        "ordering": "source_last_contact_timestamp_not_file_order_or_wall_clock",
        "unique_snapshot_count": len(inspection.snapshots),
        "aggregates": aggregates,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Synthetic-only App Privacy Report inspection demo.")
    parser.add_argument("--demo", action="store_true", help="read only the bundled synthetic fixtures")
    parser.add_argument("--coverage", action="store_true",
                        help="include source timestamps and line provenance; requires --demo")
    parser.add_argument("--reconcile", action="store_true",
                        help="add cross-snapshot network reconciliation (no sums or deltas); requires --demo")
    parser.add_argument("--ledger", metavar="PATH",
                        help="import fixtures through a JSON ledger at PATH (outside the repo); requires --demo")
    args = parser.parse_args(argv)
    if args.coverage and not args.demo:
        parser.error("--coverage requires --demo")
    if (args.reconcile or args.ledger) and not args.demo:
        parser.error("--reconcile and --ledger require --demo")
    if args.ledger and args.coverage:
        parser.error("--ledger cannot be combined with --coverage")
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
        repeated = [*inputs, inputs[0]]
        if args.ledger:
            result = import_snapshots(repeated, ImportLedger(args.ledger))
            inspection = result.inspection
        else:
            inspection = inspect_snapshots(repeated)
    except (OSError, InputLimitError, LedgerError):
        print("Synthetic fixture inspection failed; check fixture availability and input bounds.")
        return 2
    if args.ledger:
        output = result.summary()
    else:
        output = inspection.coverage_report() if args.coverage else inspection.summary()
    if args.reconcile:
        output = {**output, "reconciliation": reconcile_network_aggregates(inspection)}
    print(json.dumps(output, indent=2, sort_keys=True))
    return 1 if any(i.severity == "error" for s in inspection.snapshots for i in s.issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
