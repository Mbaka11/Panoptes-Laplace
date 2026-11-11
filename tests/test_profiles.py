import json
import re
import unittest
from datetime import datetime

from spikes import explorer_export, profiles

START = datetime(2026, 1, 5)


def day_of(rec):
    return (datetime.fromisoformat((rec.get("event_start") or rec["event_time"])[:10]) - START).days


def of_type(doc, typ):
    return [r for r in doc["records"] if r["type"] == typ]


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs)


def daily(doc, typ, value, pred=lambda r: True):
    out = {d: 0.0 for d in range(profiles.DAYS)}
    for r in of_type(doc, typ):
        if pred(r):
            out[day_of(r)] += value(r)
    return out


def split(series, day):
    return mean(v for d, v in series.items() if d < day), mean(v for d, v in series.items() if d >= day)


class ProfileCase(unittest.TestCase):
    docs = {}

    @classmethod
    def setUpClass(cls):
        cls.docs = {k: profiles.build(k) for k in profiles.PROFILES}


class Invariants(ProfileCase):
    def test_profiles_and_validator(self):
        self.assertEqual(profiles.PROFILES, ("steady", "doomscroll", "social_drop", "search_drift", "commuter", "sparse"))
        for k, doc in self.docs.items():
            with self.subTest(k):
                self.assertEqual(explorer_export.validate_contract(doc), [])
                self.assertLess(len(profiles.dumps(doc)), 1_500_000)

    def test_meta(self):
        for k, doc in self.docs.items():
            m = doc["meta"]
            with self.subTest(k):
                self.assertEqual(m["contract_version"], "persona-contract-0.2-provisional")
                self.assertIs(m["synthetic"], True)
                self.assertEqual(m["profile"], k)
                self.assertEqual(m["unknown_token"], "unknown")
                self.assertEqual(m["evidence_classes"], list(profiles.EVIDENCE_CLASSES))
                self.assertIn("PROVISIONAL", m["status"])
                self.assertEqual(m["timezone"], "Etc/GMT+5")
                self.assertTrue(m["profile_description"].startswith("Synthetic profile"))

    def test_workspace_ids_unique(self):
        ids = [d["meta"]["workspace_id"] for d in self.docs.values()]
        self.assertEqual(len(set(ids)), 6)
        for k, doc in self.docs.items():
            self.assertTrue(all(r["workspace_id"] == doc["meta"]["workspace_id"] for r in doc["records"]))

    def test_determinism(self):
        for k in profiles.PROFILES:
            self.assertEqual(profiles.dumps(profiles.build(k)), profiles.dumps(self.docs[k]))

    def test_no_scenario_leak(self):
        for k, doc in self.docs.items():
            text = profiles.dumps(doc).lower()
            for word in ("change_day", "planted", "scenario", "approx_ratio", "expected_absent", "realized"):
                self.assertNotIn(word, text, (k, word))
            self.assertEqual(text.count('"profile":'), 1)
        self.assertIn("change_day", json.dumps(profiles.scenario_truth("doomscroll")))

    def test_unknown_never_zero(self):
        for k, doc in self.docs.items():
            for r in of_type(doc, "DailyHealthAggregate"):
                if r["steps_status"] != "measured":
                    self.assertEqual(r["steps"], "unknown", k)
                else:
                    self.assertGreater(r["steps"], 0)
        # sparse has genuinely unknown steps days and location-off days without Visit records
        sp = self.docs["sparse"]
        self.assertGreaterEqual(sum(1 for r in of_type(sp, "DailyHealthAggregate") if r["steps"] == "unknown"), 8)
        days_with_visits = {day_of(r) for r in of_type(sp, "Visit")}
        self.assertLess(len(days_with_visits), 48)

    def test_messaging_pseudonymous(self):
        allowed = {"id", "type", "workspace_id", "source_id", "evidence_class", "granularity", "app_id", "contact_ref",
                   "sent", "received", "provenance", "import_batch_id", "timezone", "event_start", "event_end"}
        for k, doc in self.docs.items():
            recs = of_type(doc, "MessagingDaily")
            self.assertEqual(len(recs), 3 * profiles.DAYS)
            for r in recs:
                self.assertRegex(r["contact_ref"], r"^contact-[A-Z]$")
                self.assertLessEqual(set(r), allowed)

    def test_screen_time_not_summable_and_absent_in_sparse(self):
        for k, doc in self.docs.items():
            recs = of_type(doc, "ScreenTimeDaily") + of_type(doc, "NotificationDaily")
            if k == "sparse":
                self.assertEqual(recs, [])
                self.assertFalse(any("screentime" in r["id"] for r in doc["records"] if r["type"] == "Source"))
            else:
                self.assertTrue(recs)
                for r in of_type(doc, "ScreenTimeDaily"):
                    self.assertIs(r["summable"], False)

    def test_sparse_sleep_unknown(self):
        sp = self.docs["sparse"]
        self.assertEqual(of_type(sp, "SleepInterval"), [])
        hk = next(r for r in sp["records"] if r["id"] == "src-healthkit")
        self.assertEqual(hk["sleep_read_status"], "unknown")
        self.assertTrue(all(r["sleep_read_status"] == "unknown" for r in of_type(sp, "DailyHealthAggregate")))
        for k in profiles.PROFILES:
            if k != "sparse":
                self.assertTrue(of_type(self.docs[k], "SleepInterval"))

    def test_sources_carry_availability(self):
        for doc in self.docs.values():
            for s in of_type(doc, "Source"):
                self.assertTrue(s["availability"])
                self.assertIn("support", s)
                self.assertIn("provisioning", s)

    def test_search_records_carry_topics(self):
        for doc in self.docs.values():
            searches = [r for r in of_type(doc, "AccountActivity") if r["activity_kind"] == "search"]
            self.assertTrue(searches)
            for r in searches:
                self.assertEqual(r["topic_method"], "keyword_lexicon_v0")
                self.assertIn(r["sensitive_category"], ("none", "health", "mental_health"))

    def test_transactions_only_commuter(self):
        for k, doc in self.docs.items():
            self.assertEqual(bool(of_type(doc, "Transaction")), k == "commuter")


