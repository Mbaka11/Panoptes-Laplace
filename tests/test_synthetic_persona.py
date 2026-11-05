"""Tests for the SYNTHETIC Subject EX-01 persona. Demonstration data, not a production schema."""

import json
from datetime import datetime
from pathlib import Path
import unittest

from spikes import synthetic_persona as sp

OUT = Path(__file__).resolve().parent.parent / "prototypes" / "explorer-concept" / "data" / "persona.json"
DOC = sp.build()
RECS = DOC["records"]
BY_ID = {r["id"]: r for r in RECS}
TEMPORAL = {"LocationSample", "Visit", "Trip", "ActivityInterval", "DailyHealthAggregate", "CalendarEvent",
            "ResourceAccess", "NetworkAggregate", "AccountActivity"}
GRAN = {"LocationSample": "point", "AccountActivity": "point", "DailyHealthAggregate": "aggregate",
        "NetworkAggregate": "aggregate"}


def of(t):
    return [r for r in RECS if r["type"] == t]


class DeterminismTests(unittest.TestCase):
    def test_identical_across_builds(self):
        self.assertEqual(sp.dumps(sp.build()), sp.dumps(sp.build()))

    def test_committed_output_matches_generator(self):
        if OUT.exists():
            self.assertEqual(OUT.read_text(encoding="utf-8"), sp.dumps(DOC))

    def test_size_bound(self):
        # PG008 limit is 256 KiB; the lead asked for at most 240 KiB.
        self.assertLessEqual(len(sp.dumps(DOC).encode()), 240 * 1024)
        if OUT.exists():
            self.assertLessEqual(OUT.stat().st_size, 240 * 1024)


class EnvelopeTests(unittest.TestCase):
    def test_ids_unique_and_workspace_single(self):
        self.assertEqual(len(BY_ID), len(RECS))
        self.assertEqual({r["workspace_id"] for r in RECS}, {sp.WS})

    def test_required_envelope_and_vocabularies(self):
        for r in RECS:
            for k in ("id", "type", "workspace_id", "source_id", "evidence_class"):
                self.assertIn(k, r, r["id"])
            self.assertIn(r["evidence_class"], sp.EVIDENCE_CLASSES, r["id"])
            self.assertIn(r.get("granularity", "not_applicable"), sp.GRANULARITIES, r["id"])
            self.assertEqual("granularity" in r, r["type"] in TEMPORAL, r["id"])
            if r["type"] != "Link":
                self.assertEqual(set(r["provenance"]),
                                 {"source", "method", "method_version", "line_or_record"}, r["id"])

    def test_temporal_records_have_event_time_timezone_and_import_batch(self):
        for r in RECS:
            if r["type"] not in TEMPORAL:
                continue
            self.assertIn("timezone", r)
            self.assertTrue("event_time" in r or ("event_start" in r and "event_end" in r), r["id"])
            batch = BY_ID[r["import_batch_id"]]
            self.assertEqual(batch["type"], "ImportBatch")
            self.assertIn("import_time", batch)
            self.assertEqual(r["granularity"], GRAN.get(r["type"], "interval"), r["id"])
            if "event_start" in r:
                self.assertLessEqual(datetime.fromisoformat(r["event_start"]), datetime.fromisoformat(r["event_end"]))

    def test_event_time_differs_from_import_time(self):
        for r in of("LocationSample"):
            self.assertLess(datetime.fromisoformat(r["event_time"]),
                            datetime.fromisoformat(BY_ID[r["import_batch_id"]]["import_time"]))


