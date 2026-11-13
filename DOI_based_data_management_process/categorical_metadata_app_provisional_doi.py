"""
Categorical Dynamic Metadata Construction & Live Provenance Explorer (Provisional ID & DOI Minting Edition)
============================================================================================================
- 外部 JSON 読み込み (shared_dataset_dual_lineage.json 等に対応)
- 新規データ・論文追加時の「仮ID（Provisional ID: prov:temp-...）」自動発行・手動指定機能
- 仮ID（黄色点線枠で視覚的区別）から「正式DOI（10.xxxx/...）」へのアップグレード・置換機能
- 置換時に、すべてのエッジ参照・過去遡及（Provenance）・JSON-LD を無矛盾に一括更新（同型写像 / Isomorphic Replacement）
- 全メニュー（リセット、追加、DOI確定アップグレード、観点転換、余極限、動画再生バー）搭載
"""

import http.server
import socketserver
import webbrowser
import threading
import json
import os
import sys

PORT = 8080
DEFAULT_DATA_FILE = "shared_dataset_dual_lineage.json"


def load_or_create_default_data(filepath):
    if os.path.exists(filepath):
        print(f"[*] 入力データファイルを読み込みました: {filepath}")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] JSON読み込みエラー ({filepath}): {e}")

    print(f"[*] '{filepath}' が見つからないためフォールバックを使用します。")
    return {"snapshots": []}


