"""Synthetic-only lifecycle tests for XFR-01 / ISO-01 / DEL-01.

The payload is NOT encrypted; HMAC is a stand-in. These tests do not show confidentiality
or that any real ciphersuite is secure.
"""

import copy
import secrets
import unittest

from spikes import transfer_package as tp

LO, HI = "2026-01-01T00:00:00+00:00", "2026-02-01T00:00:00+00:00"
CAL, STEPS = "com.example.calendar", "com.example.steps"


def rec(source, rid, ts, value="synthetic"):
    return {"source": source, "id": rid, "ts": ts, "value": value}


RECORDS = [
    rec(CAL, "e1", "2026-01-05T09:00:00+00:00"),
    rec(CAL, "e2", "2026-01-31T23:59:59+00:00"),
    rec(CAL, "e3", "2026-02-01T00:00:00+00:00"),   # boundary: excluded (to is exclusive)
    rec(CAL, "e0", "2025-12-31T23:59:59+00:00"),   # before window
    rec(STEPS, "s1", "2026-01-06T09:00:00+00:00"),
]


class Base(unittest.TestCase):
    def setUp(self):
        self.key = secrets.token_bytes(32)  # generated in-test, never written
        self.log = tp.StagingLog()
        self.imp = tp.Importer("ws.example.a", "mac.example", {"phone.example": self.key})

    def build(self, **kw):
        args = dict(sender_id="phone.example", sender_key=self.key, recipient_id="mac.example",
                    workspace_id="ws.example.a", package_id="pkg-1", sequence=1, sources=[CAL],
                    date_from=LO, date_to=HI, log=self.log)
        args.update(kw)
        return tp.build_package(RECORDS, **args)

    def assertRejected(self, pkg, code, importer=None):
        with self.assertRaises(tp.ImportRejected) as cm:
            (importer or self.imp).import_package(pkg)
        self.assertEqual(cm.exception.code, code)
        return cm.exception


class ScopeTests(Base):
    def test_round_trip_only_selected_sources_and_dates(self):
        result = self.imp.import_package(self.build())
        self.assertEqual(result["status"], "imported")
        self.assertEqual(result["new"], 2)
        self.assertEqual(sorted(i for _, i in self.imp.records), ["e1", "e2"])

    def test_unselected_source_never_in_package(self):
        pkg = self.build()
        self.assertEqual(list(pkg["files"]), [f"{CAL}.ndjson"])
        self.assertNotIn(b"s1", b"".join(pkg["files"].values()))

    def test_other_source_selection(self):
        self.imp.import_package(self.build(sources=[STEPS]))
        self.assertEqual(list(self.imp.records), [(STEPS, "s1")])

    def test_boundaries_inclusive_from_exclusive_to(self):
        pkg = self.build(date_from="2026-01-05T09:00:00+00:00", date_to="2026-02-01T00:00:00+00:00")
        self.imp.import_package(pkg)
        ids = sorted(i for _, i in self.imp.records)
        self.assertEqual(ids, ["e1", "e2"])  # e1 on 'from' included; e3 on 'to' excluded

    def test_out_of_scope_record_in_authenticated_package_rejected(self):
        # A malicious/buggy sender tags a package whose file holds an out-of-scope record.
        pkg = self.build()
        name = f"{CAL}.ndjson"
        bad = pkg["files"][name] + tp._canon(RECORDS[2]) + b"\n"
        pkg["files"][name] = bad
        pkg["manifest"]["files"][0].update(sha256=tp._sha256(bad), size=len(bad))
        pkg["tag"] = tp._tag(self.key, pkg["header"], pkg["manifest"])
        self.assertRejected(pkg, "scope_violation")
        self.assertEqual(self.imp.records, {})


