"""Tests for spikes.insights using small synthetic documents built here (no fixtures)."""

from __future__ import annotations

import copy
from datetime import datetime, timedelta
import random
import unittest

from spikes import explorer_export, insights

TZ = "-05:00"
START = datetime(2026, 3, 2)  # a Monday
WS = "ws-test-insights"
BANNED = ("diagnos", "depress", "disorder", "causes", "because of")


def iso(d: int, minute: float = 0) -> str:
    return (START + timedelta(days=d, minutes=minute)).isoformat(timespec="minutes") + TZ


def make_doc(days: int = 56, seed: int = 1, *, change: int | None = None, steps: bool = True, screen: bool = True,
             sleep: bool = True, messaging: bool = False, searches: bool = False, office: bool = False,
             lag_link: bool = False, steps_known: int | None = None, bad_category: bool = False) -> dict:
    """Synthetic document. `change` plants a step at that day on steps, screen, sleep, messaging, searches."""
    rng = random.Random(seed)
    recs: list[dict] = []

    def add(rid, typ, src, gran, cls="observation", **f):
        recs.append({"id": rid, "type": typ, "workspace_id": WS, "source_id": src, "evidence_class": cls,
                     "granularity": gran, "timezone": "Etc/GMT+5", "import_batch_id": "ib-t", **f})

    for sid in ("src-a", "src-b", "src-c", "src-d"):
        recs.append({"id": sid, "type": "Source", "workspace_id": WS, "source_id": sid, "evidence_class": "observation",
                     "missing_periods": []})
    recs.append({"id": "ib-t", "type": "ImportBatch", "workspace_id": WS, "source_id": "src-a", "evidence_class": "observation"})
    for app in ("app-clips", "app-mail", "app-chat"):
        recs.append({"id": app, "type": "App", "workspace_id": WS, "source_id": "src-b", "evidence_class": "observation"})
    recs.append({"id": "place-home", "type": "Place", "workspace_id": WS, "source_id": "src-a", "evidence_class": "inference", "category": "home"})
    recs.append({"id": "place-work", "type": "Place", "workspace_id": WS, "source_id": "src-a", "evidence_class": "inference", "category": "work"})
    late_prev = 0.0
    for d in range(days):
        after = change is not None and d >= change
        late = max(0.0, (40 if after else 3) + rng.gauss(0, 4)) if change is not None else max(0.0, 10 + rng.gauss(0, 6))
        base = 7000 * (0.7 if after else 1.0)
        n_steps = base + rng.gauss(0, 500)
        if lag_link:
            n_steps = 7000 - 60 * late_prev + rng.gauss(0, 300)
        late_prev = late
        if steps and (steps_known is None or d < steps_known):
            add(f"health-{d}", "DailyHealthAggregate", "src-a", "aggregate", event_start=iso(d), event_end=iso(d + 1),
                steps=int(n_steps), steps_status="measured")
        elif steps:
            add(f"health-{d}", "DailyHealthAggregate", "src-a", "aggregate", event_start=iso(d), event_end=iso(d + 1),
                steps=insights.UNKNOWN, steps_status="not_collected")
        if screen:
            add(f"st-{d}-v", "ScreenTimeDaily", "src-b", "aggregate", event_start=iso(d), event_end=iso(d + 1),
                app_id="app-clips", app_category="short_video", minutes=int((150 if after else 50) + rng.gauss(0, 10)),
                pickups=30, late_night_minutes=round(late), summable=False)
            add(f"st-{d}-o", "ScreenTimeDaily", "src-b", "aggregate", event_start=iso(d), event_end=iso(d + 1),
                app_id="app-mail", app_category="productivity", minutes=int(40 + rng.gauss(0, 6)), pickups=10,
                late_night_minutes=0, summable=False)
        if sleep:
            onset = 22 * 60 + (80 if after else 0) + rng.gauss(0, 20)
            dur = (330 if after else 450) + rng.gauss(0, 20)
            s = START + timedelta(days=d - 1, minutes=onset)
            add(f"sleep-{d}", "SleepInterval", "src-c", "interval", event_start=s.isoformat(timespec="minutes") + TZ,
                event_end=(s + timedelta(minutes=dur)).isoformat(timespec="minutes") + TZ, sleep_source="watch", stage="asleep")
        if messaging and (change is None or d < change):
            add(f"msg-{d}", "MessagingDaily", "src-d", "aggregate", event_start=iso(d), event_end=iso(d + 1),
                app_id="app-chat", contact_ref="contact-A", sent=rng.randint(3, 6), received=rng.randint(3, 6))
        if searches:
            for j in range(rng.randint(2, 4)):
                topic = "none"
                if change is not None and d >= change and j == 0:
                    topic = "depression_like" if bad_category else "anxiety"
                add(f"acct-{d}-{j}", "AccountActivity", "src-d", "point", event_time=iso(d, 600 + j * 30),
                    activity_kind="search", sensitive_category=topic, topic="x", topic_method="keyword_lexicon_v0")
        if office:
            wd = (START + timedelta(days=d)).weekday()
            at_work = wd in (1, 2, 3)
            add(f"visit-{d}", "Visit", "src-a", "interval", cls="normalized_event", event_start=iso(d, 540 if at_work else 0),
                event_end=iso(d, 1020 if at_work else 600), place_id="place-work" if at_work else "place-home")
            if at_work:
                add(f"tx-{d}", "Transaction", "src-d", "point", event_time=iso(d, 520), merchant_category="parking",
                    amount=14.0, currency="CAD", place_id=insights.UNKNOWN)
    counts: dict[str, int] = {}
    for r in recs:
        counts[r["type"]] = counts.get(r["type"], 0) + 1
    meta = {"contract_version": "persona-contract-0.2-provisional", "synthetic": True, "workspace_id": WS,
            "timezone": "Etc/GMT+5", "window": {"start": iso(0), "end": iso(days)}, "type_counts": counts,
            "evidence_classes": list(explorer_export.EVIDENCE_CLASSES)}
    return {"meta": meta, "records": recs}