def convert_snapshots_to_graph(data):
    if "nodes" in data and "edges" in data:
        return data

    if "snapshots" not in data:
        return {"nodes": [], "edges": []}

    nodes = []
    edges = []
    node_id_set = set()

    layer_y = {
        "NewPaper": 60, "Paper": 100, "Reference": 220, "Data": 340,
        "ThermalLimit": 460, "Material": 580, "NewMaterial": 680,
        "FailedData": 780, "Researcher": 280, "Entity": 880
    }
    x_step = 340
    slot_tracker = {}

    # 1. 全ノードの登録
    for idx, snap in enumerate(data.get("snapshots", [])):
        v = snap.get("version", idx * 10)

        # 観点転換ノード
        for s in snap.get("perspective_shifts", []):
            tgt_id = f"{s['new_id']}@t{v}"
            if tgt_id not in node_id_set:
                node_id_set.add(tgt_id)
                col_x = (v // 10) * x_step + 100
                nodes.append({
                    "id": tgt_id,
                    "rawId": s["new_id"],
                    "doi": s.get("doi", ""),
                    "isProvisional": s["new_id"].startswith("temp-") or s["new_id"].startswith("prov-"),
                    "type": s.get("new_type", "ThermalLimit"),
                    "version": v,
                    "label": f"{s['new_id']} (t={v})\n{s['name'][:20]}",
                    "title": s["name"],
                    "x": col_x,
                    "y": 460
                })

        for node in snap.get("@graph", []):
            raw_id = node["@id"]
            is_agent = raw_id.startswith("orcid:") or raw_id.startswith("agent:")
            node_id = raw_id if is_agent else f"{raw_id}@t{v}"

            if node_id not in node_id_set:
                node_id_set.add(node_id)
                n_type = node.get("cat:type", "Entity")
                name = node.get("schema:name", raw_id)
                doi_val = node.get("datacite:doi", "")
                is_prov = bool(node.get("cat:isProvisional", False)) or raw_id.startswith("temp-") or raw_id.startswith("prov-")

                col_x = (v // 10) * x_step + 100
                if "Shared" in raw_id:
                    node_y = 440
                elif is_agent:
                    node_y = 260 + (len([n for n in nodes if n['type'] == 'Researcher']) * 70)
                    col_x = 100
                else:
                    base_y = layer_y.get(n_type, 450)
                    slot_key = (v, n_type)
                    slot_idx = slot_tracker.get(slot_key, 0)
                    slot_tracker[slot_key] = slot_idx + 1
                    node_y = base_y + (slot_idx * 75)

                nodes.append({
                    "id": node_id,
                    "rawId": raw_id,
                    "doi": doi_val,
                    "isProvisional": is_prov,
                    "type": n_type,
                    "version": v if not is_agent else 0,
                    "label": f"{raw_id} (t={v})\n{name[:22]}" if not is_agent else name,
                    "title": f"{name} (Type: {n_type})",
                    "x": col_x,
                    "y": node_y
                })

    # 2. 全エッジの登録
    for idx, snap in enumerate(data.get("snapshots", [])):
        v = snap.get("version", idx * 10)

        for s in snap.get("perspective_shifts", []):
            prev_v = data["snapshots"][idx - 1]["version"] if idx > 0 else 0
            src_node = f"{s['source_id']}@t{prev_v}"
            tgt_node = f"{s['new_id']}@t{v}"
            if src_node in node_id_set and tgt_node in node_id_set:
                edges.append({
                    "id": f"shift_{src_node}_{tgt_node}",
                    "from": src_node,
                    "to": tgt_node,
                    "relation": "PerspectiveShift",
                    "edge_type": "inter"
                })

        for node in snap.get("@graph", []):
            raw_id = node["@id"]
            is_agent = raw_id.startswith("orcid:") or raw_id.startswith("agent:")
            node_id = raw_id if is_agent else f"{raw_id}@t{v}"

            for key, targets in node.items():
                if any(key.startswith(p) for p in ["schema:", "prov:", "sio:"]):
                    t_list = targets if isinstance(targets, list) else [targets]
                    for tgt in t_list:
                        if isinstance(tgt, dict) and "@id" in tgt:
                            tgt_raw = tgt["@id"]
                            candidate_ids = [
                                tgt_raw,
                                f"{tgt_raw}@t{v}",
                                f"{tgt_raw}@t0"
                            ]
                            matched_id = next((cid for cid in candidate_ids if cid in node_id_set), None)
                            if matched_id and node_id in node_id_set:
                                edges.append({
                                    "id": f"e_{node_id}_{matched_id}_{key}",
                                    "from": node_id,
                                    "to": matched_id,
                                    "relation": key,
                                    "edge_type": "intra" if "@t" in matched_id and f"@t{v}" in matched_id else "inter"
                                })

        for hf in snap.get("higher_functors", []):
            if hf["from"] in node_id_set and hf["to"] in node_id_set:
                edges.append({
                    "id": f"hf_{hf['from']}_{hf['to']}",
                    "from": hf["from"],
                    "to": hf["to"],
                    "relation": hf.get("transform", "Functor"),
                    "edge_type": "inter"
                })

    return {"nodes": nodes, "edges": edges}


def build_html_content(graph_data, current_filename):
    data_json_str = json.dumps(graph_data, ensure_ascii=False)
    
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>Categorical Metadata & Provenance Explorer (∫D) - Provisional ID & DOI Minting</title>
  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    :root {{
      --bg-main: #07090e;
      --bg-panel: #111827;
      --bg-header: #0f172a;
      --border: #1f2937;
      --cyan: #38bdf8;
      --magenta: #f43f5e;
      --orange: #fb923c;
      --green: #22c55e;
      --gold: #eab308;
      --amber: #f59e0b;
      --text: #f3f4f6;
      --text-muted: #9ca3af;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg-main);
      color: var(--text);
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }}
    header {{
      background: var(--bg-header);
      padding: 0 16px;
      height: 48px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--border);
      z-index: 100;
      gap: 8px;
    }}
    h1 {{ font-size: 13px; font-weight: 700; color: var(--cyan); display: flex; align-items: center; gap: 8px; white-space: nowrap; }}
    .badge {{ background: #0284c7; color: white; font-size: 9px; padding: 2px 6px; border-radius: 4px; }}
    .file-badge {{ background: #166534; color: #86efac; font-size: 10px; padding: 2px 8px; border-radius: 4px; border: 1px solid #22c55e; }}

    .toolbar {{ display: flex; gap: 6px; align-items: center; }}
    .selector-box {{
      display: flex;
      align-items: center;
      gap: 4px;
      background: #1e293b;
      padding: 3px 6px;
      border-radius: 4px;
      border: 1px solid var(--border);
      font-size: 11px;
    }}
    select {{
      background: #0b0f17;
      color: #fff;
      border: 1px solid #4b5563;
      padding: 2px 4px;
      border-radius: 4px;
      font-size: 11px;
      max-width: 170px;
    }}
    button {{
      background: #2563eb;
      color: #fff;
      border: none;
      padding: 5px 10px;
      border-radius: 4px;
      cursor: pointer;
      font-size: 11px;
      font-weight: 600;
      transition: all 0.15s;
      white-space: nowrap;
    }}
    button:hover {{ background: #1d4ed8; filter: brightness(1.1); }}
    button.btn-danger {{ background: #b91c1c; }}
    button.btn-danger:hover {{ background: #dc2626; }}
    button.btn-orange {{ background: #ea580c; }}
    button.btn-orange:hover {{ background: #f97316; }}
    button.btn-purple {{ background: #7c3aed; }}
    button.btn-purple:hover {{ background: #8b5cf6; }}
    button.btn-green {{ background: #16a34a; }}
    button.btn-green:hover {{ background: #22c55e; }}
    button.btn-gold {{ background: #ca8a04; color: #fff; }}
    button.btn-gold:hover {{ background: #a16207; }}
    button.btn-secondary {{ background: #374151; }}
    button.btn-secondary:hover {{ background: #4b5563; }}

    .main-container {{
      display: flex;
      flex: 1;
      height: calc(100vh - 48px - 42px);
    }}
    #network-canvas {{
      flex: 1;
      height: 100%;
      background: radial-gradient(circle at center, #111827 0%, #030712 100%);
      position: relative;
    }}
    .legend-overlay {{
      position: absolute;
      bottom: 12px;
      left: 12px;
      background: rgba(17, 24, 39, 0.94);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 8px 12px;
      font-size: 10px;
      pointer-events: none;
      backdrop-filter: blur(4px);
    }}
    .legend-item {{ display: flex; align-items: center; gap: 6px; margin-bottom: 2px; }}
    .legend-dot {{ width: 8px; height: 8px; border-radius: 2px; }}

    .sidebar {{
      width: 450px;
      background: var(--bg-panel);
      border-left: 1px solid var(--border);
      display: flex;
      flex-direction: column;
    }}
    .tabs {{
      display: flex;
      border-bottom: 1px solid var(--border);
      background: #0b0f17;
    }}
    .tab-btn {{
      flex: 1;
      background: transparent;
      border: none;
      border-bottom: 2px solid transparent;
      padding: 9px 4px;
      color: var(--text-muted);
      cursor: pointer;
      font-size: 11px;
      text-align: center;
    }}
    .tab-btn.active {{
      color: #fff;
      border-bottom-color: var(--cyan);
      background: var(--bg-panel);
      font-weight: 700;
    }}
    .tab-content {{
      flex: 1;
      overflow-y: auto;
      padding: 12px;
      display: none;
      flex-direction: column;
      gap: 10px;
    }}
    .tab-content.active {{ display: flex; }}
    .card {{
      background: #0b0f17;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 10px;
      font-size: 11px;
    }}
    .card h3 {{
      font-size: 12px;
      margin-bottom: 6px;
      color: var(--cyan);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .provenance-list {{ list-style: none; margin-top: 4px; }}
    .provenance-list li {{
      padding: 4px 6px;
      border-left: 2px solid var(--border);
      margin-bottom: 3px;
      font-size: 10px;
      display: flex;
      justify-content: space-between;
      cursor: pointer;
    }}
    .provenance-list li.cyan {{ border-left-color: var(--cyan); background: rgba(56, 189, 248, 0.08); }}
    .provenance-list li.magenta {{ border-left-color: var(--magenta); background: rgba(244, 63, 94, 0.08); }}

    textarea {{
      width: 100%;
      height: 250px;
      background: #05070c;
      color: #38bdf8;
      border: 1px solid var(--border);
      border-radius: 4px;
      font-family: monospace;
      font-size: 10px;
      padding: 8px;
      resize: vertical;
    }}
    .form-group {{
      display: flex;
      flex-direction: column;
      gap: 2px;
      margin-bottom: 6px;
    }}
    .form-group label {{ font-size: 10px; color: var(--text-muted); font-weight: 500; }}
    .form-group input, .form-group select {{
      background: #07090e;
      border: 1px solid var(--border);
      color: var(--text);
      padding: 5px;
      border-radius: 4px;
      font-size: 11px;
    }}
    .inline-row {{
      display: flex;
      gap: 4px;
      align-items: center;
    }}
    .inline-row input {{
      flex: 1;
    }}
    .status-pill {{
      display: inline-block;
      padding: 1px 6px;
      border-radius: 10px;
      font-size: 9px;
      font-weight: 700;
    }}
    .status-prov {{
      background: rgba(245, 158, 11, 0.2);
      color: #fbbf24;
      border: 1px dashed #f59e0b;
    }}
    .status-doi {{
      background: rgba(34, 197, 94, 0.2);
      color: #4ade80;
      border: 1px solid #22c55e;
    }}

    footer {{
      height: 42px;
      background: #0f172a;
      border-top: 1px solid var(--border);
      display: flex;
      align-items: center;
      padding: 0 16px;
      gap: 12px;
      z-index: 100;
    }}
    .playback-btn {{
      width: 26px; height: 26px;
      border-radius: 50%;
      background: #2563eb;
      border: none;
      display: flex; align-items: center; justify-content: center;
      padding: 0;
      font-size: 12px;
    }}
    .timeline-slider-wrap {{
      flex: 1;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    input[type=range] {{
      flex: 1;
      accent-color: #38bdf8;
      cursor: pointer;
    }}
  </style>
</head>
<body>
  <header>
    <div style="display: flex; align-items: center; gap: 8px;">
      <h1>Categorical Metadata Explorer <span class="badge">∫D</span></h1>
      <span class="file-badge">Loaded: {current_filename}</span>
    </div>

    <div class="toolbar">
      <div class="selector-box">
        <label style="color:#9ca3af;">🎯 探索:</label>
        <select id="quick-target-select" onchange="onQuickSelectChange(this.value)">
          <option value="">-- ノードを選択 --</option>
        </select>
      </div>

      <div class="selector-box">
        <label style="color:#9ca3af;">⏳ 時間:</label>
        <select id="filter-version-select" onchange="filterByVersion(this.value)">
          <option value="ALL">全時間層</option>
          <option value="0">t=0</option>
          <option value="10">t=10</option>
          <option value="20">t=20</option>
        </select>
      </div>

      <div class="selector-box">
        <label style="color:#9ca3af;">🏷️ 種別:</label>
        <select id="filter-type-select" onchange="filterByType(this.value)">
          <option value="ALL">全種別</option>
          <option value="Paper">Paper</option>
          <option value="NewPaper">NewPaper</option>
          <option value="Data">Data</option>
          <option value="FailedData">FailedData</option>
          <option value="ThermalLimit">ThermalLimit</option>
          <option value="NewMaterial">NewMaterial</option>
          <option value="Researcher">Researcher</option>
        </select>
      </div>

      <button class="btn-danger" onclick="resetAllState()">⟲ 全体リセット</button>
      <button class="btn-secondary" onclick="resetView()">センタリング</button>
    </div>
  </header>

  <div class="main-container">
    <div id="network-canvas">
      <div class="legend-overlay">
        <div style="font-weight:700; margin-bottom:4px; color:#fff;">階層・エッジ凡例</div>
        <div class="legend-item"><div class="legend-dot" style="background:#1d4ed8"></div>Paper (論文)</div>
        <div class="legend-item"><div class="legend-dot" style="background:#7e22ce"></div>NewPaper (新論文)</div>
        <div class="legend-item"><div class="legend-dot" style="background:#0891b2"></div>Data (測定データ)</div>
        <div class="legend-item"><div class="legend-dot" style="background:#eab308"></div>Shared Data (共通基底)</div>
        <div class="legend-item"><div class="legend-dot" style="background:#b91c1c"></div>FailedData (失敗ログ)</div>
        <div class="legend-item"><div class="legend-dot" style="background:#be185d"></div>ThermalLimit (再解釈限界値)</div>
        <div class="legend-item"><div class="legend-dot" style="background:#c2410c"></div>NewMaterial (新標本)</div>
        <div class="legend-item"><div class="legend-dot" style="background:#10b981"></div>Researcher (ORCID)</div>
        <div class="legend-item"><div class="legend-dot" style="background:transparent; border:1.5px dashed #fbbf24;"></div>仮ID (Provisional ID / 未DOI)</div>
        <hr style="margin:3px 0; border:0; border-top:1px solid #374151;">
        <div style="color:#fb923c; font-weight:bold;">― 太線オレンジ: 関手射 (Inter-fiber)</div>
        <div style="color:#9ca3af;">┄ 破線グレー: 同時間内構造 (Intra-fiber)</div>
      </div>
    </div>

    <div class="sidebar">
      <div class="tabs">
        <button class="tab-btn active" onclick="switchTab('tab-inspector')">プロバナンス検証</button>
        <button class="tab-btn" onclick="switchTab('tab-ops')">圏論操作メニュー</button>
        <button class="tab-btn" onclick="switchTab('tab-json')">JSON-LD ライブ</button>
      </div>

      <div id="tab-inspector" class="tab-content active">
        <div class="card">
          <h3>
            選択ノード属性
            <button class="btn-secondary" style="padding:1px 6px; font-size:10px;" onclick="clearSelection()">解除</button>
          </h3>
          <div id="selected-node-info" style="color: var(--text-muted); line-height:1.5;">
            ノードをクリックすると過去起源（シアン）と将来影響（マゼンタ）が発光します。
          </div>
          <!-- 選択ノードが仮IDの場合、ここから直接DOI昇格パネルへ飛べるクイックボタン -->
          <div id="quick-promote-area" style="margin-top:8px; display:none;">
            <button class="btn-gold" style="width:100%;" onclick="jumpToPromoteSelected()">★ この仮IDに正式DOIを割り当てて確定する</button>
          </div>
        </div>

        <div class="card">
          <h3>過去遡及ルーツ (Backward Provenance) <span id="ancestor-count" style="color:var(--cyan);">0 件</span></h3>
          <ul id="ancestor-list" class="provenance-list"></ul>
        </div>

        <div class="card">
          <h3>将来波及影響 (Forward Impact) <span id="descendant-count" style="color:var(--magenta);">0 件</span></h3>
          <ul id="descendant-list" class="provenance-list"></ul>
        </div>
      </div>

      <div id="tab-ops" class="tab-content">
        <!-- 1. 新規データ・論文の追加（仮ID自動発行機能付き） -->
        <div class="card" style="border-left: 3px solid var(--green);">
          <h3 style="color: var(--green);">＋ データ・論文の新規追加（仮ID発行）</h3>
          <p style="font-size:10px; color:var(--text-muted); margin-bottom:5px;">DOI未取得の段階では仮ID（<code>temp-...</code>）を発行してグラフに組み込み、後から正式DOIへ差し替え可能です。</p>
          <div class="form-group">
            <label>配置先時間層:</label>
            <select id="add-node-version">
              <option value="0">t=0 (初期実験層)</option>
              <option value="10">t=10 (中間展開層)</option>
              <option value="20">t=20 (合成論文層)</option>
            </select>
          </div>
          <div class="form-group">
            <label>ノード種別:</label>
            <select id="add-node-type">
              <option value="Data">Data (測定データ)</option>
              <option value="FailedData">FailedData (失敗ログ)</option>
              <option value="Paper">Paper (論文)</option>
              <option value="Material">Material (材料標本)</option>
            </select>
          </div>
          <div class="form-group">
            <label>IDモード & 仮ID発行:</label>
            <div class="inline-row">
              <input type="text" id="add-node-id" placeholder="temp-20261112-001">
              <button type="button" class="btn-secondary" onclick="generateProvisionalId()">仮ID自動採番</button>
            </div>
          </div>
          <div class="form-group">
            <label>正式DOI (既にあれば入力・空欄なら仮ID扱い):</label>
            <input type="text" id="add-node-doi" placeholder="例: 10.5281/zenodo.1234567 (空欄可)">
          </div>
          <div class="form-group">
            <label>名称・タイトル (schema:name):</label>
            <input type="text" id="add-node-name" placeholder="例: Preliminary XRD Scan Dataset">
          </div>
          <div class="form-group">
            <label>接続先ノード:</label>
            <select id="add-edge-target"><option value="">-- 単独ノード --</option></select>
          </div>
          <div class="form-group">
            <label>関係性射:</label>
            <select id="add-edge-relation">
              <option value="schema:hasPart">schema:hasPart</option>
              <option value="prov:wasDerivedFrom">prov:wasDerivedFrom</option>
            </select>
          </div>
          <button class="btn-green" style="width:100%; margin-top:2px;" onclick="executeAddNode()">＋ 仮ID / 新規ノードを登録</button>
        </div>

        <!-- 2. 仮IDから正式DOIへのアップグレード（同型置換） -->
        <div class="card" style="border-left: 3px solid var(--gold);">
          <h3 style="color: var(--gold);">★ 仮ID → 正式DOI 確定・置換（DOI Minting）</h3>
          <p style="font-size:10px; color:var(--text-muted); margin-bottom:5px;">仮IDのまま構築した依存関係・エッジ・履歴を一切壊さず、正式なDOIおよび識別子へ同型置換します。</p>
          <div class="form-group">
            <label>対象の仮IDノード:</label>
            <select id="promote-source-select" onchange="onPromoteSourceChange(this.value)"></select>
          </div>
          <div class="form-group">
            <label>正式DOI (datacite:doi):</label>
            <input type="text" id="promote-new-doi" placeholder="例: 10.5281/zenodo.9876543">
          </div>
          <div class="form-group">
            <label>確定後の正式ノードID (@id):</label>
            <input type="text" id="promote-new-id" placeholder="例: Data_XRD_Scan_DOI">
          </div>
          <button class="btn-gold" style="width:100%; margin-top:2px;" onclick="executePromoteToDoi()">正式DOIを付与して確定置換</button>
        </div>

        <!-- 3. 観点転換関手 (Shift) -->
        <div class="card" style="border-left: 3px solid var(--orange);">
          <h3 style="color: var(--orange);">★ 観点転換関手 (Shift)</h3>
          <div class="form-group">
            <label>転換元ノード:</label>
            <select id="shift-source-select"></select>
          </div>
          <div class="form-group">
            <label>新カテゴリ型:</label>
            <select id="shift-target-type-select">
              <option value="ThermalLimit">ThermalLimit</option>
              <option value="Data">Data</option>
            </select>
          </div>
          <div class="form-group">
            <label>新ノードID:</label>
            <input type="text" id="shift-new-id" value="LimitEntry_Custom">
          </div>
          <div class="form-group">
            <label>再定義名:</label>
            <input type="text" id="shift-new-name" value="Custom Physical Limit Boundary">
          </div>
          <button class="btn-orange" style="width:100%; margin-top:2px;" onclick="executePerspectiveShift()">観点転換を実行</button>
        </div>

        <!-- 4. 余極限合成 (Colimit) -->
        <div class="card" style="border-left: 3px solid var(--purple);">
          <h3 style="color: var(--purple);">★ 余極限合成 (Colimit)</h3>
          <div class="form-group">
            <label>基準時間層:</label>
            <select id="colimit-source-version-select">
              <option value="10">t=10</option>
              <option value="0">t=0</option>
            </select>
          </div>
          <div class="form-group">
            <label>新論文ID:</label>
            <input type="text" id="colimit-new-id" value="Paper_NewSynthesis">
          </div>
          <div class="form-group">
            <label>論文タイトル:</label>
            <input type="text" id="colimit-new-title" value="Synthesis of High-Efficiency Functional Materials">
          </div>
          <button class="btn-purple" style="width:100%; margin-top:2px;" onclick="executeColimitSynthesis()">新論文を創出</button>
        </div>
      </div>

      <div id="tab-json" class="tab-content">
        <div class="card">
          <h3>
            PROV-O / SIO 準拠 JSON-LD
            <button class="btn-secondary" style="padding:1px 6px; font-size:10px;" onclick="downloadJsonLd()">ダウンロード</button>
          </h3>
          <textarea id="json-editor" spellcheck="false"></textarea>
        </div>
      </div>
    </div>
  </div>

  <footer>
    <div style="display:flex; align-items:center; gap:8px;">
      <button class="playback-btn" id="play-btn" onclick="togglePlay()">▶</button>
      <button class="btn-secondary" style="padding:3px 8px; font-size:10px;" onclick="restartSimulation()">⟲ 最初から</button>
    </div>

    <div class="timeline-slider-wrap">
      <span style="font-size:11px; color:var(--cyan); font-weight:700;">EVOLUTION:</span>
      <input type="range" id="time-scrubber" min="0" max="20" step="1" value="20" oninput="onScrub(this.value)">
      <span id="time-display" style="font-size:11px; color:#fff; font-weight:700; min-width:45px;">t = 20</span>
    </div>
  </footer>

  <script>
    const initialGraph = {data_json_str};

    let rawNodes = JSON.parse(JSON.stringify(initialGraph.nodes || []));
    let rawEdges = JSON.parse(JSON.stringify(initialGraph.edges || []));
    let tempCounter = 1;

    const typeColors = {{
      Paper: "#1d4ed8",
      NewPaper: "#7e22ce",
      Data: "#0891b2",
      FailedData: "#b91c1c",
      ThermalLimit: "#be185d",
      Material: "#15803d",
      NewMaterial: "#c2410c",
      Researcher: "#10b981",
      Reference: "#4b5563",
      Entity: "#64748b"
    }};

    let network = null;
    let nodesDataset = null;
    let edgesDataset = null;
    let currentSelectedNodeId = null;

    function getNodeStyleProps(n) {{
      let bgCol = typeColors[n.type] || "#64748b";
      if (n.id.includes("Shared")) bgCol = "#eab308";
      const isProv = Boolean(n.isProvisional);

      return {{
        color: {{
          background: bgCol,
          border: isProv ? "#fbbf24" : "#ffffff"
        }},
        borderWidth: isProv ? 2.5 : 1,
        shapeProperties: {{
          borderDashes: isProv ? [5, 4] : false
        }}
      }};
    }}

    function initNetwork() {{
      const container = document.getElementById('network-canvas');
      
      const visNodes = rawNodes.map(n => {{
        const styleProps = getNodeStyleProps(n);
        const badgePrefix = n.isProvisional ? "[仮ID] " : (n.doi ? "[DOI確定] " : "");
        return {{
          id: n.id,
          label: badgePrefix + (n.label || n.id),
          title: n.title || n.label || n.id,
          color: styleProps.color,
          borderWidth: styleProps.borderWidth,
          shapeProperties: styleProps.shapeProperties,
          font: {{ color: "#ffffff", size: 10, face: "Segoe UI, sans-serif" }},
          shape: "box",
          margin: 8,
          x: n.x,
          y: n.y,
          physics: false
        }};
      }});

      const visEdges = rawEdges.map((e, idx) => {{
        const isInter = (e.edge_type === "inter");
        const isShared = (e.from.includes("Shared") || e.to.includes("Shared"));

        return {{
          id: e.id || `e_${{idx}}`,
          from: e.from,
          to: e.to,
          label: e.relation || e.label || "",
          font: {{ size: 8, color: "#94a3b8", strokeWidth: 2, strokeColor: "#0b0f17", align: "middle" }},
          arrows: "to",
          color: {{ color: isShared ? "#eab308" : (isInter ? "#fb923c" : "#475569") }},
          width: isShared ? 3.0 : (isInter ? 2.2 : 1.2),
          dashes: !isInter,
          smooth: {{ type: "cubicBezier", forceDirection: "horizontal", roundness: 0.35 }}
        }};
      }});

      nodesDataset = new vis.DataSet(visNodes);
      edgesDataset = new vis.DataSet(visEdges);

      const data = {{ nodes: nodesDataset, edges: edgesDataset }};
      const options = {{
        interaction: {{ hover: true, dragNodes: true, zoomView: true, dragView: true }},
        physics: {{ enabled: false }}
      }};

      network = new vis.Network(container, data, options);

      network.on("click", function(params) {{
        if (params.nodes.length > 0) selectNode(params.nodes[0]);
        else clearSelection();
      }});

      generateProvisionalId();
      populateDropdowns();
      updateJsonView();
      setTimeout(resetView, 300);
    }}

    function generateProvisionalId() {{
      const today = new Date().toISOString().slice(0, 10).replace(/-/g, "");
      const seq = String(tempCounter).padStart(3, "0");
      document.getElementById("add-node-id").value = `temp-${{today}}-${{seq}}`;
    }}

    function resetAllState() {{
      rawNodes = JSON.parse(JSON.stringify(initialGraph.nodes || []));
      rawEdges = JSON.parse(JSON.stringify(initialGraph.edges || []));
      tempCounter = 1;

      nodesDataset.clear();
      edgesDataset.clear();

      rawNodes.forEach(n => {{
        const styleProps = getNodeStyleProps(n);
        const badgePrefix = n.isProvisional ? "[仮ID] " : (n.doi ? "[DOI確定] " : "");
        nodesDataset.add({{
          id: n.id,
          label: badgePrefix + (n.label || n.id),
          title: n.title || n.label || n.id,
          color: styleProps.color,
          borderWidth: styleProps.borderWidth,
          shapeProperties: styleProps.shapeProperties,
          font: {{ color: "#ffffff", size: 10, face: "Segoe UI, sans-serif" }},
          shape: "box",
          margin: 8,
          x: n.x,
          y: n.y,
          physics: false
        }});
      }});

      rawEdges.forEach((e, idx) => {{
        const isInter = (e.edge_type === "inter");
        const isShared = (e.from.includes("Shared") || e.to.includes("Shared"));
        edgesDataset.add({{
          id: e.id || `e_${{idx}}`,
          from: e.from,
          to: e.to,
          label: e.relation || e.label || "",
          font: {{ size: 8, color: "#94a3b8", strokeWidth: 2, strokeColor: "#0b0f17", align: "middle" }},
          arrows: "to",
          color: {{ color: isShared ? "#eab308" : (isInter ? "#fb923c" : "#475569") }},
          width: isShared ? 3.0 : (isInter ? 2.2 : 1.2),
          dashes: !isInter,
          smooth: {{ type: "cubicBezier", forceDirection: "horizontal", roundness: 0.35 }}
        }});
      }});

      document.getElementById("filter-version-select").value = "ALL";
      document.getElementById("filter-type-select").value = "ALL";
      document.getElementById("quick-target-select").value = "";

      generateProvisionalId();
      clearSelection();
      populateDropdowns();
      updateJsonView();
      resetView();
    }}

    function selectNode(nodeId) {{
      currentSelectedNodeId = nodeId;
      document.getElementById("quick-target-select").value = nodeId;

      const node = rawNodes.find(n => n.id === nodeId);
      if (!node) return;

      const ancestors = findAncestors(nodeId);
      const descendants = findDescendants(nodeId);

      const statusBadge = node.isProvisional
        ? `<span class="status-pill status-prov">仮ID (Provisional / DOI未付与)</span>`
        : (node.doi ? `<span class="status-pill status-doi">DOI確定: ${{node.doi}}</span>` : `<span class="status-pill" style="background:#1e293b; color:#94a3b8;">ローカル識別子</span>`);

      const prevProvNote = node.formerProvisionalId
        ? `<br><span style="color:#fbbf24; font-size:10px;">旧仮ID履歴: <code>${{node.formerProvisionalId}}</code> から昇格</span>`
        : "";

      document.getElementById("selected-node-info").innerHTML = `
        <div style="margin-bottom:4px;">${{statusBadge}}</div>
        <b style="color:#fff; font-size:12px;">${{node.id}}</b><br>
        <b>Type:</b> ${{node.type || 'Entity'}} | <b>Version:</b> t=${{node.version ?? '-'}}<br>
        <span style="color:#38bdf8;">${{node.title || node.label}}</span>${{prevProvNote}}
      `;

      // 仮IDノード選択時はワンクリックDOI昇格ボタンを表示
      const quickPromoteArea = document.getElementById("quick-promote-area");
      if (node.isProvisional) {{
        quickPromoteArea.style.display = "block";
      }} else {{
        quickPromoteArea.style.display = "none";
      }}

      document.getElementById("ancestor-count").innerText = `${{ancestors.length}} 件`;
      const ancList = document.getElementById("ancestor-list");
      ancList.innerHTML = ancestors.length ? "" : "<li style='color:#6b7280'>祖先なし (起点)</li>";
      ancestors.forEach(a => {{
        ancList.innerHTML += `<li class="cyan" onclick="selectNode('${{a.id}}')"><span>${{a.id}}</span> <span style="color:#94a3b8">t=${{a.version ?? '-'}}</span></li>`;
      }});

      document.getElementById("descendant-count").innerText = `${{descendants.length}} 件`;
      const descList = document.getElementById("descendant-list");
      descList.innerHTML = descendants.length ? "" : "<li style='color:#6b7280'>派生先なし</li>";
      descendants.forEach(d => {{
        descList.innerHTML += `<li class="magenta" onclick="selectNode('${{d.id}}')"><span>${{d.id}}</span> <span style="color:#94a3b8">t=${{d.version ?? '-'}}</span></li>`;
      }});

      const ancIds = new Set(ancestors.map(a => a.id));
      const descIds = new Set(descendants.map(d => d.id));

      nodesDataset.forEach(n => {{
        const orig = rawNodes.find(o => o.id === n.id) || n;
        const styleProps = getNodeStyleProps(orig);

        if (n.id === nodeId) {{
          nodesDataset.update({{ id: n.id, borderWidth: 4, color: {{ border: "#ffffff", background: "#f59e0b" }}, shapeProperties: {{ borderDashes: false }} }});
        }} else if (ancIds.has(n.id)) {{
          nodesDataset.update({{ id: n.id, borderWidth: 3, color: {{ border: "#38bdf8", background: styleProps.color.background }}, shapeProperties: styleProps.shapeProperties }});
        }} else if (descIds.has(n.id)) {{
          nodesDataset.update({{ id: n.id, borderWidth: 3, color: {{ border: "#f43f5e", background: styleProps.color.background }}, shapeProperties: styleProps.shapeProperties }});
        }} else {{
          nodesDataset.update({{ id: n.id, borderWidth: 1, color: {{ border: "#1f2937", background: "#0f172a" }}, shapeProperties: styleProps.shapeProperties }});
        }}
      }});

      edgesDataset.forEach(e => {{
        const isAnc = ancIds.has(e.from) && (ancIds.has(e.to) || e.to === nodeId);
        const isDesc = (e.from === nodeId && descIds.has(e.to)) || (descIds.has(e.from) && descIds.has(e.to));
        if (isAnc) edgesDataset.update({{ id: e.id, color: {{ color: "#38bdf8" }}, width: 3.5 }});
        else if (isDesc) edgesDataset.update({{ id: e.id, color: {{ color: "#f43f5e" }}, width: 3.5 }});
        else edgesDataset.update({{ id: e.id, color: {{ color: "#374151" }}, width: 1 }});
      }});

      switchTab('tab-inspector');
    }}

    function jumpToPromoteSelected() {{
      if (!currentSelectedNodeId) return;
      switchTab('tab-ops');
      const sel = document.getElementById("promote-source-select");
      sel.value = currentSelectedNodeId;
      onPromoteSourceChange(currentSelectedNodeId);
    }}

    function onPromoteSourceChange(nodeId) {{
      const node = rawNodes.find(n => n.id === nodeId);
      if (!node) return;
      const suggestedId = node.rawId.replace(/^temp-/, "Data_Confirmed_").replace(/^prov-/, "Data_Confirmed_");
      document.getElementById("promote-new-id").value = suggestedId + "_DOI";
    }}

    function clearSelection() {{
      currentSelectedNodeId = null;
      document.getElementById("quick-target-select").value = "";
      document.getElementById("quick-promote-area").style.display = "none";
      document.getElementById("selected-node-info").innerText = "ノードをクリックすると過去起源と将来影響が発光します。";
      document.getElementById("ancestor-list").innerHTML = "";
      document.getElementById("descendant-list").innerHTML = "";
      document.getElementById("ancestor-count").innerText = "0 件";
      document.getElementById("descendant-count").innerText = "0 件";

      nodesDataset.forEach(n => {{
        const orig = rawNodes.find(o => o.id === n.id) || n;
        const styleProps = getNodeStyleProps(orig);
        nodesDataset.update({{
          id: n.id,
          borderWidth: styleProps.borderWidth,
          color: styleProps.color,
          shapeProperties: styleProps.shapeProperties
        }});
      }});

      edgesDataset.forEach(e => {{
        const isInter = (e.edge_type === "inter");
        const isShared = (e.from.includes("Shared") || e.to.includes("Shared"));
        edgesDataset.update({{ id: e.id, color: {{ color: isShared ? "#eab308" : (isInter ? "#fb923c" : "#475569") }}, width: isShared ? 3.0 : (isInter ? 2.2 : 1.2) }});
      }});
    }}

    function findAncestors(targetId) {{
      const visited = new Set();
      const queue = [targetId];
      while (queue.length > 0) {{
        const curr = queue.shift();
        rawEdges.filter(e => e.to === curr).forEach(e => {{
          if (!visited.has(e.from)) {{
            visited.add(e.from);
            queue.push(e.from);
          }}
        }});
      }}
      return Array.from(visited).map(id => rawNodes.find(n => n.id === id)).filter(Boolean);
    }}

    function findDescendants(sourceId) {{
      const visited = new Set();
      const queue = [sourceId];
      while (queue.length > 0) {{
        const curr = queue.shift();
        rawEdges.filter(e => e.from === curr).forEach(e => {{
          if (!visited.has(e.to)) {{
            visited.add(e.to);
            queue.push(e.to);
          }}
        }});
      }}
      return Array.from(visited).map(id => rawNodes.find(n => n.id === id)).filter(Boolean);
    }}

    function onQuickSelectChange(nodeId) {{
      if (nodeId) selectNode(nodeId);
      else clearSelection();
    }}

    function filterByVersion(v) {{
      const typeFilter = document.getElementById("filter-type-select").value;
      applyFilters(v, typeFilter);
    }}

    function filterByType(t) {{
      const versionFilter = document.getElementById("filter-version-select").value;
      applyFilters(versionFilter, t);
    }}

    function applyFilters(vFilter, tFilter) {{
      nodesDataset.forEach(n => {{
        const orig = rawNodes.find(o => o.id === n.id);
        const matchVersion = (vFilter === "ALL" || orig.version === parseInt(vFilter));
        const matchType = (tFilter === "ALL" || orig.type === tFilter);
        nodesDataset.update({{ id: n.id, hidden: !(matchVersion && matchType) }});
      }});
    }}

    // 1. 新規データ・論文の追加（仮IDサポート）
    function executeAddNode() {{
      const v = parseInt(document.getElementById("add-node-version").value);
      const nType = document.getElementById("add-node-type").value;
      let rawId = document.getElementById("add-node-id").value.trim();
      const doiVal = document.getElementById("add-node-doi").value.trim();
      const name = document.getElementById("add-node-name").value.trim() || rawId;
      const targetEdgeNode = document.getElementById("add-edge-target").value;
      const edgeRel = document.getElementById("add-edge-relation").value;

      if (!rawId) {{
        generateProvisionalId();
        rawId = document.getElementById("add-node-id").value.trim();
      }}

      const isProv = (!doiVal) || rawId.startsWith("temp-") || rawId.startsWith("prov-");
      const nodeId = `${{rawId}}@t${{v}}`;
      if (rawNodes.some(n => n.id === nodeId)) return alert(`ノード ${{nodeId}} は既に存在します`);

      const colX = (v / 10) * 340 + 100;
      const sameTypeCount = rawNodes.filter(n => n.version === v && n.type === nType).length;
      const nodeY = 400 + (sameTypeCount * 65);

      const baseLabel = `${{rawId}} (t=${{v}})\\n${{name.substring(0, 20)}}`;
      const newNode = {{
        id: nodeId,
        rawId: rawId,
        doi: doiVal,
        isProvisional: isProv,
        type: nType,
        version: v,
        label: baseLabel,
        title: doiVal ? `${{name}} [DOI: ${{doiVal}}]` : `${{name}} [仮ID状態]`,
        x: colX,
        y: nodeY
      }};

      rawNodes.push(newNode);
      const styleProps = getNodeStyleProps(newNode);
      const badgePrefix = isProv ? "[仮ID] " : "[DOI確定] ";

      nodesDataset.add({{
        id: newNode.id,
        label: badgePrefix + baseLabel,
        title: newNode.title,
        color: styleProps.color,
        borderWidth: styleProps.borderWidth,
        shapeProperties: styleProps.shapeProperties,
        font: {{ color: "#ffffff", size: 10, face: "Segoe UI, sans-serif" }},
        shape: "box",
        margin: 8,
        x: newNode.x,
        y: newNode.y,
        physics: false
      }});

      if (targetEdgeNode) {{
        const targetNodeObj = rawNodes.find(n => n.id === targetEdgeNode);
        const isInter = targetNodeObj && (targetNodeObj.version !== v);
        const newEdge = {{
          id: `e_user_${{Date.now()}}`,
          from: nodeId,
          to: targetEdgeNode,
          label: edgeRel,
          edge_type: isInter ? "inter" : "intra",
          relation: edgeRel
        }};
        rawEdges.push(newEdge);
        edgesDataset.add({{
          id: newEdge.id,
          from: newEdge.from,
          to: newEdge.to,
          label: newEdge.label,
          font: {{ size: 8, color: "#94a3b8", strokeWidth: 2, strokeColor: "#0b0f17", align: "middle" }},
          arrows: "to",
          color: {{ color: isInter ? "#fb923c" : "#475569" }},
          width: isInter ? 2.2 : 1.2,
          dashes: !isInter,
          smooth: {{ type: "cubicBezier", forceDirection: "horizontal", roundness: 0.35 }}
        }});
      }}

      tempCounter += 1;
      generateProvisionalId();
      document.getElementById("add-node-doi").value = "";
      document.getElementById("add-node-name").value = "";

      populateDropdowns();
      updateJsonView();
      selectNode(nodeId);
    }}

    // 2. 仮IDから正式DOIへの同型置換アップグレード
    function executePromoteToDoi() {{
      const oldNodeId = document.getElementById("promote-source-select").value;
      const newDoi = document.getElementById("promote-new-doi").value.trim();
      const newRawId = document.getElementById("promote-new-id").value.trim();

      if (!oldNodeId) return alert("置換対象の仮IDノードを選択してください");
      if (!newDoi) return alert("正式な DOI（例: 10.5281/zenodo.9876543）を入力してください");
      if (!newRawId) return alert("確定後のノードIDを入力してください");

      const targetNode = rawNodes.find(n => n.id === oldNodeId);
      if (!targetNode) return;

      const v = targetNode.version;
      const newNodeId = `${{newRawId}}@t${{v}}`;

      if (newNodeId !== oldNodeId && rawNodes.some(n => n.id === newNodeId)) {{
        return alert(`ID ${{newNodeId}} は既に存在します。別のIDを指定してください。`);
      }}

      // 1) ノード属性の同型更新（旧仮IDを prov:alternateOf / formerProvisionalId に履歴保持）
      const oldRawId = targetNode.rawId;
      targetNode.id = newNodeId;
      targetNode.rawId = newRawId;
      targetNode.doi = newDoi;
      targetNode.isProvisional = false;
      targetNode.formerProvisionalId = oldRawId;

      const cleanTitle = targetNode.title.replace(/\s*\[仮ID状態\]$/, "");
      targetNode.title = `${{cleanTitle}} [DOI: ${{newDoi}}]`;
      targetNode.label = `${{newRawId}} (t=${{v}})\\n${{cleanTitle.substring(0, 20)}}`;

      // 2) 全エッジの端点 (from / to) を新しいノードIDへ無矛盾に張り替え
      rawEdges.forEach(e => {{
        if (e.from === oldNodeId) e.from = newNodeId;
        if (e.to === oldNodeId) e.to = newNodeId;
      }});

      // 3) Vis.js データセットの更新（旧ノード削除 -> 同一座標に確定ノード挿入 & エッジ再描画）
      nodesDataset.remove(oldNodeId);
      const styleProps = getNodeStyleProps(targetNode);
      nodesDataset.add({{
        id: targetNode.id,
        label: "[DOI確定] " + targetNode.label,
        title: targetNode.title,
        color: styleProps.color,
        borderWidth: styleProps.borderWidth,
        shapeProperties: styleProps.shapeProperties,
        font: {{ color: "#ffffff", size: 10, face: "Segoe UI, sans-serif" }},
        shape: "box",
        margin: 8,
        x: targetNode.x,
        y: targetNode.y,
        physics: false
      }});

      edgesDataset.clear();
      rawEdges.forEach((e, idx) => {{
        const isInter = (e.edge_type === "inter");
        const isShared = (e.from.includes("Shared") || e.to.includes("Shared"));
        edgesDataset.add({{
          id: e.id || `e_${{idx}}`,
          from: e.from,
          to: e.to,
          label: e.relation || e.label || "",
          font: {{ size: 8, color: "#94a3b8", strokeWidth: 2, strokeColor: "#0b0f17", align: "middle" }},
          arrows: "to",
          color: {{ color: isShared ? "#eab308" : (isInter ? "#fb923c" : "#475569") }},
          width: isShared ? 3.0 : (isInter ? 2.2 : 1.2),
          dashes: !isInter,
          smooth: {{ type: "cubicBezier", forceDirection: "horizontal", roundness: 0.35 }}
        }});
      }});

      document.getElementById("promote-new-doi").value = "";
      document.getElementById("promote-new-id").value = "";

      populateDropdowns();
      updateJsonView();
      selectNode(newNodeId);
      alert(`仮ID (${{oldRawId}}) を正式DOI (${{newDoi}}) へ確定・置換しました。すべての来歴リンクは維持されています。`);
    }}

    // 3. 観点転換関手
    function executePerspectiveShift() {{
      const srcId = document.getElementById("shift-source-select").value;
      const targetType = document.getElementById("shift-target-type-select").value;
      const newRawId = document.getElementById("shift-new-id").value;
      const newName = document.getElementById("shift-new-name").value;
      const newId = `${{newRawId}}@t10`;

      if (!srcId || !newRawId) return alert("入力が不足しています");

      const isProv = newRawId.startsWith("temp-") || newRawId.startsWith("prov-");
      const newNode = {{
        id: newId,
        rawId: newRawId,
        doi: "",
        isProvisional: isProv,
        type: targetType,
        version: 10,
        label: `${{newRawId}} (t=10)\\n${{newName.substring(0, 20)}}`,
        title: `観点転換限界値: ${{newName}}`,
        x: 440,
        y: 470
      }};

      const newEdge = {{
        id: `e_${{Date.now()}}`,
        from: srcId,
        to: newId,
        relation: "PerspectiveShift",
        edge_type: "inter"
      }};

      rawNodes.push(newNode);
      rawEdges.push(newEdge);
      const styleProps = getNodeStyleProps(newNode);
      nodesDataset.add({{
        id: newNode.id,
        label: (isProv ? "[仮ID] " : "") + newNode.label,
        title: newNode.title,
        color: styleProps.color,
        borderWidth: styleProps.borderWidth,
        shapeProperties: styleProps.shapeProperties,
        font: {{ color: "#ffffff", size: 10 }},
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
        font: {{ size: 8, color: "#94a3b8" }},
        arrows: "to",
        color: {{ color: "#fb923c" }},
        width: 2.5
      }});

      populateDropdowns();
      updateJsonView();
      selectNode(newId);
    }}

    // 4. 余極限合成
    function executeColimitSynthesis() {{
      const baseVersion = parseInt(document.getElementById("colimit-source-version-select").value);
      const newRawId = document.getElementById("colimit-new-id").value;
      const newTitle = document.getElementById("colimit-new-title").value;
      const newId = `${{newRawId}}@t20`;
      if (!newRawId) return alert("ノードIDを入力してください");

      const isProv = newRawId.startsWith("temp-") || newRawId.startsWith("prov-");
      const newNode = {{
        id: newId,
        rawId: newRawId,
        doi: "",
        isProvisional: isProv,
        type: "NewPaper",
        version: 20,
        label: `${{newRawId}} (t=20)\\n${{newTitle.substring(0, 20)}}`,
        title: `余極限合成論文: ${{newTitle}}`,
        x: 780,
        y: 120
      }};

      rawNodes.push(newNode);
      const styleProps = getNodeStyleProps(newNode);
      nodesDataset.add({{
        id: newNode.id,
        label: (isProv ? "[仮ID] " : "") + newNode.label,
        title: newNode.title,
        color: styleProps.color,
        borderWidth: styleProps.borderWidth,
        shapeProperties: styleProps.shapeProperties,
        font: {{ color: "#ffffff", size: 10 }},
        shape: "box",
        margin: 8,
        x: newNode.x,
        y: newNode.y,
        physics: false
      }});

      const srcNodes = rawNodes.filter(n => n.version === baseVersion);
      srcNodes.forEach((src, idx) => {{
        const edge = {{
          id: `e_col_${{Date.now()}}_${{idx}}`,
          from: src.id,
          to: newId,
          relation: "ColimitProjection",
          edge_type: "inter"
        }};
        rawEdges.push(edge);
        edgesDataset.add({{
          id: edge.id,
          from: edge.from,
          to: edge.to,
          label: edge.relation,
          font: {{ size: 8, color: "#94a3b8" }},
          arrows: "to",
          color: {{ color: "#fb923c" }},
          width: 2.5
        }});
      }});

      populateDropdowns();
      updateJsonView();
      selectNode(newId);
    }}

    function populateDropdowns() {{
      const targetSelect = document.getElementById("quick-target-select");
      const currentSelected = targetSelect.value;
      targetSelect.innerHTML = '<option value="">-- ノードを選択 --</option>';
      rawNodes.forEach(n => {{
        const tag = n.isProvisional ? "[仮ID] " : "";
        targetSelect.innerHTML += `<option value="${{n.id}}">${{tag}}${{n.id}} (${{n.type}})</option>`;
      }});
      if (currentSelected && rawNodes.some(n => n.id === currentSelected)) {{
        targetSelect.value = currentSelected;
      }}

      // 仮IDノード専用のプルダウン更新
      const promoteSelect = document.getElementById("promote-source-select");
      const provNodes = rawNodes.filter(n => n.isProvisional);
      if (provNodes.length === 0) {{
        promoteSelect.innerHTML = '<option value="">-- 現在仮IDのノードはありません --</option>';
      }} else {{
        promoteSelect.innerHTML = "";
        provNodes.forEach(n => {{
          promoteSelect.innerHTML += `<option value="${{n.id}}">${{n.id}} (${{n.type}})</option>`;
        }});
        onPromoteSourceChange(provNodes[0].id);
      }}

      const shiftSelect = document.getElementById("shift-source-select");
      shiftSelect.innerHTML = "";
      rawNodes.filter(n => n.type === "FailedData" || n.type === "Data").forEach(n => {{
        shiftSelect.innerHTML += `<option value="${{n.id}}">${{n.id}} [t=${{n.version}}]</option>`;
      }});

      const edgeTargetSelect = document.getElementById("add-edge-target");
      edgeTargetSelect.innerHTML = '<option value="">-- 接続しない（単独ノード） --</option>';
      rawNodes.forEach(n => {{
        edgeTargetSelect.innerHTML += `<option value="${{n.id}}">${{n.id}} [t=${{n.version}}] (${{n.type}})</option>`;
      }});
    }}

    function updateJsonView() {{
      const jsonLd = {{
        "@context": {{
          "schema": "http://schema.org/",
          "prov": "http://www.w3.org/ns/prov#",
          "sio": "http://semanticscience.org/resource/",
          "datacite": "http://purl.org/spar/datacite/",
          "cat": "http://example.org/category#"
        }},
        "@graph": rawNodes.map(n => {{
          const entry = {{
            "@id": n.rawId || n.id,
            "@type": n.type,
            "schema:name": n.title || n.label,
            "cat:version": n.version,
            "cat:status": n.isProvisional ? "Provisional" : "Persistent"
          }};
          if (n.doi) {{
            entry["datacite:doi"] = n.doi;
            entry["schema:identifier"] = `https://doi.org/${{n.doi}}`;
          }}
          if (n.formerProvisionalId) {{
            entry["prov:alternateOf"] = n.formerProvisionalId;
          }}
          const derived = rawEdges.filter(e => e.to === n.id).map(e => e.from);
          if (derived.length > 0) {{
            entry["prov:wasDerivedFrom"] = derived;
          }}
          return entry;
        }})
      }};
      document.getElementById("json-editor").value = JSON.stringify(jsonLd, null, 2);
    }}

    function downloadJsonLd() {{
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(document.getElementById("json-editor").value);
      const dlAnchor = document.createElement('a');
      dlAnchor.setAttribute("href", dataStr);
      dlAnchor.setAttribute("download", "categorical_provenance_doi_minted.jsonld");
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

    let isPlaying = false;
    let playTimer = null;

    function togglePlay() {{
      isPlaying = !isPlaying;
      document.getElementById("play-btn").innerText = isPlaying ? "⏸" : "▶";
      if (isPlaying) {{
        playTimer = setInterval(() => {{
          let scrub = document.getElementById("time-scrubber");
          let val = parseInt(scrub.value) + 10;
          if (val > 20) val = 0;
          scrub.value = val;
          onScrub(val);
        }}, 800);
      }} else {{
        clearInterval(playTimer);
      }}
    }}

    function onScrub(v) {{
      const tVal = parseInt(v);
      document.getElementById("time-display").innerText = `t = ${{tVal}}`;
      nodesDataset.forEach(n => {{
        const orig = rawNodes.find(o => o.id === n.id);
        nodesDataset.update({{ id: n.id, hidden: orig.version > tVal }});
      }});
    }}

    function restartSimulation() {{
      document.getElementById("time-scrubber").value = 0;
      onScrub(0);
      if (!isPlaying) togglePlay();
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
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self.HTML_DATA.encode('utf-8'))
        else:
            super().do_GET()


def start_server(data_filepath):
    raw_data = load_or_create_default_data(data_filepath)
    graph_data = convert_snapshots_to_graph(raw_data)
    html_content = build_html_content(graph_data, os.path.basename(data_filepath))
    CustomHandler.HTML_DATA = html_content

    class ReuseTCPServer(socketserver.TCPServer):
        allow_reuse_address = True

    with ReuseTCPServer(("", PORT), CustomHandler) as httpd:
        print("=" * 68)
        print("[*] 圏論的メタデータ探索サーバー起動 (仮ID発行・DOI置換対応版)")
        print(f"[*] 読み込みファイル: {os.path.abspath(data_filepath)}")
        print(f"[*] URL: http://localhost:{PORT}")
        print("[*] 終了するにはターミナルで Ctrl+C を押してください")
        print("=" * 68)
        
        threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] サーバーを停止しました。")
            httpd.server_close()


if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DATA_FILE
    start_server(target_file)