class TamperTests(Base):
    def test_payload_bit_flip_rejected_and_nothing_written(self):
        pkg = self.build()
        name = f"{CAL}.ndjson"
        data = bytearray(pkg["files"][name])
        data[10] ^= 0x01
        pkg["files"][name] = bytes(data)
        self.assertRejected(pkg, "integrity_failure")
        self.assertEqual(self.imp.records, {})
        self.assertEqual(self.imp.package_ledger, set())

    def test_payload_tamper_with_recomputed_file_digest_still_rejected(self):
        # Shows a bare hash is not authentication: manifest edit breaks the keyed tag.
        pkg = self.build()
        name = f"{CAL}.ndjson"
        bad = pkg["files"][name].replace(b"synthetic", b"forged-xx")
        pkg["files"][name] = bad
        pkg["manifest"]["files"][0].update(sha256=tp._sha256(bad), size=len(bad))
        self.assertRejected(pkg, "integrity_failure")

    def test_manifest_edit_rejected(self):
        pkg = self.build()
        pkg["manifest"]["scope"]["date_to"] = "2027-01-01T00:00:00+00:00"
        self.assertRejected(pkg, "integrity_failure")

    def test_header_edit_rejected(self):
        pkg = self.build()
        pkg["header"]["package_id"] = "pkg-other"
        self.assertRejected(pkg, "integrity_failure")

    def test_tag_edit_rejected(self):
        pkg = self.build()
        pkg["tag"] = "0" * 64
        self.assertRejected(pkg, "integrity_failure")

    def test_forger_with_wrong_key_using_enrolled_id_rejected(self):
        pkg = self.build(sender_key=secrets.token_bytes(32))
        self.assertRejected(pkg, "integrity_failure")

    def test_unknown_sender_rejected(self):
        pkg = self.build(sender_id="phone.unenrolled.example", sender_key=secrets.token_bytes(32))
        self.assertRejected(pkg, "unknown_sender")

    def test_missing_file_rejected(self):
        pkg = self.build(sources=[CAL, STEPS])
        del pkg["files"][f"{STEPS}.ndjson"]
        self.assertRejected(pkg, "file_set_mismatch")

    def test_extra_file_rejected(self):
        pkg = self.build()
        pkg["files"]["com.example.extra.ndjson"] = b"{}\n"
        self.assertRejected(pkg, "file_set_mismatch")

    def test_swapped_file_from_other_package_rejected(self):
        a, b = self.build(), self.build(package_id="pkg-2", sequence=2, date_to="2026-01-20T00:00:00+00:00")
        a["files"] = b["files"]
        self.assertRejected(a, "integrity_failure")

    def test_malformed_package_rejected(self):
        self.assertRejected({"header": {}}, "malformed")
        self.assertRejected("not a package", "malformed")

    def test_path_traversal_file_name_rejected(self):
        pkg = self.build()
        name = f"{CAL}.ndjson"
        evil = "../escape.ndjson"
        pkg["files"] = {evil: pkg["files"][name]}
        pkg["manifest"]["files"][0]["name"] = evil
        pkg["tag"] = tp._tag(self.key, pkg["header"], pkg["manifest"])
        self.assertRejected(pkg, "malformed")