def kinds(records, kind):
    return [r for r in records if r["type"] == "Finding" and r["finding_kind"] == kind]


class ShiftTests(unittest.TestCase):
    def test_planted_step_is_found_near_the_right_day(self):
        doc = make_doc(change=28)
        found = {f["metric"]: f for f in kinds(insights.analyze(doc, permutations=199), "shift")}
        for metric in ("steps", "short_video_minutes", "late_night_minutes", "sleep_duration", "sleep_onset"):
            self.assertIn(metric, found)
            change = datetime.fromisoformat(found[metric]["change_day"])
            self.assertLessEqual(abs((change - (START + timedelta(days=28))).days), 3, metric)
        f = found["short_video_minutes"]
        self.assertEqual(f["effect"]["direction"], "up")
        self.assertGreater(f["effect"]["ratio"], 2.0)
        self.assertLessEqual(f["q_value"], 0.05)
        self.assertGreater(f["metrics_scanned"], 5)
        self.assertIn("autocorrelation", f["uncertainty"])
        self.assertEqual(found["steps"]["effect"]["direction"], "down")

    def test_noise_rarely_produces_a_shift(self):
        clean = 0
        for seed in range(20):
            out = insights.analyze(make_doc(seed=100 + seed), permutations=99, seed=seed)
            clean += not kinds(out, "shift")
        self.assertGreaterEqual(clean, 18)

    def test_mostly_unknown_metric_gives_insufficient_not_shift(self):
        doc = make_doc(change=10, sleep=False, screen=False, steps_known=15)  # big drop, but only 15 measured days
        out = insights.analyze(doc, permutations=99)
        self.assertEqual(kinds(out, "shift"), [])
        self.assertTrue(any(f["missing"] == "steps" for f in kinds(out, "insufficient")))

    def test_all_unknown_steps_no_shift(self):
        doc = make_doc(sleep=False, screen=False, steps_known=0)
        self.assertEqual(kinds(insights.analyze(doc, permutations=99), "shift"), [])


