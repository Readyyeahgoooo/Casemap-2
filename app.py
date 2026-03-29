from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import parse_qs

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from casemap.graphrag import RerankedRetriever

MVP_ARTIFACT_DIR = BASE_DIR / "artifacts" / "contract_big"
MVP_GRAPH_PATH = MVP_ARTIFACT_DIR / "graph.json"
MVP_CHUNK_PATH = MVP_ARTIFACT_DIR / "chunks.json"
MVP_MANIFEST_PATH = MVP_ARTIFACT_DIR / "manifest.json"
MVP_SAMPLE_QUERY_PATH = MVP_ARTIFACT_DIR / "sample_queries.json"
MVP_MAP_PATH = MVP_ARTIFACT_DIR / "knowledge_map.html"

PUBLIC_RELATIONSHIP_DIR = BASE_DIR / "artifacts" / "public_relationship_graph"
PUBLIC_RELATIONSHIP_GRAPH_PATH = PUBLIC_RELATIONSHIP_DIR / "relationship_graph.json"
PUBLIC_RELATIONSHIP_MANIFEST_PATH = PUBLIC_RELATIONSHIP_DIR / "manifest.json"
PUBLIC_RELATIONSHIP_MAP_PATH = PUBLIC_RELATIONSHIP_DIR / "relationship_map.html"
PUBLIC_RELATIONSHIP_TREE_PATH = PUBLIC_RELATIONSHIP_DIR / "relationship_tree.html"

_retriever: RerankedRetriever | None = None


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> dict | list:
    return json.loads(_load_text(path))


def _get_retriever() -> RerankedRetriever | None:
    global _retriever
    if _retriever is None and MVP_GRAPH_PATH.exists() and MVP_CHUNK_PATH.exists():
        _retriever = RerankedRetriever.from_files(MVP_GRAPH_PATH, MVP_CHUNK_PATH)
    return _retriever


def _respond(start_response, status: str, body: bytes, content_type: str) -> list[bytes]:
    headers = [
        ("Content-Type", content_type),
        ("Content-Length", str(len(body))),
        ("Cache-Control", "public, max-age=60"),
    ]
    start_response(status, headers)
    return [body]


def _json_response(start_response, payload: dict | list, status: str = "200 OK") -> list[bytes]:
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    return _respond(start_response, status, body, "application/json; charset=utf-8")


def _html_response(start_response, html: str, status: str = "200 OK") -> list[bytes]:
    return _respond(start_response, status, html.encode("utf-8"), "text/html; charset=utf-8")


def _not_found(start_response) -> list[bytes]:
    payload = {
        "error": "Not found",
        "routes": [
            "/",
            "/tree",
            "/mvp",
            "/relationships",
            "/health",
            "/api/manifest",
            "/api/relationship-manifest",
            "/api/sample-queries",
            "/api/query?q=offer+acceptance",
        ],
    }
    return _json_response(start_response, payload, status="404 Not Found")


def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET").upper()

    if method != "GET":
        return _json_response(start_response, {"error": "Method not allowed"}, status="405 Method Not Allowed")

    if path in {"/", "/index.html", "/tree"}:
        if PUBLIC_RELATIONSHIP_TREE_PATH.exists():
            return _html_response(start_response, _load_text(PUBLIC_RELATIONSHIP_TREE_PATH))
        if PUBLIC_RELATIONSHIP_MAP_PATH.exists():
            return _html_response(start_response, _load_text(PUBLIC_RELATIONSHIP_MAP_PATH))
        if MVP_MAP_PATH.exists():
            return _html_response(start_response, _load_text(MVP_MAP_PATH))
        return _html_response(
            start_response,
            "<h1>Casemap</h1><p>No public artifact is available in this deployment.</p>",
            status="503 Service Unavailable",
        )

    if path == "/relationships":
        if PUBLIC_RELATIONSHIP_MAP_PATH.exists():
            return _html_response(start_response, _load_text(PUBLIC_RELATIONSHIP_MAP_PATH))
        if MVP_MAP_PATH.exists():
            return _html_response(start_response, _load_text(MVP_MAP_PATH))
        return _html_response(
            start_response,
            "<h1>Casemap</h1><p>No public artifact is available in this deployment.</p>",
            status="503 Service Unavailable",
        )

    if path == "/mvp":
        if not MVP_MAP_PATH.exists():
            return _html_response(
                start_response,
                "<h1>Casemap</h1><p>The MVP knowledge map artifact is not available in this deployment.</p>",
                status="503 Service Unavailable",
            )
        return _html_response(start_response, _load_text(MVP_MAP_PATH))

    if path == "/health":
        return _json_response(
            start_response,
            {
                "ok": True,
                "artifacts_present": {
                    "mvp_graph": MVP_GRAPH_PATH.exists(),
                    "mvp_chunks": MVP_CHUNK_PATH.exists(),
                    "mvp_manifest": MVP_MANIFEST_PATH.exists(),
                    "mvp_map": MVP_MAP_PATH.exists(),
                    "public_relationship_graph": PUBLIC_RELATIONSHIP_GRAPH_PATH.exists(),
                    "public_relationship_manifest": PUBLIC_RELATIONSHIP_MANIFEST_PATH.exists(),
                    "public_relationship_map": PUBLIC_RELATIONSHIP_MAP_PATH.exists(),
                    "public_relationship_tree": PUBLIC_RELATIONSHIP_TREE_PATH.exists(),
                },
            },
        )

    if path == "/api/manifest":
        if not MVP_MANIFEST_PATH.exists():
            return _json_response(start_response, {"error": "manifest.json not found"}, status="503 Service Unavailable")
        return _json_response(start_response, _load_json(MVP_MANIFEST_PATH))

    if path == "/api/relationship-manifest":
        if not PUBLIC_RELATIONSHIP_MANIFEST_PATH.exists():
            return _json_response(
                start_response,
                {"error": "public relationship manifest not found"},
                status="503 Service Unavailable",
            )
        return _json_response(start_response, _load_json(PUBLIC_RELATIONSHIP_MANIFEST_PATH))

    if path == "/api/sample-queries":
        if not MVP_SAMPLE_QUERY_PATH.exists():
            return _json_response(
                start_response,
                {"error": "sample_queries.json not found"},
                status="503 Service Unavailable",
            )
        return _json_response(start_response, _load_json(MVP_SAMPLE_QUERY_PATH))

    if path == "/api/query":
        retriever = _get_retriever()
        if retriever is None:
            return _json_response(
                start_response,
                {"error": "graph artifacts are not available for querying"},
                status="503 Service Unavailable",
            )

        params = parse_qs(environ.get("QUERY_STRING", ""))
        question = params.get("q", [""])[0].strip()
        top_k_raw = params.get("top_k", ["5"])[0]
        try:
            top_k = max(1, min(int(top_k_raw), 10))
        except ValueError:
            top_k = 5

        if not question:
            return _json_response(
                start_response,
                {"error": "Missing query string parameter 'q'"},
                status="400 Bad Request",
            )

        return _json_response(
            start_response,
            {
                "question": question,
                "top_k": top_k,
                "results": retriever.search(question, top_k=top_k),
            },
        )

    return _not_found(start_response)
