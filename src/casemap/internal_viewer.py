from __future__ import annotations


def render_internal_graph_explorer(title: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      --bg: #f5f0e4;
      --panel: rgba(255, 250, 242, 0.9);
      --ink: #1f2328;
      --muted: #6a665e;
      --line: rgba(31, 35, 40, 0.12);
      --accent: #8f3b1b;
      --soft: #d9cbb2;
      --case: #5b7f63;
      --topic: #ba8b2e;
      --lineage: #205072;
    }}

    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Georgia", "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(186, 139, 46, 0.15), transparent 28%),
        radial-gradient(circle at top right, rgba(32, 80, 114, 0.14), transparent 24%),
        linear-gradient(180deg, #f8f3ea 0%, var(--bg) 100%);
    }}
    .shell {{
      display: grid;
      grid-template-columns: 320px minmax(0, 1fr) 420px;
      min-height: 100vh;
    }}
    .panel {{
      border-right: 1px solid var(--line);
      background: var(--panel);
      padding: 24px 20px;
      overflow-y: auto;
    }}
    .canvas {{
      padding: 28px;
      overflow-y: auto;
    }}
    .meta {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }}
    h1, h2, h3 {{ margin: 0 0 12px; }}
    .query {{
      display: grid;
      gap: 10px;
      margin: 18px 0 24px;
    }}
    input, button {{
      font: inherit;
      border-radius: 14px;
      border: 1px solid var(--line);
      padding: 12px 14px;
      background: rgba(255, 255, 255, 0.72);
      color: var(--ink);
    }}
    button {{
      cursor: pointer;
      background: linear-gradient(180deg, rgba(143, 59, 27, 0.96), rgba(124, 45, 18, 0.96));
      color: white;
      border: 0;
    }}
    .section {{
      margin-bottom: 24px;
    }}
    .tree-item, .card, .edge {{
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.58);
      border-radius: 16px;
      padding: 12px 14px;
      margin-bottom: 10px;
    }}
    .chip {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      background: rgba(31, 35, 40, 0.08);
      color: var(--muted);
      margin-right: 6px;
      margin-bottom: 6px;
    }}
    .chip.case {{ background: rgba(91, 127, 99, 0.15); color: var(--case); }}
    .chip.topic {{ background: rgba(186, 139, 46, 0.15); color: var(--topic); }}
    .chip.lineage {{ background: rgba(32, 80, 114, 0.12); color: var(--lineage); }}
    .small {{ color: var(--muted); font-size: 13px; line-height: 1.45; }}
    .list {{ display: grid; gap: 10px; }}
    .empty {{ color: var(--muted); font-style: italic; }}
    @media (max-width: 1200px) {{
      .shell {{ grid-template-columns: 1fr; }}
      .panel {{ border-right: 0; border-bottom: 1px solid var(--line); }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <aside class="panel">
      <div class="meta">Internal Explorer</div>
      <h1>{title}</h1>
      <p class="small">This explorer fetches tree, topic, case, and focus-graph data from API endpoints instead of loading the full graph into the browser.</p>
      <form id="queryForm" class="query">
        <input id="queryInput" type="search" placeholder="Ask about implied terms, penalties, vacant possession...">
        <button type="submit">Run Graph Query</button>
      </form>
      <div class="section">
        <div class="meta">Modules</div>
        <div id="treePanel" class="list"><div class="empty">Loading tree...</div></div>
      </div>
    </aside>
    <main class="canvas">
      <div class="section">
        <div class="meta">Focus Graph</div>
        <h2 id="focusTitle">Select a topic or case</h2>
        <div id="focusSummary" class="small">The focus graph is fetched on demand.</div>
      </div>
      <div class="section">
        <div class="meta">Nodes</div>
        <div id="graphNodes" class="list"><div class="empty">No graph loaded.</div></div>
      </div>
      <div class="section">
        <div class="meta">Edges</div>
        <div id="graphEdges" class="list"><div class="empty">No graph loaded.</div></div>
      </div>
    </main>
    <aside class="panel">
      <div class="meta">Details</div>
      <h2 id="detailTitle">Awaiting selection</h2>
      <div id="detailBody" class="small">Pick a topic to inspect lead cases and lineages, or run a graph query.</div>
    </aside>
  </div>
  <script>
    const treePanel = document.getElementById("treePanel");
    const focusTitle = document.getElementById("focusTitle");
    const focusSummary = document.getElementById("focusSummary");
    const graphNodes = document.getElementById("graphNodes");
    const graphEdges = document.getElementById("graphEdges");
    const detailTitle = document.getElementById("detailTitle");
    const detailBody = document.getElementById("detailBody");
    const queryForm = document.getElementById("queryForm");
    const queryInput = document.getElementById("queryInput");

    function escapeHtml(value) {{
      return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }}

    function renderFocusGraph(payload) {{
      focusTitle.textContent = payload.focus;
      focusSummary.textContent = `${{payload.nodes.length}} nodes, ${{payload.edges.length}} edges, facets: ` + Object.entries(payload.facets || {{}}).map(([key, count]) => `${{key}} ${{count}}`).join(" · ");
      graphNodes.innerHTML = "";
      payload.nodes.forEach((node) => {{
        const el = document.createElement("div");
        el.className = "card";
        el.innerHTML = `<div class="chip ${{node.type === "Case" ? "case" : node.type === "Topic" ? "topic" : node.type === "AuthorityLineage" ? "lineage" : ""}}">${{escapeHtml(node.type)}}</div><strong>${{escapeHtml(node.label || node.case_name || node.title || node.id)}}</strong><div class="small">${{escapeHtml(node.summary || node.summary_en || node.path || node.neutral_citation || "")}}</div>`;
        if (node.type === "Case") {{
          el.addEventListener("click", () => loadCase(node.id));
        }}
        if (node.type === "Topic") {{
          el.addEventListener("click", () => loadTopic(node.id));
        }}
        graphNodes.appendChild(el);
      }});
      graphEdges.innerHTML = "";
      payload.edges.forEach((edge) => {{
        const el = document.createElement("div");
        el.className = "edge";
        el.innerHTML = `<strong>${{escapeHtml(edge.type)}}</strong><div class="small">${{escapeHtml(edge.source)}} → ${{escapeHtml(edge.target)}}</div>`;
        graphEdges.appendChild(el);
      }});
    }}

    async function loadFocus(id, depth = 1) {{
      const response = await fetch(`/api/graph/focus?id=${{encodeURIComponent(id)}}&depth=${{depth}}`);
      const payload = await response.json();
      renderFocusGraph(payload);
    }}

    async function loadTopic(topicId) {{
      const response = await fetch(`/api/topic/${{encodeURIComponent(topicId)}}`);
      const payload = await response.json();
      detailTitle.textContent = payload.topic.label;
      const leadCases = (payload.lead_cases || []).map((card) => `
        <div class="card">
          <div class="chip case">${{escapeHtml(card.metadata.court_code || "CASE")}}</div>
          <strong>${{escapeHtml(card.metadata.case_name)}}</strong>
          <div class="small">${{escapeHtml(card.metadata.neutral_citation || card.metadata.summary_en || "")}}</div>
        </div>
      `).join("");
      const lineages = (payload.lineages || []).map((lineage) => `
        <div class="card">
          <div class="chip lineage">Lineage</div>
          <strong>${{escapeHtml(lineage.title)}}</strong>
          <div class="small">${{escapeHtml((lineage.codes || []).join(" · "))}}</div>
        </div>
      `).join("");
      detailBody.innerHTML = `
        <div class="small">${{escapeHtml(payload.topic.summary || payload.topic.path || "")}}</div>
        <h3>Lead Cases</h3>
        ${{leadCases || "<div class='empty'>No lead cases mapped.</div>"}}
        <h3>Lineages</h3>
        ${{lineages || "<div class='empty'>No lineages attached.</div>"}}
      `;
      renderFocusGraph(payload.focus_graph);
    }}

    async function loadCase(caseId) {{
      const response = await fetch(`/api/case/${{encodeURIComponent(caseId)}}`);
      const payload = await response.json();
      detailTitle.textContent = payload.metadata.case_name;
      const principles = (payload.principles || []).map((principle) => `
        <div class="card">
          <div class="chip case">${{escapeHtml(principle.paragraph_span || "Principle")}}</div>
          <strong>${{escapeHtml(principle.label_en)}}</strong>
          <div class="small">${{escapeHtml(principle.statement_en)}}</div>
        </div>
      `).join("");
      const relationships = (payload.relationships || []).map((relationship) => `
        <div class="card">
          <div class="chip">${{escapeHtml(relationship.type)}}</div>
          <strong>${{escapeHtml(relationship.target_label)}}</strong>
          <div class="small">${{escapeHtml(relationship.explanation || relationship.direction)}}</div>
        </div>
      `).join("");
      detailBody.innerHTML = `
        <div class="small">${{escapeHtml(payload.metadata.neutral_citation || "")}} · ${{escapeHtml(payload.metadata.court_name || "")}}</div>
        <div class="small">${{escapeHtml(payload.metadata.summary_en || "")}}</div>
        <h3>Principles</h3>
        ${{principles || "<div class='empty'>No enriched principles for this case.</div>"}}
        <h3>Relationships</h3>
        ${{relationships || "<div class='empty'>No typed relationships found.</div>"}}
      `;
      await loadFocus(caseId, 1);
    }}

    async function loadTree() {{
      const response = await fetch("/api/tree");
      const payload = await response.json();
      treePanel.innerHTML = "";
      payload.modules.forEach((module) => {{
        const moduleEl = document.createElement("div");
        moduleEl.className = "tree-item";
        const subgrounds = (module.subgrounds || []).map((subground) => `
          <div class="card">
            <strong>${{escapeHtml(subground.label_en)}}</strong>
            <div class="small">${{subground.metrics.topics}} topics · ${{subground.metrics.cases}} cases</div>
            <div class="small">${{(subground.topic_ids || []).map((topicId) => `<a href="#" data-topic="${{escapeHtml(topicId)}}">${{escapeHtml(topicId.split(":").slice(-1)[0].replaceAll("_", " "))}}</a>`).join("<br>") || ""}}</div>
          </div>
        `).join("");
        moduleEl.innerHTML = `<strong>${{escapeHtml(module.label_en)}}</strong><div class="small">${{module.metrics.cases}} cases · ${{module.metrics.lineages}} lineages</div>${{subgrounds}}`;
        treePanel.appendChild(moduleEl);
      }});
      treePanel.querySelectorAll("[data-topic]").forEach((link) => {{
        link.addEventListener("click", (event) => {{
          event.preventDefault();
          loadTopic(link.dataset.topic);
        }});
      }});
    }}

    queryForm.addEventListener("submit", async (event) => {{
      event.preventDefault();
      const question = queryInput.value.trim();
      if (!question) return;
      const response = await fetch("/api/query", {{
        method: "POST",
        headers: {{"Content-Type": "application/json"}},
        body: JSON.stringify({{question}})
      }});
      const payload = await response.json();
      detailTitle.textContent = "Graph Query";
      detailBody.innerHTML = `
        <div class="small">${{escapeHtml(payload.answer || "")}}</div>
        <h3>Sources</h3>
        ${{
          (payload.sources || []).map((source) => `
            <div class="card">
              <strong>${{escapeHtml(source.case_name)}}</strong>
              <div class="small">${{escapeHtml(source.neutral_citation || source.paragraph_span || "")}}</div>
            </div>
          `).join("") || "<div class='empty'>No sources returned.</div>"
        }}
      `;
      const focusId = payload.supporting_nodes && payload.supporting_nodes.length ? payload.supporting_nodes[0].id : null;
      if (focusId) {{
        loadFocus(focusId, 1);
      }}
    }});

    loadTree();
  </script>
</body>
</html>
"""