class BindingTests(Base):
    def test_wrong_workspace_rejected(self):
        pkg = self.build(workspace_id="ws.example.b")
        self.assertRejected(pkg, "wrong_workspace")
        self.assertEqual(self.imp.records, {})

    def test_wrong_recipient_rejected(self):
        self.assertRejected(self.build(recipient_id="mac.other.example"), "wrong_recipient")

    def test_editing_workspace_in_manifest_to_match_is_integrity_failure(self):
        pkg = self.build(workspace_id="ws.example.b")
        pkg["manifest"]["workspace_id"] = "ws.example.a"
        self.assertRejected(pkg, "integrity_failure")

    def test_unsupported_future_version_rejected(self):
        self.assertRejected(self.build(format_version=3), "unsupported_version")

    def test_validly_tagged_old_version_is_a_downgrade_and_rejected(self):
        self.assertRejected(self.build(format_version=1), "unsupported_version")

    def test_header_version_rewritten_to_old_rejected(self):
        pkg = self.build()
        pkg["header"]["format_version"] = 1
        self.assertRejected(pkg, "unsupported_version")

    def test_unknown_algorithm_rejected(self):
        pkg = self.build()
        pkg["header"]["alg"] = "NONE"
        self.assertRejected(pkg, "unsupported_version")

    def test_colliding_ids_in_two_workspaces_stay_separate(self):
        other = tp.Importer("ws.example.b", "mac.example", {"phone.example": self.key})
        self.imp.import_package(self.build())
        other.import_package(self.build(workspace_id="ws.example.b"))
        self.assertEqual(self.imp.records.keys(), other.records.keys())  # same source IDs
        self.imp.delete_record(CAL, "e1")
        self.assertIn((CAL, "e1"), other.records)
        self.assertRejected(self.build(), "wrong_workspace", importer=other)

    def test_failure_messages_contain_no_record_values(self):
        marker = "ZZ-SECRET-MARKER"
        recs = [rec(CAL, "e1", "2026-01-05T09:00:00+00:00", marker)]
        pkg = tp.build_package(recs, sender_id="phone.example", sender_key=self.key,
                               recipient_id="mac.other.example", workspace_id="ws.example.a",
                               package_id="pkg-m", sequence=1, sources=[CAL], date_from=LO, date_to=HI)
        exc = self.assertRejected(pkg, "wrong_recipient")
        self.assertNotIn(marker, str(exc))
        self.assertFalse(any(marker in line for line in self.imp.audit))


class ReplayTests(Base):
    """Policy: R1 package-ID ledger + R3 per-sender monotonic sequence (see docs)."""

    def test_exact_reimport_is_idempotent_duplicate(self):
        pkg = self.build()
        self.imp.import_package(pkg)
        before = copy.deepcopy(self.imp.records)
        again = self.imp.import_package(pkg)
        self.assertEqual(again["status"], "duplicate")
        self.assertEqual((again["new"], again["changed"]), (0, 0))
        self.assertEqual(self.imp.records, before)

    def test_replay_of_old_package_after_newer_rejected(self):
        old = self.build(package_id="pkg-old", sequence=1)
        new = self.build(package_id="pkg-new", sequence=2)
        self.imp.import_package(new)
        self.assertRejected(old, "replay_rejected")
        self.assertNotIn("pkg-old", self.imp.package_ledger)

    def test_replay_cannot_resurrect_deleted_record(self):
        old = self.build(package_id="pkg-old", sequence=1)
        self.imp.import_package(old)
        self.imp.import_package(self.build(package_id="pkg-new", sequence=2, sources=[STEPS]))
        self.imp.delete_record(CAL, "e1")
        # Known old ID: R1 reports duplicate with no state change; e1 stays deleted.
        self.assertEqual(self.imp.import_package(old)["status"], "duplicate")
        self.assertNotIn((CAL, "e1"), self.imp.records)
        # Never-seen old ID with a stale sequence: R3 rejects.
        self.assertRejected(self.build(package_id="pkg-old-2", sequence=1), "replay_rejected")
        self.assertNotIn((CAL, "e1"), self.imp.records)

    def test_newer_package_does_not_resurrect_tombstoned_record(self):
        self.imp.import_package(self.build())
        self.imp.delete_record(CAL, "e1")
        result = self.imp.import_package(self.build(package_id="pkg-2", sequence=2))
        self.assertEqual(result["skipped_tombstoned"], 1)
        self.assertNotIn((CAL, "e1"), self.imp.records)

    def test_overlapping_packages_do_not_inflate(self):
        self.imp.import_package(self.build())
        result = self.imp.import_package(self.build(package_id="pkg-2", sequence=2))
        self.assertEqual((result["new"], result["unchanged"]), (0, 2))
        self.assertEqual(len(self.imp.records), 2)

    def test_same_id_reused_with_different_content_is_still_duplicate_no_change(self):
        self.imp.import_package(self.build())
        again = self.imp.import_package(self.build(date_to="2026-01-10T00:00:00+00:00"))
        self.assertEqual(again["status"], "duplicate")
        self.assertEqual(len(self.imp.records), 2)

    def test_sequences_are_per_sender(self):
        key2 = secrets.token_bytes(32)
        imp = tp.Importer("ws.example.a", "mac.example", {"phone.example": self.key, "phone2.example": key2})
        imp.import_package(self.build(sequence=5))
        pkg = self.build(sender_id="phone2.example", sender_key=key2, package_id="pkg-b", sequence=1)
        self.assertEqual(imp.import_package(pkg)["status"], "imported")

    def test_out_of_order_legitimate_package_is_rejected_documented_tradeoff(self):
        self.imp.import_package(self.build(package_id="pkg-3", sequence=3))
        self.assertRejected(self.build(package_id="pkg-2", sequence=2), "replay_rejected")

    def test_failed_import_does_not_advance_ledger_or_sequence(self):
        bad = self.build(package_id="pkg-bad", sequence=9)
        bad["files"][f"{CAL}.ndjson"] += b" "
        self.assertRejected(bad, "integrity_failure")
        self.assertEqual(self.imp.last_sequence, {})
        self.assertEqual(self.imp.import_package(self.build())["status"], "imported")

    def test_ledger_and_audit_hold_no_record_values(self):
        self.imp.import_package(self.build())
        blob = repr((self.imp.package_ledger, self.imp.last_sequence, self.imp.tombstones, self.imp.audit))
        self.assertNotIn("synthetic", blob)


