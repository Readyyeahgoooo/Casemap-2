from __future__ import annotations

from collections import Counter, defaultdict, deque
from datetime import UTC, datetime
from pathlib import Path
import json
import math
import os
import re
from urllib import error as urllib_error
from urllib import request as urllib_request

from .case_enrichment_data import CURATED_CASE_ENRICHMENTS
from .graphrag import normalize_scores, slugify, tokenize
from .relationship_graph import export_public_relationship_payload

CASE_EDGE_TYPES = {"CITES", "FOLLOWS", "APPLIES", "DISTINGUISHES", "OVERRULES", "DOUBTS"}
TREATMENT_EDGE_TYPES = {"FOLLOWS", "APPLIES", "DISTINGUISHES", "OVERRULES", "DOUBTS", "INTERPRETS"}
COURT_LEVEL_SCORES = {"CFA": 1.0, "CA": 0.82, "CFI": 0.6, "DC": 0.45, "TRIB": 0.3}
VECTOR_DIMENSIONS = 1536
NEO4J_CONSTRAINTS_CYPHER = f"""// Core uniqueness constraints
CREATE CONSTRAINT module_id IF NOT EXISTS FOR (n:Module) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT subground_id IF NOT EXISTS FOR (n:Subground) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT topic_id IF NOT EXISTS FOR (n:Topic) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT topic_path IF NOT EXISTS FOR (n:Topic) REQUIRE n.path IS UNIQUE;
CREATE CONSTRAINT lineage_id IF NOT EXISTS FOR (n:AuthorityLineage) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT case_id IF NOT EXISTS FOR (n:Case) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT statute_id IF NOT EXISTS FOR (n:Statute) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT paragraph_id IF NOT EXISTS FOR (n:Paragraph) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT proposition_id IF NOT EXISTS FOR (n:Proposition) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT judge_id IF NOT EXISTS FOR (n:Judge) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT source_id IF NOT EXISTS FOR (n:SourceDocument) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT case_neutral_citation IF NOT EXISTS FOR (n:Case) REQUIRE n.neutral_citation IS UNIQUE;
CREATE CONSTRAINT statute_cap_section_key IF NOT EXISTS FOR (n:Statute) REQUIRE n.cap_section_key IS UNIQUE;

// Search indexes
CREATE INDEX case_name IF NOT EXISTS FOR (n:Case) ON (n.case_name);
CREATE INDEX case_court_code IF NOT EXISTS FOR (n:Case) ON (n.court_code);
CREATE INDEX case_decision_date IF NOT EXISTS FOR (n:Case) ON (n.decision_date);
CREATE INDEX topic_label_en IF NOT EXISTS FOR (n:Topic) ON (n.label_en);

// Vector indexes
CREATE VECTOR INDEX case_summary_embedding IF NOT EXISTS
FOR (n:Case) ON (n.summary_embedding)
OPTIONS {{indexConfig: {{`vector.dimensions`: {VECTOR_DIMENSIONS}, `vector.similarity_function`: 'cosine'}}}};

CREATE VECTOR INDEX paragraph_embedding IF NOT EXISTS
FOR (n:Paragraph) ON (n.embedding)
OPTIONS {{indexConfig: {{`vector.dimensions`: {VECTOR_DIMENSIONS}, `vector.similarity_function`: 'cosine'}}}};
"""

NEO4J_IMPORT_TEMPLATE = """// Requires APOC for dynamic labels.
// Load hierarchical_graph.json externally and pass {nodes: [...], edges: [...]} as parameters.
UNWIND $nodes AS node
CALL apoc.merge.node([node.type], {id: node.id}, node, node) YIELD node AS merged_node
RETURN count(merged_node) AS merged_nodes;

UNWIND $edges AS edge
MATCH (source {id: edge.source})
MATCH (target {id: edge.target})
CALL apoc.merge.relationship(source, edge.type, {source: edge.source, target: edge.target}, edge, target)
YIELD rel
RETURN count(rel) AS merged_relationships;
"""

OPENROUTER_API_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_DEFAULT_MODEL = "openrouter/auto"
OPENROUTER_TIMEOUT_SECONDS = 25
OPENROUTER_CITATION_TAG_RE = re.compile(r"\[(C\d+)\]")


def _normalize_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _stable_statute_key(label: str) -> str:
    cap_match = re.search(r"Cap(?:\.|\s)(\d+[A-Z]?)", label, flags=re.IGNORECASE)
    section_match = re.search(r"\bs(?:ection)?s?\.?\s*([0-9A-Z(),.\-\s]+)", label, flags=re.IGNORECASE)
    cap = cap_match.group(1).upper() if cap_match else "UNK"
    section = section_match.group(1).strip().upper() if section_match else "GEN"
    section = re.sub(r"\s+", "", section)
    return f"{cap}:{section}"


def _short_case_name(label: str) -> str:
    compact = re.sub(r"\s+", " ", label).strip()
    if len(compact) <= 60:
        return compact
    if " v " in compact:
        left, right = compact.split(" v ", 1)
        return f"{left[:24].strip()} v {right[:24].strip()}".strip()
    return compact[:57].rstrip() + "..."


def _court_score(court_level: str, lineage_count: int, typed_links: int, degree: int) -> float:
    base = COURT_LEVEL_SCORES.get(court_level.upper(), 0.25) if court_level else 0.25
    score = base + (0.08 * min(lineage_count, 4)) + (0.03 * min(typed_links, 8)) + (0.01 * min(degree, 15))
    return round(min(score, 1.6), 4)


def _extract_openrouter_message_text(content: object) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if not isinstance(part, dict):
                continue
            text = part.get("text") or part.get("content")
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())
        return "\n".join(parts).strip()
    return ""


