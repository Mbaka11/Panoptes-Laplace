"""Conservative pre-commit guard against real participant data and secrets.

Scans staged content (``--staged``) or all tracked files (``--all``). Output
contains only path, line and rule ID, never a matched value. Exit 1 on findings.
This is a best-effort tripwire, not a guarantee; see tools/precommit-guard.md.
"""
from __future__ import annotations

import argparse
import math
import re
import subprocess
import sys
from pathlib import PurePosixPath

ALLOWLIST_FILE = "tools/precommit-allowlist.txt"
SYNTHETIC_PATHS = ("spikes/fixtures/**", "prototypes/**/data/**", "tests/**")
PRIVATE_DIRS = {"private-data", "participant-data", "exports", "workspaces"}
DATA_EXTS = {".ndjson", ".jsonl", ".csv", ".json", ".gpx", ".kml", ".zip"}
BINARY_DATA_EXTS = {".zip"}
SIGNING_EXTS = {".p12", ".p8", ".mobileprovision", ".cer"}
MAX_DATA_BYTES = 256 * 1024
MARKERS = ("com.example", ".example", "example.com", "example.org", "example.net", "synthetic")
RESERVED_SUFFIXES = (".example", ".test", ".invalid", ".localhost")
RESERVED_DOMAINS = {"example.com", "example.org", "example.net"}

RULES = {
    "PG001": "private key block",
    "PG002": "Apple signing/certificate file",
    "PG003": "API token or secret-like assignment",
    "PG004": ".env file",
    "PG005": "data-like file outside synthetic allowlist (or unverifiable binary)",
    "PG006": "identifiers (email/domain/bundle ID) without a fictitious marker",
    "PG007": "real-looking email, domain or bundle ID in data file",
    "PG008": "data file exceeds size limit",
    "PG009": "file under a private-data directory",
    "PG010": "invalid allowlist entry",
}

_BEGIN = "-----" + "BEGIN"
RE_PRIVKEY = re.compile(_BEGIN + r"[A-Z0-9 ]*PRIVATE KEY")
RE_TOKENS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}"),
]
RE_ASSIGN = re.compile(
    r"(?:key|token|secret|passw(?:or)?d)[\w.-]*[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9_\-+/=.]{20,})",
    re.I,
)
PLACEHOLDERS = ("example", "changeme", "your", "xxxx", "placeholder", "redacted",
                "synthetic", "dummy", "fake")
RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)")
RE_URL_HOST = re.compile(r"\b[a-z][a-z0-9+.-]*://(?:[^/\s\"'@]*@)?([A-Za-z0-9.-]+)", re.I)
RE_BUNDLE = re.compile(
    r"\b((?:com|org|net|io|me|app|ai|ca)\.[a-z0-9-]+(?:\.[a-z0-9-]+)+)\b", re.I)


def entropy(s: str) -> float:
    return -sum(s.count(c) / len(s) * math.log2(s.count(c) / len(s)) for c in set(s))


def glob_to_re(pattern: str) -> re.Pattern:
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile("^" + out + "$")


def matches_any(path: str, patterns) -> bool:
    return any(glob_to_re(p).match(path) for p in patterns)


def load_allowlist(text: str):
    """Return (entries {glob: reason}, findings)."""
    entries, findings = {}, []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        pat, _, reason = line.partition("#")
        pat, reason = pat.strip(), reason.strip()
        if not reason or not re.search(r"[A-Za-z0-9_]", pat):
            findings.append((ALLOWLIST_FILE, n, "PG010"))
        else:
            entries[pat] = reason
    return entries, findings


def is_binary(data: bytes) -> bool:
    return b"\0" in data[:8192]