class Effects(ProfileCase):
    def test_doomscroll(self):
        d = self.docs["doomscroll"]
        sv = daily(d, "ScreenTimeDaily", lambda r: r["minutes"], lambda r: r["app_category"] == "short_video")
        a, b = split(sv, 28)
        self.assertGreater(b, 2 * a)
        late = daily(d, "ScreenTimeDaily", lambda r: r["late_night_minutes"])
        a, b = split(late, 28)
        self.assertGreater(b, 5 * a)
        steps = {day_of(r): r["steps"] for r in of_type(d, "DailyHealthAggregate") if r["steps"] != "unknown"}
        before = mean(v for k, v in steps.items() if k < 28)
        after = mean(v for k, v in steps.items() if k >= 28)
        self.assertLess(after, 0.8 * before)
        sl = [(int(r["id"][6:]) - 1, r) for r in of_type(d, "SleepInterval")]  # night of day d

        def onset(r):
            s = datetime.fromisoformat(r["event_start"]).replace(tzinfo=None)
            return (s - START).total_seconds() / 60 - (int(r["id"][6:]) - 1) * 1440 - 18 * 60

        def dur(r):
            return (datetime.fromisoformat(r["event_end"]) - datetime.fromisoformat(r["event_start"])).total_seconds() / 60

        self.assertGreater(mean(onset(r) for k, r in sl if k >= 28), mean(onset(r) for k, r in sl if k < 28) + 45)
        self.assertLess(mean(dur(r) for k, r in sl if k >= 28), mean(dur(r) for k, r in sl if k < 28) - 45)
        # lagged: more late-night minutes on a day, fewer steps the next day (raw sign check)
        xs = [late[k] for k in range(55) if k + 1 in steps]
        ys = [steps[k + 1] for k in range(55) if k + 1 in steps]
        mx, my = mean(xs), mean(ys)
        cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        self.assertLess(cov, 0)

    def test_social_drop(self):
        d = self.docs["social_drop"]
        for c, expect_zero in (("contact-A", True), ("contact-B", False), ("contact-C", False)):
            s = daily(d, "MessagingDaily", lambda r: r["sent"] + r["received"], lambda r, c=c: r["contact_ref"] == c)
            a, b = split(s, 31)
            if expect_zero:
                self.assertEqual(b, 0.0)
                self.assertGreater(a, 8)
            else:
                self.assertTrue(0.7 < b / a < 1.4, (c, a, b))

    def test_search_drift(self):
        d = self.docs["search_drift"]
        s = [r for r in of_type(d, "AccountActivity") if r["activity_kind"] == "search"]

        def share(rs):
            return sum(1 for r in rs if r["sensitive_category"] != "none") / len(rs)

        a, b = share([r for r in s if day_of(r) < 24]), share([r for r in s if day_of(r) >= 24])
        self.assertGreater(b, 2 * a)
        self.assertTrue(any("anxiety" in r["title"] or "asleep" in r["title"] for r in s))

    def test_commuter(self):
        d = self.docs["commuter"]
        work = {day_of(r) for r in of_type(d, "Visit") if r["place_id"] == "place-work"}
        self.assertTrue(work)
        self.assertTrue(all(k % 7 in (1, 2, 3) for k in work))
        tx = [r for r in of_type(d, "Transaction") if r["merchant_category"] == "parking"]
        self.assertEqual({day_of(r) for r in tx}, work)
        rain = {day_of(r): r["precip_mm"] for r in of_type(d, "WeatherDaily")}
        off = {r for r in work}
        planned = [k for k in range(profiles.DAYS) if k % 7 in (1, 2, 3)]
        located = [k for k in planned if k not in profiles.scenario_truth("commuter")["realized"]["location_off_days"]]
        wet = [k for k in located if rain[k] >= 2.0]
        dry = [k for k in located if rain[k] < 2.0]
        self.assertGreaterEqual(len(wet), 4)
        self.assertGreater(sum(k in off for k in dry) / len(dry), 0.95)
        self.assertLess(sum(k in off for k in wet) / len(wet), 0.4)

    def test_steady_is_flat(self):
        d = self.docs["steady"]
        steps = {day_of(r): r["steps"] for r in of_type(d, "DailyHealthAggregate") if r["steps"] != "unknown"}
        series = {
            "steps": steps,
            "total_screen": daily(d, "ScreenTimeDaily", lambda r: r["minutes"]),
            "short_video": daily(d, "ScreenTimeDaily", lambda r: r["minutes"], lambda r: r["app_category"] == "short_video"),
            "pickups": daily(d, "ScreenTimeDaily", lambda r: r["pickups"]),
            "notifications": daily(d, "NotificationDaily", lambda r: r["count"]),
            "contact_A": daily(d, "MessagingDaily", lambda r: r["sent"] + r["received"], lambda r: r["contact_ref"] == "contact-A"),
        }
        for name, s in series.items():
            a, b = split(s, 28)
            self.assertLess(abs(b / a - 1), 0.15, (name, a, b))
        a, b = split(daily(d, "ScreenTimeDaily", lambda r: r["late_night_minutes"]), 28)
        self.assertLess(abs(b - a), 3)


class Truth(unittest.TestCase):
    def test_truth_shape(self):
        for k in profiles.PROFILES:
            t = profiles.scenario_truth(k)
            for key in ("planted_changes", "planted_lags", "planted_contexts", "expected_absent"):
                self.assertIn(key, t)
        self.assertEqual({c["metric"] for c in profiles.scenario_truth("doomscroll")["planted_changes"]} >= {"short_video_minutes", "steps"}, True)
        self.assertEqual(profiles.scenario_truth("steady")["planted_changes"], [])

    def test_unknown_profile(self):
        with self.assertRaises(ValueError):
            profiles.build("nope")


if __name__ == "__main__":
    unittest.main()
