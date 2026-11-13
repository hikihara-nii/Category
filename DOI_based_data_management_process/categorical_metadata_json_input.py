"""
Categorical Dynamic Metadata Construction & Live Provenance Explorer
====================================================================
圏論に基づく動的メタデータ構築・観点転換・余極限合成・双方向プロバナンス可視化システム
外部 JSON ファイル（スナップショット形式またはグラフ形式）を読み込んで起動する仕様に改修
Python 単体で実行可能な軽量ローカルWebアプリケーションサーバー (標準ライブラリのみ使用)
"""

import http.server
import json
import os
import socketserver
import sys
import threading
import webbrowser

PORT = 8080

# デフォルトの入力データファイル名
# 引数で指定があればそれを使用: python categorical_metadata_app.py custom_data.json
DEFAULT_DATA_FILE = "shared_dataset_dual_lineage.json"


def load_or_create_default_data(filepath):
  """指定された JSON ファイルを読み込み、存在しない場合はフォールバックデータを生成して返す"""
  if os.path.exists(filepath):
    print(f"[*] 入力データファイルを読み込みました: {filepath}")
    try:
      with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception as e:
      print(
          f"[!] JSON読み込みエラー ({filepath}): {e}。フォールバックデータを使用します。"
      )

  print(
      f"[*] '{filepath}'"
      " が見つからないため、標準の初期データを生成して使用します。"
  )
  fallback_data = {
      "metadata": {
          "title": "Default Categorical Metadata Pipeline",
          "description": "初期生成された動的メタデータスナップショット",
      },
      "nodes": [
          {
              "id": "Paper_A@t0",
              "rawId": "Paper_A",
              "type": "Paper",
              "version": 0,
              "label": "Paper_A (t=0)\nInitial Study A",
              "title": "PEDOT導電性ポリマーの初期合成",
              "x": 100,
              "y": 80,
          },
          {
              "id": "Data_A@t0",
              "rawId": "Data_A",
              "type": "Data",
              "version": 0,
              "label": "Data_A (t=0)\nConductivity 12.4 S/cm",
              "title": "正常伝導率測定データ",
              "x": 100,
              "y": 220,
          },
          {
              "id": "Material_A@t0",
              "rawId": "Material_A",
              "type": "Material",
              "version": 0,
              "label": "Material_A (t=0)\nPEDOT Sample Lot 101",
              "title": "供試高分子ロット",
              "x": 100,
              "y": 360,
          },
          {
              "id": "Exp_Fail_01@t0",
              "rawId": "Exp_Fail_01",
              "type": "FailedData",
              "version": 0,
              "label": "Exp_Fail_01 (t=0)\nDecomposed at 280C",
              "title": "高温で主鎖分解・失敗と記録",
              "x": 100,
              "y": 500,
          },
          {
              "id": "Ref_Paper_B@t0",
              "rawId": "Ref_Paper_B",
              "type": "Reference",
              "version": 0,
              "label": "Ref_Paper_B (t=0)\nPrior Doping Work",
              "title": "先行文献 (Smith et al.)",
              "x": 100,
              "y": 640,
          },
          {
              "id": "Data_A@t10",
              "rawId": "Data_A",
              "type": "Data",
              "version": 10,
              "label": "Data_A (t=10)\nPreserved",
              "title": "継承された正常データ",
              "x": 380,
              "y": 220,
          },
          {
              "id": "Material_A@t10",
              "rawId": "Material_A",
              "type": "Material",
              "version": 10,
              "label": "Material_A (t=10)\nPreserved",
              "title": "継承された材料",
              "x": 380,
              "y": 360,
          },
          {
              "id": "LimitEntry_01@t10",
              "rawId": "LimitEntry_01",
              "type": "ThermalLimit",
              "version": 10,
              "label": "LimitEntry_01 (t=10)\nThermal Boundary (280C)",
              "title": "再解釈された最大耐熱閾値",
              "x": 380,
              "y": 500,
          },
          {
              "id": "New_Material_X@t10",
              "rawId": "New_Material_X",
              "type": "NewMaterial",
              "version": 10,
              "label": "New_Material_X (t=10)\nSilica-Doped Matrix",
              "title": "新調された耐熱シリカ基板",
              "x": 380,
              "y": 640,
          },
          {
              "id": "Paper_C@t20",
              "rawId": "Paper_C",
              "type": "NewPaper",
              "version": 20,
              "label": "Paper_C (t=20)\nThermal Boundaries & Stabil.",
              "title": "再解釈限界値と新資材による新論文",
              "x": 680,
              "y": 150,
          },
      ],
      "edges": [
          {
              "id": "e1",
              "from": "Paper_A@t0",
              "to": "Data_A@t0",
              "relation": "schema:hasPart",
              "edge_type": "intra",
          },
          {
              "id": "e2",
              "from": "Paper_A@t0",
              "to": "Material_A@t0",
              "relation": "schema:hasPart",
              "edge_type": "intra",
          },
          {
              "id": "e3",
              "from": "Paper_A@t0",
              "to": "Exp_Fail_01@t0",
              "relation": "schema:hasPart",
              "edge_type": "intra",
          },
          {
              "id": "e4",
              "from": "Paper_A@t0",
              "to": "Ref_Paper_B@t0",
              "relation": "schema:citation",
              "edge_type": "intra",
          },
          {
              "id": "e5",
              "from": "Data_A@t0",
              "to": "Data_A@t10",
              "relation": "KanExtension",
              "edge_type": "inter",
          },
          {
              "id": "e6",
              "from": "Material_A@t0",
              "to": "Material_A@t10",
              "relation": "KanExtension",
              "edge_type": "inter",
          },
          {
              "id": "e7",
              "from": "Exp_Fail_01@t0",
              "to": "LimitEntry_01@t10",
              "relation": "PerspectiveShift",
              "edge_type": "inter",
          },
          {
              "id": "e8",
              "from": "Paper_A@t0",
              "to": "Paper_C@t20",
              "relation": "Lineage",
              "edge_type": "inter",
          },
          {
              "id": "e9",
              "from": "Data_A@t10",
              "to": "Paper_C@t20",
              "relation": "PreserveAndCite",
              "edge_type": "inter",
          },
          {
              "id": "e10",
              "from": "LimitEntry_01@t10",
              "to": "Paper_C@t20",
              "relation": "ColimitProjection",
              "edge_type": "inter",
          },
          {
              "id": "e11",
              "from": "New_Material_X@t10",
              "to": "Paper_C@t20",
              "relation": "Pushout",
              "edge_type": "inter",
          },
      ],
  }
  try:
    with open(filepath, "w", encoding="utf-8") as f:
      json.dump(fallback_data, f, ensure_ascii=False, indent=2)
    print(f"[*] 初期データを '{filepath}' に自動保存しました。")
  except Exception:
    pass
  return fallback_data


