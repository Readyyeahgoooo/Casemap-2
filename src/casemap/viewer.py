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
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Casemap Authority Tree</title>
  <style>
    :root {
      --bg: #edf0f4;
      --bg-deep: #dfe4ea;
      --panel: rgba(255, 255, 255, 0.78);
      --panel-strong: rgba(255, 255, 255, 0.9);
      --ink: #101216;
      --muted: #6c727c;
      --line: rgba(16, 18, 22, 0.1);
      --line-strong: rgba(16, 18, 22, 0.16);
      --shadow: 0 24px 80px rgba(16, 18, 22, 0.08);
      --shadow-soft: 0 14px 32px rgba(16, 18, 22, 0.06);
      --glass: blur(22px);
      --root: #0f1114;
      --silver: #c7cdd6;
      --silver-deep: #959da8;
      --silver-soft: #f5f7fa;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      font-family: "Avenir Next", "Helvetica Neue", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(255, 255, 255, 0.78), transparent 28%),
        radial-gradient(circle at top right, rgba(199, 205, 214, 0.38), transparent 24%),
        linear-gradient(180deg, #f8f9fb 0%, var(--bg) 48%, var(--bg-deep) 100%);
    }

    .shell {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 390px;
      min-height: 100vh;
    }

    .workspace {
      padding: 28px;
      overflow: auto;
    }

    .detail-panel {
      border-left: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.82), rgba(242, 244, 247, 0.92));
      backdrop-filter: var(--glass);
      -webkit-backdrop-filter: var(--glass);
      padding: 24px 22px 32px;
      overflow-y: auto;
    }

    .meta {
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      margin-bottom: 10px;
    }

    h1, h2, h3 {
      margin: 0;
      font-weight: 600;
    }

    h1 {
      font-size: clamp(34px, 4vw, 52px);
      letter-spacing: -0.05em;
      line-height: 0.92;
      margin-bottom: 12px;
    }

    .intro {
      max-width: 920px;
      color: var(--muted);
      font-size: 15px;
      line-height: 1.62;
      margin: 0 0 18px;
    }

    .toolbar {
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      gap: 16px;
      flex-wrap: wrap;
      margin-bottom: 18px;
    }

    .nav {
      display: inline-flex;
      gap: 8px;
      padding: 6px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.56);
      backdrop-filter: var(--glass);
      -webkit-backdrop-filter: var(--glass);
      box-shadow: var(--shadow-soft);
    }

    .nav a {
      padding: 10px 14px;
      border-radius: 999px;
      color: var(--ink);
      text-decoration: none;
      font-size: 13px;
      letter-spacing: 0.01em;
    }

    .nav a.active {
      background: var(--root);
      color: white;
    }

    .search-box {
      width: min(360px, 100%);
      display: grid;
      gap: 8px;
    }

    .search-box input {
      width: 100%;
      border: 1px solid rgba(16, 18, 22, 0.12);
      border-radius: 18px;
      padding: 13px 15px;
      background: rgba(255, 255, 255, 0.82);
      box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.8);
      font: inherit;
      color: var(--ink);
    }

    .breadcrumbs {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 14px;
    }

    .crumb,
    .result-pill {
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.66);
      border-radius: 999px;
      padding: 9px 13px;
      font: inherit;
      font-size: 13px;
      color: var(--ink);
      cursor: pointer;
      box-shadow: var(--shadow-soft);
    }

    .results {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 16px;
      min-height: 18px;
    }

    .stack-view {
      display: grid;
      gap: 18px;
      padding-bottom: 22px;
    }

    .tree-section {
      border: 1px solid var(--line);
      border-radius: 28px;
      padding: 18px;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.84), rgba(250, 251, 253, 0.72));
      backdrop-filter: var(--glass);
      -webkit-backdrop-filter: var(--glass);
      box-shadow: var(--shadow);
    }

    .section-head {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 12px;
      flex-wrap: wrap;
      margin-bottom: 14px;
    }

    .section-title {
      font-size: 18px;
      letter-spacing: -0.02em;
    }

    .section-caption {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }

    .root-wrap,
    .domain-row,
    .topic-grid,
    .node-grid {
      display: flex;
      justify-content: center;
      gap: 12px;
      flex-wrap: wrap;
    }

    .topic-grid,
    .node-grid {
      justify-content: flex-start;
    }

    .tree-node {
      min-width: 190px;
      max-width: 280px;
      border: 1px solid rgba(16, 18, 22, 0.1);
      border-radius: 24px;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(248, 250, 252, 0.84));
      box-shadow: var(--shadow-soft);
      padding: 14px 15px;
      text-align: left;
      cursor: pointer;
      transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
      font: inherit;
      color: var(--ink);
    }

    .tree-node:hover {
      transform: translateY(-2px);
      border-color: var(--line-strong);
      box-shadow: 0 20px 44px rgba(16, 18, 22, 0.08);
    }

    .tree-node.active {
      border-color: rgba(15, 17, 20, 0.28);
      box-shadow: 0 22px 54px rgba(15, 17, 20, 0.14);
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(242, 244, 248, 0.92));
    }

    .tree-node.root {
      min-width: 300px;
      background: linear-gradient(180deg, #14171b, #0f1114);
      color: white;
      border-color: rgba(15, 17, 20, 0.66);
    }

    .tree-node.domain {
      background: linear-gradient(180deg, rgba(248, 249, 251, 0.94), rgba(229, 233, 239, 0.88));
    }

    .tree-node.topic {
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(239, 242, 246, 0.88));
    }

    .tree-node.case,
    .tree-node.statute,
    .tree-node.source {
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(245, 247, 250, 0.92));
    }

    .node-kicker {
      display: inline-flex;
      margin-bottom: 10px;
      padding: 5px 9px;
      border-radius: 999px;
      font-size: 10px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
      background: rgba(255, 255, 255, 0.54);
      border: 1px solid rgba(16, 18, 22, 0.08);
    }

    .tree-node.root .node-kicker {
      color: rgba(255, 255, 255, 0.76);
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(255, 255, 255, 0.14);
    }

    .node-name {
      display: block;
      font-size: 16px;
      line-height: 1.24;
      letter-spacing: -0.02em;
    }

    .tree-node.root .node-name {
      font-size: 20px;
    }

    .chip-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }

    .micro-chip,
    .signal-chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border: 1px solid rgba(16, 18, 22, 0.1);
      border-radius: 999px;
      padding: 6px 9px;
      font-size: 11px;
      color: var(--muted);
      background: rgba(255, 255, 255, 0.76);
    }

    .tree-node.root .micro-chip {
      color: rgba(255, 255, 255, 0.76);
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(255, 255, 255, 0.14);
    }

    .micro-chip.code,
    .signal-chip.code {
      color: var(--ink);
      background: rgba(199, 205, 214, 0.28);
    }

    .signal-chip.adopted,
    .signal-chip.followed,
    .signal-chip.applied {
      color: white;
      background: var(--root);
      border-color: rgba(15, 17, 20, 0.3);
    }

    .signal-chip.qualified,
    .signal-chip.originating-authority,
    .signal-chip.relevant-authority {
      color: var(--ink);
      background: rgba(199, 205, 214, 0.32);
    }

    .signal-chip.not-adopted,
    .signal-chip.codified {
      color: var(--ink);
      background: rgba(149, 157, 168, 0.24);
    }

    .authority-stack {
      display: grid;
      gap: 16px;
    }

    .lineage-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 14px;
      align-items: start;
    }

    .lineage-panel,
    .aux-panel {
      border: 1px solid rgba(16, 18, 22, 0.08);
      border-radius: 24px;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(246, 248, 251, 0.82));
      padding: 16px;
      box-shadow: var(--shadow-soft);
    }

    .branch-head {
      margin-bottom: 14px;
    }

    .branch-head h3 {
      font-size: 16px;
      line-height: 1.2;
      letter-spacing: -0.02em;
      margin-bottom: 6px;
    }

    .branch-meta {
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }

    .lineage-track {
      position: relative;
      display: grid;
      gap: 14px;
      justify-items: center;
      padding: 4px 0;
    }

    .lineage-track::before {
      content: "";
      position: absolute;
      top: 8px;
      bottom: 8px;
      left: calc(50% - 1px);
      width: 2px;
      border-radius: 999px;
      background: linear-gradient(180deg, rgba(199, 205, 214, 0.15), rgba(149, 157, 168, 0.5), rgba(199, 205, 214, 0.15));
    }

    .lineage-step {
      width: 100%;
      display: flex;
      justify-content: center;
      position: relative;
      z-index: 1;
    }

    .lineage-step .tree-node {
      width: min(100%, 260px);
    }

    .aux-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
    }

    .detail-type {
      display: inline-flex;
      margin-bottom: 14px;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.86);
      border: 1px solid var(--line);
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.1em;
    }

    .detail-summary {
      font-size: 15px;
      line-height: 1.64;
      margin: 0 0 16px;
    }

    .signal-panel {
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 14px;
      background: rgba(255, 255, 255, 0.66);
      box-shadow: var(--shadow-soft);
      margin-bottom: 18px;
    }

    .signal-panel.empty-state {
      color: var(--muted);
      font-style: italic;
    }

    .signal-panel p {
      margin: 12px 0 0;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.58;
    }

    .data-list {
      list-style: none;
      padding: 0;
      margin: 0 0 18px;
      display: grid;
      gap: 10px;
    }

    .data-list li {
      border: 1px solid rgba(16, 18, 22, 0.08);
      border-radius: 18px;
      padding: 12px 14px;
      background: rgba(255, 255, 255, 0.6);
      line-height: 1.5;
      font-size: 14px;
      box-shadow: var(--shadow-soft);
    }

    .data-list li.clickable {
      cursor: pointer;
    }

    .list-meta {
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 5px;
    }

    .empty {
      color: var(--muted);
      font-style: italic;
    }

    a {
      color: var(--ink);
      text-decoration: none;
      border-bottom: 1px solid rgba(16, 18, 22, 0.16);
    }

    a:hover {
      border-color: rgba(16, 18, 22, 0.36);
    }

    @media (max-width: 1120px) {
      .shell {
        grid-template-columns: 1fr;
      }

      .detail-panel {
        border-left: 0;
        border-top: 1px solid var(--line);
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="workspace">
      <div class="meta">Casemap Vertical Tree</div>
      <h1>Hong Kong Contract Law Authority Tree</h1>
      <p class="intro">A top-down doctrine tree for Hong Kong contract law. The node faces stay compact so the full structure remains readable. Hover a ground, sub-ground, or authority to preview its details in the side panel, and click to lock the selection and open the next branch.</p>
      <div class="toolbar">
        <nav class="nav">
          <a href="/" class="active">Authority Tree</a>
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
      <div id="treeStack" class="stack-view"></div>
    </section>
    <aside class="detail-panel">
      <div class="meta">Selection</div>
      <h2 id="detailTitle">Overview</h2>
      <div id="detailType" class="detail-type">Root</div>
      <p id="detailSummary" class="detail-summary">Hover or click a branch to inspect case treatment, lineage codes, public notes, references, and linked authorities.</p>
      <div id="detailSignal" class="signal-panel empty-state">Treatment notes and short quotations appear here when a node carries them.</div>
      <div class="meta">Metrics</div>
      <ul id="metricList" class="data-list"><li class="empty">Choose a node to view metrics.</li></ul>
      <div class="meta">External Links</div>
      <ul id="linkList" class="data-list"><li class="empty">No node selected.</li></ul>
      <div class="meta">Lineage Paths</div>
      <ul id="lineageList" class="data-list"><li class="empty">No lineage path selected.</li></ul>
      <div class="meta">References</div>
      <ul id="referenceList" class="data-list"><li class="empty">No references attached.</li></ul>
      <div class="meta">Related Nodes</div>
      <ul id="neighborList" class="data-list"><li class="empty">No related nodes.</li></ul>
    </aside>
  </div>
  <script>
    const payload = __CASEMAP_DATA__;
    const nodes = payload.nodes || [];
    const edges = payload.edges || [];
    const nodeMap = new Map(nodes.map((node) => [node.id, node]));
    const adjacency = new Map(nodes.map((node) => [node.id, new Set()]));
    edges.forEach((edge) => {
      if (!adjacency.has(edge.source)) adjacency.set(edge.source, new Set());
      if (!adjacency.has(edge.target)) adjacency.set(edge.target, new Set());
      adjacency.get(edge.source).add(edge.target);
      adjacency.get(edge.target).add(edge.source);
    });

    const treeStack = document.getElementById("treeStack");
    const breadcrumbsEl = document.getElementById("breadcrumbs");
    const resultsEl = document.getElementById("results");
    const searchInput = document.getElementById("searchInput");
    const detailTitle = document.getElementById("detailTitle");
    const detailType = document.getElementById("detailType");
    const detailSummary = document.getElementById("detailSummary");
    const detailSignal = document.getElementById("detailSignal");
    const metricList = document.getElementById("metricList");
    const linkList = document.getElementById("linkList");
    const lineageList = document.getElementById("lineageList");
    const referenceList = document.getElementById("referenceList");
    const neighborList = document.getElementById("neighborList");

    const domains = nodes
      .filter((node) => node.type === "domain")
      .sort((left, right) => left.label.localeCompare(right.label));

    const lineages = (payload.meta.lineages || [])
      .map((lineage) => ({
        ...lineage,
        members: (lineage.members || []).filter((member) => nodeMap.has(member.node_id)),
      }))
      .sort((left, right) => left.title.localeCompare(right.title));

    const topicLineages = new Map();
    const lineageMap = new Map(lineages.map((lineage) => [lineage.id, lineage]));
    lineages.forEach((lineage) => {
      (lineage.topic_ids || []).forEach((topicId) => {
        const current = topicLineages.get(topicId) || [];
        current.push(lineage);
        topicLineages.set(topicId, current);
      });
    });

    const rootNode = {
      id: "__root__",
      label: payload.meta.title || "Hong Kong Contract Law",
      type: "root",
      summary: "Top-level doctrinal overview. Choose a domain, then a topic, then an authority branch. The right panel shows the detail only when you hover or click.",
      metrics: {
        domains: domains.length,
        topics: nodes.filter((node) => node.type === "topic").length,
        authorities: nodes.filter((node) => node.type === "case" || node.type === "statute").length,
        lineages: payload.meta.curated_lineage_count || lineages.length,
      },
      links: [],
      references: [],
      lineage_memberships: [],
    };

    const state = {
      domainId: null,
      topicId: null,
      selectedNodeId: rootNode.id,
    };

    function escapeHtml(value) {
      return String(value || "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "\"": "&quot;",
        "'": "&#39;",
      }[char]));
    }

    function getNode(nodeId) {
      if (nodeId === rootNode.id) return rootNode;
      return nodeMap.get(nodeId) || null;
    }

    function labelForType(type) {
      const labels = {
        root: "Root",
        domain: "Ground",
        topic: "Sub-ground",
        case: "Case",
        statute: "Statute",
        source: "Source",
      };
      return labels[type] || type;
    }

    function statusClass(value) {
      return String(value || "relevant authority").toLowerCase().replace(/[^a-z0-9]+/g, "-");
    }

    function sortByLabel(items) {
      return items.slice().sort((left, right) => left.label.localeCompare(right.label));
    }

    function neighborsByType(nodeId, type) {
      return sortByLabel(
        [...(adjacency.get(nodeId) || [])]
          .map((neighborId) => getNode(neighborId))
          .filter((node) => node && node.type === type)
      );
    }

    function childrenOfDomain(domainId) {
      return sortByLabel(
        edges
          .filter((edge) => edge.type === "contains" && edge.source === domainId)
          .map((edge) => getNode(edge.target))
          .filter(Boolean)
      );
    }

    function preferredTopicForNode(node) {
      if (!node || node.type === "root") return null;
      if (node.type === "topic") return node;
      const connectedTopics = neighborsByType(node.id, "topic");
      if (state.topicId && connectedTopics.some((topic) => topic.id === state.topicId)) {
        return getNode(state.topicId);
      }
      for (const membership of node.lineage_memberships || []) {
        for (const topicId of membership.topic_ids || []) {
          const topic = getNode(topicId);
          if (topic) return topic;
        }
      }
      return connectedTopics[0] || null;
    }

    function relatedLineagesForNode(node) {
      const lineageIds = new Set((node.lineage_memberships || []).map((membership) => membership.lineage_id));
      return [...lineageIds]
        .map((lineageId) => lineageMap.get(lineageId))
        .filter(Boolean)
        .sort((left, right) => left.title.localeCompare(right.title));
    }

    function setSelection(node) {
      if (!node) return;
      if (node.type === "root") {
        state.domainId = null;
        state.topicId = null;
        state.selectedNodeId = rootNode.id;
        return;
      }
      if (node.type === "domain") {
        state.domainId = node.id;
        state.topicId = null;
        state.selectedNodeId = node.id;
        return;
      }
      if (node.type === "topic") {
        state.domainId = node.domain_id || state.domainId;
        state.topicId = node.id;
        state.selectedNodeId = node.id;
        return;
      }
      const topic = preferredTopicForNode(node);
      if (topic) {
        state.topicId = topic.id;
        state.domainId = topic.domain_id || state.domainId;
      }
      state.selectedNodeId = node.id;
    }

    function makeSection(title, caption) {
      const section = document.createElement("section");
      section.className = "tree-section";
      const head = document.createElement("div");
      head.className = "section-head";
      head.innerHTML = `<h3 class="section-title">${escapeHtml(title)}</h3><div class="section-caption">${escapeHtml(caption || "")}</div>`;
      section.appendChild(head);
      return section;
    }

    function bindNodeInteractions(element, node) {
      element.addEventListener("mouseenter", () => renderDetails(node, true));
      element.addEventListener("mouseleave", () => renderDetails(getNode(state.selectedNodeId) || rootNode));
      element.addEventListener("click", () => {
        setSelection(node);
        render();
      });
    }

    function createNodeCard(node, extra = {}) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `tree-node ${node.type}`;
      if (state.selectedNodeId === node.id) {
        button.classList.add("active");
      }

      const chips = [];
      if (extra.countLabel) chips.push(`<span class="micro-chip">${escapeHtml(extra.countLabel)}</span>`);
      if (extra.code) chips.push(`<span class="micro-chip code">${escapeHtml(extra.code)}</span>`);
      if (extra.treatment) chips.push(`<span class="signal-chip ${statusClass(extra.treatment)}">${escapeHtml(extra.treatment)}</span>`);

      button.title = extra.preview || node.summary || node.label;
      button.innerHTML = `
        <span class="node-kicker">${escapeHtml(extra.kicker || labelForType(node.type))}</span>
        <span class="node-name">${escapeHtml(node.label)}</span>
        <span class="chip-row">${chips.join("")}</span>
      `;
      bindNodeInteractions(button, node);
      return button;
    }

    function fillList(listEl, items, emptyText) {
      listEl.innerHTML = "";
      if (!items.length) {
        listEl.innerHTML = `<li class="empty">${escapeHtml(emptyText)}</li>`;
        return;
      }
      items.forEach((item) => listEl.appendChild(item));
    }

    function renderDetails(node, preview = false) {
      const target = node || rootNode;
      const profile = target.case_profile || {};
      const memberships = target.lineage_memberships || [];

      detailTitle.textContent = target.label;
      detailType.textContent = preview ? `${labelForType(target.type)} Preview` : labelForType(target.type);
      detailSummary.textContent = profile.note || profile.quote || target.summary || "No summary available.";

      const signalBits = [];
      if (profile.treatment) {
        signalBits.push(`<span class="signal-chip ${statusClass(profile.treatment)}">${escapeHtml(profile.treatment)}</span>`);
      }
      if (profile.code) {
        signalBits.push(`<span class="signal-chip code">${escapeHtml(profile.code)}</span>`);
      }
      if (memberships.length) {
        signalBits.push(`<span class="signal-chip code">${memberships.length} lineage path(s)</span>`);
      }
      const noteText = profile.quote || profile.note || "";
      if (!signalBits.length && !noteText) {
        detailSignal.className = "signal-panel empty-state";
        detailSignal.textContent = "Hover or click a node to surface treatment notes, short quotations, and lineage codes.";
      } else {
        detailSignal.className = "signal-panel";
        detailSignal.innerHTML = `${signalBits.join("")}${noteText ? `<p>${escapeHtml(noteText)}</p>` : ""}`;
      }

      const metricItems = [];
      const degree = target.id === rootNode.id ? 0 : (target.degree || 0);
      const degreeItem = document.createElement("li");
      degreeItem.textContent = `degree: ${degree}`;
      metricItems.push(degreeItem);
      Object.entries(target.metrics || {}).forEach(([key, value]) => {
        const item = document.createElement("li");
        item.textContent = `${key}: ${value}`;
        metricItems.push(item);
      });
      fillList(metricList, metricItems, "No extra metrics available.");

      const linkItems = (target.links || []).map((link) => {
        const item = document.createElement("li");
        item.innerHTML = `<a href="${escapeHtml(link.url)}" target="_blank" rel="noreferrer">${escapeHtml(link.label)}</a>`;
        return item;
      });
      fillList(linkList, linkItems, "No external links available.");

      const lineageItems = [];
      if (target.id === rootNode.id) {
        Object.entries(payload.meta.lineage_codes || {}).forEach(([code, meaning]) => {
          const item = document.createElement("li");
          item.innerHTML = `<div class="list-meta">${escapeHtml(code)}</div><div>${escapeHtml(meaning)}</div>`;
          lineageItems.push(item);
        });
      } else {
        memberships.forEach((membership) => {
          const item = document.createElement("li");
          item.className = "clickable";
          item.innerHTML = `
            <div class="list-meta">${escapeHtml(membership.code || "lineage")} · ${escapeHtml(membership.treatment || "authority")}</div>
            <strong>${escapeHtml(membership.lineage_title)}</strong>
            <div>${escapeHtml(membership.note || "No additional note attached.")}</div>
          `;
          item.addEventListener("click", () => {
            const topicId = (membership.topic_ids || [])[0];
            if (topicId && getNode(topicId)) {
              setSelection(getNode(topicId));
              render();
            }
          });
          lineageItems.push(item);
        });
      }
      fillList(lineageList, lineageItems, "No lineage path attached.");

      const referenceItems = (target.references || []).map((reference) => {
        const item = document.createElement("li");
        item.innerHTML = `
          <div class="list-meta">${escapeHtml(reference.source_label)} · ${escapeHtml(reference.location)}</div>
          <div>${escapeHtml(reference.snippet)}</div>
        `;
        return item;
      });
      fillList(referenceList, referenceItems, "No references attached.");

      const neighborItems = [];
      if (target.id !== rootNode.id) {
        neighborsByType(target.id, "topic")
          .concat(neighborsByType(target.id, "case"))
          .concat(neighborsByType(target.id, "statute"))
          .concat(neighborsByType(target.id, "source"))
          .filter((neighbor, index, values) => values.findIndex((item) => item.id === neighbor.id) === index)
          .slice(0, 14)
          .forEach((neighbor) => {
            const item = document.createElement("li");
            item.className = "clickable";
            item.innerHTML = `<div class="list-meta">${escapeHtml(labelForType(neighbor.type))}</div><strong>${escapeHtml(neighbor.label)}</strong>`;
            bindNodeInteractions(item, neighbor);
            neighborItems.push(item);
          });
      }
      fillList(neighborList, neighborItems, "No related nodes.");
    }

    function renderBreadcrumbs() {
      breadcrumbsEl.innerHTML = "";
      const trail = [rootNode];
      if (state.domainId) trail.push(getNode(state.domainId));
      if (state.topicId) trail.push(getNode(state.topicId));
      const selectedNode = getNode(state.selectedNodeId);
      if (
        selectedNode &&
        selectedNode.id !== rootNode.id &&
        selectedNode.id !== state.domainId &&
        selectedNode.id !== state.topicId
      ) {
        trail.push(selectedNode);
      }

      trail.filter(Boolean).forEach((node) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "crumb";
        button.textContent = node.label;
        bindNodeInteractions(button, node);
        breadcrumbsEl.appendChild(button);
      });
    }

    function renderResults(query) {
      const lowered = query.trim().toLowerCase();
      resultsEl.innerHTML = "";
      if (!lowered) return;
      const matches = nodes
        .filter((node) => `${node.label} ${node.summary || ""}`.toLowerCase().includes(lowered))
        .sort((left, right) => (right.degree || 0) - (left.degree || 0))
        .slice(0, 12);

      if (!matches.length) {
        resultsEl.innerHTML = "<div class='empty'>No matching nodes.</div>";
        return;
      }

      matches.forEach((node) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "result-pill";
        button.textContent = `${node.label} · ${labelForType(node.type)}`;
        bindNodeInteractions(button, node);
        resultsEl.appendChild(button);
      });
    }

    function renderAuthorityLineage(lineage) {
      const panel = document.createElement("article");
      panel.className = "lineage-panel";
      panel.innerHTML = `
        <div class="branch-head">
          <h3>${escapeHtml(lineage.title)}</h3>
          <div class="branch-meta">${escapeHtml((lineage.codes || []).join(" · ") || "authority path")}</div>
        </div>
      `;
      const track = document.createElement("div");
      track.className = "lineage-track";
      (lineage.members || []).forEach((member) => {
        const node = getNode(member.node_id);
        if (!node) return;
        const step = document.createElement("div");
        step.className = "lineage-step";
        step.appendChild(
          createNodeCard(node, {
            kicker: member.type === "statute" ? "statute" : "case",
            code: member.code,
            treatment: member.treatment,
            preview: member.note || node.summary,
          })
        );
        track.appendChild(step);
      });
      panel.appendChild(track);
      return panel;
    }

    function renderAuxPanel(title, caption, items, cardBuilder) {
      if (!items.length) return null;
      const panel = document.createElement("article");
      panel.className = "aux-panel";
      panel.innerHTML = `
        <div class="branch-head">
          <h3>${escapeHtml(title)}</h3>
          <div class="branch-meta">${escapeHtml(caption)}</div>
        </div>
      `;
      const grid = document.createElement("div");
      grid.className = "aux-grid";
      items.forEach((item) => grid.appendChild(cardBuilder(item)));
      panel.appendChild(grid);
      return panel;
    }

    function renderTree() {
      treeStack.innerHTML = "";

      const rootSection = makeSection("Overview", "start here");
      const rootWrap = document.createElement("div");
      rootWrap.className = "root-wrap";
      rootWrap.appendChild(
        createNodeCard(rootNode, {
          kicker: "root",
          countLabel: `${domains.length} domains · ${lineages.length} lineages`,
          preview: rootNode.summary,
        })
      );
      rootSection.appendChild(rootWrap);
      treeStack.appendChild(rootSection);

      const domainSection = makeSection("Doctrinal Grounds", "top-level branches");
      const domainRow = document.createElement("div");
      domainRow.className = "domain-row";
      domains.forEach((domain) => {
        domainRow.appendChild(
          createNodeCard(domain, {
            countLabel: `${childrenOfDomain(domain.id).length} topics`,
          })
        );
      });
      domainSection.appendChild(domainRow);
      treeStack.appendChild(domainSection);

      if (!state.domainId || !getNode(state.domainId)) return;
      const selectedDomain = getNode(state.domainId);
      const topics = childrenOfDomain(selectedDomain.id);
      const topicSection = makeSection(selectedDomain.label, "sub-grounds");
      const topicGrid = document.createElement("div");
      topicGrid.className = "topic-grid";
      topics.forEach((topic) => {
        const topicCases = neighborsByType(topic.id, "case").length;
        const topicStatutes = neighborsByType(topic.id, "statute").length;
        const topicLineageCount = (topicLineages.get(topic.id) || []).length;
        topicGrid.appendChild(
          createNodeCard(topic, {
            countLabel: `${topicCases} cases · ${topicStatutes} statutes · ${topicLineageCount} lineages`,
          })
        );
      });
      topicSection.appendChild(topicGrid);
      treeStack.appendChild(topicSection);

      if (!state.topicId || !getNode(state.topicId)) return;
      const selectedTopic = getNode(state.topicId);
      const cases = neighborsByType(selectedTopic.id, "case");
      const statutes = neighborsByType(selectedTopic.id, "statute");
      const sources = neighborsByType(selectedTopic.id, "source");
      const matchedLineages = (topicLineages.get(selectedTopic.id) || []).slice().sort((left, right) => left.title.localeCompare(right.title));
      const lineageNodeIds = new Set(
        matchedLineages.flatMap((lineage) => (lineage.members || []).map((member) => member.node_id))
      );

      const authoritySection = makeSection(selectedTopic.label, "authority branches");
      const authorityStack = document.createElement("div");
      authorityStack.className = "authority-stack";

      if (matchedLineages.length) {
        const lineageGrid = document.createElement("div");
        lineageGrid.className = "lineage-grid";
        matchedLineages.forEach((lineage) => lineageGrid.appendChild(renderAuthorityLineage(lineage)));
        authorityStack.appendChild(lineageGrid);
      }

      const auxPanels = [];
      const extraCases = cases.filter((node) => !lineageNodeIds.has(node.id));
      const extraStatutes = statutes.filter((node) => !lineageNodeIds.has(node.id));
      const extraSources = sources;

      const otherCasesPanel = renderAuxPanel("Other Cases", "same topic but outside the curated lineage", extraCases, (caseNode) =>
        createNodeCard(caseNode, {
          kicker: "case",
          treatment: (caseNode.case_profile || {}).treatment,
          code: (caseNode.case_profile || {}).code,
        })
      );
      if (otherCasesPanel) auxPanels.push(otherCasesPanel);

      const statutePanel = renderAuxPanel("Statutes", "public primary materials", extraStatutes, (statuteNode) =>
        createNodeCard(statuteNode, { kicker: "statute" })
      );
      if (statutePanel) auxPanels.push(statutePanel);

      const sourcePanel = renderAuxPanel("Sources", "supporting books, notes, and structure", extraSources, (sourceNode) =>
        createNodeCard(sourceNode, { kicker: "source" })
      );
      if (sourcePanel) auxPanels.push(sourcePanel);

      if (auxPanels.length) {
        const auxGrid = document.createElement("div");
        auxGrid.className = "lineage-grid";
        auxPanels.forEach((panel) => auxGrid.appendChild(panel));
        authorityStack.appendChild(auxGrid);
      }

      authoritySection.appendChild(authorityStack);
      treeStack.appendChild(authoritySection);

      const selectedNode = getNode(state.selectedNodeId);
      if (!selectedNode || selectedNode.id === rootNode.id) return;
      const focusedLineages = relatedLineagesForNode(selectedNode).filter((lineage) =>
        (lineage.topic_ids || []).includes(selectedTopic.id) || selectedNode.id === state.selectedNodeId
      );
      if (!focusedLineages.length && (selectedNode.type === "domain" || selectedNode.type === "topic")) return;

      const focusSection = makeSection("Focused Authority Path", "zoomed branch");
      if (focusedLineages.length) {
        const focusGrid = document.createElement("div");
        focusGrid.className = "lineage-grid";
        focusedLineages.forEach((lineage) => focusGrid.appendChild(renderAuthorityLineage(lineage)));
        focusSection.appendChild(focusGrid);
      } else {
        const relatedPanel = renderAuxPanel(
          "Related Authorities",
          "same branch connections",
          neighborsByType(selectedNode.id, "case")
            .concat(neighborsByType(selectedNode.id, "statute"))
            .filter((neighbor, index, values) => values.findIndex((item) => item.id === neighbor.id) === index)
            .slice(0, 12),
          (neighbor) =>
            createNodeCard(neighbor, {
              kicker: labelForType(neighbor.type).toLowerCase(),
              treatment: (neighbor.case_profile || {}).treatment,
              code: (neighbor.case_profile || {}).code,
            })
        );
        if (relatedPanel) focusSection.appendChild(relatedPanel);
      }
      treeStack.appendChild(focusSection);
    }

    function render() {
      renderBreadcrumbs();
      renderTree();
      renderDetails(getNode(state.selectedNodeId) || rootNode);
      renderResults(searchInput.value);
    }

    searchInput.addEventListener("input", (event) => renderResults(event.target.value));
    render();
  </script>
</body>
</html>
"""
    return html.replace("__CASEMAP_DATA__", data)