def _openrouter_grounded_answer(question: str, citations: list[dict], model: str = "") -> tuple[str, str]:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured")
    if not citations:
        raise RuntimeError("No citations available for grounded synthesis")

    selected_model = model.strip() or os.environ.get("OPENROUTER_MODEL", "").strip() or OPENROUTER_DEFAULT_MODEL
    evidence_lines = []
    for citation in citations:
        evidence_lines.append(
            (
                f"[{citation['citation_id']}] "
                f"Case: {citation.get('case_name', '')} {citation.get('neutral_citation', '')}\n"
                f"Paragraph: {citation.get('paragraph_span', '') or 'n/a'}\n"
                f"Quote: {citation.get('quote', '')}"
            ).strip()
        )

    payload = {
        "model": selected_model,
        "temperature": 0,
        "top_p": 1,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a legal GraphRAG synthesis assistant. Answer using only the provided evidence. "
                    "Do not invent cases, statutes, facts, or paragraphs. Every factual sentence must end with one or more "
                    "citation tags like [C1]. If evidence is insufficient, explicitly say so."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question:\n{question.strip()}\n\n"
                    "Evidence:\n"
                    + "\n\n".join(evidence_lines)
                    + "\n\nReturn a concise legal analysis grounded only in the evidence above."
                ),
            },
        ],
    }

    request = urllib_request.Request(
        OPENROUTER_API_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib_request.urlopen(request, timeout=OPENROUTER_TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8")
    except urllib_error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else ""
        raise RuntimeError(f"OpenRouter HTTP {exc.code}: {body[:240]}".strip()) from exc
    except urllib_error.URLError as exc:
        raise RuntimeError(f"OpenRouter request failed: {exc.reason}") from exc

    parsed = json.loads(raw)
    choices = parsed.get("choices", [])
    if not choices:
        raise RuntimeError("OpenRouter returned no choices")
    message = choices[0].get("message", {})
    answer = _extract_openrouter_message_text(message.get("content", ""))
    if not answer:
        raise RuntimeError("OpenRouter returned an empty message")

    valid_ids = {citation["citation_id"] for citation in citations}
    cited_ids = set(OPENROUTER_CITATION_TAG_RE.findall(answer))
    if not cited_ids:
        raise RuntimeError("OpenRouter response did not include citation tags")
    if not cited_ids.issubset(valid_ids):
        unknown = sorted(cited_ids - valid_ids)
        raise RuntimeError(f"OpenRouter response referenced unknown citations: {', '.join(unknown)}")
    return answer.strip(), selected_model


def _code_to_edge_type(code: str, fallback_treatment: str = "") -> str:
    normalized = (code or "").upper()
    if normalized == "FLLW":
        return "FOLLOWS"
    if normalized == "APPD":
        return "APPLIES"
    if normalized == "DIST":
        return "DISTINGUISHES"
    if normalized == "DPRT":
        return "OVERRULES"
    treatment = fallback_treatment.lower()
    if "follow" in treatment or "adopt" in treatment:
        return "FOLLOWS"
    if "distinguish" in treatment or "qualif" in treatment:
        return "DISTINGUISHES"
    if "overrule" in treatment or "depart" in treatment:
        return "OVERRULES"
    if "doubt" in treatment:
        return "DOUBTS"
    return "APPLIES"


def _clone_public(value):
    if isinstance(value, dict):
        return {key: _clone_public(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_clone_public(item) for item in value]
    return value


def _strip_private_fields(node: dict) -> dict:
    public_node = _clone_public(node)
    for key in ("embedding", "summary_embedding", "text_private"):
        public_node.pop(key, None)
    if public_node.get("type") == "Paragraph":
        public_node["public_excerpt"] = public_node.get("public_excerpt", "")
    return public_node


def _strip_private_case_card(card: dict) -> dict:
    public_card = _clone_public(card)
    for principle in public_card.get("principles", []):
        principle.pop("text_private", None)
        principle.pop("embedding", None)
    return public_card


def _match_existing_topic_ids(hint: str, topic_nodes: dict[str, dict], subground_lookup: dict[str, dict]) -> list[str]:
    normalized_hint = _normalize_label(hint)
    if not normalized_hint:
        return []

    direct_matches = [
        topic_id
        for topic_id, topic in topic_nodes.items()
        if normalized_hint == _normalize_label(topic.get("label_en", topic.get("label", "")))
        or normalized_hint == _normalize_label(topic.get("label", ""))
    ]
    if direct_matches:
        return direct_matches

    contains_matches = [
        topic_id
        for topic_id, topic in topic_nodes.items()
        if normalized_hint in _normalize_label(topic.get("label_en", topic.get("label", "")))
        or _normalize_label(topic.get("label_en", topic.get("label", ""))) in normalized_hint
    ]
    if contains_matches:
        return contains_matches[:2]

    subground_matches = [
        subground_id
        for subground_id, subground in subground_lookup.items()
        if normalized_hint == _normalize_label(subground.get("label_en", subground.get("label", "")))
        or normalized_hint in _normalize_label(subground.get("label_en", subground.get("label", "")))
    ]
    topic_ids: list[str] = []
    for subground_id in subground_matches:
        topic_ids.extend(subground_lookup[subground_id].get("topic_ids", []))
    return topic_ids[:2]


def _make_topic_path(module_label: str, subground_label: str, topic_label: str) -> str:
    return f"{module_label}/{subground_label}/{topic_label}"


def build_hierarchical_graph_bundle(relationship_payload: dict, title: str | None = None) -> dict:
    public_projection = (
        relationship_payload
        if relationship_payload.get("meta", {}).get("authority_tree")
        else export_public_relationship_payload(relationship_payload, title=title)
    )
    effective_title = title or public_projection.get("meta", {}).get("title") or relationship_payload.get("meta", {}).get("title")

    bundle_nodes: list[dict] = []
    bundle_edges: list[dict] = []
    node_ids: set[str] = set()
    edge_keys: set[tuple[str, str, str]] = set()
    original_node_lookup = {node["id"]: node for node in relationship_payload.get("nodes", [])}
    public_node_lookup = {node["id"]: node for node in public_projection.get("nodes", [])}
    tree = public_projection["meta"]["authority_tree"]
    topic_context: dict[str, dict] = {}
    topic_nodes: dict[str, dict] = {}
    subground_lookup: dict[str, dict] = {}
    module_lookup: dict[str, dict] = {}

    def add_node(node: dict) -> dict:
        if node["id"] in node_ids:
            existing = next(item for item in bundle_nodes if item["id"] == node["id"])
            existing.update({key: value for key, value in node.items() if value not in (None, [], "", {})})
            return existing
        node_ids.add(node["id"])
        bundle_nodes.append(node)
        return node

    def add_edge(source: str, target: str, edge_type: str, **properties: object) -> None:
        key = (source, target, edge_type)
        if key in edge_keys or source not in node_ids or target not in node_ids:
            return
        edge = {
            "source": source,
            "target": target,
            "type": edge_type,
            "weight": float(properties.pop("weight", 1.0)),
        }
        edge.update(properties)
        bundle_edges.append(edge)
        edge_keys.add(key)

    def ensure_source_document(label: str, kind: str, path: str = "") -> dict:
        source_id = f"source_document:{slugify(label)[:80]}"
        return add_node(
            {
                "id": source_id,
                "type": "SourceDocument",
                "label": label,
                "label_en": label,
                "kind": kind,
                "path": path,
            }
        )

    def ensure_case(case_name: str, neutral_citation: str = "", **updates: object) -> dict:
        normalized = _normalize_label(case_name)
        for node in bundle_nodes:
            if node["type"] != "Case":
                continue
            if neutral_citation and node.get("neutral_citation") == neutral_citation:
                node.update({key: value for key, value in updates.items() if value not in (None, "")})
                return node
            if normalized and _normalize_label(node.get("case_name", node.get("label", ""))) == normalized:
                if neutral_citation and not node.get("neutral_citation"):
                    node["neutral_citation"] = neutral_citation
                node.update({key: value for key, value in updates.items() if value not in (None, "")})
                return node
        case_id = f"case:{slugify(neutral_citation or case_name)[:80]}"
        case_node = {
            "id": case_id,
            "type": "Case",
            "label": case_name,
            "case_name": case_name,
            "short_name": _short_case_name(case_name),
            "neutral_citation": neutral_citation,
            "parallel_citations": [],
            "court_code": "",
            "court_name": "",
            "court_level": "",
            "decision_date": "",
            "judges": [],
            "source_links": [],
            "summary_en": "",
            "summary_zh": "",
            "authority_score": 0.0,
            "topic_paths": [],
            "lineage_ids": [],
            "enrichment_status": "case_only",
            "summary_embedding": [],
            "references": [],
        }
        case_node.update({key: value for key, value in updates.items() if value is not None})
        return add_node(case_node)

    def ensure_statute(label: str) -> dict:
        normalized = _normalize_label(label)
        for node in bundle_nodes:
            if node["type"] == "Statute" and _normalize_label(node.get("label", "")) == normalized:
                return node
        return add_node(
            {
                "id": f"statute:{slugify(label)[:80]}",
                "type": "Statute",
                "label": label,
                "title": label,
                "cap_section_key": _stable_statute_key(label),
                "source_links": [],
                "summary_en": "",
                "summary_zh": "",
            }
        )

    def ensure_synthetic_subground(module_id: str, label: str) -> dict:
        synthetic_id = f"subground:{slugify(module_id)}:synthetic:{slugify(label)[:40]}"
        if synthetic_id in subground_lookup:
            return subground_lookup[synthetic_id]
        module = module_lookup[module_id]
        node = add_node(
            {
                "id": synthetic_id,
                "type": "Subground",
                "label": label,
                "label_en": label,
                "label_zh": "",
                "module_id": module_id,
                "summary": f"Synthetic subground created to absorb additional graph concepts under {module['label_en']}.",
                "topic_ids": [],
            }
        )
        subground_lookup[synthetic_id] = node
        add_edge(module_id, synthetic_id, "CONTAINS")
        return node

    def ensure_synthetic_topic(hint: str) -> str:
        topic_id = f"topic:synthetic:{slugify(hint)[:56]}"
        if topic_id in topic_nodes:
            return topic_id
        chosen_subground_id = ""
        normalized_hint = _normalize_label(hint)
        for subground_id, subground in subground_lookup.items():
            label = _normalize_label(subground.get("label_en", subground.get("label", "")))
            if normalized_hint and (normalized_hint in label or label in normalized_hint):
                chosen_subground_id = subground_id
                break
        if not chosen_subground_id:
            fallback_module_id = "module:cross_cutting" if "module:cross_cutting" in module_lookup else next(iter(module_lookup))
            chosen_subground_id = ensure_synthetic_subground(fallback_module_id, "Derived Topics")["id"]
        subground = subground_lookup[chosen_subground_id]
        module = module_lookup[subground["module_id"]]
        topic_node = add_node(
            {
                "id": topic_id,
                "type": "Topic",
                "label": hint,
                "label_en": hint,
                "label_zh": "",
                "summary": f"Synthetic topic created from case enrichment data for {hint}.",
                "path": _make_topic_path(module["label_en"], subground.get("label_en", subground["label"]), hint),
                "module_id": module["id"],
                "subground_id": chosen_subground_id,
            }
        )
        topic_nodes[topic_id] = topic_node
        subground.setdefault("topic_ids", []).append(topic_id)
        add_edge(chosen_subground_id, topic_id, "CONTAINS")
        topic_context[topic_id] = {
            "module_id": module["id"],
            "module_label": module["label_en"],
            "subground_id": chosen_subground_id,
            "subground_label": subground.get("label_en", subground["label"]),
            "path": topic_node["path"],
        }
        return topic_id

    def resolve_topic_ids(hints: list[str]) -> list[str]:
        resolved: list[str] = []
        for hint in hints:
            matched = _match_existing_topic_ids(hint, topic_nodes, subground_lookup)
            if matched:
                for topic_id in matched:
                    if topic_id not in resolved:
                        resolved.append(topic_id)
                continue
            synthetic_id = ensure_synthetic_topic(hint)
            if synthetic_id not in resolved:
                resolved.append(synthetic_id)
        return resolved

    for module in tree["modules"]:
        module_id = module["id"]
        module_node = add_node(
            {
                "id": module_id,
                "type": "Module",
                "label": module["label_en"],
                "label_en": module["label_en"],
                "label_zh": module.get("label_zh", ""),
                "summary": module.get("summary_en", module.get("summary", "")),
            }
        )
        module_lookup[module_id] = module_node
        for subground in module.get("subgrounds", []):
            subground_node = add_node(
                {
                    "id": subground["id"],
                    "type": "Subground",
                    "label": subground["label_en"],
                    "label_en": subground["label_en"],
                    "label_zh": subground.get("label_zh", ""),
                    "summary": subground.get("summary_en", subground.get("summary", "")),
                    "module_id": module_id,
                    "children": subground.get("children", []),
                    "topic_ids": list(subground.get("topic_ids", [])),
                }
            )
            subground_lookup[subground["id"]] = subground_node
            add_edge(module_id, subground["id"], "CONTAINS")

    for topic_id, public_topic in public_node_lookup.items():
        if public_topic["type"] != "topic":
            continue
        context = None
        for module in tree["modules"]:
            for subground in module.get("subgrounds", []):
                if topic_id in subground.get("topic_ids", []):
                    context = {
                        "module_id": module["id"],
                        "module_label": module["label_en"],
                        "subground_id": subground["id"],
                        "subground_label": subground["label_en"],
                    }
                    break
            if context:
                break
        if not context:
            synthetic_subground = ensure_synthetic_subground("module:cross_cutting", "Derived Topics")
            context = {
                "module_id": "module:cross_cutting",
                "module_label": module_lookup["module:cross_cutting"]["label_en"],
                "subground_id": synthetic_subground["id"],
                "subground_label": synthetic_subground["label_en"],
            }
        path = _make_topic_path(context["module_label"], context["subground_label"], public_topic["label"])
        topic_node = add_node(
            {
                "id": topic_id,
                "type": "Topic",
                "label": public_topic["label"],
                "label_en": public_topic["label"],
                "label_zh": "",
                "summary": public_topic.get("summary", ""),
                "path": path,
                "module_id": context["module_id"],
                "subground_id": context["subground_id"],
            }
        )
        topic_nodes[topic_id] = topic_node
        topic_context[topic_id] = {**context, "path": path}
        add_edge(context["subground_id"], topic_id, "CONTAINS")

    for subground_id, subground in subground_lookup.items():
        topic_ids = [topic_id for topic_id in subground.get("topic_ids", []) if topic_id in topic_nodes]
        for index, left_topic in enumerate(topic_ids):
            for right_topic in topic_ids[index + 1 :]:
                add_edge(left_topic, right_topic, "RELATED_TOPIC", reason="same subground", weight=0.35)

    source_documents_by_id: dict[str, dict] = {}
    for source in relationship_payload.get("meta", {}).get("source_documents", []):
        source_node = ensure_source_document(source["label"], source.get("kind", "unknown"), source.get("path", ""))
        source_documents_by_id[source_node["id"]] = source_node
    for node in relationship_payload.get("nodes", []):
        if node.get("type") != "source":
            continue
        source_node = ensure_source_document(node["label"], node.get("metrics", {}).get("kind", "unknown"))
        source_documents_by_id[source_node["id"]] = source_node

    source_aliases = {
        source.get("label", ""): ensure_source_document(source.get("label", ""), source.get("kind", "unknown")).get("id")
        for source in relationship_payload.get("meta", {}).get("source_documents", [])
        if source.get("label")
    }

    for node in public_projection.get("nodes", []):
        if node["type"] == "case":
            original = original_node_lookup.get(node["id"], node)
            case_node = ensure_case(
                node["label"],
                summary_en=original.get("summary", node.get("summary", "")),
                source_links=original.get("links", node.get("links", [])),
                references=original.get("references", node.get("references", [])),
            )
            for reference in original.get("references", node.get("references", [])):
                source_label = reference.get("source_label", "")
                source_id = source_aliases.get(source_label)
                if source_id:
                    add_edge(source_id, case_node["id"], "MENTIONS", location=reference.get("location", ""))
        elif node["type"] == "statute":
            statute_node = ensure_statute(node["label"])
            statute_node["summary_en"] = original_node_lookup.get(node["id"], node).get("summary", node.get("summary", ""))
            statute_node["source_links"] = original_node_lookup.get(node["id"], node).get("links", node.get("links", []))
            for reference in original_node_lookup.get(node["id"], node).get("references", node.get("references", [])):
                source_label = reference.get("source_label", "")
                source_id = source_aliases.get(source_label)
                if source_id:
                    add_edge(source_id, statute_node["id"], "MENTIONS", location=reference.get("location", ""))

    for edge in public_projection.get("edges", []):
        source_node = public_node_lookup.get(edge["source"])
        target_node = public_node_lookup.get(edge["target"])
        edge_type = edge["type"]
        if source_node and source_node["type"] == "topic" and target_node and target_node["type"] == "case":
            context = topic_context.get(source_node["id"], {})
            case_node = ensure_case(target_node["label"])
            path = context.get("path", source_node["label"])
            if path not in case_node["topic_paths"]:
                case_node["topic_paths"].append(path)
            add_edge(
                case_node["id"],
                source_node["id"],
                "BELONGS_TO_TOPIC",
                score=round(float(edge.get("weight", 1.0)), 4),
                primary=edge_type == "lineage_case",
                assignment_source=edge_type,
                curated=edge_type == "lineage_case",
            )
        elif source_node and source_node["type"] == "topic" and target_node and target_node["type"] == "statute":
            statute_node = ensure_statute(target_node["label"])
            add_edge(statute_node["id"], source_node["id"], "BELONGS_TO_TOPIC", score=round(float(edge.get("weight", 1.0)), 4), assignment_source=edge_type, curated=edge_type == "lineage_statute")
        elif source_node and source_node["type"] == "source":
            mapped_source_id = source_aliases.get(source_node["label"])
            if mapped_source_id and target_node and target_node["type"] == "topic":
                add_edge(mapped_source_id, target_node["id"], "MENTIONS", mention_source=edge_type)

    for lineage in public_projection["meta"].get("lineages", []):
        lineage_id = f"lineage:{lineage['id']}"
        add_node(
            {
                "id": lineage_id,
                "type": "AuthorityLineage",
                "label": lineage["title"],
                "title": lineage["title"],
                "codes": lineage.get("codes", []),
                "topic_ids": list(lineage.get("topic_ids", [])),
            }
        )
        for topic_id in lineage.get("topic_ids", []):
            if topic_id in topic_nodes:
                add_edge(lineage_id, topic_id, "ABOUT_TOPIC")
        previous_member_id = ""
        previous_member_type = ""
        for member in lineage.get("members", []):
            if member["type"] == "case":
                member_node = ensure_case(member["label"])
            else:
                member_node = ensure_statute(member["label"])
            if lineage["id"] not in member_node.get("lineage_ids", []):
                member_node.setdefault("lineage_ids", []).append(lineage["id"])
            add_edge(
                lineage_id,
                member_node["id"],
                "HAS_MEMBER",
                position=member["position"],
                code=member.get("code", ""),
                treatment=member.get("treatment", ""),
                note=member.get("note", ""),
            )
            if previous_member_id and previous_member_type == member["type"]:
                lineage_edge_type = _code_to_edge_type(member.get("code", ""), member.get("treatment", ""))
                add_edge(previous_member_id, member_node["id"], lineage_edge_type, lineage_id=lineage["id"], curated=True, explanation=member.get("note", ""))
                if member["type"] == "case":
                    add_edge(previous_member_id, member_node["id"], "CITES", lineage_id=lineage["id"], curated=True)
            previous_member_id = member_node["id"]
            previous_member_type = member["type"]

    for enrichment in CURATED_CASE_ENRICHMENTS:
        case_node = ensure_case(
            enrichment["case_name"],
            enrichment["neutral_citation"],
            parallel_citations=enrichment.get("parallel_citations", []),
            short_name=enrichment.get("short_name", _short_case_name(enrichment["case_name"])),
            court_code=enrichment.get("court_code", ""),
            court_name=enrichment.get("court_name", ""),
            court_level=enrichment.get("court_level", ""),
            decision_date=enrichment.get("decision_date", ""),
            judges=enrichment.get("judges", []),
            source_links=enrichment.get("source_links", []),
            summary_en=enrichment.get("summary_en", ""),
            summary_zh=enrichment.get("summary_zh", ""),
            enrichment_status="seeded",
        )
        topic_ids = resolve_topic_ids(enrichment.get("topic_hints", []))
        for topic_id in topic_ids:
            context = topic_context.get(topic_id, {})
            if context.get("path") and context["path"] not in case_node["topic_paths"]:
                case_node["topic_paths"].append(context["path"])
            add_edge(case_node["id"], topic_id, "BELONGS_TO_TOPIC", score=1.0, primary=True, assignment_source="curated_case_enrichment", curated=True)
        for judge in enrichment.get("judges", []):
            judge_id = f"judge:{slugify(judge)[:80]}"
            add_node({"id": judge_id, "type": "Judge", "label": judge, "name": judge})
            add_edge(case_node["id"], judge_id, "DECIDED_BY")
        for index, principle in enumerate(enrichment.get("principles", []), start=1):
            paragraph_id = f"paragraph:{slugify((enrichment['neutral_citation'] or enrichment['case_name']) + ':' + str(index))[:80]}"
            proposition_id = f"proposition:{slugify((enrichment['neutral_citation'] or enrichment['case_name']) + ':' + principle['label_en'])[:80]}"
            paragraph_node = add_node(
                {
                    "id": paragraph_id,
                    "type": "Paragraph",
                    "label": f"{case_node['short_name']} {principle.get('paragraph_span', '').strip()}".strip(),
                    "case_id": case_node["id"],
                    "para_start": principle.get("para_start"),
                    "para_end": principle.get("para_end"),
                    "paragraph_span": principle.get("paragraph_span", ""),
                    "public_excerpt": principle.get("statement_en", ""),
                    "text_private": principle.get("statement_en", ""),
                    "embedding": [],
                    "principle_ids": [proposition_id],
                }
            )
            proposition_node = add_node(
                {
                    "id": proposition_id,
                    "type": "Proposition",
                    "label": principle["label_en"],
                    "label_en": principle["label_en"],
                    "label_zh": principle.get("label_zh", ""),
                    "statement_en": principle.get("statement_en", ""),
                    "statement_zh": principle.get("statement_zh", ""),
                    "doctrine_key": slugify(principle["label_en"]),
                    "confidence": 0.98,
                }
            )
            add_edge(paragraph_node["id"], case_node["id"], "PART_OF")
            add_edge(paragraph_node["id"], proposition_node["id"], "SUPPORTS")
            cited_authority = principle.get("cited_authority")
            if cited_authority:
                if cited_authority["type"] == "case":
                    authority_node = ensure_case(cited_authority["label"])
                    add_edge(case_node["id"], authority_node["id"], "CITES", reason="principle citation", curated=True)
                else:
                    authority_node = ensure_statute(cited_authority["label"])
                add_edge(proposition_node["id"], authority_node["id"], "CITES", reason="principle citation", curated=True)
        for relationship in enrichment.get("relationships", []):
            if relationship["target_type"] == "case":
                target_node = ensure_case(relationship["target_label"])
                add_edge(case_node["id"], target_node["id"], relationship["type"], explanation=relationship["description"], curated=True)
                add_edge(case_node["id"], target_node["id"], "CITES", explanation=relationship["description"], curated=True)
            else:
                target_node = ensure_statute(relationship["target_label"])
                add_edge(case_node["id"], target_node["id"], relationship["type"], explanation=relationship["description"], curated=True)

    outgoing: defaultdict[str, list[dict]] = defaultdict(list)
    incoming: defaultdict[str, list[dict]] = defaultdict(list)
    for edge in bundle_edges:
        outgoing[edge["source"]].append(edge)
        incoming[edge["target"]].append(edge)

    shared_topic_counts: Counter[tuple[str, str]] = Counter()
    case_topic_memberships: defaultdict[str, set[str]] = defaultdict(set)
    for edge in bundle_edges:
        if edge["type"] == "BELONGS_TO_TOPIC":
            case_topic_memberships[edge["source"]].add(edge["target"])
    for topic_ids in case_topic_memberships.values():
        topic_list = sorted(topic_ids)
        for index, left_topic in enumerate(topic_list):
            for right_topic in topic_list[index + 1 :]:
                shared_topic_counts[(left_topic, right_topic)] += 1
    for (left_topic, right_topic), count in shared_topic_counts.items():
        if count >= 2:
            add_edge(left_topic, right_topic, "RELATED_TOPIC", reason="shared authoritative cases", weight=min(1.0, 0.22 * count))

    bundle_node_lookup = {node["id"]: node for node in bundle_nodes}
    adjacency: defaultdict[str, set[str]] = defaultdict(set)
    for edge in bundle_edges:
        adjacency[edge["source"]].add(edge["target"])
        adjacency[edge["target"]].add(edge["source"])

    for node in bundle_nodes:
        node["degree"] = len(adjacency.get(node["id"], set()))
        if node["type"] == "Case":
            typed_link_count = sum(1 for edge in outgoing[node["id"]] + incoming[node["id"]] if edge["type"] in TREATMENT_EDGE_TYPES)
            lineage_count = len(node.get("lineage_ids", []))
            node["authority_score"] = _court_score(node.get("court_level", ""), lineage_count, typed_link_count, node["degree"])

    case_cards: dict[str, dict] = {}
    for node in bundle_nodes:
        if node["type"] != "Case":
            continue
        principles: list[dict] = []
        relationships: list[dict] = []
        lineage_memberships: list[dict] = []
        for edge in outgoing[node["id"]]:
            target = bundle_node_lookup[edge["target"]]
            if edge["type"] == "PART_OF":
                continue
            if target["type"] == "Paragraph":
                continue
            if edge["type"] in {"BELONGS_TO_TOPIC", "DECIDED_BY"}:
                continue
            if edge["type"] in TREATMENT_EDGE_TYPES or edge["type"] == "CITES":
                relationships.append(
                    {
                        "direction": "outgoing",
                        "type": edge["type"],
                        "target_id": target["id"],
                        "target_label": target.get("label", target.get("case_name", "")),
                        "target_type": target["type"],
                        "explanation": edge.get("explanation") or edge.get("reason") or edge.get("note") or "",
                    }
                )
        for edge in incoming[node["id"]]:
            source = bundle_node_lookup[edge["source"]]
            if edge["type"] == "HAS_MEMBER":
                lineage_memberships.append(
                    {
                        "lineage_id": source["id"].removeprefix("lineage:"),
                        "lineage_node_id": source["id"],
                        "lineage_title": source.get("title", source["label"]),
                        "position": edge.get("position"),
                        "code": edge.get("code", ""),
                        "treatment": edge.get("treatment", ""),
                        "topic_ids": source.get("topic_ids", []),
                        "note": edge.get("note", ""),
                    }
                )
                continue
            if edge["type"] in TREATMENT_EDGE_TYPES or edge["type"] == "CITES":
                relationships.append(
                    {
                        "direction": "incoming",
                        "type": edge["type"],
                        "target_id": source["id"],
                        "target_label": source.get("label", source.get("case_name", "")),
                        "target_type": source["type"],
                        "explanation": edge.get("explanation") or edge.get("reason") or edge.get("note") or "",
                    }
                )
        paragraph_nodes = [bundle_node_lookup[edge["source"]] for edge in incoming[node["id"]] if edge["type"] == "PART_OF"]
        for paragraph in sorted(paragraph_nodes, key=lambda item: (item.get("para_start") or 0, item["id"])):
            support_edges = outgoing[paragraph["id"]]
            proposition = next((bundle_node_lookup[edge["target"]] for edge in support_edges if edge["type"] == "SUPPORTS"), None)
            cited_edges = outgoing[proposition["id"]] if proposition else []
            cited_target = next((bundle_node_lookup[edge["target"]] for edge in cited_edges if edge["type"] == "CITES"), None)
            principles.append(
                {
                    "paragraph_span": paragraph.get("paragraph_span", ""),
                    "para_start": paragraph.get("para_start"),
                    "para_end": paragraph.get("para_end"),
                    "label_en": proposition.get("label_en", proposition.get("label", "")) if proposition else "",
                    "label_zh": proposition.get("label_zh", "") if proposition else "",
                    "statement_en": proposition.get("statement_en", paragraph.get("public_excerpt", "")) if proposition else paragraph.get("public_excerpt", ""),
                    "statement_zh": proposition.get("statement_zh", "") if proposition else "",
                    "public_excerpt": paragraph.get("public_excerpt", ""),
                    "text_private": paragraph.get("text_private", ""),
                    "cited_authority": (
                        {
                            "id": cited_target["id"],
                            "label": cited_target.get("label", cited_target.get("title", "")),
                            "type": cited_target["type"],
                        }
                        if cited_target
                        else None
                    ),
                }
            )

        lineage_titles = {membership["lineage_title"] for membership in lineage_memberships}
        same_lineage_cases: list[dict] = []
        for other in bundle_nodes:
            if other["type"] != "Case" or other["id"] == node["id"]:
                continue
            if set(other.get("lineage_ids", [])) & set(node.get("lineage_ids", [])):
                same_lineage_cases.append(
                    {
                        "id": other["id"],
                        "label": other["case_name"],
                        "neutral_citation": other.get("neutral_citation", ""),
                    }
                )
        derived_relationships = {
            "upstream_authorities": [
                relation for relation in relationships if relation["direction"] == "outgoing" and relation["type"] in {"FOLLOWS", "APPLIES", "CITES"}
            ],
            "downstream_applications": [
                relation for relation in relationships if relation["direction"] == "incoming" and relation["type"] in {"FOLLOWS", "APPLIES", "CITES"}
            ],
            "same_lineage_cases": sorted(same_lineage_cases, key=lambda item: item["label"])[:12],
            "statutory_interpretations": [
                relation for relation in relationships if relation["type"] == "INTERPRETS"
            ],
        }
        case_cards[node["id"]] = {
            "id": node["id"],
            "metadata": {
                "id": node["id"],
                "neutral_citation": node.get("neutral_citation", ""),
                "parallel_citations": node.get("parallel_citations", []),
                "case_name": node.get("case_name", node["label"]),
                "short_name": node.get("short_name", _short_case_name(node.get("case_name", node["label"]))),
                "court_code": node.get("court_code", ""),
                "court_name": node.get("court_name", ""),
                "court_level": node.get("court_level", ""),
                "decision_date": node.get("decision_date", ""),
                "judges": node.get("judges", []),
                "source_links": node.get("source_links", []),
                "summary_en": node.get("summary_en", ""),
                "summary_zh": node.get("summary_zh", ""),
                "authority_score": node.get("authority_score", 0.0),
                "topic_paths": sorted(node.get("topic_paths", [])),
                "lineage_ids": sorted(node.get("lineage_ids", [])),
                "lineage_titles": sorted(lineage_titles),
                "enrichment_status": node.get("enrichment_status", "case_only"),
            },
            "principles": principles,
            "relationships": sorted(relationships, key=lambda item: (item["type"], item["direction"], item["target_label"])),
            "lineage_memberships": sorted(lineage_memberships, key=lambda item: (item["lineage_title"], item["position"] or 0)),
            "derived_relationships": derived_relationships,
        }

    tree_modules: list[dict] = []
    for module in tree["modules"]:
        module_id = module["id"]
        module_case_ids: set[str] = set()
        module_lineage_ids: set[str] = set()
        subground_payloads: list[dict] = []
        for subground in [item for item in subground_lookup.values() if item["module_id"] == module_id]:
            topic_ids = [topic_id for topic_id in subground.get("topic_ids", []) if topic_id in topic_nodes]
            case_ids: set[str] = set()
            lineage_ids: set[str] = set()
            for topic_id in topic_ids:
                for edge in incoming[topic_id]:
                    if edge["type"] == "BELONGS_TO_TOPIC" and bundle_node_lookup[edge["source"]]["type"] == "Case":
                        case_ids.add(edge["source"])
                for edge in incoming[topic_id]:
                    if edge["type"] == "ABOUT_TOPIC":
                        lineage_ids.add(edge["source"].removeprefix("lineage:"))
            module_case_ids.update(case_ids)
            module_lineage_ids.update(lineage_ids)
            subground_payloads.append(
                {
                    "id": subground["id"],
                    "label_en": subground.get("label_en", subground["label"]),
                    "label_zh": subground.get("label_zh", ""),
                    "topic_ids": topic_ids,
                    "metrics": {
                        "topics": len(topic_ids),
                        "cases": len(case_ids),
                        "lineages": len(lineage_ids),
                    },
                }
            )
        tree_modules.append(
            {
                "id": module_id,
                "label_en": module_lookup[module_id]["label_en"],
                "label_zh": module_lookup[module_id].get("label_zh", ""),
                "metrics": {
                    "subgrounds": len(subground_payloads),
                    "cases": len(module_case_ids),
                    "lineages": len(module_lineage_ids),
                },
                "subgrounds": sorted(subground_payloads, key=lambda item: item["label_en"]),
            }
        )

    bundle = {
        "meta": {
            "title": effective_title,
            "generated_at": datetime.now(UTC).isoformat(),
            "node_count": len(bundle_nodes),
            "edge_count": len(bundle_edges),
            "case_count": sum(1 for node in bundle_nodes if node["type"] == "Case"),
            "statute_count": sum(1 for node in bundle_nodes if node["type"] == "Statute"),
            "topic_count": sum(1 for node in bundle_nodes if node["type"] == "Topic"),
            "lineage_count": sum(1 for node in bundle_nodes if node["type"] == "AuthorityLineage"),
            "paragraph_count": sum(1 for node in bundle_nodes if node["type"] == "Paragraph"),
            "proposition_count": sum(1 for node in bundle_nodes if node["type"] == "Proposition"),
            "enriched_case_count": sum(1 for node in bundle_nodes if node["type"] == "Case" and node.get("enrichment_status") != "case_only"),
            "notes": [
                "Hybrid hierarchical graph bundle generated from the Casemap relationship graph.",
                "Hierarchy is represented explicitly as Module -> Subground -> Topic while authorities remain graph-native.",
                "Neo4j constraints and import templates are included for database-backed deployment.",
            ],
            "neo4j": {
                "vector_dimensions": VECTOR_DIMENSIONS,
                "constraints_file": "neo4j_constraints.cypher",
                "import_file": "neo4j_import.cypher",
            },
            "viewer_heading_public": public_projection.get("meta", {}).get("viewer_heading_public", ""),
            "viewer_heading_internal": public_projection.get("meta", {}).get("viewer_heading_internal", ""),
            "viewer_intro_public": public_projection.get("meta", {}).get("viewer_intro_public", ""),
            "viewer_intro_internal": public_projection.get("meta", {}).get("viewer_intro_internal", ""),
        },
        "tree": {
            "id": tree["id"],
            "label_en": tree["label_en"],
            "label_zh": tree["label_zh"],
            "modules": sorted(tree_modules, key=lambda item: item["label_en"]),
        },
        "nodes": bundle_nodes,
        "edges": bundle_edges,
        "case_cards": case_cards,
    }
    return bundle


def export_public_projection(bundle: dict, title: str | None = None) -> dict:
    public_projection = {
        "meta": {
            **_clone_public(bundle["meta"]),
            "title": title or bundle["meta"]["title"],
            "public_mode": True,
        },
        "tree": _clone_public(bundle["tree"]),
        "nodes": [_strip_private_fields(node) for node in bundle["nodes"] if node["type"] != "SourceDocument"],
        "edges": _clone_public(bundle["edges"]),
        "case_cards": {
            case_id: _strip_private_case_card(card)
            for case_id, card in bundle.get("case_cards", {}).items()
            if bundle["case_cards"][case_id]["metadata"].get("enrichment_status") != "case_only"
        },
    }
    return public_projection


def write_hybrid_graph_artifacts(bundle: dict, output_dir: str | Path) -> dict:
    output_path = Path(output_dir).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    graph_file = output_path / "hierarchical_graph.json"
    manifest_file = output_path / "manifest.json"
    public_projection_file = output_path / "public_projection.json"
    neo4j_constraints_file = output_path / "neo4j_constraints.cypher"
    neo4j_import_file = output_path / "neo4j_import.cypher"

    graph_file.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest_file.write_text(json.dumps(bundle["meta"], indent=2, ensure_ascii=False), encoding="utf-8")
    public_projection_file.write_text(json.dumps(export_public_projection(bundle), indent=2, ensure_ascii=False), encoding="utf-8")
    neo4j_constraints_file.write_text(NEO4J_CONSTRAINTS_CYPHER, encoding="utf-8")
    neo4j_import_file.write_text(NEO4J_IMPORT_TEMPLATE, encoding="utf-8")
    return bundle["meta"]


def build_hybrid_graph_artifacts(
    graph_path: str | Path,
    output_dir: str | Path,
    title: str | None = None,
) -> dict:
    payload = json.loads(Path(graph_path).read_text(encoding="utf-8"))
    bundle = build_hierarchical_graph_bundle(payload, title=title)
    return write_hybrid_graph_artifacts(bundle, output_dir)


class HybridGraphStore:
    def __init__(self, bundle: dict) -> None:
        self.bundle = bundle
        self.nodes = {node["id"]: node for node in bundle["nodes"]}
        self.edges = bundle["edges"]
        self.case_cards = bundle.get("case_cards", {})
        self.outgoing: defaultdict[str, list[dict]] = defaultdict(list)
        self.incoming: defaultdict[str, list[dict]] = defaultdict(list)
        for edge in self.edges:
            self.outgoing[edge["source"]].append(edge)
            self.incoming[edge["target"]].append(edge)

    @classmethod
    def from_file(cls, path: str | Path) -> "HybridGraphStore":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def manifest(self) -> dict:
        return self.bundle["meta"]

    def tree_counts(self) -> dict:
        return self.bundle["tree"]

    def case_card(self, case_id: str) -> dict:
        card = self.case_cards.get(case_id)
        if card:
            return card
        node = self.nodes.get(case_id)
        if not node or node["type"] != "Case":
            raise KeyError(case_id)
        return {
            "id": case_id,
            "metadata": {
                "id": node["id"],
                "neutral_citation": node.get("neutral_citation", ""),
                "parallel_citations": node.get("parallel_citations", []),
                "case_name": node.get("case_name", node["label"]),
                "short_name": node.get("short_name", _short_case_name(node.get("case_name", node["label"]))),
                "court_code": node.get("court_code", ""),
                "court_name": node.get("court_name", ""),
                "court_level": node.get("court_level", ""),
                "decision_date": node.get("decision_date", ""),
                "judges": node.get("judges", []),
                "source_links": node.get("source_links", []),
                "summary_en": node.get("summary_en", ""),
                "summary_zh": node.get("summary_zh", ""),
                "authority_score": node.get("authority_score", 0.0),
                "topic_paths": node.get("topic_paths", []),
                "lineage_ids": node.get("lineage_ids", []),
                "enrichment_status": node.get("enrichment_status", "case_only"),
            },
            "principles": [],
            "relationships": [],
            "lineage_memberships": [],
            "derived_relationships": {
                "upstream_authorities": [],
                "downstream_applications": [],
                "same_lineage_cases": [],
                "statutory_interpretations": [],
            },
        }

    def focus_graph(self, node_id: str, depth: int = 1) -> dict:
        if node_id not in self.nodes:
            raise KeyError(node_id)
        bounded_depth = max(1, min(depth, 2))
        visited = {node_id}
        queue = deque([(node_id, 0)])
        while queue:
            current, current_depth = queue.popleft()
            if current_depth >= bounded_depth:
                continue
            neighbors = self.outgoing[current] + self.incoming[current]
            ranked_neighbors = sorted(
                neighbors,
                key=lambda edge: (
                    edge["type"] not in TREATMENT_EDGE_TYPES,
                    -float(edge.get("weight", 1.0)),
                    edge["target"],
                ),
            )
            limit = 18 if current_depth == 0 else 12
            for edge in ranked_neighbors[:limit]:
                other = edge["target"] if edge["source"] == current else edge["source"]
                if other in visited:
                    continue
                visited.add(other)
                queue.append((other, current_depth + 1))
        nodes = [self.nodes[visited_id] for visited_id in visited]
        node_set = {node["id"] for node in nodes}
        edges = [edge for edge in self.edges if edge["source"] in node_set and edge["target"] in node_set]
        facets = Counter(node["type"] for node in nodes)
        return {"focus": node_id, "nodes": nodes, "edges": edges, "facets": dict(facets)}

    def topic_detail(self, topic_id: str) -> dict:
        if topic_id not in self.nodes or self.nodes[topic_id]["type"] != "Topic":
            raise KeyError(topic_id)
        topic = self.nodes[topic_id]
        case_ids = [edge["source"] for edge in self.incoming[topic_id] if edge["type"] == "BELONGS_TO_TOPIC" and self.nodes[edge["source"]]["type"] == "Case"]
        lead_cases = sorted(
            (self.case_card(case_id) for case_id in case_ids),
            key=lambda card: (card["metadata"]["authority_score"], card["metadata"]["case_name"]),
            reverse=True,
        )[:8]
        lineages = []
        for edge in self.incoming[topic_id]:
            if edge["type"] != "ABOUT_TOPIC":
                continue
            lineage = self.nodes[edge["source"]]
            members = [
                {
                    "id": member_edge["target"],
                    "label": self.nodes[member_edge["target"]].get("label", self.nodes[member_edge["target"]].get("case_name", "")),
                    "type": self.nodes[member_edge["target"]]["type"],
                    "position": member_edge.get("position"),
                    "code": member_edge.get("code", ""),
                    "treatment": member_edge.get("treatment", ""),
                }
                for member_edge in self.outgoing[lineage["id"]]
                if member_edge["type"] == "HAS_MEMBER"
            ]
            lineages.append(
                {
                    "id": lineage["id"],
                    "title": lineage.get("title", lineage["label"]),
                    "codes": lineage.get("codes", []),
                    "members": sorted(members, key=lambda item: item["position"] or 0),
                }
            )
        return {
            "topic": topic,
            "lead_cases": lead_cases,
            "lineages": sorted(lineages, key=lambda item: item["title"]),
            "focus_graph": self.focus_graph(topic_id, depth=1),
        }

    def query(
        self,
        question: str,
        top_k: int = 5,
        mode: str = "extractive",
        model: str = "",
        max_citations: int = 8,
    ) -> dict:
        try:
            bounded_top_k = max(1, min(int(top_k), 10))
        except (TypeError, ValueError):
            bounded_top_k = 5
        try:
            bounded_max_citations = max(2, min(int(max_citations), 20))
        except (TypeError, ValueError):
            bounded_max_citations = 8
        requested_mode = (mode or "extractive").strip().lower()
        query_tokens = tokenize(question)
        if not query_tokens:
            return {
                "question": question.strip(),
                "answer": "No usable legal terms were found in the query.",
                "answer_mode": "extractive",
                "sources": [],
                "citations": [],
                "authority_path": [],
                "supporting_nodes": [],
                "retrieval_trace": {"query_tokens": [], "matched_node_ids": []},
                "warnings": [],
                "llm": {
                    "requested": requested_mode == "openrouter",
                    "used": False,
                    "provider": "openrouter",
                    "model": model.strip() or os.environ.get("OPENROUTER_MODEL", "").strip() or OPENROUTER_DEFAULT_MODEL,
                },
            }

        searchable: list[tuple[str, str, str]] = []
        for node in self.nodes.values():
            if node["type"] == "Case":
                searchable.append((node["id"], "Case", f"{node.get('case_name', '')} {node.get('summary_en', '')} {' '.join(node.get('topic_paths', []))}"))
            elif node["type"] == "Topic":
                searchable.append((node["id"], "Topic", f"{node.get('label_en', node.get('label', ''))} {node.get('summary', '')}"))
            elif node["type"] == "Proposition":
                searchable.append((node["id"], "Proposition", f"{node.get('label_en', '')} {node.get('statement_en', '')}"))

        lexical_scores: dict[str, float] = {}
        for node_id, kind, text in searchable:
            text_tokens = tokenize(text)
            if not text_tokens:
                lexical_scores[node_id] = 0.0
                continue
            overlap = len(set(query_tokens) & set(text_tokens))
            score = overlap / max(math.sqrt(len(set(text_tokens)) * len(set(query_tokens))), 1)
            if kind == "Proposition":
                score += 0.12
            lexical_scores[node_id] = score
        lexical_norm = normalize_scores(lexical_scores)
        best_node_ids = [
            node_id
            for node_id in sorted(lexical_norm, key=lexical_norm.get, reverse=True)
            if lexical_norm[node_id] > 0
        ][: max(bounded_top_k * 2, 8)]

        supporting_node_ids: set[str] = set(best_node_ids[:bounded_top_k])
        support_case_ids: set[str] = set()
        support_case_scores: defaultdict[str, float] = defaultdict(float)
        for node_id in best_node_ids[:6]:
            node = self.nodes[node_id]
            node_score = lexical_norm.get(node_id, 0.0)
            if node["type"] == "Case":
                support_case_ids.add(node_id)
                support_case_scores[node_id] += node_score
            elif node["type"] == "Proposition":
                for edge in self.incoming[node_id]:
                    if edge["type"] != "SUPPORTS":
                        continue
                    paragraph_id = edge["source"]
                    supporting_node_ids.add(paragraph_id)
                    for paragraph_edge in self.outgoing[paragraph_id]:
                        if paragraph_edge["type"] == "PART_OF":
                            support_case_ids.add(paragraph_edge["target"])
                            supporting_node_ids.add(paragraph_edge["target"])
                            support_case_scores[paragraph_edge["target"]] += node_score + 0.22
            elif node["type"] == "Topic":
                for edge in self.incoming[node_id]:
                    if edge["type"] == "BELONGS_TO_TOPIC" and self.nodes[edge["source"]]["type"] == "Case":
                        support_case_ids.add(edge["source"])
                        supporting_node_ids.add(edge["source"])
                        support_case_scores[edge["source"]] += node_score * 0.75
            for edge in self.outgoing[node_id][:8] + self.incoming[node_id][:8]:
                supporting_node_ids.add(edge["source"])
                supporting_node_ids.add(edge["target"])
                if self.nodes.get(edge["source"], {}).get("type") == "Case":
                    support_case_ids.add(edge["source"])
                    support_case_scores[edge["source"]] += node_score * 0.15
                if self.nodes.get(edge["target"], {}).get("type") == "Case":
                    support_case_ids.add(edge["target"])
                    support_case_scores[edge["target"]] += node_score * 0.15

        support_cases = [
            self.case_card(case_id)
            for case_id in support_case_ids
            if case_id in self.nodes and self.nodes[case_id]["type"] == "Case"
        ]
        support_cases = sorted(
            support_cases,
            key=lambda card: (
                support_case_scores.get(card["id"], 0.0),
                len(card["principles"]),
                card["metadata"]["authority_score"],
                lexical_norm.get(card["id"], 0.0),
            ),
            reverse=True,
        )[:bounded_top_k]

        citation_pool: list[dict] = []
        for card in support_cases:
            case_score = support_case_scores.get(card["id"], 0.0)
            lineage_titles = sorted({entry["lineage_title"] for entry in card.get("lineage_memberships", []) if entry.get("lineage_title")})
            principles = card.get("principles", [])
            if principles:
                for position, principle in enumerate(principles[:3], start=1):
                    quote = (principle.get("statement_en") or principle.get("public_excerpt") or "").strip()
                    if not quote:
                        continue
                    citation_pool.append(
                        {
                            "case_id": card["id"],
                            "focus_node_id": card["id"],
                            "case_name": card["metadata"]["case_name"],
                            "neutral_citation": card["metadata"]["neutral_citation"],
                            "paragraph_span": principle.get("paragraph_span", ""),
                            "principle_label": principle.get("label_en", ""),
                            "quote": quote,
                            "lineage_titles": lineage_titles,
                            "support_score": round(case_score + (0.06 / position), 6),
                        }
                    )
            else:
                summary = (card["metadata"].get("summary_en") or "").strip()
                if summary:
                    citation_pool.append(
                        {
                            "case_id": card["id"],
                            "focus_node_id": card["id"],
                            "case_name": card["metadata"]["case_name"],
                            "neutral_citation": card["metadata"]["neutral_citation"],
                            "paragraph_span": "",
                            "principle_label": "",
                            "quote": summary,
                            "lineage_titles": lineage_titles,
                            "support_score": round(case_score, 6),
                        }
                    )

        citations = sorted(
            citation_pool,
            key=lambda item: (item["support_score"], len(item["quote"]), item["case_name"]),
            reverse=True,
        )[:bounded_max_citations]
        for index, citation in enumerate(citations, start=1):
            citation["citation_id"] = f"C{index}"

        if citations:
            extractive_answer = " ".join(
                f"[{citation['citation_id']}] {citation['quote']}"
                for citation in citations[: min(3, len(citations))]
            ).strip()
        elif support_cases:
            extractive_answer = " ".join(
                card["metadata"]["summary_en"]
                for card in support_cases[:2]
                if card["metadata"]["summary_en"] and not card["metadata"]["summary_en"].startswith("Case linked to")
            ).strip() or "No paragraph-level evidence was found for this query, but related cases were retrieved."
        else:
            extractive_answer = "No sufficiently relevant authority path was found in the current graph bundle."

        answer_mode = "extractive"
        resolved_model = model.strip() or os.environ.get("OPENROUTER_MODEL", "").strip() or OPENROUTER_DEFAULT_MODEL
        warnings: list[str] = []
        answer = extractive_answer
        if requested_mode == "openrouter":
            try:
                answer, resolved_model = _openrouter_grounded_answer(question, citations, model=model)
                answer_mode = "openrouter_grounded"
            except Exception as exc:  # pragma: no cover - exercised only when OpenRouter mode is requested.
                warnings.append(f"OpenRouter synthesis skipped: {exc}")

        authority_path = []
        for card in support_cases:
            if card["lineage_memberships"]:
                first_lineage = card["lineage_memberships"][0]
                authority_path.append(
                    {
                        "lineage_id": first_lineage["lineage_id"],
                        "lineage_title": first_lineage["lineage_title"],
                        "case_id": card["id"],
                        "case_name": card["metadata"]["case_name"],
                        "position": first_lineage.get("position"),
                    }
                )
        if not authority_path and support_cases:
            top_case = support_cases[0]
            authority_path = [
                {
                    "lineage_id": "",
                    "lineage_title": "Derived authority neighborhood",
                    "case_id": top_case["id"],
                    "case_name": top_case["metadata"]["case_name"],
                    "position": None,
                }
            ]

        sources = []
        seen_cases: set[str] = set()
        for citation in citations:
            case_id = citation["case_id"]
            if case_id in seen_cases:
                continue
            seen_cases.add(case_id)
            card = next((entry for entry in support_cases if entry["id"] == case_id), None)
            sources.append(
                {
                    "case_id": case_id,
                    "case_name": citation["case_name"],
                    "neutral_citation": citation["neutral_citation"],
                    "paragraph_span": citation["paragraph_span"],
                    "text": citation["quote"],
                    "links": card["metadata"]["source_links"] if card else [],
                    "citation_ids": [entry["citation_id"] for entry in citations if entry["case_id"] == case_id],
                }
            )

        return {
            "question": question.strip(),
            "answer": answer.strip(),
            "answer_mode": answer_mode,
            "sources": sources,
            "citations": citations,
            "authority_path": authority_path,
            "supporting_nodes": [
                {
                    "id": node_id,
                    "type": self.nodes[node_id]["type"],
                    "label": self.nodes[node_id].get("label", self.nodes[node_id].get("case_name", "")),
                }
                for node_id in sorted(supporting_node_ids)
                if node_id in self.nodes
            ][:25],
            "retrieval_trace": {
                "query_tokens": query_tokens[:24],
                "matched_node_ids": best_node_ids[:12],
                "top_case_scores": [
                    {
                        "case_id": card["id"],
                        "case_name": card["metadata"]["case_name"],
                        "support_score": round(support_case_scores.get(card["id"], 0.0), 6),
                    }
                    for card in support_cases
                ],
            },
            "warnings": warnings,
            "llm": {
                "requested": requested_mode == "openrouter",
                "used": answer_mode == "openrouter_grounded",
                "provider": "openrouter",
                "model": resolved_model,
            },
        }
