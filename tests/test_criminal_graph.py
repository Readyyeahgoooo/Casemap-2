from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from casemap.criminal_graph import build_criminal_graph_artifacts
from casemap.domain_graph import build_domain_graph_artifacts
from casemap.hklii_crawler import HKLIICaseDocument, HKLIIParagraph, HKLIISearchResult
from casemap.source_parser import Passage, SourceDocument


class _FakeCrawler:
    def __init__(self, *args, **kwargs) -> None:
        self.warnings = []

    def simple_search(self, query: str, limit: int = 10) -> list[HKLIISearchResult]:
        return [
            HKLIISearchResult(
                title="HKSAR v. Wong Chun Man",
                subtitle="[2022] HKCA 978",
                path="/en/cases/hkca/2022/978",
                db="Court of Appeal",
                pub_date="2022-06-30T00:00:00+08:00",
            )
        ]

    def crawl_paths(self, public_paths: list[str]) -> list[HKLIICaseDocument]:
        return [
            HKLIICaseDocument(
                case_name="HKSAR v. Wong Chun Man",
                court_name="Court of Appeal",
                neutral_citation="[2022] HKCA 978",
                decision_date="2022-06-30T00:00:00+08:00",
                court_code="HKCA",
                public_url="https://www.hklii.hk/en/cases/hkca/2022/978",
                raw_html="",
                paragraphs=[
                    HKLIIParagraph("para 1", "The appeal concerns murder, secondary liability, and the scope of foresight in criminal responsibility."),
                    HKLIIParagraph("para 2", "The court discussed murder and manslaughter doctrines in Hong Kong criminal law."),
                ],
                judges=["Macrae VP, Zervos JA, A Pang JA"],
                cited_cases=[],
                cited_statutes=[],
                title="CACC 28/2020 HKSAR v. Wong Chun Man",
            )
        ]


def _fake_load_source_document(path: str):
    source = SourceDocument(
        source_id="source:criminal_textbook",
        label="Criminal Law In Hong Kong",
        path=str(path),
        kind="pdf",
    )
    passages = [
        Passage(
            passage_id="source:criminal_textbook:p0001:01",
            source_id=source.source_id,
            source_label=source.label,
            source_kind=source.kind,
            location="page 1",
            order=1,
            text="Murder and manslaughter are core homicide topics. HKSAR v Wong Chun Man discusses murder and secondary liability.",
        ),
        Passage(
            passage_id="source:criminal_textbook:p0002:01",
            source_id=source.source_id,
            source_label=source.label,
            source_kind=source.kind,
            location="page 2",
            order=2,
            text="Theft and robbery involve dishonesty, appropriation, and force under Hong Kong criminal law.",
        ),
    ]
    return source, passages


class CriminalGraphTests(unittest.TestCase):
    @mock.patch("casemap.criminal_graph.load_source_document", side_effect=_fake_load_source_document)
    @mock.patch("casemap.criminal_graph.HKLIICrawler", _FakeCrawler)
    def test_build_criminal_graph_artifacts_smoke(self, mocked_loader) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir) / "relationship"
            hybrid_dir = Path(tmp_dir) / "hybrid"
            manifest = build_criminal_graph_artifacts(
                source_paths=["/tmp/fake-source.pdf"],
                relationship_output_dir=output_dir,
                hybrid_output_dir=hybrid_dir,
                max_cases=4,
                embedding_backend="local-hash",
            )

            self.assertEqual(manifest["storage"]["embedding_backend"]["backend"], "local-hash")
            self.assertTrue((output_dir / "relationship_graph.json").exists())
            self.assertTrue((output_dir / "chroma_records.json").exists())
            self.assertTrue((output_dir / "monitor_report.json").exists())
            self.assertTrue((output_dir / "monitor_report.html").exists())
            self.assertTrue((output_dir / "build_progress.json").exists())
            self.assertTrue((hybrid_dir / "hierarchical_graph.json").exists())

            chroma_payload = json.loads((output_dir / "chroma_records.json").read_text(encoding="utf-8"))
            self.assertEqual(chroma_payload["collection"], "hk_criminal_cases")
            self.assertEqual(chroma_payload["embedding_backend"]["backend"], "local-hash")
            self.assertGreater(len(chroma_payload["records"]), 0)

            progress_payload = json.loads((output_dir / "build_progress.json").read_text(encoding="utf-8"))
            self.assertEqual(progress_payload["status"], "completed")
            self.assertEqual(progress_payload["stage"], "completed")
            self.assertEqual(progress_payload["percent"], 100)

            monitor_html = (output_dir / "monitor_report.html").read_text(encoding="utf-8")
            self.assertIn("Coverage Summary", monitor_html)
            self.assertIn("refreshes every 5 minutes", monitor_html)

            bundle = json.loads((hybrid_dir / "hierarchical_graph.json").read_text(encoding="utf-8"))
            self.assertEqual(bundle["meta"]["viewer_heading_public"], "Hong Kong Criminal Law Hierarchical Knowledge Graph")
            self.assertEqual(bundle["meta"]["viewer_heading_internal"], "Hong Kong Criminal Law Internal Hierarchy Explorer")
            self.assertEqual(bundle["meta"]["legal_domain"], "criminal")
            case_names = {
                node.get("case_name", node.get("label", ""))
                for node in bundle["nodes"]
                if node["type"] == "Case"
            }
            self.assertNotIn("Chiu Man On Paul t/a Pacific Power Engineering Co. v Vaford Contracting Co. Ltd.", case_names)

    @mock.patch("casemap.domain_graph.load_source_document", side_effect=_fake_load_source_document)
    @mock.patch("casemap.domain_graph.HKLIICrawler", _FakeCrawler)
    def test_build_domain_graph_artifacts_uses_requested_domain(self, mocked_loader) -> None:
        family_tree = {
            "label_en": "Hong Kong Family Law",
            "summary_en": "Family-law authority tree for matrimonial and child-related disputes.",
            "modules": [
                {
                    "id": "children",
                    "label_en": "Children",
                    "summary_en": "Children, care, custody, and welfare principles.",
                    "subgrounds": [
                        {
                            "id": "welfare",
                            "label_en": "Welfare Principle",
                            "summary_en": "Best interests and welfare of children.",
                            "topics": [
                                {
                                    "id": "best_interests",
                                    "label_en": "Best Interests",
                                    "search_queries": ["best interests child hong kong family law"],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir) / "relationship"
            manifest = build_domain_graph_artifacts(
                domain_id="family",
                tree=family_tree,
                source_paths=["/tmp/fake-source.pdf"],
                relationship_output_dir=output_dir,
                max_cases=2,
                embedding_backend="local-hash",
            )

            self.assertEqual(manifest["legal_domain"], "family")
            chroma_payload = json.loads((output_dir / "chroma_records.json").read_text(encoding="utf-8"))
            self.assertEqual(chroma_payload["collection"], "hk_family_cases")
            graph_payload = json.loads((output_dir / "relationship_graph.json").read_text(encoding="utf-8"))
            self.assertEqual(graph_payload["meta"]["legal_domain"], "family")
            self.assertTrue(all(node["legal_domain"] == "family" for node in graph_payload["nodes"]))


if __name__ == "__main__":
    unittest.main()
