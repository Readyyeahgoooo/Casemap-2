from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote_plus
import json
import math
import re

from .docx_parser import extract_paragraphs
from .graphrag import (
    CASE_RE,
    STATUTE_RE,
    extract_authorities,
    parse_sections,
    slugify,
    split_topic,
    tokenize,
    top_keywords,
)
from .source_parser import Passage, SourceDocument, load_source_document
from .viewer import render_relationship_map

CASE_SEARCH_TEMPLATE = 'https://www.google.com/search?q={query}'
CASE_NAME_CONNECTORS = {
    "&",
    "and",
    "co",
    "co.",
    "company",
    "contractors",
    "corp",
    "corporation",
    "de",
    "east",
    "far",
    "for",
    "ltd",
    "ltd.",
    "mbh",
    "nicholls",
    "of",
    "plc",
    "pty",
    "sa",
    "stahl",
    "stahag",
    "the",
    "und",
    "van",
    "von",
}


@dataclass
class TopicProfile:
    topic_id: str
    label: str
    domain_id: str
    domain_label: str
    summary: str
    token_set: set[str]


def _normalize_case_name(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value).strip(" ,.;:")
    normalized = re.sub(r"\s+\(\d{4}\)$", "", normalized)
    tokens = normalized.split()
    v_index = next((index for index, token in enumerate(tokens) if token.lower().rstrip(".") == "v"), None)
    if v_index is None:
        return normalized

    def is_name_token(token: str) -> bool:
        cleaned = token.strip(" ,.;:()[]")
        if not cleaned:
            return False
        if cleaned.lower() in CASE_NAME_CONNECTORS:
            return True
        return bool(re.match(r"^[A-Z][A-Za-z0-9'&.\-]*$", cleaned))

    left: list[str] = []
    cursor = v_index - 1
    while cursor >= 0 and is_name_token(tokens[cursor]):
        left.append(tokens[cursor].strip(" ,.;:()[]"))
        cursor -= 1
    left.reverse()

    right: list[str] = []
    cursor = v_index + 1
    while cursor < len(tokens) and is_name_token(tokens[cursor]):
        right.append(tokens[cursor].strip(" ,.;:()[]"))
        cursor += 1

    if not left or not right:
        return normalized
    return " ".join(left + ["v"] + right).strip()


def _normalize_statute_name(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value).strip(" ,.;:")
    normalized = re.sub(r"^(Under|under|Pursuant to|pursuant to)\s+", "", normalized)
    normalized = re.sub(r"^(The|the)\s+", "", normalized)
    return normalized


