import copy
import http.client
import json
import threading
import unittest
from pathlib import Path

from explorer import server as srv
from spikes import explorer_export, synthetic_persona

REPO = Path(__file__).resolve().parent.parent


class ServerCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = srv.make_server("127.0.0.1", 0, quiet=True)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def request(self, method, path, host=None, body=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        headers = {"Host": host or f"127.0.0.1:{self.port}"}
        conn.request(method, path, body=body, headers=headers)
        resp = conn.getresponse()
        data = resp.read()
        conn.close()
        return resp, data


class ApiTests(ServerCase):
    def test_health(self):
        resp, data = self.request("GET", "/api/health")
        self.assertEqual(resp.status, 200)
        self.assertEqual(json.loads(data)["synthetic_only"], True)

    def test_workspace_list_is_synthetic_and_isolated(self):
        resp, data = self.request("GET", "/api/workspaces")
        listing = json.loads(data)["workspaces"]
        from spikes import profiles
        self.assertEqual({w["key"] for w in listing},
                         {"persona", "fixtures"} | {f"profile-{k}" for k in profiles.PROFILES})
        self.assertTrue(all(w["synthetic"] is True for w in listing))
        self.assertEqual(len({w["workspace_id"] for w in listing}), len(listing))

    def test_profile_workspace_carries_computed_findings(self):
        resp, data = self.request("GET", "/api/workspaces/profile-doomscroll")
        doc = json.loads(data)
        kinds = {r.get("finding_kind") for r in doc["records"] if r["type"] == "Finding"}
        self.assertIn("shift", kinds)
        self.assertIn("observer_inference", kinds)
        self.assertIn("insights", doc["meta"])
        resp, data = self.request("GET", "/api/workspaces/profile-sparse/metrics")
        metrics = json.loads(data)["metrics"]
        self.assertTrue(all(v == "unknown" for v in metrics["sleep_duration"].values()))
        sources = json.loads(data)["metric_sources"]
        self.assertNotIn("sleep_duration", sources)  # no producer: no derivation claimed
        self.assertEqual(sources["steps"], ["DailyHealthAggregate"])

    def test_workspace_document_matches_spike_builder_and_checked_in_file(self):
        resp, data = self.request("GET", "/api/workspaces/persona")
        self.assertEqual(resp.status, 200)
        doc = json.loads(data)
        self.assertEqual(doc, synthetic_persona.build())
        checked_in = json.loads((REPO / "prototypes/explorer-concept/data/persona.json").read_text())
        self.assertEqual(doc, checked_in)
        resp, data = self.request("GET", "/api/workspaces/fixtures")
        self.assertEqual(json.loads(data), explorer_export.build_fixture_document())

    def test_validation_endpoint(self):
        resp, data = self.request("GET", "/api/workspaces/fixtures/validation")
        self.assertEqual(json.loads(data), {"workspace": "fixtures", "valid": True, "problems": []})

    def test_unknown_workspace_and_endpoint(self):
        self.assertEqual(self.request("GET", "/api/workspaces/nope")[0].status, 404)
        self.assertEqual(self.request("GET", "/api/records")[0].status, 404)

    def test_no_store_and_security_headers(self):
        resp, _ = self.request("GET", "/api/workspaces/persona")
        self.assertEqual(resp.getheader("Cache-Control"), "no-store")
        self.assertEqual(resp.getheader("X-Content-Type-Options"), "nosniff")
        self.assertIn("connect-src 'self'", resp.getheader("Content-Security-Policy"))
        self.assertIsNone(resp.getheader("Access-Control-Allow-Origin"))


class BoundaryTests(ServerCase):
    def test_read_only(self):
        for method in ("POST", "PUT", "PATCH", "DELETE", "OPTIONS"):
            resp, _ = self.request(method, "/api/workspaces/persona", body=b"{}")
            self.assertEqual(resp.status, 405, method)
            self.assertEqual(resp.getheader("Allow"), "GET, HEAD")

    def test_non_loopback_host_header_rejected(self):
        for host in ("evil.example", "evil.example:8765", "192.168.1.5", "127.0.0.1.evil.example"):
            self.assertEqual(self.request("GET", "/api/health", host=host)[0].status, 421, host)
        self.assertEqual(self.request("GET", "/api/health", host=f"localhost:{self.port}")[0].status, 200)

    def test_static_serving_and_traversal(self):
        resp, data = self.request("GET", "/explorer-cinematic/")
        self.assertEqual(resp.status, 200)
        self.assertIn(b"/api/workspaces/", data)
        for path in ("/../AGENTS.md", "/%2e%2e/AGENTS.md", "/explorer-cinematic/../../AGENTS.md",
                     "/.git/config", "/explorer-concept/README.py", "/explorer-cinematic/data/"):
            self.assertEqual(self.request("GET", path)[0].status, 404, path)

    def test_root_redirects_to_app(self):
        resp, _ = self.request("GET", "/")
        self.assertEqual(resp.status, 302)
        self.assertEqual(resp.getheader("Location"), "/explorer-cinematic/")


class RegistryTests(unittest.TestCase):
    def test_refuses_non_loopback_bind(self):
        for host in ("0.0.0.0", "192.168.1.5", "example.com"):
            with self.assertRaises(ValueError):
                srv.make_server(host, 0, workspaces={})

    def test_refuses_non_synthetic_document(self):
        doc = synthetic_persona.build()
        doc["meta"]["synthetic"] = False
        with self.assertRaises(srv.WorkspaceRefused):
            srv.load_workspaces({"x": ("x", "test", lambda: doc)})

    def test_refuses_invalid_document(self):
        doc = synthetic_persona.build()
        doc["records"].append(copy.deepcopy(doc["records"][0]))  # duplicate id
        with self.assertRaises(srv.WorkspaceRefused):
            srv.load_workspaces({"x": ("x", "test", lambda: doc)})

    def test_refuses_shared_workspace_id(self):
        with self.assertRaises(srv.WorkspaceRefused):
            srv.load_workspaces({"a": ("a", "t", synthetic_persona.build),
                                 "b": ("b", "t", synthetic_persona.build)})

    def test_host_header_parsing(self):
        ok = ["127.0.0.1", "127.0.0.1:80", "localhost:8765", "[::1]:8765", "[::1]"]
        bad = [None, "", "evil.example", "localhost.evil.example", "[::2]:80", "0.0.0.0:8765"]
        for h in ok:
            self.assertTrue(srv.host_header_ok(h), h)
        for h in bad:
            self.assertFalse(srv.host_header_ok(h), h)


if __name__ == "__main__":
    unittest.main()