class IntegrityTests(unittest.TestCase):
    def test_links_and_evidence_resolve(self):
        for l in of("Link"):
            self.assertIn(l["from"], BY_ID, l["id"])
            self.assertIn(l["to"], BY_ID, l["id"])
            self.assertTrue(l["evidence_ids"], l["id"])
            for e in l["evidence_ids"]:
                self.assertIn(e, BY_ID, l["id"])

    def test_inline_references_resolve(self):
        keys = ("source_id", "import_batch_id", "place_id", "from_place_id", "to_place_id", "app_id", "domain_id",
                "endpoint_domain_id", "snapshot_id", "target_id", "duplicate_of", "expected_place_id")
        for r in RECS:
            for k in keys:
                if r.get(k) is not None:
                    self.assertIn(r[k], BY_ID, f"{r['id']}.{k}")
            for k in ("confirmed_by", "possible_overlap_with", "also_seen_in_snapshots", "motivated_by_ids",
                      "supporting_evidence_ids", "contradicting_evidence_ids"):
                for e in r.get(k, []):
                    self.assertIn(e, BY_ID, f"{r['id']}.{k}")

    def test_finding_lists_mirror_links(self):
        for f in of("Finding"):
            for kind, key in (("SUPPORTED_BY", "supporting_evidence_ids"),
                              ("CONTRADICTED_BY", "contradicting_evidence_ids")):
                linked = [e for l in of("Link") if l["link_type"] == kind and l["from"] == f["id"]
                          for e in l["evidence_ids"]]
                self.assertEqual(linked, f[key], f["id"])

    def test_trips_have_corroborating_motion_links(self):
        corr = {l["from"]: l["to"] for l in of("Link") if l["link_type"] == "CORROBORATED_BY"}
        for t in of("Trip"):
            self.assertEqual(BY_ID[corr[t["id"]]]["type"], "ActivityInterval")


class EvidenceClassTests(unittest.TestCase):
    def test_findings(self):
        fs = {f["finding_kind"]: f for f in of("Finding")}
        self.assertEqual(set(fs), {"descriptive_pattern", "correlation", "hypothesis", "null_or_insufficient"})
        for f in fs.values():
            for k in ("input_window", "method", "method_version", "supporting_evidence_ids",
                      "contradicting_evidence_ids", "participant_correction", "uncertainty", "confidence"):
                self.assertIn(k, f, f["id"])
            self.assertIs(f["causal_claim"], False)
            cited = {BY_ID[e]["evidence_class"] for e in f["supporting_evidence_ids"] + f["contradicting_evidence_ids"]}
            self.assertFalse({"hypothesis", "prediction", "inference"} & cited, f["id"])
            if f["evidence_class"] == "inference":
                self.assertTrue(f["supporting_evidence_ids"])

    def test_hypothesis_is_not_proof(self):
        h = next(f for f in of("Finding") if f["finding_kind"] == "hypothesis")
        self.assertEqual(h["evidence_class"], "hypothesis")
        self.assertEqual(h["supporting_evidence_ids"], [])
        self.assertEqual(h["status"], "awaiting_evidence")
        self.assertTrue(h["needs_evidence"])
        for f in of("Finding"):
            self.assertNotIn(h["id"], f["supporting_evidence_ids"] + f["contradicting_evidence_ids"])

    def test_correlation_labelled_with_size_and_uncertainty(self):
        c = next(f for f in of("Finding") if f["finding_kind"] == "correlation")
        self.assertIn("CORRELATION, not causation", c["statement"])
        self.assertEqual(c["statistic"]["n"], 27)
        self.assertEqual(len(c["statistic"]["ci95_approx"]), 2)
        self.assertTrue(c["alternative_explanations"])

    def test_null_result_and_correction(self):
        n = next(f for f in of("Finding") if f["finding_kind"] == "null_or_insufficient")
        self.assertEqual(n["result"], "insufficient_evidence")
        self.assertLess(min(n["statistic"]["n_groups"]), n["statistic"]["min_n_rule"])
        cor = of("Correction")
        self.assertEqual(len(cor), 1)
        self.assertEqual(BY_ID[cor[0]["target_id"]]["participant_correction"], cor[0]["id"])

    def test_class_assignments(self):
        for t in ("Visit", "Trip"):
            self.assertTrue(all(r["evidence_class"] == "normalized_event" for r in of(t)))
        for t in ("LocationSample", "ActivityInterval", "DailyHealthAggregate", "ResourceAccess",
                  "NetworkAggregate", "AccountActivity"):
            self.assertTrue(all(r["evidence_class"] == "observation" for r in of(t)))
        self.assertTrue(all(r["evidence_class"] == "inference" for r in of("Place")))


