"""Synthetic-only tests for SYN-07 through SYN-10. Not device or security tests."""

import unittest

from spikes import workspace_semantics as ws


POLICY = {"feature": "remove", "finding": "invalidate", "cache": "remove", "export": "invalidate"}


def build():
    store = ws.WorkspaceStore()
    for w, value in (("ws-a", "alpha"), ("ws-b", "beta")):
        store.add_source(w, "com.example.source", [{"v": value}])
        store.derive(w, "feature", "feat", ["com.example.source"], {"f": value})
        store.derive(w, "finding", "find", ["feat"], {"claim": value})
        store.derive(w, "cache", "cache", ["feat"], {"c": value})
        store.derive(w, "export", "exp", ["find"], {"e": value}, delivered=True)
    return store


class HealthTests(unittest.TestCase):
    def test_empty_query_with_write_status_is_unknown_not_zero_or_denied(self):
        obs = ws.health_query_observation([], "sharingAuthorized")
        self.assertEqual(obs["rows_returned"], 0)
        self.assertEqual(obs["measurements"], [])
        self.assertEqual(obs["measured_value"], ws.UNKNOWN)
        self.assertEqual(obs["read_authorization"], ws.UNKNOWN)
        self.assertEqual(obs["write_status"], "sharingAuthorized")
        self.assertEqual(obs["interpretation"], "no_rows_returned_cause_unknown")
        self.assertNotIn("denied", str(obs["interpretation"]))

    def test_denied_write_status_does_not_become_read_claim(self):
        obs = ws.health_query_observation([], "sharingDenied")
        self.assertEqual(obs["read_authorization"], ws.UNKNOWN)
        self.assertEqual(obs["write_status"], "sharingDenied")

    def test_missing_write_status_is_unknown(self):
        self.assertEqual(ws.health_query_observation([], None)["write_status"], ws.UNKNOWN)

    def test_rows_kept_and_read_authorization_still_not_asserted(self):
        rows = [{"type": "example.steps", "start": "2026-01-01T08:00:00Z"}]
        obs = ws.health_query_observation(rows, "sharingDenied")
        self.assertEqual(obs["measurements"], rows)
        self.assertIsNot(obs["measurements"][0], rows[0])
        self.assertEqual(obs["read_authorization"], ws.UNKNOWN)


class CalendarTests(unittest.TestCase):
    EVENT = {"id": "evt", "start": "2026-01-01T09:00:00Z", "end": "2026-01-01T10:00:00Z"}

    def test_planned_event_is_scheduled_context(self):
        r = ws.classify_calendar_events([self.EVENT], [])[0]
        self.assertEqual(r["role"], "scheduled_context")
        self.assertEqual(r["observed_duration"], ws.UNKNOWN)
        self.assertEqual(r["confirmed_by"], [])

    def test_overlap_alone_is_not_confirmation(self):
        obs = [{"id": "o1", "start": "2026-01-01T09:30:00Z", "end": "2026-01-01T09:40:00Z"}]
        r = ws.classify_calendar_events([self.EVENT], obs)[0]
        self.assertEqual(r["role"], "scheduled_context")
        self.assertEqual(r["possible_overlap_with"], ["o1"])

    def test_explicit_confirmation_makes_observed_but_duration_stays_unknown(self):
        obs = [{"id": "o1", "confirms_event_id": "evt"}]
        r = ws.classify_calendar_events([self.EVENT], obs)[0]
        self.assertEqual(r["role"], "observed_activity")
        self.assertEqual(r["confirmed_by"], ["o1"])
        self.assertEqual(r["observed_duration"], ws.UNKNOWN)

    def test_event_missing_times_does_not_fail(self):
        r = ws.classify_calendar_events([{"id": "x"}], [{"id": "o", "start": "a", "end": "b"}])[0]
        self.assertEqual(r["role"], "scheduled_context")
        self.assertEqual(r["possible_overlap_with"], [])


