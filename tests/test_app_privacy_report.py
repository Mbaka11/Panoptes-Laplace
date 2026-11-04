"""Synthetic-only tests for the isolated inspector, not device capability tests."""

from contextlib import redirect_stderr, redirect_stdout
import copy
import hashlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from spikes import app_privacy_report as apr


FIXTURES = Path(__file__).resolve().parents[1] / "spikes" / "fixtures" / "app_privacy_report"


def ndjson(*records):
    return ("\n".join(json.dumps(record) for record in records) + "\n").encode("utf-8")


def access(kind="intervalBegin", timestamp="2026-01-01T08:00:00Z", **changes):
    record = {
        "type": "access",
        "accessor": {"identifier": "com.example.demo", "identifierType": "bundleID"},
        "category": "location", "identifier": "synthetic-interval",
        "kind": kind, "timeStamp": timestamp,
    }
    record.update(changes)
    return record


def network(**changes):
    record = {
        "type": "networkActivity", "bundleID": "com.example.demo",
        "domain": "api.example.com", "hits": 5,
        "firstTimeStamp": "2026-01-01T08:00:00Z",
        "timeStamp": "2026-01-02T08:00:00Z",
        "domainType": 2, "initiatedType": "AppInitiated", "context": "", "domainOwner": "",
    }
    record.update(changes)
    return record


def codes(snapshot):
    return {issue.code for issue in snapshot.issues}


class IntervalTests(unittest.TestCase):
    def test_complete_interval_preserves_raw_and_provenance(self):
        raw = ndjson(access(), access("intervalEnd", "2026-01-01T08:10:00Z"))
        snapshot = apr.inspect_snapshot(raw)
        self.assertEqual(snapshot.raw_bytes, raw)
        self.assertEqual(snapshot.sha256, hashlib.sha256(raw).hexdigest())
        self.assertEqual(snapshot.intervals[0].source_lines, (1, 2))
        self.assertEqual(snapshot.intervals[0].status, "complete")
        self.assertEqual(snapshot.intervals[0].duration_seconds, 600)
        self.assertEqual(snapshot.records[0].value, access())
        self.assertFalse(snapshot.issues)

    def test_incomplete_intervals_never_get_a_duration(self):
        for kind, expected in (("intervalBegin", "missing_end"), ("intervalEnd", "missing_begin")):
            with self.subTest(kind=kind):
                snapshot = apr.inspect_snapshot(ndjson(access(kind)))
                self.assertEqual(snapshot.intervals[0].status, expected)
                self.assertIsNone(snapshot.intervals[0].duration_seconds)
                self.assertIn("incomplete_interval", codes(snapshot))

    def test_different_offsets_compare_by_instant(self):
        snapshot = apr.inspect_snapshot(ndjson(
            access(timestamp="2026-01-01T08:00:00+01:00"),
            access("intervalEnd", "2026-01-01T07:05:00Z"),
        ))
        self.assertEqual(snapshot.intervals[0].duration_seconds, 300)
        self.assertEqual(snapshot.records[0].value["timeStamp"], "2026-01-01T08:00:00+01:00")

    def test_end_before_begin_in_file_is_not_reversed_time(self):
        snapshot = apr.inspect_snapshot(ndjson(
            access("intervalEnd", "2026-01-01T08:10:00Z"), access(),
        ))
        self.assertEqual(snapshot.intervals[0].status, "complete")

    def test_reversed_interval_is_flagged(self):
        snapshot = apr.inspect_snapshot(ndjson(
            access(), access("intervalEnd", "2026-01-01T07:59:59Z"),
        ))
        self.assertEqual(snapshot.intervals[0].status, "reversed")
        self.assertIsNone(snapshot.intervals[0].duration_seconds)
        self.assertIn("reversed_interval", codes(snapshot))

    def test_zero_duration_is_not_missing(self):
        snapshot = apr.inspect_snapshot(ndjson(access(), access("intervalEnd")))
        self.assertEqual(snapshot.intervals[0].duration_seconds, 0)

    def test_duplicate_boundaries_are_ambiguous(self):
        snapshot = apr.inspect_snapshot(ndjson(access(), access(), access("intervalEnd")))
        self.assertEqual(snapshot.intervals[0].status, "ambiguous")
        self.assertIsNone(snapshot.intervals[0].duration_seconds)
        self.assertEqual(len(snapshot.records), 3)

    def test_conflicting_actor_category_or_broadcaster_is_not_paired(self):
        variants = [
            {"accessor": {"identifier": "com.example.other", "identifierType": "bundleID"}},
            {"category": "photos"},
            {"broadcaster": {"identifier": "com.example.broadcaster", "identifierType": "bundleID"}},
        ]
        for change in variants:
            with self.subTest(change=change):
                snapshot = apr.inspect_snapshot(ndjson(access(), access("intervalEnd", **change)))
                self.assertEqual(snapshot.intervals[0].status, "ambiguous")

    def test_invalid_extra_boundary_prevents_false_complete_pair(self):
        snapshot = apr.inspect_snapshot(ndjson(
            access(), access("intervalEnd"), access(timestamp="not-a-time"),
        ))
        self.assertEqual(snapshot.intervals[0].status, "ambiguous")
        self.assertIn("invalid_timestamp", codes(snapshot))

    def test_missing_identifier_remains_invalid_not_invented(self):
        row = access()
        del row["identifier"]
        snapshot = apr.inspect_snapshot(ndjson(row))
        self.assertEqual(snapshot.records[0].status, "invalid")
        self.assertFalse(snapshot.intervals)

    def test_intervals_are_never_stitched_across_snapshots(self):
        report = apr.inspect_snapshots([ndjson(access()), ndjson(access("intervalEnd"))])
        self.assertEqual(report.snapshots[0].intervals[0].status, "missing_end")
        self.assertEqual(report.snapshots[1].intervals[0].status, "missing_begin")


