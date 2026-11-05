# Explorer UI concept (provisional)

**Status:** design exploration only. This document selects no UI framework, no Mac UI technology, and no schema, and it does not start explorer implementation. Mac UI frameworks remain deferred (see [architecture](architecture.md) and [D-010](decisions.md)). All data shown in this document is synthetic. Object names such as `Visit` or `ResourceAccess` are conceptual labels from [the ontology](ontology.md), not a production schema.

## 1. Brief and constraints

The owner wants the local Panoptes explorer to feel very futuristic: a spy / James Bond / FBI / CSI operations room. Two references inform this:

1. **Palantir Foundry, for concepts only.** Borrowed: an ontology-backed object explorer, object dossiers, a link graph, a timeline, a map, an investigation workspace, and actions. [D-022](decisions.md) forbids copying proprietary visual identity, typography, iconography, or screenshots, so none of those are used here. See also [branding](branding.md).
2. **bilawalsidhu/gods-eye-view (MIT).** Studied for interaction ideas only: full-screen globe with a tactical HUD, glass side panels for data layers, sensor-style visual modes switched by number keys, a click-to-open telemetry card, fading trails behind tracked targets, a short intelligence-style AI readout of the current view, and shareable view links. No code or assets are assumed to be reused; any later reuse needs its own license review.

