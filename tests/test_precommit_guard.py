"""Tests for tools.precommit_guard. Secrets are assembled at runtime and are fake."""
import io
import os
import shutil
import subprocess
import tempfile
import unittest

from tools import precommit_guard as pg

HAVE_GIT = shutil.which("git") is not None

FAKE_SK = "sk-" + "A1b2C3d4E5f6G7h8I9j0K1l2"
FAKE_KEY_BLOCK = "-----" + "BEGIN RSA PRIVATE KEY-----\nAAAA\n"


def rules(findings):
    return {r for _, _, r in findings}


class ScanFileTests(unittest.TestCase):
    def test_private_key_and_sk_token(self):
        f = pg.scan_file("notes.txt", (FAKE_KEY_BLOCK + "token " + FAKE_SK + "\n").encode())
        self.assertIn("PG001", rules(f))
        self.assertIn("PG003", rules(f))

    def test_assignment_entropy_and_placeholder(self):
        # Assembled at runtime so this test file does not trip its own guard.
        hi = pg.scan_file("a.py", b"API_" + b'TOKEN = "' + b"q8Zr3LmX9vB2" + b'nKp7TcW4yHd1"\n')
        self.assertIn("PG003", rules(hi))
        lo = pg.scan_file("a.py", b'API_TOKEN = "your-token-goes-here-please"\n')
        self.assertNotIn("PG003", rules(lo))

    def test_signing_and_env(self):
        self.assertIn("PG002", rules(pg.scan_file("x/dev.p12", b"\0\1")))
        self.assertIn("PG002", rules(pg.scan_file("dev.mobileprovision", b"x")))
        self.assertIn("PG004", rules(pg.scan_file(".env", b"A=1\n")))
        self.assertIn("PG004", rules(pg.scan_file("app/.env.local", b"A=1\n")))
        self.assertNotIn("PG004", rules(pg.scan_file(".env.example", b"A=\n")))

    def test_data_outside_allowlist(self):
        for p in ("data.csv", "docs/a.ndjson", "export.xml", "Takeout/x.txt", "a.zip", "r.gpx"):
            self.assertIn("PG005", rules(pg.scan_file(p, b"a,b\n")), p)

    def test_data_in_allowlist_ok_and_size(self):
        ok = b'{"id":"com.example.app","u":"https://a.example.com/x"}\n'
        self.assertEqual(pg.scan_file("spikes/fixtures/a/b.json", ok), [])
        big = b"x" * (pg.MAX_DATA_BYTES + 1)
        self.assertIn("PG008", rules(pg.scan_file("tests/big.csv", big)))
        self.assertIn("PG005", rules(pg.scan_file("spikes/fixtures/a.zip", b"PK\0")))

    def test_markers_and_real_identifiers(self):
        f = pg.scan_file("tests/d.json", b'{"mail":"jane.doe@gmail.com"}\n')
        self.assertIn("PG006", rules(f))
        self.assertIn("PG007", rules(f))
        f = pg.scan_file("tests/d.json", b'{"s":"synthetic","u":"https://news.bbc.co.uk/x"}\n')
        self.assertEqual(rules(f), {"PG007"})
        f = pg.scan_file("tests/d.json", b'{"s":"synthetic","b":"com.apple.mobilesafari"}\n')
        self.assertEqual(rules(f), {"PG007"})
        f = pg.scan_file("tests/d.json", b'{"m":"a@example.com","b":"com.example.x"}\n')
        self.assertEqual(f, [])

    def test_private_dirs(self):
        self.assertIn("PG009", rules(pg.scan_file("exports/readme.txt", b"hi")))
        self.assertIn("PG009", rules(pg.scan_file("a/private-data/x.txt", b"hi")))

    def test_output_never_contains_value(self):
        f = pg.scan_file("n.txt", ("k = " + FAKE_SK).encode())
        self.assertNotIn(FAKE_SK, repr(f))

    def test_allowlist_parsing(self):
        entries, bad = pg.load_allowlist("# c\n\nfoo/*.csv  # reviewed\nbar.csv\n*  \n**  # all\n")
        self.assertEqual(entries["foo/*.csv"], "reviewed")
        self.assertEqual(len(bad), 3)
        self.assertEqual({n for _, n, _ in bad}, {4, 5, 6})

    def test_glob(self):
        self.assertTrue(pg.glob_to_re("prototypes/**/data/**").match("prototypes/a/b/data/x.json"))
        self.assertTrue(pg.glob_to_re("tests/**").match("tests/a.json"))
        self.assertFalse(pg.glob_to_re("tests/**").match("src/tests/a.json"))


@unittest.skipUnless(HAVE_GIT, "git unavailable")
class GitIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
        self.env = env
        subprocess.run(["git", "init", "-q"], cwd=self.tmp, check=True, env=env)

    def put(self, rel, data, stage=True):
        path = os.path.join(self.tmp, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(data)
        if stage:
            subprocess.run(["git", "add", "-f", rel], cwd=self.tmp, check=True, env=self.env)

    def run_guard(self, mode="staged"):
        err = io.StringIO()
        return pg.run(mode, self.tmp, stream=err), err.getvalue()

    def test_clean_repo_passes(self):
        self.put("README.md", b"hello\n")
        self.put("spikes/fixtures/a.ndjson", b'{"b":"com.example.app"}\n')
        self.assertEqual(self.run_guard()[0], [])

    def test_staged_findings(self):
        self.put("real.csv", b"a,b\n")
        self.put("cfg.txt", ("k=" + FAKE_SK + "\n").encode())
        found, _ = self.run_guard()
        self.assertEqual(rules(found), {"PG005", "PG003"})

    def test_staged_content_not_worktree(self):
        self.put("n.txt", ("k=" + FAKE_SK + "\n").encode())
        self.put("n.txt", b"clean\n", stage=False)  # worktree clean, index dirty
        self.assertIn("PG003", rules(self.run_guard()[0]))

    def test_all_mode_and_main_exit_codes(self):
        self.put("x/.env", b"A=1\n")
        self.assertIn("PG004", rules(self.run_guard("all")[0]))
        self.assertEqual(pg.main(["--all", "--repo", self.tmp]), 1)

    def test_clean_main_exit_zero(self):
        self.put("a.txt", b"fine\n")
        self.assertEqual(pg.main(["--staged", "--repo", self.tmp]), 0)

    def test_allowlist_override_is_logged(self):
        self.put("tools/precommit-allowlist.txt", b"special/data.csv  # reviewed synthetic\n")
        self.put("special/data.csv", b"a,b\n")
        found, log = self.run_guard()
        self.assertEqual(found, [])
        self.assertIn("OVERRIDE special/data.csv", log)
        self.assertIn("reviewed synthetic", log)

    def test_allowlist_without_reason_fails(self):
        self.put("tools/precommit-allowlist.txt", b"special/data.csv\n")
        self.put("special/data.csv", b"a,b\n")
        found, _ = self.run_guard()
        self.assertIn("PG010", rules(found))
        self.assertIn("PG005", rules(found))


if __name__ == "__main__":
    unittest.main()