def scan_file(path: str, data: bytes):
    """Return list of (path, line, rule)."""
    f = []
    p = PurePosixPath(path)
    name, ext = p.name.lower(), p.suffix.lower()
    parts = {x.lower() for x in p.parts[:-1]}

    if parts & PRIVATE_DIRS:
        f.append((path, 0, "PG009"))
    if ext in SIGNING_EXTS:
        f.append((path, 0, "PG002"))
    if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
        f.append((path, 0, "PG004"))

    synthetic = matches_any(path, SYNTHETIC_PATHS)
    low = path.lower()
    health = name in {"export.xml", "export_cda.xml"} or "apple_health_export" in low
    takeout = "takeout" in low
    data_like = ext in DATA_EXTS or health or takeout
    if data_like:
        if not synthetic:
            f.append((path, 0, "PG005"))
        elif ext in BINARY_DATA_EXTS or health or takeout or is_binary(data):
            f.append((path, 0, "PG005"))
        if len(data) > MAX_DATA_BYTES:
            f.append((path, 0, "PG008"))

    if is_binary(data):
        return f
    text = data.decode("utf-8", errors="replace")
    lines = text.splitlines()
    for n, line in enumerate(lines, 1):
        if RE_PRIVKEY.search(line):
            f.append((path, n, "PG001"))
        hit = False
        # Windowed to avoid pathological regex time on huge single-line files.
        for start in range(0, max(len(line), 1), 4000):
            chunk = line[start:start + 4300]
            if any(r.search(chunk) for r in RE_TOKENS):
                hit = True
            for m in RE_ASSIGN.finditer(chunk):
                v = m.group(1)
                if (not any(w in v.lower() for w in PLACEHOLDERS) and entropy(v) >= 3.5
                        and re.search(r"\d", v) and re.search(r"[A-Za-z]", v)):
                    hit = True
            if hit:
                break
        if hit:
            f.append((path, n, "PG003"))

    if data_like and synthetic and ext not in BINARY_DATA_EXTS:
        found = []  # (line, kind, value)
        for n, line in enumerate(lines, 1):
            for m in RE_EMAIL.finditer(line):
                found.append((n, "domain", m.group(1)))
            for m in RE_URL_HOST.finditer(line):
                found.append((n, "domain", m.group(1)))
            for m in RE_BUNDLE.finditer(line):
                found.append((n, "bundle", m.group(1)))
        if found:
            lowtext = text.lower()
            if not any(mk in lowtext for mk in MARKERS):
                f.append((path, found[0][0], "PG006"))
            for n, kind, v in found:
                v = v.lower().rstrip(".")
                if kind == "bundle":
                    ok = v.startswith("com.example.") or v == "com.example"
                else:
                    ok = (v in RESERVED_DOMAINS or v.endswith(RESERVED_SUFFIXES)
                          or any(v.endswith("." + d) for d in RESERVED_DOMAINS))
                if not ok:
                    f.append((path, n, "PG007"))
    return f


def git(args, cwd, check=True):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True)
    if check and r.returncode:
        raise RuntimeError("git %s failed" % " ".join(args))
    return r.stdout


def list_paths(mode, cwd):
    if mode == "staged":
        out = git(["diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"], cwd)
    else:
        out = git(["ls-files", "-z"], cwd)
    return [p.decode("utf-8", "replace") for p in out.split(b"\0") if p]


def run(mode, cwd, stream=sys.stderr):
    """Scan and return the list of findings; logs overrides to stream."""
    al_data = git(["show", ":" + ALLOWLIST_FILE], cwd, check=False)
    entries, findings = load_allowlist(al_data.decode("utf-8", "replace"))
    for path in list_paths(mode, cwd):
        try:
            data = git(["show", ":" + path], cwd)
        except RuntimeError:
            findings.append((path, 0, "PG005"))  # unreadable: fail closed
            continue
        got = scan_file(path, data)
        if not got:
            continue
        pat = next((p for p in entries if glob_to_re(p).match(path)), None)
        if pat:
            print("OVERRIDE %s (%d finding(s) suppressed by allowlist: %s)"
                  % (path, len(got), entries[pat]), file=stream)
        else:
            findings.extend(got)
    return findings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--staged", action="store_true", help="scan staged content")
    g.add_argument("--all", action="store_true", help="scan all tracked files (index content)")
    ap.add_argument("--repo", default=".", help="repository directory (default: current)")
    a = ap.parse_args(argv)
    try:
        findings = run("staged" if a.staged else "all", a.repo)
    except (RuntimeError, OSError) as e:
        print("precommit-guard: cannot scan (%s); failing closed" % e, file=sys.stderr)
        return 1
    uniq = sorted(set(findings))
    for path, line, rule in uniq:
        loc = "%s:%d" % (path, line) if line else path
        print("%s %s: %s" % (rule, loc, RULES[rule]))
    if uniq:
        print("precommit-guard: %d finding(s); commit blocked. No values are printed." % len(uniq),
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
