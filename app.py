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

ARTIFACT_DIR = BASE_DIR / "artifacts" / "contract_big"
GRAPH_PATH = ARTIFACT_DIR / "graph.json"
CHUNK_PATH = ARTIFACT_DIR / "chunks.json"
MANIFEST_PATH = ARTIFACT_DIR / "manifest.json"
SAMPLE_QUERY_PATH = ARTIFACT_DIR / "sample_queries.json"
MAP_PATH = ARTIFACT_DIR / "knowledge_map.html"

_retriever: RerankedRetriever | None = None


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> dict | list:
    return json.loads(_load_text(path))


def _get_retriever() -> RerankedRetriever | None:
    global _retriever
    if _retriever is None and GRAPH_PATH.exists() and CHUNK_PATH.exists():
        _retriever = RerankedRetriever.from_files(GRAPH_PATH, CHUNK_PATH)
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
        "routes": ["/", "/health", "/api/manifest", "/api/sample-queries", "/api/query?q=offer+acceptance"],
    }
    return _json_response(start_response, payload, status="404 Not Found")


def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET").upper()

    if method != "GET":
        return _json_response(start_response, {"error": "Method not allowed"}, status="405 Method Not Allowed")

    if path in {"/", "/index.html"}:
        if not MAP_PATH.exists():
            return _html_response(
                start_response,
                "<h1>Casemap</h1><p>The knowledge map artifact is not available in this deployment.</p>",
                status="503 Service Unavailable",
            )
        return _html_response(start_response, _load_text(MAP_PATH))

    if path == "/health":
        return _json_response(
            start_response,
            {
                "ok": True,
                "artifacts_present": {
                    "graph": GRAPH_PATH.exists(),
                    "chunks": CHUNK_PATH.exists(),
                    "manifest": MANIFEST_PATH.exists(),
                    "map": MAP_PATH.exists(),
                },
            },
        )

    if path == "/api/manifest":
        if not MANIFEST_PATH.exists():
            return _json_response(start_response, {"error": "manifest.json not found"}, status="503 Service Unavailable")
        return _json_response(start_response, _load_json(MANIFEST_PATH))

    if path == "/api/sample-queries":
        if not SAMPLE_QUERY_PATH.exists():
            return _json_response(
                start_response,
                {"error": "sample_queries.json not found"},
                status="503 Service Unavailable",
            )
        return _json_response(start_response, _load_json(SAMPLE_QUERY_PATH))

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
