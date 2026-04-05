from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest import mock

from casemap.hklii_crawler import HKLIICaseDocument, HKLIIParagraph, HKLIISearchResult
from casemap.hybrid_graph import HybridGraphStore, build_hierarchical_graph_bundle, export_public_projection


class _FallbackCrawler:
    def __init__(self, *args, **kwargs) -> None:
        self.warnings = []

    def simple_search(self, query: str, limit: int = 10) -> list[HKLIISearchResult]:
        return [
            HKLIISearchResult(
                title="HKSAR v Animal Care Example",
                subtitle="[2021] HKMC 12",
                path="/en/cases/hkmc/2021/12",
                db="Magistrates' Courts",
                pub_date="2021-01-10",
            )
        ]

    def crawl_paths(self, public_paths: list[str]) -> list[HKLIICaseDocument]:
        return [
            HKLIICaseDocument(
                case_name="HKSAR v Animal Care Example",
                court_name="Magistrates' Courts",
                neutral_citation="[2021] HKMC 12",
                decision_date="2021-01-10",
                court_code="HKMC",
                public_url="https://www.hklii.hk/en/cases/hkmc/2021/12",
                raw_html="",
                paragraphs=[
                    HKLIIParagraph(
                        "para 4",
                        "The prosecution concerned animal cruelty after a dog was deprived of necessary care, and the court discussed criminal liability under Hong Kong law.",
                    )
                ],
                judges=[],
                cited_cases=[],
                cited_statutes=[],
                title="HKSAR v Animal Care Example",
            )
        ]


class HybridGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        payload_path = Path("artifacts/public_relationship_graph/relationship_graph.json")
        cls.payload = json.loads(payload_path.read_text(encoding="utf-8"))
        cls.bundle = build_hierarchical_graph_bundle(cls.payload, title="Hybrid Graph Test")
        cls.store = HybridGraphStore(cls.bundle)
        criminal_payload_path = Path("artifacts/hk_criminal_relationship/relationship_graph.json")
        cls.criminal_payload = json.loads(criminal_payload_path.read_text(encoding="utf-8"))
        cls.criminal_bundle = build_hierarchical_graph_bundle(cls.criminal_payload, title="Hybrid Criminal Graph Test")

    def test_taxonomy_import_preserves_modules(self) -> None:
        expected_module_ids = {
            module["id"]
            for module in self.payload["meta"]["authority_tree"]["modules"]
        }
        actual_module_ids = {
            module["id"]
            for module in self.bundle["tree"]["modules"]
        }
        self.assertTrue(expected_module_ids.issubset(actual_module_ids))

    def test_curated_lineages_become_nodes_with_members(self) -> None:
        expected_count = len(self.payload["meta"]["lineages"])
        actual_count = sum(1 for node in self.bundle["nodes"] if node["type"] == "AuthorityLineage")
        self.assertEqual(expected_count, actual_count)

        lineage_node = next(node for node in self.bundle["nodes"] if node["id"] == "lineage:penalty_clauses_modern_test")
        self.assertEqual(lineage_node["type"], "AuthorityLineage")
        member_edges = [
            edge for edge in self.bundle["edges"]
            if edge["source"] == lineage_node["id"] and edge["type"] == "HAS_MEMBER"
        ]
        self.assertGreaterEqual(len(member_edges), 4)
        self.assertIn("FLLW", {edge.get("code", "") for edge in member_edges})

    def test_sample_case_card_matches_requested_shape(self) -> None:
        sample_card = next(
            card
            for card in self.bundle["case_cards"].values()
            if card["metadata"]["neutral_citation"] == "[1999] HKCFI 1007"
        )
        self.assertEqual(sample_card["metadata"]["case_name"], "Chiu Man On Paul t/a Pacific Power Engineering Co. v Vaford Contracting Co. Ltd.")
        self.assertEqual(len(sample_card["principles"]), 3)
        self.assertGreaterEqual(len(sample_card["relationships"]), 2)
        self.assertEqual(
            sorted(sample_card["derived_relationships"].keys()),
            ["downstream_applications", "same_lineage_cases", "statutory_interpretations", "upstream_authorities"],
        )
        first_principle = sample_card["principles"][0]
        self.assertIn("paragraph_span", first_principle)
        self.assertIn("statement_en", first_principle)
        self.assertIn("statement_zh", first_principle)

    def test_topic_focus_graph_is_bounded(self) -> None:
        implied_terms_topic = next(
            node["id"]
            for node in self.bundle["nodes"]
            if node["type"] == "Topic" and node["label"] == "Implied Terms"
        )
        focus = self.store.focus_graph(implied_terms_topic, depth=1)
        self.assertLess(len(focus["nodes"]), 60)
        self.assertLess(len(focus["edges"]), 120)
        self.assertIn("Topic", focus["facets"])

    def test_query_returns_sources_and_supporting_nodes(self) -> None:
        result = self.store.query("When can terms be implied into a contract in Hong Kong?", top_k=3)
        self.assertTrue(result["answer"])
        self.assertEqual(result["answer_mode"], "extractive")
        self.assertGreaterEqual(len(result["sources"]), 1)
        self.assertGreaterEqual(len(result["citations"]), 1)
        self.assertTrue(result["citations"][0]["citation_id"].startswith("C"))
        self.assertGreaterEqual(len(result["supporting_nodes"]), 1)
        self.assertIn("retrieval_trace", result)

    def test_query_openrouter_mode_falls_back_when_api_key_missing(self) -> None:
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=False):
            result = self.store.query("What is the modern penalty clauses approach in Hong Kong?", top_k=3, mode="openrouter")
        self.assertTrue(result["answer"])
        self.assertEqual(result["answer_mode"], "extractive")
        self.assertTrue(result["llm"]["requested"])
        self.assertFalse(result["llm"]["used"])
        self.assertGreaterEqual(len(result["warnings"]), 1)

    def test_criminal_bundle_excludes_contract_curated_enrichments(self) -> None:
        case_names = {
            node.get("case_name", node.get("label", ""))
            for node in self.criminal_bundle["nodes"]
            if node["type"] == "Case"
        }
        self.assertNotIn("Chiu Man On Paul t/a Pacific Power Engineering Co. v Vaford Contracting Co. Ltd.", case_names)
        self.assertNotIn("To Yung Sing Herman v Szeto Chak Mei and Others", case_names)
        self.assertEqual(self.criminal_bundle["meta"]["legal_domain"], "criminal")

    @mock.patch("casemap.hybrid_graph.HKLIICrawler", _FallbackCrawler)
    def test_criminal_query_uses_live_hklii_when_local_grounding_is_weak(self) -> None:
        store = HybridGraphStore(
            {
                "meta": {"title": "Hong Kong Criminal Law Hierarchical Graph", "legal_domain": "criminal"},
                "tree": {},
                "nodes": [],
                "edges": [],
                "case_cards": {},
            }
        )
        result = store.query("What is my legal liability if I eat my own dog?", top_k=3, mode="extractive")
        self.assertTrue(result["retrieval_trace"]["live_hklii"]["attempted"])
        self.assertTrue(result["retrieval_trace"]["live_hklii"]["used"])
        self.assertGreaterEqual(len(result["citations"]), 1)
        self.assertEqual(result["sources"][0]["retrieval_origin"], "hklii_live")
        self.assertIn("animal cruelty", result["answer"].lower())

    def test_public_projection_strips_private_fields(self) -> None:
        public_projection = export_public_projection(self.bundle)
        paragraph_nodes = [node for node in public_projection["nodes"] if node["type"] == "Paragraph"]
        if paragraph_nodes:
            self.assertNotIn("text_private", paragraph_nodes[0])
            self.assertNotIn("embedding", paragraph_nodes[0])
        sample_card = next(iter(public_projection["case_cards"].values()))
        first_principle = sample_card["principles"][0]
        self.assertNotIn("text_private", first_principle)
        self.assertIn("paragraph_span", first_principle)


if __name__ == "__main__":
    unittest.main()
