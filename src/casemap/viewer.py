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


def render_relationship_tree(graph_payload: dict) -> str:
    data = json.dumps(graph_payload, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Casemap Relationship Tree</title>
  <style>
    :root {{
      --bg: #f7f0e4;
      --panel: rgba(255, 251, 244, 0.96);
      --ink: #232427;
      --muted: #666055;
      --line: rgba(35, 36, 39, 0.1);
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
      font-family: "Georgia", "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(244, 162, 97, 0.16), transparent 26%),
        linear-gradient(180deg, #faf5eb 0%, var(--bg) 100%);
      min-height: 100vh;
    }}

    .shell {{
      display: grid;
      grid-template-columns: 440px minmax(0, 1fr);
      min-height: 100vh;
    }}

    .tree-panel, .detail-panel {{
      padding: 22px 20px;
      overflow-y: auto;
    }}

    .tree-panel {{
      border-right: 1px solid var(--line);
      background: var(--panel);
    }}

    .detail-panel {{
      background: linear-gradient(180deg, rgba(255, 251, 244, 0.78), rgba(247, 240, 228, 0.92));
    }}

    .meta {{
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.14em;
      margin-bottom: 8px;
    }}

    h1, h2, h3 {{
      margin: 0;
    }}

    h1 {{
      font-size: 36px;
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

    .nav {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 18px;
    }}

    .nav a {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 9px 12px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.58);
      color: var(--ink);
      text-decoration: none;
      font-size: 13px;
    }}

    .nav a.active {{
      background: rgba(15, 76, 92, 0.12);
      border-color: rgba(15, 76, 92, 0.24);
    }}

    .search-box {{
      margin-bottom: 18px;
    }}

    .search-box input {{
      width: 100%;
      padding: 12px 14px;
      border-radius: 16px;
      border: 1px solid rgba(35, 36, 39, 0.14);
      font-size: 14px;
      background: rgba(255, 255, 255, 0.86);
    }}

    .result-list, .ref-list, .neighbor-list, .metric-list, .link-list {{
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      gap: 10px;
    }}

    .result-list {{
      margin-bottom: 22px;
    }}

    .result-btn, .node-btn {{
      width: 100%;
      text-align: left;
      border: 1px solid rgba(35, 36, 39, 0.08);
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.56);
      padding: 10px 12px;
      cursor: pointer;
      font: inherit;
      color: inherit;
    }}

    .node-btn small, .result-btn small {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-top: 4px;
    }}

    details {{
      border-left: 2px solid rgba(35, 36, 39, 0.08);
      padding-left: 12px;
      margin-bottom: 12px;
    }}

    details > summary {{
      list-style: none;
      cursor: pointer;
      margin-left: -12px;
      padding-left: 12px;
    }}

    details > summary::-webkit-details-marker {{
      display: none;
    }}

    .domain-summary {{
      padding: 10px 12px;
      border-radius: 16px;
      background: rgba(15, 76, 92, 0.08);
      border: 1px solid rgba(15, 76, 92, 0.18);
    }}

    .topic-summary {{
      padding: 8px 10px;
      border-radius: 12px;
      background: rgba(244, 162, 97, 0.12);
      border: 1px solid rgba(244, 162, 97, 0.18);
    }}

    .group-block {{
      margin: 10px 0 16px;
      padding-left: 8px;
      display: grid;
      gap: 8px;
    }}

    .group-title {{
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      margin-top: 2px;
    }}

    .chip {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 11px;
      margin-bottom: 8px;
      color: white;
    }}

    .chip.domain {{ background: var(--domain); }}
    .chip.topic {{ background: var(--topic); color: var(--ink); }}
    .chip.case {{ background: var(--case); }}
    .chip.statute {{ background: var(--statute); }}
    .chip.source {{ background: var(--source); }}

    .summary {{
      font-size: 15px;
      line-height: 1.6;
      margin: 0 0 18px;
    }}

    .metric-list li, .link-list li, .ref-list li, .neighbor-list li {{
      border: 1px solid rgba(35, 36, 39, 0.08);
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.54);
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

    .empty {{
      color: var(--muted);
      font-style: italic;
    }}

    @media (max-width: 1080px) {{
      .shell {{
        grid-template-columns: 1fr;
      }}
      .tree-panel {{
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <aside class="tree-panel">
      <div class="meta">Casemap Tree</div>
      <h1>Hierarchical Contract Law Tree</h1>
      <p class="intro">Read the legal picture top-down: doctrinal domains, their sub-topics, and the related authorities and sources attached to each branch.</p>
      <nav class="nav">
        <a href="/" class="active">Tree</a>
        <a href="/relationships">Graph</a>
        <a href="/mvp">MVP</a>
      </nav>
      <div class="search-box">
        <div class="meta">Jump To Node</div>
        <input id="searchInput" type="search" placeholder="Case, topic, statute, source">
      </div>
      <ul id="resultList" class="result-list"></ul>
      <div class="meta">Tree</div>
      <div id="treeRoot"></div>
    </aside>
    <main class="detail-panel">
      <div class="meta">Selection</div>
      <h2 id="nodeTitle">Overview</h2>
      <div id="nodeChip" class="chip domain">tree</div>
      <p id="nodeSummary" class="summary">Select a domain, topic, case, statute, or source to inspect its details, public links, and graph neighbors.</p>
      <div class="meta">Metrics</div>
      <ul id="metricList" class="metric-list"><li class="empty">Choose a node to view metrics.</li></ul>
      <div class="meta">External Links</div>
      <ul id="linkList" class="link-list"><li class="empty">No node selected.</li></ul>
      <div class="meta">Supporting References</div>
      <ul id="referenceList" class="ref-list"><li class="empty">No node selected.</li></ul>
      <div class="meta">Related Nodes</div>
      <ul id="neighborList" class="neighbor-list"><li class="empty">No node selected.</li></ul>
    </main>
  </div>
  <script>
    const payload = {data};
    const nodes = payload.nodes;
    const edges = payload.edges;
    const nodeMap = new Map(nodes.map((node) => [node.id, node]));
    const adjacency = new Map(nodes.map((node) => [node.id, new Set()]));
    const byType = {{
      domain: nodes.filter((node) => node.type === "domain").sort((a, b) => a.label.localeCompare(b.label)),
    }};

    edges.forEach((edge) => {{
      adjacency.get(edge.source)?.add(edge.target);
      adjacency.get(edge.target)?.add(edge.source);
    }});

    const treeRoot = document.getElementById("treeRoot");
    const resultList = document.getElementById("resultList");
    const searchInput = document.getElementById("searchInput");
    const titleEl = document.getElementById("nodeTitle");
    const chipEl = document.getElementById("nodeChip");
    const summaryEl = document.getElementById("nodeSummary");
    const metricList = document.getElementById("metricList");
    const linkList = document.getElementById("linkList");
    const referenceList = document.getElementById("referenceList");
    const neighborList = document.getElementById("neighborList");

    function neighborsByType(nodeId, type) {{
      return [...(adjacency.get(nodeId) || [])]
        .map((id) => nodeMap.get(id))
        .filter((node) => node && node.type === type)
        .sort((a, b) => a.label.localeCompare(b.label));
    }}

    function makeNodeButton(node, context) {{
      const button = document.createElement("button");
      button.type = "button";
      button.className = "node-btn";
      button.innerHTML = `<strong>${{node.label}}</strong><small>${{node.type}}${{context ? " · " + context : ""}}</small>`;
      button.addEventListener("click", () => selectNode(node.id));
      return button;
    }}

    function renderTree() {{
      treeRoot.innerHTML = "";
      byType.domain.forEach((domain) => {{
        const domainDetails = document.createElement("details");
        domainDetails.open = true;

        const domainSummary = document.createElement("summary");
        domainSummary.className = "domain-summary";
        domainSummary.appendChild(makeNodeButton(domain, `${{neighborsByType(domain.id, "topic").length}} topics`));
        domainDetails.appendChild(domainSummary);

        const topicIds = edges
          .filter((edge) => edge.type === "contains" && edge.source === domain.id)
          .map((edge) => nodeMap.get(edge.target))
          .filter(Boolean)
          .sort((a, b) => a.label.localeCompare(b.label));

        topicIds.forEach((topic) => {{
          const topicDetails = document.createElement("details");
          const topicSummary = document.createElement("summary");
          topicSummary.className = "topic-summary";
          topicSummary.appendChild(makeNodeButton(topic, `${{neighborsByType(topic.id, "case").length}} cases · ${{neighborsByType(topic.id, "statute").length}} statutes`));
          topicDetails.appendChild(topicSummary);

          const blocks = [
            ["Cases", neighborsByType(topic.id, "case")],
            ["Statutes", neighborsByType(topic.id, "statute")],
            ["Sources", neighborsByType(topic.id, "source")],
          ];

          blocks.forEach(([label, items]) => {{
            if (!items.length) return;
            const block = document.createElement("div");
            block.className = "group-block";
            const heading = document.createElement("div");
            heading.className = "group-title";
            heading.textContent = label;
            block.appendChild(heading);
            items.slice(0, 16).forEach((item) => block.appendChild(makeNodeButton(item, topic.label)));
            topicDetails.appendChild(block);
          }});

          domainDetails.appendChild(topicDetails);
        }});

        const domainAuthorities = [
          ...neighborsByType(domain.id, "case"),
          ...neighborsByType(domain.id, "statute"),
        ]
          .filter((node, index, arr) => arr.findIndex((item) => item.id === node.id) === index)
          .slice(0, 12);

        if (domainAuthorities.length) {{
          const crossBlock = document.createElement("div");
          crossBlock.className = "group-block";
          const heading = document.createElement("div");
          heading.className = "group-title";
          heading.textContent = "Cross-cutting Authorities";
          crossBlock.appendChild(heading);
          domainAuthorities.forEach((item) => crossBlock.appendChild(makeNodeButton(item, domain.label)));
          domainDetails.appendChild(crossBlock);
        }}

        treeRoot.appendChild(domainDetails);
      }});
    }}

    function renderResults(query) {{
      const lowered = query.trim().toLowerCase();
      resultList.innerHTML = "";
      if (!lowered) return;
      const matches = nodes
        .filter((node) => `${{node.label}} ${{node.summary || ""}}`.toLowerCase().includes(lowered))
        .sort((a, b) => (b.degree || 0) - (a.degree || 0))
        .slice(0, 10);
      matches.forEach((node) => {{
        const item = document.createElement("li");
        item.appendChild(makeNodeButton(node, `degree ${{node.degree || 0}}`));
        resultList.appendChild(item);
      }});
      if (!matches.length) {{
        resultList.innerHTML = "<li class='empty'>No matching nodes.</li>";
      }}
    }}

    function renderMetrics(node) {{
      metricList.innerHTML = "";
      const metrics = Object.entries(node.metrics || {{}});
      const degreeItem = document.createElement("li");
      degreeItem.textContent = `degree: ${{node.degree || 0}}`;
      metricList.appendChild(degreeItem);
      if (!metrics.length) return;
      metrics.forEach(([key, value]) => {{
        const item = document.createElement("li");
        item.textContent = `${{key}}: ${{value}}`;
        metricList.appendChild(item);
      }});
    }}

    function renderLinks(node) {{
      linkList.innerHTML = "";
      if (!node.links || !node.links.length) {{
        linkList.innerHTML = "<li class='empty'>No external links available.</li>";
        return;
      }}
      node.links.forEach((link) => {{
        const item = document.createElement("li");
        item.innerHTML = `<a href="${{link.url}}" target="_blank" rel="noreferrer">${{link.label}}</a>`;
        linkList.appendChild(item);
      }});
    }}

    function renderReferences(node) {{
      referenceList.innerHTML = "";
      if (!node.references || !node.references.length) {{
        referenceList.innerHTML = "<li class='empty'>No references attached.</li>";
        return;
      }}
      node.references.forEach((reference) => {{
        const item = document.createElement("li");
        item.innerHTML = `<div class="ref-meta">${{reference.source_label}} · ${{reference.location}}</div><div>${{reference.snippet}}</div>`;
        referenceList.appendChild(item);
      }});
    }}

    function renderNeighbors(node) {{
      neighborList.innerHTML = "";
      const neighbors = [...(adjacency.get(node.id) || [])]
        .map((id) => nodeMap.get(id))
        .filter(Boolean)
        .sort((a, b) => a.label.localeCompare(b.label))
        .slice(0, 18);
      if (!neighbors.length) {{
        neighborList.innerHTML = "<li class='empty'>No related nodes.</li>";
        return;
      }}
      neighbors.forEach((neighbor) => {{
        const item = document.createElement("li");
        item.innerHTML = `<strong>${{neighbor.label}}</strong><div class="ref-meta">${{neighbor.type}}</div>`;
        item.addEventListener("click", () => selectNode(neighbor.id));
        neighborList.appendChild(item);
      }});
    }}

    function selectNode(nodeId) {{
      const node = nodeMap.get(nodeId);
      if (!node) return;
      titleEl.textContent = node.label;
      chipEl.textContent = node.type;
      chipEl.className = `chip ${{node.type}}`;
      summaryEl.textContent = node.summary || "No summary available.";
      renderMetrics(node);
      renderLinks(node);
      renderReferences(node);
      renderNeighbors(node);
    }}

    searchInput.addEventListener("input", (event) => renderResults(event.target.value));

    renderTree();
    const firstDomain = byType.domain[0];
    if (firstDomain) {{
      selectNode(firstDomain.id);
    }}
  </script>
</body>
</html>
"""


def render_relationship_family_tree(graph_payload: dict) -> str:
    data = json.dumps(graph_payload, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Casemap Family Tree</title>
  <style>
    :root {{
      --bg: #f7f0e4;
      --panel: rgba(255, 251, 244, 0.94);
      --ink: #232427;
      --muted: #666055;
      --line: rgba(35, 36, 39, 0.1);
      --domain: #0f4c5c;
      --topic: #f4a261;
      --case: #7f5539;
      --statute: #bc4749;
      --source: #52796f;
      --accent: #283618;
      --shadow: 0 20px 60px rgba(35, 36, 39, 0.08);
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      min-height: 100vh;
      font-family: "Georgia", "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(244, 162, 97, 0.17), transparent 28%),
        radial-gradient(circle at top right, rgba(15, 76, 92, 0.12), transparent 24%),
        linear-gradient(180deg, #faf5eb 0%, var(--bg) 100%);
    }}

    .shell {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 380px;
      min-height: 100vh;
    }}

    .workspace {{
      padding: 26px;
      overflow: auto;
    }}

    .detail-panel {{
      border-left: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(255, 251, 244, 0.92), rgba(247, 240, 228, 0.98));
      padding: 24px 22px;
      overflow-y: auto;
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
      font-size: clamp(34px, 4vw, 48px);
      line-height: 0.94;
      letter-spacing: -0.045em;
      margin-bottom: 10px;
    }}

    .intro {{
      color: var(--muted);
      font-size: 15px;
      line-height: 1.58;
      max-width: 900px;
      margin-bottom: 18px;
    }}

    .toolbar {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
      margin-bottom: 18px;
      flex-wrap: wrap;
    }}

    .nav {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }}

    .nav a {{
      display: inline-flex;
      align-items: center;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.58);
      color: var(--ink);
      text-decoration: none;
      font-size: 13px;
    }}

    .nav a.active {{
      background: rgba(15, 76, 92, 0.12);
      border-color: rgba(15, 76, 92, 0.24);
    }}

    .search-box {{
      width: min(360px, 100%);
      display: grid;
      gap: 8px;
    }}

    .search-box input {{
      width: 100%;
      padding: 12px 14px;
      border-radius: 16px;
      border: 1px solid rgba(35, 36, 39, 0.14);
      font-size: 14px;
      background: rgba(255, 255, 255, 0.88);
    }}

    .breadcrumbs {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 18px;
    }}

    .crumb {{
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.56);
      border-radius: 999px;
      padding: 8px 12px;
      font-size: 13px;
      cursor: pointer;
      color: var(--ink);
      font: inherit;
    }}

    .results {{
      display: grid;
      gap: 10px;
      margin-bottom: 18px;
    }}

    .card-grid {{
      display: flex;
      gap: 18px;
      align-items: flex-start;
      overflow-x: auto;
      padding-bottom: 18px;
    }}

    .lane {{
      min-width: 320px;
      width: 320px;
      display: grid;
      gap: 14px;
      position: relative;
    }}

    .lane::after {{
      content: "";
      position: absolute;
      top: 36px;
      right: -11px;
      width: 22px;
      height: 2px;
      background: rgba(35, 36, 39, 0.12);
    }}

    .lane:last-child::after {{
      display: none;
    }}

    .lane-title {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--muted);
      padding-left: 4px;
    }}

    .node-card, .group-card {{
      border: 1px solid rgba(35, 36, 39, 0.08);
      border-radius: 22px;
      background: rgba(255, 255, 255, 0.72);
      box-shadow: var(--shadow);
      padding: 16px;
    }}

    .node-card {{
      cursor: pointer;
      transition: transform 140ms ease, border-color 140ms ease;
    }}

    .node-card:hover {{
      transform: translateY(-2px);
      border-color: rgba(35, 36, 39, 0.18);
    }}

    .node-card.active {{
      border-color: rgba(40, 54, 24, 0.35);
      box-shadow: 0 24px 70px rgba(40, 54, 24, 0.12);
    }}

    .card-type {{
      display: inline-block;
      padding: 5px 9px;
      border-radius: 999px;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: white;
      margin-bottom: 10px;
    }}

    .card-type.domain {{ background: var(--domain); }}
    .card-type.topic {{ background: var(--topic); color: var(--ink); }}
    .card-type.case {{ background: var(--case); }}
    .card-type.statute {{ background: var(--statute); }}
    .card-type.source {{ background: var(--source); }}

    .node-title {{
      font-size: 22px;
      line-height: 1.08;
      margin-bottom: 8px;
    }}

    .node-summary {{
      color: var(--muted);
      font-size: 14px;
      line-height: 1.5;
      margin-bottom: 12px;
    }}

    .chip-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}

    .mini-chip {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 9px;
      border-radius: 999px;
      font-size: 11px;
      border: 1px solid rgba(35, 36, 39, 0.08);
      background: rgba(255, 255, 255, 0.6);
      color: var(--muted);
    }}

    .group-title {{
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      margin-bottom: 10px;
    }}

    .stack {{
      display: grid;
      gap: 10px;
    }}

    .case-card {{
      border: 1px solid rgba(35, 36, 39, 0.08);
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.66);
      padding: 14px;
      cursor: pointer;
    }}

    .case-card.active {{
      border-color: rgba(127, 85, 57, 0.36);
      box-shadow: 0 20px 60px rgba(127, 85, 57, 0.12);
    }}

    .case-head {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 10px;
      margin-bottom: 8px;
    }}

    .case-title {{
      font-size: 17px;
      line-height: 1.2;
    }}

    .status {{
      display: inline-block;
      padding: 5px 8px;
      border-radius: 999px;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      white-space: nowrap;
    }}

    .status.adopted {{
      background: rgba(82, 121, 111, 0.16);
      color: var(--source);
    }}

    .status.qualified {{
      background: rgba(244, 162, 97, 0.18);
      color: #8c4b11;
    }}

    .status.not-adopted {{
      background: rgba(188, 71, 73, 0.14);
      color: var(--statute);
    }}

    .status.relevant-authority {{
      background: rgba(15, 76, 92, 0.12);
      color: var(--domain);
    }}

    .quote {{
      border-left: 3px solid rgba(127, 85, 57, 0.22);
      padding-left: 10px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
      margin: 0 0 10px;
    }}

    .details-type {{
      display: inline-block;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(35, 36, 39, 0.06);
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 14px;
    }}

    .details-summary {{
      font-size: 15px;
      line-height: 1.62;
      margin: 0 0 18px;
    }}

    .metric-list, .link-list, .ref-list, .neighbor-list {{
      list-style: none;
      margin: 0 0 20px;
      padding: 0;
      display: grid;
      gap: 10px;
    }}

    .metric-list li, .link-list li, .ref-list li, .neighbor-list li {{
      border: 1px solid rgba(35, 36, 39, 0.08);
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.54);
      padding: 12px 14px;
      font-size: 14px;
      line-height: 1.5;
    }}

    .ref-meta {{
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }}

    .empty {{
      color: var(--muted);
      font-style: italic;
    }}

    a {{
      color: var(--domain);
      text-decoration: none;
    }}

    a:hover {{
      text-decoration: underline;
    }}

    @media (max-width: 1100px) {{
      .shell {{
        grid-template-columns: 1fr;
      }}

      .detail-panel {{
        border-left: 0;
        border-top: 1px solid var(--line);
      }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <section class="workspace">
      <div class="meta">Casemap Family Tree</div>
      <h1>Hong Kong Contract Law Branch Explorer</h1>
      <p class="intro">Inspired by a large family-tree layout, this view opens one branch at a time. Click a doctrinal domain, then a sub-topic, then a case or statute leaf. Case cards surface relevance, treatment status, and any available note-style quotation.</p>
      <div class="toolbar">
        <nav class="nav">
          <a href="/" class="active">Family Tree</a>
          <a href="/relationships">Relationship Graph</a>
          <a href="/mvp">MVP GraphRAG</a>
        </nav>
        <label class="search-box">
          <span class="meta">Jump To Node</span>
          <input id="searchInput" type="search" placeholder="Case, topic, statute, source">
        </label>
      </div>
      <div id="breadcrumbs" class="breadcrumbs"></div>
      <div id="results" class="results"></div>
      <div id="board" class="card-grid"></div>
    </section>
    <aside class="detail-panel">
      <div class="meta">Selection</div>
      <h2 id="detailTitle">Overview</h2>
      <div id="detailType" class="details-type">Tree</div>
      <p id="detailSummary" class="details-summary">Select a branch card to zoom in. The right panel keeps the selected node's relationship details and any available public-facing quote or treatment signal.</p>
      <div class="meta">Metrics</div>
      <ul id="metricList" class="metric-list"><li class="empty">Choose a node to view metrics.</li></ul>
      <div class="meta">External Links</div>
      <ul id="linkList" class="link-list"><li class="empty">No node selected.</li></ul>
      <div class="meta">References</div>
      <ul id="referenceList" class="ref-list"><li class="empty">No node selected.</li></ul>
      <div class="meta">Related Nodes</div>
      <ul id="neighborList" class="neighbor-list"><li class="empty">No node selected.</li></ul>
    </aside>
  </div>
  <script>
    const payload = {data};
    const nodes = payload.nodes;
    const edges = payload.edges;
    const nodeMap = new Map(nodes.map((node) => [node.id, node]));
    const adjacency = new Map(nodes.map((node) => [node.id, new Set()]));
    edges.forEach((edge) => {{
      adjacency.get(edge.source)?.add(edge.target);
      adjacency.get(edge.target)?.add(edge.source);
    }});

    const boardEl = document.getElementById("board");
    const resultsEl = document.getElementById("results");
    const breadcrumbsEl = document.getElementById("breadcrumbs");
    const searchInput = document.getElementById("searchInput");
    const detailTitle = document.getElementById("detailTitle");
    const detailType = document.getElementById("detailType");
    const detailSummary = document.getElementById("detailSummary");
    const metricList = document.getElementById("metricList");
    const linkList = document.getElementById("linkList");
    const referenceList = document.getElementById("referenceList");
    const neighborList = document.getElementById("neighborList");

    const domains = nodes.filter((node) => node.type === "domain").sort((a, b) => a.label.localeCompare(b.label));
    const rootNode = {{
      id: "__root__",
      label: payload.meta.title || "Hong Kong Contract Law",
      type: "root",
      summary: "Top-level doctrinal overview. Select a domain to drill down into topics and authorities.",
      metrics: {{
        domains: domains.length,
        nodes: payload.meta.node_count,
        edges: payload.meta.edge_count
      }},
      links: [],
      references: [],
    }};

    const state = {{
      domainId: null,
      topicId: null,
      nodeId: rootNode.id,
    }};

    function getNode(id) {{
      if (id === rootNode.id) return rootNode;
      return nodeMap.get(id);
    }}

    function neighborsByType(nodeId, type) {{
      return [...(adjacency.get(nodeId) || [])]
        .map((id) => nodeMap.get(id))
        .filter((node) => node && node.type === type)
        .sort((a, b) => a.label.localeCompare(b.label));
    }}

    function childrenOfDomain(domainId) {{
      return edges
        .filter((edge) => edge.type === "contains" && edge.source === domainId)
        .map((edge) => nodeMap.get(edge.target))
        .filter(Boolean)
        .sort((a, b) => a.label.localeCompare(b.label));
    }}

    function caseStatusClass(status) {{
      return (status || "relevant authority").replace(/\\s+/g, "-");
    }}

    function createCard(node, extra = {{}}, options = {{ compact: false }}) {{
      const element = document.createElement("article");
      element.className = (node.type === "case") ? "case-card" : "node-card";
      if (state.nodeId === node.id) {{
        element.classList.add("active");
      }}
      element.addEventListener("click", () => {{
        if (node.type === "domain") {{
          state.domainId = node.id;
          state.topicId = null;
        }} else if (node.type === "topic") {{
          state.topicId = node.id;
        }}
        state.nodeId = node.id;
        render();
      }});

      if (node.type === "case") {{
        const profile = node.case_profile || {{}};
        const status = profile.treatment || "relevant authority";
        const relevance = extra.relevance ? `<div class="mini-chip">${{extra.relevance}}</div>` : "";
        const quote = profile.quote ? `<p class="quote">"${{profile.quote}}"</p>` : "<p class='quote'>Public quote not yet attached. Use the authority links to verify treatment on public sources.</p>";
        element.innerHTML = `
          <div class="case-head">
            <div class="case-title">${{node.label}}</div>
            <span class="status ${{caseStatusClass(status)}}">${{status}}</span>
          </div>
          ${{quote}}
          <div class="chip-row">
            ${{relevance}}
            <div class="mini-chip">${{(node.metrics && node.metrics.sources) || 0}} sources</div>
            <div class="mini-chip">${{(node.metrics && node.metrics.mentions) || 0}} mentions</div>
          </div>
        `;
        return element;
      }}

      const summary = node.summary ? node.summary : "No summary available.";
      const chips = [];
      if (extra.subtitle) chips.push(`<div class="mini-chip">${{extra.subtitle}}</div>`);
      if (extra.countLabel) chips.push(`<div class="mini-chip">${{extra.countLabel}}</div>`);
      element.innerHTML = `
        <div class="card-type ${{node.type}}">${{node.type}}</div>
        <div class="node-title">${{node.label}}</div>
        <div class="node-summary">${{summary}}</div>
        <div class="chip-row">${{chips.join("")}}</div>
      `;
      return element;
    }}

    function buildBreadcrumbs() {{
      breadcrumbsEl.innerHTML = "";
      const crumbNodes = [rootNode];
      if (state.domainId) crumbNodes.push(getNode(state.domainId));
      if (state.topicId) crumbNodes.push(getNode(state.topicId));
      if (state.nodeId && state.nodeId !== rootNode.id && state.nodeId !== state.domainId && state.nodeId !== state.topicId) {{
        crumbNodes.push(getNode(state.nodeId));
      }}
      crumbNodes.filter(Boolean).forEach((node, index) => {{
        const button = document.createElement("button");
        button.className = "crumb";
        button.textContent = node.label;
        button.addEventListener("click", () => {{
          if (node.id === rootNode.id) {{
            state.domainId = null;
            state.topicId = null;
            state.nodeId = rootNode.id;
          }} else if (node.type === "domain") {{
            state.domainId = node.id;
            state.topicId = null;
            state.nodeId = node.id;
          }} else if (node.type === "topic") {{
            state.topicId = node.id;
            state.nodeId = node.id;
          }} else {{
            state.nodeId = node.id;
          }}
          render();
        }});
        breadcrumbsEl.appendChild(button);
      }});
    }}

    function renderDetails(node) {{
      detailTitle.textContent = node.label;
      detailType.textContent = node.type;
      detailSummary.textContent = node.summary || "No summary available.";

      metricList.innerHTML = "";
      const metrics = Object.entries(node.metrics || {{}});
      const degree = node.id === rootNode.id ? 0 : ((node.degree || 0));
      const degreeItem = document.createElement("li");
      degreeItem.textContent = `degree: ${{degree}}`;
      metricList.appendChild(degreeItem);
      if (!metrics.length) {{
        const item = document.createElement("li");
        item.className = "empty";
        item.textContent = "No extra metrics available.";
        metricList.appendChild(item);
      }} else {{
        metrics.forEach(([key, value]) => {{
          const item = document.createElement("li");
          item.textContent = `${{key}}: ${{value}}`;
          metricList.appendChild(item);
        }});
      }}
      if (node.case_profile && node.case_profile.treatment) {{
        const item = document.createElement("li");
        item.textContent = `treatment: ${{node.case_profile.treatment}}`;
        metricList.appendChild(item);
      }}

      linkList.innerHTML = "";
      if (!node.links || !node.links.length) {{
        linkList.innerHTML = "<li class='empty'>No external links available.</li>";
      }} else {{
        node.links.forEach((link) => {{
          const item = document.createElement("li");
          item.innerHTML = `<a href="${{link.url}}" target="_blank" rel="noreferrer">${{link.label}}</a>`;
          linkList.appendChild(item);
        }});
      }}

      referenceList.innerHTML = "";
      if (!node.references || !node.references.length) {{
        referenceList.innerHTML = "<li class='empty'>No references attached.</li>";
      }} else {{
        node.references.forEach((reference) => {{
          const item = document.createElement("li");
          item.innerHTML = `<div class="ref-meta">${{reference.source_label}} · ${{reference.location}}</div><div>${{reference.snippet}}</div>`;
          referenceList.appendChild(item);
        }});
      }}

      neighborList.innerHTML = "";
      if (node.id === rootNode.id) {{
        neighborList.innerHTML = "<li class='empty'>Select a branch card to inspect related nodes.</li>";
      }} else {{
        const neighbors = [...(adjacency.get(node.id) || [])]
          .map((id) => nodeMap.get(id))
          .filter(Boolean)
          .sort((a, b) => a.label.localeCompare(b.label))
          .slice(0, 18);
        if (!neighbors.length) {{
          neighborList.innerHTML = "<li class='empty'>No related nodes.</li>";
        }} else {{
          neighbors.forEach((neighbor) => {{
            const item = document.createElement("li");
            item.innerHTML = `<strong>${{neighbor.label}}</strong><div class="ref-meta">${{neighbor.type}}</div>`;
            item.addEventListener("click", () => {{
              if (neighbor.type === "domain") state.domainId = neighbor.id;
              if (neighbor.type === "topic") state.topicId = neighbor.id;
              state.nodeId = neighbor.id;
              render();
            }});
            neighborList.appendChild(item);
          }});
        }}
      }}
    }}

    function renderResults(query) {{
      const lowered = query.trim().toLowerCase();
      resultsEl.innerHTML = "";
      if (!lowered) return;
      const matches = nodes
        .filter((node) => `${{node.label}} ${{node.summary || ""}}`.toLowerCase().includes(lowered))
        .sort((a, b) => (b.degree || 0) - (a.degree || 0))
        .slice(0, 8);
      matches.forEach((node) => {{
        const card = createCard(node, {{ subtitle: `degree ${{node.degree || 0}}` }});
        resultsEl.appendChild(card);
      }});
      if (!matches.length) {{
        resultsEl.innerHTML = "<div class='empty'>No matching nodes.</div>";
      }}
    }}

    function renderBoard() {{
      boardEl.innerHTML = "";

      const rootLane = document.createElement("section");
      rootLane.className = "lane";
      rootLane.innerHTML = "<div class='lane-title'>Start</div>";
      rootLane.appendChild(createCard(rootNode, {{ countLabel: `${{domains.length}} domains` }}));
      boardEl.appendChild(rootLane);

      const domainLane = document.createElement("section");
      domainLane.className = "lane";
      domainLane.innerHTML = "<div class='lane-title'>Domains</div>";
      domains.forEach((domain) => {{
        domainLane.appendChild(createCard(domain, {{ countLabel: `${{childrenOfDomain(domain.id).length}} topics` }}));
      }});
      boardEl.appendChild(domainLane);

      if (!state.domainId) return;
      const selectedDomain = getNode(state.domainId);
      const topics = childrenOfDomain(selectedDomain.id);
      const topicLane = document.createElement("section");
      topicLane.className = "lane";
      topicLane.innerHTML = `<div class='lane-title'>${{selectedDomain.label}} Topics</div>`;
      topics.forEach((topic) => {{
        const cases = neighborsByType(topic.id, "case").length;
        const statutes = neighborsByType(topic.id, "statute").length;
        topicLane.appendChild(createCard(topic, {{ countLabel: `${{cases}} cases · ${{statutes}} statutes` }}));
      }});
      boardEl.appendChild(topicLane);

      if (!state.topicId) return;
      const selectedTopic = getNode(state.topicId);
      const authorityLane = document.createElement("section");
      authorityLane.className = "lane";
      authorityLane.innerHTML = `<div class='lane-title'>${{selectedTopic.label}} Authorities</div>`;

      const cases = neighborsByType(selectedTopic.id, "case");
      const statutes = neighborsByType(selectedTopic.id, "statute");
      const sources = neighborsByType(selectedTopic.id, "source");

      if (cases.length) {{
        const block = document.createElement("div");
        block.className = "group-card";
        block.innerHTML = "<div class='group-title'>Cases</div>";
        const stack = document.createElement("div");
        stack.className = "stack";
        cases.slice(0, 18).forEach((caseNode) => {{
          const profile = caseNode.case_profile || {{}};
          const relevance = selectedTopic.label;
          stack.appendChild(createCard(caseNode, {{ relevance, treatment: profile.treatment || "relevant authority" }}));
        }});
        block.appendChild(stack);
        authorityLane.appendChild(block);
      }}

      if (statutes.length) {{
        const block = document.createElement("div");
        block.className = "group-card";
        block.innerHTML = "<div class='group-title'>Statutes</div>";
        const stack = document.createElement("div");
        stack.className = "stack";
        statutes.slice(0, 10).forEach((item) => stack.appendChild(createCard(item)));
        block.appendChild(stack);
        authorityLane.appendChild(block);
      }}

      if (sources.length) {{
        const block = document.createElement("div");
        block.className = "group-card";
        block.innerHTML = "<div class='group-title'>Sources</div>";
        const stack = document.createElement("div");
        stack.className = "stack";
        sources.slice(0, 8).forEach((item) => stack.appendChild(createCard(item)));
        block.appendChild(stack);
        authorityLane.appendChild(block);
      }}
      boardEl.appendChild(authorityLane);

      const selectedNode = getNode(state.nodeId);
      if (!selectedNode || selectedNode.type !== "case") return;
      const developmentLane = document.createElement("section");
      developmentLane.className = "lane";
      developmentLane.innerHTML = `<div class='lane-title'>Case Development</div>`;
      const developmentCard = document.createElement("div");
      developmentCard.className = "group-card";
      developmentCard.innerHTML = "<div class='group-title'>Related Authorities</div>";
      const stack = document.createElement("div");
      stack.className = "stack";
      const relatedCases = neighborsByType(selectedNode.id, "case");
      const sameTopicCases = cases.filter((item) => item.id !== selectedNode.id);
      [...relatedCases, ...sameTopicCases]
        .filter((node, index, arr) => arr.findIndex((item) => item.id === node.id) === index)
        .slice(0, 12)
        .forEach((item) => stack.appendChild(createCard(item, {{ relevance: "related authority" }})));
      if (!stack.childNodes.length) {{
        const empty = document.createElement("div");
        empty.className = "empty";
        empty.textContent = "No additional related case branch is available for this node yet.";
        developmentCard.appendChild(empty);
      }} else {{
        developmentCard.appendChild(stack);
      }}
      developmentLane.appendChild(developmentCard);
      boardEl.appendChild(developmentLane);
    }}

    function render() {{
      if (!state.domainId && domains[0]) {{
        state.domainId = domains[0].id;
      }}
      if (state.domainId && !state.topicId) {{
        const firstTopic = childrenOfDomain(state.domainId)[0];
        if (firstTopic) state.topicId = firstTopic.id;
      }}
      if (!state.nodeId || state.nodeId === rootNode.id) {{
        state.nodeId = state.topicId || state.domainId || rootNode.id;
      }}
      buildBreadcrumbs();
      renderBoard();
      renderDetails(getNode(state.nodeId) || rootNode);
      renderResults(searchInput.value);
    }}

    searchInput.addEventListener("input", (event) => renderResults(event.target.value));
    render();
  </script>
</body>
</html>
"""
