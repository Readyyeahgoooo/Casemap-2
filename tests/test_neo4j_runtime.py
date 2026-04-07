from __future__ import annotations

from io import BytesIO
import json
import os
import unittest
from unittest import mock

import app as casemap_app


class _FakeNeo4jStore:
    def manifest(self) -> dict:
        return {
            "title": "Neo4j Test Graph",
            "viewer_heading_public": "Neo4j Test Graph",
            "legal_domain": "criminal",
            "node_count": 2,
            "edge_count": 1,
            "case_count": 1,
            "statute_count": 0,
            "data_source": "neo4j",
        }

    def project_bundle(self) -> dict:
        return {
            "meta": self.manifest(),
            "nodes": [
                {"id": "module:test", "type": "Module", "label": "Neo4j Module", "summary": "Module summary"},
                {"id": "case:test", "type": "Case", "label": "Neo4j Case", "summary": "Case summary"},
            ],
            "edges": [{"source": "module:test", "target": "case:test", "type": "CONTAINS"}],
            "case_cards": {},
            "tree": {"id": "neo4j_runtime", "label_en": "Neo4j Runtime", "modules": []},
        }

    def focus_graph(self, node_id: str, depth: int = 1) -> dict:
        return {
            "focus": node_id,
            "nodes": [{"id": node_id, "type": "Case", "label": "Focused Neo4j Case", "summary": ""}],
            "edges": [],
            "facets": {"Case": 1},
            "data_source": "neo4j",
        }


def _call_app(path: str, *, query: str = "") -> tuple[str, dict[str, str], str]:
    captured: dict[str, object] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        captured["status"] = status
        captured["headers"] = dict(headers)

    environ = {
        "PATH_INFO": path,
        "REQUEST_METHOD": "GET",
        "QUERY_STRING": query,
        "CONTENT_LENGTH": "0",
        "wsgi.input": BytesIO(b""),
    }
    body = b"".join(casemap_app.app(environ, start_response)).decode("utf-8")
    return captured["status"], captured["headers"], body


def _reset_app_cache() -> None:
    casemap_app._hybrid_store = None
    casemap_app._hybrid_store_path = None
    casemap_app._neo4j_store = None
    casemap_app._neo4j_checked = False


class Neo4jRuntimeTests(unittest.TestCase):
    def tearDown(self) -> None:
        _reset_app_cache()

    def test_graph_route_prefers_neo4j_projection(self) -> None:
        with mock.patch.dict(os.environ, {"CASEMAP_PROFILE": "criminal"}, clear=False):
            casemap_app._neo4j_store = _FakeNeo4jStore()
            casemap_app._neo4j_checked = True
            status, headers, body = _call_app("/graph")
        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertIn("Neo4j Test Graph", body)
        self.assertIn("Neo4j Module", body)

    def test_api_manifest_prefers_neo4j(self) -> None:
        with mock.patch.dict(os.environ, {"CASEMAP_PROFILE": "criminal"}, clear=False):
            casemap_app._neo4j_store = _FakeNeo4jStore()
            casemap_app._neo4j_checked = True
            status, headers, body = _call_app("/api/manifest")
        payload = json.loads(body)
        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
        self.assertEqual(payload["data_source"], "neo4j")
        self.assertEqual(payload["title"], "Neo4j Test Graph")

    def test_api_focus_prefers_neo4j(self) -> None:
        with mock.patch.dict(os.environ, {"CASEMAP_PROFILE": "criminal"}, clear=False):
            casemap_app._neo4j_store = _FakeNeo4jStore()
            casemap_app._neo4j_checked = True
            status, _, body = _call_app("/api/graph/focus", query="id=case:test&depth=1")
        payload = json.loads(body)
        self.assertEqual(status, "200 OK")
        self.assertEqual(payload["data_source"], "neo4j")
        self.assertEqual(payload["focus"], "case:test")


if __name__ == "__main__":
    unittest.main()