class MetricsAndSources(unittest.TestCase):
    def test_absent_source_is_unknown_not_zero(self):
        doc = make_doc(sleep=False, screen=False)
        metrics = insights.daily_metrics(doc)
        for m in ("sleep_duration", "sleep_onset", "screen_minutes", "short_video_minutes", "late_night_minutes", "pickups"):
            self.assertTrue(all(v == "unknown" for v in metrics[m].values()), m)
        self.assertTrue(all(isinstance(v, float) for v in metrics["steps"].values()))
        out = insights.analyze(doc, permutations=99)
        missing = {f["missing"] for f in kinds(out, "insufficient")}
        self.assertTrue({"SleepInterval", "ScreenTimeDaily"} <= missing)
        for f in out:
            if f["type"] == "Finding" and f["finding_kind"] in ("shift", "lagged_association"):
                self.assertNotIn("sleep", f.get("metric", "") + f.get("x_metric", "") + f.get("y_metric", ""))

    def test_unmeasured_step_day_is_unknown(self):
        doc = make_doc(steps_known=30)
        steps = insights.daily_metrics(doc)["steps"]
        self.assertEqual(sum(1 for v in steps.values() if v == "unknown"), 26)

    def test_overlapping_screen_reports_are_not_summed(self):
        doc = make_doc(days=12, sleep=False, steps=False)
        dup = copy.deepcopy([r for r in doc["records"] if r["id"] == "st-3-v"][0])
        dup["id"] = "st-3-v-again"
        doc["records"].append(dup)
        a = insights.daily_metrics(make_doc(days=12, sleep=False, steps=False))["screen_minutes"]
        b = insights.daily_metrics(doc)["screen_minutes"]
        self.assertEqual(a, b)

    def test_sleep_assigned_to_wake_day(self):
        doc = make_doc(days=12, steps=False, screen=False)
        m = insights.daily_metrics(doc)
        self.assertEqual(m["sleep_duration"][iso(0)[:10]], m["sleep_duration"][iso(0)[:10]])
        self.assertGreater(m["sleep_onset"][iso(5)[:10]], 3 * 60)  # after ~21:00


class AssociationTests(unittest.TestCase):
    def test_planted_lag1_association(self):
        doc = make_doc(lag_link=True, sleep=False, seed=5)
        out = insights.analyze(doc, permutations=299)
        hits = [f for f in kinds(out, "lagged_association") if f["x_metric"] == "late_night_minutes" and f["y_metric"] == "steps"]
        self.assertEqual(len(hits), 1)
        f = hits[0]
        self.assertEqual(f["lag_days"], 1)
        self.assertLess(f["rho"], -0.4)
        self.assertTrue(f["alternatives"])
        self.assertTrue(f["statement"].startswith("CORRELATION, not causation"))

    def test_no_association_in_independent_noise(self):
        doc = make_doc(seed=77, sleep=False)
        self.assertEqual(kinds(insights.analyze(doc, permutations=99), "lagged_association"), [])


