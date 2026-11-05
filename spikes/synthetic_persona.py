"""Deterministic SYNTHETIC demo participant ("Subject EX-01") for an explorer concept prototype.

Everything here is invented: a fictional city ("Port Meridian") placed at fictitious
coordinates over open ocean, com.example.* identifiers, *.example domains. This is
demonstration data and a PROVISIONAL explorer data contract, NOT a production schema,
storage design, or evidence about any real person or device. See synthetic-persona.md.

Standard library only, seeded RNG, identical output on every run, no I/O except --out.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import random
from typing import Any

UNKNOWN = "unknown"  # Unmeasured value; never substitute 0.
WS = "ws-demo-01"
SEED = 20260302
CONTRACT_VERSION = "persona-contract-0.1-provisional"
TZ_NAME = "Etc/GMT+5"  # fixed UTC-05:00, no daylight saving; chosen for determinism
TZ = timezone(timedelta(hours=-5))
START = datetime(2026, 3, 2, tzinfo=TZ)  # a Monday
DAYS = 28
EVIDENCE_CLASSES = ("observation", "normalized_event", "hypothesis", "inference", "prediction")
GRANULARITIES = ("point", "interval", "aggregate", "not_applicable")
# Fictitious bounding box in the open Atlantic; no real address or settlement is implied.
BBOX = {"lat_min": 30.00, "lat_max": 30.06, "lon_min": -40.06, "lon_max": -40.00}
NO_LOCATION_DAY = 9          # participant switched location off all day (Mon 2026-03-02 + 9 = Wed)
GAP_DAY, GAP_START, GAP_END = 17, 13 * 60, 16 * 60 + 30  # locked-phone background gap
NO_STEPS_DAY = 20            # no step record collected; unknown, not zero
SNAPSHOTS = {  # id -> (first_day, last_day_inclusive, import_day, import_minute)
    "s1": (0, 9, 10, 9 * 60), "s2": (6, 17, 18, 9 * 60), "s3": (20, 27, 28, 8 * 60 + 30),
}
DEVICE_IMPORT = (28, 8 * 60)
ACCOUNT_IMPORT = (28, 9 * 60)

PLACES = {
    "home": ("Home (fictional)", 30.020, -40.030), "work": ("Work office (fictional)", 30.040, -40.010),
    "gym": ("Gym (fictional)", 30.032, -40.020), "cafe": ("Corner cafe (fictional)", 30.036, -40.012),
    "park": ("Meridian Park (fictional)", 30.012, -40.045), "grocery": ("Grocery (fictional)", 30.025, -40.038),
}
APPS = {
    "mail": "Example Mail", "maps": "Example Maps", "video": "Example Video", "social": "Example Social",
    "notes": "Example Notes", "news": "Example News", "fitlog": "Example FitLog",
}
DOMAINS = {
    "mail": "api.mail.example", "tiles": "tiles.maps.example", "video": "cdn.video.example",
    "search": "search.video.example", "ads": "ads.tracker.example", "social": "graph.social.example",
    "news": "feed.news.example", "fit": "sync.fitlog.example",
}
NET_PAIRS = [("mail", "mail", 40), ("maps", "tiles", 90), ("video", "video", 160), ("video", "ads", 55),
             ("social", "social", 70), ("social", "ads", 45)]
ACCESS_CATEGORIES = ("location", "camera", "microphone", "photos", "contacts")
ACCESS_APPS = {"location": ("maps", "fitlog", "social"), "camera": ("social", "notes"),
               "microphone": ("social", "video"), "photos": ("social", "notes"), "contacts": ("mail", "social")}


def at(day: int, minute: float) -> datetime:
    return START + timedelta(days=day, minutes=minute)


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="minutes")


def rec(rid: str, typ: str, source_id: str, evidence_class: str, granularity: str, **fields: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"id": rid, "type": typ, "workspace_id": WS, "source_id": source_id,
                           "evidence_class": evidence_class}
    if granularity != "not_applicable":  # omitted for entities and links that have no time granularity
        out["granularity"] = granularity
    out.update(fields)
    return out


def prov(source: str, method: str, version: str, where: str) -> dict[str, str]:
    return {"source": source, "method": method, "method_version": version, "line_or_record": where}


def timing(batch: str, imported: datetime, start: datetime, end: datetime | None = None) -> dict[str, Any]:
    t: dict[str, Any] = {"import_batch_id": batch, "timezone": TZ_NAME}
    if end is None:
        t["event_time"] = iso(start)
    else:
        t["event_start"], t["event_end"] = iso(start), iso(end)
    return t


def km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return math.hypot((lat2 - lat1) * 111.2, (lon2 - lon1) * 111.2 * math.cos(math.radians(lat1)))


# --- plan ------------------------------------------------------------------------

def plan_day(day: int, rng: random.Random) -> list[dict[str, Any]]:
    """Ground-truth movement plan for a day: stays and trips in minutes after local midnight."""
    dow, segs, gym_day = day % 7, [], day % 7 in (1, 3)

    def stay(place: str, s: float, e: float) -> None:
        segs.append({"kind": "stay", "place": place, "s": s, "e": e})

    def trip(a: str, b: str, s: float, mins: float, mode: str) -> float:
        segs.append({"kind": "trip", "from": a, "to": b, "s": s, "e": s + mins, "mode": mode})
        return s + mins

    if dow < 5:
        leave = 8 * 60 + rng.randrange(10, 50)
        t = trip("home", "work", leave, rng.randrange(18, 35), rng.choice(["transit", "transit", "walk", "cycle"]))
        stay("home", 0, leave)
        lunch = False  # no lunch outing in this persona (size budget)
        leave_work = 17 * 60 + rng.randrange(0, 40)
        if lunch:
            stay("work", t, 12 * 60 + 10)
            t = trip("work", "cafe", 12 * 60 + 10, 6, "walk")
            stay("cafe", t, 12 * 60 + 56)
            t = trip("cafe", "work", 12 * 60 + 56, 6, "walk")
        stay("work", t, leave_work)
        if gym_day:
            t = trip("work", "gym", leave_work, rng.randrange(10, 16), rng.choice(["walk", "transit"]))
            end = t + rng.randrange(55, 80)
            stay("gym", t, end)
            t = trip("gym", "home", end, rng.randrange(15, 26), "transit")
        else:
            t = trip("work", "home", leave_work, rng.randrange(18, 35), rng.choice(["transit", "walk"]))
        stay("home", t, 1440)
    elif dow == 5:
        stay("home", 0, 10 * 60 + 15)
        t = trip("home", "park", 10 * 60 + 15, 15, "walk")
        stay("park", t, 12 * 60)
        t = trip("park", "cafe", 12 * 60, 12, "walk")
        stay("cafe", t, 13 * 60 + 30)
        t = trip("cafe", "home", 13 * 60 + 30, 22, "walk")
        stay("home", t, 1440)
    else:
        if day % 14 == 6:
            stay("home", 0, 11 * 60)
            t = trip("home", "grocery", 11 * 60, 12, "walk")
            stay("grocery", t, 11 * 60 + 55)
            t = trip("grocery", "home", 11 * 60 + 55, 12, "walk")
            stay("home", t, 1440)
        else:
            stay("home", 0, 1440)
    return segs


def in_gap(day: int, minute: float) -> bool:
    return day == NO_LOCATION_DAY or (day == GAP_DAY and GAP_START <= minute < GAP_END)


def is_evening(a: dict[str, Any]) -> bool:
    """Evening = local time 20:00 or later (text compare on the ISO time part)."""
    return a["event_time"][11:16] >= "20:00"


def spearman(x: list[float], y: list[float]) -> float:
    def ranks(v: list[float]) -> list[float]:
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return r

    a, b = ranks(x), ranks(y)
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    den = math.sqrt(sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b))
    return num / den if den else 0.0


# --- build -----------------------------------------------------------------------

def build() -> dict[str, Any]:
    r_plan, r_loc, r_mot = random.Random(SEED), random.Random(SEED + 1), random.Random(SEED + 2)
    r_health, r_acct, r_apr = random.Random(SEED + 3), random.Random(SEED + 4), random.Random(SEED + 5)
    dev_import = at(*DEVICE_IMPORT)
    objs: list[dict[str, Any]] = []
    links: list[dict[str, Any]] = []
    link_n = [0]

    def link(kind: str, a: str, b: str, evidence: list[str], source_id: str, ev: str = "normalized_event",
             **extra: Any) -> None:
        link_n[0] += 1
        links.append(rec(f"link-{link_n[0]:04d}", "Link", source_id, ev, "not_applicable",
                         link_type=kind, **{"from": a, "to": b}, evidence_ids=evidence, **extra))

    # import batches
    batches = []

    def batch(bid: str, source_id: str, when: datetime, label: str, **extra: Any) -> None:
        digest = hashlib.sha256(f"synthetic-content::{label}".encode()).hexdigest()
        batches.append(rec(bid, "ImportBatch", source_id, "observation", "not_applicable",
                           import_time=iso(when), timezone=TZ_NAME, content_digest_sha256=digest,
                           status="imported", duplicate_of=None, records_added=None,
                           provenance=prov("synthetic-fixture", "batch_import", "0.1", label), **extra))

    for sid, label in (("location", "loc"), ("motion", "mot"), ("healthkit", "hk"), ("eventkit", "ek")):
        batch(f"ib-{sid}", f"src-{sid}", dev_import, f"{label}-batch")
    for snap, (d0, d1, imp_d, imp_m) in SNAPSHOTS.items():
        batch(f"ib-apr-{snap}", "src-apr", at(imp_d, imp_m), f"apr-{snap}",
              window_start=iso(at(d0, 0)), window_end=iso(at(d1 + 1, 0)))
    dup = dict(next(b for b in batches if b["id"] == "ib-apr-s2"))
    dup.update(id="ib-apr-s2-again", import_time=iso(at(19, 10 * 60)), status="duplicate_skipped",
               duplicate_of="ib-apr-s2", records_added=0)
    batches.append(dup)
    batch("ib-account", "src-account-export", at(*ACCOUNT_IMPORT), "account-export-1")
    link("DUPLICATE_OF", "ib-apr-s2-again", "ib-apr-s2", ["ib-apr-s2-again", "ib-apr-s2"], "src-apr", "observation")
    batch_time = {b["id"]: b["import_time"] for b in batches}

    def T(batch_id: str, start: datetime, end: datetime | None = None) -> dict[str, Any]:
        t = timing(batch_id, datetime.fromisoformat(batch_time[batch_id]), start, end)
        return t

    # places
    place_ids = {}
    for key, (name, lat, lon) in PLACES.items():
        place_ids[key] = f"place-{key}"
        objs.append(rec(f"place-{key}", "Place", "src-location", "inference", "not_applicable",
                        label=name, category=key, lat=lat, lon=lon, radius_m=80, coordinates_fictitious=True,
                        label_basis="synthetic_assignment", confidence="high",
                        provenance=prov("synthetic-persona", "assigned_label", "0.1", f"place:{key}")))

    # movement, samples, visits, trips, motion
    samples, visits, trips, motion, gym_days, loc_n = [], [], [], [], [], [0]
    visit_day: dict[str, int] = {}
    for day in range(DAYS):
        prev_last, pending = None, None  # a Trip is evidenced by the neighbouring Visits' samples
        for idx, seg in enumerate(plan_day(day, r_plan)):
            seg_samples = []
            if seg["kind"] == "stay":
                lat0, lon0 = PLACES[seg["place"]][1:]
                lo_m, hi_m = int(seg["s"]) + (30 if seg["place"] == "home" else 2), int(seg["e"]) - (10 if seg["place"] == "home" else 2)
                minutes = [lo_m, hi_m] if seg["place"] != "home" else ([] if seg["s"] == 0 and seg["e"] < 1440 else [lo_m])
                minutes = list(dict.fromkeys(minutes))
            else:
                minutes = []
            for m in minutes:
                if in_gap(day, m):
                    continue
                lat, lon = lat0, lon0
                acc = r_loc.choice([8, 12, 20, 35, 65, 120])
                lat += r_loc.gauss(0, acc / 111000)
                lon += r_loc.gauss(0, acc / 111000)
                loc_n[0] += 1
                s = rec(f"loc-{loc_n[0]:04d}", "LocationSample", "src-location", "observation", "point",
                        lat=round(lat, 5), lon=round(lon, 5), accuracy_m=acc,
                        provenance=prov("ios.core_location", "probe_export", "0.1", f"locations.jsonl:L{loc_n[0]}"),
                        **T("ib-location", at(day, m)))
                samples.append(s)
                seg_samples.append(s)
            if seg["kind"] == "stay" and seg_samples:
                first, last = seg_samples[0], seg_samples[-1]
                gapped = day == GAP_DAY and seg["place"] == "work"
                mean_acc = sum(s["accuracy_m"] for s in seg_samples) / len(seg_samples)
                v = rec(f"visit-{len(visits) + 1:04d}", "Visit", "src-location", "normalized_event", "interval",
                        place_id=place_ids[seg["place"]],
                        interrupted_by_gap=gapped, match_confidence="high" if mean_acc < 50 else "medium",
                        provenance=prov("derived", "dwell_from_samples", "0.1", f"day{day}:seg{idx}"),
                        **T("ib-location", datetime.fromisoformat(first["event_time"]),
                            datetime.fromisoformat(last["event_time"])))
                visits.append(v)
                visit_day[v["id"]] = day
                link("VISITED", v["id"], place_ids[seg["place"]], [s["id"] for s in seg_samples], "src-location", "inference")
                if seg["place"] == "gym":
                    gym_days.append(day)
                if pending is not None:
                    a, conf, tseg, tidx = pending
                    t = rec(f"trip-{len(trips) + 1:04d}", "Trip", "src-location", "normalized_event", "interval",
                            from_place_id=place_ids[tseg["from"]], to_place_id=place_ids[tseg["to"]],
                            mode=tseg["mode"], mode_confidence=conf,
                            provenance=prov("derived", "trip_between_visits", "0.1", f"day{day}:seg{tidx}"),
                            **T("ib-location", at(day, tseg["s"]), at(day, tseg["e"])))
                    trips.append(t)
                    link("CORROBORATED_BY", t["id"], a["id"], [t["id"], a["id"]] + ([prev_last["id"]] if prev_last else []) + [first["id"]],
                         "src-motion", "normalized_event")
            if seg["kind"] == "stay":
                prev_last, pending = (seg_samples[-1] if seg_samples else None), None
            if seg["kind"] == "trip":
                # Core Motion runs regardless of location availability.
                mtype = {"walk": "walking", "cycle": "cycling", "transit": "automotive"}[seg["mode"]]
                conf = r_mot.choices(["high", "medium", "low"], [5, 3, 1])[0]
                ms, me = seg["s"] + r_mot.randrange(0, 2), seg["e"] - r_mot.randrange(0, 2)
                a = rec(f"act-{len(motion) + 1:04d}", "ActivityInterval", "src-motion", "observation", "interval",
                        activity_type=mtype, confidence=conf,
                        provenance=prov("ios.core_motion", "activity_query", "0.1", f"motion.jsonl:L{len(motion) + 1}"),
                        **T("ib-motion", at(day, ms), at(day, me)))
                motion.append(a)
                pending = (a, conf, seg, idx)
    objs += samples + visits + trips + motion

    # health: daily steps aggregates; heart rate and sleep have no producer -> unknown
    health, steps_by_day = [], {}
    for day in range(DAYS):
        dow = day % 7
        steps = int(4200 + (1500 if dow < 5 else 0) + (2500 if dow == 5 else 0)
                    + r_health.gauss(0, 900))
        steps = max(steps, 1200)
        known = day != NO_STEPS_DAY
        steps_by_day[day] = steps if known else None
        h = rec(f"health-{day + 1:04d}", "DailyHealthAggregate", "src-healthkit", "observation", "aggregate",
                steps=steps if known else UNKNOWN, steps_status="measured" if known else "not_collected",
                heart_rate_resting=UNKNOWN, sleep_duration=UNKNOWN,
                read_authorization=UNKNOWN,
                provenance=prov("ios.healthkit", "statistics_query", "0.1", f"health.jsonl:L{day + 1}"),
                **T("ib-healthkit", at(day, 0), at(day + 1, 0)))
        health.append(h)
    objs += health

    # calendar: scheduled context; confirmed only by an explicit link
    events = []

    def event(day: int, s: float, e: float, title: str, cal: str, place: str | None) -> None:
        events.append(rec(f"cal-{len(events) + 1:04d}", "CalendarEvent", "src-eventkit", "observation", "interval",
                          title=title, calendar=cal, expected_place_id=place_ids.get(place) if place else None,
                          scheduled_duration_minutes=int(e - s), observed_duration=UNKNOWN,
                          role="scheduled_context", confirmed_by=[], possible_overlap_with=[],
                          provenance=prov("ios.eventkit", "event_query", "0.1", f"events.jsonl:L{len(events) + 1}"),
                          import_batch_id="ib-eventkit", timezone=TZ_NAME,
                          event_start=iso(at(day, s)), event_end=iso(at(day, e))))
        events[-1]["_day"], events[-1]["_place"] = day, place

    for day in range(DAYS):
        dow = day % 7
        if dow in (0, 2):
            event(day, 600, 630, "Team sync", "Work", "work")
        if dow in (1, 3):
            event(day, 18 * 60, 19 * 60, "Gym session", "Personal", "gym")
    event(14, 14 * 60, 15 * 60, "Appointment (offsite)", "Personal", None)
    for e in events:
        day, place = e.pop("_day"), e.pop("_place")
        es, ee = datetime.fromisoformat(e["event_start"]), datetime.fromisoformat(e["event_end"])
        for v in visits:
            if visit_day[v["id"]] != day:
                continue
            vs, ve = datetime.fromisoformat(v["event_start"]), datetime.fromisoformat(v["event_end"])
            if vs < ee and es < ve:
                if place == "gym" and v["place_id"] == place_ids["gym"]:
                    e["confirmed_by"].append(v["id"])
                    link("CONFIRMS", v["id"], e["id"], [v["id"], e["id"]], "src-eventkit", "normalized_event",
                         basis="explicit_checkin_link_synthetic")
                else:
                    e["possible_overlap_with"].append(v["id"])
        if e["confirmed_by"]:
            e["role"] = "observed_activity"
    objs += events

    # apps, domains
    for k, name in APPS.items():
        objs.append(rec(f"app-{k}", "App", "src-apr", "observation", "not_applicable", bundle_id=f"com.example.{k}",
                        display_name=name, provenance=prov("ios.app_privacy_report", "snapshot_import", "0.1", f"app:{k}")))
    for k, host in DOMAINS.items():
        objs.append(rec(f"dom-{k}", "Domain", "src-apr", "observation", "not_applicable", host=host,
                        provenance=prov("ios.app_privacy_report", "snapshot_import", "0.1", f"domain:{k}")))

    # resource access intervals (deduplicated across overlapping snapshots)
    snaps_for_day = {d: [s for s, (a, b, _, _) in SNAPSHOTS.items() if a <= d <= b] for d in range(DAYS)}
    access = []
    for day in range(DAYS):
        covering = snaps_for_day[day]
        if not covering:
            continue
        for _ in range(r_apr.randrange(0, 2)):
            cat = r_apr.choice(ACCESS_CATEGORIES)
            app = r_apr.choice(ACCESS_APPS[cat])
            s = r_apr.randrange(7 * 60, 22 * 60)
            dur = r_apr.randrange(1, 20)
            endpoint = r_apr.random() < 0.7
            dom = r_apr.choice(list(DOMAINS)) if endpoint else None
            n = len(access) + 1
            a = rec(f"access-{n:04d}", "ResourceAccess", "src-apr", "observation", "interval",
                    app_id=f"app-{app}", category=cat, endpoint_domain_id=f"dom-{dom}" if dom else None,
                    endpoint_match="matched" if dom else "unmatched",
                    **({} if dom else {"endpoint_label": "unlisted-endpoint.example"}),
                    **({"also_seen_in_snapshots": [f"ib-apr-{c}" for c in covering[1:]]} if len(covering) > 1 else {}),
                    provenance=prov("ios.app_privacy_report", "paired_access_events", "0.1",
                                    f"{covering[0]}.ndjson:L{n}"),
                    **T(f"ib-apr-{covering[0]}", at(day, s), at(day, s + dur)))
            access.append(a)
            link("ACCESSED_BY", a["id"], a["app_id"], [a["id"]], "src-apr", "observation")
    objs += access

    # per-snapshot network aggregates: overlapping windows, never summed
    nets = []
    for snap, (d0, d1, _, _) in SNAPSHOTS.items():
        span = d1 - d0 + 1
        for app, dom, rate in NET_PAIRS:
            hits = int(rate * span * r_apr.uniform(0.7, 1.3))
            n = rec(f"net-{snap}-{len(nets) % len(NET_PAIRS) + 1:02d}", "NetworkAggregate", "src-apr", "observation",
                    "aggregate", app_id=f"app-{app}", domain_id=f"dom-{dom}", hits=hits, snapshot_id=f"ib-apr-{snap}",
                    summable=False,
                    provenance=prov("ios.app_privacy_report", "snapshot_counter", "0.1",
                                    f"{snap}.ndjson:network:{len(nets) % len(NET_PAIRS) + 1}"),
                    **T(f"ib-apr-{snap}", at(d0, 0), at(d1 + 1, 0)))
            nets.append(n)
    objs += nets
    for app, dom, _ in NET_PAIRS:  # one App -> Domain link per pair; per-snapshot totals stay separate
        ids = [n["id"] for n in nets if n["app_id"] == f"app-{app}" and n["domain_id"] == f"dom-{dom}"]
        link("CONTACTED", f"app-{app}", f"dom-{dom}", ids, "src-apr", "observation", combine="latest_snapshot_only_never_sum")

    # account activity: instant records, no duration in source
    drafts = []
    for day in range(DAYS):
        s = steps_by_day[day] if steps_by_day[day] is not None else 6000
        n_eve = max(0, round(0.1 - (s - 6000) / 1300 + r_acct.gauss(0, 1.8)))
        times = [r_acct.randrange(20 * 60, 23 * 60 + 40) for _ in range(n_eve)]
        times += [r_acct.randrange(7 * 60, 19 * 60) for _ in range(1 if day % 4 == 1 else 0)]
        for m in times:
            drafts.append((day, m, r_acct.choices(["watch", "search", "like"], [5, 4, 2])[0]))
    drafts.sort()
    for n, (day, m, kind) in enumerate(drafts, 1):
        title = {"watch": f"watched 'Example Clip {n}'", "search": f"searched for 'sample query {n}'",
                 "like": f"liked 'Example Clip {n}'"}[kind]
        objs.append(rec(f"acct-{n:04d}", "AccountActivity", "src-account-export", "observation", "point",
                        activity_kind=kind, title=title, domain_id="dom-search" if kind == "search" else "dom-video",
                        duration_seconds=UNKNOWN,
                        provenance=prov("example-account-export", "activity_json_import", "0.1", f"activity.json#L{n}"),
                        **T("ib-account", at(day, m))))
    acct = [o for o in objs if o["type"] == "AccountActivity"]

    # findings
    created = iso(at(28, 12 * 60))
    known_days = [d for d in range(DAYS) if steps_by_day[d] is not None]
    eve_count = {d: sum(1 for a in acct if is_evening(a) and a["event_time"][:10] == iso(at(d, 0))[:10]) for d in range(DAYS)}
    window = {"start": iso(at(0, 0)), "end": iso(at(DAYS, 0))}

    # F1 descriptive routine
    first_work, wk_days = {}, [d for d in range(DAYS) if d % 7 < 5]
    for v in visits:
        if v["place_id"] == place_ids["work"] and visit_day[v["id"]] % 7 < 5 and visit_day[v["id"]] not in first_work:
            first_work[visit_day[v["id"]]] = v
    def mins(v: dict[str, Any]) -> int:
        dt = datetime.fromisoformat(v["event_start"])
        return dt.hour * 60 + dt.minute
    inside = [v for v in first_work.values() if 8 * 60 + 30 <= mins(v) <= 9 * 60]
    outside = [v for v in first_work.values() if v not in inside]
    no_loc_wk = [d for d in wk_days if d not in first_work]
    med = sorted(mins(v) for v in first_work.values())[len(first_work) // 2]
    f1 = rec("finding-0001", "Finding", "src-workspace", "inference", "not_applicable", finding_kind="descriptive_pattern",
             statement=f"On {len(inside)} of {len(first_work)} weekdays with location coverage, the first Work visit began "
                       f"between 08:30 and 09:00 (median {med // 60:02d}:{med % 60:02d}).",
             input_window=window, method="window_count", method_version="0.1",
             statistic={"name": "share_in_window", "value": round(len(inside) / len(first_work), 3), "n": len(first_work)},
             excluded_unknown_days=no_loc_wk, supporting_evidence_ids=[v["id"] for v in inside],
             contradicting_evidence_ids=[v["id"] for v in outside], causal_claim=False,
             uncertainty="Visit start is the first sample, an upper bound on arrival; sparse sampling widens it.",
             confidence={"level": "medium", "basis": "visit_start_bounds"}, status="descriptive",
             participant_correction="cor-0001", participant_review_status="corrected", created_at=created)

    # F2 correlation
    xs = [float(steps_by_day[d]) for d in known_days]
    ys = [float(eve_count[d]) for d in known_days]
    rho, n = spearman(xs, ys), len(known_days)
    z, se = math.atanh(max(-0.999, min(0.999, rho))), 1 / math.sqrt(n - 3)
    ci = [round(math.tanh(z - 1.96 * se), 2), round(math.tanh(z + 1.96 * se), 2)]
    med_s, med_e = sorted(xs)[n // 2], sorted(ys)[n // 2]
    contra = [f"health-{d + 1:04d}" for d in known_days if steps_by_day[d] > med_s and eve_count[d] >= med_e]
    f2 = rec("finding-0002", "Finding", "src-workspace", "inference", "not_applicable", finding_kind="correlation",
             statement=f"CORRELATION, not causation: days with fewer steps tended to have more evening (20:00 onward) "
                       f"account-activity records (Spearman rho = {rho:.2f}, n = {n} days, approx. 95% CI {ci[0]} to {ci[1]}).",
             input_window=window, method="spearman_rank_correlation", method_version="0.1",
             statistic={"name": "spearman_rho", "value": round(rho, 3), "n": n, "ci95_approx": ci,
                        "ci_method": "fisher_z_ignores_ties_and_autocorrelation"},
             supporting_evidence_ids=[f"health-{d + 1:04d}" for d in known_days]
                                     + [a["id"] for a in acct if is_evening(a)],
             contradicting_evidence_ids=contra, causal_claim=False,
             alternative_explanations=["weekday versus weekend routine", "gym days", "unobserved factors (weather, mood)"],
             uncertainty="Small sample of daily values from one synthetic subject; one of several exploratory comparisons "
                         "and not corrected for multiplicity; the dependence was built into the synthetic generator.",
             confidence={"level": "low", "basis": "n=27_exploratory"}, status="exploratory",
             participant_correction=None, participant_review_status="unreviewed", created_at=created)

    # F3 hypothesis awaiting evidence
    f3 = rec("finding-0003", "Finding", "src-workspace", "hypothesis", "not_applicable", finding_kind="hypothesis",
             statement="Late-evening account activity might be followed by shorter sleep.",
             input_window=window, method="analyst_suggestion", method_version="0.1",
             motivated_by_ids=["finding-0002"], supporting_evidence_ids=[], contradicting_evidence_ids=[],
             needs_evidence=["sleep records; no producer observed in this persona, so the test cannot run yet"],
             causal_claim=False, uncertainty="Untested; not evidence of anything.",
             confidence={"level": "none", "basis": "no_evidence"}, status="awaiting_evidence",
             participant_correction=None, participant_review_status="unreviewed", created_at=created)

    # F4 null / insufficient evidence
    after_gym = {d + 1 for d in gym_days if d + 1 < DAYS}
    g1 = [steps_by_day[d] for d in known_days if d in after_gym and d % 7 < 5]
    g2 = [steps_by_day[d] for d in known_days if d not in after_gym and d % 7 < 5]
    diff = sum(g1) / len(g1) - sum(g2) / len(g2)
    pr, hits = random.Random(7), 0
    pool = g1 + g2
    for _ in range(2000):
        pr.shuffle(pool)
        hits += abs(sum(pool[:len(g1)]) / len(g1) - sum(pool[len(g1):]) / len(g2)) >= abs(diff)
    p = (hits + 1) / 2001
    f4 = rec("finding-0004", "Finding", "src-workspace", "inference", "not_applicable", finding_kind="null_or_insufficient",
             statement=f"No conclusion: weekday steps on days after a gym visit differ from other weekdays by "
                       f"{diff:+.0f} steps (n = {len(g1)} vs {len(g2)}; permutation p = {p:.2f}); evidence is insufficient "
                       f"(rule: at least 15 days per group).",
             input_window=window, method="permutation_difference_in_means", method_version="0.1",
             statistic={"name": "mean_difference_steps", "value": round(diff), "n_groups": [len(g1), len(g2)],
                        "permutation_p": round(p, 3), "permutations": 2000, "min_n_rule": 15},
             result="insufficient_evidence",
             supporting_evidence_ids=[f"health-{d + 1:04d}" for d in known_days if d % 7 < 5]
                                     + [v["id"] for v in visits if v["place_id"] == place_ids["gym"]],
             contradicting_evidence_ids=[], causal_claim=False,
             uncertainty="Groups are below the minimum size; absence of a detected difference is not evidence of no effect.",
             confidence={"level": "none", "basis": "below_min_n"}, status="insufficient_evidence",
             participant_correction=None, participant_review_status="unreviewed", created_at=created)
    findings = [f1, f2, f3, f4]
    for f in findings:
        f["provenance"] = prov("laplace-demo", f["method"], f["method_version"], f["id"])
        for kind, ids in (("SUPPORTED_BY", f["supporting_evidence_ids"]), ("CONTRADICTED_BY", f["contradicting_evidence_ids"])):
            if ids:
                link(kind, f["id"], ids[0], list(ids), "src-workspace", "inference")
    cor = rec("cor-0001", "Correction", "src-workspace", "observation", "not_applicable", target_id="finding-0001",
              correction_kind="annotation", participant_text="Synthetic note: some Monday starts are late because I work offsite.",
              effect="qualifier_added_statement_unchanged", status="accepted", created_at=iso(at(28, 13 * 60)),
              provenance=prov("participant-input", "manual_annotation", "0.1", "cor-0001"))
    link("CORRECTS", "cor-0001", "finding-0001", ["cor-0001"], "src-workspace", "observation")
    objs += findings + [cor]
    objs += batches

    # sources (computed last)
    data_types = ("LocationSample", "Visit", "Trip", "ActivityInterval", "DailyHealthAggregate", "CalendarEvent",
                  "ResourceAccess", "NetworkAggregate", "AccountActivity")

    def stats(sid: str) -> dict[str, Any]:
        rs = [o for o in objs if o["source_id"] == sid and o["type"] in data_types]
        ends = [o.get("event_end") or o.get("event_time") for o in rs]
        return {"record_count": len(rs), "latest_event_time": max(ends) if ends else UNKNOWN}

    def gap(day: int, s: int, e: int, kind: str, reason: str) -> dict[str, str]:
        return {"start": iso(at(day, s)), "end": iso(at(day, e)), "kind": kind, "reason": reason}

    srcs = [
        ("src-location", "Location", "ios.core_location", "partial", "point",
         [gap(NO_LOCATION_DAY, 0, 1440, "no_location_day", "location_off_by_participant_synthetic"),
          gap(GAP_DAY, GAP_START, GAP_END, "background_gap", "locked_phone_background_suspension_synthetic")],
         {"authorization": "authorized_always_synthetic_value", "background_behavior": "observed_gap_see_missing_periods"}),
        ("src-motion", "Motion", "ios.core_motion", "complete_in_window", "interval", [],
         {"authorization": "authorized_synthetic_value", "history_depth_limit": UNKNOWN}),
        ("src-healthkit", "HealthKit", "ios.healthkit", "partial", "aggregate",
         [gap(NO_STEPS_DAY, 0, 1440, "no_step_record", "not_collected_cause_unknown")],
         {"read_authorization": UNKNOWN, "aggregation": "sum_over_local_day", "producers": UNKNOWN,
          "absent_reason": "no_authorized_producer_observed_cause_unknown", "signals": {"steps": "partial", "heart_rate": "unavailable_no_producer_or_unknown",
                                                     "sleep": "unavailable_no_producer_or_unknown"},
          "last_probe": {"types": ["heart_rate", "sleep"], "rows_returned": 0, "measured_value": UNKNOWN,
                         "interpretation": "no_rows_returned_cause_unknown"}}),
        ("src-eventkit", "EventKit", "ios.eventkit", "complete_in_window", "interval", [],
         {"authorization": "full_access_synthetic_value", "note": "scheduled_context_not_observed_activity"}),
        ("src-apr", "AppPrivacyReport", "ios.app_privacy_report", "partial", "interval",
         [gap(18, 0, 1440, "no_snapshot_covers", "between_snapshots"), gap(19, 0, 1440, "no_snapshot_covers", "between_snapshots")],
         {"snapshots": {k: [iso(at(a, 0)), iso(at(b + 1, 0))] for k, (a, b, _, _) in SNAPSHOTS.items()},
          "overlap": "s1/s2 days 6-9 and s2 days 6-17 vs s1; network aggregates never summed",
          "duplicate_imports": ["ib-apr-s2-again"]}),
        ("src-account-export", "AccountExport", "example-account-export", "partial", "point", [],
         {"fields_unavailable": ["duration", "scroll_depth", "viewed_content_detail"], "exports_imported": 1}),
        ("src-workspace", "Derived", "laplace-demo", "not_applicable", "not_applicable", [],
         {"note": "Findings, corrections; derived or participant-authored, not a collection source."}),
    ]
    sources = []
    for sid, name, system, coverage, gran, missing, extra in srcs:
        sources.append(rec(sid, "Source", sid, "observation", "not_applicable", name=name, system=system,
                           support="supported_synthetic", provisioning="not_applicable_synthetic",
                           coverage_status=coverage, source_granularity=gran, missing_periods=missing,
                           export_success="synthetic_fixture_ok", **stats(sid), **extra,
                           provenance=prov("synthetic-persona", "source_summary", "0.1", sid)))

    records = sources + objs + links
    counts: dict[str, int] = {}
    for r in records:
        counts[r["type"]] = counts.get(r["type"], 0) + 1
    meta = {
        "contract_version": CONTRACT_VERSION, "status": "PROVISIONAL demonstration data; NOT a production schema",
        "synthetic": True, "subject": "Subject EX-01 (fictitious; no real person)", "workspace_id": WS,
        "city": "Port Meridian (fictional)", "bounding_box": BBOX, "coordinates_fictitious": True,
        "timezone": TZ_NAME, "window": window, "seed": SEED, "type_counts": counts,
        "unknown_token": UNKNOWN, "evidence_classes": list(EVIDENCE_CLASSES),
        "notice": "All names, coordinates, identifiers and numbers are invented. Not an anonymization example.",
    }
    return {"meta": meta, "records": records}


def dumps(doc: dict[str, Any]) -> str:
    return json.dumps(doc, separators=(",", ":"), ensure_ascii=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate the synthetic Subject EX-01 persona (demo data only).")
    ap.add_argument("--out", help="write persona JSON to this path")
    args = ap.parse_args(argv)
    doc = build()
    text = dumps(doc)
    if args.out:
        p = Path(args.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({"bytes": len(text.encode()), "type_counts": doc["meta"]["type_counts"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
