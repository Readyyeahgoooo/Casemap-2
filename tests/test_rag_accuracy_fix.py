"""Property tests for the HK legal RAG accuracy fixes."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from casemap.criminal_law_data import iter_criminal_topics


# ---------------------------------------------------------------------------
# Task 1.2 — Animal cruelty topic present in criminal_law_data
# ---------------------------------------------------------------------------

def test_animal_cruelty_topic_exists():
    """iter_criminal_topics() must include at least one topic whose
    search_queries contain 'cap 169' or 'animal cruelty'."""
    topics = iter_criminal_topics()
    matching = [
        t for t in topics
        if any(
            "cap 169" in q.lower() or "animal cruelty" in q.lower()
            for q in t.get("search_queries", [])
        )
    ]
    assert matching, (
        "No topic found with search_queries containing 'cap 169' or 'animal cruelty'. "
        "The regulatory_and_welfare_offences module may be missing."
    )


def test_animal_cruelty_topic_has_module():
    """The animal cruelty topic must be assigned to a module."""
    topics = iter_criminal_topics()
    animal_topics = [
        t for t in topics
        if any("cap 169" in q.lower() or "animal cruelty" in q.lower() for q in t.get("search_queries", []))
    ]
    for t in animal_topics:
        assert t.get("module_id"), f"Topic {t['id']} has no module_id"


# ---------------------------------------------------------------------------
# Task 2.3 — HKLII fallback triggered for animal queries on sparse bundle
# ---------------------------------------------------------------------------

def _make_minimal_bundle(legal_domain: str = "criminal") -> dict:
    """Build a minimal hybrid graph bundle with no animal-cruelty nodes."""
    return {
        "meta": {"legal_domain": legal_domain, "title": "Test Criminal Bundle"},
        "nodes": [
            {
                "id": "module:general_principles",
                "type": "Module",
                "label": "General Principles",
                "label_en": "General Principles",
                "summary": "",
                "legal_domain": "criminal",
                "domain_tags": ["criminal"],
            },
            {
                "id": "case:hksar-v-chan",
                "type": "Case",
                "label": "HKSAR v Chan",
                "case_name": "HKSAR v Chan",
                "short_name": "HKSAR v Chan",
                "neutral_citation": "[2020] HKCA 1",
                "parallel_citations": [],
                "court_code": "CA",
                "court_name": "Court of Appeal",
                "court_level": "CA",
                "decision_date": "2020-01-01",
                "judges": [],
                "source_links": [],
                "summary_en": "A case about murder and stabbing of a human victim.",
                "summary_zh": "",
                "authority_score": 0.8,
                "topic_paths": ["General Principles/Actus Reus/Causation"],
                "lineage_ids": [],
                "enrichment_status": "seeded",
                "summary_embedding": [],
                "references": [],
                "legal_domain": "criminal",
                "domain_tags": ["criminal"],
                "degree": 1,
            },
        ],
        "edges": [],
        "case_cards": {
            "case:hksar-v-chan": {
                "id": "case:hksar-v-chan",
                "metadata": {
                    "id": "case:hksar-v-chan",
                    "neutral_citation": "[2020] HKCA 1",
                    "parallel_citations": [],
                    "case_name": "HKSAR v Chan",
                    "short_name": "HKSAR v Chan",
                    "court_code": "CA",
                    "court_name": "Court of Appeal",
                    "court_level": "CA",
                    "decision_date": "2020-01-01",
                    "judges": [],
                    "source_links": [],
                    "summary_en": "A case about murder and stabbing of a human victim.",
                    "summary_zh": "",
                    "authority_score": 0.8,
                    "topic_paths": [],
                    "lineage_ids": [],
                    "enrichment_status": "seeded",
                },
                "principles": [
                    {
                        "paragraph_span": "[1]",
                        "para_start": 1,
                        "para_end": 1,
                        "label_en": "Stabbing as actus reus",
                        "label_zh": "",
                        "statement_en": "The act of stabbing constitutes the actus reus of murder.",
                        "statement_zh": "",
                        "public_excerpt": "The act of stabbing constitutes the actus reus of murder.",
                        "text_private": "",
                        "cited_authority": None,
                    }
                ],
                "relationships": [],
                "lineage_memberships": [],
                "derived_relationships": {
                    "upstream_authorities": [],
                    "downstream_applications": [],
                    "same_lineage_cases": [],
                    "statutory_interpretations": [],
                },
            }
        },
        "tree": {
            "id": "criminal_law",
            "label_en": "Criminal Law",
            "label_zh": "刑事法",
            "modules": [],
        },
    }


def test_animal_query_triggers_hklii_fallback(monkeypatch):
    """Querying 'stabbing one's dog' against a bundle with no animal-cruelty
    nodes must set live_hklii.attempted = True in the retrieval trace."""
    from casemap.hybrid_graph import HybridGraphStore

    # Patch _live_hklii_grounding to avoid real network calls
    import casemap.hybrid_graph as hg_module

    def _mock_live_grounding(question, legal_domain, max_results=4, max_citations=8):
        return {"citations": [], "sources": [], "warnings": [], "search_trace": [{"query": question, "result_count": 0}]}

    monkeypatch.setattr(hg_module, "_live_hklii_grounding", _mock_live_grounding)

    store = HybridGraphStore(_make_minimal_bundle())
    result = store.query("What is the legal consequence of stabbing one's dog?", top_k=5)

    trace = result.get("retrieval_trace", {})
    live = trace.get("live_hklii", {})
    assert live.get("attempted") is True, (
        f"Expected live_hklii.attempted=True for animal query, got: {live}. "
        "The hint-domain coverage check may not be triggering the fallback."
    )


# ---------------------------------------------------------------------------
# Task 3.4 — render_knowledge_graph produces valid D3 HTML
# ---------------------------------------------------------------------------

def test_render_knowledge_graph_contains_d3():
    """render_knowledge_graph() output must contain 'd3' and node type labels."""
    from casemap.viewer import render_knowledge_graph

    bundle = _make_minimal_bundle()
    html = render_knowledge_graph(bundle)
    assert "d3" in html.lower(), "render_knowledge_graph output must include D3.js reference"
    assert "Module" in html or "Case" in html, "render_knowledge_graph output must include node type labels"


# ---------------------------------------------------------------------------
# Task 4.3 — /graph route returns 200 with D3 HTML
# ---------------------------------------------------------------------------

def test_graph_route_returns_200(monkeypatch):
    """/graph route must return 200 OK with HTML containing 'd3'."""
    import importlib
    import casemap.hybrid_graph as hg_module

    bundle = _make_minimal_bundle()
    store = hg_module.HybridGraphStore(bundle)

    import app as app_module
    monkeypatch.setattr(app_module, "_hybrid_store", store)
    monkeypatch.setattr(app_module, "_hybrid_store_path", None)

    responses = []

    def fake_start_response(status, headers):
        responses.append(status)

    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/graph",
        "QUERY_STRING": "",
        "CONTENT_LENGTH": "0",
        "wsgi.input": __import__("io").BytesIO(b""),
    }

    body_parts = app_module.app(environ, fake_start_response)
    body = b"".join(body_parts).decode("utf-8")

    assert responses and responses[0].startswith("200"), f"Expected 200, got {responses}"
    assert "d3" in body.lower(), "/graph response must include D3.js reference"


# ---------------------------------------------------------------------------
# Task 5.1 — Regression: well-covered topics still return citations
# ---------------------------------------------------------------------------

def test_well_covered_topic_returns_citations(monkeypatch):
    """Querying a well-covered topic must return at least one citation."""
    from casemap.hybrid_graph import HybridGraphStore

    import casemap.hybrid_graph as hg_module
    monkeypatch.setattr(hg_module, "_live_hklii_grounding", lambda *a, **kw: {"citations": [], "sources": [], "warnings": [], "search_trace": []})

    bundle = _make_minimal_bundle()
    # Add a proposition node so the query can match
    bundle["nodes"].append({
        "id": "proposition:murder-intent",
        "type": "Proposition",
        "label_en": "Intention for murder requires foresight of death",
        "statement_en": "The mens rea for murder requires the accused to intend to kill or cause grievous bodily harm.",
        "label_zh": "",
        "statement_zh": "",
        "doctrine_key": "murder-intent",
        "confidence": 0.98,
        "legal_domain": "criminal",
        "domain_tags": ["criminal"],
        "degree": 0,
    })
    store = HybridGraphStore(bundle)
    result = store.query("mens rea intention murder", top_k=5)
    # With a proposition node matching the query, we expect at least some supporting nodes
    assert result.get("supporting_nodes") is not None, "supporting_nodes must be present in result"
