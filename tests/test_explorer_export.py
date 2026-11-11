"""Synthetic-only tests for the explorer exporter and contract validator."""

from contextlib import redirect_stderr, redirect_stdout
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest

from spikes import explorer_export as ex

ROOT = Path(__file__).resolve().parents[1]
PERSONA = ROOT / "prototypes" / "explorer-concept" / "data" / "persona.json"
OUTPUT = ROOT / "prototypes" / "explorer-cinematic" / "data" / "fixtures-workspace.json"


def of(doc, rtype):
    return [r for r in doc["records"] if r["type"] == rtype]


class MappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = ex.build_fixture_document()

    def test_meta_and_counts(self):
        m = self.doc["meta"]
        self.assertIs(m["synthetic"], True)
        self.assertEqual(m["workspace_id"], "ws-demo-02")
        self.assertIn("Fixture-derived", m["notice"])
        self.assertEqual(m["contract_version"], "persona-contract-0.1-provisional")
        self.assertEqual(m["type_counts"], {"Source": 2, "App": 1, "Domain": 3, "ImportBatch": 5,
                                            "ResourceAccess": 3, "NetworkAggregate": 2,
                                            "AccountActivity": 10, "Link": 6})
        self.assertEqual(ex.validate_contract(self.doc), [])

    def test_incomplete_intervals_stay_incomplete(self):
        by = {r["interval_status"]: r for r in of(self.doc, "ResourceAccess")}
        self.assertEqual(set(by), {"complete", "missing_end", "missing_begin"})
        self.assertEqual(by["complete"]["duration_seconds"], 600)
        self.assertEqual(by["missing_end"]["event_end"], "unknown")
        self.assertNotEqual(by["missing_end"]["event_start"], "unknown")
        self.assertEqual(by["missing_begin"]["event_start"], "unknown")
        for st in ("missing_end", "missing_begin"):
            self.assertEqual(by[st]["duration_seconds"], "unknown")

    def test_network_aggregates_never_summable_or_summed(self):
        nets = of(self.doc, "NetworkAggregate")
        self.assertEqual(sorted(n["hits"] for n in nets), [5, 8])
        self.assertTrue(all(n["summable"] is False for n in nets))
        contacted = [l for l in of(self.doc, "Link") if l["link_type"] == "CONTACTED"]
        self.assertEqual(len(contacted), 1)
        self.assertEqual(contacted[0]["combine"], "latest_snapshot_only_never_sum")
        self.assertEqual(len(contacted[0]["evidence_ids"]), 2)

    def test_duplicate_batches_link_and_add_no_records(self):
        dups = [b for b in of(self.doc, "ImportBatch") if b["status"] == "duplicate_skipped"]
        self.assertEqual(len(dups), 2)
        links = {(l["from"], l["to"]) for l in of(self.doc, "Link") if l["link_type"] == "DUPLICATE_OF"}
        for b in dups:
            self.assertEqual(b["records_added"], 0)
            self.assertIn((b["id"], b["duplicate_of"]), links)
        self.assertFalse([a for a in of(self.doc, "AccountActivity") if a["import_batch_id"] == "ib-account-2"])
        self.assertEqual(len(of(self.doc, "AccountActivity")), 10)

    def test_ledger_info_and_fixed_import_time(self):
        b = next(x for x in of(self.doc, "ImportBatch") if x["id"] == "ib-apr-s1")
        self.assertEqual(b["import_time"], "2026-01-10T00:00:00Z")
        self.assertEqual(b["ledger"]["supported_records"], 4)
        self.assertEqual(b["collection_window"], "unknown")

    def test_unknown_not_zero_in_account_activity(self):
        acts = of(self.doc, "AccountActivity")
        self.assertTrue(all(a["duration_seconds"] == "unknown" for a in acts))
        bad_time = [a for a in acts if a["event_time_status"] == "invalid"]
        self.assertEqual(len(bad_time), 1)
        self.assertEqual(bad_time[0]["event_time"], "unknown")
        self.assertIn("invalid_time", bad_time[0]["source_issue_codes"])
        self.assertEqual(len([a for a in acts if a["duration_status"] == "invalid"]), 1)

    def test_sources_declare_only_known_coverage(self):
        for s in of(self.doc, "Source"):
            self.assertEqual(s["coverage_status"], "unknown")
            self.assertEqual(s["missing_periods"], [])
            self.assertEqual(s["missing_periods_status"], "unknown")
        apr = next(s for s in of(self.doc, "Source") if s["id"] == "src-apr")
        self.assertEqual(apr["latest_event_time"], "2026-01-03T09:00:00Z")
        self.assertEqual(apr["unmeasured"]["collection_window"], "unknown")
        acct = next(s for s in of(self.doc, "Source") if s["id"] == "src-account-export")
        self.assertIn("duration", acct["fields_unavailable"])

    def test_provenance_on_non_link_records(self):
        keys = {"source", "method", "method_version", "line_or_record"}
        for r in self.doc["records"]:
            if r["type"] != "Link":
                self.assertEqual(set(r["provenance"]), keys, r["id"])

    def test_deterministic_and_checked_in_output(self):
        text = ex.dumps(self.doc)
        self.assertEqual(text, ex.dumps(ex.build_fixture_document()))
        self.assertEqual(OUTPUT.read_text(encoding="utf-8"), text)
        self.assertLess(len(text.encode()), 240 * 1024)


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.doc = copy.deepcopy(ex.build_fixture_document())

    def problems(self):
        return " | ".join(ex.validate_contract(self.doc))

    def rec(self, rid):
        return next(r for r in self.doc["records"] if r["id"] == rid)

    def test_clean(self):
        self.assertEqual(ex.validate_contract(self.doc), [])

    def test_duplicate_id(self):
        self.doc["records"].append(copy.deepcopy(self.doc["records"][1]))
        self.assertIn("duplicate id", self.problems())

    def test_dangling_reference(self):
        self.rec("access-s1-01")["app_id"] = "app-missing"
        self.assertIn("unresolved reference app-missing", self.problems())
        self.setUp()
        next(r for r in self.doc["records"] if r["type"] == "Link")["evidence_ids"].append("ghost")
        self.assertIn("unresolved reference ghost", self.problems())

    def test_bad_evidence_class(self):
        self.rec("net-s1-01")["evidence_class"] = "fact"
        self.assertIn("evidence_class not allowed", self.problems())

    def test_second_workspace(self):
        self.rec("net-s1-01")["workspace_id"] = "ws-other"
        self.assertIn("workspace_id differs", self.problems())

    def test_zero_where_unknown(self):
        self.rec("acct-1-0001")["duration_seconds"] = 0
        self.assertIn("numeric although", self.problems())
        self.setUp()
        self.rec("access-s1-02")["duration_seconds"] = 0
        self.assertIn("incomplete interval carries a numeric duration", self.problems())

    def test_invented_end(self):
        self.rec("access-s1-02")["event_end"] = "2026-01-02T09:05:00Z"
        self.assertIn("invented end", self.problems())

    def test_missing_synthetic_flag(self):
        del self.doc["meta"]["synthetic"]
        self.assertIn("meta.synthetic", self.problems())

    def test_unparseable_time(self):
        self.rec("net-s1-01")["event_start"] = "yesterday"
        self.assertIn("event_start not parseable", self.problems())

    def test_summable_network(self):
        self.rec("net-s1-01")["summable"] = True
        self.assertIn("summable false", self.problems())

    def test_duplicate_without_link(self):
        self.doc["records"] = [r for r in self.doc["records"]
                               if not (r["type"] == "Link" and r["link_type"] == "DUPLICATE_OF")]
        self.doc["meta"]["type_counts"]["Link"] -= 2
        self.assertIn("lacks a DUPLICATE_OF link", self.problems())

    def test_type_counts_mismatch(self):
        self.doc["meta"]["type_counts"]["App"] = 9
        self.assertIn("type_counts", self.problems())

    def test_persona_json_validates(self):
        persona = json.loads(PERSONA.read_text(encoding="utf-8"))
        self.assertEqual(ex.validate_contract(persona), [])

    def test_not_a_document(self):
        self.assertTrue(ex.validate_contract([]))


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        out = io.StringIO()
        with redirect_stdout(out):
            code = ex.main(list(args))
        return code, out.getvalue()

    def test_summary_default(self):
        code, out = self.run_cli("--fixtures")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["validation"], "ok")
        self.assertNotIn("records", data)

    def test_requires_fixtures_flag(self):
        code, out = self.run_cli()
        self.assertEqual(code, 0)
        self.assertIn("--fixtures", out)

    def test_refuses_repo_paths(self):
        for p in (ROOT / "out.json", ROOT / "docs" / "x.json", ROOT / "prototypes" / "x.json",
                  ROOT / "prototypes" / "explorer-cinematic" / "x.json",
                  ROOT / "prototypes" / "explorer-cinematic" / "data"):
            code, _ = self.run_cli("--fixtures", "--out", str(p))
            self.assertEqual(code, 2, p)
        self.assertFalse((ROOT / "out.json").exists())

    def test_allows_outside_repo_and_prototype_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "sub" / "w.json"
            code, _ = self.run_cli("--fixtures", "--out", str(target))
            self.assertEqual(code, 0)
            self.assertEqual(target.read_text(encoding="utf-8"), ex.dumps(ex.build_fixture_document()))
        ex.check_out_path(ROOT / "prototypes" / "explorer-cinematic" / "data" / "fixtures-workspace.json")

    def test_no_raw_input_argument(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            ex.main(["--fixtures", "--input", "x"])

    def test_invalid_document_not_written(self):
        doc = ex.build_fixture_document()
        doc["meta"]["synthetic"] = "yes"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ex.ExportError):
                ex.write_document(doc, Path(tmp) / "w.json")
            self.assertFalse((Path(tmp) / "w.json").exists())


if __name__ == "__main__":
    unittest.main()
