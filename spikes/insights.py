"""Insight engine for persona-contract 0.2 documents (synthetic only, PROVISIONAL).

Reads a {meta, records} workspace document, computes per-day metrics, and appends Finding
records (shift, lagged_association, routine, observer_inference, suggestion, insufficient)
with SUPPORTED_BY links. Standard library only, deterministic for a given seed.

This is a transparent demonstration engine, not a production analyzer. Shift and
association p-values come from permutation tests that ignore temporal autocorrelation
and are therefore optimistic. Nothing here claims causation, diagnosis, or that any real
company holds or uses a source. See insights.md and docs/insight-lenses.md (D-043).
"""

from __future__ import annotations

import argparse
import bisect
from collections import defaultdict
import copy
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
import fnmatch
import json
import math
import random
import re
from typing import Any

ENGINE = "spikes.insights"
VERSION = "0.1"
UNKNOWN = "unknown"
WORKSPACE_SOURCE = "src-workspace"
PROVENANCE_SOURCE = "laplace-insights"
MIN_SEGMENT = 10          # known days required on each side of a candidate change day
MIN_KNOWN_FRACTION = 0.6  # share of window days a metric needs before a shift scan is allowed
MIN_PAIRS = 20            # day pairs needed for a lagged association
DEFAULT_PERMUTATIONS = 999
BANNED_WORDING = ("diagnos", "depress", "disorder", "causes", "because of", "caused by")
SHORT_VIDEO_CATEGORIES = frozenset({"short_video", "short-video", "shortvideo"})
OFFICE_CATEGORIES = frozenset({"work", "office"})
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

# Predeclared association pairs: (x_metric, y_metric, lag_days).
PAIRS: tuple[tuple[str, str, int], ...] = (
    ("late_night_minutes", "steps", 1),
    ("late_night_minutes", "sleep_duration", 0),
    ("sleep_duration", "steps", 1),
    ("precip_mm", "office_visit", 0),
    ("screen_minutes", "steps", 0),
)
PAIR_ALTERNATIVES: dict[tuple[str, str, int], list[str]] = {
    ("late_night_minutes", "steps", 1): ["weekday or work-schedule differences", "illness or travel", "a shared trend in both series"],
    ("late_night_minutes", "sleep_duration", 0): ["a shared weekday pattern", "a device not worn or charged at night", "a shared trend in both series"],
    ("sleep_duration", "steps", 1): ["weekday routine", "gym or commute days", "a shared trend in both series"],
    ("precip_mm", "office_visit", 0): ["a standing remote-work arrangement", "calendar commitments", "seasonal change in routine"],
    ("screen_minutes", "steps", 0): ["time spent at a desk", "weekday routine", "a shared trend in both series"],
}

# metric -> (label, unit, source record types). Per-contact and per-topic metrics are added dynamically.
METRIC_INFO: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "steps": ("daily steps", "steps/day", ("DailyHealthAggregate",)),
    "screen_minutes": ("total screen time", "min/day", ("ScreenTimeDaily",)),
    "short_video_minutes": ("short-video screen time", "min/day", ("ScreenTimeDaily",)),
    "late_night_minutes": ("late-night (00:00 to 05:00) phone use", "min/day", ("ScreenTimeDaily",)),
    "pickups": ("phone pickups", "pickups/day", ("ScreenTimeDaily",)),
    "notifications": ("notifications received", "notifications/day", ("NotificationDaily",)),
    "sleep_onset": ("sleep onset", "min after 18:00", ("SleepInterval",)),
    "sleep_duration": ("sleep duration", "min/night", ("SleepInterval",)),
    "distinct_places": ("distinct places visited", "places/day", ("Visit",)),
    "minutes_away": ("time away from home", "min/day", ("Visit",)),
    "office_visit": ("office visits", "share of days", ("Visit",)),
    "sensitive_search_share": ("share of searches on sensitive topics", "share of searches", ("AccountActivity",)),
    "precip_mm": ("precipitation", "mm/day", ("WeatherDaily",)),
}

# Who could plausibly see each source type. Always "could see", never "has".
HOLDERS: dict[str, list[tuple[str, str]]] = {
    "ScreenTimeDaily": [("the device vendor (on-device)", "per-app daily screen time, pickups and late-night use"),
                        ("each app vendor (its own usage only)", "how long and when that app was used")],
    "NotificationDaily": [("the device vendor (on-device)", "notification counts per app")],
    "DailyHealthAggregate": [("the device vendor (on-device Health store)", "daily activity totals"),
                             ("apps the participant authorizes for Health access", "the data types granted")],
    "SleepInterval": [("the device vendor (on-device Health store)", "sleep timing and duration, if a producer writes it"),
                      ("apps the participant authorizes for Health access", "the data types granted")],
    "MessagingDaily": [("the messaging service operator", "daily sent and received counts per conversation partner reference")],
    "AccountActivity": [("the account service operator", "the account's own activity and search history")],
    "Transaction": [("the card issuer or payment processor", "transaction time, merchant category and amount"),
                    ("the merchant", "its own transactions only")],
    "Visit": [("apps with location permission", "visited places, if granted"),
              ("the device vendor (on-device)", "significant-location history, if enabled")],
    "WeatherDaily": [("the weather data provider", "a coarse location, if a live lookup were used")],
}


# --- small numeric helpers ----------------------------------------------------

def _num(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None


def _median(sorted_values: list[float]) -> float:
    n = len(sorted_values)
    mid = n // 2
    return sorted_values[mid] if n % 2 else (sorted_values[mid - 1] + sorted_values[mid]) / 2


def _med(values: list[float]) -> float:
    return _median(sorted(values))


def _mad(values: list[float]) -> float:
    m = _med(values)
    return _med([abs(v - m) for v in values])


def _fmt(value: float) -> str:
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}".rstrip("0").rstrip(".")
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def _pearson(a: list[float], b: list[float]) -> float:
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    sa = math.sqrt(sum((x - ma) ** 2 for x in a))
    sb = math.sqrt(sum((y - mb) ** 2 for y in b))
    return 0.0 if sa == 0 or sb == 0 else sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb)


def benjamini_hochberg(p_values: list[float | None]) -> list[float]:
    """BH q-values; None (stopped early, certainly above alpha) counts as 1.0."""
    m = len(p_values)
    ps = [1.0 if p is None else p for p in p_values]
    order = sorted(range(m), key=lambda i: ps[i])
    q = [1.0] * m
    running = 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        running = min(running, ps[i] * m / rank)
        q[i] = running
    return q


# --- daily metrics ------------------------------------------------------------

@dataclass
class Metrics:
    dates: list[str]
    series: dict[str, list[float | None]] = field(default_factory=dict)
    evidence: dict[str, list[list[str]]] = field(default_factory=dict)
    source_types: dict[str, tuple[str, ...]] = field(default_factory=dict)

    @property
    def weekdays(self) -> list[int]:
        return [date.fromisoformat(d).weekday() for d in self.dates]

    def known(self, metric: str) -> list[int]:
        return [i for i, v in enumerate(self.series[metric]) if v is not None]

    def public(self) -> dict[str, dict[str, float | str]]:
        out = {m: {d: (UNKNOWN if v is None else v) for d, v in zip(self.dates, vals)}
               for m, vals in self.series.items()}
        for m in METRIC_INFO:  # standard metrics whose source is absent: every day unknown
            out.setdefault(m, {d: UNKNOWN for d in self.dates})
        return out


