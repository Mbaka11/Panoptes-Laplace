"""Integration: the insight engine scored against the hidden scenario truth of each synthetic profile.

Known limits are asserted as limits, not hidden: the search_drift share change is near the
detection boundary at this sample size, and a -7% minutes-away change is below it.
"""
import unittest
from datetime import date

from spikes import explorer_export, insights, profiles

ALIAS = {"messages_contact_A": "messages_contact-A", "total_screen_minutes": "screen_minutes",
         "searches_sensitive_share": "sensitive_search_share", "minutes_away_from_home": "minutes_away"}


def _findings(key, seed=0):
    doc = insights.enrich(profiles.build(key), seed=seed)
    return doc, [r for r in doc["records"] if r["type"] == "Finding"]


def _kind(findings, kind):
    return [f for f in findings if f["finding_kind"] == kind]


def _day(doc, iso):
    start = date.fromisoformat(doc["meta"]["window"]["start"][:10])
    return (date.fromisoformat(iso) - start).days


class ProfileScoring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = {k: _findings(k) for k in profiles.PROFILES}

    def test_every_enriched_profile_is_valid(self):
        for key, (doc, _) in self.out.items():
            self.assertEqual(explorer_export.validate_contract(doc), [], key)

    def test_null_profiles_report_no_shift(self):
        for key in ("steady", "commuter", "sparse"):
            self.assertEqual(_kind(self.out[key][1], "shift"), [], key)

    def test_doomscroll_all_planted_shifts_near_the_change_day(self):
        doc, fs = self.out["doomscroll"]
        truth = profiles.scenario_truth("doomscroll")["planted_changes"]
        found = {f["metric"]: f for f in _kind(fs, "shift")}
        for c in truth:
            metric = ALIAS.get(c["metric"], c["metric"])
            self.assertIn(metric, found, metric)
            self.assertLessEqual(abs(_day(doc, found[metric]["change_day"]) - c["change_day"]), 3, metric)
            self.assertEqual(found[metric]["effect"]["direction"], c["direction"], metric)
        self.assertEqual(set(found), {ALIAS.get(c["metric"], c["metric"]) for c in truth})

    def test_doomscroll_planted_lag_and_mirror(self):
        _, fs = self.out["doomscroll"]
        lags = {(f["x_metric"], f["y_metric"], f["lag_days"]): f for f in _kind(fs, "lagged_association")}
        self.assertIn(("late_night_minutes", "steps", 1), lags)
        self.assertLess(lags[("late_night_minutes", "steps", 1)]["rho"], 0)
        labels = {f["segment_label"] for f in _kind(fs, "observer_inference")}
        self.assertTrue(any("sleep" in s for s in labels))
        self.assertTrue(any("short-video" in s for s in labels))

    def test_social_drop_contact_change_is_a_hypothesis_about_the_participant(self):
        doc, fs = self.out["social_drop"]
        contact = [f for f in _kind(fs, "shift") if f["metric"] == "messages_contact-A"]
        self.assertEqual(len(contact), 1)
        self.assertEqual(_day(doc, contact[0]["change_day"]), 31)
        mirror = [f for f in _kind(fs, "observer_inference") if "contact-A" in f["segment_label"]]
        self.assertEqual(len(mirror), 1)
        self.assertEqual(mirror[0]["evidence_class"], "hypothesis")
        self.assertTrue(mirror[0]["sensitive"])
        self.assertTrue(mirror[0]["alternatives"])

    def test_commuter_context_routine_and_suggestion(self):
        _, fs = self.out["commuter"]
        lags = {(f["x_metric"], f["y_metric"]) for f in _kind(fs, "lagged_association")}
        self.assertIn(("precip_mm", "office_visit"), lags)
        self.assertTrue(any("parking" in f["statement"] for f in _kind(fs, "routine")))
        self.assertTrue(_kind(fs, "suggestion"))
        for s in _kind(fs, "suggestion"):
            self.assertEqual(s["evidence_class"], "hypothesis")

    def test_sparse_reports_insufficient_not_zero(self):
        _, fs = self.out["sparse"]
        missing = {f["missing"] for f in _kind(fs, "insufficient")}
        self.assertIn("SleepInterval", missing)
        self.assertIn("ScreenTimeDaily", missing)

    def test_doomscroll_day_type_and_trend_near_the_change_day(self):
        doc, fs = self.out["doomscroll"]
        late = [t for t in _kind(fs, "day_type") if t["stable"] and any(
            i["metric"] == "late_night_minutes" and i["direction"] == "up" for i in t["portrait"])]
        self.assertTrue(late)
        self.assertTrue(any(i["metric"] in ("steps", "sleep_duration") and i["direction"] == "down"
                            for t in late for i in t["portrait"]))
        trends = [t for t in _kind(fs, "day_type_trend") if t["direction"] == "more_frequent"
                  and t["rests_on"][0] in {x["id"] for x in late}]
        self.assertTrue(trends)
        for t in trends:
            self.assertLessEqual(abs(_day(doc, t["change_day"]) - 28), 5)
        self.assertTrue(any(f["rule"] == "state_timing" for f in _kind(fs, "observer_inference")))

    def test_steady_has_no_day_type_trend(self):
        self.assertEqual(_kind(self.out["steady"][1], "day_type_trend"), [])

    def test_sparse_day_types_use_no_sleep_or_screen_features(self):
        doc, fs = self.out["sparse"]
        feats = doc["meta"]["insights"]["day_types"]["features"]
        for f in ("sleep_onset", "sleep_duration", "screen_minutes", "short_video_minutes", "late_night_minutes", "pickups"):
            self.assertNotIn(f, feats)
        for t in _kind(fs, "day_type"):
            self.assertFalse({i["metric"] for i in t["portrait"]} & set(("sleep_onset", "sleep_duration", "screen_minutes")))

    def test_day_type_meta_present_on_every_profile(self):
        for key, (doc, _) in self.out.items():
            dtm = doc["meta"]["insights"]["day_types"]
            self.assertEqual(set(dtm), {"features", "silhouette_by_k", "k", "unclassified_days"}, key)

    def test_known_power_limit_search_drift_never_wrong_direction(self):
        # Near the detection boundary (about 4 searches/day, 10% -> 40% sensitive share, 16 metrics
        # under BH): detection depends on the permutation seed. When found, it must point up.
        doc, fs = self.out["search_drift"]
        for f in _kind(fs, "shift"):
            self.assertEqual(f["metric"], "sensitive_search_share")
            self.assertEqual(f["effect"]["direction"], "up")


if __name__ == "__main__":
    unittest.main()
