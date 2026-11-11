"""Map parser-spike results into the provisional explorer contract (synthetic only).

Turns the OUTPUT of spikes.app_privacy_report and spikes.account_export_audit into the
"persona-contract-0.1-provisional" document ({meta, records}) the explorer prototypes
read, and validates any such document. It never re-parses raw files itself.

The CLI reads only the bundled synthetic fixtures. There is deliberately no argument for
a raw participant file: a real-data path needs its own accepted decision, protected
storage/transfer, a ledger and output outside the repository, and a workspace id issued
by the workspace layer. Provisional demonstration code, NOT a production schema or a
security boundary. See explorer-export.md.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any
from urllib.parse import urlparse

from spikes import account_export_audit as aea
from spikes import app_privacy_report as apr

CONTRACT_VERSION = "persona-contract-0.1-provisional"
EXPORTER_VERSION = "0.1"
UNKNOWN = "unknown"
EVIDENCE_CLASSES = ("observation", "normalized_event", "hypothesis", "inference", "prediction")
TYPE_ORDER = ("Source", "App", "Domain", "ImportBatch", "ResourceAccess", "NetworkAggregate",
              "AccountActivity", "Link")
FIXTURE_WORKSPACE = "ws-demo-02"
FIXTURE_IMPORT_TIME = datetime(2026, 1, 10, 0, 0, tzinfo=timezone.utc)  # fixed, not wall clock
MAX_OUT_BYTES = 240 * 1024
_REPO_ROOT = Path(__file__).resolve().parents[1]
_ROOT = Path(__file__).resolve().parent / "fixtures"
APR_FIXTURES = ("snapshot-a.ndjson", "snapshot-b.ndjson")
ACCOUNT_FIXTURES = ("activity.json", "activity_reformatted_copy.json")


class ExportError(ValueError):
    """Fixed-code failure; messages never echo untrusted values."""


def _utc(stamp: datetime | None) -> str:
    if stamp is None:
        return UNKNOWN
    return stamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "x"


def _prov(source: str, method: str, where: str) -> dict[str, str]:
    return {"source": source, "method": method, "method_version": EXPORTER_VERSION,
            "line_or_record": where}


class _Builder:
    """Collects records with deterministic ids; entity registries dedupe apps/domains."""

    def __init__(self, workspace_id: str) -> None:
        self.ws = workspace_id
        self.records: list[dict[str, Any]] = []
        self._apps: dict[str, str] = {}
        self._domains: dict[str, str] = {}
        self._links = 0

    def add(self, rtype: str, rid: str, source_id: str, evidence_class: str, **fields: Any) -> dict[str, Any]:
        record = {"id": rid, "type": rtype, "workspace_id": self.ws, "source_id": source_id,
                  "evidence_class": evidence_class, **fields}
        self.records.append(record)
        return record

    def app(self, bundle_id: Any, source_id: str, where: str) -> str:
        if not isinstance(bundle_id, str) or not bundle_id:
            return UNKNOWN
        if bundle_id not in self._apps:
            rid = "app-" + _slug(bundle_id)
            if rid in self._apps.values():
                rid += "-" + str(len(self._apps) + 1)
            self._apps[bundle_id] = rid
            self.add("App", rid, source_id, "observation", bundle_id=bundle_id,
                     display_name=UNKNOWN, provenance=_prov("ios.app_privacy_report", "snapshot_import", where))
        return self._apps[bundle_id]

    def domain(self, host: Any, source_id: str, evidence_class: str, source: str, method: str, where: str) -> str:
        if not isinstance(host, str) or not host:
            return UNKNOWN
        host = host.lower()
        if host not in self._domains:
            rid = "dom-" + _slug(host)
            if rid in self._domains.values():
                rid += "-" + str(len(self._domains) + 1)
            self._domains[host] = rid
            self.add("Domain", rid, source_id, evidence_class, host=host,
                     provenance=_prov(source, method, where))
        return self._domains[host]

    def link(self, kind: str, a: str, b: str, evidence: list[str], source_id: str, **extra: Any) -> None:
        self._links += 1
        self.add("Link", f"link-{self._links:04d}", source_id, "observation", link_type=kind,
                 **{"from": a, "to": b}, evidence_ids=evidence, **extra)


# --- App Privacy Report -------------------------------------------------------

def _extent_pair(extent: dict[str, Any]) -> tuple[str | None, str | None]:
    e, l = extent.get("earliest"), extent.get("latest")
    return (e["utc"] if e else None, l["utc"] if l else None)


def add_app_privacy_report(b: _Builder, labels: list[str], result: apr.ImportResult,
                           ledger: apr.ImportLedger, source_id: str = "src-apr") -> dict[str, Any]:
    """Map an ImportResult (plus its ledger) into batches, accesses, aggregates and links.

    labels[i] names input position i+1 (used only in provenance text). Returns the
    Source record, appended last so its counts reflect what was mapped.
    """
    inspection = result.inspection
    entries = {e["sha256"]: e for e in ledger.entries()}
    batch_ids: dict[int, str] = {}  # input position -> batch id (unique snapshots)
    for index, position in enumerate(inspection.snapshot_input_positions, 1):
        batch_ids[position] = f"ib-apr-s{index}"
    extents: dict[str, list[str | None]] = {}
    all_latest: list[str] = []
    record_count = 0
    net_ids: dict[tuple[int, int], str] = {}  # (snapshot_index, line) -> net id
    coverage = inspection.coverage_report()

    for index, (position, snap) in enumerate(
            zip(inspection.snapshot_input_positions, inspection.snapshots, strict=True), 1):
        bid = batch_ids[position]
        label = labels[position - 1]
        cov = snap.coverage()
        a_lo, a_hi = _extent_pair(cov["access"]["timestamp_extent"])
        n_lo, n_hi = _extent_pair(cov["network_activity"]["timestamp_extent"])
        stamps = sorted(x for x in (a_lo, a_hi, n_lo, n_hi) if x)
        extents[bid] = [stamps[0] if stamps else None, stamps[-1] if stamps else None]
        if stamps:
            all_latest.append(stamps[-1])
        counts = {s: sum(1 for r in snap.records if r.status == s)
                  for s in ("supported", "invalid", "unsupported")}
        record_count += cov["access"]["supported_record_count"] + cov["network_activity"]["supported_record_count"]
        entry = entries.get(snap.sha256, {})
        b.add("ImportBatch", bid, source_id, "observation",
              import_time=entry.get("imported_at", UNKNOWN), timezone="UTC",
              content_digest_sha256=snap.sha256, status="imported", duplicate_of=None,
              records_added=counts["supported"],
              ledger={k: entry.get(k, UNKNOWN) for k in
                      ("byte_count", "physical_lines", "supported_records", "invalid_records",
                       "unsupported_records")},
              observed_extent={"earliest": extents[bid][0] or UNKNOWN, "latest": extents[bid][1] or UNKNOWN},
              collection_window=UNKNOWN, issue_codes=sorted({i.code for i in snap.issues}),
              provenance=_prov("synthetic-fixture", "batch_import", label))

        by_line = {r.line: r for r in snap.records}
        for n, interval in enumerate(snap.intervals, 1):
            values = [by_line[ln].value for ln in interval.source_lines
                      if ln in by_line and by_line[ln].status == "supported" and by_line[ln].value]
            idents = {(v["accessor"]["identifier"], v["category"]) for v in values
                      if isinstance(v.get("accessor"), dict) and "identifier" in v["accessor"]}
            where = f"{label}:L" + ",L".join(str(x) for x in interval.source_lines)
            app_id, category = UNKNOWN, UNKNOWN
            if len(idents) == 1 and interval.status != "ambiguous":
                (bundle, category), = idents
                app_id = b.app(bundle, source_id, where)
            rid = f"access-s{index}-{n:02d}"
            duration = interval.duration_seconds
            b.add("ResourceAccess", rid, source_id, "observation", granularity="interval",
                  app_id=app_id, category=category, endpoint_domain_id=UNKNOWN, endpoint_match=UNKNOWN,
                  interval_status=interval.status,
                  duration_seconds=UNKNOWN if duration is None else duration,
                  provenance=_prov("ios.app_privacy_report", "paired_access_events", where),
                  import_batch_id=bid, timezone="UTC",
                  event_start=_utc(interval.start), event_end=_utc(interval.end))
            if app_id != UNKNOWN:
                b.link("ACCESSED_BY", rid, app_id, [rid], source_id)

        for n, rec in enumerate(snap.network_aggregates, 1):
            v = rec.value
            where = f"{label}:L{rec.line}"
            app_id = b.app(v["bundleID"], source_id, where)
            dom_id = b.domain(v["domain"], source_id, "observation", "ios.app_privacy_report",
                              "snapshot_import", where)
            rid = f"net-s{index}-{n:02d}"
            net_ids[(index, rec.line)] = rid
            known = {"type", "domain", "firstTimeStamp", "context", "timeStamp", "domainType",
                     "initiatedType", "hits", "domainOwner", "bundleID"}
            b.add("NetworkAggregate", rid, source_id, "observation", granularity="aggregate",
                  app_id=app_id, domain_id=dom_id, hits=v["hits"], hits_status="measured",
                  snapshot_id=bid, summable=False, initiated_type=v.get("initiatedType", UNKNOWN),
                  unknown_source_fields=sorted(set(v) - known),
                  provenance=_prov("ios.app_privacy_report", "snapshot_counter", where),
                  import_batch_id=bid, timezone="UTC",
                  event_start=_utc(apr._timestamp(v["firstTimeStamp"])),
                  event_end=_utc(apr._timestamp(v["timeStamp"])))

    # Duplicate inputs within the call, and artifacts the ledger already knew.
    first_batch = {pos: bid for pos, bid in batch_ids.items()}
    duplicate_ids: list[str] = []
    for dup, first in inspection.duplicate_inputs:
        bid = f"ib-apr-s{list(inspection.snapshot_input_positions).index(first) + 1}-dup{dup}"
        original = first_batch[first]
        duplicate_ids.append(bid)
        digest = next(s.sha256 for p, s in zip(inspection.snapshot_input_positions, inspection.snapshots)
                      if p == first)
        b.add("ImportBatch", bid, source_id, "observation", import_time=UNKNOWN, timezone="UTC",
              content_digest_sha256=digest, status="duplicate_skipped", duplicate_of=original,
              records_added=0, collection_window=UNKNOWN,
              provenance=_prov("synthetic-fixture", "batch_import", labels[dup - 1]))
        b.link("DUPLICATE_OF", bid, original, [bid, original], source_id)
    for position, digest in result.already_imported:
        bid = f"ib-apr-prior-{position}"
        duplicate_ids.append(bid)
        entry = entries.get(digest, {})
        b.add("ImportBatch", bid, source_id, "observation", import_time=entry.get("imported_at", UNKNOWN),
              timezone="UTC", content_digest_sha256=digest, status="already_imported_ledger",
              duplicate_of=None, records_added=0, collection_window=UNKNOWN,
              provenance=_prov("synthetic-fixture", "ledger_match", labels[position - 1]))

    # Reconciliation: one CONTACTED link per (app, domain); never a sum or delta.
    for agg in apr.reconcile_network_aggregates(inspection)["aggregates"]:
        ids = [net_ids[(o["snapshot_index"], o["line"])] for o in agg["observations"]]
        latest = agg["latest_observed"]
        b.link("CONTACTED", b.app(agg["app"], source_id, "reconcile"),
               b.domain(agg["domain"], source_id, "observation", "ios.app_privacy_report", "snapshot_import",
                        "reconcile"), ids, source_id, combine="latest_snapshot_only_never_sum",
               latest_observed_id=UNKNOWN if latest is None else net_ids[(latest["snapshot_index"], latest["line"])],
               reconciliation_flags=sorted({f["code"] for f in agg["flags"]}), consistent=agg["consistent"])

    return {"id": source_id, "extents": extents, "record_count": record_count,
            "latest": max(all_latest) if all_latest else None, "duplicates": duplicate_ids,
            "unmeasured": coverage["unmeasured"]}


def _apr_source(b: _Builder, info: dict[str, Any], source_id: str = "src-apr") -> None:
    b.add("Source", source_id, source_id, "observation", name="AppPrivacyReport",
          system="ios.app_privacy_report", support="supported_synthetic",
          provisioning="not_applicable_synthetic", coverage_status=UNKNOWN,
          source_granularity="interval", missing_periods=[], missing_periods_status=UNKNOWN,
          export_success="synthetic_fixture_parsed", record_count=info["record_count"],
          latest_event_time=info["latest"] or UNKNOWN, snapshot_extents=info["extents"],
          duplicate_imports=info["duplicates"], unmeasured=info["unmeasured"],
          overlap="network aggregates are never summed or differenced across snapshots",
          provenance=_prov("explorer_export", "source_summary", source_id))


# --- Account export -----------------------------------------------------------

def add_account_export(b: _Builder, results: list[tuple[str, aea.Audit]],
                       source_id: str = "src-account-export") -> None:
    """Map inspect_imports() output; duplicate imports add a batch + link, never activities."""
    ids = {label: f"ib-account-{n}" for n, (label, _) in enumerate(results, 1)}
    for label, audit in results:
        bid = ids[label]
        dup = audit.duplicate_of
        b.add("ImportBatch", bid, source_id, "observation", import_time=UNKNOWN, timezone="UTC",
              content_digest_sha256=audit.sha256,
              status="duplicate_skipped" if dup else "imported", duplicate_of=ids[dup] if dup else None,
              records_added=0 if dup else len(audit.records), parse_complete=audit.parse_complete,
              collection_window=UNKNOWN, issue_codes=sorted({i.code for i in audit.issues}),
              provenance=_prov("synthetic-fixture", "batch_import", label))
        if dup:
            b.link("DUPLICATE_OF", bid, ids[dup], [bid, ids[dup]], source_id)
            continue
        for r in audit.records:
            v = r.value
            codes = sorted({i.code for i in audit.issues if i.record == r.index})
            where = f"{label}#L{r.line}"
            url = v.get("titleUrl")
            host = urlparse(url).hostname if isinstance(url, str) else None
            dom = b.domain(host, source_id, "normalized_event", "example-account-export",
                           "title_url_host", where)
            valid_duration = aea._has_duration(r)
            time_status = ("measured" if r.time else "missing" if "time" not in v else "invalid")
            title = v.get("title")
            b.add("AccountActivity", f"acct-{bid[len('ib-account-'):]}-{r.index + 1:04d}", source_id,
                  "observation", granularity="point", activity_kind=r.category or UNKNOWN,
                  title=title if isinstance(title, str) else UNKNOWN, domain_id=dom,
                  duration_seconds=v["durationSeconds"] if valid_duration else UNKNOWN,
                  duration_status="measured" if valid_duration else
                  ("invalid" if "durationSeconds" in v else "not_reported"),
                  event_time_status=time_status, source_issue_codes=codes,
                  provenance=_prov("example-account-export", "activity_json_import", where),
                  import_batch_id=bid, timezone="UTC", event_time=_utc(r.time))


def _account_source(b: _Builder, results: list[tuple[str, aea.Audit]], source_id: str = "src-account-export") -> None:
    cov = aea.coverage([a for _, a in results])
    b.add("Source", source_id, source_id, "observation", name="AccountExport",
          system="example-account-export", support="supported_synthetic",
          provisioning="not_applicable_synthetic", coverage_status=UNKNOWN,
          source_granularity="point", missing_periods=[], missing_periods_status=UNKNOWN,
          export_success="synthetic_fixture_parsed", record_count=cov["records_counted"],
          latest_event_time=(cov["timestamp_max"] or UNKNOWN),
          fields_unavailable=sorted(f for f, s in cov["fields"].items() if s["status"] == "absent"),
          field_status={f: s["status"] for f, s in cov["fields"].items()},
          never_inferred=["dwell_time", "scroll_depth"], exports_imported=cov["imports"],
          duplicate_imports=cov["duplicate_imports"], schema_status=cov["schema_status"],
          provenance=_prov("explorer_export", "source_summary", source_id))


# --- Document -----------------------------------------------------------------

def build_document(workspace_id: str, apr_input: tuple[list[str], apr.ImportResult, apr.ImportLedger] | None,
                   account: list[tuple[str, aea.Audit]] | None, notice: str, synthetic: bool = True,
                   subject: str = "Fixture-derived workspace (no real person)") -> dict[str, Any]:
    b = _Builder(workspace_id)
    if apr_input is not None:
        labels, result, ledger = apr_input
        info = add_app_privacy_report(b, labels, result, ledger)
        _apr_source(b, info)
    if account is not None:
        add_account_export(b, account)
        _account_source(b, account)
    order = {t: i for i, t in enumerate(TYPE_ORDER)}
    records = sorted(b.records, key=lambda r: order[r["type"]])  # stable within a type
    times = sorted(t for r in records for k in ("event_time", "event_start", "event_end")
                   if isinstance((t := r.get(k)), str) and t != UNKNOWN)
    counts: dict[str, int] = {}
    for r in records:
        counts[r["type"]] = counts.get(r["type"], 0) + 1
    meta = {
        "contract_version": CONTRACT_VERSION,
        "status": "PROVISIONAL demonstration data; NOT a production schema",
        "synthetic": synthetic, "subject": subject, "workspace_id": workspace_id,
        "timezone": "UTC",
        "window": {"start": times[0] if times else UNKNOWN, "end": times[-1] if times else UNKNOWN,
                   "basis": "observed_record_extent_not_collection_window"},
        "exporter": {"name": "spikes.explorer_export", "version": EXPORTER_VERSION},
        "type_counts": counts, "unknown_token": UNKNOWN, "evidence_classes": list(EVIDENCE_CLASSES),
        "notice": notice,
    }
    return {"meta": meta, "records": records}


def build_fixture_document() -> dict[str, Any]:
    """Run the bundled synthetic fixtures through the parser spikes, then map."""
    apr_inputs = [(_ROOT / "app_privacy_report" / n).read_bytes() for n in APR_FIXTURES]
    apr_inputs.append(apr_inputs[0])  # repeated artifact, as the APR demo does
    labels = [*APR_FIXTURES, APR_FIXTURES[0]]
    ledger = apr.ImportLedger()  # in memory only
    result = apr.import_snapshots(apr_inputs, ledger, now=FIXTURE_IMPORT_TIME)
    account = aea.inspect_imports([(n, (_ROOT / "account_export" / n).read_bytes()) for n in ACCOUNT_FIXTURES])
    notice = ("Fixture-derived: built from the bundled synthetic fixtures via the parser spikes. "
              "All names, hosts, timestamps and counts are invented; not an anonymization example "
              "and not evidence about any device or provider export format.")
    return build_document(FIXTURE_WORKSPACE, (labels, result, ledger), account, notice)


def dumps(doc: dict[str, Any]) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=True) + "\n"


# --- Validator ----------------------------------------------------------------

_TIME_KEYS = ("event_time", "event_start", "event_end", "import_time", "created_at",
              "window_start", "window_end", "latest_event_time")
_NOT_A_REF = {"workspace_id", "bundle_id"}
_REF_LISTS = ("evidence_ids", "supporting_evidence_ids", "confirmed_by", "possible_overlap_with")
_UNKNOWN_STATUSES = {UNKNOWN, "missing", "invalid", "not_reported", "unavailable"}


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate_contract(doc: Any) -> list[str]:
    """Return problem strings (empty list means no problem found). Fixed wording, ids only."""
    if not isinstance(doc, dict) or not isinstance(doc.get("meta"), dict) or not isinstance(doc.get("records"), list):
        return ["document must be {meta, records[]}"]
    meta, records = doc["meta"], doc["records"]
    problems: list[str] = []
    if not isinstance(meta.get("synthetic"), bool):
        problems.append("meta.synthetic must be present and boolean")
    ws = meta.get("workspace_id")
    if not isinstance(ws, str) or not ws:
        problems.append("meta.workspace_id must be a non-empty string")
    if meta.get("evidence_classes") != list(EVIDENCE_CLASSES):
        problems.append("meta.evidence_classes must list the 5 allowed classes")
    ids: dict[str, str] = {}
    for n, r in enumerate(records):
        if not isinstance(r, dict) or not isinstance(r.get("id"), str) or not isinstance(r.get("type"), str):
            problems.append(f"record[{n}] lacks string id/type")
            continue
        if r["id"] in ids:
            problems.append(f"duplicate id {r['id']}")
        ids[r["id"]] = r["type"]
    for r in records:
        if not isinstance(r, dict) or r.get("id") not in ids:
            continue
        rid = r["id"]
        if r.get("workspace_id") != ws:
            problems.append(f"{rid}: workspace_id differs from meta.workspace_id")
        if r.get("evidence_class") not in EVIDENCE_CLASSES:
            problems.append(f"{rid}: evidence_class not allowed")
        refs: list[str] = []
        for k, v in r.items():
            if k in _NOT_A_REF:
                continue
            if (k.endswith("_id") or k in ("duplicate_of", "from", "to")) and isinstance(v, str):
                refs.append(v)
            elif k in _REF_LISTS and isinstance(v, list):
                refs.extend(x for x in v if isinstance(x, str))
        for ref in refs:
            if ref != UNKNOWN and ref not in ids:
                problems.append(f"{rid}: unresolved reference {ref}")
        for k in _TIME_KEYS:
            if k in r and r[k] != UNKNOWN and _parse_time(r[k]) is None:
                problems.append(f"{rid}: {k} not parseable")
        for period in r.get("missing_periods", []) if isinstance(r.get("missing_periods"), list) else []:
            for k in ("start", "end"):
                if not isinstance(period, dict) or _parse_time(period.get(k)) is None:
                    problems.append(f"{rid}: missing_periods.{k} not parseable")
        for k, v in r.items():
            if k.endswith("_status") and isinstance(v, str) and v in _UNKNOWN_STATUSES:
                base = k[:-7]
                for k2, v2 in r.items():
                    if _is_number(v2) and (k2 == base or k2.startswith(base + "_")):
                        problems.append(f"{rid}: {k2} is numeric although {k} says {v}")
        if r.get("missing_periods_status") == UNKNOWN and r.get("missing_periods"):
            problems.append(f"{rid}: missing_periods listed although status is unknown")
        if r["type"] == "NetworkAggregate" and r.get("summable") is not False:
            problems.append(f"{rid}: NetworkAggregate must have summable false")
        if r["type"] == "ResourceAccess" and "interval_status" in r:
            st = r["interval_status"]
            if st != "complete" and _is_number(r.get("duration_seconds")):
                problems.append(f"{rid}: incomplete interval carries a numeric duration")
            if st == "missing_end" and r.get("event_end") != UNKNOWN:
                problems.append(f"{rid}: missing_end interval has an invented end")
            if st == "missing_begin" and r.get("event_start") != UNKNOWN:
                problems.append(f"{rid}: missing_begin interval has an invented start")
        s, e = _parse_time(r.get("event_start")), _parse_time(r.get("event_end"))
        if s and e and e < s and r.get("interval_status") != "reversed":
            problems.append(f"{rid}: event_end precedes event_start")
        if r["type"] == "Link":
            if r.get("link_type") == "DUPLICATE_OF" and ids.get(r.get("from")) != "ImportBatch":
                problems.append(f"{rid}: DUPLICATE_OF must start at an ImportBatch")
    for r in records:
        if isinstance(r, dict) and r.get("type") == "ImportBatch" and r.get("duplicate_of"):
            has = any(isinstance(x, dict) and x.get("type") == "Link" and x.get("link_type") == "DUPLICATE_OF"
                      and x.get("from") == r["id"] and x.get("to") == r["duplicate_of"] for x in records)
            if not has:
                problems.append(f"{r['id']}: duplicate batch lacks a DUPLICATE_OF link")
    counts = meta.get("type_counts")
    if isinstance(counts, dict):
        actual: dict[str, int] = {}
        for r in records:
            if isinstance(r, dict) and isinstance(r.get("type"), str):
                actual[r["type"]] = actual.get(r["type"], 0) + 1
        if counts != actual:
            problems.append("meta.type_counts does not match records")
    return problems


# --- CLI ----------------------------------------------------------------------

def check_out_path(path: str | os.PathLike[str]) -> Path:
    """Allow paths outside the repository, or inside prototypes/<name>/data/ only."""
    resolved = Path(path).resolve()
    if resolved == _REPO_ROOT or _REPO_ROOT in resolved.parents:
        parts = resolved.relative_to(_REPO_ROOT).parts
        if not (len(parts) >= 4 and parts[0] == "prototypes" and parts[2] == "data"):
            raise ExportError("out_path_inside_repository")
    if resolved.is_dir():
        raise ExportError("out_path_is_directory")
    return resolved


def write_document(doc: dict[str, Any], path: str | os.PathLike[str]) -> Path:
    target = check_out_path(path)
    problems = validate_contract(doc)
    if problems:
        raise ExportError("document_failed_validation")
    text = dumps(doc).encode("utf-8")
    if len(text) > MAX_OUT_BYTES:
        raise ExportError("output_too_large")
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=target.parent, suffix=".tmp")
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(text)
        os.replace(temporary, target)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the explorer contract from bundled synthetic fixtures.")
    parser.add_argument("--fixtures", action="store_true", help="use only the bundled synthetic fixtures")
    parser.add_argument("--out", metavar="PATH", help="write JSON (outside the repo, or under prototypes/*/data/)")
    args = parser.parse_args(argv)
    if not args.fixtures:
        parser.print_help()
        return 0
    try:
        doc = build_fixture_document()
        problems = validate_contract(doc)
        if args.out:
            written = write_document(doc, args.out)
    except ExportError as exc:
        print(f"Export refused: {exc}")
        return 2
    except (OSError, apr.InputLimitError, aea.InputLimitError, apr.LedgerError):
        print("Fixture export failed; check fixture availability and the output location.")
        return 2
    summary = {"workspace_id": doc["meta"]["workspace_id"], "synthetic": doc["meta"]["synthetic"],
               "type_counts": doc["meta"]["type_counts"], "validation": "ok" if not problems else problems}
    if args.out:
        summary["written"] = written.name
    print(json.dumps(summary, indent=2))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
