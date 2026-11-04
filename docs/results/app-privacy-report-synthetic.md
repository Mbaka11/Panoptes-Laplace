# App Privacy Report synthetic inspection result

## Execution scope

- **Date:** 2026-10-05; coverage follow-up verified at `2026-10-05T16:37:32-04:00` (local clock, not independently witnessed).
- **Case:** APR-02, documented subset only; relevant synthetic semantics from SYN-01 through SYN-06.
- **Environment observed:** Windows / Git Bash, Python 3.10.11.
- **Execution:** completed for the synthetic inspector, bundled demo, and opt-in source-coverage report.
- **Outcome:** 61 unit tests passed (40 original plus 21 coverage/regression tests); both CLI modes completed with expected warnings and exit code 0; Python bytecode compilation passed. The original 40-test baseline was rerun successfully before this extension.
- **Capability conclusion:** synthetic parser semantics observed within the limits below. Actual iPhone export compatibility remains unknown.
- **Method version:** uncommitted working-tree spike, identified by the source/test fingerprints below. This is not a production schema version.
- **Evidence class:** synthetic test execution, not simulator or physical-device evidence.
- **Participant data, credentials, devices, and external services used by the spike:** none.

## Reproduce

From the repository root:

```bash
python -m unittest discover -s tests -v
python -m spikes.app_privacy_report --demo
python -m spikes.app_privacy_report --demo --coverage
python -m compileall -q spikes tests
```

The implementation and limitations are described in [the spike guide](../../spikes/app-privacy-report.md).

## Observed results

| Observation | Result |
|---|---|
| Test run | 61 tests, all passed |
| Demo inputs | Two synthetic snapshots plus a repeated copy of the first |
| Distinct snapshot artifacts | Two |
| Duplicate reporting | Input 3 references identical input 1 |
| Snapshot A | Four supported-subset records; one complete interval, one missing-end interval, one network aggregate |
| Snapshot B | Two supported-subset records; one missing-begin interval, one network aggregate |
| Complete interval | 600 seconds, traceable to snapshot A lines 1 and 2 |
| Incomplete boundaries across files | Kept separate; no cross-snapshot duration invented |
| Network values inspected by tests | Five and eight hits retained in separate source records; no combined total or inferred delta |
| Expected demo warnings | Unknown field preserved; incomplete intervals |
| Summary disclosure | Default summary still omits timestamps, source domains/identifiers, and content hashes; opt-in coverage includes timestamps/durations but not source identifiers, raw lines, or hashes |
| Coverage provenance | Every reported timestamp extremum retains source-line/field references; ties preserve all references; interleaved duplicate inputs retain original positions |
| Unknown capability dimensions | Device support, provisioning, authorization, real source-export success, full collection windows, and missing periods remain explicitly untested/not observed/unknown |
| Timestamp boundary regression | Instants that overflow Python's UTC year range are diagnosed without inventing a replacement time; supported extreme-year values remain inspectable |
| Duplicate comparison regression | Distinct bytes survive even when the test forces identical digest outputs; actual artifact equality is checked directly |
| CLI repeatability | Both modes produced identical JSON on repeated subprocess runs; `--coverage` without `--demo` returned usage exit code 2 |
| Network and file behavior | Both modes completed with socket creation blocked by unit tests; coverage CLI file-open checks observed only the two fixture reads in `rb` mode |
| Repository hygiene | Ignore checks matched private-data/export paths, example secret/signing names, and Python cache paths; synthetic fixtures remain trackable |

The source files are hand-authored examples, not genuine iPhone exports. No claim is made about all Apple record variants, the full collection window, or the participant's actual activity. The fake five/eight counts are not evidence of any real traffic.

### Coverage report observations

The opt-in report is versioned `synthetic-coverage-v1`; this is an experimental presentation format, not a production event/report schema. For the unchanged bundled fixtures:

| Distinct artifact / first input | Supported access-boundary records | Latest supported access timestamp | Supported network-aggregate records | Latest supported contact timestamp |
|---|---|---|---|---|
| Snapshot 1 / input 1 | 3 | `2026-01-02T09:00:00Z`, line 3 `timeStamp` | 1 | `2026-01-02T09:00:00Z`, line 4 `timeStamp` |
| Snapshot 2 / input 2 | 1 | `2026-01-02T09:05:00Z`, line 1 `timeStamp` | 1 | `2026-01-03T09:00:00Z`, line 2 `timeStamp` |

Input 3 repeats input 1 and creates no additional artifact. Counts describe source records, not independent user actions or unique requests. The interval durations remain 600 seconds for the complete pair and unknown for both incomplete fragments. Contact/access extrema are not collection-window endpoints or freshness measurements. No multi-domain coverage target has been satisfied by splitting this one source into access and network fields.

Additional synthetic cases distinguish blank files from invalid/unsupported-only files, exclude invalid/unknown records from extrema, retain tied timestamp references, compare offsets by instant, preserve zero/large aggregate counts without expanding hits, and confirm report generation does not mutate source records. Reporting the absence of supported records does not infer denial, lack of real activity, or successful import of the complete source schema.

## Coverage limits and outstanding tests

- Same-call byte-identical artifact detection is **not** persistent import idempotency.
- This tool has no participant-workspace model; it establishes **no** logical or cryptographic isolation guarantee.
- Source validation is deliberately partial. Unknown fields/types and unsupported precision remain visible; the real exporter must still be checked.
- No encrypted transfer, storage design, source deletion propagation, researcher access control, real-data import, or iOS build has been implemented or tested here.
- SYN-07 through SYN-10 and the native/device cases remain pending. APR-01 remains pending. Do not mark the entire collection lab complete.
- Neither reduced diagnostics nor detailed coverage is a formal de-identification guarantee. The opt-in report deliberately reveals source timestamps/durations; in-memory record objects still retain all supplied synthetic values.
- The CLI only reads bundled fixtures. There is no raw participant-file argument or background collection process.

## Evidence fingerprints

SHA-256 of the files as tested in this working tree. Byte-identical reruns can use these to identify the experiment; a hash does not establish an independently witnessed execution time, authorization, or data authenticity. Line-ending changes in later checkouts may change file hashes.

| File | SHA-256 |
|---|---|
| `spikes/app_privacy_report.py` | `ffc296e2c9398b9e16fee6731bc442ec93849e864e93fba93b0c62c38a92e119` |
| `tests/test_app_privacy_report.py` | `34e31150081a0073931f838d6b6ce3e339efe6d9956c3e5d807979295a61957f` |
| `spikes/fixtures/app_privacy_report/snapshot-a.ndjson` | `48d39964a27bb888bc477b974e4baef49963bbbc8c317408d20871c17d5fdaa7` |
| `spikes/fixtures/app_privacy_report/snapshot-b.ndjson` | `51c8c3bfee70a2b41f8e5d2b98bcd82cffa2d455389f362dbd97dca482cf857e` |

## Cleanup and next evidence

No real-data copies were created. The inspector writes no raw-data output; stdout contains the synthetic diagnostic summary or the explicitly requested coverage report. Python's generated bytecode caches are ignored. The checked-in fixture candidates remain as reproducible synthetic examples; no commit was made in this session.

Next evidence requires a source-specific, participant-controlled export inspection under the separately selected [real-data protections](../collection-probe.md#real-data-gate--separate-from-the-build-gate). Mac preflight still gates native scaffolding. This result changes implementation status, not the product's platform constraints or trust requirements.