class NetworkAndSnapshotTests(unittest.TestCase):
    def test_contact_count_stays_one_aggregate(self):
        snapshot = apr.inspect_snapshot(ndjson(network()))
        self.assertEqual(len(snapshot.network_aggregates), 1)
        self.assertEqual(snapshot.network_aggregates[0].value["hits"], 5)
        self.assertEqual(len(snapshot.records), 1)
        self.assertFalse(snapshot.intervals)

    def test_overlapping_snapshots_are_not_summed_or_differenced(self):
        report = apr.inspect_snapshots([
            ndjson(network()),
            ndjson(network(hits=8, timeStamp="2026-01-03T08:00:00Z")),
        ])
        self.assertEqual([s.network_aggregates[0].value["hits"] for s in report.snapshots], [5, 8])
        summary = report.summary()
        self.assertEqual(summary["unique_snapshot_count"], 2)
        self.assertEqual(summary["network_policy"], "preserve_each_snapshot_no_cross_snapshot_sum_or_delta")
        self.assertNotIn("total_hits", summary)
        self.assertNotIn("delta", summary)
        self.assertTrue(summary["collection_window"].startswith("unknown"))

    def test_identical_artifacts_are_deduplicated_with_input_references(self):
        a, b = ndjson(network()), ndjson(network(hits=8))
        report = apr.inspect_snapshots([a, b, a, b])
        self.assertEqual(len(report.snapshots), 2)
        self.assertEqual(report.duplicate_inputs, ((3, 1), (4, 2)))

    def test_no_hidden_state_between_calls(self):
        raw = ndjson(network())
        self.assertEqual(len(apr.inspect_snapshots([raw]).snapshots), 1)
        self.assertEqual(apr.inspect_snapshots([raw]).duplicate_inputs, ())

    def test_deduplication_is_exact_bytes_not_schema_normalization(self):
        a = ndjson(network())
        b = json.dumps(network(), separators=(",", ":")).encode()
        self.assertEqual(len(apr.inspect_snapshots([a, b]).snapshots), 2)

    def test_invalid_hits_are_not_coerced(self):
        for value in (True, False, -1, 1.5, "5", None):
            with self.subTest(value=value):
                snapshot = apr.inspect_snapshot(ndjson(network(hits=value)))
                self.assertFalse(snapshot.network_aggregates)
                self.assertIn("invalid_hits", codes(snapshot))

    def test_zero_hits_preserved(self):
        snapshot = apr.inspect_snapshot(ndjson(network(hits=0)))
        self.assertEqual(snapshot.network_aggregates[0].value["hits"], 0)

    def test_invalid_network_times_are_not_an_aggregate(self):
        snapshot = apr.inspect_snapshot(ndjson(network(firstTimeStamp="2026-01-03T08:00:00Z")))
        self.assertFalse(snapshot.network_aggregates)
        self.assertIn("reversed_contact_timestamps", codes(snapshot))

    def test_unknown_domain_class_is_retained_without_interpretation(self):
        snapshot = apr.inspect_snapshot(ndjson(network(domainType=42, initiatedType="FutureType")))
        self.assertEqual(len(snapshot.network_aggregates), 1)
        self.assertIn("unknown_domain_type_preserved", codes(snapshot))
        self.assertIn("unknown_initiator_type_preserved", codes(snapshot))

    def test_wrong_optional_types_are_not_silently_accepted(self):
        for change in ({"domainType": True}, {"context": []}, {"domainOwner": 12}):
            with self.subTest(change=change):
                snapshot = apr.inspect_snapshot(ndjson(network(**change)))
                self.assertEqual(snapshot.records[0].status, "invalid")