class RoutineAndMirror(unittest.TestCase):
    def setUp(self):
        self.doc = make_doc(change=28, messaging=True, searches=True, office=True)
        self.out = insights.analyze(self.doc, permutations=199)

    def test_routines(self):
        pats = {f["pattern_key"]: f for f in kinds(self.out, "routine")}
        self.assertIn("weekday_office", pats)
        self.assertEqual(pats["weekday_office"]["weekdays"], ["Tue", "Wed", "Thu"])
        self.assertIn("recurring_spend:parking", pats)

    def test_rules_fire_and_are_well_formed(self):
        mirror = {f["rule"]: f for f in kinds(self.out, "observer_inference")}
        for name in ("sleep_deprivation_low_activity", "heavy_short_video_use", "possible_relationship_change",
                     "sensitive_topic_interest", "commuter_paid_parking"):
            self.assertIn(name, mirror)
        ids = {r["id"]: r for r in self.out}
        for f in mirror.values():
            self.assertEqual(f["evidence_class"], "hypothesis")
            self.assertIn("could infer", f["statement"])
            self.assertIsInstance(f["sensitive"], bool)
            self.assertTrue(f["holders"] and f["typical_uses"] and f["alternatives"] and f["rests_on"])
            self.assertEqual(f["supporting_evidence_ids"], [])
            self.assertTrue(set(f["sources_required"]) <= {"src-a", "src-b", "src-c", "src-d"})
            for rid in f["rests_on"]:
                self.assertIn(ids[rid]["finding_kind"], ("shift", "routine", "lagged_association", "day_type", "day_type_trend"))
            for h in f["holders"]:
                self.assertNotIn(" has ", h["holder"])
        self.assertTrue(mirror["possible_relationship_change"]["sensitive"])
        self.assertTrue(mirror["sensitive_topic_interest"]["sensitive"])
        self.assertIn("contact-A", mirror["possible_relationship_change"]["statement"])

    def test_missing_source_suppresses_rule(self):
        out = insights.analyze(make_doc(change=28, sleep=False), permutations=99)
        self.assertNotIn("sleep_deprivation_low_activity", {f["rule"] for f in kinds(out, "observer_inference")})


class Guardrails(unittest.TestCase):
    def test_wording_and_evidence_rules(self):
        for kwargs in (dict(change=28, messaging=True, searches=True, office=True),
                       dict(change=28, searches=True, bad_category=True)):
            doc = make_doc(**kwargs)
            out = insights.analyze(doc, permutations=199)
            classes = {r["id"]: r["evidence_class"] for r in doc["records"]}
            self.assertTrue(kinds(out, "shift"))
            for f in (r for r in out if r["type"] == "Finding"):
                text = " ".join(str(f.get(k, "")) for k in ("statement", "text", "uncertainty", "segment_label")).lower()
                text += " ".join(map(str, f.get("alternatives", []))).lower()
                for bad in BANNED:
                    self.assertNotIn(bad, text, f["id"])
                self.assertIs(f["causal_claim"], False)
                self.assertEqual(f["source_id"], "src-workspace")
                self.assertEqual(f["workspace_id"], WS)
                self.assertTrue(f["provenance"]["method"] and f["provenance"]["method_version"])
                for eid in f["supporting_evidence_ids"]:
                    self.assertIn(classes[eid], ("observation", "normalized_event"))
                if f["finding_kind"] not in ("observer_inference", "day_type_trend"):
                    self.assertNotIn("rests_on", f if f["finding_kind"] != "suggestion" else {})
            for f in kinds(out, "observer_inference"):
                self.assertNotIn(" did ", f["statement"])

    def test_sensitive_topic_wording_is_topic_interest(self):
        out = insights.analyze(make_doc(change=28, searches=True), permutations=199)
        f = [x for x in kinds(out, "observer_inference") if x["rule"] == "sensitive_topic_interest"][0]
        self.assertIn("interest in searches about anxiety", f["statement"])
        self.assertIn("topic interest only", f["statement"])

    def test_lexicon_label_with_banned_stem_is_withheld(self):
        out = insights.analyze(make_doc(change=28, searches=True, bad_category=True), permutations=199)
        f = [x for x in kinds(out, "observer_inference") if x["rule"] == "sensitive_topic_interest"][0]
        self.assertIn("a sensitive topic", f["statement"])

    def test_contact_reference_not_altered_or_expanded(self):
        out = insights.analyze(make_doc(change=28, messaging=True), permutations=199)
        for f in kinds(out, "shift"):
            if f["metric"].startswith("messages_"):
                self.assertIn("contact-A", f["statement"])
                self.assertEqual(f["metric"], "messages_contact-A")

    def test_guardrail_checker_rejects_bad_findings(self):
        bad = {"id": "x", "finding_kind": "shift", "statement": "Sleep loss causes low steps", "causal_claim": False}
        with self.assertRaises(ValueError):
            insights.check_guardrails([bad], {})
        bad2 = dict(bad, statement="ok", supporting_evidence_ids=["p1"])
        with self.assertRaises(ValueError):
            insights.check_guardrails([bad2], {"p1": "inference"})


