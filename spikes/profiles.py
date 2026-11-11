"""Six deterministic SYNTHETIC profiles under persona-contract-0.2-provisional.

Everything here is invented: a fictional city ("Port Meridian") at fictitious coordinates over open
ocean, com.example.* identifiers, *.example hosts, pseudonymous contacts (contact-A ...). This is
demonstration data and a PROVISIONAL explorer data contract, NOT a production schema, a capability
claim for any real source, or evidence about a real person. See profiles.md and docs/insight-lenses.md.

Each profile covers 56 days. Planted behaviour changes live only in `scenario_truth(key)`, which is for
tests and scoring; it is never written into the workspace document.

Standard library only, seeded RNG streams, identical output on every run.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import random
from typing import Any

UNKNOWN = "unknown"  # Unmeasured value; never substitute 0.
CONTRACT_VERSION = "persona-contract-0.2-provisional"
TZ_NAME = "Etc/GMT+5"  # fixed UTC-05:00, no daylight saving; chosen for determinism
TZ = timezone(timedelta(hours=-5))
START = datetime(2026, 1, 5, tzinfo=TZ)  # a Monday
DAYS = 56
EVIDENCE_CLASSES = ("observation", "normalized_event", "hypothesis", "inference", "prediction")
BBOX = {"lat_min": 30.00, "lat_max": 30.06, "lon_min": -40.06, "lon_max": -40.00}
PROFILES = ("steady", "doomscroll", "social_drop", "search_drift", "commuter", "sparse")
WORKSPACES = {"steady": "ws-prof-steady", "doomscroll": "ws-prof-doomscroll", "social_drop": "ws-prof-social",
              "search_drift": "ws-prof-search", "commuter": "ws-prof-commuter", "sparse": "ws-prof-sparse"}
SEEDS = {"steady": 20260411, "doomscroll": 20260422, "social_drop": 20260433,
         "search_drift": 20260444, "commuter": 20260455, "sparse": 20260466}
SUBJECTS = {"steady": "PR-01", "doomscroll": "PR-02", "social_drop": "PR-03",
            "search_drift": "PR-04", "commuter": "PR-05", "sparse": "PR-06"}
DESCRIPTIONS = {  # neutral on purpose: no hint of the planted scenario
    "steady": "Synthetic profile: office worker, 8 weeks",
    "doomscroll": "Synthetic profile: office worker, 8 weeks",
    "social_drop": "Synthetic profile: office worker, 8 weeks",
    "search_drift": "Synthetic profile: office worker, 8 weeks",
    "commuter": "Synthetic profile: hybrid worker, 8 weeks",
    "sparse": "Synthetic profile: office worker, limited sources, 8 weeks",
}
STREAMS = ("plan", "steps", "screen", "sleep", "acct", "msg", "weather", "loc", "motion", "misc")

PLACES = {
    "home": ("Home (fictional)", 30.020, -40.030), "work": ("Work office (fictional)", 30.040, -40.010),
    "gym": ("Gym (fictional)", 30.032, -40.020), "cafe": ("Corner cafe (fictional)", 30.036, -40.012),
    "park": ("Meridian Park (fictional)", 30.012, -40.045), "grocery": ("Grocery (fictional)", 30.025, -40.038),
}
PARKING = ("Office parking (fictional)", 30.041, -40.011)
# key -> (display name, category, weekday mean minutes, weekend mean minutes, pickups per minute)
APPS = {
    "clips": ("Example Clips", "short_video", 22.0, 35.0, 0.20),
    "social": ("Example Social", "social", 25.0, 35.0, 0.25),
    "chat": ("Example Chat", "messaging", 30.0, 30.0, 0.30),
    "news": ("Example News", "news", 15.0, 20.0, 0.12),
    "mail": ("Example Mail", "productivity", 20.0, 6.0, 0.35),
    "browser": ("Example Browser", "browser", 25.0, 20.0, 0.15),
}
NOTIFY = {"chat": (45, 35), "social": (30, 30), "mail": (40, 8), "news": (10, 10)}
DOMAINS = {"search": "search.example", "video": "clips.example", "chat": "chat.example", "social": "social.example",
           "news": "news.example"}
CONTACTS = {"contact-A": (7.0, 8.0), "contact-B": (3.0, 3.0), "contact-C": (1.2, 1.4)}  # (sent, received) means
NEUTRAL_QUERIES = {
    "cooking": ["easy rice recipe", "how long to roast vegetables", "simple soup ideas"],
    "travel": ["weekend train times", "pack list for a short trip", "museum opening hours"],
    "technology": ["update phone software", "compare laptop batteries", "fix slow wifi"],
    "sports": ["running plan for beginners", "local league results", "stretching routine"],
    "local_transport": ["bus route changes", "bike lane map", "parking near the station"],
    "shopping": ["best desk lamp", "winter boots sale", "gift ideas under budget"],
}
SENSITIVE_QUERIES = {  # topic -> (sensitive_category, queries); bland and fictional
    "sleep": ("health", ["how to fall asleep faster", "why am I always tired", "sleep schedule tips"]),
    "anxiety": ("mental_health", ["anxiety symptoms", "how to calm down quickly", "feeling restless at night"]),
}
SOURCES = {  # sid -> (name, system, real-world status, availability note)
    "src-location": ("Location", "ios.core_location", "supported_in_probe",
                     "Core Location via the collector app; background behavior and battery impact still under test."),
    "src-motion": ("Motion", "ios.core_motion", "supported_in_probe",
                   "Core Motion activity history; history depth limit unverified."),
    "src-healthkit": ("HealthKit", "ios.healthkit", "partly_unproven",
                      "HealthKit read access; sleep needs an authorized producer (HLT-01, unproven). Read denial is "
                      "not observable from empty results."),
    "src-eventkit": ("EventKit", "ios.eventkit", "supported_in_probe",
                     "EventKit calendar read; scheduled context, not observed activity."),
    "src-apr": ("AppPrivacyReport", "ios.app_privacy_report", "supported_in_probe",
                "App Privacy Report export; supplies app and domain identities only in this profile."),
    "src-screentime": ("ScreenTime", "ios.family_controls_device_activity", "gated",
                       "Family Controls / DeviceActivity export. Gated: entitlement, iOS 26.4+, region (A4 to A6). "
                       "Synthetic availability is not a capability claim."),
    "src-account-export": ("AccountExport", "example-account-export", "unproven",
                           "Participant's own account export (ACC-01, unproven). Topic labels are derived by "
                           "keyword_lexicon_v0."),
    "src-messaging-export": ("MessagingExport", "example-chat-export", "unproven",
                             "Participant's own account export of a chat app (ACC-01, unproven). Daily counts per "
                             "pseudonymous contact only; no names or content."),
    "src-transactions": ("Transactions", "example-transaction-export", "participant_provided_only",
                         "Optional participant-provided transaction export. No general iPhone API."),
    "src-weather": ("Weather", "example-public-weather", "public_lookup",
                    "Public weather for the fictional city. A real lookup would reveal a coarse location to the "
                    "weather provider."),
    "src-workspace": ("Derived", "laplace-demo", "not_applicable",
                      "Findings and corrections; derived or participant-authored, not a collection source."),
}
DATA_TYPES = ("LocationSample", "Visit", "Trip", "ActivityInterval", "DailyHealthAggregate", "SleepInterval",
              "CalendarEvent", "ScreenTimeDaily", "NotificationDaily", "MessagingDaily", "AccountActivity",
              "Transaction", "WeatherDaily")

# Planted parameters (also mirrored in scenario_truth).
DOOM_DAY, SOCIAL_DAY, SEARCH_DAY = 28, 31, 24
RAIN_MM, RAIN_STAYS_HOME = 2.0, 0.85


# --- helpers --------------------------------------------------------------------------------

def at(day: int, minute: float) -> datetime:
    return START + timedelta(days=day, minutes=minute)


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="minutes")


def prov(source: str, method: str, where: str) -> dict[str, str]:
    return {"source": source, "method": method, "method_version": "0.2", "line_or_record": where}


def _generate(key: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if key not in PROFILES:
        raise ValueError(f"unknown profile {key!r}")
    ws, seed = WORKSPACES[key], SEEDS[key]
    R = {name: random.Random(seed * 100 + i) for i, name in enumerate(STREAMS)}
    has_screen, has_sleep, has_tx = key != "sparse", key != "sparse", key == "commuter"

    def rec(rid: str, typ: str, source_id: str, evidence_class: str, granularity: str, **fields: Any) -> dict[str, Any]:
        out: dict[str, Any] = {"id": rid, "type": typ, "workspace_id": ws, "source_id": source_id,
                               "evidence_class": evidence_class}
        if granularity != "not_applicable":
            out["granularity"] = granularity
        out.update(fields)
        return out

    def T(batch_id: str, start: datetime, end: datetime | None = None) -> dict[str, Any]:
        t: dict[str, Any] = {"import_batch_id": batch_id, "timezone": TZ_NAME}
        if end is None:
            t["event_time"] = iso(start)
        else:
            t["event_start"], t["event_end"] = iso(start), iso(end)
        return t

    def day_bounds(batch_id: str, day: int) -> dict[str, Any]:
        return T(batch_id, at(day, 0), at(day + 1, 0))

    objs: list[dict[str, Any]] = []
    links: list[dict[str, Any]] = []

    def link(kind: str, a: str, b: str, evidence: list[str], source_id: str, ev: str = "normalized_event") -> None:
        links.append(rec(f"link-{len(links) + 1:04d}", "Link", source_id, ev, "not_applicable",
                         link_type=kind, **{"from": a, "to": b}, evidence_ids=evidence))

    # -- weather (drives the commuter story; present, but inert, in the other profiles)
    weather = []
    for d in range(DAYS):
        u, e, g, c = R["weather"].random(), R["weather"].expovariate(1 / 5.0), R["weather"].gauss(0, 3.0), R["weather"].random()
        precip = round(0.4 + e, 1) if u >= (0.30 if key == "commuter" else 0.62) else 0.0
        cond = "rain" if precip >= RAIN_MM else ("drizzle" if precip > 0 else ("clear" if c < 0.5 else "cloudy"))
        weather.append({"precip": precip, "temp": round(-2.0 + 0.05 * d + g, 1), "cond": cond})

    # -- movement plan
    location_off_p = 0.38 if key == "sparse" else 0.03
    loc_off = [R["loc"].random() < location_off_p for _ in range(DAYS)]
    plans: list[list[tuple]] = []
    attended: list[bool] = []
    for d in range(DAYS):
        dow = d % 7
        x = [R["plan"].random() for _ in range(10)]
        planned = (dow in (1, 2, 3)) if key == "commuter" else dow < 5
        rain_skip = key == "commuter" and weather[d]["precip"] >= RAIN_MM and x[9] < RAIN_STAYS_HOME
        go_office = planned and not rain_skip
        attended.append(go_office)
        late_social = key == "social_drop" and d >= SOCIAL_DAY
        gp, cp = (0.30, 0.15) if late_social else (0.85, 0.50)
        pk, gr = (0.35, 0.45) if late_social else (0.80, 0.60)
        mode = "drive" if key == "commuter" else ("transit" if x[4] < 0.5 else ("walk" if x[4] < 0.75 else "cycle"))
        segs: list[tuple] = []
        st = {"cur": "home", "t": 0.0}

        def go(dest: str, depart: float, mins: float, how: str) -> None:
            segs.append(("stay", st["cur"], st["t"], depart))
            segs.append(("trip", st["cur"], dest, depart, depart + mins, how))
            st["cur"], st["t"] = dest, depart + mins

        if dow < 5:
            if go_office:
                go("work", 490 + int(x[0] * 50), 18 + int(x[1] * 17), mode)
                dep = 1010 + int(x[2] * 50)
            else:
                if dow in (0, 4) and x[7] < 0.4:
                    go("cafe", 720 + int(x[8] * 30), 8, "walk")
                    go("home", st["t"] + 45, 8, "walk")
                dep = 1080 + int(x[4] * 30)
            if dow in (1, 3) and x[3] < gp:
                go("gym", dep, 12 + int(x[5] * 5), "walk" if x[5] < 0.5 else "transit")
                go("home", st["t"] + 55 + int(x[6] * 25), 15 + int(x[6] * 10), "transit")
            elif dow == 4 and x[3] < cp:
                go("cafe", dep, 10, "walk")
                go("home", st["t"] + 60, 10, "walk")
            elif st["cur"] == "work":
                go("home", dep, 18 + int(x[6] * 17), mode)
        elif dow == 5 and x[5] < pk:
            go("park", 615 + int(x[0] * 40), 15, "walk")
            if x[6] < 0.6:
                go("cafe", st["t"] + 75, 12, "walk")
                go("home", st["t"] + 80, 22, "walk")
            else:
                go("home", st["t"] + 90, 15, "walk")
        elif dow == 6 and x[5] < gr:
            go("grocery", 660 + int(x[0] * 60), 12, "walk")
            go("home", st["t"] + 45, 12, "walk")
        segs.append(("stay", st["cur"], st["t"], 1440))
        plans.append(segs)

    # -- screen time model (computed for every profile so RNG streams do not depend on the scenario)
    screen: list[dict[str, Any]] = []
    for d in range(DAYS):
        wk = d % 7 < 5
        doom = key == "doomscroll" and d >= DOOM_DAY
        late_total = max(0, round(R["screen"].gauss(4, 2.5)))
        late_doom = max(10, round(R["screen"].gauss(50, 22)))
        if doom:
            late_total = late_doom
        late = {"clips": round(late_total * 0.6), "social": late_total - round(late_total * 0.6)}
        row: dict[str, Any] = {"late_total": late_total}
        for app, (_, _, wkm, wem, ppm) in APPS.items():
            base = (wkm if wk else wem) * (1 + R["screen"].gauss(0, 0.22))
            pk_noise = 1 + R["screen"].gauss(0, 0.15)
            if doom and app == "clips":
                base *= 1.45
            lt = late.get(app, 0)
            minutes = max(1, round(base)) + lt
            row[app] = {"minutes": minutes, "late": lt, "pickups": max(1, round(minutes * ppm * pk_noise))}
        row["notify"] = {a: max(0, round((w if wk else we) * (1 + R["screen"].gauss(0, 0.2))))
                         for a, (w, we) in NOTIFY.items()}
        screen.append(row)

    # -- steps
    steps: list[Any] = []
    for d in range(DAYS):
        dow = d % 7
        base = 6000 + (1800 if attended[d] else 0) + (1800 if dow >= 5 else 0)
        level = 0.7 if key == "doomscroll" and d >= DOOM_DAY else 1.0
        lag = 30.0 * screen[d - 1]["late_total"] if key == "doomscroll" and d > 0 else 0.0
        v = int(max(1200, (base + R["steps"].gauss(0, 1000)) * level - lag))
        u = R["steps"].random()
        miss_p = 0.25 if key == "sparse" else 0.03
        steps.append(UNKNOWN if u < miss_p else v)

    # -- sleep
    sleep: list[Any] = []
    for d in range(DAYS):
        wk = d % 7 < 5
        onset = (300 if wk else 340) + R["sleep"].gauss(0, 25 if wk else 40)
        dur = (450 if wk else 480) + R["sleep"].gauss(0, 35 if wk else 45)
        miss = R["sleep"].random() < 0.04
        if key == "doomscroll" and d >= DOOM_DAY:
            onset, dur = onset + 70, dur - 70
        sleep.append(None if miss else (int(onset), int(dur)))

    # -- batches
    imp = at(DAYS, 8 * 60)
    batch_defs = ["location", "motion", "healthkit", "eventkit", "apr", "account-export", "messaging-export", "weather"]
    if has_screen:
        batch_defs.insert(5, "screentime")
    if has_tx:
        batch_defs.append("transactions")
    window = {"start": iso(at(0, 0)), "end": iso(at(DAYS, 0))}
    batches = []
    for b in batch_defs:
        digest = hashlib.sha256(f"synthetic-content::{key}::{b}".encode()).hexdigest()
        batches.append(rec(f"ib-{b}", "ImportBatch", f"src-{b}", "observation", "not_applicable", import_time=iso(imp),
                           timezone=TZ_NAME, content_digest_sha256=digest, status="imported", duplicate_of=None,
                           records_added=None, window_start=window["start"], window_end=window["end"],
                           provenance=prov("synthetic-fixture", "batch_import", f"{b}-batch")))

    # -- places
    place_ids = {}
    place_defs = dict(PLACES)
    if key == "commuter":
        place_defs["parking"] = PARKING
    for k, (name, lat, lon) in place_defs.items():
        place_ids[k] = f"place-{k}"
        objs.append(rec(f"place-{k}", "Place", "src-location", "inference", "not_applicable", label=name, category=k,
                        lat=lat, lon=lon, radius_m=80, coordinates_fictitious=True, label_basis="synthetic_assignment",
                        confidence="high", provenance=prov("synthetic-profile", "assigned_label", f"place:{k}")))

    # -- visits, trips, motion
    visits, trips, motion, vmeta = [], [], [], []
    for d in range(DAYS):
        for seg in plans[d]:
            if seg[0] == "stay":
                _, place, s, e = seg
                if loc_off[d]:
                    continue
                vs, ve = s + (15 if s == 0 else 2), e - (5 if e == 1440 else 2)
                if ve <= vs:
                    continue
                conf = "high" if R["loc"].random() < 0.8 else "medium"
                v = rec(f"visit-{len(visits) + 1:04d}", "Visit", "src-location", "normalized_event", "interval",
                        place_id=place_ids[place], interrupted_by_gap=False, match_confidence=conf,
                        provenance=prov("derived", "dwell_from_samples", f"day{d}:{place}"),
                        **T("ib-location", at(d, vs), at(d, ve)))
                visits.append(v)
                vmeta.append((v["id"], d, place, at(d, vs), at(d, ve)))
                link("VISITED", v["id"], place_ids[place], [v["id"]], "src-location", "inference")
            else:
                _, a, b, s, e, how = seg
                mtype = {"walk": "walking", "cycle": "cycling", "transit": "automotive", "drive": "automotive"}[how]
                mconf = R["motion"].choices(["high", "medium", "low"], [5, 3, 1])[0]
                motion.append(rec(f"act-{len(motion) + 1:04d}", "ActivityInterval", "src-motion", "observation", "interval",
                                  activity_type=mtype, confidence=mconf,
                                  provenance=prov("ios.core_motion", "activity_query", f"motion:L{len(motion) + 1}"),
                                  **T("ib-motion", at(d, s), at(d, e))))
                if not loc_off[d]:
                    trips.append(rec(f"trip-{len(trips) + 1:04d}", "Trip", "src-location", "normalized_event", "interval",
                                     from_place_id=place_ids[a], to_place_id=place_ids[b], mode=how,
                                     mode_confidence=mconf,
                                     provenance=prov("derived", "trip_between_visits", f"day{d}:{a}-{b}"),
                                     **T("ib-location", at(d, s), at(d, e))))
    objs += visits + trips + motion

    # -- health aggregates and sleep
    for d in range(DAYS):
        known = steps[d] != UNKNOWN
        objs.append(rec(f"health-{d + 1:04d}", "DailyHealthAggregate", "src-healthkit", "observation", "aggregate",
                        steps=steps[d], steps_status="measured" if known else "not_collected",
                        heart_rate_resting=UNKNOWN, read_authorization=UNKNOWN,
                        sleep_read_status="rows_returned" if has_sleep else UNKNOWN,
                        provenance=prov("ios.healthkit", "statistics_query", f"health:L{d + 1}"),
                        **day_bounds("ib-healthkit", d)))
    sleep_gaps = []
    if has_sleep:
        for d in range(DAYS):
            if sleep[d] is None:
                sleep_gaps.append((d, 18 * 60, 24 * 60 + 8 * 60))
                continue
            onset, dur = sleep[d]
            objs.append(rec(f"sleep-{d + 1:04d}",
                            "SleepInterval", "src-healthkit", "observation", "interval", sleep_source="watch",
                            stage="asleep",
                            provenance=prov("ios.healthkit", "sleep_analysis_query", f"sleep:L{d + 1}"),
                            **T("ib-healthkit", at(d, 18 * 60 + onset), at(d, 18 * 60 + onset + dur))))

    # -- calendar
    events = []

    def event(d: int, s: float, e: float, title: str, cal: str, place: str) -> None:
        ev = rec(f"cal-{len(events) + 1:04d}", "CalendarEvent", "src-eventkit", "observation", "interval", title=title,
                 calendar=cal, expected_place_id=place_ids[place], scheduled_duration_minutes=int(e - s),
                 observed_duration=UNKNOWN, role="scheduled_context", confirmed_by=[], possible_overlap_with=[],
                 provenance=prov("ios.eventkit", "event_query", f"events:L{len(events) + 1}"),
                 **T("ib-eventkit", at(d, s), at(d, e)))
        for vid, vd, vp, vs, ve in vmeta:
            if vd == d and vs < at(d, e) and at(d, s) < ve and vp == place:
                ev["possible_overlap_with"].append(vid)
        events.append(ev)

    team_days = (2,) if key == "commuter" else (0, 2)
    for d in range(DAYS):
        if d % 7 in team_days:
            event(d, 600, 630, "Team sync", "Work", "work")
        if d % 7 in (1, 3):
            event(d, 18 * 60, 19 * 60, "Gym session", "Personal", "gym")
    objs += events

    # -- apps and domains (identities only)
    for k, (name, cat, *_r) in APPS.items():
        objs.append(rec(f"app-{k}", "App", "src-apr", "observation", "not_applicable", bundle_id=f"com.example.{k}",
                        display_name=name, app_category=cat, provenance=prov("ios.app_privacy_report", "snapshot_import", f"app:{k}")))
    for k, host in DOMAINS.items():
        objs.append(rec(f"dom-{k}", "Domain", "src-apr", "observation", "not_applicable", host=host,
                        provenance=prov("ios.app_privacy_report", "snapshot_import", f"domain:{k}")))

    # -- screen time and notifications (absent, not zero, when the source is absent)
    if has_screen:
        n = m = 0
        for d in range(DAYS):
            for app, (_, cat, *_r) in APPS.items():
                s = screen[d][app]
                n += 1
                objs.append(rec(f"st-{n:04d}", "ScreenTimeDaily", "src-screentime", "observation", "aggregate",
                                app_id=f"app-{app}", app_category=cat, minutes=s["minutes"], pickups=s["pickups"],
                                late_night_minutes=s["late"], summable=False,
                                provenance=prov("ios.device_activity", "report_export", f"screentime:L{n}"),
                                **day_bounds("ib-screentime", d)))
            for app, cnt in screen[d]["notify"].items():
                m += 1
                objs.append(rec(f"nt-{m:04d}", "NotificationDaily", "src-screentime", "observation", "aggregate",
                                app_id=f"app-{app}", count=cnt,
                                provenance=prov("ios.device_activity", "report_export", f"notifications:L{m}"),
                                **day_bounds("ib-screentime", d)))

    # -- messaging: counts per pseudonymous contact only
    n = 0
    for d in range(DAYS):
        f = 1.0 if d % 7 < 5 else 1.2
        for contact, (sm, rm) in CONTACTS.items():
            sent = max(0, round(sm * f + R["msg"].gauss(0, sm ** 0.5 * 0.8)))
            recv = max(0, round(rm * f + R["msg"].gauss(0, rm ** 0.5 * 0.8)))
            if key == "social_drop" and contact == "contact-A" and d >= SOCIAL_DAY:
                sent = recv = 0
            n += 1
            objs.append(rec(f"msg-{n:04d}", "MessagingDaily", "src-messaging-export", "observation", "aggregate",
                            app_id="app-chat", contact_ref=contact, sent=sent, received=recv,
                            provenance=prov("example-chat-export", "daily_counts", f"messaging:L{n}"),
                            **day_bounds("ib-messaging-export", d)))

    # -- account activity (searches with derived topic labels, plus watch history)
    n = 0
    for d in range(DAYS):
        wk = d % 7 < 5
        n_search = max(0, round(R["acct"].gauss(3.6 if wk else 2.5, 1.6)))
        n_watch = max(0, round(R["acct"].gauss(1.5, 1.1)))
        p_sens = 0.40 if key == "search_drift" and d >= SEARCH_DAY else 0.10
        items: list[tuple[int, str, str, str, str]] = []
        for _ in range(n_search):
            minute = R["acct"].randrange(7 * 60, 23 * 60 + 30)
            u, pick, pick2 = R["acct"].random(), R["acct"].random(), R["acct"].random()
            if u < p_sens:
                topic = "sleep" if pick < 0.5 else "anxiety"
                cat, qs = SENSITIVE_QUERIES[topic]
            else:
                topic = list(NEUTRAL_QUERIES)[int(pick * len(NEUTRAL_QUERIES))]
                cat, qs = "none", NEUTRAL_QUERIES[topic]
            items.append((minute, "search", f"searched for '{qs[int(pick2 * len(qs))]}'", topic, cat))
        for _ in range(n_watch):
            minute = R["acct"].randrange(7 * 60, 23 * 60 + 30)
            items.append((minute, "watch", "", "", ""))
        for minute, kind, title, topic, cat in sorted(items):
            n += 1
            extra = ({"topic": topic, "topic_method": "keyword_lexicon_v0", "sensitive_category": cat}
                     if kind == "search" else {})
            objs.append(rec(f"acct-{n:04d}", "AccountActivity", "src-account-export", "observation", "point",
                            activity_kind=kind, title=title or f"watched 'Example Clip {n}'",
                            domain_id="dom-search" if kind == "search" else "dom-video", duration_seconds=UNKNOWN,
                            **extra, provenance=prov("example-account-export", "activity_json_import", f"activity.json#L{n}"),
                            **T("ib-account-export", at(d, minute))))

    # -- transactions (commuter only; optional participant-provided export)
    if has_tx:
        n, tx_misc = 0, R["misc"]

        def tx(d: int, minute: float, cat: str, amount: float, place: str) -> None:
            nonlocal n
            n += 1
            objs.append(rec(f"tx-{n:04d}", "Transaction", "src-transactions", "observation", "point",
                            merchant_category=cat, amount=amount, currency="EXC", place_id=place_ids[place],
                            provenance=prov("example-transaction-export", "csv_import", f"transactions.csv#L{n}"),
                            **T("ib-transactions", at(d, minute))))

        for d in range(DAYS):
            x = [tx_misc.random() for _ in range(4)]
            if attended[d]:
                tx(d, 515 + int(x[0] * 40), "parking", 12.5, "parking")
            if d % 7 == 4 and any(vp == "cafe" and vd == d for _, vd, vp, _, _ in vmeta):
                tx(d, 1100, "food_drink", round(4 + x[1] * 4, 2), "cafe")
            if d % 7 == 6 and any(vp == "grocery" and vd == d for _, vd, vp, _, _ in vmeta):
                tx(d, 700, "groceries", round(30 + x[2] * 50, 2), "grocery")

    # -- weather records
    for d in range(DAYS):
        w = weather[d]
        objs.append(rec(f"wx-{d + 1:04d}", "WeatherDaily", "src-weather", "observation", "aggregate",
                        precip_mm=w["precip"], temp_c_max=w["temp"], condition=w["cond"],
                        provenance=prov("example-public-weather", "daily_lookup", f"weather:L{d + 1}"),
                        **day_bounds("ib-weather", d)))
    objs += batches

    # -- sources (computed last)
    def stats(sid: str) -> dict[str, Any]:
        rs = [o for o in objs if o["source_id"] == sid and o["type"] in DATA_TYPES]
        ends = [o.get("event_end") or o.get("event_time") for o in rs]
        return {"record_count": len(rs), "latest_event_time": max(ends) if ends else UNKNOWN}

    def gap(d: int, s: int, e: int, kind: str, reason: str) -> dict[str, str]:
        return {"start": iso(at(d, s)), "end": iso(at(d, e)), "kind": kind, "reason": reason}

    unknown_step_days = [d for d in range(DAYS) if steps[d] == UNKNOWN]
    extras: dict[str, tuple[str, list[dict[str, str]], dict[str, Any]]] = {
        "src-location": ("partial" if any(loc_off) else "complete_in_window",
                         [gap(d, 0, 1440, "no_location_day", "location_off_by_participant_synthetic")
                          for d in range(DAYS) if loc_off[d]],
                         {"authorization": "authorized_always_synthetic_value"}),
        "src-motion": ("complete_in_window", [], {"authorization": "authorized_synthetic_value",
                                                  "history_depth_limit": UNKNOWN}),
        "src-healthkit": ("partial", [gap(d, 0, 1440, "no_step_record", "not_collected_cause_unknown")
                                      for d in unknown_step_days]
                          + [gap(d, 18 * 60, 32 * 60, "no_sleep_record", "not_collected_cause_unknown")
                             for d, _, _ in sleep_gaps],
                          {"read_authorization": UNKNOWN, "aggregation": "sum_over_local_day", "producers": UNKNOWN,
                           "sleep_read_status": "rows_returned" if has_sleep else UNKNOWN,
                           "signals": {"steps": "partial", "heart_rate": "unavailable_no_producer_or_unknown",
                                       "sleep": "partial" if has_sleep else "unavailable_no_producer_or_unknown"}}),
        "src-eventkit": ("complete_in_window", [], {"authorization": "full_access_synthetic_value"}),
        "src-apr": ("complete_in_window", [], {}),
        "src-screentime": ("complete_in_window", [], {"authorization": "family_controls_synthetic_value"}),
        "src-account-export": ("complete_in_window", [], {"fields_unavailable": ["duration", "scroll_depth",
                                                                                 "viewed_content_detail"]}),
        "src-messaging-export": ("complete_in_window", [], {"fields_unavailable": ["names", "content"]}),
        "src-transactions": ("complete_in_window", [], {}),
        "src-weather": ("complete_in_window", [], {}),
        "src-workspace": ("not_applicable", [], {}),
    }
    sources = []
    for sid, (name, system, status, availability) in SOURCES.items():
        if (sid == "src-screentime" and not has_screen) or (sid == "src-transactions" and not has_tx):
            continue
        cov, missing, extra = extras[sid]
        sources.append(rec(sid, "Source", sid, "observation", "not_applicable", name=name, system=system,
                           support="supported_synthetic", provisioning="not_applicable_synthetic",
                           real_world_status=status, availability=availability, coverage_status=cov,
                           source_granularity="aggregate" if sid in ("src-healthkit", "src-screentime", "src-messaging-export",
                                                                     "src-weather") else "interval",
                           missing_periods=missing, export_success="synthetic_fixture_ok", **stats(sid), **extra,
                           provenance=prov("synthetic-profile", "source_summary", sid)))

    records = sources + objs + links
    counts: dict[str, int] = {}
    for r in records:
        counts[r["type"]] = counts.get(r["type"], 0) + 1
    meta = {
        "contract_version": CONTRACT_VERSION, "status": "PROVISIONAL demonstration data; NOT a production schema",
        "synthetic": True, "subject": f"Subject {SUBJECTS[key]} (fictitious; no real person)", "workspace_id": ws,
        "profile": key, "profile_description": DESCRIPTIONS[key],
        "city": "Port Meridian (fictional)", "bounding_box": BBOX, "coordinates_fictitious": True,
        "timezone": TZ_NAME, "window": window, "seed": seed, "type_counts": counts,
        "unknown_token": UNKNOWN, "evidence_classes": list(EVIDENCE_CLASSES),
        "notice": "All names, coordinates, identifiers and numbers are invented. Not an anonymization example.",
    }
    rainy_office = [d for d in range(DAYS) if (d % 7 in (1, 2, 3)) and weather[d]["precip"] >= RAIN_MM]
    internal = {"rainy_planned_office_days": rainy_office,
                "rainy_office_days_skipped": [d for d in rainy_office if not attended[d]],
                "location_off_days": [d for d in range(DAYS) if loc_off[d]],
                "unknown_step_days": unknown_step_days}
    return {"meta": meta, "records": records}, internal


def build(key: str) -> dict[str, Any]:
    """Return {meta, records} for one profile; deterministic."""
    return _generate(key)[0]


_TRUTH: dict[str, dict[str, Any]] = {
    "steady": {
        "planted_changes": [], "planted_lags": [], "planted_contexts": [],
        "expected_absent": ["any shift finding at the declared level (null control)", "any lagged association"],
        "expected_present": ["routine findings (weekday office visits)"],
    },
    "doomscroll": {
        "planted_changes": [
            {"metric": "short_video_minutes", "change_day": DOOM_DAY, "direction": "up", "approx_ratio": 2.5},
            {"metric": "late_night_minutes", "change_day": DOOM_DAY, "direction": "up", "approx_from": 4, "approx_to": 50},
            {"metric": "total_screen_minutes", "change_day": DOOM_DAY, "direction": "up", "approx_ratio": 1.4},
            {"metric": "pickups", "change_day": DOOM_DAY, "direction": "up", "approx_ratio": 1.4},
            {"metric": "sleep_onset", "change_day": DOOM_DAY, "direction": "up", "approx_delta_minutes": 70},
            {"metric": "sleep_duration", "change_day": DOOM_DAY, "direction": "down", "approx_delta_minutes": -70},
            {"metric": "steps", "change_day": DOOM_DAY, "direction": "down", "approx_ratio": 0.7},
        ],
        "planted_lags": [{"x_metric": "late_night_minutes", "y_metric": "steps", "lag_days": 1, "direction": "negative"}],
        "planted_contexts": [],
        "expected_absent": ["shift in messages with any contact", "shift in office_visits",
                            "shift in notifications", "shift in searches_sensitive_share"],
        "expected_present": ["observer inference: possible sleep deprivation and lower activity (could, not did)"],
    },
    "social_drop": {
        "planted_changes": [
            {"metric": "messages_contact_A", "change_day": SOCIAL_DAY, "direction": "down", "approx_to": 0},
            {"metric": "minutes_away_from_home", "change_day": SOCIAL_DAY, "direction": "down", "approx_ratio": 0.8,
             "note": "evening outings drop; weaker and noisier than the messaging change"},
        ],
        "planted_lags": [], "planted_contexts": [],
        "expected_absent": ["shift in messages_contact_B", "shift in messages_contact_C", "shift in short_video_minutes",
                            "shift in sleep_onset", "shift in office_visits"],
        "expected_present": ["hypothesis only: possible change in one relationship, with alternatives; "
                             "total messages shifts as a consequence of contact-A"],
    },
    "search_drift": {
        "planted_changes": [
            {"metric": "searches_sensitive_share", "change_day": SEARCH_DAY, "direction": "up",
             "approx_from": 0.10, "approx_to": 0.40, "note": "sleep and anxiety topics; total searches per day unchanged"},
        ],
        "planted_lags": [], "planted_contexts": [],
        "expected_absent": ["shift in steps, screen time, sleep, messaging or places"],
        "expected_present": ["sensitive observer inference worded as topic interest, shown in own workspace only"],
    },
    "commuter": {
        "planted_changes": [],
        "planted_lags": [],
        "planted_contexts": [
            {"context": "rain", "outcome": "office_attendance", "rule": "rainy planned office day (precip >= "
             f"{RAIN_MM} mm): stays home with probability {RAIN_STAYS_HOME}; dry days: attends", "direction": "negative"},
            {"routine": "office on Tue/Wed/Thu with a parking Transaction on each attended office day"},
        ],
        "expected_absent": ["any shift finding at the declared level (no planted change)"],
        "expected_present": ["routine: office days", "context: rain then stays home", "observer inference: commuter, parking spend"],
    },
    "sparse": {
        "planted_changes": [], "planted_lags": [], "planted_contexts": [],
        "expected_absent": ["any fabricated shift", "any finding computed from sleep or Screen Time (no such source)",
                            "zero-filled values for unknown steps or location-off days"],
        "expected_present": ["insufficient findings for sleep and Screen Time metrics"],
    },
}


def scenario_truth(key: str) -> dict[str, Any]:
    """Hidden scenario truth for tests and scoring only; never placed in a workspace document."""
    if key not in PROFILES:
        raise ValueError(f"unknown profile {key!r}")
    truth = json.loads(json.dumps(_TRUTH[key]))
    truth.update(key=key, workspace_id=WORKSPACES[key], days=DAYS, start_day_of_week="Monday")
    truth["realized"] = _generate(key)[1]
    return truth


def dumps(doc: dict[str, Any]) -> str:
    return json.dumps(doc, separators=(",", ":"), ensure_ascii=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate the six synthetic 0.2 profiles (demo data only).")
    ap.add_argument("--summary", action="store_true", help="print per-profile type counts and document size")
    args = ap.parse_args(argv)
    if not args.summary:
        ap.print_help()
        return 0
    for key in PROFILES:
        doc = build(key)
        print(json.dumps({"profile": key, "workspace_id": doc["meta"]["workspace_id"],
                          "bytes": len(dumps(doc).encode()), "type_counts": doc["meta"]["type_counts"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