class ValidationTests(unittest.TestCase):
    def test_invalid_json_and_nonobjects_stay_in_line_accounting(self):
        snapshot = apr.inspect_snapshot(b'\n{bad\n[]\nnull\n42\n')
        self.assertEqual(snapshot.physical_lines, 5)
        self.assertEqual(snapshot.blank_lines, 1)
        self.assertEqual([r.line for r in snapshot.records], [2, 3, 4, 5])
        self.assertTrue(all(r.status == "invalid" for r in snapshot.records))
        self.assertEqual(snapshot.records[0].raw_line, "{bad")

    def test_duplicate_keys_and_nonfinite_numbers_are_rejected(self):
        for row in (
            '{"type":"access","type":"networkActivity"}',
            '{"type":"unknown","x":{"a":1,"a":2}}',
            '{"type":"unknown","x":NaN}',
            '{"type":"unknown","x":Infinity}',
            '{"type":"unknown","x":1e9999}',
            '{"type":"unknown","x":' + '9' * 65 + '}',
        ):
            with self.subTest(row=row[:40]):
                snapshot = apr.inspect_snapshot(row.encode())
                self.assertEqual(snapshot.records[0].status, "invalid")
                self.assertIn("invalid_json", codes(snapshot))

    def test_unknown_type_is_visible_and_preserved(self):
        row = {"type": "futureRecord", "payload": {"synthetic": True}}
        snapshot = apr.inspect_snapshot(ndjson(row))
        self.assertEqual(snapshot.records[0].status, "unsupported")
        self.assertEqual(snapshot.records[0].value, row)
        self.assertIn("unsupported_record_type", codes(snapshot))

    def test_unknown_fields_are_preserved_at_top_and_actor_levels(self):
        row = access(futureField={"x": 1})
        row["accessor"]["futureActorField"] = "synthetic"
        original = copy.deepcopy(row)
        snapshot = apr.inspect_snapshot(ndjson(row))
        self.assertEqual(snapshot.records[0].value, original)
        self.assertIn("unknown_fields_preserved", codes(snapshot))
        self.assertIn("unknown_nested_fields_preserved", codes(snapshot))

    def test_missing_or_wrong_types_produce_diagnostics_not_crashes(self):
        for row in ({}, {"type": []}, access(accessor=[]), access(category=None), access(kind={})):
            with self.subTest(row=row):
                snapshot = apr.inspect_snapshot(ndjson(row))
                self.assertEqual(snapshot.records[0].status, "invalid")

    def test_unknown_time_offsets_naive_invalid_or_truncated_precision_rejected(self):
        for stamp in (
            "2026-01-01", "2026-01-01T08:00:00", "2026-02-30T08:00:00Z",
            "2026-01-01T08:00:00-00:00", "2026-01-01T08:00:00+00:99",
            "2026-01-01T08:00:00.1234567Z", None,
        ):
            with self.subTest(stamp=stamp):
                snapshot = apr.inspect_snapshot(ndjson(access(timestamp=stamp)))
                self.assertIn("invalid_timestamp", codes(snapshot))

    def test_bom_crlf_and_blank_lines(self):
        raw = b"\xef\xbb\xbf\r\n" + ndjson(network()).replace(b"\n", b"\r\n")
        snapshot = apr.inspect_snapshot(raw)
        self.assertEqual(snapshot.blank_lines, 1)
        self.assertEqual(snapshot.records[0].line, 2)
        self.assertEqual(len(snapshot.network_aggregates), 1)
        self.assertEqual(snapshot.raw_bytes, raw)

    def test_unicode_line_separator_inside_a_string_does_not_split_record(self):
        raw = json.dumps(network(context="synthetic\u2028text"), ensure_ascii=False).encode()
        snapshot = apr.inspect_snapshot(raw)
        self.assertEqual(snapshot.physical_lines, 1)
        self.assertEqual(len(snapshot.network_aggregates), 1)

    def test_non_json_whitespace_is_not_silently_skipped(self):
        snapshot = apr.inspect_snapshot("\u00a0\n".encode())
        self.assertEqual(snapshot.blank_lines, 0)
        self.assertEqual(snapshot.records[0].status, "invalid")

    def test_summary_never_echoes_source_values_or_hashes(self):
        secret = "synthetic-value-not-for-summary"
        snapshot = apr.inspect_snapshot(ndjson(network(domain=secret, extra={secret: secret})))
        output = json.dumps(snapshot.summary())
        self.assertNotIn(secret, output)
        self.assertNotIn("com.example.demo", output)
        self.assertNotIn(snapshot.sha256, output)
        self.assertIn(secret, snapshot.records[0].raw_line)

    def test_deep_json_is_reported_as_invalid_not_uncaught(self):
        raw = ('{"type":"future","x":' + '[' * 1200 + '0' + ']' * 1200 + '}').encode()
        snapshot = apr.inspect_snapshot(raw)
        self.assertEqual(snapshot.records[0].status, "invalid")

    def test_empty_inputs_do_not_fabricate_records(self):
        self.assertEqual(apr.inspect_snapshot(b"").physical_lines, 0)
        self.assertFalse(apr.inspect_snapshot(b"").records)
        self.assertFalse(apr.inspect_snapshots([]).snapshots)


