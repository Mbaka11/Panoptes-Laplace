"""Local explorer server (provisional, synthetic workspaces only).

Serves the explorer web prototype and a small read-only JSON API. Workspaces are
built in memory from the existing spikes at start-up, validated with
``spikes.explorer_export.validate_contract``, and refused unless
``meta.synthetic`` is true. There is no upload, no write endpoint, no raw-file
argument, and no persistence. Binding is restricted to loopback, and requests
whose Host header is not a loopback name are rejected (DNS-rebinding defence).

This is not a production server or schema (D-042). Standard library only.

    python -m explorer.server            # http://127.0.0.1:8765/
    python -m explorer.server --port 0   # any free port
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import sys
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import unquote, urlsplit

from spikes import explorer_export, insights, profiles, synthetic_persona

API_VERSION = "explorer-api-0.1-provisional"
REPO = Path(__file__).resolve().parent.parent
PROTOTYPES = REPO / "prototypes"
DEFAULT_APP = "explorer-cinematic"
LOOPBACK_NAMES = {"localhost", "127.0.0.1", "::1", "[::1]"}

# Only files with these extensions are served; anything else is a 404.
STATIC_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".md": "text/plain; charset=utf-8",
}

# The page loads Three.js from cdnjs and fonts from Google Fonts (D-039 prototype
# conveniences; both reveal the viewer's IP to those hosts) and uses inline script/style. connect-src stays 'self': the page may only talk to this server.
CSP = (
    "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data:; connect-src 'self'; "
    "object-src 'none'; base-uri 'none'; frame-ancestors 'self'; form-action 'none'"
)


class WorkspaceRefused(ValueError):
    """A workspace document failed validation or is not marked synthetic."""


@dataclass(frozen=True)
class Workspace:
    key: str
    label: str
    origin: str
    document: dict[str, Any]
    body: bytes
    sha256: str

    def summary(self) -> dict[str, Any]:
        meta = self.document["meta"]
        return {
            "key": self.key,
            "label": self.label,
            "origin": self.origin,
            "workspace_id": meta.get("workspace_id"),
            "contract_version": meta.get("contract_version"),
            "synthetic": meta.get("synthetic"),
            "window": meta.get("window"),
            "record_count": len(self.document["records"]),
            "type_counts": meta.get("type_counts"),
            "sha256": self.sha256,
        }


# Registry: key -> (label, origin description, builder). Builders are the spikes
# themselves, so the API serves what the pipeline produces, not a hand-edited file.
BUILDERS: dict[str, tuple[str, str, Callable[[], dict[str, Any]]]] = {
    "persona": (
        "EX-01 persona",
        "spikes.synthetic_persona.build (seeded, deterministic)",
        synthetic_persona.build,
    ),
    "fixtures": (
        "Fixture export",
        "spikes.explorer_export.build_fixture_document (parser spikes on bundled fixtures)",
        explorer_export.build_fixture_document,
    ),
}


def _profile_builder(key: str) -> Callable[[], dict[str, Any]]:
    return lambda: insights.enrich(profiles.build(key))


# Contract 0.2 profiles (D-043): generator plus insight engine, so every finding shown is computed.
for _key in profiles.PROFILES:
    BUILDERS[f"profile-{_key}"] = (
        f"Profile · {_key.replace('_', ' ')}",
        f"spikes.profiles.build('{_key}') + spikes.insights.enrich",
        _profile_builder(_key),
    )


def make_workspace(key: str, label: str, origin: str, document: dict[str, Any]) -> Workspace:
    problems = explorer_export.validate_contract(document)
    if problems:
        raise WorkspaceRefused(f"{key}: {len(problems)} contract problem(s): {problems[:5]}")
    if document.get("meta", {}).get("synthetic") is not True:
        raise WorkspaceRefused(f"{key}: meta.synthetic is not true; this server serves synthetic data only")
    body = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return Workspace(key, label, origin, document, body, hashlib.sha256(body).hexdigest())


def load_workspaces(builders: dict[str, tuple[str, str, Callable[[], dict[str, Any]]]] | None = None) -> dict[str, Workspace]:
    out: dict[str, Workspace] = {}
    for key, (label, origin, build) in (builders or BUILDERS).items():
        out[key] = make_workspace(key, label, origin, build())
    ids = [w.document["meta"]["workspace_id"] for w in out.values()]
    if len(ids) != len(set(ids)):
        raise WorkspaceRefused("two registered workspaces share a workspace_id; workspaces must stay isolated")
    return out


def is_loopback_host(value: str) -> bool:
    try:
        return ipaddress.ip_address(value.strip("[]")).is_loopback
    except ValueError:
        return value.lower() == "localhost"


def host_header_ok(header: str | None) -> bool:
    if not header:
        return False
    host = header.strip()
    if host.startswith("["):  # [::1]:8765
        name = host[: host.find("]") + 1] if "]" in host else host
    else:
        name = host.rsplit(":", 1)[0] if host.count(":") == 1 else host
    return name.lower() in LOOPBACK_NAMES


def resolve_static(root: Path, url_path: str) -> Path | None:
    """Map a URL path to a file under ``root``; None when outside, hidden or not allowed."""
    rel = unquote(url_path).lstrip("/")
    if not rel or rel.endswith("/"):
        rel += "index.html"
    parts = Path(rel).parts
    if any(p in ("..", "") or p.startswith(".") for p in parts):
        return None
    target = (root / rel).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return None
    if target.suffix.lower() not in STATIC_TYPES or not target.is_file():
        return None
    return target


class ExplorerHandler(BaseHTTPRequestHandler):
    server_version = "PanoptesExplorer/0.1"
    sys_version = ""
    workspaces: dict[str, Workspace] = {}
    static_root: Path = PROTOTYPES
    app: str = DEFAULT_APP
    quiet: bool = False

    # -- plumbing ---------------------------------------------------------
    def log_message(self, fmt: str, *args: Any) -> None:  # never log query strings or bodies
        if not self.quiet:
            sys.stderr.write(f"{self.command} {urlsplit(self.path).path} -> {args[1] if len(args) > 1 else ''}\n")

    def _headers(self, status: int, ctype: str, length: int, extra: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Content-Security-Policy", CSP)
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()

    def _send(self, status: int, body: bytes, ctype: str, extra: dict[str, str] | None = None) -> None:
        self._headers(status, ctype, len(body), extra)
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, status: int, payload: Any) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), STATIC_TYPES[".json"])

    def _error(self, status: HTTPStatus, code: str) -> None:
        self._json(status, {"error": code, "status": int(status)})

    # -- methods ----------------------------------------------------------
    def do_GET(self) -> None:
        if not host_header_ok(self.headers.get("Host")):
            return self._error(HTTPStatus.MISDIRECTED_REQUEST, "host_not_loopback")
        path = urlsplit(self.path).path
        if path == "/":
            return self._send(HTTPStatus.FOUND, b"", "text/plain", {"Location": f"/{self.app}/"})
        if path.startswith("/api/"):
            return self._api(path)
        target = resolve_static(self.static_root, path)
        if target is None:
            return self._error(HTTPStatus.NOT_FOUND, "not_found")
        self._send(HTTPStatus.OK, target.read_bytes(), STATIC_TYPES[target.suffix.lower()])

    do_HEAD = do_GET

    def _reject(self) -> None:
        self._send(HTTPStatus.METHOD_NOT_ALLOWED, b'{"error":"read_only"}', STATIC_TYPES[".json"], {"Allow": "GET, HEAD"})

    do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = _reject

    def _api(self, path: str) -> None:
        parts = [p for p in path.split("/") if p][1:]  # drop "api"
        if parts == ["health"]:
            return self._json(HTTPStatus.OK, {"status": "ok", "api_version": API_VERSION, "synthetic_only": True})
        if parts == ["workspaces"]:
            return self._json(HTTPStatus.OK, {
                "api_version": API_VERSION,
                "workspaces": [w.summary() for w in self.workspaces.values()],
            })
        if len(parts) in (2, 3) and parts[0] == "workspaces":
            ws = self.workspaces.get(parts[1])
            if ws is None:
                return self._error(HTTPStatus.NOT_FOUND, "unknown_workspace")
            if len(parts) == 2:
                return self._send(HTTPStatus.OK, ws.body, STATIC_TYPES[".json"], {"ETag": f'"{ws.sha256}"'})
            if parts[2] == "summary":
                return self._json(HTTPStatus.OK, ws.summary())
            if parts[2] == "metrics":
                # Daily metrics as computed by the insight engine; "unknown" stays a string, never 0.
                return self._json(HTTPStatus.OK, {"workspace": ws.key, "engine": insights.ENGINE, "version": insights.VERSION,
                                                  "metrics": insights.daily_metrics(ws.document)})
            if parts[2] == "validation":
                problems = explorer_export.validate_contract(ws.document)
                return self._json(HTTPStatus.OK, {"workspace": ws.key, "valid": not problems, "problems": problems})
        self._error(HTTPStatus.NOT_FOUND, "unknown_endpoint")


def make_server(host: str = "127.0.0.1", port: int = 8765, *, workspaces: dict[str, Workspace] | None = None,
                quiet: bool = False) -> ThreadingHTTPServer:
    if not is_loopback_host(host):
        raise ValueError("the explorer server only binds to a loopback address")
    handler = type("BoundExplorerHandler", (ExplorerHandler,), {
        "workspaces": workspaces if workspaces is not None else load_workspaces(),
        "quiet": quiet,
    })
    server_cls = ThreadingHTTPServer
    if ":" in host:
        import socket
        server_cls = type("V6Server", (ThreadingHTTPServer,), {"address_family": socket.AF_INET6})
    return server_cls((host, port), handler)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Serve the synthetic explorer locally (read-only).")
    ap.add_argument("--host", default="127.0.0.1", help="loopback address only (default 127.0.0.1)")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    try:
        server = make_server(args.host, args.port, quiet=args.quiet)
    except (ValueError, WorkspaceRefused) as exc:
        print(f"explorer: {exc}", file=sys.stderr)
        return 2
    host, port = server.server_address[:2]
    shown = f"[{host}]" if ":" in str(host) else host
    print(f"Panoptes explorer (synthetic only): http://{shown}:{port}/  - Ctrl+C to stop")
    for ws in server.RequestHandlerClass.workspaces.values():
        print(f"  {ws.key:9} {ws.summary()['record_count']:4} records  {ws.document['meta']['workspace_id']}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