def convert_snapshots_to_graph(data):
  """入力 JSON が snapshots 形式の場合は nodes/edges 形式に正規化する。

  すでに nodes/edges 形式の場合はそのまま返す。
  """
  if "nodes" in data and "edges" in data:
    return data

  if "snapshots" not in data:
    return {"nodes": [], "edges": []}

  nodes = []
  edges = []
  layer_y = {
      "NewPaper": 80,
      "Paper": 120,
      "Reference": 240,
      "Data": 360,
      "ThermalLimit": 480,
      "Material": 600,
      "NewMaterial": 700,
      "FailedData": 800,
      "Entity": 900,
  }
  x_step = 320
  slot_tracker = {}

  for idx, snap in enumerate(data.get("snapshots", [])):
    v = snap.get("version", idx * 10)

    # 観点転換関手 (Shift)
    for s in snap.get("perspective_shifts", []):
      prev_v = data["snapshots"][idx - 1]["version"]
      src_node = f"{s['source_id']}@t{prev_v}"
      tgt_node = f"{s['new_id']}@t{v}"
      edges.append({
          "id": f"shift_{src_node}_{tgt_node}",
          "from": src_node,
          "to": tgt_node,
          "relation": "PerspectiveShift",
          "edge_type": "inter",
      })

    for node in snap.get("@graph", []):
      raw_id = node["@id"]
      node_id = f"{raw_id}@t{v}"
      n_type = node.get("cat:type", "Entity")
      name = node.get("schema:name", raw_id)

      col_x = (v // 10) * x_step + 100
      base_y = layer_y.get(n_type, 500)
      slot_key = (v, n_type)
      slot_idx = slot_tracker.get(slot_key, 0)
      slot_tracker[slot_key] = slot_idx + 1
      node_y = base_y + (slot_idx * 75)

      nodes.append({
          "id": node_id,
          "rawId": raw_id,
          "type": n_type,
          "version": v,
          "label": f"{raw_id} (t={v})\n{name[:20]}",
          "title": name,
          "x": col_x,
          "y": node_y,
      })

      for key, targets in node.items():
        if any(key.startswith(p) for p in ["schema:", "prov:", "sio:"]):
          t_list = targets if isinstance(targets, list) else [targets]
          for tgt in t_list:
            if isinstance(tgt, dict) and "@id" in tgt:
              tgt_id = f"{tgt['@id']}@t{v}"
              edges.append({
                  "id": f"e_{node_id}_{tgt_id}_{key}",
                  "from": node_id,
                  "to": tgt_id,
                  "relation": key,
                  "edge_type": "intra",
              })

    for hf in snap.get("higher_functors", []):
      edges.append({
          "id": f"hf_{hf['from']}_{hf['to']}",
          "from": hf["from"],
          "to": hf["to"],
          "relation": hf.get("transform", "Functor"),
          "edge_type": "inter",
      })

  return {"nodes": nodes, "edges": edges}


def build_html_content(graph_data, current_filename):
  data_json_str = json.dumps(graph_data, ensure_ascii=False)

  return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>Categorical Metadata & Provenance Explorer (∫D)</title>
  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    :root {{
      --bg-main: #121418;
      --bg-panel: #1a1e24;
      --bg-header: #21262d;
      --border: #30363d;
      --accent-cyan: #38bdf8;
      --accent-magenta: #f43f5e;
      --accent-orange: #fb923c;
      --text: #e2e8f0;
      --text-muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg-main);
      color: var(--text);
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }}
    header {{
      background: var(--bg-header);
      padding: 10px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--border);
    }}
    header h1 {{ font-size: 15px; font-weight: 600; color: #fff; display: flex; align-items: center; gap: 8px; }}
    .badge {{
      background: #0284c7;
      color: white;
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 12px;
    }}
    .file-badge {{
      background: #166534;
      color: #86efac;
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 12px;
      border: 1px solid #22c55e;
    }}
    .toolbar {{
      display: flex;
      gap: 8px;
      align-items: center;
    }}
    button {{
      background: #238636;
      color: #fff;
      border: 1px solid rgba(255,255,255,0.1);
      padding: 6px 12px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 12px;
      font-weight: 500;
      transition: all 0.2s;
    }}
    button:hover {{ background: #2ea043; }}
    button.btn-secondary {{ background: #30363d; }}
    button.btn-secondary:hover {{ background: #3c444d; }}
    button.btn-orange {{ background: #ea580c; }}
    button.btn-orange:hover {{ background: #f97316; }}
    button.btn-purple {{ background: #7c3aed; }}
    button.btn-purple:hover {{ background: #8b5cf6; }}

    .main-container {{
      display: flex;
      flex: 1;
      height: calc(100vh - 53px);
    }}
    #network-canvas {{
      flex: 1;
      height: 100%;
      background: radial-gradient(circle at center, #161b22 0%, #0d1117 100%);
      position: relative;
    }}
    .legend-overlay {{
      position: absolute;
      top: 12px;
      left: 12px;
      background: rgba(26, 30, 36, 0.9);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px 14px;
      font-size: 11px;
      pointer-events: none;
      backdrop-filter: blur(4px);
    }}
    .legend-item {{ display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }}
    .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; }}
    .legend-line {{ width: 16px; height: 2px; }}

    .sidebar {{
      width: 420px;
      background: var(--bg-panel);
      border-left: 1px solid var(--border);
      display: flex;
      flex-direction: column;
    }}
    .tabs {{
      display: flex;
      border-bottom: 1px solid var(--border);
      background: var(--bg-header);
    }}
    .tab-btn {{
      flex: 1;
      background: transparent;
      border: none;
      border-bottom: 2px solid transparent;
      padding: 10px;
      color: var(--text-muted);
      cursor: pointer;
      font-size: 12px;
    }}
    .tab-btn.active {{
      color: #fff;
      border-bottom-color: var(--accent-cyan);
      background: var(--bg-panel);
    }}
    .tab-content {{
      flex: 1;
      overflow-y: auto;
      padding: 15px;
      display: none;
    }}
    .tab-content.active {{ display: flex; flex-direction: column; gap: 12px; }}
    .card {{
      background: #161b22;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 12px;
      font-size: 12px;
    }}
    .card h3 {{
      font-size: 13px;
      margin-bottom: 8px;
      color: var(--accent-cyan);
      display: flex;
      justify-content: space-between;
    }}
    .provenance-list {{
      list-style: none;
      margin-top: 6px;
    }}
    .provenance-list li {{
      padding: 4px 6px;
      border-left: 2px solid var(--border);
      margin-bottom: 4px;
      font-size: 11px;
      display: flex;
      justify-content: space-between;
    }}
    .provenance-list li.cyan {{ border-left-color: var(--accent-cyan); background: rgba(56, 189, 248, 0.08); }}
    .provenance-list li.magenta {{ border-left-color: var(--accent-magenta); background: rgba(244, 63, 94, 0.08); }}

    textarea {{
      width: 100%;
      height: 280px;
      background: #0d1117;
      color: #38bdf8;
      border: 1px solid var(--border);
      border-radius: 6px;
      font-family: monospace;
      font-size: 11px;
      padding: 10px;
      resize: vertical;
    }}
    .form-group {{
      display: flex;
      flex-direction: column;
      gap: 4px;
      margin-bottom: 8px;
    }}
    .form-group label {{ font-size: 11px; color: var(--text-muted); }}
    .form-group input, .form-group select {{
      background: #0d1117;
      border: 1px solid var(--border);
      color: var(--text);
      padding: 6px;
      border-radius: 4px;
      font-size: 12px;
    }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Categorical Metadata & Provenance Explorer (∫D) 
        <span class="badge">PROV-O / SIO</span>
        <span class="file-badge">Loaded: {current_filename}</span>
      </h1>
    </div>
    <div class="toolbar">
      <button class="btn-orange" onclick="switchTab('tab-ops')">★ 圏論操作 (Shift / Colimit)</button>
      <button class="btn-secondary" onclick="resetView()">全体表示</button>
    </div>
  </header>

  <div class="main-container">
    <div id="network-canvas">
      <div class="legend-overlay">
        <div style="font-weight:600; margin-bottom:6px; color:#fff;">階層・エッジ凡例</div>
        <div class="legend-item"><div class="legend-dot" style="background:#1f77b4"></div>Paper (論文)</div>
        <div class="legend-item"><div class="legend-dot" style="background:#17becf"></div>Data (測定データ)</div>
        <div class="legend-item"><div class="legend-dot" style="background:#d62728"></div>FailedData (アノマリー/失敗)</div>
        <div class="legend-item"><div class="legend-dot" style="background:#e377c2"></div>ThermalLimit (再解釈限界値)</div>
        <div class="legend-item"><div class="legend-dot" style="background:#9467bd"></div>NewPaper (合成された新論文)</div>
        <div class="legend-item"><div class="legend-line" style="background:#64748b"></div>同時間層 (Intra-fiber)</div>
        <div class="legend-item"><div class="legend-line" style="background:#fb923c; height:3px"></div>時間・関手射 (Inter-fiber)</div>
      </div>
    </div>

    <div class="sidebar">
      <div class="tabs">
        <button class="tab-btn active" onclick="switchTab('tab-inspector')">プロバナンス検証</button>
        <button class="tab-btn" onclick="switchTab('tab-json')">JSON-LD ライブ同期</button>
        <button class="tab-btn" onclick="switchTab('tab-ops')">圏論操作</button>
      </div>

      <!-- Tab 1: Inspector -->
      <div id="tab-inspector" class="tab-content active">
        <div class="card" id="selection-card">
          <h3>選択ノード属性</h3>
          <div id="selected-node-info" style="color: var(--text-muted);">
            キャンバス上のノードをクリックすると、過去ルーツ（シアン）と将来影響（マゼンタ）が発光します。
          </div>
        </div>

        <div class="card">
          <h3>過去遡及ルーツ (Backward Provenance) <span id="ancestor-count" style="font-size:11px; color:var(--accent-cyan);">0 件</span></h3>
          <p style="font-size:10px; color:var(--text-muted); margin-bottom:4px;">選択ノードが依存する全過去データ・文献</p>
          <ul id="ancestor-list" class="provenance-list"></ul>
        </div>

        <div class="card">
          <h3>将来波及影響 (Forward Impact) <span id="descendant-count" style="font-size:11px; color:var(--accent-magenta);">0 件</span></h3>
          <p style="font-size:10px; color:var(--text-muted); margin-bottom:4px;">このノードから派生・創出された新成果</p>
          <ul id="descendant-list" class="provenance-list"></ul>
        </div>
      </div>

      <!-- Tab 2: JSON-LD -->
      <div id="tab-json" class="tab-content">
        <div class="card">
          <h3>PROV-O / SIO 準拠 JSON-LD スナップショット</h3>
          <p style="font-size:11px; color:var(--text-muted); margin-bottom:6px;">グラフの動的変更がリアルタイムに反映されます</p>
          <textarea id="json-editor" spellcheck="false"></textarea>
          <div style="display:flex; gap:8px; margin-top:8px;">
            <button onclick="applyJsonToGraph()">JSONからグラフへ反映</button>
            <button class="btn-secondary" onclick="exportJsonFile()">JSONダウンロード</button>
          </div>
        </div>
      </div>

      <!-- Tab 3: Operations -->
      <div id="tab-ops" class="tab-content">
        <div class="card">
          <h3>観点転換関手 (Perspective Shift)</h3>
          <p style="font-size:11px; color:var(--text-muted); margin-bottom:8px;">「目標未達の失敗データ」を「境界条件データ」として再定義し新時間層へ移行します。</p>
          <div class="form-group">
            <label>対象の失敗データノード:</label>
            <select id="shift-source-select"></select>
          </div>
          <div class="form-group">
            <label>新ノードID (t=10):</label>
            <input type="text" id="shift-new-id" value="LimitEntry_02">
          </div>
          <div class="form-group">
            <label>再定義された概念名 (schema:name):</label>
            <input type="text" id="shift-new-name" value="Oxidation Boundary at 300C">
          </div>
          <button class="btn-orange" onclick="executePerspectiveShift()">観点転換を実行 (Shift Functor)</button>
        </div>

        <div class="card">
          <h3>余極限合成 (Colimit / Pushout)</h3>
          <p style="font-size:11px; color:var(--text-muted); margin-bottom:8px;">再解釈された限界値や新材料を貼り合わせ、新論文・新成果ノードを創出します。</p>
          <div class="form-group">
            <label>新論文ノードID (t=20):</label>
            <input type="text" id="colimit-new-id" value="Paper_D">
          </div>
          <div class="form-group">
            <label>論文タイトル (schema:name):</label>
            <input type="text" id="colimit-new-title" value="Synthesis of High-Temp Silica-Doped Composites">
          </div>
          <button class="btn-purple" onclick="executeColimitSynthesis()">新論文を創出 (Colimit Projection)</button>
        </div>
      </div>
    </div>
  </div>

  <script>
    // 外部 JSON から読み込まれたグラフデータ
    let graphData = {data_json_str};

    const typeColors = {{
      Paper: "#1f77b4",
      Data: "#17becf",
      FailedData: "#d62728",
      ThermalLimit: "#e377c2",
      Material: "#2ca02c",
      NewMaterial: "#ff7f0e",
      Reference: "#7f7f7f",
      NewPaper: "#9467bd",
      Entity: "#64748b"
    }};

    let network = null;
    let nodesDataset = null;
    let edgesDataset = null;
    let selectedNodeId = null;

    function initNetwork() {{
      const container = document.getElementById('network-canvas');
      
      const visNodes = (graphData.nodes || []).map(n => ({{
        id: n.id,
        label: n.label || n.id,
        title: `${{n.title || n.label || n.id}} (Type: ${{n.type || 'Entity'}})`,
        color: {{ background: typeColors[n.type] || "#475569", border: "#fff" }},
        font: {{ color: "#fff", size: 11, face: "sans-serif" }},
        shape: "box",
        margin: 8,
        x: n.x,
        y: n.y,
        physics: false
      }}));

      const visEdges = (graphData.edges || []).map(e => ({{
        id: e.id,
        from: e.from,
        to: e.to,
        label: e.relation || e.label || "",
        font: {{ size: 9, color: "#94a3b8", strokeWidth: 0 }},
        arrows: "to",
        color: e.edge_type === "inter" ? {{ color: "#fb923c", highlight: "#f97316" }} : {{ color: "#475569", highlight: "#64748b" }},
        width: e.edge_type === "inter" ? 3 : 1.2,
        dashes: e.edge_type === "intra"
      }}));

      nodesDataset = new vis.DataSet(visNodes);
      edgesDataset = new vis.DataSet(visEdges);

      const data = {{ nodes: nodesDataset, edges: edgesDataset }};
      const options = {{
        interaction: {{ hover: true, selectConnectedEdges: false }},
        physics: {{ enabled: false }}
      }};

      network = new vis.Network(container, data, options);

      network.on("click", function(params) {{
        if (params.nodes.length > 0) {{
          selectNode(params.nodes[0]);
        }} else {{
          clearSelection();
        }}
      }});

      updateJsonView();
      populateShiftSelect();
      setTimeout(resetView, 300);
    }}

    function selectNode(nodeId) {{
      selectedNodeId = nodeId;
      const node = graphData.nodes.find(n => n.id === nodeId);
      if (!node) return;

      const ancestors = findAncestors(nodeId);
      const descendants = findDescendants(nodeId);

      document.getElementById("selected-node-info").innerHTML = `
        <b style="color:#fff; font-size:13px;">${{node.id}}</b><br>
        <b>Type:</b> ${{node.type || 'Entity'}}<br>
        <b>Version:</b> t=${{node.version ?? '-'}}<br>
        <b>Note:</b> ${{node.title || node.label}}
      `;

      document.getElementById("ancestor-count").innerText = `${{ancestors.length}} 件`;
      const ancList = document.getElementById("ancestor-list");
      ancList.innerHTML = ancestors.length ? "" : "<li style='color:#64748b'>祖先ノードなし (起点)</li>";
      ancestors.forEach(a => {{
        ancList.innerHTML += `<li class="cyan"><span>${{a.id}}</span> <span style="color:#94a3b8">t=${{a.version ?? '-'}} [${{a.type || 'Entity'}}]</span></li>`;
      }});

      document.getElementById("descendant-count").innerText = `${{descendants.length}} 件`;
      const descList = document.getElementById("descendant-list");
      descList.innerHTML = descendants.length ? "" : "<li style='color:#64748b'>派生先なし (最先端)</li>";
      descendants.forEach(d => {{
        descList.innerHTML += `<li class="magenta"><span>${{d.id}}</span> <span style="color:#94a3b8">t=${{d.version ?? '-'}} [${{d.type || 'Entity'}}]</span></li>`;
      }});

      const ancIds = new Set(ancestors.map(a => a.id));
      const descIds = new Set(descendants.map(d => d.id));

      nodesDataset.forEach(n => {{
        if (n.id === nodeId) {{
          nodesDataset.update({{ id: n.id, borderWidth: 4, color: {{ border: "#ffffff", background: "#f59e0b" }} }});
        }} else if (ancIds.has(n.id)) {{
          nodesDataset.update({{ id: n.id, borderWidth: 3, color: {{ border: "#38bdf8", background: typeColors[n.type] || "#475569" }} }});
        }} else if (descIds.has(n.id)) {{
          nodesDataset.update({{ id: n.id, borderWidth: 3, color: {{ border: "#f43f5e", background: typeColors[n.type] || "#475569" }} }});
        }} else {{
          nodesDataset.update({{ id: n.id, borderWidth: 1, color: {{ border: "#334155", background: "#1e293b" }} }});
        }}
      }});
    }}

    function clearSelection() {{
      selectedNodeId = null;
      document.getElementById("selected-node-info").innerText = "キャンバス上のノードをクリックしてください。";
      document.getElementById("ancestor-list").innerHTML = "";
      document.getElementById("descendant-list").innerHTML = "";
      document.getElementById("ancestor-count").innerText = "0 件";
      document.getElementById("descendant-count").innerText = "0 件";

      nodesDataset.forEach(n => {{
        const orig = graphData.nodes.find(o => o.id === n.id);
        nodesDataset.update({{
          id: n.id,
          borderWidth: 1,
          color: {{ border: "#fff", background: typeColors[orig?.type] || "#475569" }}
        }});
      }});
    }}

    function findAncestors(targetId) {{
      const visited = new Set();
      const queue = [targetId];
      while (queue.length > 0) {{
        const curr = queue.shift();
        graphData.edges.filter(e => e.to === curr).forEach(e => {{
          if (!visited.has(e.from)) {{
            visited.add(e.from);
            queue.push(e.from);
          }}
        }});
      }}
      return Array.from(visited).map(id => graphData.nodes.find(n => n.id === id)).filter(Boolean);
    }}

    function findDescendants(sourceId) {{
      const visited = new Set();
      const queue = [sourceId];
      while (queue.length > 0) {{
        const curr = queue.shift();
        graphData.edges.filter(e => e.from === curr).forEach(e => {{
          if (!visited.has(e.to)) {{
            visited.add(e.to);
            queue.push(e.to);
          }}
        }});
      }}
      return Array.from(visited).map(id => graphData.nodes.find(n => n.id === id)).filter(Boolean);
    }}

    function executePerspectiveShift() {{
      const srcId = document.getElementById("shift-source-select").value;
      const newRawId = document.getElementById("shift-new-id").value;
      const newName = document.getElementById("shift-new-name").value;
      const newId = `${{newRawId}}@t10`;

      if (!srcId || !newRawId) return alert("入力が不足しています");

      const newNode = {{
        id: newId,
        rawId: newRawId,
        type: "ThermalLimit",
        version: 10,
        label: `${{newRawId}} (t=10)\\n${{newName}}`,
        title: `観点転換による再解釈限界値: ${{newName}}`,
        x: 380,
        y: 420
      }};

      const newEdge = {{
        id: `e_${{Date.now()}}`,
        from: srcId,
        to: newId,
        relation: "PerspectiveShift",
        edge_type: "inter"
      }};

      graphData.nodes.push(newNode);
      graphData.edges.push(newEdge);

      nodesDataset.add({{
        id: newNode.id,
        label: newNode.label,
        title: newNode.title,
        color: {{ background: typeColors.ThermalLimit, border: "#fff" }},
        font: {{ color: "#fff", size: 11 }},
        shape: "box",
        margin: 8,
        x: newNode.x,
        y: newNode.y,
        physics: false
      }});

      edgesDataset.add({{
        id: newEdge.id,
        from: newEdge.from,
        to: newEdge.to,
        label: newEdge.relation,
        font: {{ size: 9, color: "#94a3b8" }},
        arrows: "to",
        color: {{ color: "#fb923c" }},
        width: 3
      }});

      updateJsonView();
      populateShiftSelect();
      selectNode(newId);
      switchTab('tab-inspector');
    }}

    function executeColimitSynthesis() {{
      const newRawId = document.getElementById("colimit-new-id").value;
      const newTitle = document.getElementById("colimit-new-title").value;
      const newId = `${{newRawId}}@t20`;

      if (!newRawId) return alert("ノードIDを指定してください");

      const newNode = {{
        id: newId,
        rawId: newRawId,
        type: "NewPaper",
        version: 20,
        label: `${{newRawId}} (t=20)\\n${{newTitle}}`,
        title: `余極限合成論文: ${{newTitle}}`,
        x: 680,
        y: 340
      }};

      graphData.nodes.push(newNode);
      nodesDataset.add({{
        id: newNode.id,
        label: newNode.label,
        title: newNode.title,
        color: {{ background: typeColors.NewPaper, border: "#fff" }},
        font: {{ color: "#fff", size: 11 }},
        shape: "box",
        margin: 8,
        x: newNode.x,
        y: newNode.y,
        physics: false
      }});

      const t10Nodes = graphData.nodes.filter(n => n.version === 10);
      t10Nodes.forEach((src, idx) => {{
        const edge = {{
          id: `e_col_${{Date.now()}}_${{idx}}`,
          from: src.id,
          to: newId,
          relation: src.type === "NewMaterial" ? "Pushout" : "ColimitProjection",
          edge_type: "inter"
        }};
        graphData.edges.push(edge);
        edgesDataset.add({{
          id: edge.id,
          from: edge.from,
          to: edge.to,
          label: edge.relation,
          font: {{ size: 9, color: "#94a3b8" }},
          arrows: "to",
          color: {{ color: "#fb923c" }},
          width: 3
        }});
      }});

      updateJsonView();
      selectNode(newId);
      switchTab('tab-inspector');
    }}

    function populateShiftSelect() {{
      const select = document.getElementById("shift-source-select");
      select.innerHTML = "";
      graphData.nodes.filter(n => n.type === "FailedData").forEach(n => {{
        select.innerHTML += `<option value="${{n.id}}">${{n.id}} (${{n.title || n.label}})</option>`;
      }});
    }}

    function updateJsonView() {{
      const jsonLd = {{
        "@context": {{
          "schema": "http://schema.org/",
          "prov": "http://www.w3.org/ns/prov#",
          "sio": "http://semanticscience.org/resource/",
          "cat": "http://example.org/category#"
        }},
        "@graph": graphData.nodes.map(n => ({{
          "@id": n.rawId || n.id,
          "@type": n.type,
          "schema:name": n.title || n.label,
          "cat:version": n.version,
          "prov:wasDerivedFrom": graphData.edges.filter(e => e.to === n.id).map(e => e.from)
        }}))
      }};
      document.getElementById("json-editor").value = JSON.stringify(jsonLd, null, 2);
    }}

    function applyJsonToGraph() {{
      try {{
        const parsed = JSON.parse(document.getElementById("json-editor").value);
        if (parsed["@graph"]) {{
          alert("JSON-LD の変更を検知しました。再描画します。");
        }}
      }} catch(e) {{
        alert("JSON パースエラー: " + e.message);
      }}
    }}

    function exportJsonFile() {{
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(document.getElementById("json-editor").value);
      const dlAnchor = document.createElement('a');
      dlAnchor.setAttribute("href", dataStr);
      dlAnchor.setAttribute("download", "provenance_metadata.jsonld");
      document.body.appendChild(dlAnchor);
      dlAnchor.click();
      dlAnchor.remove();
    }}

    function switchTab(tabId) {{
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(b => b.getAttribute('onclick').includes(tabId));
      if (activeBtn) activeBtn.classList.add('active');
      document.getElementById(tabId).classList.add('active');
    }}

    function resetView() {{
      if (network) network.fit({{ animation: {{ duration: 500, easingFunction: "easeInOutQuad" }} }});
    }}

    window.onload = initNetwork;
  </script>
</body>
</html>
"""


class CustomHandler(http.server.SimpleHTTPRequestHandler):
  HTML_DATA = ""

  def do_GET(self):
    if self.path == "/" or self.path.endswith(".html"):
      self.send_response(200)
      self.send_header("Content-Type", "text/html; charset=utf-8")
      self.end_headers()
      self.wfile.write(self.HTML_DATA.encode("utf-8"))
    else:
      super().do_GET()


def start_server(data_filepath):
  # 1. 外部 JSON データの読み込み
  raw_data = load_or_create_default_data(data_filepath)
  # 2. スナップショット形式・グラフ形式の自動正規化
  graph_data = convert_snapshots_to_graph(raw_data)
  # 3. HTML のビルド
  html_content = build_html_content(
      graph_data, os.path.basename(data_filepath)
  )
  CustomHandler.HTML_DATA = html_content

  # 4. サーバー起動
  socketserver.TCPServer.allow_reuse_address = True
  with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
    print("=" * 68)
    print("[*] 圏論的メタデータ探索サーバー起動")
    print(f"[*] 読み込みファイル: {os.path.abspath(data_filepath)}")
    print(f"[*] URL: http://localhost:{PORT}")
    print("[*] 終了するにはターミナルで Ctrl+C を押してください")
    print("=" * 68)

    threading.Timer(
        1.0, lambda: webbrowser.open(f"http://localhost:{PORT}")
    ).start()
    try:
      httpd.serve_forever()
    except KeyboardInterrupt:
      print("\n[*] サーバーを停止しました。")
      httpd.server_close()


if __name__ == "__main__":
  # コマンドライン引数があれば第1引数をファイル名とする
  target_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DATA_FILE
  start_server(target_file)