class CoverageTests(unittest.TestCase):
    def coverage(self, *inputs):
        return apr.inspect_snapshots(inputs).coverage_report()

    def test_fixture_report_keeps_semantics_and_line_provenance(self):
        a = (FIXTURES / "snapshot-a.ndjson").read_bytes()
        b = (FIXTURES / "snapshot-b.ndjson").read_bytes()
        report = self.coverage(a, b, a)
        self.assertEqual(report["report_version"], "synthetic-coverage-v1")
        self.assertEqual(report["unique_snapshot_count"], 2)
        self.assertEqual(report["duplicate_inputs"], [[3, 1]])
        first, second = report["snapshots"]
        self.assertEqual(first["snapshot_index"], 1)
        self.assertEqual(first["first_input_position"], 1)
        self.assertEqual(first["record_lines_by_status"], {
            "supported": [1, 2, 3, 4], "invalid": [], "unsupported": [],
        })
        self.assertEqual(first["access"]["supported_record_count"], 3)
        self.assertEqual(first["access"]["intervals"], [
            {"source_lines": [1, 2], "status": "complete", "duration_seconds": 600},
            {"source_lines": [3], "status": "missing_end", "duration_seconds": None},
        ])
        self.assertEqual(second["access"]["intervals"][0]["status"], "missing_begin")
        self.assertEqual(first["network_activity"]["supported_record_count"], 1)
        self.assertEqual(first["network_activity"]["source_lines"], [4])
        self.assertEqual(second["network_activity"]["timestamp_extent"]["latest"], {
            "utc": "2026-01-03T09:00:00Z", "source_refs": [{"line": 2, "field": "timeStamp"}],
        })
        self.assertEqual(first["diagnostic_state"], "warnings_present")

    def test_unknown_measurements_are_not_promoted_to_device_evidence(self):
        report = self.coverage(ndjson(network()))
        self.assertEqual(report["evidence_class"], "synthetic_input_only_not_device_evidence")
        self.assertEqual(report["unmeasured"], {
            "device_support": "not_tested", "provisioning": "not_tested",
            "os_authorization": "not_observed", "participant_scope": "not_applicable_synthetic_only",
            "source_export_success": "not_tested", "recording_enabled_at": "unknown",
            "collection_window": "unknown", "source_generated_at": "unknown",
            "missing_periods": "unknown", "freshness": "not_evaluated",
        })
        self.assertEqual(report["network_policy"], "preserve_each_snapshot_no_cross_snapshot_sum_or_delta")
        self.assertNotIn("total_hits", json.dumps(report))
        self.assertNotIn("coverage_percentage", json.dumps(report))

    def test_empty_artifact_and_no_inputs_remain_distinct(self):
        no_inputs = self.coverage()
        blank = self.coverage(b"\n \t\r\n")
        self.assertEqual(no_inputs["snapshots"], [])
        self.assertEqual(blank["unique_snapshot_count"], 1)
        snapshot = blank["snapshots"][0]
        self.assertEqual(snapshot["physical_lines"], 2)
        self.assertEqual(snapshot["blank_lines"], 2)
        self.assertEqual(snapshot["data_state"], "no_nonblank_records")
        self.assertEqual(snapshot["record_lines_by_status"], {
            "supported": [], "invalid": [], "unsupported": [],
        })
        for name in ("access", "network_activity"):
            self.assertEqual(snapshot[name]["supported_record_count"], 0)
            self.assertEqual(snapshot[name]["timestamp_extent"], {"earliest": None, "latest": None})
        self.assertEqual(blank["unmeasured"]["os_authorization"], "not_observed")
        self.assertEqual(blank["unmeasured"]["missing_periods"], "unknown")

    def test_invalid_and_unsupported_lines_are_not_a_successful_empty_import(self):
        report = self.coverage(b'\n{bad\n{"type":"future"}\n')
        snapshot = report["snapshots"][0]
        self.assertEqual(snapshot["data_state"], "no_supported_records")
        self.assertEqual(snapshot["diagnostic_state"], "errors_present")
        self.assertEqual(snapshot["record_lines_by_status"], {
            "supported": [], "invalid": [2], "unsupported": [3],
        })
        self.assertIsNone(snapshot["network_activity"]["timestamp_extent"]["latest"])

    def test_supported_subset_is_not_a_full_schema_or_completeness_claim(self):
        clean = self.coverage(ndjson(network()))["snapshots"][0]
        self.assertEqual(clean["data_state"], "supported_subset_present")
        self.assertEqual(clean["diagnostic_state"], "none_reported")
        mixed = self.coverage(ndjson(network(), {"type": "future"}) + b'{bad\n')["snapshots"][0]
        self.assertEqual(mixed["data_state"], "supported_subset_present")
        self.assertEqual(mixed["diagnostic_state"], "errors_present")
        self.assertEqual(mixed["record_lines_by_status"]["supported"], [1])

    def test_access_extent_compares_instants_and_preserves_original_offset(self):
        raw = ndjson(access(timestamp="2026-01-01T08:00:00+01:00"),
                     access("intervalEnd", "2026-01-01T07:05:00.123456Z"))
        inspection = apr.inspect_snapshots([raw])
        extent = inspection.coverage_report()["snapshots"][0]["access"]["timestamp_extent"]
        self.assertEqual(extent["earliest"], {
            "utc": "2026-01-01T07:00:00Z", "source_refs": [{"line": 1, "field": "timeStamp"}],
        })
        self.assertEqual(extent["latest"]["utc"], "2026-01-01T07:05:00.123456Z")
        self.assertEqual(inspection.snapshots[0].records[0].value["timeStamp"], "2026-01-01T08:00:00+01:00")

    def test_equal_timestamp_extrema_keep_all_source_references(self):
        stamp = "2026-01-01T08:00:00Z"
        snapshot = self.coverage(ndjson(network(firstTimeStamp=stamp, timeStamp=stamp),
                                       network(firstTimeStamp=stamp, timeStamp="2026-01-01T09:00:00+01:00")))["snapshots"][0]
        extent = snapshot["network_activity"]["timestamp_extent"]
        expected = {
            "utc": stamp, "source_refs": [
                {"line": 1, "field": "firstTimeStamp"}, {"line": 1, "field": "timeStamp"},
                {"line": 2, "field": "firstTimeStamp"}, {"line": 2, "field": "timeStamp"},
            ],
        }
        self.assertEqual(extent, {"earliest": expected, "latest": expected})
        self.assertEqual(snapshot["network_activity"]["supported_record_count"], 2)

    def test_invalid_and_unknown_records_cannot_supply_timestamp_extrema(self):
        raw = ndjson(network(), network(hits=-1, timeStamp="2099-01-01T00:00:00Z"),
                     {"type": "future", "timeStamp": "2099-01-02T00:00:00Z"},
                     access(timestamp="not-a-time"))
        snapshot = self.coverage(raw)["snapshots"][0]
        self.assertEqual(snapshot["network_activity"]["timestamp_extent"]["latest"]["utc"],
                         "2026-01-02T08:00:00Z")
        self.assertIsNone(snapshot["access"]["timestamp_extent"]["latest"])
        self.assertEqual(snapshot["record_lines_by_status"]["invalid"], [2, 4])
        self.assertEqual(snapshot["record_lines_by_status"]["unsupported"], [3])

    def test_ambiguous_and_reversed_intervals_do_not_gain_durations(self):
        for raw, status in (
            (ndjson(access(), access(), access("intervalEnd")), "ambiguous"),
            (ndjson(access(), access("intervalEnd", "2026-01-01T07:00:00Z")), "reversed"),
        ):
            with self.subTest(status=status):
                snapshot = self.coverage(raw)["snapshots"][0]
                interval = snapshot["access"]["intervals"][0]
                self.assertEqual(interval["status"], status)
                self.assertIsNone(interval["duration_seconds"])
                self.assertEqual(snapshot["diagnostic_state"], "errors_present")

    def test_zero_and_large_hits_count_records_not_requests(self):
        snapshot = self.coverage(ndjson(network(hits=0), network(hits=10**63)))["snapshots"][0]
        self.assertEqual(snapshot["network_activity"]["supported_record_count"], 2)
        self.assertEqual(snapshot["network_activity"]["source_lines"], [1, 2])
        self.assertEqual(snapshot["network_activity"]["counting_unit"], "source_aggregate_records_not_requests")
        self.assertNotIn(str(10**63), json.dumps(snapshot))

    def test_unknown_metadata_does_not_fill_unmeasured_source_fields(self):
        report = self.coverage(ndjson(network(collection_window="invented", source_generated_at="invented")))
        self.assertEqual(report["unmeasured"]["collection_window"], "unknown")
        self.assertEqual(report["unmeasured"]["source_generated_at"], "unknown")
        self.assertIn("unknown_fields_preserved", json.dumps(report))
        self.assertNotIn("invented", json.dumps(report))

    def test_coverage_excludes_identifiers_domains_raw_values_and_digests(self):
        sentinel = "synthetic-private-marker"
        raw = ndjson(network(domain=sentinel, bundleID=sentinel, context=sentinel,
                             extra={sentinel: sentinel}),
                     access(category=sentinel, identifier=sentinel), {"type": sentinel})
        inspection = apr.inspect_snapshots([raw])
        output = json.dumps(inspection.coverage_report())
        self.assertNotIn(sentinel, output)
        self.assertNotIn("com.example.demo", output)
        self.assertNotIn(inspection.snapshots[0].sha256, output)
        self.assertNotIn("raw_line", output)
        # Timestamp disclosure is intentional in this opt-in view, not anonymization.
        self.assertIn("2026-01-02T08:00:00Z", output)
        self.assertNotIn("2026-", json.dumps(inspection.summary()))

    def test_interleaved_duplicates_keep_original_input_positions(self):
        a, b, c = ndjson(network()), ndjson(network(hits=8)), ndjson(access())
        report = self.coverage(a, a, b, b, c, a)
        self.assertEqual([s["snapshot_index"] for s in report["snapshots"]], [1, 2, 3])
        self.assertEqual([s["first_input_position"] for s in report["snapshots"]], [1, 3, 5])
        self.assertEqual(report["duplicate_inputs"], [[2, 1], [4, 3], [6, 1]])

    def test_same_semantics_different_bytes_remain_separate_artifacts(self):
        a = ndjson(network())
        b = json.dumps(network(), separators=(",", ":")).encode()
        report = self.coverage(a, b)
        self.assertEqual(report["unique_snapshot_count"], 2)
        self.assertEqual(report["duplicate_inputs"], [])

    def test_digest_collision_cannot_discard_distinct_bytes(self):
        a, b = ndjson(network()), ndjson(network(hits=8))
        with patch.object(apr.hashlib, "sha256") as digest:
            digest.return_value.hexdigest.return_value = "synthetic-collision"
            inspection = apr.inspect_snapshots([a, b, a])
        self.assertEqual(len(inspection.snapshots), 2)
        self.assertEqual([s.network_aggregates[0].value["hits"] for s in inspection.snapshots], [5, 8])
        self.assertEqual(inspection.duplicate_inputs, ((3, 1),))

    def test_reporting_is_repeatable_and_does_not_mutate_source_values(self):
        inspection = apr.inspect_snapshots([ndjson(network(), access())])
        before = copy.deepcopy(inspection)
        first = inspection.coverage_report()
        self.assertEqual(first, inspection.coverage_report())
        first["snapshots"][0]["access"]["source_lines"].append(99)
        self.assertNotIn(99, inspection.coverage_report()["snapshots"][0]["access"]["source_lines"])
        self.assertEqual(before, inspection)