class IsolationTests(unittest.TestCase):
    def test_same_source_id_reads_are_isolated(self):
        store = build()
        self.assertEqual(store.read("ws-a", "com.example.source"), [{"v": "alpha"}])
        self.assertEqual(store.read("ws-b", "com.example.source"), [{"v": "beta"}])

    def test_unknown_workspace_or_id_raises(self):
        store = build()
        with self.assertRaises(KeyError):
            store.read("ws-c", "com.example.source")
        with self.assertRaises(KeyError):
            store.read("ws-a", "missing")

    def test_returned_content_is_a_copy(self):
        store = build()
        store.read("ws-a", "com.example.source")[0]["v"] = "tampered"
        self.assertEqual(store.read("ws-a", "com.example.source"), [{"v": "alpha"}])

    def test_links_cannot_cross_workspaces(self):
        store = build()
        store.add_source("ws-a", "only-a", [])
        with self.assertRaises(KeyError):
            store.derive("ws-b", "feature", "bad", ["only-a"], {})

    def test_corrections_are_isolated(self):
        store = build()
        store.correct("ws-a", "find", "wrong")
        self.assertEqual(store.corrections("ws-a", "find"), ["wrong"])
        self.assertEqual(store.corrections("ws-b", "find"), [])

    def test_exports_contain_only_own_workspace(self):
        store = build()
        store.correct("ws-a", "find", "wrong")
        out = store.export("ws-a")
        self.assertEqual(out["workspace"], "ws-a")
        self.assertNotIn("beta", str(out))
        self.assertEqual(out["nodes"]["find"]["corrections"], ["wrong"])
        self.assertEqual(out["nodes"]["find"]["parents"], ["feat"])
        self.assertNotIn("wrong", str(store.export("ws-b")))


class DeletionTests(unittest.TestCase):
    def test_policy_applied_transitively_and_other_workspace_preserved(self):
        store = build()
        before_b = store.snapshot("ws-b")
        report = store.delete_source("ws-a", "com.example.source", POLICY)
        self.assertEqual(report["actions"], {
            "com.example.source": "remove", "feat": "remove", "find": "invalidate",
            "cache": "remove", "exp": "invalidate"})
        with self.assertRaises(KeyError):
            store.read("ws-a", "com.example.source")
        with self.assertRaises(KeyError):
            store.read("ws-a", "feat")
        self.assertEqual(store.read("ws-a", "find"), {"status": "invalidated"})
        self.assertEqual(store.read("ws-a", "exp"), {"status": "invalidated"})
        self.assertEqual(store.snapshot("ws-b"), before_b)
        self.assertEqual(store.read("ws-b", "find"), {"claim": "beta"})
        self.assertIn("beta", str(store.export("ws-b")))

    def test_delivered_export_reported_as_unverified_copy(self):
        store = build()
        report = store.delete_source("ws-a", "com.example.source", POLICY)
        self.assertEqual(report["unverified_copies"], ["exp"])

    def test_undelivered_export_is_not_flagged(self):
        store = ws.WorkspaceStore()
        store.add_source("w", "s", [])
        store.derive("w", "export", "e", ["s"], {}, delivered=False)
        self.assertEqual(store.delete_source("w", "s", POLICY)["unverified_copies"], [])

    def test_exports_after_deletion_omit_invalidated_content(self):
        store = build()
        store.delete_source("ws-a", "com.example.source", POLICY)
        self.assertEqual(store.export("ws-a")["nodes"], {})

    def test_corrections_on_removed_dropped_and_tombstones_flagged(self):
        store = build()
        store.correct("ws-a", "feat", "n1")
        store.correct("ws-a", "find", "n2")
        report = store.delete_source("ws-a", "com.example.source", POLICY)
        self.assertEqual(report["orphaned_corrections"], ["feat", "find"])
        self.assertEqual(store.corrections("ws-a", "feat"), [])
        self.assertEqual(store.corrections("ws-a", "find"), ["n2"])

    def test_incomplete_or_invalid_policy_rejected_without_change(self):
        store = build()
        before = store.snapshot("ws-a")
        for bad in ({}, {"feature": "remove"}, {**POLICY, "cache": "keep"}, {**POLICY, "extra": "remove"}):
            with self.assertRaises(ValueError):
                store.delete_source("ws-a", "com.example.source", bad)
        self.assertEqual(store.snapshot("ws-a"), before)

    def test_deleting_non_source_or_missing_raises(self):
        store = build()
        with self.assertRaises(KeyError):
            store.delete_source("ws-a", "feat", POLICY)
        with self.assertRaises(KeyError):
            store.delete_source("ws-c", "com.example.source", POLICY)

    def test_unrelated_source_in_same_workspace_survives(self):
        store = build()
        store.add_source("ws-a", "other", [1])
        store.derive("ws-a", "feature", "feat2", ["other"], {"k": 1})
        store.delete_source("ws-a", "com.example.source", POLICY)
        self.assertEqual(store.read("ws-a", "feat2"), {"k": 1})

    def test_multi_parent_dependent_invalidated_when_any_source_deleted(self):
        store = ws.WorkspaceStore()
        store.add_source("w", "s1", [])
        store.add_source("w", "s2", [])
        store.derive("w", "finding", "f", ["s1", "s2"], {"x": 1})
        store.delete_source("w", "s1", POLICY)
        self.assertEqual(store.read("w", "f"), {"status": "invalidated"})
        self.assertEqual(store.read("w", "s2"), [])


if __name__ == "__main__":
    unittest.main()
