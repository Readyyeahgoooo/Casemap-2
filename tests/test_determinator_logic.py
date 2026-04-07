from __future__ import annotations

import json
import os
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest import mock

from casemap.hybrid_graph import DeterminatorPipeline, HybridGraphStore, KnowledgeGrowthWriter


def _minimal_bundle() -> dict:
    return {
        "meta": {"legal_domain": "criminal", "title": "Test", "node_count": 1, "edge_count": 0},
        "nodes": [
            {
                "id": "module:gp",
                "type": "Module",
                "label": "General Principles",
                "label_en": "General Principles",
                "summary": "",
                "legal_domain": "criminal",
                "domain_tags": ["criminal"],
                "degree": 0,
            }
        ],
        "edges": [],
        "case_cards": {},
        "tree": {"id": "criminal_law", "label_en": "Criminal Law", "label_zh": "", "modules": []},
    }


@dataclass
class _Paragraph:
    paragraph_span: str
    text: str


@dataclass
class _Reference:
    label: str
    url: str
    kind: str


@dataclass
class _CaseDoc:
    case_name: str
    court_name: str
    neutral_citation: str
    decision_date: str
    court_code: str
    public_url: str
    raw_html: str
    paragraphs: list[_Paragraph]
    judges: list[str]
    cited_cases: list[_Reference]
    cited_statutes: list[_Reference]
    title: str = ""


class DeterminatorLogicTests(unittest.TestCase):
    def test_tax_query_maps_to_inland_revenue_ordinance(self) -> None:
        pipeline = DeterminatorPipeline()
        classification = pipeline._classify("What if I do not pay tax in Hong Kong?")
        self.assertTrue(classification["offence_candidates"])
        self.assertIn("Inland Revenue Ordinance", classification["primary_ordinance"]["ordinance"])

    def test_dog_query_maps_to_animal_cruelty(self) -> None:
        pipeline = DeterminatorPipeline()
        classification = pipeline._classify("What is my liability if I stab my own dog?")
        self.assertTrue(classification["offence_candidates"])
        self.assertIn("Cap. 169", classification["primary_ordinance"]["ordinance"])

    def test_unverified_growth_item_is_rejected(self) -> None:
        writer = KnowledgeGrowthWriter()
        verified, rejected = writer.verify_items(
            [{"type": "Case", "label": "Made Up Case", "neutral_citation": "[2024] HKCA 999"}],
            legal_domain="criminal",
        )
        self.assertEqual(verified, [])
        self.assertEqual(len(rejected), 1)
        self.assertIn("Missing HKLII URL", rejected[0]["reason"])

    def test_verified_growth_item_can_sync_to_supabase(self) -> None:
        writer = KnowledgeGrowthWriter()
        store = HybridGraphStore(_minimal_bundle())
        case_doc = _CaseDoc(
            case_name="HKSAR v Example",
            court_name="Court of Appeal",
            neutral_citation="[2024] HKCA 123",
            decision_date="2024-01-01",
            court_code="HKCA",
            public_url="https://www.hklii.hk/en/cases/hkca/2024/123",
            raw_html="",
            paragraphs=[_Paragraph("[1]", "Verified example paragraph.")],
            judges=["Example JA"],
            cited_cases=[],
            cited_statutes=[],
            title="HKSAR v Example",
        )
        item = {
            "type": "Case",
            "label": "HKSAR v Example",
            "neutral_citation": "[2024] HKCA 123",
            "ratio": "Verified example ratio",
            "ordinance": "Cap. 210",
            "hklii_url": case_doc.public_url,
            "_verified_case_document": case_doc,
            "verification_status": "verified_hklii",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_path = Path(tmpdir) / "hierarchical_graph.json"
            graph_path.write_text(json.dumps(store.bundle), encoding="utf-8")
            with mock.patch.dict(
                os.environ,
                {
                    "SUPABASE_URL": "https://example.supabase.co",
                    "SUPABASE_PUBLISHABLE_KEY": "pub",
                    "SUPABASE_SERVICE_ROLE_KEY": "svc",
                },
                clear=False,
            ):
                with mock.patch("casemap.supabase_sync.sync_case_document_to_supabase") as sync_mock:
                    added = writer.persist([item], store, graph_path)
        self.assertEqual(len(added), 1)
        sync_mock.assert_called_once()

    def test_determinator_page_safely_embeds_hierarchy_html(self) -> None:
        from casemap.viewer import render_determinator_page

        html = render_determinator_page(
            _minimal_bundle(),
            "<html><body><script>window.bad = true;</script><div>Hierarchy</div></body></html>",
        )
        self.assertIn("atob(", html)
        self.assertNotIn("const hierarchyHtml = \"<html><body><script>", html)


if __name__ == "__main__":
    unittest.main()