class SemanticsTests(unittest.TestCase):
    def test_absent_health_is_unknown_not_zero(self):
        hs = of("DailyHealthAggregate")
        self.assertEqual(len(hs), sp.DAYS)
        for h in hs:
            self.assertEqual(h["heart_rate_resting"], sp.UNKNOWN)
            self.assertEqual(h["sleep_duration"], sp.UNKNOWN)
            self.assertEqual(h["read_authorization"], sp.UNKNOWN)
            self.assertNotEqual(h["steps"], 0)
        missing = [h for h in hs if h["steps"] == sp.UNKNOWN]
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]["steps_status"], "not_collected")
        src = BY_ID["src-healthkit"]
        self.assertEqual(src["read_authorization"], sp.UNKNOWN)
        self.assertEqual(src["last_probe"]["rows_returned"], 0)
        self.assertEqual(src["last_probe"]["measured_value"], sp.UNKNOWN)

    def test_network_aggregates_are_not_summed(self):
        nets = of("NetworkAggregate")
        self.assertTrue(all(n["summable"] is False for n in nets))
        self.assertFalse(any(k in ("total", "sum", "grand_total") for n in nets for k in n))
        by_key = {}
        for n in nets:
            by_key.setdefault((n["app_id"], n["domain_id"]), []).append(n)
        self.assertTrue(any(len(v) > 1 for v in by_key.values()))
        wins = sorted({(n["event_start"], n["event_end"]) for n in nets})
        self.assertTrue(any(wins[i][1] > wins[i + 1][0] for i in range(len(wins) - 1)), "snapshots must overlap")
        contacted = [l for l in of("Link") if l["link_type"] == "CONTACTED"]
        self.assertTrue(contacted)
        for l in contacted:
            self.assertEqual(l["combine"], "latest_snapshot_only_never_sum")

    def test_deliberate_gaps(self):
        def day(r):
            return (datetime.fromisoformat(r["event_time"]) - sp.START).days

        def mins(r):
            return (datetime.fromisoformat(r["event_time"]) - sp.START).seconds // 60

        samples = of("LocationSample")
        self.assertFalse([s for s in samples if day(s) == sp.NO_LOCATION_DAY])
        self.assertFalse([s for s in samples if day(s) == sp.GAP_DAY and sp.GAP_START <= mins(s) < sp.GAP_END])
        self.assertTrue([s for s in samples if day(s) == sp.GAP_DAY])
        kinds = {m["kind"] for m in BY_ID["src-location"]["missing_periods"]}
        self.assertEqual(kinds, {"no_location_day", "background_gap"})
        self.assertTrue(any(v["interrupted_by_gap"] for v in of("Visit")))
        motion_days = {(datetime.fromisoformat(a["event_start"]) - sp.START).days for a in of("ActivityInterval")}
        self.assertIn(sp.NO_LOCATION_DAY, motion_days)  # Motion continues where Location is absent

    def test_duplicate_import_adds_nothing(self):
        dup, orig = BY_ID["ib-apr-s2-again"], BY_ID["ib-apr-s2"]
        self.assertEqual(dup["status"], "duplicate_skipped")
        self.assertEqual(dup["duplicate_of"], "ib-apr-s2")
        self.assertEqual(dup["content_digest_sha256"], orig["content_digest_sha256"])
        self.assertEqual(dup["records_added"], 0)
        self.assertFalse([r for r in RECS if r.get("import_batch_id") == "ib-apr-s2-again"])

    def test_sources_cover_states(self):
        names = {s["name"] for s in of("Source")}
        self.assertTrue({"Location", "Motion", "HealthKit", "EventKit", "AppPrivacyReport", "AccountExport"} <= names)
        for s in of("Source"):
            for k in ("support", "provisioning", "coverage_status", "missing_periods", "record_count",
                      "latest_event_time", "export_success"):
                self.assertIn(k, s)
        self.assertIn("unavailable", json.dumps(BY_ID["src-healthkit"]["signals"]))
        self.assertTrue(BY_ID["src-apr"]["missing_periods"])
        self.assertEqual(BY_ID["src-account-export"]["fields_unavailable"][0], "duration")

    def test_calendar_scheduled_context_unless_confirmed(self):
        confirm = {l["to"]: l["from"] for l in of("Link") if l["link_type"] == "CONFIRMS"}
        evs = of("CalendarEvent")
        for e in evs:
            self.assertEqual(e["observed_duration"], sp.UNKNOWN)
            if e["id"] in confirm:
                self.assertEqual(e["role"], "observed_activity")
                self.assertEqual(e["confirmed_by"], [confirm[e["id"]]])
            else:
                self.assertEqual(e["role"], "scheduled_context")
                self.assertEqual(e["confirmed_by"], [])
        self.assertTrue(confirm)
        self.assertTrue(any(e["role"] == "scheduled_context" and e["possible_overlap_with"] for e in evs))
        self.assertTrue(any(e["role"] == "scheduled_context" and not e["possible_overlap_with"] for e in evs))

    def test_resource_access_unmatched_and_account_no_duration(self):
        acc = of("ResourceAccess")
        self.assertTrue(any(a["endpoint_match"] == "unmatched" and a["endpoint_domain_id"] is None for a in acc))
        self.assertTrue(any(a["endpoint_match"] == "matched" for a in acc))
        for a in of("AccountActivity"):
            self.assertEqual(a["duration_seconds"], sp.UNKNOWN)
            self.assertIn(a["activity_kind"], ("search", "watch", "like"))