**Explicitly rejected from that reference:** its nonparticipant layers (CCTV, ALPR, other people's flights or vehicles). Panoptes shows only the consenting participant's own data, per [trust and governance](trust-and-data-governance.md) and the non-negotiable boundary against analysis of nonparticipants. Third parties who appear inside the participant's own records (a contact name in a calendar event, for example) are handled under the governance document's third-party rules and are not turned into tracked targets.

**Tone** follows [branding](branding.md): powerful, technical, slightly unsettling, never covert. The contrast is the message: the surveillance aesthetic is in service of the person being observed, and the UI says so on every screen.

## 2. Design principles

1. **Spectacle must never fake certainty.** Glow, motion, and drama are allowed only where they encode something true. Decoration that implies precision, liveness, or confidence the data lacks is a defect, not a style choice.
2. **Five epistemic classes are always visually distinct** ([ontology](ontology.md): observation is not inference):

   | Class | Meaning | Visual rule (see section 3) |
   |---|---|---|
   | Observation | raw source record | solid outline, source-colored tick, mono text |
   | Normalized event | canonical record after parsing | solid fill, square corner marker |
   | Hypothesis | candidate pattern, untested | dashed outline, no glow |
   | Inference | tested, method + version + uncertainty attached | double outline, uncertainty band always drawn |
   | Prediction | future-facing, optionally locked | hatched fill, "FORECAST" tag, future-tinted |

   A user must be able to tell the class of any visible mark without reading a tooltip.
3. **Aggregates are not events.** Interval, point, and windowed-aggregate glyphs differ in shape, not just color. An App Privacy Report domain-contact total keeps its window and is never drawn as a dot at a time ([ontology: preserve source granularity](ontology.md)).
4. **Unknown is not zero.** "No data" is rendered as a distinct pattern (see 3.5), never as an empty lane, a zero-height bar, or a cold color. A HealthKit read with no results is not drawn as denial, and a denied permission is never inferred from emptiness.
5. **Missing periods are visible.** Every time axis shows gaps in coverage in-line. Charts that would hide gaps by interpolation must either break the line or display the interpolation as hypothesis-class.
6. **Provenance is one gesture away.** Every mark opens a chain back to its source record, method, and version in at most two actions.
7. **Effects are opt-in in analysis views.** The dramatic layer (CRT, scanlines, glow, parallax) belongs to the Ops map and briefing "show" surfaces. Timeline, Dossier, Investigation, and Coverage default to flat, high-legibility rendering (section 8).
8. **Correlation is drawn as correlation.** No arrow semantics implying causation unless a method explicitly supports it, and then it is labeled with that method.
9. **The participant is the operator.** Pause, scope, export, and delete are always reachable (global shortcut and persistent control), never buried.
10. **Null results are first-class.** An investigation that finds nothing gets a finished-looking, well-designed result card ([D-025](decisions.md)).

## 3. Original visual language

### 3.1 Working name and concept

Working visual concept: **"Argus Desk"** (internal, not a product name; checked for collisions only against the exclusions in [branding](branding.md), not cleared). A dim operations room where many small "eyes" (sources) converge into one picture. Motif: a lattice of small apertures (one per source) around a central field, instead of any single eye logo. Logo work remains deferred.

### 3.2 Palette tokens (provisional)

Named semantically, not by hue alone, so that modes and themes can re-map values without redefining meaning. Values are starting points for look-and-feel testing.

| Token | Role | Starting value |
|---|---|---|
| `--bg-void` | app background | `#070A0F` |
| `--bg-panel` | glass panel base (alpha 0.62) | `#0E141C` |
| `--line-faint` | grids, dividers | `#1E2A38` |
| `--line-strong` | panel borders | `#33475E` |
| `--text-primary` | body text | `#D7E2EE` |
| `--text-muted` | labels | `#7F93A8` |
| `--accent-participant` | the participant's own data, primary accent | `#3EE0C4` (cold teal) |
| `--cls-observation` | observation class | `#9FB4C8` |
| `--cls-event` | normalized event | `#5CA8FF` |
| `--cls-hypothesis` | hypothesis | `#E6B84C` |
| `--cls-inference` | inference | `#B58CFF` |
| `--cls-prediction` | prediction | `#FF7AB0` |
| `--state-unknown` | missing/unknown pattern | `#566170` over diagonal hatch |
| `--state-alert` | destructive/irreversible actions | `#FF5A4D` |
| `--state-ok` | verified | `#6BE39A` |
| `--consent-band` | classification banner | `#12303A` bg / `#3EE0C4` text |

Rules: no class color is used for anything else; no single red-green pair carries meaning (color is always paired with shape or label); amber and magenta are reserved for hypothesis and prediction so that "glowing" never defaults to "important".

### 3.3 Typography

- **Data / HUD:** a monospaced or tabular-figure face for timestamps, counts, and IDs (framework-neutral; selection deferred, open-licensed faces preferred such as IBM Plex Mono or JetBrains Mono, both SIL OFL).
- **Narrative / labels:** a neutral humanist or grotesque sans (for example Inter, SIL OFL).
- **Headings:** the same sans, uppercase, wide letter-spacing, small size. No condensed military stencil face.
- Tabular numerals everywhere numbers are compared. Minimum 12 px equivalent for any data text; 11 px caps only for non-essential tags.

### 3.4 HUD grammar

- **Corner brackets** (not full borders) frame focus regions; a bracket's style encodes epistemic class (solid / dashed / double / hatched).
- **Tick rulers** on timeline and map edges show scale and window; the window start/end are always printed.
- **Reticle** marks the selected object; it never "locks on" with animation implying surveillance of someone else. The reticle label reads the object's type and class, for example `PLACE · INFERENCE`.
- **Telemetry cards** (click-to-open, analogous to the reference) show: type, class, source(s), time or window, quality (sensor accuracy shown as accuracy, not as probability), method/version if derived, and actions (inspect provenance, correct, hide from view, delete).
- **Status strip** (bottom): workspace name, current lens, time window, record counts in view, and a "stale/last refresh" stamp so live-looking data is never ambiguous.
- **Glass panels** use blur and low-alpha fill but keep a contrast-safe solid fallback; text never sits on busy imagery without a backing plate.

### 3.5 Pattern vocabulary (shape, not just color)

| Meaning | Glyph / pattern |
|---|---|
| Point observation | small filled circle |
| Interval / session | horizontal bar with end caps (open cap if end is unknown) |
| Windowed aggregate | wide low bar with a sawtooth top edge and the window length printed |
| Daily aggregate (e.g. step count) | flat block spanning the day, labeled `AGG` |
| Derived/inferred span | bar with double outline |
| Predicted span | hatched bar with `FORECAST` tag |
| Unknown / not collected | diagonal hatch in `--state-unknown` plus label "NO DATA" |
| Known zero | an explicit baseline tick with "0 (recorded)" |
| Source permission off | striped lane with a lock mark, "PAUSED BY PARTICIPANT" |
| Overlap/duplicate import | collapsed with `x2 imports` badge (counted once) |

### 3.6 Motion

- Motion encodes change in data or participant action, not ambient decoration. Examples: a trail fades with age to show recency; a panel slides to confirm a mode change; a pulse appears only on newly imported records.
- Ambient effects (scanline drift, glow breathing, radar sweep) are limited to the Ops map and the optional "show" mode, are off in analysis views, and obey reduced-motion settings.
- Durations 120-240 ms for UI, up to 600 ms for mode transitions. No motion loops faster than 3 Hz. Nothing flashes.
- Fading trails encode age only; trail brightness is never used to imply confidence.

### 3.7 Classification banner (pastiche)

A fixed top strip borrows the form of a classification marking and replaces secrecy with consent:

```text
+------------------------------------------------------------------------------+
|  CONSENTED  ·  PARTICIPANT-CONTROLLED  ·  LOCAL ONLY      workspace: DEMO-01   |
+------------------------------------------------------------------------------+
```

- It states facts the app can truthfully assert at that moment. If a claim becomes untrue, the banner changes state rather than lying: for example, if a researcher share is active it reads `SHARED WITH: <named researcher> · scope: <scope> · until <date>`; if collection is paused it shows `COLLECTION PAUSED`; if an external LLM is enabled for a briefing it adds `EXTERNAL MODEL ACTIVE`.
- "LOCAL ONLY" is only shown when no network transfer of workspace data is configured; the condition and its verification method are open questions (section 15), and the banner must not claim more than can be checked.
- In demo mode it reads `SYNTHETIC PERSONA · NOT REAL DATA`.
- The banner is never hidden, including in screenshot-safe or full-screen modes.

### 3.8 What makes this distinct from Foundry / Gotham (D-022)

This section is a self-imposed checklist, not legal advice.

- **No reuse of Palantir imagery:** no logos, iconography, icon style, screenshots, color palette sampling, or typographic clones. Reviewers should compare new screens against public screenshots only to avoid resemblance, not to copy.
- **Structurally different layout:** an operations-room "desk" with a persistent consent banner, lens bar, and status strip; object detail in a dossier that foregrounds provenance and participant correction (neither of which is a signature of the reference product).
- **Different semantics:** every mark carries an epistemic class and granularity glyph; panels show "what this does NOT tell you."
- **Different emotional register:** the spy aesthetic is turned on its head. The operator is the observed person, and the interface says so.
- **Concepts borrowed, expression original:** ontology, links, timeline, map, investigation, actions. The borrowing stops at concepts.

## 4. Lens modes

The reference uses sensor-style visual modes (CRT, night vision, thermal, noir) on keys 1-6. Here the equivalent are **lenses**: each lens changes what the same objects are colored and emphasized by, and each answers a real question. They are analytic, not skins. Keys 1-6 switch lens in any view that supports it (section 6.9); a lens never changes the data, only its encoding.

| Key | Lens | Question answered | Encoding |
|---|---|---|---|
| 1 | **Evidence** (default) | What is this based on? | Color by epistemic class; brackets show class; provenance badge counts source records behind each mark. |
| 2 | **Coverage / missingness** | Where is the data thin or absent? | Hatch for no data, lock for paused sources, fill density by record count per bucket. Known zeros separated from unknowns. |
| 3 | **Time-heat** | When does this happen? | Heat by time-of-day/day-of-week density. Shown as aggregate with its window; heat of an inferred routine is labeled hypothesis/inference. |
| 4 | **Uncertainty** | How sure are we? | Sensor accuracy as radius; statistical interval as band; low-support marks washed out. Does not convert accuracy into probability. |
| 5 | **Privacy exposure** | Which apps touched which resources and domains? | Highlights `App`, `Domain`, `ResourceAccess`, `NetworkAggregate`; edge thickness = count within window. Shows what a third party could see in principle given that data, not what any company actually knows ([D-023](decisions.md)). |
| 6 | **Noir / focus** | Reduce noise to read one thing. | Desaturated, all effects off, high contrast; the accessible "analysis" rendering. |

Rules:

- The active lens is always named in the status strip.
- Lens 5 must display a standing note: "Shows what these records could expose; it does not show what any company inferred."
- A cosmetic "show" skin (CRT/thermal look) may exist later, but it is a separate toggle labeled `STYLE`, off by default, and not mistaken for a lens.

## 5. Screen inventory and data mapping

| # | Screen | Primary object types |
|---|---|---|
| 1 | Ops map | Place, Visit, Trip, Source, Link, Finding (overlaid) |
| 2 | Timeline | ActivityInterval, DailyHealthAggregate, CalendarEvent, Visit, Trip, NetworkAggregate, ResourceAccess, AccountActivity, Source |
| 3 | Object dossier | any object; examples: Place, App; plus Link, Correction, Finding |
| 4 | Link graph | all types as nodes; Link as edges |
| 5 | Source coverage board | Source (primary), counts by every record type |
| 6 | Investigation workspace | Finding, Correction, Link, evidence from any type |
| 7 | Participant control room | Source, Correction, Finding (derivative cascade), all deletable types |
| 8 | Briefing | Finding (selected), plus any objects cited |

Conceptual object types used here: Source, Place, Visit, Trip, ActivityInterval, DailyHealthAggregate, CalendarEvent, App, Domain, ResourceAccess, NetworkAggregate, AccountActivity, Finding, Correction, Link. They are display-level categories; the ontology doc's finer types (ActivitySession, SleepSession, Hypothesis, Inference, Prediction, ParticipantCorrection) map into them as follows: `Finding` covers Hypothesis, Inference, and Prediction records, with the epistemic class as a field; `Correction` corresponds to ParticipantCorrection. This mapping is illustrative, not a schema decision.

All wireframes below are synthetic and use a fictional city ("Veridia") and a synthetic persona. They are layout sketches, not pixel specifications.

## 6. Screens

### 6.1 Ops map

Full-bleed map of a fictional city with a glass layer panel, trail rendering, and click-to-open telemetry card. The map base is an abstract vector grid, not real cartography, in the concept stage. A real base map brings tile licensing and network questions (open question section 15).

```text
+------------------------------------------------------------------------------+
| CONSENTED · PARTICIPANT-CONTROLLED · LOCAL ONLY          SYNTHETIC PERSONA     |
+---------------+--------------------------------------------------+-----------+
| LAYERS        |                                                  | TELEMETRY |
| [x] Visits    |        .  .                                      | PLACE     |
| [x] Trips     |     .-'  [P2]=== trail (fades with age)          | "Cafe 7"  |
| [ ] Raw GPS   |    /       \                                     | INFERENCE |
| [x] Places    |  [P1]       o-.-.-.-> [P3]                       | label:    |
| [ ] Findings  |  home?       (reticle)                           |  "work?"  |
|               |  dashed =                                        | visits 14 |
| LENS: 1 EVID  |  hypothesis             .. no data ..            | acc ±18m  |
| TIME WINDOW   |                         (hatched region)         | [prove]   |
| |----o====|   |                                                  | [correct] |
| 03 Mar-09 Mar |                                                  | [delete]  |
+---------------+--------------------------------------------------+-----------+
| lens:EVIDENCE · window:7d · 412 obs · 31 visits · 6 trips · gaps:3 · 12:04   |
+------------------------------------------------------------------------------+
```

Key behaviors:

- **Trails** show the participant's own recent movement; fade encodes age. A trail is drawn only where points exist; between sparse points it is drawn as dashed (gap), not interpolated.
- **Visits** are interval glyphs (bars on a pin), **Trips** are routes with start/end caps. Raw coordinate observations are optional points with accuracy circles.
- **Places** are labeled as inference (double outline) until the participant confirms a label, at which point the correction is shown as such (section 6.3).
- **Hatched regions** denote time or space with no data, or an explicit "location sharing paused".
- **Click** a mark to open the telemetry card; **Shift-click** to add to the investigation scratch set.
- Time scrubber at the bottom of the layers panel, shared with the Timeline.
- The reference's "AI readout" is represented by the Briefing screen (6.8), not an always-on overlay, to avoid unlabeled model prose on a dramatic surface.

Data mapping: Place, Visit, Trip, Source (quality/coverage), Link (visit-to-place), Finding (optional overlays such as a routine, labeled by class).

### 6.2 Timeline

Multi-lane, one lane per source, with the shared window and a fixed granularity glyph vocabulary.

```text
 window: Mon 03 - Sun 09 Mar          zoom: day  [ - ][ + ]      lens: 2 COVERAGE
 lane \ time    00    06    12    18    00    06    12    18
 Location       .. .. ●●● ●●●●●●●●● ..  [///no data///] ●● ●●●●●
 Visits         |=Home==|   [=Cafe 7=]  |==Gym==|   ?-----open
 Motion         ====walk==   ==auto==                    (intervals)
 HealthKit      [steps 8,412 AGG day]   [ HR: no records ]  [sleep: n/a]
 Calendar       [Standup 09:30-10:00]     [Dentist 15:00-16:00]
 Reminders      o due 10:00   x done 10:12
 AppPrivacyRpt  ~~~ Domains x41 (window 7d AGG, not events) ~~~
 NetworkAgg     ▂▃▅▂▁ bytes by hour (AGG)
 AccountExport  ▏login ▏purchase ▏purchase           (point events)
 Findings       - - Routine "morning cafe" (hypothesis) - -  ==Inference==
 legend: ● point  [===] interval  ▂▃ aggregate  /// unknown  [lock] paused
```

(The final legend line is illustrative text only; icons in the real UI are the glyphs in section 3.5.)

Key behaviors:

- Lanes are collapsible and reorderable; each lane header shows source status, last record timestamp, and record count in view.
- **Hover** shows exact timestamps, source, and granularity; **click** opens the dossier; **drag** selects a range for investigation.
- A lane with no collection shows hatching; a lane with a known zero shows an explicit baseline mark.
- Findings occupy their own lane, drawn in their epistemic class.
- Timezone is shown in the header; DST transitions and time-zone changes render as marked seams. (Time-zone semantics are an open ontology issue.)

Data mapping: ActivityInterval, DailyHealthAggregate, CalendarEvent, Visit, Trip, ResourceAccess, NetworkAggregate, AccountActivity, Source, Finding.

### 6.3 Object dossier

A page for any object. Example below is a `Place` (an inference), with an `App` variant noted afterward.

```text
+------------------------------------------------------------------------------+
| PLACE · INFERENCE (double outline)         "Cafe 7"   status: label CORRECTED  |
+--------------------------+---------------------------------------------------+
| IDENTITY                 | LINKED OBJECTS                                    |
| label: Cafe 7 (user)     |  Visit x14  ·  Trip x9 (arrive)  ·  CalendarEvent  |
| inferred: "workplace?"   |  x3 (location text)  ·  Finding x2                 |
| first seen: 03 Feb       |  [ open in graph ]                                 |
| last seen:  09 Mar       +---------------------------------------------------+
| centroid acc: ±18 m      | PROVENANCE TRAIL                                  |
| class: INFERENCE         |  1 Observation   Core Location (src: iphone-demo)  |
|                          |  2 Event         visit.normalized v0.1            |
| WHAT THIS DOES NOT SAY   |  3 Inference     place.cluster  method v0.1        |
| - not a confirmed role   |  4 Correction    user relabeled 05 Mar             |
| - no content/activity    |  [ show raw record ids ]                           |
|   inside the place       +---------------------------------------------------+
|                          | CORRECTIONS & HISTORY                             |
| ACTIONS                  |  05 Mar  label "workplace?" -> "Cafe 7"  (by user) |
| [correct label]          |  derived items recomputed: 2  (view)               |
| [merge] [split]          |  [ undo ]                                          |
| [hide] [delete..]        |                                                   |
+--------------------------+---------------------------------------------------+
```

`App` dossier variant: identity (name, source), linked `Domain` contacts and `ResourceAccess` entries (camera, microphone, location, contacts, etc., with timestamps and window), `NetworkAggregate` totals with their window, and a standing note that these are aggregates of contact, not browsing or content. Wording follows the provenance rules in [the App Privacy Report notes](../spikes/app-privacy-report.md).

Key behaviors:

- Every field shows its class; edited fields show original and correction.
- "What this does NOT say" is mandatory on derived objects.
- Corrections trigger a dependent-recompute list; nothing is silently rewritten (history preserved).

Data mapping: any object; Place, App as primary examples; Link, Correction, Finding, Source in side panels.

### 6.4 Link graph

Node-link view showing connected objects with typed, time-bounded, provenance-bearing edges.

```text
        (Source: iphone-demo)
            |  CAME_FROM
      [Visit 12]--OCCURRED_AT-->{Place: Cafe 7}--VISITED_BY--(Participant)
            |                         |
      PART_OF                    LINKED_TO
            v                         v
   <Routine: morning cafe>      [CalendarEvent: Standup]
        (hypothesis, dashed)         (cal export, solid)

 node shape = type    outline = class    edge weight = count in window
 edge dashed = inferred link    edge has [t0..t1] on hover
```

Key behaviors:

- **Expand** neighbors one hop at a time; hop depth is shown; the visible subset is not presented as the whole graph.
- Filter by type, class, source, and time window; **time slider** shows the graph as of a moment (links carry time ranges).
- Edge hover shows: type, time range, evidence count, method/version for inferred links, and whether a correction applies.
- Layout is stable and deterministic (same view, same positions) so screenshots and shareable views are reproducible.
- Rendered as flat shapes by default; the dramatic glow is an optional style.
- Large graphs aggregate into clusters with counts rather than hairballs; clusters are labeled as aggregates.

Data mapping: all object types as nodes; Link as edges; Finding and Correction as annotated nodes.

### 6.5 Source coverage board

"What data do I actually have?" is the first V1 demonstration question ([mvp](mvp.md)), so this board is a first-class screen, not a settings page.

```text
+------------------------------------------------------------------------------+
| SOURCE            SUPPORT  AUTH      RECORDS  LATEST        GRANULARITY  GAPS |
| Core Location     yes      while-use 4,120    09 Mar 11:58  point        3    |
| Core Motion       yes      granted   212      09 Mar 11:40  interval     1    |
| HealthKit         yes      n/obs.*   steps:9d  09 Mar        daily AGG    HR:? |
| EventKit          yes      granted   58       08 Mar        interval     0    |
| App Privacy Rpt   import   (file)    41 dom   07 Mar        7d AGG       ?    |
| Account export    import   (file)    1,206    01 Mar        point        ?    |
| Screen Time       gated    n/a       --       --            --           --   |
| * HealthKit read denial is not observable; empty != denied.                   |
| Coverage strip (28d):  Loc [██▒▒░░██]  Motion [██▒░░░░█]  Cal [████████]      |
|   █ data   ▒ sparse   ░ none-known   (hatch) unknown                          |
+------------------------------------------------------------------------------+
```

Columns mirror the per-capability facts required by [the collection probe](collection-probe.md): support, provisioning, authorization where observable, record count, latest timestamp, granularity, missingness, and export success. Cells that cannot be known display `unknown` or `not observable`, never a guess. A summary line tracks progress toward the provisional "three useful categories across two domains" target and states honestly if it falls short.

Data mapping: Source (primary), with counts per record type (ActivityInterval, DailyHealthAggregate, CalendarEvent, NetworkAggregate, AccountActivity, ResourceAccess, Visit).

### 6.6 Investigation workspace

A reproducible analytical investigation per [D-025](decisions.md). Null and inconclusive results are complete outcomes.

```text
+------------------------------------------------------------------------------+
| FINDING · HYPOTHESIS -> (candidate) INFERENCE      id: F-0007  status: DRAFT   |
+------------------------------------------------------------------------------+
| STATEMENT  Evenings with >3h screen time are associated with more sleep      |
|            interruptions.   [correlation, not causation]                      |
| METHOD     rank-correlation + permutation test       version 0.1  (pinned)    |
| WINDOW     21 days     N = 19 paired nights     missing: 2 nights (shown)     |
| EFFECT     +0.21 (illustrative)    95% interval [-0.18, +0.52]  (WIDE)        |
| VERDICT    INCONCLUSIVE - interval includes zero    [null result is valid]    |
+---------------------------+--------------------------+-----------------------+
| SUPPORTING EVIDENCE       | CONTRADICTING EVIDENCE   | ALTERNATIVE EXPLAINS  |
| 7 nights (list, source)   | 9 nights (list, source)  | - travel week         |
|                           |                          | - weekend effect      |
|                           |                          | - measurement gaps    |
+---------------------------+--------------------------+-----------------------+
| REPRODUCE  inputs hash (declared scope) · parameters · [ re-run ] [ diff ]    |
| PARTICIPANT  [confirm] [reject] [annotate]   corrections preserved in history |
| LOCK (optional, forecasts only): requires verifiable pre-outcome mechanism    |
+------------------------------------------------------------------------------+
```

Rules:

- Always show: statement, method and version, window, sample size, missingness, effect, uncertainty, verdict, supporting and contradicting evidence, alternatives, and review status ([ontology: inference object](ontology.md)).
- Layout gives contradicting evidence equal visual weight to supporting evidence.
- The verdict vocabulary includes `INCONCLUSIVE`, `NO EVIDENCE OF EFFECT`, and `INSUFFICIENT DATA`, each styled as a completed result.
- A 21-day window is labeled as pipeline validation, not stable statistical significance ([mvp](mvp.md)). The example numbers above are illustrative only.
- A hash alone is never presented as proof of time; "lock" is available only for forecasts and only with a verifiable mechanism (see [inference engine notes](inference-engine.md)).
- Model suggestions appear in a labeled "Suggestions (not evidence)" drawer.

Data mapping: Finding (primary); Correction; Link; evidence from any record type.

### 6.7 Participant control room

All participant-agency controls on one screen. The participant must be able to understand collection, pause it, initiate sharing, correct conclusions, and delete data.

```text
+------------------------------------------------------------------------------+
| CONTROL ROOM                                          COLLECTION: [ PAUSE ALL ]|
+---------------------+--------------------------------------------------------+
| PER-SOURCE          | SCOPE & SHARING                                        |
| Location  [ON ][..] | Current share: NONE (self-operated)                    |
| Motion    [ON ][..] | [ create export ]  encrypted batch · scope: [select]   |
| Calendar  [OFF][..] | [ authorize researcher.. ]  named · scope · expiry     |
| (per-source pause,  | Last export: none                                      |
|  window, retention) | Activity log (what left this workspace, when, to whom) |
+---------------------+--------------------------------------------------------+
| DELETE (preview first; nothing deleted yet)                                  |
|  target: Source "Calendar" · 01 Mar - 09 Mar                                  |
|  will remove:  58 CalendarEvent records                                       |
|  derived-data cascade (will be removed or recomputed):                        |
|     Visit links x6 · Finding F-0003 (inference) · Briefing B-0002             |
|     [ view each ]                                                             |
|  UNVERIFIED / possibly remaining copies (cannot confirm deletion):            |
|     - exported encrypted package from 06 Mar (location unknown to app)        |
|     - Mac backups / OS snapshots (outside app control)                        |
|     - screenshots and shared view files (if any)                              |
|  [ cancel ]                                  [ delete after typing DELETE ]   |
+------------------------------------------------------------------------------+
```

Key behaviors:

- The cascade preview lists derivatives (links, findings, briefings, caches) that will be removed or recomputed, following the sensitive-derivative rule in [ontology](ontology.md) and the deletion section of [governance](trust-and-data-governance.md).
- The **unverified copies list** is a design requirement: the UI states what it cannot verify (backups, exported packages, screenshots) and does not claim "all copies deleted."
- Deletion confirmation is deliberate (typed confirmation), but pausing is one action.
- An export dialog shows exactly what will leave: source scope, date range, derived items included or excluded, and recipient.
- The researcher-access section appears only when authorization is configured, and clearly separates self-use from researcher-assisted mode ([D-024](decisions.md)).

Data mapping: Source (primary), Correction, Finding (cascade), plus all deletable record types.

### 6.8 Briefing readout

An intelligence-style short readout of the current view, inspired by the reference's AI readout, but with strict labeling.

```text
+------------------------------------------------------------------------------+
| BRIEFING · view: Timeline · 03-09 Mar · lens: EVIDENCE                        |
+------------------------------------------------------------------------------+
| FROM THE DATA (generated by code, reproducible)                               |
|   31 visits across 5 places; 6 trips; 3 coverage gaps (longest 14 h).         |
|   Location lane has no data 07 Mar 02:00-16:00 (cause unknown).               |
+------------------------------------------------------------------------------+
| EXPLANATION - model-written, NOT PROOF                       model: [local/ext]|
|   "Your week shows a stable weekday pattern around two places. The gap on     |
|    07 Mar may reflect the phone being off or location paused."                |
|   [?] why am I seeing this    [view the objects cited]    [regenerate]        |
|   Every sentence links to its cited objects; unlinked sentences are flagged.  |
+------------------------------------------------------------------------------+
| EXPORT/SHARE VIEW  [ snapshot, scope-checked ]  -> see screenshot safety (10) |
+------------------------------------------------------------------------------+
```

Rules:

- Two clearly separated blocks: **deterministic summary** (counts and facts computed by code) and **model explanation** (labeled `EXPLANATION - NOT PROOF`).
- Model prose cannot introduce facts that are not backed by cited objects; unsupported sentences are flagged or removed. Model prose never appears as an inference ([D-012](decisions.md)).
- Local versus external model is a visible indicator and a participant choice; the selection stays deferred and provider-neutral ([D-013](decisions.md)). When an external model is used, the banner shows `EXTERNAL MODEL ACTIVE`, and the data sent is previewable beforehand.
- The briefing is regenerated from the view, not stored as authoritative; saved briefings are Findings-adjacent artifacts with their own deletion cascade.
- Shareable "view links" from the reference are replaced by local **view snapshots** (section 10) that include scope, lens, and window and never embed a remote URL carrying data.

Data mapping: Finding, plus any objects cited; Source for provenance.

### 6.9 Navigation, lenses and layout summary

```text
[Banner]
[Lens bar: 1 EVID  2 COVER  3 TIME  4 UNCERT  5 PRIVACY  6 FOCUS]  [Cmd palette]
[ Left rail: Map | Timeline | Dossier | Graph | Coverage | Investigate | Control ]
[ Main view ................................................... ][ Context ]
[Status strip]
```

Selection, time window, and lens are shared across screens so moving from the map to the dossier keeps context.

## 7. Keyboard-first interaction and command palette

Principle: everything is reachable without a mouse; pointing is a convenience.

- **Command palette** (`Ctrl/Cmd+K`): fuzzy search for objects ("Cafe 7"), screens ("go to Timeline"), lenses ("lens uncertainty"), and actions ("pause collection", "export view snapshot", "open delete preview"). Destructive commands open the preview, never execute directly.
- **Lens keys 1-6**; **screen keys** `G` then `M/T/D/L/C/I/P` (Map, Timeline, Dossier, Link graph, Coverage, Investigation, Participant control).
- **Time:** `[` / `]` step the window; `-` / `+` zoom; `T` jump to today; `Space` sets/clears a time marker.
- **Selection:** `Tab` cycles marks in view; `Enter` opens the dossier; `Shift+Enter` adds to the investigation scratch set; `Esc` closes cards or exits modes.
- **Provenance:** `P` on a selected mark shows its provenance trail.
- **Panic / privacy:** `Ctrl/Cmd+Shift+H` hides sensitive content (blur) immediately; `Ctrl/Cmd+Shift+P` pauses collection (confirmation visible).
- Shortcuts are listed in a `?` overlay, and are rebindable (later). Final bindings must be checked against platform conventions and screen-reader use.

## 8. Accessibility

- **Reduced motion:** honor the OS setting; ambient effects off; transitions become instant or crossfades. Trail fade remains as static opacity steps.
- **Effects off by default in analysis views** (Timeline, Dossier, Investigation, Coverage, Control): no glow, scanlines, blur-heavy panels, or parallax unless the participant turns on the `STYLE` toggle. The Ops map may offer effects but defaults to a restrained rendering.
- **Contrast:** target WCAG AA for text and non-text UI elements against actual panel backgrounds, including glass panels with their fallback fill; dark theme is the design baseline, and a light theme is an open question rather than an afterthought.
- **Never color alone:** class, state, and lens meaning are carried by shape, pattern, and label as well.
- **Screen readers and keyboard:** every chart has a tabular alternative and a text summary; focus order is deterministic; focus rings are visible.
- **Text size:** scalable; layouts must survive larger type. Minimum sizes in section 3.3.
- **Seizure and vestibular safety:** no flashing; no large-area fast motion; no parallax that the participant cannot disable.
- Accessibility is a design requirement to verify, not a claim of conformance; no audit has been done.

## 9. Language and honesty rules for UI text

- Use "associated with" and "correlation," never "causes," unless a method supports it and is cited.
- Use "records show" for observations; "appears to be" for inferences; "forecast" for predictions.
- Never present absence of records as absence of behavior: "no records in this window" instead of "you did not."
- Privacy-exposure wording says "could expose" and "contacted," not "tracked" or "stole."
- Avoid theatrical text that implies more capability than exists (for example "TARGET ACQUIRED"). The aesthetic is in the typography and structure, not in false claims. Provocative copy follows the branding rule: it resolves immediately into a statement of consent and local ownership.

## 10. Privacy of the UI itself

The explorer displays highly sensitive material, so the interface is itself a leak surface.

- **Screenshots and screen sharing:** a screenshot-safe mode blurs or redacts precise coordinates, names, and domains; the banner stays visible. The app cannot prevent OS-level screenshots, so the UI warns rather than promises (open question on OS support).
- **Demo mode with synthetic persona:** a one-key switch loads a bundled synthetic workspace (fictional city, fake accounts, fake apps), with the banner reading `SYNTHETIC PERSONA · NOT REAL DATA`. Demo and real workspaces never share a view, cache, or snapshot. Public demos, docs, and recruitment visuals use only this mode ([AGENTS](../AGENTS.md): synthetic fixtures in the repository).
- **View snapshots instead of remote share links:** exportable view states carry scope, lens, and window, strip raw identifiers by default, and show a preview of what they contain. No server is assumed.
- **Idle lock / blur:** optional auto-blur on inactivity and on window defocus.
- **Map tiles and fonts:** a real base map or web fonts would cause network requests that can leak location of interest; the default is no network calls and bundled assets (open question on offline map data).
- **No cross-workspace UI state:** recent items, search history, and caches are per-workspace and deleted with the workspace.
- **Logs and crash reports** must not contain participant data.
- **Third parties:** names or details of nonparticipants in the participant's own records are masked by default in snapshots and demo materials.

## 11. Mapping of object types to screens (summary)

| Object type | Map | Timeline | Dossier | Graph | Coverage | Investigation | Control | Briefing |
|---|---|---|---|---|---|---|---|---|
| Source | quality | lane header | side panel | node | primary | provenance | primary | provenance |
| Place | primary | markers | primary | node | - | evidence | delete | cited |
| Visit | primary | lane | primary | node | count | evidence | delete | cited |
| Trip | primary | lane | primary | node | count | evidence | delete | cited |
| ActivityInterval | - | lane | primary | node | count | evidence | delete | cited |
| DailyHealthAggregate | - | AGG lane | primary | node | count | evidence | delete | cited |
| CalendarEvent | - | lane | primary | node | count | evidence | delete | cited |
| App | - | - | primary | node | - | evidence | - | cited |
| Domain | - | window lane | primary | node | count | evidence | - | cited |
| ResourceAccess | - | lane | primary | edge/node | count | evidence | delete | cited |
| NetworkAggregate | - | AGG lane | primary | node | count | evidence | delete | cited |
| AccountActivity | - | lane | primary | node | count | evidence | delete | cited |
| Finding | overlay | lane | primary | node | - | primary | cascade | primary |
| Correction | badge | badge | history | annotation | - | history | history | - |
| Link | trails/routes | - | side panel | edge | - | evidence | cascade | cited |

## 12. Out of scope for this concept

- Choosing a UI framework, rendering engine, globe/map library, or app architecture.
- Any change to collection scope; the UI shows only data the participant has authorized. Optional capture approaches stay gated by [the inspirations review](inspirations-and-collection-patterns.md).
- Implementing a 3D globe: this concept uses a city-scale map first, because most participant data is local movement; a globe is a possible later style for travel data.
- Multi-participant or cross-workspace views (workspaces stay isolated, [D-016](decisions.md)).
- Final branding, logo, and name decisions ([D-020](decisions.md)).
- Forecast, notification, and experiment surfaces beyond a placeholder (optional extensions).

## 13. Prototype plan

Goal: test look-and-feel, legibility of the epistemic encodings, and the honesty rules, before choosing a production stack. This does not begin explorer implementation or constrain the production stack.

1. **Standalone synthetic HTML concept** (single static page set, no build step, no network calls, bundled fonts or system fonts). Acceptable because it validates visual language without selecting a Mac UI technology. Lives under a clearly named prototype folder when created, with synthetic data only. No raw participant data is ever loaded, and the prototype includes the banner and demo-mode indicator.
2. **Content:** a fictional city map, a synthetic persona with about 4 weeks of generated data, a timeline with all glyph types, one Place dossier, one App dossier, a small link graph, a coverage board that includes unknown and denied-not-observable cases, one null-result investigation, and a control-room delete preview with an unverified-copies list.
3. **Lens mechanics** keys 1-6 and the command palette, with an effects toggle default-off outside the map.
4. **Legibility tests** (informal, with willing synthetic-data viewers): can they tell observation vs inference vs prediction; aggregate vs event; unknown vs zero; can they find the gap; can they find provenance in two actions. Record results as design notes, not as validated usability claims.
5. **Accessibility pass:** reduced-motion, keyboard-only walkthrough, contrast checks on actual colors, grayscale/color-vision simulation.
6. **Outcome:** a short result note (what worked, what was misread, what to change), then a separate decision on the production stack after the collection feasibility lab and Mac preflight ([D-027](decisions.md)). Native Swift/SwiftUI, a local web view, or another approach remains open.
7. The prototype is a design artifact. It must not be presented as the product or as evidence that any data source works.

## 14. Risks

- **Spectacle outrunning truth:** dramatic visuals make weak data look authoritative. Mitigation: principles in section 2, effects off in analysis, mandatory class and granularity encodings.
- **Resemblance to a proprietary product:** mitigated by the checklist in 3.8 and by review before publication.
- **Surveillance aesthetic misread as covert tooling:** mitigated by the always-visible consent banner and consent-forward copy.
- **Sensitive display leaks** (screen sharing, screenshots): see section 10.
- **Overbuilding before collection is proven:** the explorer remains blocked behind the collection feasibility lab; this concept is preparation only.

## 15. Open questions

1. Which claims may "LOCAL ONLY" assert, and how is "no network transfer" verified so the banner cannot lie?
2. Real versus abstract base map: is there an acceptable offline map data source and license, and does tile fetching leak location?
3. Is a globe view valuable for this participant data, or is a city-scale map enough?
4. Should the reference's keys 1-6 map exactly to the six lenses above, or should lenses be user-configurable?
5. How should uncertainty be drawn when sources provide only accuracy radius versus statistical intervals, without implying a common scale?
6. What is the correct visual treatment for overlapping or duplicate imports (counted once) at timeline zoom levels?
7. How are time zones, DST, and device clock changes displayed without misleading gaps?
8. Light theme and high-contrast theme: required for V1 or later?
9. How strong should masking be for nonparticipants appearing in the participant's own records?
10. What can the app truthfully claim about deleted copies, given backups and OS snapshots?
11. Sound: is any audio feedback desired? Default none; if added, off by default and optional.
12. Do view snapshots need signing or integrity marks, and what would "integrity" mean without a trusted time source?
13. Which fonts and assets are acceptable under the open-source license decision ([D-021](decisions.md)), and is any reuse of the MIT reference code desired?
14. Should the "show" style exist at all in the production explorer, or only in demos and recruitment visuals?

## 16. Proposed decision text

Proposed for `docs/decisions.md` (not yet recorded; needs owner approval):

> **D-NEXT (Provisional):** Adopt an original dark "operations room" visual concept for the local explorer, with an always-visible consent banner, sensor-style lenses that encode evidence, coverage, time, uncertainty, and privacy exposure, and no nonparticipant layers; no UI framework is selected.
> **Consequence:** every mark must distinguish observation/event/hypothesis/inference/prediction, aggregate vs event, and unknown vs zero; effects are off by default in analysis views; a standalone synthetic HTML prototype may test look-and-feel, while production stack and implementation stay gated behind the collection feasibility lab and Mac preflight.
