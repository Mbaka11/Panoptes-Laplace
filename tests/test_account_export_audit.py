"""Synthetic-only tests for the account-export audit spike."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import unittest

from spikes import account_export_audit as aea

FIXTURES = Path(__file__).resolve().parents[1] / "spikes" / "fixtures" / "account_export"


def js(*records):
    return json.dumps(list(records), indent=1).encode()


def rec(title="Watched Synthetic", time="2026-01-01T00:00:00Z", **kw):
    r = {"title": title, "time": time, "products": ["Example"]}
    r.update(kw)
    return r


class AuditTests(unittest.TestCase):
    def fixture_audit(self):
        return aea.inspect_bytes((FIXTURES / "activity.json").read_bytes())

    def test_fixture_counts_and_statuses(self):
        a = self.fixture_audit()
        self.assertTrue(a.parse_complete)
        self.assertEqual(a.total_elements, 11)
        cov = aea.coverage([a])
        self.assertEqual(cov["records_counted"], 10)  # non-object reported, not counted
        f = cov["fields"]
        self.assertEqual(f["viewed_content"]["status"], "present")
        self.assertEqual(f["searches"]["status"], "present")
        self.assertEqual(f["interactions"]["status"], "present")
        self.assertEqual(f["timestamps"]["status"], "present")
        self.assertEqual(f["duration"]["status"], "absent")

    def test_missingness_and_extrema(self):
        cov = aea.coverage([self.fixture_audit()])
        self.assertEqual(cov["missingness"]["time"], 1)  # one unparseable time
        self.assertEqual(cov["missingness"]["title"], 1)
        self.assertEqual(cov["timestamp_min"], "2026-01-01T08:00:00+00:00")
        self.assertEqual(cov["timestamp_max"], "2026-01-06T08:00:00+00:00")

    def test_issues_reported_with_provenance(self):
        a = self.fixture_audit()
        codes = {(i.code) for i in a.issues}
        for c in ("invalid_time", "missing_title", "invalid_products", "record_not_object",
                  "invalid_duration", "unknown_fields", "unclassified_title"):
            self.assertIn(c, codes)
        bad = [i for i in a.issues if i.code == "record_not_object"][0]
        self.assertEqual(bad.record, 9)
        self.assertEqual(bad.line, 11)  # 1-based physical line of the element
        self.assertTrue(all(i.line for i in a.issues if i.record is not None))

    def test_timezone_offset_normalized(self):
        a = aea.inspect_bytes(js(rec(time="2026-01-04T07:15:00-05:00")))
        self.assertEqual(a.records[0].time.isoformat(), "2026-01-04T12:15:00+00:00")

    def test_no_dwell_or_scroll_inference(self):
        a = aea.inspect_bytes(js(rec(time="2026-01-01T00:00:00Z"), rec(time="2026-01-01T00:05:00Z")))
        cov = aea.coverage([a])
        self.assertEqual(cov["fields"]["viewed_content"]["status"], "present")
        self.assertEqual(cov["fields"]["duration"]["status"], "absent")
        self.assertFalse(cov["dwell_time_inferred"])
        self.assertFalse(cov["scroll_depth_inferred"])
        self.assertNotIn("scroll", json.dumps(cov["fields"]).replace("scroll_depth_inferred", ""))

    def test_explicit_duration_counted(self):
        a = aea.inspect_bytes(js(rec(durationSeconds=12.5), rec()))
        self.assertEqual(aea.coverage([a])["fields"]["duration"]["records"], 1)

    def test_unknown_when_empty_or_unclassified(self):
        cov = aea.coverage([aea.inspect_bytes(b"[]")])
        self.assertEqual(cov["fields"]["searches"]["status"], "unknown")
        cov = aea.coverage([aea.inspect_bytes(js(rec(title="Used something")))])
        self.assertEqual(cov["fields"]["searches"]["status"], "unknown")
        self.assertEqual(cov["fields"]["viewed_content"]["status"], "unknown")

    def test_duplicate_import_not_double_counted(self):
        one = (FIXTURES / "activity.json").read_bytes()
        two = (FIXTURES / "activity_reformatted_copy.json").read_bytes()
        self.assertNotEqual(one, two)
        results = aea.inspect_imports([("a", one), ("b", two)])
        self.assertIsNone(results[0][1].duplicate_of)
        self.assertEqual(results[1][1].duplicate_of, "a")
        single = aea.coverage([results[0][1]])
        both = aea.coverage([a for _, a in results])
        self.assertEqual(both["records_counted"], single["records_counted"])
        self.assertEqual(both["duplicate_imports"], 1)
        self.assertEqual(both["fields"], single["fields"])

    def test_changed_content_not_duplicate(self):
        r = aea.inspect_imports([("a", js(rec())), ("b", js(rec(), rec(title="Searched for x")))])
        self.assertIsNone(r[1][1].duplicate_of)

    def test_malformed_json_reported(self):
        a = aea.inspect_bytes(b'[\n{"title": "Watched x", "time": "2026-01-01T00:00:00Z"},\n{oops}\n]')
        self.assertFalse(a.parse_complete)
        self.assertEqual(len(a.records), 1)
        bad = [i for i in a.issues if i.code == "malformed_json_stop"][0]
        self.assertEqual(bad.line, 3)
        self.assertEqual(aea.coverage([a])["parse_complete"], False)

    def test_structural_failures(self):
        self.assertEqual(aea.inspect_bytes(b"{}").issues[0].code, "not_a_json_list")
        self.assertEqual(aea.inspect_bytes(b"\xff\xfe").issues[0].code, "invalid_utf8")
        t = aea.inspect_bytes(b'[{"title":"Watched x"}')
        self.assertFalse(t.parse_complete)
        self.assertIn("malformed_json_stop", [i.code for i in t.issues])
        self.assertIn("truncated_list", [i.code for i in aea.inspect_bytes(b'[{"title":"Watched x"},').issues])
        a = aea.inspect_bytes(b"[] junk")
        self.assertIn("trailing_content", [i.code for i in a.issues])

    def test_limits(self):
        with self.assertRaises(aea.InputLimitError):
            aea.inspect_bytes(b" " * (aea.MAX_BYTES + 1))

    def test_issues_do_not_echo_source_values(self):
        secret = "SECRET-synthetic-marker"
        a = aea.inspect_bytes(js(rec(time=secret, **{secret: 1})))
        blob = json.dumps(aea.provenance(a)) + json.dumps(aea.coverage([a]))
        self.assertNotIn(secret, blob.replace("<redacted>", ""))

    def test_cli_demo(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(aea.main(["--demo", "--provenance"]), 0)
        report = json.loads(out.getvalue())
        self.assertEqual(report["duplicate_imports"], 1)
        self.assertEqual(report["export_completeness"], "unknown")
        self.assertIn("unverified", report["schema_status"])
        self.assertIn("activity.json", report["provenance"])


if __name__ == "__main__":
    unittest.main()
