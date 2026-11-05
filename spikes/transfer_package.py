"""Synthetic spike for XFR-01 / ISO-01 / DEL-01 package LIFECYCLE logic.

!!! NOT ENCRYPTED. NOT A SECURITY DESIGN. !!!
The payload in these packages is PLAINTEXT. The Python standard library has no AEAD,
so HMAC-SHA256 is used ONLY as a stand-in for "authenticated integrity". It is not the
selected ciphersuite (D-031 selects none), provides no confidentiality, and being
symmetric it only imitates sender authentication. Nothing here is a package format,
key-handling design, or storage design. Synthetic, fictitious data only; keys are
generated in memory by the caller and never written anywhere. See transfer-package.md.

Replay policy exercised: R1 (package-ID ledger) + R3 (per-sender monotonic sequence)
from docs/transfer-package-design.md section 6, with ID-only deletion tombstones and
key-based upsert so overlapping packages cannot inflate counts.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import shutil
import tempfile
from datetime import datetime
from typing import Any

NOT_ENCRYPTED_NOTICE = (
    "NOT ENCRYPTED: payload is plaintext; HMAC-SHA256 is a stand-in for authenticated "
    "integrity only; no ciphersuite is selected (D-031)."
)
ALG = "HMAC-SHA256-STANDIN"
SUPPORTED_VERSIONS = (2,)  # version 1 stands for an older/weaker format: downgrade -> reject
_DOMAIN = b"panoptes-synthetic-standin-v2\0"
_FILE_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*\.ndjson$")

# Generic failure classes. Messages never echo record values or which byte differed.
REJECTION_MESSAGES = {
    "malformed": "package is unreadable or malformed",
    "unsupported_version": "unsupported or downgraded format version or algorithm",
    "unknown_sender": "sender is not enrolled for this workspace",
    "integrity_failure": "integrity check failed",
    "wrong_workspace": "package is not for this workspace",
    "wrong_recipient": "package is not for this recipient",
    "file_set_mismatch": "package files do not match the manifest",
    "scope_violation": "package content is outside its declared scope",
    "replay_rejected": "package is older than the last accepted package from this sender",
}


class ImportRejected(Exception):
    """Raised with a generic failure class only."""

    def __init__(self, code: str):
        super().__init__(REJECTION_MESSAGES[code])
        self.code = code


def _canon(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _tag(sender_key: bytes, header: dict, manifest: dict) -> str:
    msg = _DOMAIN + _canon(header) + b"\0" + _canon(manifest)
    return hmac.new(sender_key, msg, hashlib.sha256).hexdigest()


def _ts(value: str) -> datetime:
    return datetime.fromisoformat(value)


# --- DEL-01: staging / plaintext copy inventory ------------------------------------

# Locations this spike cannot observe. Listed so DEL-01 never claims them clean.
UNVERIFIED_LOCATIONS = (
    ("transport_channel", "AirDrop/Files/cable/mail copy of the package"),
    ("files_app_or_downloads", "user-visible copy outside project control"),
    ("device_and_mac_backups", "iPhone backup, Time Machine, cloud backup"),
    ("spotlight_and_indexes", "OS search indexes and thumbnails"),
    ("swap_and_crash_reports", "swap files, crash reports, logs outside this process"),
    ("recipient_derived_copies", "screenshots, notes, exports made by a recipient"),
)


class StagingLog:
    """Records each plaintext/staging copy this spike creates and its disposition."""

    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    def record(self, copy_id: str, location_class: str, phase: str, disposition: str,
               verified_absent: bool | None) -> None:
        self.entries.append({
            "copy_id": copy_id, "location_class": location_class, "phase": phase,
            "disposition": disposition, "verified_absent": verified_absent,
        })

    def inventory(self) -> list[dict[str, Any]]:
        out = [dict(e) for e in self.entries]
        for loc, _desc in UNVERIFIED_LOCATIONS:
            out.append({"copy_id": loc, "location_class": loc, "phase": "not_observed",
                        "disposition": "unverified", "verified_absent": None})
        return out


class _Staged:
    """Temporary directory that is removed (and checked) on success AND failure."""

    def __init__(self, log: StagingLog | None, copy_id: str, location_class: str, phase: str):
        self.log, self.copy_id, self.location_class, self.phase = log, copy_id, location_class, phase
        self.path = ""

    def __enter__(self) -> str:
        self.path = tempfile.mkdtemp(prefix="synthetic-xfr-")
        return self.path

    def __exit__(self, *exc: Any) -> bool:
        shutil.rmtree(self.path, ignore_errors=True)
        if self.log is not None:
            self.log.record(self.copy_id, self.location_class, self.phase, "deleted",
                            not os.path.exists(self.path))
        return False


# --- Sender side -----------------------------------------------------------------

def select_records(records: list[dict], sources: list[str], date_from: str, date_to: str) -> list[dict]:
    """Selected sources only; dates inclusive of date_from, exclusive of date_to."""
    lo, hi = _ts(date_from), _ts(date_to)
    return [r for r in records if r["source"] in sources and lo <= _ts(r["ts"]) < hi]


def build_package(records: list[dict], *, sender_id: str, sender_key: bytes, recipient_id: str,
                  workspace_id: str, package_id: str, sequence: int, sources: list[str],
                  date_from: str, date_to: str, format_version: int = 2,
                  log: StagingLog | None = None) -> dict[str, Any]:
    """Build an UNENCRYPTED, HMAC-tagged package containing only the selected scope."""
    selected = select_records(records, sources, date_from, date_to)
    files: dict[str, bytes] = {}
    # The plaintext NDJSON exists on disk here, exactly the staging risk of design sec. 7.
    with _Staged(log, f"{package_id}:sender_plaintext_export", "sender_temp_dir", "build") as d:
        for source in sorted(set(sources)):
            name = f"{source}.ndjson"
            body = b"".join(_canon(r) + b"\n" for r in selected if r["source"] == source)
            with open(os.path.join(d, name), "wb") as fh:
                fh.write(body)
        for name in sorted(os.listdir(d)):
            with open(os.path.join(d, name), "rb") as fh:
                files[name] = fh.read()
    if log is not None:
        log.record(f"{package_id}:package_file", "transport_or_participant_storage", "build",
                   "retained_plaintext_until_participant_deletes", None)
    manifest = {
        "format_version": format_version, "package_id": package_id, "sender_id": sender_id,
        "recipient_id": recipient_id, "workspace_id": workspace_id, "sequence": sequence,
        "scope": {"sources": sorted(set(sources)), "date_from": date_from, "date_to": date_to,
                  "boundaries": "from inclusive, to exclusive"},
        "files": [{"name": n, "sha256": _sha256(b), "size": len(b)} for n, b in sorted(files.items())],
    }
    header = {"format_version": format_version, "alg": ALG, "package_id": package_id,
              "sender_id": sender_id}
    return {"header": header, "manifest": manifest, "files": files,
            "tag": _tag(sender_key, header, manifest), "notice": NOT_ENCRYPTED_NOTICE}


# --- Receiver side ---------------------------------------------------------------

class Importer:
    """One workspace + one recipient identity. Validates fully, then commits atomically."""

    def __init__(self, workspace_id: str, recipient_id: str, enrolled_senders: dict[str, bytes]):
        self.workspace_id, self.recipient_id = workspace_id, recipient_id
        self._senders = dict(enrolled_senders)  # sender_id -> key (stand-in for enrolled public key)
        self.records: dict[tuple[str, str], dict] = {}
        self.tombstones: set[tuple[str, str]] = set()  # IDs only, no values
        self.package_ledger: set[str] = set()  # R1
        self.last_sequence: dict[str, int] = {}  # R3
        self.audit: list[str] = []  # value-free audit text
        self.log = StagingLog()

    def delete_record(self, source: str, record_id: str) -> None:
        self.records.pop((source, record_id), None)
        self.tombstones.add((source, record_id))
        self.audit.append("record_deleted")

    def import_package(self, package: dict[str, Any]) -> dict[str, Any]:
        try:
            result = self._import(package)
        except ImportRejected as exc:
            self.audit.append(f"rejected:{exc.code}")
            raise
        except (KeyError, TypeError, ValueError, AttributeError, UnicodeDecodeError):
            self.audit.append("rejected:malformed")
            raise ImportRejected("malformed") from None
        self.audit.append(f"{result['status']}:{result['package_id']}")
        return result

    def _import(self, package: dict[str, Any]) -> dict[str, Any]:
        header, manifest, files, tag = package["header"], package["manifest"], package["files"], package["tag"]
        # 1. Version/algorithm first: unknown or downgraded formats are never "repaired".
        if (header["format_version"] not in SUPPORTED_VERSIONS or header["alg"] != ALG
                or manifest["format_version"] not in SUPPORTED_VERSIONS):
            raise ImportRejected("unsupported_version")
        # 2. Sender must be enrolled (selects the verification key).
        key = self._senders.get(header["sender_id"])
        if key is None:
            raise ImportRejected("unknown_sender")
        # 3. Authenticated integrity over header + manifest (recomputing a bare hash is not enough).
        if not hmac.compare_digest(tag, _tag(key, header, manifest)):
            raise ImportRejected("integrity_failure")
        # 4. Authenticated context must agree with itself and with this importer.
        if (header["package_id"] != manifest["package_id"] or header["sender_id"] != manifest["sender_id"]
                or header["format_version"] != manifest["format_version"]):
            raise ImportRejected("integrity_failure")
        if manifest["workspace_id"] != self.workspace_id:
            raise ImportRejected("wrong_workspace")
        if manifest["recipient_id"] != self.recipient_id:
            raise ImportRejected("wrong_recipient")
        # 5. Exact file set, then per-file digests (payload tamper detection).
        listed = {f["name"]: f for f in manifest["files"]}
        if len(listed) != len(manifest["files"]) or set(listed) != set(files):
            raise ImportRejected("file_set_mismatch")
        for name in listed:
            if not _FILE_RE.match(name):
                raise ImportRejected("malformed")
        # 6. Materialize in an isolated temp dir, validate, parse; always removed.
        parsed: list[dict] = []
        with _Staged(self.log, f"{manifest['package_id']}:validation_temp", "mac_temp_dir", "import") as d:
            for name, data in files.items():
                if not isinstance(data, bytes):
                    raise ImportRejected("malformed")
                with open(os.path.join(d, name), "wb") as fh:
                    fh.write(data)
            for name, meta in listed.items():
                with open(os.path.join(d, name), "rb") as fh:
                    data = fh.read()
                if _sha256(data) != meta["sha256"] or len(data) != meta["size"]:
                    raise ImportRejected("integrity_failure")
                for line in data.splitlines():
                    parsed.append(json.loads(line.decode("utf-8")))
        scope = manifest["scope"]
        lo, hi = _ts(scope["date_from"]), _ts(scope["date_to"])
        for r in parsed:
            if r["source"] not in scope["sources"] or not (lo <= _ts(r["ts"]) < hi):
                raise ImportRejected("scope_violation")
        # 7. Replay / idempotency policy: R1 then R3 (after authentication, before commit).
        pid, sender, seq = manifest["package_id"], manifest["sender_id"], manifest["sequence"]
        if pid in self.package_ledger:
            return {"status": "duplicate", "package_id": pid, "new": 0, "unchanged": 0,
                    "changed": 0, "skipped_tombstoned": 0}
        if not isinstance(seq, int) or seq <= self.last_sequence.get(sender, 0):
            raise ImportRejected("replay_rejected")
        # 8. Commit: key-based upsert (no inflation), tombstones respected.
        counts = {"new": 0, "unchanged": 0, "changed": 0, "skipped_tombstoned": 0}
        for r in parsed:
            k = (r["source"], r["id"])
            if k in self.tombstones:
                counts["skipped_tombstoned"] += 1
            elif k not in self.records:
                self.records[k] = r
                counts["new"] += 1
            elif self.records[k] == r:
                counts["unchanged"] += 1
            else:
                self.records[k] = r
                counts["changed"] += 1
        self.package_ledger.add(pid)
        self.last_sequence[sender] = seq
        self.log.record(f"{pid}:workspace_records", "mac_workspace_store", "import",
                        "retained_by_design_pending_deletion_policy", None)
        return {"status": "imported", "package_id": pid, **counts}


def _demo() -> None:
    import secrets
    print(NOT_ENCRYPTED_NOTICE)
    key = secrets.token_bytes(32)  # generated in memory, never written
    records = [
        {"source": "com.example.calendar", "id": "e1", "ts": "2026-01-05T09:00:00+00:00", "value": "synthetic-1"},
        {"source": "com.example.calendar", "id": "e2", "ts": "2026-02-05T09:00:00+00:00", "value": "synthetic-2"},
        {"source": "com.example.steps", "id": "s1", "ts": "2026-01-06T09:00:00+00:00", "value": "synthetic-3"},
    ]
    pkg = build_package(records, sender_id="phone.example", sender_key=key, recipient_id="mac.example",
                        workspace_id="ws.example.a", package_id="pkg-1", sequence=1,
                        sources=["com.example.calendar"], date_from="2026-01-01T00:00:00+00:00",
                        date_to="2026-02-01T00:00:00+00:00")
    imp = Importer("ws.example.a", "mac.example", {"phone.example": key})
    print("first import:", imp.import_package(pkg))
    print("second import:", imp.import_package(pkg))
    print("staging inventory:")
    for e in imp.log.inventory():
        print("  ", e)


if __name__ == "__main__":
    import sys
    if "--demo" in sys.argv:
        _demo()
    else:
        print(NOT_ENCRYPTED_NOTICE)
        print("usage: python -m spikes.transfer_package --demo")