class CoverageBoundsAndCliTests(unittest.TestCase):
    def test_unrepresentable_utc_instants_are_diagnosed_not_crashes(self):
        for stamp in ("0001-01-01T00:00:00+01:00", "9999-12-31T23:59:59-01:00"):
            with self.subTest(stamp=stamp):
                inspection = apr.inspect_snapshots([ndjson(access(timestamp=stamp))])
                self.assertIn("invalid_timestamp", codes(inspection.snapshots[0]))
                coverage = inspection.coverage_report()["snapshots"][0]
                self.assertIsNone(coverage["access"]["timestamp_extent"]["latest"])
                self.assertEqual(inspection.snapshots[0].records[0].value["timeStamp"], stamp)

    def test_representable_extreme_years_remain_supported(self):
        raw = ndjson(access(timestamp="0001-01-01T01:00:00+01:00"),
                     access("intervalEnd", "9999-12-31T22:59:59-01:00"))
        snapshot = apr.inspect_snapshots([raw]).coverage_report()["snapshots"][0]
        extent = snapshot["access"]["timestamp_extent"]
        self.assertEqual(extent["earliest"]["utc"], "0001-01-01T00:00:00Z")
        self.assertEqual(extent["latest"]["utc"], "9999-12-31T23:59:59Z")
        self.assertEqual(snapshot["diagnostic_state"], "none_reported")

    def test_coverage_cli_only_reads_fixtures_and_uses_no_network(self):
        output = io.StringIO()
        original_open = Path.open
        with redirect_stdout(output), patch("socket.socket", side_effect=AssertionError("network access")), \
                patch.object(Path, "open", autospec=True, side_effect=original_open) as opened:
            self.assertEqual(apr.main(["--demo", "--coverage"]), 0)
        self.assertEqual([call.args[0].name for call in opened.call_args_list],
                         ["snapshot-a.ndjson", "snapshot-b.ndjson"])
        self.assertTrue(all(call.args[1:] == ("rb",) for call in opened.call_args_list))
        report = json.loads(output.getvalue())
        self.assertEqual(report["report_version"], "synthetic-coverage-v1")
        self.assertEqual(report["unique_snapshot_count"], 2)
        self.assertNotIn("api.example.com", output.getvalue())

    def test_coverage_requires_demo_and_rejects_participant_file_arguments(self):
        for args in (["--coverage"], ["--demo", "--coverage", "private.ndjson"]):
            with self.subTest(args=args), redirect_stderr(io.StringIO()), patch.object(Path, "open") as opened:
                with self.assertRaises(SystemExit) as error:
                    apr.main(args)
                self.assertEqual(error.exception.code, 2)
                opened.assert_not_called()

    def test_coverage_error_diagnostics_preserve_nonzero_exit(self):
        inspection = apr.inspect_snapshots([ndjson(network(hits=-1))])
        for args in (["--demo"], ["--demo", "--coverage"]):
            with self.subTest(args=args), redirect_stdout(io.StringIO()), \
                    patch.object(apr, "inspect_snapshots", return_value=inspection):
                self.assertEqual(apr.main(args), 1)