def _sentence_split(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def _make_snippet(text: str, anchors: list[str], max_chars: int = 420) -> str:
    lowered = text.lower()
    for anchor in anchors:
        if not anchor:
            continue
        position = lowered.find(anchor.lower())
        if position == -1:
            continue
        start = max(position - (max_chars // 3), 0)
        end = min(start + max_chars, len(text))
        snippet = text[start:end].strip()
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        return snippet
    compact = re.sub(r"\s+", " ", text).strip()
    return compact[: max_chars - 3] + "..." if len(compact) > max_chars else compact


def _build_taxonomy(taxonomy_docx_path: str | Path) -> tuple[list[dict], list[TopicProfile]]:
    paragraphs = extract_paragraphs(taxonomy_docx_path)
    sections = parse_sections(paragraphs)
    domains: list[dict] = []
    topics: list[TopicProfile] = []
    seen_domains: set[str] = set()

    for section in sections:
        if section.number < 1 or section.number > 11:
            continue
        domain_id = f"domain:{slugify(section.title)}"
        if domain_id in seen_domains:
            continue
        seen_domains.add(domain_id)
        section_summary = " ".join(section.paragraphs[:2]).strip()
        domains.append(
            {
                "id": domain_id,
                "label": section.title,
                "type": "domain",
                "summary": section_summary or section.title,
                "keywords": top_keywords(section.title + " " + section_summary),
            }
        )

        seen_topic_labels: set[str] = set()
        for index, paragraph in enumerate(section.paragraphs, start=1):
            title, body = split_topic(paragraph)
            cleaned_title = re.sub(r"\s+", " ", title).strip(" ,.;:")
            if cleaned_title.lower() in seen_topic_labels:
                continue
            if CASE_RE.search(cleaned_title) or STATUTE_RE.search(cleaned_title):
                continue
            if len(tokenize(cleaned_title)) < 1:
                continue
            seen_topic_labels.add(cleaned_title.lower())

            summary = body or paragraph
            token_set = set(tokenize(cleaned_title + " " + section.title + " " + summary))
            topics.append(
                TopicProfile(
                    topic_id=f"topic:{slugify(section.title)}:{index:02d}:{slugify(cleaned_title)[:36]}",
                    label=cleaned_title,
                    domain_id=domain_id,
                    domain_label=section.title,
                    summary=summary[:500],
                    token_set=token_set,
                )
            )
    return domains, topics


def _topic_scores(text: str, topics: list[TopicProfile]) -> list[tuple[TopicProfile, float]]:
    token_set = set(tokenize(text))
    if not token_set:
        return []

    scored: list[tuple[TopicProfile, float]] = []
    lowered = text.lower()
    for topic in topics:
        overlap = token_set & topic.token_set
        lexical = len(overlap) / max(math.sqrt(len(token_set) * len(topic.token_set)), 1)
        if topic.label.lower() in lowered:
            lexical += 0.85
        if topic.domain_label.lower() in lowered:
            lexical += 0.18
        if lexical >= 0.12:
            scored.append((topic, lexical))
    return sorted(scored, key=lambda item: item[1], reverse=True)[:3]


def _select_references(references: list[dict], limit: int = 6) -> list[dict]:
    selected: list[dict] = []
    seen_sources: set[tuple[str, str]] = set()
    for reference in sorted(references, key=lambda item: item["score"], reverse=True):
        key = (reference["source_id"], reference["location"])
        if key in seen_sources:
            continue
        payload = dict(reference)
        payload.pop("score", None)
        selected.append(payload)
        seen_sources.add(key)
        if len(selected) >= limit:
            break
    return selected


def _summarize_authority(name: str, references: list[dict], fallback: str) -> str:
    candidates: list[str] = []
    ranked = sorted(
        references,
        key=lambda item: (item["score"], len(item["snippet"])),
        reverse=True,
    )
    for reference in ranked:
        for sentence in _sentence_split(reference["snippet"]):
            cleaned = sentence.strip()
            if len(cleaned) < 55:
                continue
            if cleaned.count(";") >= 2:
                continue
            if name.lower() in sentence.lower() or any(
                marker in sentence.lower()
                for marker in ("held", "held that", "principle", "applies", "means", "effective", "requires")
            ):
                candidates.append(cleaned)
        if len(candidates) >= 3:
            break

    if not candidates:
        return fallback

    unique_sentences: list[str] = []
    seen: set[str] = set()
    for sentence in candidates:
        normalized = sentence.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        unique_sentences.append(sentence)
        if len(unique_sentences) >= 2:
            break
    summary = " ".join(unique_sentences).strip()
    return summary[:560] + "..." if len(summary) > 560 else summary


def _case_links(case_name: str) -> list[dict]:
    query = quote_plus(f'site:hklii.hk "{case_name}"')
    return [
        {
            "label": "Find on HKLII",
            "url": CASE_SEARCH_TEMPLATE.format(query=query),
        }
    ]


def _statute_links(statute_name: str) -> list[dict]:
    match = re.search(r"Cap\. (\d+[A-Z]?)", statute_name)
    if not match:
        return []
    cap_number = match.group(1).lower()
    return [
        {
            "label": "HKLII legislation",
            "url": f"https://hklii.hk/en/legis/ord/{cap_number}",
        }
    ]


def build_relationship_artifacts(
    taxonomy_docx_path: str | Path,
    source_paths: list[str | Path],
    output_dir: str | Path,
    title: str = "Hong Kong Contract Law Relationship Graph",
) -> dict:
    output_path = Path(output_dir).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    domains, topics = _build_taxonomy(taxonomy_docx_path)
    domain_lookup = {domain["id"]: domain for domain in domains}

    sources: list[SourceDocument] = []
    passages: list[Passage] = []
    loaded_source_ids: set[str] = set()

    for path in [taxonomy_docx_path, *source_paths]:
        source, source_passages = load_source_document(path)
        if source.source_id in loaded_source_ids:
            continue
        loaded_source_ids.add(source.source_id)
        sources.append(source)
        passages.extend(source_passages)

    nodes: list[dict] = []
    node_ids: set[str] = set()
    edges_counter: Counter[tuple[str, str, str]] = Counter()
    edge_weights: defaultdict[tuple[str, str, str], float] = defaultdict(float)

    def add_node(node: dict) -> None:
        if node["id"] in node_ids:
            return
        node_ids.add(node["id"])
        nodes.append(node)

    for source in sources:
        add_node(
            {
                "id": source.source_id,
                "label": source.label,
                "type": "source",
                "summary": f"{source.kind.upper()} source document used to enrich the Hong Kong contract-law graph.",
                "references": [],
                "links": [],
                "metrics": {"kind": source.kind},
            }
        )

    for domain in domains:
        add_node(
            {
                "id": domain["id"],
                "label": domain["label"],
                "type": "domain",
                "summary": domain["summary"],
                "references": [],
                "links": [],
                "metrics": {},
                "keywords": domain["keywords"],
            }
        )

    topic_lookup: dict[str, TopicProfile] = {}
    for topic in topics:
        topic_lookup[topic.topic_id] = topic
        add_node(
            {
                "id": topic.topic_id,
                "label": topic.label,
                "type": "topic",
                "summary": topic.summary,
                "references": [],
                "links": [],
                "metrics": {},
                "domain_id": topic.domain_id,
                "keywords": top_keywords(topic.label + " " + topic.summary),
            }
        )
        edges_counter[(topic.domain_id, topic.topic_id, "contains")] += 1
        edge_weights[(topic.domain_id, topic.topic_id, "contains")] += 1.0

    source_topic_counts: Counter[tuple[str, str]] = Counter()
    source_case_counts: Counter[tuple[str, str]] = Counter()
    source_statute_counts: Counter[tuple[str, str]] = Counter()
    topic_case_counts: Counter[tuple[str, str]] = Counter()
    topic_statute_counts: Counter[tuple[str, str]] = Counter()
    domain_case_counts: Counter[tuple[str, str]] = Counter()
    domain_statute_counts: Counter[tuple[str, str]] = Counter()
    case_statute_counts: Counter[tuple[str, str]] = Counter()
    case_case_counts: Counter[tuple[str, str]] = Counter()

    domain_references: defaultdict[str, list[dict]] = defaultdict(list)
    topic_references: defaultdict[str, list[dict]] = defaultdict(list)
    case_references: defaultdict[str, list[dict]] = defaultdict(list)
    statute_references: defaultdict[str, list[dict]] = defaultdict(list)

    for passage in passages:
        assigned_topics = _topic_scores(passage.text, topics)
        assigned_domains = {topic.domain_id for topic, _ in assigned_topics}
        authorities = extract_authorities(passage.text)
        cases = sorted({_normalize_case_name(case) for case in authorities["cases"]})
        statutes = sorted({_normalize_statute_name(statute) for statute in authorities["statutes"]})

        for topic, score in assigned_topics:
            source_topic_counts[(passage.source_id, topic.topic_id)] += 1
            topic_references[topic.topic_id].append(
                {
                    "source_id": passage.source_id,
                    "source_label": passage.source_label,
                    "source_kind": passage.source_kind,
                    "location": passage.location,
                    "snippet": _make_snippet(passage.text, [topic.label, topic.domain_label]),
                    "score": score + min(len(passage.text), 700) / 1400,
                }
            )

        for domain_id in assigned_domains:
            domain_references[domain_id].append(
                {
                    "source_id": passage.source_id,
                    "source_label": passage.source_label,
                    "source_kind": passage.source_kind,
                    "location": passage.location,
                    "snippet": _make_snippet(passage.text, [domain_lookup[domain_id]["label"]]),
                    "score": 0.3 + min(len(passage.text), 700) / 2000,
                }
            )

        for case_name in cases:
            source_case_counts[(passage.source_id, case_name)] += 1
            reference = {
                "source_id": passage.source_id,
                "source_label": passage.source_label,
                "source_kind": passage.source_kind,
                "location": passage.location,
                "snippet": _make_snippet(passage.text, [case_name]),
                "score": 1.0 + (0.05 if passage.source_kind == "docx" else 0.0) + min(len(passage.text), 700) / 900,
            }
            case_references[case_name].append(reference)
            for topic, score in assigned_topics:
                topic_case_counts[(topic.topic_id, case_name)] += 1
                edge_weights[(topic.topic_id, f"case:{slugify(case_name)[:64]}", "explains_case")] += score
            for domain_id in assigned_domains:
                domain_case_counts[(domain_id, case_name)] += 1

        for statute_name in statutes:
            source_statute_counts[(passage.source_id, statute_name)] += 1
            reference = {
                "source_id": passage.source_id,
                "source_label": passage.source_label,
                "source_kind": passage.source_kind,
                "location": passage.location,
                "snippet": _make_snippet(passage.text, [statute_name]),
                "score": 1.0 + (0.05 if passage.source_kind == "docx" else 0.0) + min(len(passage.text), 700) / 900,
            }
            statute_references[statute_name].append(reference)
            for topic, score in assigned_topics:
                topic_statute_counts[(topic.topic_id, statute_name)] += 1
                edge_weights[(topic.topic_id, f"statute:{slugify(statute_name)[:64]}", "cites_statute")] += score
            for domain_id in assigned_domains:
                domain_statute_counts[(domain_id, statute_name)] += 1

        for case_name in cases:
            for statute_name in statutes:
                pair = (case_name, statute_name)
                case_statute_counts[pair] += 1

        for left_index, left_case in enumerate(cases):
            for right_case in cases[left_index + 1 :]:
                pair = tuple(sorted((left_case, right_case)))
                case_case_counts[pair] += 1

    case_priority: list[tuple[str, int, int, int]] = []
    for case_name, references in case_references.items():
        mention_count = len(references)
        source_count = len({reference["source_id"] for reference in references})
        topic_count = sum(1 for (_, case_key), count in topic_case_counts.items() if case_key == case_name and count)
        priority = (source_count * 4) + mention_count + topic_count
        case_priority.append((case_name, priority, mention_count, source_count))

    keep_cases = {
        case_name
        for case_name, _, mention_count, source_count in sorted(
        case_priority, key=lambda item: (item[1], item[2], item[3], item[0]), reverse=True
        )
        if mention_count >= 3 or source_count >= 2 or any(
            reference["source_kind"] == "docx" for reference in case_references[case_name]
        )
    }

    statute_priority: list[tuple[str, int, int, int]] = []
    for statute_name, references in statute_references.items():
        mention_count = len(references)
        source_count = len({reference["source_id"] for reference in references})
        topic_count = sum(
            1 for (_, statute_key), count in topic_statute_counts.items() if statute_key == statute_name and count
        )
        priority = (source_count * 4) + mention_count + topic_count
        statute_priority.append((statute_name, priority, mention_count, source_count))

    keep_statutes = {
        statute_name
        for statute_name, _, mention_count, source_count in sorted(
            statute_priority, key=lambda item: (item[1], item[2], item[3], item[0]), reverse=True
        )
        if mention_count >= 2 or source_count >= 2 or any(
            reference["source_id"] == sources[0].source_id for reference in statute_references[statute_name]
        )
    }

    for case_name in sorted(keep_cases):
        node_id = f"case:{slugify(case_name)[:64]}"
        references = case_references[case_name]
        mention_count = len(references)
        source_count = len({reference["source_id"] for reference in references})
        add_node(
            {
                "id": node_id,
                "label": case_name,
                "type": "case",
                "summary": _summarize_authority(
                    case_name,
                    references,
                    fallback=f"Case authority mentioned across {source_count} source(s) and {mention_count} relevant passage(s).",
                ),
                "references": _select_references(references),
                "links": _case_links(case_name),
                "metrics": {"mentions": mention_count, "sources": source_count},
            }
        )

    for statute_name in sorted(keep_statutes):
        node_id = f"statute:{slugify(statute_name)[:64]}"
        references = statute_references[statute_name]
        mention_count = len(references)
        source_count = len({reference["source_id"] for reference in references})
        add_node(
            {
                "id": node_id,
                "label": statute_name,
                "type": "statute",
                "summary": _summarize_authority(
                    statute_name,
                    references,
                    fallback=f"Statutory authority mentioned across {source_count} source(s) and {mention_count} relevant passage(s).",
                ),
                "references": _select_references(references),
                "links": _statute_links(statute_name),
                "metrics": {"mentions": mention_count, "sources": source_count},
            }
        )

    node_lookup = {node["id"]: node for node in nodes}

    for (source_id, topic_id), count in source_topic_counts.items():
        if topic_id in node_lookup:
            edges_counter[(source_id, topic_id, "covers_topic")] += count
            edge_weights[(source_id, topic_id, "covers_topic")] += count

    for (source_id, case_name), count in source_case_counts.items():
        case_id = f"case:{slugify(case_name)[:64]}"
        if case_name not in keep_cases or case_id not in node_lookup:
            continue
        edges_counter[(source_id, case_id, "discusses_case")] += count
        edge_weights[(source_id, case_id, "discusses_case")] += count

    for (source_id, statute_name), count in source_statute_counts.items():
        statute_id = f"statute:{slugify(statute_name)[:64]}"
        if statute_name not in keep_statutes or statute_id not in node_lookup:
            continue
        edges_counter[(source_id, statute_id, "discusses_statute")] += count
        edge_weights[(source_id, statute_id, "discusses_statute")] += count

    for (topic_id, case_name), count in topic_case_counts.items():
        case_id = f"case:{slugify(case_name)[:64]}"
        if case_name not in keep_cases or topic_id not in node_lookup or case_id not in node_lookup:
            continue
        edges_counter[(topic_id, case_id, "explains_case")] += count

    for (topic_id, statute_name), count in topic_statute_counts.items():
        statute_id = f"statute:{slugify(statute_name)[:64]}"
        if statute_name not in keep_statutes or topic_id not in node_lookup or statute_id not in node_lookup:
            continue
        edges_counter[(topic_id, statute_id, "cites_statute")] += count

    for (domain_id, case_name), count in domain_case_counts.items():
        case_id = f"case:{slugify(case_name)[:64]}"
        if case_name not in keep_cases or case_id not in node_lookup or domain_id not in node_lookup:
            continue
        edges_counter[(domain_id, case_id, "domain_case")] += count
        edge_weights[(domain_id, case_id, "domain_case")] += count

    for (domain_id, statute_name), count in domain_statute_counts.items():
        statute_id = f"statute:{slugify(statute_name)[:64]}"
        if statute_name not in keep_statutes or statute_id not in node_lookup or domain_id not in node_lookup:
            continue
        edges_counter[(domain_id, statute_id, "domain_statute")] += count
        edge_weights[(domain_id, statute_id, "domain_statute")] += count

    for (left_name, right_name), count in case_statute_counts.items():
        case_name, statute_name = left_name, right_name
        case_id = f"case:{slugify(case_name)[:64]}"
        statute_id = f"statute:{slugify(statute_name)[:64]}"
        if case_name not in keep_cases or statute_name not in keep_statutes:
            continue
        if case_id not in node_lookup or statute_id not in node_lookup:
            continue
        edges_counter[(case_id, statute_id, "co_mentioned")] += count
        edge_weights[(case_id, statute_id, "co_mentioned")] += count

    for (left_case, right_case), count in case_case_counts.items():
        left_id = f"case:{slugify(left_case)[:64]}"
        right_id = f"case:{slugify(right_case)[:64]}"
        if left_case not in keep_cases or right_case not in keep_cases:
            continue
        if left_id not in node_lookup or right_id not in node_lookup or count < 2:
            continue
        edges_counter[(left_id, right_id, "co_discussed")] += count
        edge_weights[(left_id, right_id, "co_discussed")] += count

    edges: list[dict] = []
    adjacency: defaultdict[str, set[str]] = defaultdict(set)
    for (source_id, target_id, edge_type), count in edges_counter.items():
        if source_id not in node_lookup or target_id not in node_lookup:
            continue
        weight = round(edge_weights[(source_id, target_id, edge_type)], 3)
        edge = {
            "source": source_id,
            "target": target_id,
            "type": edge_type,
            "weight": weight,
            "mentions": int(count),
        }
        edges.append(edge)
        adjacency[source_id].add(target_id)
        adjacency[target_id].add(source_id)

    for node in nodes:
        neighbors = sorted(adjacency.get(node["id"], set()))
        node["neighbors"] = neighbors
        node["degree"] = len(neighbors)
        if node["type"] == "domain":
            node["references"] = _select_references(domain_references[node["id"]])
        if node["type"] == "topic":
            node["references"] = _select_references(topic_references[node["id"]])

    payload = {
        "meta": {
            "title": title,
            "generated_at": datetime.now(UTC).isoformat(),
            "taxonomy_document": str(Path(taxonomy_docx_path).expanduser().resolve()),
            "source_documents": [
                {"label": source.label, "path": source.path, "kind": source.kind} for source in sources
            ],
            "source_count": len(sources),
            "passage_count": len(passages),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "retained_case_count": len(keep_cases),
            "retained_statute_count": len(keep_statutes),
        },
        "nodes": nodes,
        "edges": edges,
    }

    graph_file = output_path / "relationship_graph.json"
    viewer_file = output_path / "relationship_map.html"
    manifest_file = output_path / "manifest.json"

    graph_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    viewer_file.write_text(render_relationship_map(payload), encoding="utf-8")
    manifest_file.write_text(json.dumps(payload["meta"], indent=2, ensure_ascii=False), encoding="utf-8")
    return payload["meta"]