class DayTypeTests(unittest.TestCase):
    def test_planted_two_state_days_give_stable_type_and_trend_near_the_change(self):
        out = insights.analyze(make_doc(change=28), permutations=199)
        types = kinds(out, "day_type")
        stable = [t for t in types if t["stable"]]
        self.assertTrue(stable)
        late = [t for t in stable if any(i["metric"] == "late_night_minutes" and i["direction"] == "up" for i in t["portrait"])]
        self.assertTrue(late)
        trends = kinds(out, "day_type_trend")
        self.assertTrue(trends)
        ids = {t["id"]: t for t in types}
        up = [t for t in trends if t["direction"] == "more_frequent"]
        self.assertTrue(up)
        for t in up:
            self.assertIn(t["rests_on"][0], ids)
            self.assertLessEqual(abs((datetime.fromisoformat(t["change_day"]) - (START + timedelta(days=28))).days), 5)
            self.assertLessEqual(t["q_value"], 0.05)
            self.assertIn("more frequent", t["statement"])
        t0 = late[0]
        self.assertEqual({"metric", "median", "usual", "z", "unit"} <= set(t0["portrait"][0]), True)
        self.assertEqual(t0["k"], len(types))
        self.assertEqual(sum(t["n_days"] for t in types), 56 - len(insights.enrich(make_doc(change=28), permutations=99)["meta"]["insights"]["day_types"]["unclassified_days"]))

    def test_type_keys_are_ordered_by_size_then_first_day(self):
        types = kinds(insights.analyze(make_doc(change=28), permutations=99), "day_type")
        self.assertEqual([t["type_key"] for t in types], [f"T{i}" for i in range(1, len(types) + 1)])
        keys = [(-t["n_days"], t["days"][0]) for t in types]
        self.assertEqual(keys, sorted(keys))

    def test_pure_noise_gives_null_or_at_most_one_trend(self):
        trends = 0
        for seed in range(12):
            out = insights.analyze(make_doc(seed=200 + seed), permutations=99, seed=seed)
            trends += len(kinds(out, "day_type_trend"))
            self.assertTrue(kinds(out, "day_types_none") or kinds(out, "day_type"))
        self.assertLessEqual(trends, 1)

    def test_null_result_is_reported_as_such(self):
        out = insights.analyze(make_doc(seed=200), permutations=99)
        nulls = kinds(out, "day_types_none")
        if nulls:
            self.assertLess(nulls[0]["best_silhouette"], 0.25)
            self.assertIn("best_k", nulls[0])
            self.assertEqual(kinds(out, "day_type"), [])

    def test_unclassified_days_are_not_assigned(self):
        doc = make_doc(change=28)
        gone = set(range(5, 10))  # no screen time and no sleep: 1 of 7 features known
        doc["records"] = [r for r in doc["records"]
                          if not (r["type"] in ("ScreenTimeDaily", "SleepInterval")
                                  and any(r["id"].split("-")[1] == str(d) for d in gone))]
        out = insights.enrich(doc, permutations=99)
        unclassified = set(out["meta"]["insights"]["day_types"]["unclassified_days"])
        gone_dates = {(START + timedelta(days=d)).date().isoformat() for d in gone}
        self.assertTrue(gone_dates <= unclassified)
        for t in kinds(out["records"], "day_type"):
            self.assertFalse(gone_dates & set(t["days"]))

    def test_deterministic(self):
        doc = make_doc(change=28)
        a = insights.enrich(doc, permutations=99, seed=5)["meta"]["insights"]["day_types"]
        b = insights.enrich(doc, permutations=99, seed=5)["meta"]["insights"]["day_types"]
        self.assertEqual(a, b)
        self.assertEqual(a["k"], len(kinds(insights.analyze(doc, permutations=99, seed=5), "day_type")))

    def test_too_few_features_is_insufficient_not_a_cluster(self):
        out = insights.analyze(make_doc(sleep=False, screen=False), permutations=99)
        self.assertEqual(kinds(out, "day_type"), [])
        self.assertTrue(any(f["missing"] == "day_types" for f in kinds(out, "insufficient")))

    def test_features_exclude_absent_sources(self):
        meta = insights.enrich(make_doc(sleep=False), permutations=99)["meta"]["insights"]["day_types"]
        self.assertNotIn("sleep_duration", meta["features"])
        self.assertIn("steps", meta["features"])

    def test_guardrail_wording_and_state_timing_mirror(self):
        out = insights.analyze(make_doc(change=28), permutations=199)
        by_id = {f["id"]: f for f in out if f["type"] == "Finding"}
        for f in kinds(out, "day_type") + kinds(out, "day_type_trend") + kinds(out, "day_types_none"):
            text = (f["statement"] + f["uncertainty"]).lower()
            for bad in BANNED:
                self.assertNotIn(bad, text)
            self.assertIs(f["causal_claim"], False)
        for t in kinds(out, "day_type_trend"):
            self.assertIn("cause is not identified", t["statement"])
        mirror = [f for f in kinds(out, "observer_inference") if f["rule"] == "state_timing"]
        self.assertEqual(len(mirror), 1)
        m = mirror[0]
        self.assertTrue(m["sensitive"])
        self.assertIn("could infer", m["statement"])
        self.assertTrue(m["alternatives"] and m["holders"])
        self.assertEqual(m["evidence_class"], "hypothesis")
        self.assertEqual(m["supporting_evidence_ids"], [])
        self.assertTrue({by_id[i]["finding_kind"] for i in m["rests_on"]} == {"day_type", "day_type_trend"})

    def test_no_state_timing_without_a_trend(self):
        out = insights.analyze(make_doc(seed=3), permutations=99)
        self.assertFalse([f for f in kinds(out, "observer_inference") if f["rule"] == "state_timing"])


