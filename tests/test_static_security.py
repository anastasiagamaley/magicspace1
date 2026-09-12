"""
Exercises the real static-file routing from app.py without importing the
full module (that would open a live DB connection and start an APScheduler
background scheduler). Instead this pulls only the Flask app construction
line and the static-routing functions out of app.py via `ast`, and executes
them in an isolated namespace pointed at a throwaway tempdir of dummy files.
"""
import ast
import os
import tempfile
import unittest
from pathlib import Path

from flask import Flask, send_from_directory, abort

APP_PY = Path(__file__).resolve().parent.parent / "app.py"

ASSIGN_NAMES = {"app", "PAGE_NAME_RE", "PUBLIC_ROOT_FILES"}
ROUTE_FUNCS = {
    "index", "static_page", "public_root_file",
    "uploaded_file", "jogamartin", "sitemap", "robots",
}


def _extract_routing_module():
    tree = ast.parse(APP_PY.read_text(encoding="utf-8"), filename=str(APP_PY))
    nodes = []
    found = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in ASSIGN_NAMES:
            nodes.append(node)
            found.add(node.targets[0].id)
        elif isinstance(node, ast.FunctionDef) and node.name in ROUTE_FUNCS:
            nodes.append(node)
            found.add(node.name)
    missing = (ASSIGN_NAMES | ROUTE_FUNCS) - found
    if missing:
        raise AssertionError(f"app.py routing shape changed, missing: {sorted(missing)}")
    module = ast.Module(body=nodes, type_ignores=[])
    ast.fix_missing_locations(module)
    return compile(module, filename=str(APP_PY), mode="exec")


class StaticSecurityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.TemporaryDirectory()
        base = Path(cls.tmpdir.name)
        uploads = base / "uploads"
        uploads.mkdir()

        (base / "index.html").write_text("dummy index", encoding="utf-8")
        (base / "landing.html").write_text("dummy landing", encoding="utf-8")
        (base / "kurz.html").write_text("dummy kurz", encoding="utf-8")
        (base / "magicspace_leadmagnet.html").write_text("dummy leadmagnet page", encoding="utf-8")
        (base / "joga-park.html").write_text("dummy joga park", encoding="utf-8")
        (base / "api.js").write_text("console.log('dummy');", encoding="utf-8")
        (base / "favicon.png").write_bytes(b"\x89PNGdummy")
        (base / "magicspace_leadmagnet.pdf").write_bytes(b"%PDF dummy lead magnet")
        (base / "byt_tam_paid_guide.pdf").write_bytes(b"%PDF dummy paid guide")
        (base / "sitemap.xml").write_text("<urlset></urlset>", encoding="utf-8")
        (base / "robots.txt").write_text("User-agent: *", encoding="utf-8")
        (uploads / "photo.png").write_bytes(b"dummy image bytes")

        # dummy secrets/private files that must NEVER become servable
        (base / ".env").write_text("ADMIN_PASSWORD=dummy-secret\n", encoding="utf-8")
        (base / "app.py").write_text("# dummy source stand-in, not the real file", encoding="utf-8")
        (base / "magicspace.db").write_bytes(b"SQLite format 3 dummy")
        (base / "secret_notes.txt").write_text("dummy private note", encoding="utf-8")

        code = _extract_routing_module()
        namespace = {
            "Flask": Flask,
            "send_from_directory": send_from_directory,
            "abort": abort,
            "os": os,
            "_re": __import__("re"),
            "__name__": "app_under_test",
            "BASE": str(base),
            "UPLOADS": str(uploads),
        }
        exec(code, namespace)
        cls.app = namespace["app"]
        cls.app.testing = True
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def _get(self, path):
        resp = self.client.get(path)
        resp.close()
        return resp

    def test_no_root_catchall_static_route(self):
        self.assertIsNone(self.app.static_folder)

    def test_secrets_and_source_are_not_servable(self):
        for path in ("/.env", "/app.py", "/magicspace.db", "/secret_notes.txt"):
            with self.subTest(path=path):
                self.assertEqual(self._get(path).status_code, 404)

    def test_explicit_public_assets_servable(self):
        self.assertEqual(self._get("/api.js").status_code, 200)
        self.assertEqual(self._get("/favicon.png").status_code, 200)

    def test_explicit_public_pdfs_servable(self):
        self.assertEqual(self._get("/magicspace_leadmagnet.pdf").status_code, 200)
        self.assertEqual(self._get("/byt_tam_paid_guide.pdf").status_code, 200)

    def test_root_and_server_only_html_pages_preserved(self):
        for path in ("/", "/landing.html", "/kurz.html",
                     "/magicspace_leadmagnet.html", "/joga-park.html"):
            with self.subTest(path=path):
                self.assertEqual(self._get(path).status_code, 200)

    def test_unknown_html_page_404s(self):
        self.assertEqual(self._get("/does-not-exist.html").status_code, 404)

    def test_page_name_validation_rejects_odd_characters(self):
        for path in ("/..html", "/foo bar.html", "/foo;bar.html", "/foo%00.html"):
            with self.subTest(path=path):
                self.assertEqual(self._get(path).status_code, 404)

    def test_uploads_still_served(self):
        self.assertEqual(self._get("/uploads/photo.png").status_code, 200)

    def test_sitemap_robots_jogamartin_preserved(self):
        self.assertEqual(self._get("/sitemap.xml").status_code, 200)
        self.assertEqual(self._get("/robots.txt").status_code, 200)
        self.assertEqual(self._get("/jogamartin").status_code, 200)


if __name__ == "__main__":
    unittest.main()