class InventoryTests(Base):
    def test_success_inventory_lists_deleted_temp_copies_verified_absent(self):
        self.imp.import_package(self.build())
        entries = {e["copy_id"]: e for e in self.log.inventory() + self.imp.log.inventory()}
        sender = entries["pkg-1:sender_plaintext_export"]
        self.assertEqual((sender["disposition"], sender["verified_absent"]), ("deleted", True))
        mac = entries["pkg-1:validation_temp"]
        self.assertEqual((mac["disposition"], mac["verified_absent"]), ("deleted", True))

    def test_failure_also_cleans_validation_temp(self):
        pkg = self.build()
        pkg["files"][f"{CAL}.ndjson"] += b" "
        self.assertRejected(pkg, "integrity_failure")
        entry = next(e for e in self.imp.log.entries if e["copy_id"].endswith("validation_temp"))
        self.assertTrue(entry["verified_absent"])
        self.assertEqual(entry["disposition"], "deleted")

    def test_retained_and_unverified_copies_are_listed_not_hidden(self):
        self.imp.import_package(self.build())
        sender_inv = self.log.inventory()
        pkg_file = next(e for e in sender_inv if e["copy_id"].endswith("package_file"))
        self.assertIn("retained_plaintext", pkg_file["disposition"])
        store = next(e for e in self.imp.log.inventory() if e["copy_id"].endswith("workspace_records"))
        self.assertIsNone(store["verified_absent"])
        unverified = {e["copy_id"] for e in self.imp.log.inventory() if e["disposition"] == "unverified"}
        self.assertEqual(unverified, {loc for loc, _ in tp.UNVERIFIED_LOCATIONS})

    def test_notice_states_not_encrypted(self):
        pkg = self.build()
        self.assertIn("NOT ENCRYPTED", pkg["notice"])
        self.assertIn(b"synthetic", pkg["files"][f"{CAL}.ndjson"])  # plaintext on purpose

    def test_every_rejection_code_has_a_generic_message(self):
        for code, msg in tp.REJECTION_MESSAGES.items():
            self.assertEqual(str(tp.ImportRejected(code)), msg)


if __name__ == "__main__":
    unittest.main()