class FictitiousTests(unittest.TestCase):
    def test_identifiers_are_fictitious(self):
        for a in of("App"):
            self.assertTrue(a["bundle_id"].startswith("com.example."))
        for d in of("Domain"):
            self.assertTrue(d["host"].endswith(".example"))
        for a in of("ResourceAccess"):
            if "endpoint_label" in a:
                self.assertTrue(a["endpoint_label"].endswith(".example"))
        self.assertIn("fictitious", DOC["meta"]["subject"])
        self.assertIn("fictional", DOC["meta"]["city"])
        self.assertTrue(DOC["meta"]["coordinates_fictitious"])
        self.assertIn("NOT a production schema", DOC["meta"]["status"])

    def test_coordinates_inside_fictitious_box(self):
        b = sp.BBOX
        pts = [(r["lat"], r["lon"]) for r in of("LocationSample") + of("Place")]
        self.assertTrue(pts)
        for lat, lon in pts:
            self.assertTrue(b["lat_min"] <= lat <= b["lat_max"] and b["lon_min"] <= lon <= b["lon_max"], (lat, lon))

    def test_reserved_domains_and_bundle_ids_only(self):
        import re
        hosts = [d["host"] for d in of("Domain")] + [a["endpoint_label"] for a in of("ResourceAccess") if "endpoint_label" in a]
        self.assertTrue(hosts)
        for h in hosts:
            self.assertRegex(h, r"^[a-z0-9.-]+\.example$")
        for a in of("App"):
            self.assertRegex(a["bundle_id"], r"^com\.example\.[a-z]+$")
        text = sp.dumps(DOC)
        # every dotted hostname-like token with a letter TLD must be reserved, a file name, or an ISO/tz token
        for tok in set(re.findall(r"[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+", text)):
            ok = (tok.endswith(".example") or tok.startswith("com.example.") or tok.startswith("ios.")
                  or tok.endswith((".jsonl", ".json", ".ndjson")) or tok in ("example-account-export",))
            self.assertTrue(ok, tok)

    def test_no_contact_details_or_real_urls(self):
        text = sp.dumps(DOC)
        for needle in ("http://", "https://", "@", "www."):
            self.assertNotIn(needle, text)


if __name__ == "__main__":
    unittest.main()
