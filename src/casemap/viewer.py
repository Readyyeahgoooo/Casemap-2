from __future__ import annotations

import json


def render_knowledge_map(graph_payload: dict) -> str:
    data = json.dumps(graph_payload, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Casemap Knowledge Map</title>
  <style>
    :root {{
      --bg: #f4efe3;
      --panel: #fffaf0;
      --ink: #1c1d21;
      --muted: #6d6658;
      --line: rgba(28, 29, 33, 0.18);
      --section: #205072;
      --concept: #f4b942;
      --statute: #d95d39;
      --case: #5f7c4f;
      --accent: #7c2d12;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      font-family: "Georgia", "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(244, 185, 66, 0.22), transparent 32%),
        radial-gradient(circle at top right, rgba(32, 80, 114, 0.18), transparent 28%),
        linear-gradient(180deg, #f7f1e5 0%, var(--bg) 100%);
      min-height: 100vh;
    }}

    .shell {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 360px;
      min-height: 100vh;
    }}

    .canvas-panel {{
      padding: 28px;
    }}

    .header {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: end;
      margin-bottom: 18px;
    }}

    h1 {{
      margin: 0;
      font-size: clamp(30px, 4vw, 44px);
      line-height: 0.95;
      letter-spacing: -0.03em;
    }}

    .subtitle {{
      max-width: 720px;
      color: var(--muted);
      font-size: 15px;
      line-height: 1.5;
    }}

    .search {{
      display: grid;
      gap: 8px;
      align-self: start;
    }}

    .search input {{
      width: min(320px, 100%);
      padding: 12px 14px;
      border: 1px solid rgba(28, 29, 33, 0.2);
      border-radius: 999px;
      background: rgba(255, 250, 240, 0.9);
      color: var(--ink);
      font-size: 14px;
    }}

    .legend {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      color: var(--muted);
      font-size: 12px;
    }}

    .legend span {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}

    .swatch {{
      width: 11px;
      height: 11px;
      border-radius: 999px;
      display: inline-block;
    }}

    .board {{
      background: rgba(255, 250, 240, 0.82);
      border: 1px solid rgba(28, 29, 33, 0.1);
      border-radius: 24px;
      box-shadow: 0 26px 80px rgba(28, 29, 33, 0.08);
      overflow: hidden;
      min-height: calc(100vh - 120px);
    }}

    svg {{
      width: 100%;
      height: calc(100vh - 120px);
      display: block;
    }}

    .side-panel {{
      border-left: 1px solid rgba(28, 29, 33, 0.08);
      background: linear-gradient(180deg, rgba(255, 250, 240, 0.92), rgba(244, 239, 227, 0.98));
      padding: 24px 22px;
      overflow-y: auto;
    }}

    .meta {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      margin-bottom: 10px;
    }}

    .node-title {{
      margin: 0 0 10px;
      font-size: 28px;
      line-height: 1.05;
    }}

    .node-type {{
      display: inline-block;
      margin-bottom: 16px;
      padding: 6px 10px;
      border-radius: 999px;
      font-size: 12px;
      background: rgba(28, 29, 33, 0.06);
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}

    .node-copy {{
      margin: 0 0 18px;
      color: var(--ink);
      line-height: 1.6;
    }}

    .list-block {{
      margin: 0 0 20px;
      padding: 0;
      list-style: none;
      display: grid;
      gap: 8px;
    }}

    .list-block li {{
      padding: 10px 12px;
      border: 1px solid rgba(28, 29, 33, 0.08);
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.5);
      font-size: 14px;
      line-height: 1.45;
    }}

    .empty {{
      color: var(--muted);
      font-style: italic;
    }}

    .node {{
      cursor: pointer;
      transition: opacity 120ms ease;
    }}

    .node-label {{
      font-size: 11px;
      fill: var(--ink);
      pointer-events: none;
    }}

    .edge {{
      stroke: rgba(28, 29, 33, 0.14);
      stroke-width: 1.2;
    }}

    .faded {{
      opacity: 0.13;
    }}

    .active-node circle {{
      stroke: var(--accent);
      stroke-width: 4;
    }}

    .active-edge {{
      stroke: rgba(124, 45, 18, 0.72);
      stroke-width: 2.4;
    }}

    @media (max-width: 1024px) {{
      .shell {{
        grid-template-columns: 1fr;
      }}

      .side-panel {{
        border-left: 0;
        border-top: 1px solid rgba(28, 29, 33, 0.08);
      }}

      svg {{
        height: 70vh;
      }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <section class="canvas-panel">
      <div class="header">
        <div>
          <div class="meta">Casemap MVP GraphRAG</div>
          <h1>Contract Big Knowledge Map</h1>
          <p class="subtitle">Sections, concepts, statutes, and cases are clustered into a legal knowledge map. Select a node to inspect the summary, cited authorities, and graph neighbors.</p>
          <div class="legend">
            <span><i class="swatch" style="background: var(--section)"></i>Section</span>
            <span><i class="swatch" style="background: var(--concept)"></i>Concept</span>
            <span><i class="swatch" style="background: var(--statute)"></i>Statute</span>
            <span><i class="swatch" style="background: var(--case)"></i>Case</span>
          </div>
        </div>
        <label class="search">
          <span class="meta">Find a node</span>
          <input id="searchInput" type="search" placeholder="Search concepts, statutes, cases">
        </label>
      </div>
      <div class="board">
        <svg id="graph" viewBox="0 0 1280 920" preserveAspectRatio="xMidYMid meet"></svg>
      </div>
    </section>
    <aside class="side-panel">
      <div class="meta">Selection</div>
      <h2 class="node-title" id="nodeTitle">Overview</h2>
      <div class="node-type" id="nodeType">Graph</div>
      <p class="node-copy" id="nodeSummary">The graph groups the contract outline into numbered sections, concept nodes, and cited legal authorities. Search or click on a node to inspect its local neighborhood.</p>
      <div class="meta">Citations</div>
      <ul class="list-block" id="citationList"><li class="empty">No node selected.</li></ul>
      <div class="meta">Neighbors</div>
      <ul class="list-block" id="neighborList"><li class="empty">No node selected.</li></ul>
    </aside>
  </div>
  <script>
    const payload = {data};
    const nodes = payload.nodes.map((node) => ({{ ...node }}));
    const edges = payload.edges.map((edge, index) => ({{ ...edge, id: `edge-${{index}}` }}));
    const svg = document.getElementById("graph");
    const titleEl = document.getElementById("nodeTitle");
    const typeEl = document.getElementById("nodeType");
    const summaryEl = document.getElementById("nodeSummary");
    const citationList = document.getElementById("citationList");
    const neighborList = document.getElementById("neighborList");
    const searchInput = document.getElementById("searchInput");

    const colors = {{
      section: getComputedStyle(document.documentElement).getPropertyValue("--section").trim(),
      concept: getComputedStyle(document.documentElement).getPropertyValue("--concept").trim(),
      statute: getComputedStyle(document.documentElement).getPropertyValue("--statute").trim(),
      case: getComputedStyle(document.documentElement).getPropertyValue("--case").trim(),
    }};

    const index = new Map(nodes.map((node) => [node.id, node]));
    const neighbors = new Map(nodes.map((node) => [node.id, new Set()]));
    edges.forEach((edge) => {{
      neighbors.get(edge.source)?.add(edge.target);
      neighbors.get(edge.target)?.add(edge.source);
    }});

    function radiusFor(node) {{
      if (node.type === "section") return 18;
      if (node.type === "concept") return 10;
      return 9;
    }}

    function layout() {{
      const width = 1280;
      const height = 920;
      const centerX = width / 2;
      const centerY = height / 2;
      const sections = nodes.filter((node) => node.type === "section");
      const concepts = nodes.filter((node) => node.type === "concept");
      const authorities = nodes.filter((node) => node.type !== "section" && node.type !== "concept");

      sections.forEach((section, idx) => {{
        const angle = (Math.PI * 2 * idx) / Math.max(sections.length, 1) - Math.PI / 2;
        section.x = centerX + Math.cos(angle) * 240;
        section.y = centerY + Math.sin(angle) * 220;
      }});

      const groupedConcepts = new Map();
      concepts.forEach((concept) => {{
        const bucket = groupedConcepts.get(concept.section_id) || [];
        bucket.push(concept);
        groupedConcepts.set(concept.section_id, bucket);
      }});

      groupedConcepts.forEach((group, sectionId) => {{
        const parent = index.get(sectionId);
        if (!parent) return;
        group.forEach((concept, idx) => {{
          const angle = (Math.PI * 2 * idx) / Math.max(group.length, 1);
          const distance = 74 + (idx % 3) * 18;
          concept.x = parent.x + Math.cos(angle) * distance;
          concept.y = parent.y + Math.sin(angle) * distance;
        }});
      }});

      authorities.forEach((authority, idx) => {{
        const angle = (Math.PI * 2 * idx) / Math.max(authorities.length, 1) - Math.PI / 2;
        const ring = authority.type === "statute" ? 380 : 430;
        authority.x = centerX + Math.cos(angle) * ring;
        authority.y = centerY + Math.sin(angle) * (ring * 0.72);
      }});
    }}

    layout();

    const edgeLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const nodeLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    svg.append(edgeLayer, nodeLayer);

    const edgeEls = new Map();
    edges.forEach((edge) => {{
      const source = index.get(edge.source);
      const target = index.get(edge.target);
      if (!source || !target) return;
      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("class", "edge");
      line.setAttribute("x1", source.x);
      line.setAttribute("y1", source.y);
      line.setAttribute("x2", target.x);
      line.setAttribute("y2", target.y);
      edgeLayer.appendChild(line);
      edgeEls.set(edge.id, line);
    }});

    const nodeEls = new Map();
    nodes.forEach((node) => {{
      const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
      group.setAttribute("class", "node");
      group.dataset.id = node.id;

      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", node.x);
      circle.setAttribute("cy", node.y);
      circle.setAttribute("r", radiusFor(node));
      circle.setAttribute("fill", colors[node.type] || colors.concept);
      circle.setAttribute("fill-opacity", node.type === "section" ? "0.96" : "0.9");

      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      label.setAttribute("class", "node-label");
      label.setAttribute("x", node.x + radiusFor(node) + 6);
      label.setAttribute("y", node.y + 4);
      label.textContent = node.label;

      group.append(circle, label);
      group.addEventListener("click", () => selectNode(node.id));
      nodeLayer.appendChild(group);
      nodeEls.set(node.id, group);
    }});

    function renderList(element, values) {{
      element.innerHTML = "";
      if (!values.length) {{
        const item = document.createElement("li");
        item.className = "empty";
        item.textContent = "None";
        element.appendChild(item);
        return;
      }}
      values.forEach((value) => {{
        const item = document.createElement("li");
        item.textContent = value;
        element.appendChild(item);
      }});
    }}

    function selectNode(nodeId) {{
      const node = index.get(nodeId);
      if (!node) return;
      const localNeighbors = [...(neighbors.get(nodeId) || [])].map((id) => index.get(id)).filter(Boolean);
      titleEl.textContent = node.label;
      typeEl.textContent = node.type;
      summaryEl.textContent = node.summary || "No summary available.";
      renderList(citationList, node.citations || []);
      renderList(
        neighborList,
        localNeighbors
          .sort((left, right) => left.label.localeCompare(right.label))
          .map((item) => `${{item.label}} (${{item.type}})`)
      );

      nodeEls.forEach((element, id) => {{
        const isNeighbor = id === nodeId || (neighbors.get(nodeId)?.has(id));
        element.classList.toggle("faded", !isNeighbor);
        element.classList.toggle("active-node", id === nodeId);
      }});

      edges.forEach((edge) => {{
        const active = edge.source === nodeId || edge.target === nodeId;
        const edgeEl = edgeEls.get(edge.id);
        if (!edgeEl) return;
        edgeEl.classList.toggle("faded", !active);
        edgeEl.classList.toggle("active-edge", active);
      }});
    }}

    function clearSelection() {{
      titleEl.textContent = "Overview";
      typeEl.textContent = "Graph";
      summaryEl.textContent = "The graph groups the contract outline into numbered sections, concept nodes, and cited legal authorities. Search or click on a node to inspect its local neighborhood.";
      citationList.innerHTML = '<li class="empty">No node selected.</li>';
      neighborList.innerHTML = '<li class="empty">No node selected.</li>';
      nodeEls.forEach((element) => {{
        element.classList.remove("faded", "active-node");
      }});
      edgeEls.forEach((element) => {{
        element.classList.remove("faded", "active-edge");
      }});
    }}

    function searchNode(value) {{
      const query = value.trim().toLowerCase();
      if (!query) {{
        clearSelection();
        return;
      }}
      const match = nodes.find((node) => {{
        const haystack = `${{node.label}} ${{node.summary || ""}} ${{(node.citations || []).join(" ")}}`.toLowerCase();
        return haystack.includes(query);
      }});
      if (match) {{
        selectNode(match.id);
      }}
    }}

    searchInput.addEventListener("input", (event) => searchNode(event.target.value));
    clearSelection();
  </script>
</body>
</html>
"""


def render_relationship_map(graph_payload: dict) -> str:
    data = json.dumps(graph_payload, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Casemap Relationship Graph</title>
  <style>
    :root {{
      --bg: #f6f0e1;
      --panel: rgba(255, 251, 244, 0.96);
      --line: rgba(40, 41, 44, 0.1);
      --ink: #202124;
      --muted: #655f54;
      --domain: #0f4c5c;
      --topic: #f4a261;
      --case: #7f5539;
      --statute: #bc4749;
      --source: #52796f;
      --accent: #283618;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      min-height: 100vh;
      font-family: "Georgia", "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(244, 162, 97, 0.18), transparent 28%),
        radial-gradient(circle at bottom right, rgba(15, 76, 92, 0.16), transparent 26%),
        linear-gradient(180deg, #f9f4ea 0%, var(--bg) 100%);
    }}

    .shell {{
      display: grid;
      grid-template-columns: 300px minmax(0, 1fr) 380px;
      min-height: 100vh;
    }}

    .panel {{
      background: var(--panel);
      backdrop-filter: blur(10px);
      border-right: 1px solid var(--line);
      padding: 22px 20px;
      overflow-y: auto;
    }}

    .details {{
      border-right: 0;
      border-left: 1px solid var(--line);
    }}

    .canvas-panel {{
      padding: 20px;
      display: grid;
      grid-template-rows: auto 1fr;
      gap: 14px;
    }}

    .meta {{
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.14em;
      margin-bottom: 8px;
    }}

    h1, h2 {{
      margin: 0;
    }}

    h1 {{
      font-size: 34px;
      line-height: 0.96;
      letter-spacing: -0.04em;
      margin-bottom: 8px;
    }}

    .intro {{
      color: var(--muted);
      font-size: 14px;
      line-height: 1.55;
      margin-bottom: 18px;
    }}

    .counts {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 18px;
    }}

    .count-card {{
      padding: 12px 14px;
      border-radius: 16px;
      border: 1px solid rgba(40, 41, 44, 0.08);
      background: rgba(255, 255, 255, 0.52);
    }}

    .count-card strong {{
      display: block;
      font-size: 22px;
      line-height: 1;
      margin-bottom: 4px;
    }}

    .search-box input {{
      width: 100%;
      padding: 12px 14px;
      border-radius: 16px;
      border: 1px solid rgba(40, 41, 44, 0.14);
      font-size: 14px;
      background: rgba(255, 255, 255, 0.86);
    }}

    .filters {{
      display: grid;
      gap: 10px;
      margin: 18px 0 18px;
    }}

    .filter-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      font-size: 14px;
      color: var(--ink);
    }}

    .results {{
      display: grid;
      gap: 10px;
    }}

    .result-btn {{
      width: 100%;
      text-align: left;
      padding: 12px 14px;
      border: 1px solid rgba(40, 41, 44, 0.08);
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.58);
      cursor: pointer;
      font: inherit;
      color: inherit;
    }}

    .result-btn small {{
      display: block;
      margin-top: 4px;
      color: var(--muted);
      font-size: 12px;
    }}

    .board {{
      border-radius: 24px;
      border: 1px solid rgba(40, 41, 44, 0.08);
      background: rgba(255, 251, 244, 0.78);
      box-shadow: 0 24px 80px rgba(40, 41, 44, 0.08);
      overflow: hidden;
      min-height: calc(100vh - 70px);
    }}

    svg {{
      width: 100%;
      height: calc(100vh - 70px);
      display: block;
    }}

    .legend {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      font-size: 12px;
      color: var(--muted);
    }}

    .legend span {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}

    .swatch {{
      width: 11px;
      height: 11px;
      border-radius: 999px;
      display: inline-block;
    }}

    .node {{
      cursor: pointer;
      transition: opacity 120ms ease;
    }}

    .edge {{
      stroke: rgba(40, 41, 44, 0.12);
      stroke-width: 1.2;
    }}

    .node-label {{
      fill: var(--ink);
      font-size: 11px;
      pointer-events: none;
    }}

    .suppressed {{
      display: none;
    }}

    .faded {{
      opacity: 0.12;
    }}

    .active-edge {{
      stroke: rgba(40, 41, 44, 0.5);
      stroke-width: 2.4;
    }}

    .active-node circle {{
      stroke: var(--accent);
      stroke-width: 3.6;
    }}

    .pill {{
      display: inline-block;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(40, 41, 44, 0.06);
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 14px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}

    .summary {{
      font-size: 15px;
      line-height: 1.6;
      margin: 0 0 18px;
    }}

    .metric-list, .link-list, .ref-list, .neighbor-list {{
      list-style: none;
      margin: 0 0 18px;
      padding: 0;
      display: grid;
      gap: 10px;
    }}

    .metric-list li, .link-list li, .ref-list li, .neighbor-list li {{
      border: 1px solid rgba(40, 41, 44, 0.08);
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.5);
      padding: 12px 14px;
      font-size: 14px;
      line-height: 1.5;
    }}

    .ref-meta {{
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }}

    a {{
      color: var(--domain);
      text-decoration: none;
    }}

    a:hover {{
      text-decoration: underline;
    }}

    @media (max-width: 1200px) {{
      .shell {{
        grid-template-columns: 1fr;
      }}

      .panel, .details {{
        border: 0;
      }}

      svg {{
        height: 72vh;
      }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <aside class="panel">
      <div class="meta">Casemap Relationship Graph</div>
      <h1>Hong Kong Contract Law</h1>
      <p class="intro">This view clusters doctrine, cases, statutes, and source documents. Search for a case or concept, then inspect the supporting book passages and external links in the detail panel.</p>
      <div class="counts">
        <div class="count-card"><strong>{graph_payload["meta"]["node_count"]}</strong><span>Nodes</span></div>
        <div class="count-card"><strong>{graph_payload["meta"]["edge_count"]}</strong><span>Edges</span></div>
        <div class="count-card"><strong>{graph_payload["meta"]["source_count"]}</strong><span>Sources</span></div>
        <div class="count-card"><strong>{graph_payload["meta"]["passage_count"]}</strong><span>Passages</span></div>
      </div>
      <div class="search-box">
        <div class="meta">Search</div>
        <input id="searchInput" type="search" placeholder="Case, topic, statute, source">
      </div>
      <div class="filters">
        <div class="meta">Filters</div>
        <label class="filter-row"><span>Domains</span><input type="checkbox" data-type="domain" checked></label>
        <label class="filter-row"><span>Topics</span><input type="checkbox" data-type="topic" checked></label>
        <label class="filter-row"><span>Cases</span><input type="checkbox" data-type="case" checked></label>
        <label class="filter-row"><span>Statutes</span><input type="checkbox" data-type="statute" checked></label>
        <label class="filter-row"><span>Sources</span><input type="checkbox" data-type="source" checked></label>
      </div>
      <div class="meta">Matches</div>
      <div id="results" class="results"></div>
    </aside>
    <section class="canvas-panel">
      <div>
        <div class="legend">
          <span><i class="swatch" style="background: var(--domain)"></i>Domain</span>
          <span><i class="swatch" style="background: var(--topic)"></i>Topic</span>
          <span><i class="swatch" style="background: var(--case)"></i>Case</span>
          <span><i class="swatch" style="background: var(--statute)"></i>Statute</span>
          <span><i class="swatch" style="background: var(--source)"></i>Source</span>
        </div>
      </div>
      <div class="board">
        <svg id="graph" viewBox="0 0 1440 980" preserveAspectRatio="xMidYMid meet"></svg>
      </div>
    </section>
    <aside class="panel details">
      <div class="meta">Selection</div>
      <h2 id="nodeTitle">Overview</h2>
      <div id="nodeType" class="pill">Graph</div>
      <p id="nodeSummary" class="summary">Select a node to inspect its role in the graph, related authorities, supporting source passages, and any available external links.</p>
      <div class="meta">Metrics</div>
      <ul id="metricList" class="metric-list"><li>Choose a node to view counts and metadata.</li></ul>
      <div class="meta">External Links</div>
      <ul id="linkList" class="link-list"><li>No node selected.</li></ul>
      <div class="meta">Relevant Passages</div>
      <ul id="referenceList" class="ref-list"><li>No node selected.</li></ul>
      <div class="meta">Related Nodes</div>
      <ul id="neighborList" class="neighbor-list"><li>No node selected.</li></ul>
    </aside>
  </div>
  <script>
    const payload = {data};
    const nodes = payload.nodes.map((node) => ({{ ...node }}));
    const edges = payload.edges.map((edge, index) => ({{ ...edge, id: `edge-${{index}}` }}));
    const nodeMap = new Map(nodes.map((node) => [node.id, node]));
    const adjacency = new Map(nodes.map((node) => [node.id, new Set()]));
    edges.forEach((edge) => {{
      adjacency.get(edge.source)?.add(edge.target);
      adjacency.get(edge.target)?.add(edge.source);
    }});

    const svg = document.getElementById("graph");
    const resultsEl = document.getElementById("results");
    const searchInput = document.getElementById("searchInput");
    const typeInputs = [...document.querySelectorAll("input[data-type]")];
    const titleEl = document.getElementById("nodeTitle");
    const typeEl = document.getElementById("nodeType");
    const summaryEl = document.getElementById("nodeSummary");
    const metricList = document.getElementById("metricList");
    const linkList = document.getElementById("linkList");
    const referenceList = document.getElementById("referenceList");
    const neighborList = document.getElementById("neighborList");

    const colors = {{
      domain: getComputedStyle(document.documentElement).getPropertyValue("--domain").trim(),
      topic: getComputedStyle(document.documentElement).getPropertyValue("--topic").trim(),
      case: getComputedStyle(document.documentElement).getPropertyValue("--case").trim(),
      statute: getComputedStyle(document.documentElement).getPropertyValue("--statute").trim(),
      source: getComputedStyle(document.documentElement).getPropertyValue("--source").trim(),
    }};

    function hashCode(value) {{
      let hash = 0;
      for (let index = 0; index < value.length; index += 1) {{
        hash = ((hash << 5) - hash) + value.charCodeAt(index);
        hash |= 0;
      }}
      return Math.abs(hash);
    }}

    function radiusFor(node) {{
      if (node.type === "domain") return 18;
      if (node.type === "topic") return 11;
      if (node.type === "source") return 10;
      return 8;
    }}

    function layoutNodes() {{
      const width = 1440;
      const height = 980;
      const centerX = width / 2;
      const centerY = height / 2;
      const domains = nodes.filter((node) => node.type === "domain");
      const topics = nodes.filter((node) => node.type === "topic");
      const sources = nodes.filter((node) => node.type === "source");
      const authorities = nodes.filter((node) => node.type === "case" || node.type === "statute");

      domains.forEach((domain, index) => {{
        const angle = (Math.PI * 2 * index) / Math.max(domains.length, 1) - Math.PI / 2;
        domain.x = centerX + Math.cos(angle) * 250;
        domain.y = centerY + Math.sin(angle) * 220;
      }});

      const topicsByDomain = new Map();
      topics.forEach((topic) => {{
        const bucket = topicsByDomain.get(topic.domain_id) || [];
        bucket.push(topic);
        topicsByDomain.set(topic.domain_id, bucket);
      }});

      topicsByDomain.forEach((bucket, domainId) => {{
        const domain = nodeMap.get(domainId);
        if (!domain) return;
        bucket.forEach((topic, index) => {{
          const angle = (Math.PI * 2 * index) / Math.max(bucket.length, 1);
          const distance = 88 + ((index % 4) * 18);
          topic.x = domain.x + Math.cos(angle) * distance;
          topic.y = domain.y + Math.sin(angle) * distance;
        }});
      }});

      sources.forEach((source, index) => {{
        source.x = 126;
        source.y = 170 + (index * 120);
      }});

      authorities.forEach((node, index) => {{
        const neighbors = [...(adjacency.get(node.id) || [])]
          .map((id) => nodeMap.get(id))
          .filter((item) => item && (item.type === "topic" || item.type === "domain"));
        let baseX = centerX;
        let baseY = centerY;
        if (neighbors.length) {{
          baseX = neighbors.reduce((sum, item) => sum + item.x, 0) / neighbors.length;
          baseY = neighbors.reduce((sum, item) => sum + item.y, 0) / neighbors.length;
        }}
        const hash = hashCode(node.id);
        const angle = ((hash % 360) / 180) * Math.PI;
        const distance = node.type === "statute" ? 160 + (hash % 60) : 220 + (hash % 110);
        node.x = Math.max(70, Math.min(width - 70, baseX + Math.cos(angle) * distance));
        node.y = Math.max(70, Math.min(height - 70, baseY + Math.sin(angle) * distance * 0.75));
      }});
    }}

    layoutNodes();

    const edgeLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const nodeLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    svg.append(edgeLayer, nodeLayer);

    const edgeEls = new Map();
    edges.forEach((edge) => {{
      const source = nodeMap.get(edge.source);
      const target = nodeMap.get(edge.target);
      if (!source || !target) return;
      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("class", "edge");
      line.setAttribute("x1", source.x);
      line.setAttribute("y1", source.y);
      line.setAttribute("x2", target.x);
      line.setAttribute("y2", target.y);
      edgeLayer.appendChild(line);
      edgeEls.set(edge.id, line);
    }});

    const nodeEls = new Map();
    const labelEls = new Map();
    nodes.forEach((node) => {{
      const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
      group.setAttribute("class", "node");
      group.dataset.id = node.id;

      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", node.x);
      circle.setAttribute("cy", node.y);
      circle.setAttribute("r", radiusFor(node));
      circle.setAttribute("fill", colors[node.type] || colors.topic);
      circle.setAttribute("fill-opacity", node.type === "domain" ? "0.95" : "0.88");

      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      label.setAttribute("class", "node-label");
      if (node.type === "case" || node.type === "statute") {{
        label.classList.add("suppressed");
      }}
      label.setAttribute("x", node.x + radiusFor(node) + 6);
      label.setAttribute("y", node.y + 4);
      label.textContent = node.label;

      group.append(circle, label);
      group.addEventListener("click", () => selectNode(node.id));
      nodeLayer.appendChild(group);
      nodeEls.set(node.id, group);
      labelEls.set(node.id, label);
    }});

    function visibleTypes() {{
      return new Set(typeInputs.filter((input) => input.checked).map((input) => input.dataset.type));
    }}

    function filteredNodes(query) {{
      const allowedTypes = visibleTypes();
      const lowered = query.trim().toLowerCase();
      return nodes
        .filter((node) => allowedTypes.has(node.type))
        .filter((node) => {{
          if (!lowered) return true;
          const haystack = `${{node.label}} ${{node.summary || ""}}`.toLowerCase();
          return haystack.includes(lowered);
        }})
        .sort((left, right) => {{
          const leftScore = (left.degree || 0) + ((left.type === "domain" || left.type === "topic") ? 3 : 0);
          const rightScore = (right.degree || 0) + ((right.type === "domain" || right.type === "topic") ? 3 : 0);
          return rightScore - leftScore;
        }});
    }}

    function renderResults(query) {{
      const matches = filteredNodes(query).slice(0, 12);
      resultsEl.innerHTML = "";
      if (!matches.length) {{
        resultsEl.innerHTML = "<div class='intro'>No matching nodes for the current filters.</div>";
        return;
      }}
      matches.forEach((node) => {{
        const button = document.createElement("button");
        button.className = "result-btn";
        button.type = "button";
        button.innerHTML = `<strong>${{node.label}}</strong><small>${{node.type}} · degree ${{node.degree || 0}}</small>`;
        button.addEventListener("click", () => selectNode(node.id));
        resultsEl.appendChild(button);
      }});
    }}

    function renderMetrics(metrics) {{
      metricList.innerHTML = "";
      const entries = Object.entries(metrics || {{}});
      if (!entries.length) {{
        metricList.innerHTML = "<li>No metrics available.</li>";
        return;
      }}
      entries.forEach(([key, value]) => {{
        const item = document.createElement("li");
        item.textContent = `${{key}}: ${{value}}`;
        metricList.appendChild(item);
      }});
    }}

    function renderLinks(links) {{
      linkList.innerHTML = "";
      if (!links || !links.length) {{
        linkList.innerHTML = "<li>No external links available.</li>";
        return;
      }}
      links.forEach((link) => {{
        const item = document.createElement("li");
        item.innerHTML = `<a href="${{link.url}}" target="_blank" rel="noreferrer">${{link.label}}</a>`;
        linkList.appendChild(item);
      }});
    }}

    function renderReferences(references) {{
      referenceList.innerHTML = "";
      if (!references || !references.length) {{
        referenceList.innerHTML = "<li>No supporting passages captured for this node.</li>";
        return;
      }}
      references.forEach((reference) => {{
        const item = document.createElement("li");
        item.innerHTML = `<div class="ref-meta">${{reference.source_label}} · ${{reference.location}}</div><div>${{reference.snippet}}</div>`;
        referenceList.appendChild(item);
      }});
    }}

    function renderNeighbors(nodeId) {{
      neighborList.innerHTML = "";
      const ids = [...(adjacency.get(nodeId) || [])]
        .map((id) => nodeMap.get(id))
        .filter(Boolean)
        .sort((left, right) => left.label.localeCompare(right.label));
      if (!ids.length) {{
        neighborList.innerHTML = "<li>No related nodes.</li>";
        return;
      }}
      ids.slice(0, 16).forEach((neighbor) => {{
        const item = document.createElement("li");
        item.innerHTML = `<strong>${{neighbor.label}}</strong><div class="ref-meta">${{neighbor.type}}</div>`;
        item.addEventListener("click", () => selectNode(neighbor.id));
        neighborList.appendChild(item);
      }});
    }}

    function resetDetail() {{
      titleEl.textContent = "Overview";
      typeEl.textContent = "Graph";
      summaryEl.textContent = "Select a node to inspect its role in the graph, related authorities, supporting source passages, and any available external links.";
      metricList.innerHTML = "<li>Choose a node to view counts and metadata.</li>";
      linkList.innerHTML = "<li>No node selected.</li>";
      referenceList.innerHTML = "<li>No node selected.</li>";
      neighborList.innerHTML = "<li>No node selected.</li>";
    }}

    let selectedNodeId = null;

    function applyVisibility() {{
      const allowedTypes = visibleTypes();
      nodeEls.forEach((element, id) => {{
        const node = nodeMap.get(id);
        const allowed = allowedTypes.has(node.type);
        element.classList.toggle("suppressed", !allowed);
      }});
      edgeEls.forEach((element, edgeId) => {{
        const edge = edges.find((item) => item.id === edgeId);
        const sourceAllowed = edge && allowedTypes.has(nodeMap.get(edge.source).type);
        const targetAllowed = edge && allowedTypes.has(nodeMap.get(edge.target).type);
        element.classList.toggle("suppressed", !(sourceAllowed && targetAllowed));
      }});
    }}

    function selectNode(nodeId) {{
      const node = nodeMap.get(nodeId);
      if (!node) return;
      selectedNodeId = nodeId;
      titleEl.textContent = node.label;
      typeEl.textContent = node.type;
      summaryEl.textContent = node.summary || "No summary available.";
      renderMetrics(node.metrics || {{}});
      renderLinks(node.links || []);
      renderReferences(node.references || []);
      renderNeighbors(nodeId);

      nodeEls.forEach((element, id) => {{
        const neighbor = adjacency.get(nodeId)?.has(id);
        const active = id === nodeId;
        element.classList.toggle("active-node", active);
        element.classList.toggle("faded", !(active || neighbor));
      }});

      labelEls.forEach((element, id) => {{
        const alwaysVisible = ["domain", "topic", "source"].includes(nodeMap.get(id).type);
        const neighbor = adjacency.get(nodeId)?.has(id);
        element.classList.toggle("suppressed", !(alwaysVisible || neighbor || id === nodeId));
      }});

      edges.forEach((edge) => {{
        const edgeEl = edgeEls.get(edge.id);
        if (!edgeEl) return;
        const active = edge.source === nodeId || edge.target === nodeId;
        edgeEl.classList.toggle("faded", !active);
        edgeEl.classList.toggle("active-edge", active);
      }});
    }}

    function clearSelection() {{
      selectedNodeId = null;
      resetDetail();
      nodeEls.forEach((element) => element.classList.remove("active-node", "faded"));
      edges.forEach((edge) => {{
        const edgeEl = edgeEls.get(edge.id);
        if (edgeEl) edgeEl.classList.remove("active-edge", "faded");
      }});
      labelEls.forEach((element, id) => {{
        const alwaysVisible = ["domain", "topic", "source"].includes(nodeMap.get(id).type);
        element.classList.toggle("suppressed", !alwaysVisible);
      }});
    }}

    searchInput.addEventListener("input", (event) => {{
      const query = event.target.value;
      renderResults(query);
      if (!query.trim()) {{
        clearSelection();
      }}
    }});

    typeInputs.forEach((input) => input.addEventListener("change", () => {{
      applyVisibility();
      renderResults(searchInput.value);
      if (selectedNodeId && !visibleTypes().has(nodeMap.get(selectedNodeId).type)) {{
        clearSelection();
      }}
    }}));

    applyVisibility();
    renderResults("");
    const initialDomain = nodes.find((node) => node.type === "domain");
    if (initialDomain) {{
      selectNode(initialDomain.id);
    }} else {{
      resetDetail();
    }}
  </script>
</body>
</html>
"""
