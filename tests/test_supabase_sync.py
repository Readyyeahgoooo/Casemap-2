from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from casemap.supabase_sync import (
    _case_priority,
    _derive_hklii_id,
    _derive_public_path,
    _looks_criminally_relevant,
    load_env_file,
)


class SupabaseSyncTests(unittest.TestCase):
    def test_derive_hklii_id(self) -> None:
        self.assertEqual(_derive_hklii_id("/en/cases/hkca/2022/978"), "hkca_2022_978")

    def test_derive_public_path_prefers_explicit_hklii_link(self) -> None:
        node = {
            "links": [
                {"url": "https://www.hklii.hk/en/cases/hkdc/2022/1083"},
                {"url": "https://example.com/not-used"},
            ],
            "neutral_citation": "[2022] HKDC 1083",
            "court_code": "HKDC",
        }
        self.assertEqual(_derive_public_path(node), "/en/cases/hkdc/2022/1083")

    def test_derive_public_path_can_reconstruct_from_citation_and_court(self) -> None:
        node = {
            "links": [],
            "neutral_citation": "[2016] HKCFA 87",
            "court_code": "HKCFA",
        }
        self.assertEqual(_derive_public_path(node), "/en/cases/hkcfa/2016/87")

    def test_load_env_file_sets_missing_values_without_overwriting(self) -> None:
        original_value = os.environ.get("CASEMAP_TEST_ENV")
        os.environ["CASEMAP_TEST_ENV"] = "keep-me"
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                env_path = Path(tmp_dir) / ".env.local"
                env_path.write_text(
                    "CASEMAP_TEST_ENV=replace-me\nCASEMAP_ANOTHER_ENV=hello\n",
                    encoding="utf-8",
                )
                self.assertTrue(load_env_file(env_path))
                self.assertEqual(os.environ["CASEMAP_TEST_ENV"], "keep-me")
                self.assertEqual(os.environ["CASEMAP_ANOTHER_ENV"], "hello")
        finally:
            if original_value is None:
                os.environ.pop("CASEMAP_TEST_ENV", None)
            else:
                os.environ["CASEMAP_TEST_ENV"] = original_value
            os.environ.pop("CASEMAP_ANOTHER_ENV", None)

    def test_case_priority_prefers_richer_nodes(self) -> None:
        generic_node = {"label": "[2021] HKCFI 906", "summary_en": "Authority cited inside an HKLII criminal-law judgment."}
        richer_node = {
            "label": "HKSAR v. CHAN KAM SHING",
            "summary_en": "Murder and manslaughter principles in the Court of Final Appeal.",
            "principles": [{"statement_en": "Constructive manslaughter."}],
        }
        self.assertGreater(_case_priority(richer_node), _case_priority(generic_node))

    def test_generic_cited_authority_requires_criminal_case_name(self) -> None:
        generic_node = {"summary_en": "Authority cited inside an HKLII criminal-law judgment."}
        self.assertTrue(_looks_criminally_relevant(generic_node, "HKSAR v. ALI MUMTAZ"))
        self.assertFalse(_looks_criminally_relevant(generic_node, "LUSO INTERNATIONAL BANKING LTD v. SUMMI (GROUP) HOLDINGS LTD"))

    def test_generic_cited_authority_can_still_be_kept_for_evidential_relevance(self) -> None:
        generic_node = {"summary_en": "Authority cited inside an HKLII criminal-law judgment."}
        self.assertTrue(
            _looks_criminally_relevant(
                generic_node,
                "A BANK v. B COMPANY",
                title="On hearsay and evidence",
                sample_text="The appeal considers hearsay evidence and burden of proof.",
            )
        )


if __name__ == "__main__":
    unittest.main()
