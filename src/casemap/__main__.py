from __future__ import annotations

import argparse
import json

from .graphrag import RerankedRetriever, build_artifacts
from .relationship_graph import build_relationship_artifacts, export_public_relationship_artifacts


def build_command(args: argparse.Namespace) -> int:
    manifest = build_artifacts(docx_path=args.input, output_dir=args.output_dir)
    print(json.dumps(manifest, indent=2))
    return 0


def query_command(args: argparse.Namespace) -> int:
    retriever = RerankedRetriever.from_files(args.graph, args.chunks)
    results = retriever.search(args.question, top_k=args.top_k)
    if args.as_json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0

    for result in results:
        print(f"[{result['rank']}] {result['title']} | {result['section']} | score={result['score']}")
        print(result["text"])
        if result["citations"]:
            print("Citations:", "; ".join(result["citations"]))
        if result["graph_neighbors"]:
            print("Graph neighbors:", "; ".join(result["graph_neighbors"]))
        print()
    return 0


def build_relationships_command(args: argparse.Namespace) -> int:
    manifest = build_relationship_artifacts(
        taxonomy_docx_path=args.taxonomy,
        source_paths=args.source,
        output_dir=args.output_dir,
        title=args.title,
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


def export_public_relationships_command(args: argparse.Namespace) -> int:
    manifest = export_public_relationship_artifacts(
        graph_path=args.graph,
        output_dir=args.output_dir,
        title=args.title,
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


def parser() -> argparse.ArgumentParser:
    main_parser = argparse.ArgumentParser(description="Casemap MVP GraphRAG pipeline")
    subparsers = main_parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build graph and retrieval artifacts")
    build_parser.add_argument("--input", required=True, help="Path to the source .docx file")
    build_parser.add_argument("--output-dir", required=True, help="Directory for generated artifacts")
    build_parser.set_defaults(func=build_command)

    query_parser = subparsers.add_parser("query", help="Run reranked retrieval over built artifacts")
    query_parser.add_argument("--graph", required=True, help="Path to graph.json")
    query_parser.add_argument("--chunks", required=True, help="Path to chunks.json")
    query_parser.add_argument("--question", required=True, help="Question to search for")
    query_parser.add_argument("--top-k", type=int, default=5, help="Number of results to return")
    query_parser.add_argument("--json", action="store_true", dest="as_json", help="Print JSON output")
    query_parser.set_defaults(func=query_command)

    relationship_parser = subparsers.add_parser(
        "build-relationships",
        help="Build a richer multi-source relationship graph from a taxonomy docx and supporting sources",
    )
    relationship_parser.add_argument("--taxonomy", required=True, help="Primary taxonomy .docx path")
    relationship_parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="Supplemental source path. Repeat for each .pdf or .docx source.",
    )
    relationship_parser.add_argument("--output-dir", required=True, help="Directory for generated artifacts")
    relationship_parser.add_argument(
        "--title",
        default="Hong Kong Contract Law Relationship Graph",
        help="Display title for the generated graph",
    )
    relationship_parser.set_defaults(func=build_relationships_command)

    public_relationship_parser = subparsers.add_parser(
        "export-public-relationships",
        help="Create a public-safe relationship graph artifact from a richer local graph",
    )
    public_relationship_parser.add_argument("--graph", required=True, help="Path to relationship_graph.json")
    public_relationship_parser.add_argument("--output-dir", required=True, help="Directory for generated artifacts")
    public_relationship_parser.add_argument(
        "--title",
        default="Hong Kong Contract Law Public Relationship Graph",
        help="Display title for the generated graph",
    )
    public_relationship_parser.set_defaults(func=export_public_relationships_command)

    return main_parser


def main() -> int:
    args = parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