def _day(value: Any) -> str | None:
    if isinstance(value, str) and re.match(r"^\d{4}-\d{2}-\d{2}", value):
        try:
            date.fromisoformat(value[:10])
        except ValueError:
            return None
        return value[:10]
    return None


def _rec_day(r: dict[str, Any]) -> str | None:
    for k in ("date", "event_time", "event_start"):
        d = _day(r.get(k))
        if d:
            return d
    return None


def _local(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _window_dates(doc: dict[str, Any], by_type: dict[str, list[dict[str, Any]]]) -> list[str]:
    days: set[str] = set()
    window = doc.get("meta", {}).get("window")
    if isinstance(window, dict):
        s, e = _day(window.get("start")), _day(window.get("end"))
        if s and e:
            last = date.fromisoformat(e)
            if str(window.get("end"))[10:16] in ("T00:00", "") and last > date.fromisoformat(s):
                last -= timedelta(days=1)  # exclusive midnight end
            cur = date.fromisoformat(s)
            while cur <= last:
                days.add(cur.isoformat())
                cur += timedelta(days=1)
    for rtype in METRIC_RECORD_TYPES:
        for r in by_type.get(rtype, []):
            d = _day(r.get("event_end")) if rtype == "SleepInterval" else _rec_day(r)  # sleep belongs to its wake day
            if d:
                days.add(d)
    if not days:
        return []
    lo, hi = date.fromisoformat(min(days)), date.fromisoformat(max(days))
    return [(lo + timedelta(days=i)).isoformat() for i in range((hi - lo).days + 1)]


METRIC_RECORD_TYPES = ("ScreenTimeDaily", "NotificationDaily", "DailyHealthAggregate", "SleepInterval", "MessagingDaily",
                       "AccountActivity", "Transaction", "WeatherDaily", "Visit")


def _index(records: list[Any]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        if isinstance(r, dict) and isinstance(r.get("type"), str):
            out[r["type"]].append(r)
    return out


def _unmeasured_days(by_type: dict[str, list[dict[str, Any]]], source_id: str, dates: list[str]) -> set[str]:
    """Days a Source record lists as wholly missing (missing_periods covers the full local day)."""
    out: set[str] = set()
    for s in by_type.get("Source", []):
        if s.get("id") != source_id or not isinstance(s.get("missing_periods"), list):
            continue
        for p in s["missing_periods"]:
            ps, pe = _local(p.get("start")) if isinstance(p, dict) else None, _local(p.get("end")) if isinstance(p, dict) else None
            if ps is None or pe is None:
                continue
            for d in dates:
                d0 = datetime.fromisoformat(d)
                if ps <= d0 and pe >= d0 + timedelta(days=1):
                    out.add(d)
    return out


def compute_metrics(doc: dict[str, Any]) -> Metrics:
    """Per local-day metrics. Absent source or unmeasured day -> None (public form: 'unknown')."""
    records = doc.get("records", []) if isinstance(doc, dict) else []
    by_type = _index(records)
    dates = _window_dates(doc, by_type)
    pos = {d: i for i, d in enumerate(dates)}
    m = Metrics(dates=dates)

    def put(metric: str, types: tuple[str, ...], values: dict[int, float], evidence: dict[int, list[str]]) -> None:
        m.series[metric] = [values.get(i) for i in range(len(dates))]
        m.evidence[metric] = [sorted(set(evidence.get(i, []))) for i in range(len(dates))]
        m.source_types[metric] = types

    def has(rtype: str) -> bool:
        return any(_rec_day(r) in pos for r in by_type.get(rtype, []))

    # Health steps
    if has("DailyHealthAggregate"):
        vals, ev = {}, defaultdict(list)
        for r in by_type["DailyHealthAggregate"]:
            i, v = pos.get(_rec_day(r) or ""), _num(r.get("steps"))
            if i is not None and v is not None:
                vals[i] = v
                ev[i].append(r["id"])
        put("steps", ("DailyHealthAggregate",), vals, ev)

    # Screen Time: one record per (day, app); a later overlapping report replaces, never adds.
    if has("ScreenTimeDaily"):
        latest: dict[tuple[int, Any], dict[str, Any]] = {}
        for r in by_type["ScreenTimeDaily"]:
            i = pos.get(_rec_day(r) or "")
            if i is not None:
                latest[(i, r.get("app_id"))] = r
        fields = {"screen_minutes": "minutes", "late_night_minutes": "late_night_minutes", "pickups": "pickups"}
        acc: dict[str, tuple[dict[int, float], dict[int, list[str]]]] = {k: ({}, defaultdict(list)) for k in (*fields, "short_video_minutes")}
        for (i, _app), r in latest.items():
            for metric, fld in fields.items():
                v = _num(r.get(fld))
                if v is not None:
                    acc[metric][0][i] = acc[metric][0].get(i, 0.0) + v
                    acc[metric][1][i].append(r["id"])
            mins = _num(r.get("minutes"))
            if mins is not None and str(r.get("app_category", "")).lower() in SHORT_VIDEO_CATEGORIES:
                acc["short_video_minutes"][0][i] = acc["short_video_minutes"][0].get(i, 0.0) + mins
                acc["short_video_minutes"][1][i].append(r["id"])
        measured = {i for i, _ in latest}
        if acc["screen_minutes"][0]:
            for i in measured:  # a measured day with no short-video app is a true 0
                if i in acc["screen_minutes"][0]:
                    acc["short_video_minutes"][0].setdefault(i, 0.0)
        for metric, (vals, ev) in acc.items():
            if vals:
                put(metric, ("ScreenTimeDaily",), vals, ev)

    if has("NotificationDaily"):
        vals, ev = {}, defaultdict(list)
        for r in by_type["NotificationDaily"]:
            i, v = pos.get(_rec_day(r) or ""), _num(r.get("count"))
            if i is not None and v is not None:
                vals[i] = vals.get(i, 0.0) + v
                ev[i].append(r["id"])
        put("notifications", ("NotificationDaily",), vals, ev)

    # Sleep (asleep stage only); assigned to the wake day, onset in minutes after 18:00 the evening before.
    if by_type.get("SleepInterval"):
        per_day: dict[int, list[tuple[datetime, datetime, str]]] = defaultdict(list)
        for r in by_type["SleepInterval"]:
            s, e = _local(r.get("event_start")), _local(r.get("event_end"))
            i = pos.get(e.date().isoformat()) if e else None
            if s and e and e > s and i is not None and r.get("stage") == "asleep":
                per_day[i].append((s, e, r["id"]))
        dur, onset, ev = {}, {}, defaultdict(list)
        for i, ivs in per_day.items():
            dur[i] = sum((e - s).total_seconds() / 60 for s, e, _ in ivs)
            first = min(ivs)[0]
            eve = datetime.fromisoformat(dates[i]) - timedelta(hours=6)
            onset[i] = (first - eve).total_seconds() / 60
            ev[i] = [x[2] for x in ivs]
        if dur:
            put("sleep_duration", ("SleepInterval",), dur, ev)
            put("sleep_onset", ("SleepInterval",), onset, ev)

    # Messaging: with the source present, a day without records is a true 0 unless its Source lists the day missing.
    msg = [r for r in by_type.get("MessagingDaily", []) if _rec_day(r) in pos and isinstance(r.get("contact_ref"), str)]
    if msg:
        gone = set()
        for sid in {r.get("source_id") for r in msg}:
            gone |= {pos[d] for d in _unmeasured_days(by_type, sid, dates)}
        for ref in sorted({r["contact_ref"] for r in msg}):
            vals = {i: 0.0 for i in range(len(dates)) if i not in gone}
            ev = defaultdict(list)
            for r in msg:
                i = pos[_rec_day(r)]  # type: ignore[index]
                if r["contact_ref"] == ref and i in vals:
                    vals[i] += (_num(r.get("sent")) or 0.0) + (_num(r.get("received")) or 0.0)
                    ev[i].append(r["id"])
            put(f"messages_{ref}", ("MessagingDaily",), vals, ev)

    # Account activity searches by sensitive category (source present: no record on a day means 0 searches).
    acct = [r for r in by_type.get("AccountActivity", []) if _rec_day(r) in pos]
    if acct:
        gone_a: set[int] = set()
        for sid in {r.get("source_id") for r in acct}:
            gone_a |= {pos[d] for d in _unmeasured_days(by_type, sid, dates)}
        searches = [r for r in acct if r.get("activity_kind") == "search"]
        cats = sorted({str(r.get("sensitive_category")) for r in searches
                       if r.get("sensitive_category") not in (None, "none", UNKNOWN)})
        for cat in cats:
            vals = {i: 0.0 for i in range(len(dates)) if i not in gone_a}
            ev = defaultdict(list)
            for r in searches:
                if str(r.get("sensitive_category")) == cat:
                    i = pos[_rec_day(r)]  # type: ignore[index]
                    if i in vals:
                        vals[i] += 1
                        ev[i].append(r["id"])
            put(f"searches_{cat}", ("AccountActivity",), vals, ev)
        if searches:
            tot, sens, ev = defaultdict(float), defaultdict(float), defaultdict(list)
            for r in searches:
                i = pos[_rec_day(r)]  # type: ignore[index]
                tot[i] += 1
                if r.get("sensitive_category") not in (None, "none", UNKNOWN):
                    sens[i] += 1
                    ev[i].append(r["id"])
            put("sensitive_search_share", ("AccountActivity",), {i: sens[i] / tot[i] for i in tot}, ev)

    # Location-derived (Visit): a day is measured only if at least one Visit exists on it.
    visits = [r for r in by_type.get("Visit", []) if _rec_day(r) in pos]
    if visits:
        places = {p["id"]: p for p in by_type.get("Place", []) if isinstance(p.get("id"), str)}
        cat = lambda pid: str(places.get(pid, {}).get("category", UNKNOWN)).lower()  # noqa: E731
        per: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for r in visits:
            per[pos[_rec_day(r)]].append(r)  # type: ignore[index]
        office, distinct, away, ev_o, ev_all = {}, {}, {}, defaultdict(list), defaultdict(list)
        for i, vs in per.items():
            hits = [v for v in vs if cat(v.get("place_id")) in OFFICE_CATEGORIES]
            office[i] = 1.0 if hits else 0.0
            ev_o[i] = [v["id"] for v in hits]
            ev_all[i] = [v["id"] for v in vs]
            distinct[i] = float(len({v.get("place_id") for v in vs if v.get("place_id") not in (None, UNKNOWN)}))
            tot, ok = 0.0, False
            for v in vs:
                s, e = _local(v.get("event_start")), _local(v.get("event_end"))
                if s and e and e >= s and cat(v.get("place_id")) != "home":
                    tot += (e - s).total_seconds() / 60
                    ok = True
                elif s and e:
                    ok = True
            if ok:
                away[i] = tot
        put("office_visit", ("Visit",), office, ev_o)
        put("distinct_places", ("Visit",), distinct, ev_all)
        if any(cat(pid) == "home" for pid in places):
            put("minutes_away", ("Visit",), away, ev_all)

    if has("WeatherDaily"):
        vals, ev = {}, defaultdict(list)
        for r in by_type["WeatherDaily"]:
            i, v = pos.get(_rec_day(r) or ""), _num(r.get("precip_mm"))
            if i is not None and v is not None:
                vals[i] = v
                ev[i].append(r["id"])
        put("precip_mm", ("WeatherDaily",), vals, ev)
    return m


def daily_metrics(doc: dict[str, Any]) -> dict[str, dict[str, float | str]]:
    """{metric: {local ISO date: value or "unknown"}}. Absent source or unmeasured day is "unknown", never 0."""
    return compute_metrics(doc).public()


# --- statistics -----------------------------------------------------------------

def _deseasonalize(weekdays: list[int], values: list[float]) -> list[float]:
    groups: dict[int, list[float]] = defaultdict(list)
    for w, v in zip(weekdays, values):
        groups[w].append(v)
    if len(groups) < 7 or any(len(g) < 3 for g in groups.values()):
        return list(values)
    med = {w: _med(g) for w, g in groups.items()}
    return [v - med[w] for w, v in zip(weekdays, values)]


def _scan(vals: list[float], min_seg: int, use_mean: bool = False) -> list[tuple[int, float]]:
    """(k, center(after) - center(before)) for every candidate change index k (k = first 'after' value).
    The center is the median, or the mean for zero-inflated metrics (medians cannot see a changed share of
    nonzero days)."""
    n = len(vals)
    out = []
    if use_mean:
        total = sum(vals[:min_seg])
        rest = sum(vals[min_seg:])
        for k in range(min_seg, n - min_seg + 1):
            out.append((k, rest / (n - k) - total / k))
            total += vals[k]
            rest -= vals[k]
        return out
    left, right = sorted(vals[:min_seg]), sorted(vals[min_seg:])
    for k in range(min_seg, n - min_seg + 1):
        out.append((k, _median(right) - _median(left)))
        if k < n - min_seg:
            x = vals[k]
            del right[bisect.bisect_left(right, x)]
            bisect.insort(left, x)
    return out


def _max_stat(vals: list[float], min_seg: int, use_mean: bool = False) -> float:
    return max(abs(d) for _, d in _scan(vals, min_seg, use_mean))


def _center(values: list[float], use_mean: bool) -> float:
    return sum(values) / len(values) if use_mean else _med(values)


def _best_split(vals: list[float], min_seg: int, use_mean: bool = False) -> tuple[int, float]:
    """Split with the largest |center difference|. Center differences plateau around a step, so among
    near-maximal splits (>= 90% of the maximum) the one with the smallest within-segment absolute
    deviation is reported as the change point. The p-value uses only the maximum statistic."""
    scan = _scan(vals, min_seg, use_mean)
    top = max(abs(d) for _, d in scan)
    best: tuple[float, int, float] | None = None
    for k, d in scan:
        if abs(d) >= 0.9 * top - 1e-12:
            l, r = vals[:k], vals[k:]
            ml, mr = _center(l, use_mean), _center(r, use_mean)
            sad = sum(abs(v - ml) for v in l) + sum(abs(v - mr) for v in r)
            if best is None or sad < best[0] - 1e-12:
                best = (sad, k, d)
    assert best is not None
    return best[1], best[2]


def _perm_p(observed: float, trials: int, alpha: float, stat: Any, rng: random.Random, items: list[float]) -> float | None:
    """Add-one permutation p. Returns None once p is certain to exceed alpha (cannot be rejected by BH)."""
    cutoff = alpha * (trials + 1)
    hits = 0
    pool = list(items)
    for _ in range(trials):
        rng.shuffle(pool)
        if stat(pool) >= observed - 1e-12:
            hits += 1
            if hits + 1 > cutoff:
                return None
    return (hits + 1) / (trials + 1)


def _clock(minutes_after_18: float) -> str:
    t = int(round(minutes_after_18 + 18 * 60)) % (24 * 60)
    return f"{t // 60:02d}:{t % 60:02d}"


def _metric_label(metric: str) -> tuple[str, str]:
    if metric in METRIC_INFO:
        return METRIC_INFO[metric][0], METRIC_INFO[metric][1]
    if metric.startswith("messages_"):
        return f"daily messages with {_contact_label(metric[9:])}", "messages/day"
    if metric.startswith("searches_"):
        return f"daily searches on the topic {_topic_label(metric[9:])}", "searches/day"
    return metric, "units"


def _contact_label(ref: str) -> str:
    return ref if re.fullmatch(r"contact-[A-Za-z0-9]+", ref) else "a contact (reference withheld)"


def _topic_label(topic: str) -> str:
    low = topic.lower()
    if any(b in low for b in BANNED_WORDING) or not re.fullmatch(r"[A-Za-z0-9_ -]{1,40}", topic):
        return "a sensitive topic"
    return topic.replace("_", " ")


def _metric_types(metric: str, m: Metrics) -> tuple[str, ...]:
    return m.source_types.get(metric, ())


# --- the engine -------------------------------------------------------------------

class _Run:
    def __init__(self, doc: dict[str, Any], alpha: float, seed: Any, permutations: int) -> None:
        self.doc, self.alpha, self.seed, self.B = doc, alpha, seed, permutations
        self.ws = doc["meta"]["workspace_id"]
        self.m = compute_metrics(doc)
        self.by_type = _index(doc["records"])
        self.cls = {r["id"]: r.get("evidence_class") for r in doc["records"] if isinstance(r, dict) and "id" in r}
        self.used_ids = set(self.cls)
        self.created = self._created_at()
        self.window = ({"start": self.m.dates[0], "end": self.m.dates[-1]} if self.m.dates else {"start": UNKNOWN, "end": UNKNOWN})
        self.tz = doc["meta"].get("timezone", UNKNOWN)
        self.findings: list[dict[str, Any]] = []
        self.scanned = 0
        self._n = 0

    def _created_at(self) -> str:
        best = ""
        for r in self.doc["records"]:
            if isinstance(r, dict):
                for k in ("event_time", "event_end", "event_start"):
                    v = r.get(k)
                    if isinstance(v, str) and _local(v) and v > best and re.search(r"(Z|[+-]\d\d:\d\d)$", v):
                        best = v
        return best or "2026-01-01T00:00:00Z"

    def cite(self, ids: list[str]) -> list[str]:
        """Only observations and normalized events may be cited as supporting evidence."""
        return sorted({i for i in ids if self.cls.get(i) in ("observation", "normalized_event")})

    def new(self, kind: str, evidence_class: str, statement: str, method: str, supporting: list[str] | None = None,
            **fields: Any) -> dict[str, Any]:
        self._n += 1
        rid = f"ins-{self._n:04d}"
        while rid in self.used_ids:
            self._n += 1
            rid = f"ins-{self._n:04d}"
        self.used_ids.add(rid)
        sup = self.cite(supporting or [])
        f = {"id": rid, "type": "Finding", "workspace_id": self.ws, "source_id": WORKSPACE_SOURCE,
             "evidence_class": evidence_class, "finding_kind": kind, "statement": statement,
             "input_window": dict(self.window), "timezone": self.tz, "method": method, "method_version": VERSION,
             "supporting_evidence_ids": sup, "contradicting_evidence_ids": [], "causal_claim": False,
             **fields, "participant_correction": None, "participant_review_status": "unreviewed",
             "created_at": self.created,
             "provenance": {"source": PROVENANCE_SOURCE, "method": method, "method_version": VERSION, "line_or_record": rid}}
        self.findings.append(f)
        return f

    # -- shift
    def eligible(self, metric: str) -> bool:
        k = self.m.known(metric)
        return len(k) >= max(2 * MIN_SEGMENT, math.ceil(MIN_KNOWN_FRACTION * len(self.m.dates)))

    def shifts(self) -> None:
        cands, ps, results = [], [], []
        for metric in self.m.series:
            if metric == "precip_mm":
                continue  # context variable, not a behaviour
            known = self.m.known(metric)
            if not known:
                continue
            if not self.eligible(metric):
                self.insufficient(f"shift scan of {_metric_label(metric)[0]}", metric,
                                  f"only {len(known)} of {len(self.m.dates)} days measured; need at least "
                                  f"{max(2 * MIN_SEGMENT, math.ceil(MIN_KNOWN_FRACTION * len(self.m.dates)))} "
                                  "(unmeasured days are not treated as zero)")
                continue
            self.scanned += 1
            raw = [self.m.series[metric][i] for i in known]  # type: ignore[misc]
            wd = self.m.weekdays
            des = _deseasonalize([wd[i] for i in known], raw)  # type: ignore[arg-type]
            use_mean = sum(1 for v in raw if v == 0) / len(raw) > 0.25
            k, d = _best_split(des, MIN_SEGMENT, use_mean)
            rng = random.Random(f"shift:{self.seed}:{metric}")
            p = _perm_p(_max_stat(des, MIN_SEGMENT, use_mean), self.B, self.alpha, lambda v: _max_stat(v, MIN_SEGMENT, use_mean), rng, des)
            cands.append((metric, known, raw, des, k, d, use_mean))
            ps.append(p)
        qs = benjamini_hochberg(ps)
        for (metric, known, raw, des, k, d, use_mean), p, q in zip(cands, ps, qs):
            if p is None or q > self.alpha:
                continue
            self.add_shift(metric, known, raw, des, k, d, p, q, use_mean)

    def add_shift(self, metric: str, known: list[int], raw: list[float], des: list[float], k: int, d: float,
                  p: float, q: float, use_mean: bool) -> None:
        label, unit = _metric_label(metric)
        before, after = raw[:k], raw[k:]
        mb, ma = _center(before, use_mean), _center(after, use_mean)
        word = "mean" if use_mean else "median"
        mad_b, mad_a = _mad(before), _mad(after)
        gscale = 1.4826 * _mad(des) or 1.0
        pooled = max(1.4826 * (mad_b + mad_a) / 2, 0.25 * gscale)
        direction = "up" if d > 0 else "down"
        ratio: float | str = round(ma / mb, 3) if mb else UNKNOWN
        change = self.m.dates[known[k]]
        if metric == "sleep_onset":
            move = f"from {_clock(mb)} to {_clock(ma)} (median clock time)"
        else:
            move = f"from a {word} of {_fmt(mb)} to {_fmt(ma)} {unit}" + (f" (ratio {ratio})" if ratio != UNKNOWN else "")
        n_b, n_a = len(before), len(after)
        ev = [i for j in known for i in self.m.evidence[metric][j]]
        stmt = (f"Around {change}, {label} moved {move}; {n_b} measured days before, {n_a} after. "
                f"Descriptive change only; the cause is not identified.")
        self.new("shift", "inference", stmt, "median_shift_scan_permutation_bh", ev,
                 metric=metric, change_day=change, statistic_center=word,
                 baseline={"window": {"start": self.m.dates[known[0]], "end": self.m.dates[known[k - 1]]},
                           "median": round(_med(before), 3), "mean": round(sum(before) / n_b, 3),
                           "mad": round(mad_b, 3), "n": n_b},
                 after={"window": {"start": change, "end": self.m.dates[known[-1]]}, "median": round(_med(after), 3), "mean": round(sum(after) / n_a, 3), "n": n_a},
                 effect={"ratio": ratio, "difference": round(ma - mb, 3), "unit": unit, "direction": direction,
                         "scaled_by_pooled_mad": round(abs(d) / pooled, 2)},
                 p_value=round(p, 4), q_value=round(q, 4), metrics_scanned=None,
                 uncertainty=("Permutation p-value shuffles day order and repeats the whole change-day scan, so scanning is "
                              "accounted for, but day-to-day autocorrelation makes p optimistic (too small). Weekday medians "
                              "were removed before scanning. Small n; BH controls the false-discovery rate across scanned "
                              "metrics only."),
                 confidence={"level": "medium" if q <= self.alpha / 5 and abs(d) / pooled >= 1.5 else "low",
                             "basis": "permutation_scan_bh_autocorrelation_ignored"},
                 status="exploratory",
                 alternatives=["a change in how the source records this metric", "travel, illness, or a schedule change",
                               "a gradual trend rather than a step"])

    # -- lagged association
    def associations(self) -> None:
        tests = []
        office_days = self.office_weekdays()
        for x, y, lag in PAIRS:
            if x not in self.m.series or y not in self.m.series:
                continue
            n_days = len(self.m.dates)
            idx = [i for i in range(n_days - lag) if self.m.series[x][i] is not None and self.m.series[y][i + lag] is not None]
            restricted = y == "office_visit"
            if restricted:
                if not office_days:
                    continue
                idx = [i for i in idx if self.m.weekdays[i + lag] in office_days]
            if len(idx) < MIN_PAIRS:
                continue
            xs, ys = [self.m.series[x][i] for i in idx], [self.m.series[y][i + lag] for i in idx]
            if not restricted:
                xs = _deseasonalize([self.m.weekdays[i] for i in idx], xs)  # type: ignore[arg-type]
                ys = _deseasonalize([self.m.weekdays[i + lag] for i in idx], ys)  # type: ignore[arg-type]
            rx, ry = _ranks(xs), _ranks(ys)  # type: ignore[arg-type]
            rho = _pearson(rx, ry)
            rng = random.Random(f"assoc:{self.seed}:{x}:{y}:{lag}")
            p = _perm_p(abs(rho), self.B, self.alpha, lambda r: abs(_pearson(rx, r)), rng, ry)
            tests.append(((x, y, lag), idx, rho, p, restricted))
        qs = benjamini_hochberg([t[3] for t in tests])
        for (pair, idx, rho, p, restricted), q in zip(tests, qs):
            if p is None or q > self.alpha:
                continue
            x, y, lag = pair
            xl, yl = _metric_label(x)[0], _metric_label(y)[0]
            when = "on the same day" if lag == 0 else f"{lag} day later"
            trend = "higher" if rho > 0 else "lower"
            scope = " (restricted to usual office weekdays)" if restricted else ""
            ev = [i for j in idx for i in self.m.evidence[x][j] + self.m.evidence[y][j + lag]]
            stmt = (f"CORRELATION, not causation: days with more {xl} tended to be paired with {trend} {yl} {when}"
                    f"{scope} (Spearman rho = {rho:.2f}, n = {len(idx)} day pairs, permutation p = {p:.3f}, q = {q:.3f}).")
            self.new("lagged_association", "inference", stmt, "spearman_permutation_bh", ev,
                     x_metric=x, y_metric=y, lag_days=lag, rho=round(rho, 3), n=len(idx),
                     permutation_p=round(p, 4), q_value=round(q, 4), pairs_tested=len(tests),
                     alternatives=PAIR_ALTERNATIVES.get(pair, ["unobserved factors"]),
                     uncertainty=("Permutation p ignores autocorrelation and is optimistic; a predeclared list of "
                                  f"{len(tests)} testable pair(s) with BH correction; small n; an association, not an effect."),
                     confidence={"level": "low", "basis": f"n={len(idx)}_permutation_bh"}, status="exploratory")

    def office_weekdays(self) -> set[int]:
        if "office_visit" not in self.m.series:
            return set()
        out = set()
        for w in range(7):
            vals = [self.m.series["office_visit"][i] for i in self.m.known("office_visit") if self.m.weekdays[i] == w]
            if len(vals) >= 4 and sum(vals) / len(vals) >= 0.5:  # type: ignore[arg-type]
                out.add(w)
        return out

    # -- routines
    def routines(self) -> None:
        if "office_visit" in self.m.series:
            days, hit, total, ev = [], 0, 0, []
            for w in range(7):
                ks = [i for i in self.m.known("office_visit") if self.m.weekdays[i] == w]
                if len(ks) < 4:
                    continue
                h = [i for i in ks if self.m.series["office_visit"][i] == 1.0]
                if len(h) / len(ks) >= 0.75:
                    days.append(w)
                    hit, total = hit + len(h), total + len(ks)
                    ev += [e for i in h for e in self.m.evidence["office_visit"][i]]
            if days:
                names = ", ".join(WEEKDAYS[w] for w in days)
                self.new("routine", "inference",
                         f"The office is visited on {names}: {hit} of {total} measured such days ({hit / total:.0%}).",
                         "weekday_place_regularity", ev, pattern=f"weekday_office:{names}", pattern_key="weekday_office",
                         support=round(hit / total, 3), eligible_days=total, weekdays=[WEEKDAYS[w] for w in days],
                         uncertainty="Descriptive regularity over a short window; weekdays with fewer than 4 measured days are skipped.",
                         confidence={"level": "medium" if total >= 12 else "low", "basis": f"n={total}"},
                         status="descriptive")
        tx = [r for r in self.by_type.get("Transaction", []) if _rec_day(r)]
        if tx:
            lo, hi = min(_rec_day(r) for r in tx), max(_rec_day(r) for r in tx)  # type: ignore[type-var]
            span = [d for d in self.m.dates if lo <= d <= hi]
            for cat in sorted({str(r.get("merchant_category", UNKNOWN)) for r in tx} - {UNKNOWN}):
                mine = [r for r in tx if str(r.get("merchant_category")) == cat]
                have = {_rec_day(r) for r in mine}
                days, hit, total, ev = [], 0, 0, []
                for w in range(7):
                    ds = [d for d in span if date.fromisoformat(d).weekday() == w]
                    if len(ds) < 4:
                        continue
                    h = [d for d in ds if d in have]
                    if len(h) / len(ds) >= 0.75:
                        days.append(w)
                        hit, total = hit + len(h), total + len(ds)
                        ev += [r["id"] for r in mine if _rec_day(r) in h]
                if days:
                    names = ", ".join(WEEKDAYS[w] for w in days)
                    amounts = [a for r in mine if (a := _num(r.get("amount"))) is not None]
                    currencies = {str(r.get("currency")) for r in mine}
                    extra = {"median_amount": round(_med(amounts), 2), "currency": currencies.pop()} if amounts and len(currencies) == 1 else {}
                    self.new("routine", "inference",
                             f"Transactions in the category {cat} recur on {names}: {hit} of {total} such days ({hit / total:.0%}).",
                             "weekday_recurring_transaction", ev, pattern=f"recurring_spend:{cat}:{names}",
                             pattern_key=f"recurring_spend:{cat}", support=round(hit / total, 3), eligible_days=total,
                             weekdays=[WEEKDAYS[w] for w in days], **extra,
                             uncertainty="Descriptive regularity over the export window; assumes the transaction export is complete.",
                             confidence={"level": "medium" if total >= 12 else "low", "basis": f"n={total}"},
                             status="descriptive")

    # -- insufficient
    def insufficient(self, wanted: str, missing: str, reason: str) -> None:
        key = (wanted, missing)
        if any(f.get("finding_kind") == "insufficient" and (f["wanted"], f["missing"]) == key for f in self.findings):
            return
        self.new("insufficient", "inference", f"Insufficient data for {wanted}: {reason}.", "coverage_check",
                 wanted=wanted, missing=missing, reason=reason,
                 uncertainty="Absence of a source or of measured days is unknown, not zero; nothing is concluded.",
                 confidence={"level": "none", "basis": "no_usable_data"}, status="insufficient_evidence")

    def missing_sources(self) -> None:
        wants = [("sleep analyses (onset, duration, shifts, sleep-linked associations)", "SleepInterval", "no sleep producer or SleepInterval records"),
                 ("screen-time analyses (screen, short-video, late-night, pickups)", "ScreenTimeDaily", "no Screen Time source"),
                 ("activity analyses (steps)", "DailyHealthAggregate", "no daily health aggregate source"),
                 ("place and routine analyses", "Visit", "no location-derived Visit records"),
                 ("messaging-pattern analyses", "MessagingDaily", "no messaging export")]
        for wanted, rtype, reason in wants:
            if not any(_rec_day(r) or r.get("event_end") for r in self.by_type.get(rtype, [])):
                self.insufficient(wanted, rtype, reason)

    # -- mirror
    def mirror(self) -> None:
        shifts = [f for f in self.findings if f["finding_kind"] == "shift"]
        routines = [f for f in self.findings if f["finding_kind"] == "routine"]

        def shift_match(pattern: str, direction: str) -> list[dict[str, Any]]:
            return [f for f in shifts if fnmatch.fnmatchcase(f["metric"], pattern) and f["effect"]["direction"] == direction]

        def level(metric: str, op: str, value: float, last: int) -> bool:
            vals = [self.m.series[metric][i] for i in self.m.known(metric)][-last:] if metric in self.m.series else []
            return len(vals) >= 7 and op == ">=" and _med(vals) >= value  # type: ignore[arg-type]

        def cond(c: tuple[Any, ...]) -> list[dict[str, Any]] | None:
            """Matched findings, [] when satisfied by a metric level only, None when unmet."""
            if c[0] == "shift":
                hits = shift_match(c[1], c[2])
                return hits or None
            if c[0] == "routine":
                hits = [f for f in routines if fnmatch.fnmatchcase(f["pattern_key"], c[1])]
                return hits or None
            if c[0] == "level":
                return [] if level(c[1], c[2], c[3], c[4]) else None
            if c[0] == "any":
                for sub in c[1]:
                    got = cond(sub)
                    if got is not None:
                        return got
            return None

        for rule in RULES:
            types = rule["source_types"]
            if not all(any(_rec_day(r) or r.get("event_end") for r in self.by_type.get(t, [])) for t in types):
                continue
            matched: list[list[dict[str, Any]]] = []
            for c in rule["requires"]:
                got = cond(c)
                if got is None:
                    matched = []
                    break
                matched.append(got)
            if not matched:
                continue
            flat = [f for grp in matched for f in grp]
            instances = [(flat, None)]
            if rule.get("per_match"):
                instances = self.expand(rule, flat)
            for rests, subject in instances:
                self.add_mirror(rule, rests, subject, types)
        self.suggestions()

    def expand(self, rule: dict[str, Any], flat: list[dict[str, Any]]) -> list[tuple[list[dict[str, Any]], str]]:
        out = []
        topic_hits = [f for f in flat if f["metric"].startswith("searches_")]
        for f in (topic_hits or flat):
            out.append(([f] + ([g for g in flat if g is not f and not g["metric"].startswith("searches_")] if not topic_hits else []), f["metric"]))
        return out

    def add_mirror(self, rule: dict[str, Any], rests: list[dict[str, Any]], subject: str | None, types: list[str]) -> None:
        sids = sorted({r.get("source_id") for t in types for r in self.by_type.get(t, []) if isinstance(r.get("source_id"), str)})
        merged: dict[str, list[str]] = {}  # one entry per holder; what it could see is combined
        for t in types:
            for holder, sees in HOLDERS.get(t, []):
                if sees not in merged.setdefault(holder, []):
                    merged[holder].append(sees)
        holders = [{"holder": h, "sees": "; ".join(s)} for h, s in merged.items()]
        sensitive = bool(rule["sensitive"])
        what = rule["statement"]
        label = rule["segment_label"]
        if subject and subject.startswith("messages_"):
            ref = _contact_label(subject[9:])
            what = what.format(subject=ref)
            label = label.format(subject=ref)
        elif subject and subject.startswith("searches_"):
            topic = _topic_label(subject[9:])
            what = what.format(subject=topic)
            label = label.format(subject=topic)
        else:
            what = what.format(subject="sensitive topics")
            label = label.format(subject="sensitive topics")
        names = ", ".join(sorted(types))
        stmt = (f"An observer holding {names} data could infer: {what}. "
                f"This is what the sources could support, not a claim that anyone holds them or has drawn this conclusion.")
        self.new("observer_inference", "hypothesis", stmt, f"mirror_rule:{rule['name']}", [],
                 rule=rule["name"], segment_label=label, sources_required=sids, holders=holders,
                 typical_uses=list(rule["typical_uses"]), sensitive=sensitive,
                 rests_on=[f["id"] for f in rests], alternatives=list(rule["alternatives"]),
                 uncertainty="Rule over findings that are themselves exploratory; says nothing about what any real company does.",
                 confidence={"level": "low", "basis": "rule_over_exploratory_findings"}, status="hypothesis")

    def suggestions(self) -> None:
        for f in [f for f in self.findings if f["finding_kind"] == "lagged_association"]:
            if f["x_metric"] == "precip_mm" and f["y_metric"] == "office_visit" and f["rho"] < 0:
                ctx = [i for j in range(len(self.m.dates)) if (self.m.series["precip_mm"][j] or 0) > 0
                       and self.m.series["office_visit"][j] == 0.0 and self.m.weekdays[j] in self.office_weekdays()
                       for i in self.m.evidence["precip_mm"][j]]
                self.new("suggestion", "hypothesis",
                         "Context only: on rainy usual-office weekdays the office was visited less often. You may want to note "
                         "whether staying home on those days is a deliberate arrangement.",
                         "suggestion_rule:rainy_office_day", [], rests_on=[f["id"]], context_ids=self.cite(ctx), 
                         text="Optional note for the participant; not advice and not a prediction.",
                         alternatives=f["alternatives"],
                         uncertainty="Rests on one exploratory association; the participant knows the reason, the data does not.",
                         confidence={"level": "low", "basis": "rests_on_exploratory_association"}, status="hypothesis")

    def links(self) -> list[dict[str, Any]]:
        out = []
        for f in self.findings:
            ids = f["supporting_evidence_ids"]
            if ids:
                out.append({"id": f"link-{f['id']}", "type": "Link", "workspace_id": self.ws, "source_id": WORKSPACE_SOURCE,
                            "evidence_class": "inference", "link_type": "SUPPORTED_BY", "from": f["id"], "to": ids[0],
                            "evidence_ids": list(ids)})
        return out


# Declarative Mirror rule table. `requires` is a list of conditions that must all hold; ("any", [...]) needs one.
RULES: list[dict[str, Any]] = [
    {"name": "sleep_deprivation_low_activity",
     "segment_label": "possible sleep deprivation and declining activity",
     "statement": "a period of possible sleep deprivation together with declining daily activity",
     "requires": [("any", [("shift", "sleep_duration", "down"), ("shift", "sleep_onset", "up")]), ("shift", "steps", "down")],
     "source_types": ["SleepInterval", "DailyHealthAggregate"],
     "typical_uses": ["ad targeting categories such as sleep aids, caffeine, or delivery and fast-food promotions",
                      "wellness-product audience segments"],
     "sensitive": True,
     "alternatives": ["travel or a time-zone change", "illness or injury (not assessed)", "a new work or caring schedule",
                      "a watch or phone not worn or charged overnight (data gap)"]},
    {"name": "heavy_short_video_use",
     "segment_label": "heavy short-video use",
     "statement": "heavy and rising short-video use",
     "requires": [("any", [("shift", "short_video_minutes", "up"), ("level", "short_video_minutes", ">=", 90, 14)])],
     "source_types": ["ScreenTimeDaily"],
     "typical_uses": ["entertainment and impulse-purchase ad targeting", "engagement-based recommendation audiences"],
     "sensitive": False,
     "alternatives": ["a new job or hobby that uses video apps", "a changed app mix after an update", "a recording change in how categories are assigned"]},
    {"name": "possible_relationship_change",
     "segment_label": "possible change in the participant's messaging pattern with {subject}",
     "statement": "a possible change in the participant's own messaging pattern with {subject} (a hypothesis about the participant only)",
     "requires": [("shift", "messages_*", "down")], "per_match": True,
     "source_types": ["MessagingDaily"],
     "typical_uses": ["life-event ad segments (for example relationship or social-app targeting)"],
     "sensitive": True,
     "alternatives": ["travel", "a switch to another channel", "a changed phone or a re-installed app",
                      "a schedule change or a busy period"]},
    {"name": "sensitive_topic_interest",
     "segment_label": "rising interest in searches about {subject}",
     "statement": "a rising interest in searches about {subject} (topic interest only; it says nothing about the participant's health)",
     "requires": [("any", [("shift", "searches_*", "up"), ("shift", "sensitive_search_share", "up")])], "per_match": True,
     "source_types": ["AccountActivity"],
     "typical_uses": ["ad and content targeting by topic area", "recommendation feeds around the topic"],
     "sensitive": True,
     "alternatives": ["research for someone else or for work", "a news event or a one-off curiosity",
                      "changes in how topics are labelled by the keyword lexicon"]},
    {"name": "commuter_paid_parking",
     "segment_label": "commuter with a paid-parking routine",
     "statement": "a commuter who regularly pays for parking on office days",
     "requires": [("routine", "weekday_office"), ("routine", "recurring_spend:*park*")],
     "source_types": ["Visit", "Transaction"],
     "typical_uses": ["commute-related offers (fuel, transit, parking, insurance)", "location-based ad targeting around the workplace"],
     "sensitive": True,
     "alternatives": ["parking paid for a different reason on the same weekdays", "a shared or employer-reimbursed arrangement"]},
]


def _run(doc: dict[str, Any], alpha: float, seed: Any, permutations: int) -> tuple[list[dict[str, Any]], int]:
    if not isinstance(doc, dict) or not isinstance(doc.get("meta"), dict) or not isinstance(doc.get("records"), list):
        raise ValueError("document must be {meta, records[]}")
    if not isinstance(doc["meta"].get("workspace_id"), str):
        raise ValueError("meta.workspace_id required")
    run = _Run(doc, alpha, seed, permutations)
    run.shifts()
    for f in run.findings:
        if f["finding_kind"] == "shift":
            f["metrics_scanned"] = run.scanned
    run.associations()
    run.routines()
    run.missing_sources()
    run.mirror()
    check_guardrails(run.findings, run.cls)
    out: list[dict[str, Any]] = []
    if not any(isinstance(r, dict) and r.get("id") == WORKSPACE_SOURCE for r in doc["records"]):
        out.append(_workspace_source(run))
    out += run.findings + run.links()
    return out, run.scanned


def _workspace_source(run: _Run) -> dict[str, Any]:
    return {"id": WORKSPACE_SOURCE, "type": "Source", "workspace_id": run.ws, "source_id": WORKSPACE_SOURCE,
            "evidence_class": "observation", "name": "Derived", "system": "laplace-demo",
            "support": "supported_synthetic", "provisioning": "not_applicable_synthetic",
            "coverage_status": "not_applicable", "source_granularity": "not_applicable", "missing_periods": [],
            "export_success": "synthetic_fixture_ok", "record_count": 0, "latest_event_time": UNKNOWN,
            "note": "Findings, corrections; derived or participant-authored, not a collection source.",
            "provenance": {"source": "laplace-insights", "method": "source_summary", "method_version": VERSION,
                           "line_or_record": WORKSPACE_SOURCE}}


def check_guardrails(findings: list[dict[str, Any]], classes: dict[str, Any]) -> None:
    """Raise ValueError on a violated guardrail (a programming error, not a data error)."""
    for f in findings:
        text = " ".join(str(f.get(k, "")) for k in ("statement", "text", "uncertainty", "segment_label")) \
            + " " + " ".join(map(str, f.get("alternatives", [])))
        low = text.lower()
        for bad in BANNED_WORDING:
            if bad in low:
                raise ValueError(f"{f['id']}: banned wording {bad!r}")
        if f.get("causal_claim") is not False:
            raise ValueError(f"{f['id']}: causal_claim must be false")
        for eid in f.get("supporting_evidence_ids", []):
            if classes.get(eid) not in ("observation", "normalized_event"):
                raise ValueError(f"{f['id']}: cites a non-observation record as supporting evidence")
        if f["finding_kind"] == "observer_inference":
            if "could infer" not in f["statement"] or not isinstance(f.get("sensitive"), bool) or f.get("supporting_evidence_ids"):
                raise ValueError(f"{f['id']}: mirror finding must say 'could infer', flag sensitivity, cite via rests_on only")


def analyze(doc: dict[str, Any], *, alpha: float = 0.05, seed: Any = 0,
            permutations: int = DEFAULT_PERMUTATIONS) -> list[dict[str, Any]]:
    """New records only: Finding records, SUPPORTED_BY links, and src-workspace if missing. Input is not mutated."""
    return _run(_without_previous(doc), alpha, seed, permutations)[0]


def _without_previous(doc: dict[str, Any]) -> dict[str, Any]:
    """Analyze a view that excludes this engine's earlier output, so re-running is idempotent."""
    recs = [r for r in doc["records"] if not (isinstance(r, dict) and (r.get("provenance") or {}).get("source") == PROVENANCE_SOURCE
                                              and r.get("type") == "Finding")
            and not (isinstance(r, dict) and str(r.get("id", "")).startswith("link-ins-"))]
    return {"meta": doc["meta"], "records": recs}


def enrich(doc: dict[str, Any], *, alpha: float = 0.05, seed: Any = 0,
           permutations: int = DEFAULT_PERMUTATIONS) -> dict[str, Any]:
    """A NEW document: input records (minus any earlier insight output) plus new findings and links."""
    base = _without_previous(doc)
    new, scanned = _run(base, alpha, seed, permutations)
    out = copy.deepcopy({"meta": base["meta"], "records": base["records"]})
    out["records"] += copy.deepcopy(new)
    counts: dict[str, int] = {}
    for r in out["records"]:
        if isinstance(r, dict) and isinstance(r.get("type"), str):
            counts[r["type"]] = counts.get(r["type"], 0) + 1
    out["meta"]["type_counts"] = counts
    out["meta"]["insights"] = {"engine": ENGINE, "version": VERSION, "alpha": alpha, "metrics_scanned": scanned}
    return out


# --- demo -------------------------------------------------------------------------

def demo_document(days: int = 56, seed: int = 7) -> dict[str, Any]:
    """Small synthetic 0.2-style document with a planted step change at day days//2."""
    rng = random.Random(seed)
    start = datetime(2026, 3, 2)
    tz = "-05:00"
    recs: list[dict[str, Any]] = []

    def iso(d: int, minute: float = 0) -> str:
        return (start + timedelta(days=d, minutes=minute)).isoformat(timespec="minutes") + tz

    def add(rid: str, typ: str, src: str, gran: str, **f: Any) -> None:
        recs.append({"id": rid, "type": typ, "workspace_id": "ws-demo-insights", "source_id": src, "evidence_class": "observation",
                     "granularity": gran, "timezone": "Etc/GMT+5", "import_batch_id": "ib-demo", **f})

    for sid, name in (("src-health", "Health"), ("src-screen", "ScreenTime"), ("src-msg", "Messaging"),
                      ("src-weather", "Weather"), ("src-location", "Location"), ("src-card", "Transactions")):
        recs.append({"id": sid, "type": "Source", "workspace_id": "ws-demo-insights", "source_id": sid, "evidence_class": "observation",
                     "name": name, "missing_periods": []})
    recs.append({"id": "ib-demo", "type": "ImportBatch", "workspace_id": "ws-demo-insights", "source_id": "src-health",
                 "evidence_class": "observation"})
    for app in ("app-clips", "app-mail", "app-chat"):
        recs.append({"id": app, "type": "App", "workspace_id": "ws-demo-insights", "source_id": "src-screen", "evidence_class": "observation"})
    recs.append({"id": "place-home", "type": "Place", "workspace_id": "ws-demo-insights", "source_id": "src-location",
                 "evidence_class": "inference", "category": "home"})
    recs.append({"id": "place-work", "type": "Place", "workspace_id": "ws-demo-insights", "source_id": "src-location",
                 "evidence_class": "inference", "category": "work"})
    step = days // 2
    for d in range(days):
        late = d >= step
        wd = (start + timedelta(days=d)).weekday()
        rain = rng.random() < 0.3
        add(f"health-{d:03d}", "DailyHealthAggregate", "src-health", "aggregate", event_start=iso(d), event_end=iso(d + 1),
            steps=int(7000 * (0.7 if late else 1.0) + rng.gauss(0, 500)))
        add(f"st-{d:03d}-v", "ScreenTimeDaily", "src-screen", "aggregate", event_start=iso(d), event_end=iso(d + 1),
            app_id="app-clips", app_category="short_video", minutes=int((150 if late else 50) + rng.gauss(0, 10)),
            pickups=30, late_night_minutes=int((45 if late else 2) + abs(rng.gauss(0, 3))), summable=False)
        add(f"st-{d:03d}-m", "ScreenTimeDaily", "src-screen", "aggregate", event_start=iso(d), event_end=iso(d + 1),
            app_id="app-mail", app_category="productivity", minutes=int(40 + rng.gauss(0, 6)), pickups=20,
            late_night_minutes=0, summable=False)
        add(f"w-{d:03d}", "WeatherDaily", "src-weather", "aggregate", event_start=iso(d), event_end=iso(d + 1),
            precip_mm=round(rng.uniform(2, 12), 1) if rain else 0.0, temp_c_max=12, condition="rain" if rain else "dry")
        if d < step:
            add(f"msg-{d:03d}", "MessagingDaily", "src-msg", "aggregate", event_start=iso(d), event_end=iso(d + 1),
                app_id="app-chat", contact_ref="contact-A", sent=rng.randint(3, 6), received=rng.randint(3, 6))
        office = wd in (1, 2, 3) and not (rain and rng.random() < 0.7)
        add(f"visit-{d:03d}", "Visit", "src-location", "interval", event_start=iso(d, 9 * 60 if office else 0),
            event_end=iso(d, 17 * 60 if office else 600), place_id="place-work" if office else "place-home")
        if wd in (1, 2, 3):
            add(f"tx-{d:03d}", "Transaction", "src-card", "point", event_time=iso(d, 8 * 60 + 40),
                merchant_category="parking", amount=14.0, currency="CAD", place_id=UNKNOWN)
    counts: dict[str, int] = {}
    for r in recs:
        counts[r["type"]] = counts.get(r["type"], 0) + 1
    meta = {"contract_version": "persona-contract-0.2-provisional", "synthetic": True, "workspace_id": "ws-demo-insights",
            "timezone": "Etc/GMT+5", "window": {"start": iso(0), "end": iso(days)}, "type_counts": counts,
            "unknown_token": UNKNOWN,
            "evidence_classes": ["observation", "normalized_event", "hypothesis", "inference", "prediction"]}
    return {"meta": meta, "records": recs}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Insight engine over a built-in synthetic document (nothing is written).")
    ap.add_argument("--demo", action="store_true", help="run on the built-in synthetic demo document")
    ap.add_argument("--permutations", type=int, default=499)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)
    if not args.demo:
        ap.error("only --demo is supported; there is deliberately no raw-file input")
    doc = enrich(demo_document(), seed=args.seed, permutations=args.permutations)
    finds = [r for r in doc["records"] if r["type"] == "Finding"]
    print(json.dumps({"insights": doc["meta"]["insights"], "findings": len(finds)}, indent=1))
    for f in finds:
        print(f"[{f['finding_kind']}] {f['statement']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
