from __future__ import annotations

from io import BytesIO
import os
import unittest
from unittest import mock

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


def _reset_app_cache() -> None:
    casemap_app._hybrid_store = None
    casemap_app._hybrid_store_path = None


class AppRouteTests(unittest.TestCase):
    def tearDown(self) -> None:
        _reset_app_cache()

    def test_root_renders_public_relationship_graph(self) -> None:
        status, headers, body = _call_app("/")
        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertIn("Hong Kong Contract Law", body)
        self.assertIn("Doctrinal Relationship Map", body)
        self.assertIn('id="graph"', body)
        self.assertIn('href="/tree"', body)

    def test_tree_renders_public_hybrid_hierarchy(self) -> None:
        status, headers, body = _call_app("/tree")
        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertIn("Hong Kong Contract Law Hierarchical Knowledge Graph", body)
        self.assertIn('id="hierarchyCanvas"', body)
        self.assertIn("Visual Hierarchy Graph", body)

    def test_internal_route_renders_internal_explorer(self) -> None:
        status, headers, body = _call_app("/internal")
        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertIn("Internal Explorer", body)
        self.assertIn("Hong Kong Contract Law Internal Hierarchy Explorer", body)
        self.assertIn('id="hierarchyCanvas"', body)
        self.assertIn("Visual Hierarchy Graph", body)
        self.assertIn('href="/internal" class="active"', body)
        self.assertIn('id="graphRagForm"', body)
        self.assertIn("GraphRAG Inquiry Panel", body)

    def test_criminal_root_prefers_node_graph(self) -> None:
        with mock.patch.dict(os.environ, {"CASEMAP_PROFILE": "criminal"}, clear=False):
            _reset_app_cache()
            status, headers, body = _call_app("/")
        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertIn("Hong Kong Criminal Law", body)
        self.assertIn("Doctrinal Relationship Map", body)
        self.assertNotIn("Hong Kong Contract Law", body)


if __name__ == "__main__":
    unittest.main()
