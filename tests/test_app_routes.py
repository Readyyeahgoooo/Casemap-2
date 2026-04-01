from __future__ import annotations

from io import BytesIO
import unittest

import app as casemap_app


def _call_app(path: str) -> tuple[str, dict[str, str], str]:
    captured: dict[str, object] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        captured["status"] = status
        captured["headers"] = dict(headers)

    environ = {
        "PATH_INFO": path,
        "REQUEST_METHOD": "GET",
        "QUERY_STRING": "",
        "CONTENT_LENGTH": "0",
        "wsgi.input": BytesIO(b""),
    }
    body = b"".join(casemap_app.app(environ, start_response)).decode("utf-8")
    return captured["status"], captured["headers"], body


class AppRouteTests(unittest.TestCase):
    def test_root_renders_public_hybrid_hierarchy(self) -> None:
        status, headers, body = _call_app("/")
        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertIn("Hong Kong Contract Law Hierarchical Knowledge Graph", body)
        self.assertIn('id="hierarchyCanvas"', body)
        self.assertIn("Visual Hierarchy Graph", body)
        self.assertIn("/internal", body)
        self.assertNotIn("This explorer fetches tree, topic, case, and focus-graph data", body)

    def test_internal_route_renders_internal_explorer(self) -> None:
        status, headers, body = _call_app("/internal")
        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertIn("Internal Explorer", body)
        self.assertIn("Hong Kong Contract Law Internal Hierarchy Explorer", body)
        self.assertIn('id="hierarchyCanvas"', body)
        self.assertIn("Visual Hierarchy Graph", body)
        self.assertIn('href="/internal" class="active"', body)


if __name__ == "__main__":
    unittest.main()
