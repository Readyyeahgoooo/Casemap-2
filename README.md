# Casemap-

Casemap- is a dependency-light MVP for turning Hong Kong contract-law materials into a legal GraphRAG knowledge map. It supports:

- a document-level GraphRAG build from `Contract big .docx`
- a richer multi-source relationship graph that combines `Contract big .docx` with local `.pdf` textbooks
- a Vercel-ready read-only viewer for the committed sample artifact

## What It Produces

- `graph.json`: knowledge graph nodes and edges
- `chunks.json`: retrieval chunks with lexical and graph metadata
- `manifest.json`: build summary
- `sample_queries.json`: example reranked retrieval output
- `knowledge_map.html`: interactive local viewer

The repository also includes a Vercel-ready `app.py` WSGI entrypoint. When deployed, it serves the knowledge map at `/` and lightweight JSON endpoints such as `/api/manifest`, `/api/sample-queries`, and `/api/query?q=...`.

## Quick Start

```bash
cd /Users/puiyuenwong/PolymarketCorrelationStrategy/Casemap-
PYTHONPATH=src python3 -m casemap build \
  --input "/Users/puiyuenwong/Desktop/桌面 - Pui的MacBook Air/Real uni (1)/PCLL 2023 /Haldanes demo try /Album /Contract big .docx" \
  --output-dir artifacts/contract_big
```

Open `artifacts/contract_big/knowledge_map.html` in a browser.

Run a reranked query:

```bash
cd /Users/puiyuenwong/PolymarketCorrelationStrategy/Casemap-
PYTHONPATH=src python3 -m casemap query \
  --graph artifacts/contract_big/graph.json \
  --chunks artifacts/contract_big/chunks.json \
  --question "When can a third party enforce a contract term?" \
  --top-k 5
```

Build the richer relationship graph from a taxonomy docx plus supporting books:

```bash
cd /Users/puiyuenwong/PolymarketCorrelationStrategy/Casemap-
PYTHONPATH=src .venv/bin/python -m casemap build-relationships \
  --taxonomy "/absolute/path/to/Contract big .docx" \
  --source "/absolute/path/to/Butterworths Hong Kong Contract Law Handbook.pdf" \
  --source "/absolute/path/to/Contract Law in Hong Kong.pdf" \
  --source "/absolute/path/to/Ho  Halls Hong Kong Contract Law.pdf" \
  --output-dir artifacts/hk_contract_relationship
```

Open `artifacts/hk_contract_relationship/relationship_map.html` in a browser.

## Design

The project stays light on dependencies:

- `.docx` parsing uses the Office XML inside the archive
- `.pdf` parsing uses `pypdf`
- graph building uses heuristics over headings, concept labels, statutes, and case references
- retrieval uses a TF-IDF style lexical score
- reranking boosts graph neighbors, cited authorities, and structurally central nodes
- the relationship graph attaches source passages, page references, and HKLII-oriented external links
- both viewers are static HTML files with inline data and client-side interactions

## Vercel Deployment

Vercel's Python runtime requires a top-level ASGI or WSGI application named `app` in files such as `app.py`. This repo ships a root `app.py` that:

- serves the built map at `/`
- exposes `GET /api/manifest`
- exposes `GET /api/sample-queries`
- exposes `GET /api/query?q=third+party+rights&top_k=5`

The committed sample artifacts under `artifacts/contract_big/` let Vercel serve the MVP without access to the original `.docx` file.

## Local-Only Sources

If you enrich the graph with third-party textbooks or other licensed material, keep the generated artifacts local unless you have clear rights to publish them. The repository is set up so the committed public artifact remains the `Contract big` sample, while book-derived outputs can stay untracked under `artifacts/`.

## Project Layout

```text
Casemap-/
  src/casemap/
    __init__.py
    __main__.py
    docx_parser.py
    graphrag.py
    relationship_graph.py
    source_parser.py
    viewer.py
  artifacts/
  pyproject.toml
  README.md
```

## Next Step Ideas

- Replace heuristic extraction with LLM-assisted triplet/entity extraction
- Persist the graph in Neo4j, Oracle Database, or another graph-capable backend
- Add embeddings and a cross-encoder reranker
- Layer in answer generation once your cloud backend is ready