class LimitsAndDemoTests(unittest.TestCase):
    def test_utf8_and_input_type_rejection(self):
        with self.assertRaisesRegex(apr.InputLimitError, "invalid_utf8"):
            apr.inspect_snapshot(b"\xff")
        for function, value in ((apr.inspect_snapshot, "text"), (apr.inspect_snapshots, ["text"])):
            with self.subTest(function=function):
                with self.assertRaises(TypeError):
                    function(value)

    def test_byte_line_count_and_line_size_limits(self):
        cases = [
            ("MAX_SNAPSHOT_BYTES", 1, b"{}", "snapshot_byte_limit"),
            ("MAX_LINES", 1, b"{}\n{}\n", "line_count_limit"),
            ("MAX_LINE_BYTES", 1, b"{}", "line_byte_limit"),
        ]
        for constant, maximum, raw, code in cases:
            with self.subTest(constant=constant), patch.object(apr, constant, maximum):
                with self.assertRaisesRegex(apr.InputLimitError, code):
                    apr.inspect_snapshot(raw)

    def test_total_limits_also_bound_duplicate_inputs(self):
        with patch.object(apr, "MAX_TOTAL_BYTES", 3):
            with self.assertRaisesRegex(apr.InputLimitError, "total_byte_limit"):
                apr.inspect_snapshots([b"{}", b"{}"])
        with patch.object(apr, "MAX_SNAPSHOTS", 1):
            with self.assertRaisesRegex(apr.InputLimitError, "snapshot_count_limit"):
                apr.inspect_snapshots([b"", b""])
        with patch.object(apr, "MAX_SNAPSHOT_BYTES", 1):
            with self.assertRaisesRegex(apr.InputLimitError, "snapshot_byte_limit"):
                apr.inspect_snapshots([b"{}"])

    def test_demo_fixtures_are_repeatable_and_have_expected_semantics(self):
        a = (FIXTURES / "snapshot-a.ndjson").read_bytes()
        b = (FIXTURES / "snapshot-b.ndjson").read_bytes()
        report = apr.inspect_snapshots([a, b, a])
        self.assertEqual(report.duplicate_inputs, ((3, 1),))
        self.assertEqual(report.snapshots[0].intervals[0].duration_seconds, 600)
        self.assertEqual(report.snapshots[0].intervals[1].status, "missing_end")
        self.assertEqual(report.snapshots[1].intervals[0].status, "missing_begin")
        self.assertEqual([s.network_aggregates[0].value["hits"] for s in report.snapshots], [5, 8])
        self.assertEqual(report.summary(), apr.inspect_snapshots([a, b, a]).summary())

    def test_demo_uses_no_network_and_summary_has_no_domains(self):
        output = io.StringIO()
        with redirect_stdout(output), patch("socket.socket", side_effect=AssertionError("network access")):
            self.assertEqual(apr.main(["--demo"]), 0)
        parsed = json.loads(output.getvalue())
        self.assertEqual(parsed["unique_snapshot_count"], 2)
        self.assertEqual(parsed["duplicate_inputs"], [[3, 1]])
        self.assertNotIn("api.example.com", output.getvalue())

    def test_no_demo_only_prints_help(self):
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(apr.main([]), 0)
        self.assertIn("--demo", output.getvalue())

    def test_demo_io_failure_is_generic(self):
        output = io.StringIO()
        with patch.object(Path, "open", side_effect=OSError("sensitive path")), redirect_stdout(output):
            self.assertEqual(apr.main(["--demo"]), 2)
        self.assertNotIn("sensitive path", output.getvalue())


if __name__ == "__main__":
    unittest.main()