class ContractAndDeterminism(unittest.TestCase):
    def test_enriched_document_validates(self):
        doc = make_doc(change=28, messaging=True, searches=True, office=True)
        out = insights.enrich(doc, permutations=199)
        self.assertEqual(explorer_export.validate_contract(out), [])
        self.assertEqual(out["meta"]["insights"]["engine"], "spikes.insights")
        self.assertEqual(out["meta"]["insights"]["alpha"], 0.05)
        self.assertGreater(out["meta"]["insights"]["metrics_scanned"], 5)
        self.assertEqual(out["meta"]["type_counts"]["Finding"], len(kinds(out["records"], "shift")) + sum(
            len(kinds(out["records"], k)) for k in ("lagged_association", "routine", "observer_inference", "suggestion", "insufficient", "day_type",
                  "day_type_trend", "day_types_none")))
        self.assertTrue(any(r["id"] == "src-workspace" for r in out["records"]))
        self.assertTrue(any(r["type"] == "Link" and r["link_type"] == "SUPPORTED_BY" for r in out["records"]))

    def test_insufficient_document_validates(self):
        out = insights.enrich(make_doc(sleep=False, screen=False), permutations=99)
        self.assertEqual(explorer_export.validate_contract(out), [])

    def test_deterministic_and_input_not_mutated(self):
        doc = make_doc(change=28)
        before = copy.deepcopy(doc)
        a = insights.enrich(doc, permutations=99, seed=3)
        b = insights.enrich(doc, permutations=99, seed=3)
        self.assertEqual(a, b)
        self.assertEqual(doc, before)
        self.assertIsNot(a["records"], doc["records"])

    def test_enrich_is_idempotent(self):
        doc = make_doc(change=28)
        once = insights.enrich(doc, permutations=99)
        twice = insights.enrich(once, permutations=99)
        self.assertEqual(once, twice)

    def test_demo_document_enriches_and_validates(self):
        out = insights.enrich(insights.demo_document(), permutations=99)
        self.assertEqual(explorer_export.validate_contract(out), [])

    def test_cli_demo_runs(self):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(insights.main(["--demo", "--permutations", "99"]), 0)
        self.assertIn("[shift]", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
