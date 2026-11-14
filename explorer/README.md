# Local explorer server (D-042, provisional)

A small standard-library Python server that serves the explorer web prototype and a read-only JSON API. It is the first step toward consolidating the explorer. It does not select a production framework, storage engine, or schema.

## Run

From the repository root:

```bash
python -m explorer.server              # http://127.0.0.1:8765/
python -m explorer.server --port 0     # any free port
python -m unittest tests.test_explorer_server -v
```

`/` redirects to `/explorer-cinematic/`. The older concept page is at `/explorer-concept/`. The badge at the top of the page says `server` when its data came from the API, and `static file` when it fell back to the checked-in JSON (for example under `python -m http.server`).

## What it does

At start-up (under a second) it builds each registered workspace **from the spikes**, not from a hand-edited file:

| Key | Builder | Workspace id |
|---|---|---|
| `persona` | `spikes.synthetic_persona.build` (seeded, deterministic) | `ws-demo-01` |
| `fixtures` | `spikes.explorer_export.build_fixture_document` (APR and account-export parsers on bundled fixtures) | `ws-demo-02` |
| `profile-steady`, `profile-doomscroll`, `profile-social_drop`, `profile-search_drift`, `profile-commuter`, `profile-sparse` | `spikes.profiles.build(key)` then `spikes.insights.enrich` (contract 0.2, D-043): every Finding shown is computed by the engine at start-up | `ws-prof-*` |

Each document must pass `explorer_export.validate_contract` and carry `meta.synthetic: true`, and no two workspaces may share a `workspace_id`; otherwise the server refuses to start. Tests check that the served documents equal the checked-in files.

## API (`explorer-api-0.1-provisional`)

| Method and path | Returns |
|---|---|
| `GET /api/health` | status, API version, `synthetic_only: true` |
| `GET /api/workspaces` | one summary per workspace: id, contract version, window, record and type counts, SHA-256 of the served body |
| `GET /api/workspaces/{key}` | the full contract document (`{meta, records}`) |
| `GET /api/workspaces/{key}/summary` | the summary alone |
| `GET /api/workspaces/{key}/metrics` | daily metric series from the insight engine, `{metric: {date: number or "unknown"}}`, plus `metric_sources` `{metric: [record types]}` naming what each computed series is derived from (used by the Loom lens) |
| `GET /api/workspaces/{key}/validation` | `{valid, problems}` from the contract validator |

Anything else is a JSON 404. `POST`, `PUT`, `PATCH`, `DELETE` and `OPTIONS` return 405.

## Boundaries

- Synthetic data only. There is no upload, write endpoint, raw-file argument, or persistence. A real-data path needs its own decision plus the transfer, storage, and deletion gates (D-031, D-032, D-040).
- Binds to loopback only, and rejects requests whose `Host` header is not a loopback name, as a defence against DNS rebinding.
- Static files: only `prototypes/`, only known extensions, no hidden files, and no path traversal.
- Responses send `Cache-Control: no-store`, `nosniff`, `no-referrer`, and a Content Security Policy that keeps `connect-src 'self'`. There is no CORS header.
- The page still loads Three.js from cdnjs and fonts from Google Fonts, as in D-039. Both reveal the viewer's IP address to those hosts. Vendoring them is a later choice.
- Request logs record method, path, and status, never query strings or bodies.
