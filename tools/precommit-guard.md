# Pre-commit guard

A conservative tripwire that blocks real participant data and secrets from being committed. It satisfies the Repository row precondition in `docs/transfer-package-design.md` section 7 (ignore rules plus a pre-commit scan for key and export patterns). `.gitignore` is defense in depth; `git add -f` bypasses it, this guard does not.

Python 3.10+, standard library only. It is a best-effort heuristic, not proof that a commit is clean.

## Use

```bash
python -m tools.precommit_guard --staged   # staged content (what a commit would record)
python -m tools.precommit_guard --all      # all tracked files (index content)
```

Exit 1 on findings, 0 otherwise. Output is `RULE path:line: description` only; matched values are never printed.

## Opt-in hook install

The hook is not installed automatically and this tool never changes git config. To enable it in your clone:

```bash
git config core.hooksPath hooks
```

To disable: `git config --unset core.hooksPath`. `hooks/pre-commit` is a POSIX sh script that works in Git Bash on Windows and on macOS. It fails closed if Python 3.10+ is missing. On macOS/Linux ensure it is executable (`chmod +x hooks/pre-commit`) if git reports it is ignored.

## Rules

| ID | Blocks |
|---|---|
| PG001 | Private key blocks |
| PG002 | `.p12`, `.p8`, `.mobileprovision`, `.cer` files |
| PG003 | `sk-`, GitHub, AWS, Slack, Google-style tokens; high-entropy values assigned to names containing key/token/secret/password (placeholder words are ignored) |
| PG004 | `.env` and `.env.*` (except `.env.example`) |
| PG005 | Data-like files (`.ndjson .jsonl .csv .json .gpx .kml .zip`, Health `export.xml`, Takeout-style paths) outside `spikes/fixtures/**`, `prototypes/**/data/**`, `tests/**`; inside those paths, archives and Health/Takeout files that cannot be inspected |
| PG006 | Allowlisted data file containing emails, URL hosts or bundle IDs but no fictitious marker (`com.example`, `.example`, `example.com/org/net`, `synthetic`) |
| PG007 | Allowlisted data file with a non-reserved email/URL domain or a bundle ID not under `com.example` |
| PG008 | Data file over 256 KiB |
| PG009 | Any file under a `private-data/`, `participant-data/`, `exports/` or `workspaces/` directory |
| PG010 | Malformed override entry (missing reason) |

Secret rules (PG001, PG003) apply to every text file, including docs and tests.

## Overrides

There is no silent bypass and no `--no-verify` convenience flag in this tool. To permit a specific file, add a line to `tools/precommit-allowlist.txt`:

```
path/or/glob  # mandatory reason
```

Entries without a reason, or bare wildcards, are rejected (PG010). Each use is logged to stderr as `OVERRIDE path (...)`. The allowlist is a reviewed, committed file, so every override is visible in history. An override suppresses all rules for that path; keep entries narrow.

## Limitations

- Pattern and entropy heuristics miss unusual formats and flag some benign strings; base64/encoded or encrypted-looking blobs are not decoded.
- Text-only content rules; binary files are judged by name, size and extension only. `.zip` contents are never opened.
- Real data renamed to an allowlisted path with fictitious markers, or with no emails/domains/bundle IDs, passes. Names, locations, and health values are not detected.
- Scans current index content only, not git history; a secret already pushed must be rotated and history rewritten separately.
- `git commit --no-verify` and not enabling the hook bypass it. Consider re-running `--all` in review or CI.
- The data-like extension list is conservative: unrelated `.json` or `.csv` files outside the allowlist (for example a future `package.json`) need a reviewed allowlist entry.
