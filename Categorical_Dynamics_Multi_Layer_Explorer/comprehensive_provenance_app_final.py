"""
Categorical Provenance & Dynamic Metadata Master Explorer
=========================================================
圏論に基づく動的メタデータ構築・多層的データ集積 (t=0 -> t=40) 完全遡及・動的追跡Webシステム
全メニュー（過去データ追加／観点転換／余極限合成／多軸プルダウン／全体リセット／動画再生／JSON-LD同期）統合版
"""

import http.server
import json
import os
import socketserver
import threading
import webbrowser

PORT = 8090
HTML_FILE = "comprehensive_provenance_explorer.html"

# =========================================================================
# 1. 多層的データ集積定義 (t=0 -> t=40)
# =========================================================================
PIPELINE_DATA = {
    "snapshots": [
        {
            "version": 0,
            "description": "t=0 [1965年] 初期実験: 大腸菌への電場印加実験と電極腐食失敗・先行文献",
            "@graph": [
                {
                    "@id": "Nature_1965_Rosenberg",
                    "cat:type": "Paper",
                    "schema:name": "Inhibition of Cell Division in E. coli by Electrolysis (Nature 1965)",
                    "schema:datePublished": "1965",
                    "schema:hasPart": [
                        {"@id": "Data_CellFilamentation"},
                        {"@id": "Data_ElectricFieldGradient"},
                        {"@id": "Material_EColi_B"},
                        {"@id": "Exp_Fail_ElectrodeCorrosion"},
                        {"@id": "Exp_Fail_LowPHPrecipitate"},
                    ],
                    "schema:citation": [
                        {"@id": "Ref_Smith_1958"},
                        {"@id": "Ref_Phillips_1960"},
                    ],
                },
                {
                    "@id": "Data_CellFilamentation",
                    "cat:type": "Data",
                    "schema:name": "E. coli Filamentation Assay (300x elongation)",
                    "sio:has-value": "300x length without division",
                },
                {
                    "@id": "Data_ElectricFieldGradient",
                    "cat:type": "Data",
                    "schema:name": "Electric Field Voltage-Current Response (50-200 V/cm)",
                    "sio:has-value": "120 V/cm continuous",
                },
                {
                    "@id": "Material_EColi_B",
                    "cat:type": "Material",
                    "schema:name": "E. coli Strain B Culture Lot #01 (NH4Cl medium)",
                },
                {
                    "@id": "Exp_Fail_ElectrodeCorrosion",
                    "cat:type": "FailedData",
                    "schema:name": "Unexpected Pt Electrode Corrosion (Unknown Contaminant)",
                    "cat:failureReason": "Inert Pt electrode corroded in NH4Cl broth; formed soluble inorganic byproduct",
                },
                {
                    "@id": "Exp_Fail_LowPHPrecipitate",
                    "cat:type": "FailedData",
                    "schema:name": "Low pH Decomposition Precipitate Log",
                    "cat:failureReason": "Substance hydrolyzed and formed inactive black precipitate under acidic pH < 4.5",
                },
                {
                    "@id": "Ref_Smith_1958",
                    "cat:type": "Reference",
                    "schema:name": "Smith et al. (1958) Physical Effects of Direct Currents on Bacteria",
                },
                {
                    "@id": "Ref_Phillips_1960",
                    "cat:type": "Reference",
                    "schema:name": "Phillips (1960) Coordination Chemistry of Platinum Group Metals",
                },
            ],
        },
        {
            "version": 10,
            "description": "t=10 [1967年] 観点転換・異種分析・新材料投入: 失敗ログの再解釈とシスプラチン合成",
            "perspective_shifts": [
                {
                    "source_id": "Exp_Fail_ElectrodeCorrosion",
                    "new_id": "LimitEntry_PtCytotoxicity",
                    "new_type": "ThermalLimit",
                    "name": "Pt Complex Cell-Division Arrest Activity (IC50 = 2.5 ug/mL)",
                    "note": "Re-evaluated corrosion byproduct as potent chemical inhibitor of chromosomal division",
                },
                {
                    "source_id": "Exp_Fail_LowPHPrecipitate",
                    "new_id": "LimitEntry_HydrolysisKinetics",
                    "new_type": "ThermalLimit",
                    "name": "Aqueous Hydrolysis Rate & pH Stability Boundary",
                    "note": "Re-evaluated acid precipitate as aqueous activation kinetics",
                },
            ],
            "@graph": [
                {
                    "@id": "Data_Spectroscopy_NMR_IR",
                    "cat:type": "Data",
                    "schema:name": "IR & NMR Spectroscopy Coordination Structural Data",
                    "sio:has-value": "Cis-geometry identified (cis-Pt(NH3)2Cl2)",
                },
                {
                    "@id": "Material_Synthesized_Cisplatin",
                    "cat:type": "NewMaterial",
                    "schema:name": "cis-diamminedichloroplatinum(II) [Pure Synthetic Specimen]",
                    "schema:description": "Purely synthesized cis-isomer according to reinterpreted coordination chemistry",
                },
            ],
            "higher_functors": [
                {
                    "from": "Data_CellFilamentation@t0",
                    "to": "Data_CellFilamentation@t10",
                    "transform": "Preserve",
                    "functor": "KanExtension_Sigma",
                },
                {
                    "from": "Material_EColi_B@t0",
                    "to": "Material_EColi_B@t10",
                    "transform": "Preserve",
                    "functor": "KanExtension_Sigma",
                },
                {
                    "from": "Ref_Phillips_1960@t0",
                    "to": "Data_Spectroscopy_NMR_IR@t10",
                    "transform": "GuidedByTheory",
                    "functor": "ColimitProjection",
                },
            ],
        },
        {
            "version": 20,
            "description": "t=20 [1969-1972年] 動物抗腫瘍試験・毒性限界・Nature 1969 論文結実",
            "@graph": [
                {
                    "@id": "Nature_1969_Rosenberg",
                    "cat:type": "NewPaper",
                    "schema:name": "Platinum Compounds: a New Class of Potent Antitumour Agents (Nature 1969)",
                    "schema:datePublished": "1969",
                    "schema:hasPart": [
                        {"@id": "Data_Sarcoma180_TumorRegression"},
                        {"@id": "LimitEntry_NephrotoxicityThreshold"},
                        {"@id": "Material_Synthesized_Cisplatin"},
                    ],
                    "prov:wasDerivedFrom": [{"@id": "Nature_1965_Rosenberg"}],
                },
                {
                    "@id": "Data_Sarcoma180_TumorRegression",
                    "cat:type": "Data",
                    "schema:name": "In Vivo Sarcoma 180 Complete Tumor Regression Curve",
                    "sio:has-value": "100% cure rate at 8 mg/kg",
                },
                {
                    "@id": "LimitEntry_NephrotoxicityThreshold",
                    "cat:type": "ThermalLimit",
                    "schema:name": "Nephrotoxicity Dose Boundary (BUN/Creatinine Threshold)",
                    "sio:has-value": "Max tolerable single dose 12 mg/kg",
                },
            ],
            "higher_functors": [
                {
                    "from": "LimitEntry_PtCytotoxicity@t10",
                    "to": "Nature_1969_Rosenberg@t20",
                    "transform": "Synthesize",
                    "functor": "ColimitProjection",
                },
                {
                    "from": "LimitEntry_HydrolysisKinetics@t10",
                    "to": "LimitEntry_NephrotoxicityThreshold@t20",
                    "transform": "MechanisticProgression",
                    "functor": "Adjunction",
                },
                {
                    "from": "Material_Synthesized_Cisplatin@t10",
                    "to": "Nature_1969_Rosenberg@t20",
                    "transform": "IntegrateNew",
                    "functor": "Pushout",
                },
                {
                    "from": "Data_CellFilamentation@t10",
                    "to": "Data_Sarcoma180_TumorRegression@t20",
                    "transform": "TranslateCellToAnimal",
                    "functor": "KanExtension",
                },
                {
                    "from": "Nature_1965_Rosenberg@t0",
                    "to": "Nature_1969_Rosenberg@t20",
                    "transform": "EvolvesFrom",
                    "functor": "Lineage",
                },
            ],
        },
        {
            "version": 30,
            "description": "t=30 [1999年] X線結晶構造解析によるDNA付加体分子機序解明論文",
            "@graph": [
                {
                    "@id": "Nature_1999_Lippard",
                    "cat:type": "NewPaper",
                    "schema:name": "Crystal Structure of Major DNA Adduct of Cisplatin (Nature 1999)",
                    "schema:datePublished": "1999",
                    "schema:hasPart": [
                        {"@id": "Data_XrayCrystallography_PDB"},
                        {"@id": "Material_DuplexDNA_Adduct"},
                    ],
                    "prov:wasDerivedFrom": [{"@id": "Nature_1969_Rosenberg"}],
                },
                {
                    "@id": "Data_XrayCrystallography_PDB",
                    "cat:type": "Data",
                    "schema:name": "1.9A X-ray Crystallography Coordinate Dataset (PDB: 1AIO)",
                    "sio:has-value": "45-degree DNA bending angle",
                },
                {
                    "@id": "Material_DuplexDNA_Adduct",
                    "cat:type": "Material",
                    "schema:name": "Self-complementary 16-base-pair Duplex DNA Complex",
                },
            ],
            "higher_functors": [
                {
                    "from": "Nature_1969_Rosenberg@t20",
                    "to": "Nature_1999_Lippard@t30",
                    "transform": "StructuralElucidation",
                    "functor": "HigherAdjunction",
                },
                {
                    "from": "Material_Synthesized_Cisplatin@t10",
                    "to": "Material_DuplexDNA_Adduct@t30",
                    "transform": "ComplexFormation",
                    "functor": "Pushout",
                },
            ],
        },
        {
            "version": 40,
            "description": "t=40 [2026年 最新論文] 白金ナノキャリア標的送達・耐性克服論文 (最先端の到達点)",
            "@graph": [
                {
                    "@id": "Paper_2026_AdvancedTherapeutics",
                    "cat:type": "NewPaper",
                    "schema:name": "Targeted Pt(IV) Polymer Nanocarriers Overcoming Multi-Drug Resistance (Adv Ther 2026)",
                    "schema:datePublished": "2026",
                    "schema:hasPart": [
                        {"@id": "Data_NanoparticleTargeting_PK"},
                        {"@id": "Material_PtIV_PEG_Nanoparticle"},
                    ],
                    "prov:wasDerivedFrom": [{"@id": "Nature_1999_Lippard"}],
                },
                {
                    "@id": "Data_NanoparticleTargeting_PK",
                    "cat:type": "Data",
                    "schema:name": "Tumor Accumulation Pharmacokinetics & Zero Renal Toxicity Curve",
                    "sio:has-value": "15x tumor uptake, 0% acute kidney injury",
                },
                {
                    "@id": "Material_PtIV_PEG_Nanoparticle",
                    "cat:type": "NewMaterial",
                    "schema:name": "pH-Responsive Pt(IV) Prodrug PEG-PLGA Nanoparticles",
                },
            ],
            "higher_functors": [
                {
                    "from": "Nature_1999_Lippard@t30",
                    "to": "Paper_2026_AdvancedTherapeutics@t40",
                    "transform": "MechanismInformedDesign",
                    "functor": "HigherAdjunction",
                },
                {
                    "from": "Data_XrayCrystallography_PDB@t30",
                    "to": "Paper_2026_AdvancedTherapeutics@t40",
                    "transform": "StructureBasedDrugDesign",
                    "functor": "ColimitProjection",
                },
                {
                    "from": "LimitEntry_NephrotoxicityThreshold@t20",
                    "to": "Data_NanoparticleTargeting_PK@t40",
                    "transform": "OvercomingToxicityBoundary",
                    "functor": "PerspectiveShift",
                },
            ],
        },
    ]
}


def build_html():
    LAYER_Y = {
        "NewPaper": 40,
        "Paper": 80,
        "Reference": 200,
        "Data": 310,
        "ThermalLimit": 430,
        "Material": 550,
        "NewMaterial": 640,
        "FailedData": 730,
        "Entity": 830,
    }

    COLOR_MAP = {
        "Paper": "#1d4ed8",
        "NewPaper": "#7e22ce",
        "Data": "#0891b2",
        "FailedData": "#b91c1c",
        "ThermalLimit": "#be185d",
        "Material": "#15803d",
        "NewMaterial": "#c2410c",
        "Reference": "#4b5563",
        "Entity": "#334155",
    }

    # グラフ構築
    nodes_dict = {}
    edges_list = []

    for idx, snap in enumerate(PIPELINE_DATA["snapshots"]):
        v = snap["version"]

        # Perspective Shift
        for s in snap.get("perspective_shifts", []):
            prev_v = PIPELINE_DATA["snapshots"][idx - 1]["version"]
            src_node = f"{s['source_id']}@t{prev_v}"
            tgt_node = f"{s['new_id']}@t{v}"
            if src_node in nodes_dict:
                nodes_dict[tgt_node] = {
                    "id": tgt_node,
                    "rawId": s["new_id"],
                    "type": s["new_type"],
                    "version": v,
                    "label": f"{s['name']}\n[t={v}]",
                    "title": f"{s['name']} (Reinterpreted from {s['source_id']})",
                }
                edges_list.append(
                    {
                        "from": src_node,
                        "to": tgt_node,
                        "edge_type": "inter",
                        "label": "PerspectiveShift",
                    }
                )

        # Graph Nodes
        for node in snap.get("@graph", []):
            raw_id = node["@id"]
            node_id = f"{raw_id}@t{v}"
            node_type = node.get("cat:type", "Entity")
            name = node.get("schema:name", raw_id)
            val = node.get("sio:has-value", "")
            fail_reason = node.get("cat:failureReason", "")

            title_desc = name
            if val:
                title_desc += f" (Value: {val})"
            if fail_reason:
                title_desc += f" [Failure: {fail_reason}]"

            nodes_dict[node_id] = {
                "id": node_id,
                "rawId": raw_id,
                "type": node_type,
                "version": v,
                "label": f"{name}\n[t={v}]",
                "title": title_desc,
            }

            for key, targets in node.items():
                if any(key.startswith(p) for p in ["schema:", "prov:", "sio:"]):
                    t_list = (
                        targets if isinstance(targets, list) else [targets]
                    )
                    for tgt in t_list:
                        if isinstance(tgt, dict) and "@id" in tgt:
                            tgt_id = f"{tgt['@id']}@t{v}"
                            if tgt_id not in nodes_dict:
                                nodes_dict[tgt_id] = {
                                    "id": tgt_id,
                                    "rawId": tgt["@id"],
                                    "type": "Entity",
                                    "version": v,
                                    "label": f"{tgt['@id']}\n[t={v}]",
                                    "title": tgt["@id"],
                                }
                            edges_list.append(
                                {
                                    "from": node_id,
                                    "to": tgt_id,
                                    "edge_type": "intra",
                                    "label": key,
                                }
                            )

        # Higher Functors
        for hf in snap.get("higher_functors", []):
            edges_list.append(
                {
                    "from": hf["from"],
                    "to": hf["to"],
                    "edge_type": "inter",
                    "label": hf.get("transform", "FunctorMapping"),
                }
            )

    x_step = 320
    slot_tracker = {}
    vis_nodes = []
    for n_id, attr in nodes_dict.items():
        n_type = attr["type"]
        v = attr["version"]
        col_x = (v // 10) * x_step + 80
        base_y = LAYER_Y.get(n_type, 450)
        slot_key = (v, n_type)
        slot_idx = slot_tracker.get(slot_key, 0)
        slot_tracker[slot_key] = slot_idx + 1
        node_y = base_y + (slot_idx * 70)

        vis_nodes.append(
            {
                "id": n_id,
                "rawId": attr["rawId"],
                "type": n_type,
                "version": v,
                "label": attr["label"],
                "title": attr["title"],
                "color": {
                    "background": COLOR_MAP.get(n_type, "#334155"),
                    "border": "#ffffff",
                },
                "font": {
                    "color": "#ffffff",
                    "size": 10,
                    "face": "Segoe UI, sans-serif",
                },
                "shape": "box",
                "margin": 8,
                "x": col_x,
                "y": node_y,
                "fixed": {"x": True, "y": False},
            }
        )

    vis_edges = []
    for idx, e in enumerate(edges_list):
        is_inter = e["edge_type"] == "inter"
        vis_edges.append(
            {
                "id": f"e_{idx}",
                "from": e["from"],
                "to": e["to"],
                "label": e["label"],
                "edge_type": e["edge_type"],
                "arrows": "to",
                "font": {
                    "size": 8,
                    "color": "#94a3b8",
                    "strokeWidth": 2,
                    "strokeColor": "#0b0f17",
                    "align": "middle",
                },
                "color": {
                    "color": "#fb923c" if is_inter else "#475569",
                    "highlight": "#38bdf8",
                },
                "width": 2.5 if is_inter else 1.2,
                "dashes": not is_inter,
                "smooth": {
                    "type": "cubicBezier",
                    "forceDirection": "horizontal",
                    "roundness": 0.35,
                },
            }
        )

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <title>Categorical Provenance & Dynamic Metadata Master Explorer</title>
  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    :root {{
      --bg: #07090e;
      --panel: #111827;
      --header-bg: #0f172a;
      --border: #1f2937;
      --cyan: #38bdf8;
      --magenta: #f43f5e;
      --orange: #fb923c;
      --purple: #a855f7;
      --green: #22c55e;
      --text: #f3f4f6;
      --text-muted: #9ca3af;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      overflow: hidden;
      height: 100vh;
      display: flex;
      flex-direction: column;
    }}

    header {{
      background: var(--header-bg);
      border-bottom: 1px solid var(--border);
      padding: 0 14px;
      height: 48px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      z-index: 100;
      gap: 10px;
    }}
    .header-title-group {{ display: flex; align-items: center; gap: 8px; }}
    h1 {{ font-size: 13px; font-weight: 700; color: var(--cyan); white-space: nowrap; }}
    .badge {{ background: #0284c7; color: white; font-size: 9px; padding: 2px 6px; border-radius: 4px; }}
    
    .quick-trace-group {{ display: flex; align-items: center; gap: 6px; }}
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
      padding: 3px 6px;
      border-radius: 4px;
      font-size: 11px;
      max-width: 170px;
    }}
    button {{
      background: #2563eb;
      color: white;
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
    button.btn-cyan {{ background: #0284c7; }}
    button.btn-cyan:hover {{ background: #0369a1; }}
    button.btn-orange {{ background: #ea580c; }}
    button.btn-orange:hover {{ background: #f97316; }}
    button.btn-purple {{ background: #7c3aed; }}
    button.btn-purple:hover {{ background: #8b5cf6; }}
    button.btn-green {{ background: #16a34a; }}
    button.btn-green:hover {{ background: #22c55e; }}
    button.btn-secondary {{ background: #374151; }}
    button.btn-secondary:hover {{ background: #4b5563; }}

    .main-stage {{
      flex: 1;
      display: flex;
      height: calc(100vh - 48px - 44px);
      position: relative;
    }}
    .canvas-container {{
      flex: 1;
      display: flex;
      flex-direction: column;
      position: relative;
    }}
    .timeline-guides {{
      height: 26px;
      background: rgba(17, 24, 39, 0.85);
      border-bottom: 1px dashed var(--border);
      display: flex;
      font-size: 10px;
      color: var(--text-muted);
      font-weight: 600;
      z-index: 10;
    }}
    .col-header {{
      width: {x_step}px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-right: 1px dashed var(--border);
    }}
    #network-canvas {{
      flex: 1;
      width: 100%;
      height: 100%;
      background: radial-gradient(circle at center, #111827 0%, #030712 100%);
    }}

    .legend-box {{
      position: absolute;
      bottom: 12px;
      left: 12px;
      background: rgba(17, 24, 39, 0.94);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 8px 12px;
      font-size: 10px;
      pointer-events: none;
      backdrop-filter: blur(6px);
      z-index: 20;
    }}
    .legend-row {{ display: flex; align-items: center; gap: 6px; margin-bottom: 2px; }}
    .dot {{ width: 8px; height: 8px; border-radius: 2px; }}

    .sidebar {{
      width: 440px;
      background: var(--panel);
      border-left: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      z-index: 30;
    }}
    .tabs {{ display: flex; border-bottom: 1px solid var(--border); background: #0b0f17; }}
    .tab-btn {{
      flex: 1;
      padding: 9px 4px;
      background: transparent;
      border: none;
      border-bottom: 2px solid transparent;
      color: var(--text-muted);
      cursor: pointer;
      font-size: 11px;
      text-align: center;
    }}
    .tab-btn.active {{ color: #fff; border-bottom-color: var(--cyan); background: var(--panel); font-weight: 700; }}
    .tab-content {{ flex: 1; overflow-y: auto; padding: 12px; display: none; flex-direction: column; gap: 10px; }}
    .tab-content.active {{ display: flex; }}

    .card {{
      background: #0b0f17;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 10px;
      font-size: 11px;
    }}
    .card h3 {{
      font-size: 11px;
      margin-bottom: 6px;
      color: var(--cyan);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .tree-group {{ margin-bottom: 8px; }}
    .tree-stage-title {{
      font-size: 10px;
      font-weight: 700;
      color: var(--orange);
      border-bottom: 1px solid #1f2937;
      padding-bottom: 2px;
      margin-bottom: 3px;
    }}
    .tree-item {{
      padding: 4px 7px;
      margin-bottom: 2px;
      border-left: 3px solid var(--cyan);
      background: rgba(56, 189, 248, 0.05);
      border-radius: 0 4px 4px 0;
      font-size: 10px;
      cursor: pointer;
      transition: all 0.15s;
    }}
    .tree-item:hover {{ background: rgba(56, 189, 248, 0.15); }}
    .tree-item.failed {{
      border-left-color: var(--magenta);
      background: rgba(244, 63, 94, 0.08);
    }}
    .tree-item.failed:hover {{ background: rgba(244, 63, 94, 0.2); }}

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
      width: 100%;
    }}

    textarea {{
      width: 100%;
      height: 260px;
      background: #05070c;
      color: #38bdf8;
      border: 1px solid var(--border);
      border-radius: 4px;
      font-family: monospace;
      font-size: 10px;
      padding: 8px;
      resize: vertical;
    }}

    footer {{
      height: 44px;
      background: #0f172a;
      border-top: 1px solid var(--border);
      display: flex;
      align-items: center;
      padding: 0 16px;
      gap: 14px;
      z-index: 100;
    }}
    .playback-btn {{
      width: 28px; height: 28px;
      border-radius: 50%;
      background: #2563eb;
      border: none;
      display: flex; align-items: center; justify-content: center;
      padding: 0;
      font-size: 13px;
    }}
    .timeline-slider-wrap {{
      flex: 1;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    input[type=range] {{
      flex: 1;
      accent-color: #38bdf8;
      cursor: pointer;
    }}
    .subtitle-ticker {{
      font-size: 11px;
      color: #38bdf8;
      background: rgba(15, 23, 42, 0.8);
      padding: 3px 10px;
      border-radius: 12px;
      border: 1px solid var(--border);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 480px;
    }}
  </style>
</head>
<body>
  <header>
    <div class="header-title-group">
      <h1>Categorical Metadata Explorer <span class="badge">t=0 -> t=40</span></h1>
    </div>

    <!-- クイック遡及ボタン群 -->
    <div class="quick-trace-group">
      <button class="btn-cyan" onclick="traceTarget('Paper_2026_AdvancedTherapeutics@t40')">
        ★ 最新論文(2026)から遡及
      </button>
      <button class="btn-secondary" onclick="traceTarget('Nature_1999_Lippard@t30')">
        1999年構造論文
      </button>
      <button class="btn-secondary" onclick="traceTarget('Nature_1969_Rosenberg@t20')">
        1969年抗がん剤
      </button>
    </div>

    <!-- 検索・絞り込みプルダウン群 -->
    <div class="quick-trace-group">
      <div class="selector-box">
        <label style="color:#9ca3af;">🎯 探索:</label>
        <select id="node-selector" onchange="onSelectNodeChange(this.value)">
          <option value="">-- 全ノード一覧 --</option>
        </select>
      </div>

      <div class="selector-box">
        <label style="color:#9ca3af;">⏳ 時間:</label>
        <select id="filter-version" onchange="filterVersion(this.value)">
          <option value="ALL">全時間層</option>
          <option value="0">t=0 (1965 初期)</option>
          <option value="10">t=10 (1967 転換)</option>
          <option value="20">t=20 (1969 動物)</option>
          <option value="30">t=30 (1999 構造)</option>
          <option value="40">t=40 (2026 最新)</option>
        </select>
      </div>

      <div class="selector-box">
        <label style="color:#9ca3af;">🏷️ 種別:</label>
        <select id="filter-type" onchange="filterType(this.value)">
          <option value="ALL">全種別</option>
          <option value="Paper">Paper</option>
          <option value="NewPaper">NewPaper</option>
          <option value="Data">Data</option>
          <option value="FailedData">FailedData</option>
          <option value="ThermalLimit">ThermalLimit</option>
          <option value="Material">Material</option>
          <option value="NewMaterial">NewMaterial</option>
          <option value="Reference">Reference</option>
        </select>
      </div>

      <button class="btn-danger" onclick="resetAllState()">⟲ リセット</button>
      <button class="btn-secondary" onclick="resetView()">センタリング</button>
    </div>
  </header>

  <div class="main-stage">
    <div class="canvas-container">
      <div class="timeline-guides">
        <div class="col-header">[t=0] 1965年 初期実験・腐食失敗</div>
        <div class="col-header">[t=10] 観点転換・分光分析・シスプラチン</div>
        <div class="col-header">[t=20] 1969年 抗腫瘍試験・毒性限界・Nature</div>
        <div class="col-header">[t=30] 1999年 X線DNA付加体構造解明</div>
        <div class="col-header">[t=40] 2026年 次世代ナノキャリア最新論文</div>
      </div>

      <div id="network-canvas"></div>

      <div class="legend-box">
        <div style="font-weight:700; margin-bottom:4px; color:#fff;">階層凡例</div>
        <div class="legend-row"><div class="dot" style="background:#7e22ce;"></div>新論文 (NewPaper)</div>
        <div class="legend-row"><div class="dot" style="background:#1d4ed8;"></div>初期論文 (Paper)</div>
        <div class="legend-row"><div class="dot" style="background:#0891b2;"></div>測定データ (Data)</div>
        <div class="legend-row"><div class="dot" style="background:#b91c1c;"></div>失敗/アノマリー (FailedData)</div>
        <div class="legend-row"><div class="dot" style="background:#be185d;"></div>再解釈限界値 (ThermalLimit)</div>
        <div class="legend-row"><div class="dot" style="background:#c2410c;"></div>新材料標本 (NewMaterial)</div>
        <div class="legend-row"><div class="dot" style="background:#15803d;"></div>材料試料 (Material)</div>
        <div class="legend-row"><div class="dot" style="background:#4b5563;"></div>先行文献 (Reference)</div>
        <hr style="margin:3px 0; border:0; border-top:1px solid #374151;">
        <div style="color:#fb923c; font-weight:bold;">― 太線オレンジ: 関手射 (Inter-fiber)</div>
        <div style="color:#9ca3af;">┄ 破線グレー: 同時間内構造 (Intra-fiber)</div>
      </div>
    </div>

    <!-- 右側サイドバー (3タブ構成) -->
    <div class="sidebar">
      <div class="tabs">
        <button class="tab-btn active" onclick="switchTab('tab-trace')">ルーツ遡及ツリー</button>
        <button class="tab-btn" onclick="switchTab('tab-ops')">圏論操作メニュー</button>
        <button class="tab-btn" onclick="switchTab('tab-json')">JSON-LD ライブ</button>
      </div>

      <!-- タブ1: 完全ルーツ遡及ツリー -->
      <div id="tab-trace" class="tab-content active">
        <div class="card">
          <h3>
            選択ノード属性
            <span id="selected-badge" style="color:var(--cyan); font-size:10px;"></span>
          </h3>
          <div id="target-details" style="color:var(--text-muted); line-height:1.4;">
            上のクイックボタンまたはキャンバス上のノードをクリックしてください。
          </div>
        </div>

        <div class="card">
          <h3>
            過去遡及ルーツ (Backward Provenance)
            <span id="ancestor-count" style="color:var(--cyan);">0 件</span>
          </h3>
          <div id="tree-container">
            <p style="color:var(--text-muted); font-size:10px;">選択ノードが依存する全過去データ・失敗ログ・中間論文が世代順にリストアップされます。</p>
          </div>
        </div>

        <div class="card">
          <h3>
            将来波及影響 (Forward Impact)
            <span id="descendant-count" style="color:var(--magenta);">0 件</span>
          </h3>
          <ul id="descendant-list" style="list-style:none; max-height:120px; overflow-y:auto;"></ul>
        </div>
      </div>

      <!-- タブ2: 復活・充実した圏論操作メニュー群 -->
      <div id="tab-ops" class="tab-content">
        <!-- 1. 過去論文・データの追加フォーム -->
        <div class="card" style="border-left: 3px solid var(--green);">
          <h3 style="color: var(--green);">＋ 過去論文・データの新規追加</h3>
          <p style="font-size:10px; color:var(--text-muted); margin-bottom:5px;">任意の時間層に論文・データ・試料を配置し既存ノードと関連付けます。</p>
          
          <div class="form-group">
            <label>配置先時間層 (Version t):</label>
            <select id="add-node-version">
              <option value="0">t=0 (1965年 初期実験層)</option>
              <option value="10">t=10 (1967年 観点転換・分光層)</option>
              <option value="20">t=20 (1969年 動物試験・Nature層)</option>
              <option value="30">t=30 (1999年 X線構造論文層)</option>
              <option value="40">t=40 (2026年 最新論文層)</option>
            </select>
          </div>
          <div class="form-group">
            <label>ノード種別 (Type):</label>
            <select id="add-node-type">
              <option value="Paper">Paper (論文)</option>
              <option value="Data">Data (測定データ)</option>
              <option value="FailedData">FailedData (失敗実験データ)</option>
              <option value="Material">Material (材料標本)</option>
              <option value="Reference">Reference (先行文献)</option>
            </select>
          </div>
          <div class="form-group">
            <label>ノードID (@id):</label>
            <input type="text" id="add-node-id" placeholder="例: Paper_Smith_1964 / Data_Assay_02">
          </div>
          <div class="form-group">
            <label>名称・タイトル (schema:name):</label>
            <input type="text" id="add-node-name" placeholder="例: Early Observation of Ammonium Electrolysis">
          </div>
          
          <div class="form-group">
            <label>接続先ノード (Target):</label>
            <select id="add-edge-target">
              <option value="">-- 接続しない（単独ノード） --</option>
            </select>
          </div>
          <div class="form-group">
            <label>関係性射 (Relation):</label>
            <select id="add-edge-relation">
              <option value="schema:hasPart">schema:hasPart (構成要素として含む)</option>
              <option value="schema:citation">schema:citation (文献を引用する)</option>
              <option value="prov:wasDerivedFrom">prov:wasDerivedFrom (〜から派生した)</option>
              <option value="sio:has-attribute">sio:has-attribute (属性を付与する)</option>
            </select>
          </div>
          <button class="btn-green" style="width:100%; margin-top:2px;" onclick="executeAddNode()">＋ ノードと射をグラフへ追加</button>
        </div>

        <!-- 2. 観点転換関手 (Perspective Shift) フォーム -->
        <div class="card" style="border-left: 3px solid var(--orange);">
          <h3 style="color: var(--orange);">★ 観点転換関手 (Perspective Shift)</h3>
          <p style="font-size:10px; color:var(--text-muted); margin-bottom:5px;">失敗・アノマリーデータを境界値として再定義し新時間層へ移行します。</p>
          
          <div class="form-group">
            <label>転換元ノード (プルダウン選択):</label>
            <select id="shift-source-select"></select>
          </div>
          <div class="form-group">
            <label>変換先カテゴリ型 (新対象):</label>
            <select id="shift-target-type-select">
              <option value="ThermalLimit">ThermalLimit (耐熱・活性限界値)</option>
              <option value="Data">Data (正常データへ昇華)</option>
              <option value="Material">Material (副生成物標本)</option>
            </select>
          </div>
          <div class="form-group">
            <label>新ノードID:</label>
            <input type="text" id="shift-new-id" value="LimitEntry_CustomBoundary">
          </div>
          <div class="form-group">
            <label>再定義名 (schema:name):</label>
            <input type="text" id="shift-new-name" value="Electrochemical Byproduct Toxicity Threshold">
          </div>
          <button class="btn-orange" style="width:100%; margin-top:2px;" onclick="executePerspectiveShift()">観点転換を実行 (Shift Functor)</button>
        </div>

        <!-- 3. 余極限合成 (Colimit / Pushout) フォーム -->
        <div class="card" style="border-left: 3px solid var(--purple);">
          <h3 style="color: var(--purple);">★ 余極限合成 (Colimit / Pushout)</h3>
          <p style="font-size:10px; color:var(--text-muted); margin-bottom:5px;">再解釈された限界値や新材料を統合し新成果・新論文を創出します。</p>
          
          <div class="form-group">
            <label>統合対象の基準時間層:</label>
            <select id="colimit-source-version-select">
              <option value="10">t=10 (観点転換・分光層から合成)</option>
              <option value="20">t=20 (動物試験層から合成)</option>
              <option value="30">t=30 (X線構造層から合成)</option>
            </select>
          </div>
          <div class="form-group">
            <label>新論文ノードID:</label>
            <input type="text" id="colimit-new-id" value="Paper_FutureDiscovery_2030">
          </div>
          <div class="form-group">
            <label>論文タイトル (schema:name):</label>
            <input type="text" id="colimit-new-title" value="Next-Gen Platinum Nanotherapeutics Synthesis">
          </div>
          <button class="btn-purple" style="width:100%; margin-top:2px;" onclick="executeColimitSynthesis()">新論文を創出 (Colimit Projection)</button>
        </div>
      </div>

      <!-- タブ3: JSON-LD ライブ同期 & ダウンロード -->
      <div id="tab-json" class="tab-content">
        <div class="card">
          <h3>
            W3C PROV-O / SIO 準拠 JSON-LD
            <button class="btn-secondary" style="font-size:10px; padding:2px 6px;" onclick="downloadJsonLd()">JSONダウンロード</button>
          </h3>
          <textarea id="json-box" spellcheck="false"></textarea>
        </div>
      </div>
    </div>
  </div>

  <!-- 下部動画的コントローラー -->
  <footer>
    <div style="display:flex; align-items:center; gap:8px;">
      <button class="playback-btn" id="play-btn" onclick="togglePlay()">▶</button>
      <button class="btn-secondary" style="padding:4px 8px; font-size:10px;" onclick="restartSimulation()">⟲ 最初から</button>
    </div>

    <div class="timeline-slider-wrap">
      <span style="font-size:11px; color:var(--cyan); font-weight:700;">EVOLUTION:</span>
      <input type="range" id="time-scrubber" min="0" max="40" step="0.5" value="40" oninput="onScrub(this.value)">
      <span id="time-display" style="font-size:11px; color:#fff; font-weight:700; min-width:55px;">t = 40.0</span>
    </div>

    <div class="subtitle-ticker" id="synopsis-ticker">
      t=40.0: 最新論文 (Adv Ther 2026) への全系譜が接続完了。40年間の全ルーツを遡及可能。
    </div>
  </footer>

  <script>
    const initialNodes = {json.dumps(vis_nodes, ensure_ascii=False)};
    const initialEdges = {json.dumps(vis_edges, ensure_ascii=False)};
    const typeColors = {json.dumps(COLOR_MAP, ensure_ascii=False)};
    const layerYOrder = {json.dumps(LAYER_Y, ensure_ascii=False)};

    let rawNodes = JSON.parse(JSON.stringify(initialNodes));
    let rawEdges = JSON.parse(JSON.stringify(initialEdges));

    const nodesDataset = new vis.DataSet(rawNodes);
    const edgesDataset = new vis.DataSet(rawEdges);
    const container = document.getElementById('network-canvas');
    const data = {{ nodes: nodesDataset, edges: edgesDataset }};

    const options = {{
      physics: {{ enabled: false }},
      interaction: {{
        hover: true,
        dragNodes: true,
        zoomView: true,
        dragView: true
      }}
    }};

    const network = new vis.Network(container, data, options);

    network.on("click", function(params) {{
      if (params.nodes.length > 0) {{
        selectNode(params.nodes[0]);
      }} else {{
        clearSelection();
      }}
    }});

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

    function selectNode(nodeId) {{
      document.getElementById("node-selector").value = nodeId;

      const node = rawNodes.find(n => n.id === nodeId);
      if (!node) return;

      document.getElementById("selected-badge").innerText = `[${{node.type}} / t=${{node.version}}]`;
      document.getElementById("target-details").innerHTML = `
        <b style="color:#fff; font-size:12px;">${{node.id}}</b><br>
        <span style="color:#38bdf8;">${{node.title}}</span>
      `;

      const ancestors = findAncestors(nodeId);
      const descendants = findDescendants(nodeId);

      document.getElementById("ancestor-count").innerText = `${{ancestors.length}} 件の起源`;
      const treeContainer = document.getElementById("tree-container");
      treeContainer.innerHTML = "";

      if (ancestors.length === 0) {{
        treeContainer.innerHTML = "<p style='color:#6b7280; font-size:10px;'>祖先ノードなし (起点データ/論文)</p>";
      }} else {{
        const versionGroups = {{}};
        ancestors.forEach(a => {{
          if (!versionGroups[a.version]) versionGroups[a.version] = [];
          versionGroups[a.version].push(a);
        }});

        const sortedVersions = Object.keys(versionGroups).map(Number).sort((a,b) => a - b);
        
        sortedVersions.forEach(v => {{
          const groupDiv = document.createElement("div");
          groupDiv.className = "tree-group";
          
          let stageLabel = `時間層 t=${{v}}`;
          if (v === 0) stageLabel += " (1965年 初期実験・電極腐食失敗)";
          else if (v === 10) stageLabel += " (1967年 観点転換・分光分析)";
          else if (v === 20) stageLabel += " (1969年 動物抗腫瘍試験・Nature)";
          else if (v === 30) stageLabel += " (1999年 X線DNA付加体構造論文)";
          else if (v === 40) stageLabel += " (2026年 次世代ナノキャリア最新論文)";

          groupDiv.innerHTML = `<div class="tree-stage-title">${{stageLabel}} [${{versionGroups[v].length}}件]</div>`;
          
          versionGroups[v].forEach(item => {{
            const isFailed = (item.type === "FailedData");
            const itemDiv = document.createElement("div");
            itemDiv.className = `tree-item ${{isFailed ? 'failed' : ''}}`;
            itemDiv.innerHTML = `
              <div style="font-weight:600; color:${{isFailed ? '#f43f5e' : '#38bdf8'}}">${{item.id}}</div>
              <div style="color:#9ca3af; font-size:9px;">${{item.title}}</div>
            `;
            itemDiv.onclick = () => selectNode(item.id);
            groupDiv.appendChild(itemDiv);
          }});

          treeContainer.appendChild(groupDiv);
        }});
      }}

      document.getElementById("descendant-count").innerText = `${{descendants.length}} 件の派生成果`;
      const descList = document.getElementById("descendant-list");
      descList.innerHTML = "";
      if (descendants.length === 0) {{
        descList.innerHTML = "<li style='color:#6b7280; font-size:10px; padding:4px;'>派生先なし (最先端成果)</li>";
      }} else {{
        descendants.sort((a,b) => a.version - b.version).forEach(d => {{
          const li = document.createElement("li");
          li.style.cssText = "padding:3px 6px; margin-bottom:2px; border-left:3px solid #f43f5e; background:rgba(244,63,94,0.06); font-size:10px; cursor:pointer;";
          li.innerHTML = `<b style="color:#f43f5e;">${{d.id}}</b> <span style="color:#9ca3af;">(t=${{d.version}} / ${{d.type}})</span>`;
          li.onclick = () => selectNode(d.id);
          descList.appendChild(li);
        }});
      }}

      const ancIds = new Set(ancestors.map(a => a.id));
      const descIds = new Set(descendants.map(d => d.id));

      nodesDataset.forEach(n => {{
        if (n.id === nodeId) {{
          nodesDataset.update({{ id: n.id, borderWidth: 4, color: {{ border: "#ffffff", background: "#f59e0b" }} }});
        }} else if (ancIds.has(n.id)) {{
          nodesDataset.update({{ id: n.id, borderWidth: 3, color: {{ border: "#38bdf8", background: typeColors[n.type] || "#334155" }} }});
        }} else if (descIds.has(n.id)) {{
          nodesDataset.update({{ id: n.id, borderWidth: 3, color: {{ border: "#f43f5e", background: typeColors[n.type] || "#334155" }} }});
        }} else {{
          nodesDataset.update({{ id: n.id, borderWidth: 1, color: {{ border: "#1f2937", background: "#0f172a" }} }});
        }}
      }});

      edgesDataset.forEach(e => {{
        const isAncEdge = ancIds.has(e.from) && (ancIds.has(e.to) || e.to === nodeId);
        const isDescEdge = (e.from === nodeId && descIds.has(e.to)) || (descIds.has(e.from) && descIds.has(e.to));
        
        if (isAncEdge) {{
          edgesDataset.update({{ id: e.id, color: {{ color: "#38bdf8" }}, width: 3.5 }});
        }} else if (isDescEdge) {{
          edgesDataset.update({{ id: e.id, color: {{ color: "#f43f5e" }}, width: 3.5 }});
        }} else {{
          const isInter = (e.edge_type === "inter");
          edgesDataset.update({{ id: e.id, color: {{ color: isInter ? "#475569" : "#1f2937" }}, width: 1 }});
        }}
      }});

      updateJsonView();
      switchTab('tab-trace');
    }}

    function traceTarget(targetId) {{
      selectNode(targetId);
      network.focus(targetId, {{
        scale: 0.85,
        animation: {{ duration: 700, easingFunction: "easeInOutQuad" }}
      }});
    }}

    function onSelectNodeChange(val) {{
      if (val) selectNode(val);
      else clearSelection();
    }}

    function filterVersion(v) {{
      const typeFilter = document.getElementById("filter-type").value;
      applyFilters(v, typeFilter);
    }}

    function filterType(t) {{
      const versionFilter = document.getElementById("filter-version").value;
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

    function clearSelection() {{
      document.getElementById("node-selector").value = "";
      document.getElementById("selected-badge").innerText = "";
      document.getElementById("target-details").innerText = "ノードをクリックしてください。";
      document.getElementById("tree-container").innerHTML = "<p style='color:#6b7280; font-size:10px;'>探索対象を選択してください。</p>";
      document.getElementById("descendant-list").innerHTML = "";
      document.getElementById("ancestor-count").innerText = "0 件";
      document.getElementById("descendant-count").innerText = "0 件";

      nodesDataset.forEach(n => {{
        const orig = rawNodes.find(o => o.id === n.id);
        if (orig) {{
          nodesDataset.update({{
            id: n.id,
            borderWidth: 1,
            color: {{ border: "#ffffff", background: typeColors[orig.type] || "#334155" }}
          }});
        }}
      }});

      edgesDataset.forEach(e => {{
        const isInter = (e.edge_type === "inter");
        edgesDataset.update({{
          id: e.id,
          color: {{ color: isInter ? "#fb923c" : "#475569" }},
          width: isInter ? 2.5 : 1.2
        }});
      }});

      updateJsonView();
    }}

    function resetAllState() {{
      rawNodes = JSON.parse(JSON.stringify(initialNodes));
      rawEdges = JSON.parse(JSON.stringify(initialEdges));
      
      nodesDataset.clear();
      edgesDataset.clear();
      nodesDataset.add(rawNodes);
      edgesDataset.add(rawEdges);

      document.getElementById("filter-version").value = "ALL";
      document.getElementById("filter-type").value = "ALL";
      document.getElementById("node-selector").value = "";

      clearSelection();
      populateDropdowns();
      updateJsonView();
      resetView();
    }}

    function resetView() {{
      network.fit({{ animation: {{ duration: 600, easingFunction: "easeInOutQuad" }} }});
    }}

    function executeAddNode() {{
      const v = parseInt(document.getElementById("add-node-version").value);
      const nType = document.getElementById("add-node-type").value;
      const rawId = document.getElementById("add-node-id").value.trim();
      const name = document.getElementById("add-node-name").value.trim() || rawId;
      const targetEdgeNode = document.getElementById("add-edge-target").value;
      const edgeRel = document.getElementById("add-edge-relation").value;

      if (!rawId) return alert("ノードID (@id) を入力してください");

      const nodeId = `${{rawId}}@t${{v}}`;
      if (rawNodes.some(n => n.id === nodeId)) {{
        return alert(`ノード ${{nodeId}} は既に存在します`);
      }}

      const colX = (v / 10) * 320 + 80;
      const sameTypeCount = rawNodes.filter(n => n.version === v && n.type === nType).length;
      const baseY = layerYOrder[nType] || 450;
      const nodeY = baseY + (sameTypeCount * 70);

      const newNode = {{
        id: nodeId,
        rawId: rawId,
        type: nType,
        version: v,
        label: `${{rawId}}\\n[t=${{v}}]`,
        title: `${{name}} (Type: ${{nType}}, Version: t=${{v}})`,
        color: {{ background: typeColors[nType] || "#334155", border: "#ffffff" }},
        font: {{ color: "#ffffff", size: 10, face: "Segoe UI, sans-serif" }},
        shape: "box",
        margin: 8,
        x: colX,
        y: nodeY,
        fixed: {{ x: true, y: false }}
      }};

      rawNodes.push(newNode);
      nodesDataset.add(newNode);

      if (targetEdgeNode) {{
        const targetNodeObj = rawNodes.find(n => n.id === targetEdgeNode);
        const isInter = targetNodeObj && (targetNodeObj.version !== v);

        const newEdge = {{
          id: `e_user_${{Date.now()}}`,
          from: nodeId,
          to: targetEdgeNode,
          label: edgeRel,
          edge_type: isInter ? "inter" : "intra",
          relation: edgeRel,
          arrows: "to",
          font: {{ size: 8, color: "#94a3b8", strokeWidth: 2, strokeColor: "#0b0f17", align: "middle" }},
          color: {{ color: isInter ? "#fb923c" : "#475569", highlight: isInter ? "#f97316" : "#94a3b8" }},
          width: isInter ? 2.5 : 1.2,
          dashes: !isInter,
          smooth: {{ type: "cubicBezier", forceDirection: "horizontal", roundness: 0.35 }}
        }};

        rawEdges.push(newEdge);
        edgesDataset.add(newEdge);
      }}

      document.getElementById("add-node-id").value = "";
      document.getElementById("add-node-name").value = "";

      populateDropdowns();
      updateJsonView();
      selectNode(nodeId);
      alert(`ノード ${{nodeId}} を時間層 t=${{v}} に追加しました。`);
    }}

    function executePerspectiveShift() {{
      const srcId = document.getElementById("shift-source-select").value;
      const targetType = document.getElementById("shift-target-type-select").value;
      const newRawId = document.getElementById("shift-new-id").value;
      const newName = document.getElementById("shift-new-name").value;
      const newId = `${{newRawId}}@t10`;
      
      if (!srcId || !newRawId) return alert("入力が不足しています");

      const newNode = {{
        id: newId,
        rawId: newRawId,
        type: targetType,
        version: 10,
        label: `${{newRawId}}\\n[t=10]`,
        title: `観点転換限界値: ${{newName}}`,
        color: {{ background: typeColors[targetType] || "#be185d", border: "#ffffff" }},
        font: {{ color: "#ffffff", size: 10 }},
        shape: "box",
        margin: 8,
        x: 400,
        y: 470,
        fixed: {{ x: true, y: false }}
      }};

      const newEdge = {{
        id: `e_${{Date.now()}}`,
        from: srcId,
        to: newId,
        label: "PerspectiveShift",
        arrows: "to",
        color: {{ color: "#fb923c" }},
        width: 2.5,
        smooth: {{ type: "cubicBezier", forceDirection: "horizontal", roundness: 0.35 }}
      }};

      rawNodes.push(newNode);
      rawEdges.push(newEdge);
      nodesDataset.add(newNode);
      edgesDataset.add(newEdge);

      populateDropdowns();
      updateJsonView();
      selectNode(newId);
    }}

    function executeColimitSynthesis() {{
      const baseVersion = parseInt(document.getElementById("colimit-source-version-select").value);
      const newRawId = document.getElementById("colimit-new-id").value;
      const newTitle = document.getElementById("colimit-new-title").value;
      const newId = `${{newRawId}}@t40`;
      if (!newRawId) return alert("ノードIDを指定してください");

      const newNode = {{
        id: newId,
        rawId: newRawId,
        type: "NewPaper",
        version: 40,
        label: `${{newRawId}}\\n[t=40]`,
        title: `合成論文: ${{newTitle}}`,
        color: {{ background: typeColors.NewPaper, border: "#ffffff" }},
        font: {{ color: "#ffffff", size: 10 }},
        shape: "box",
        margin: 8,
        x: 1360,
        y: 110,
        fixed: {{ x: true, y: false }}
      }};

      rawNodes.push(newNode);
      nodesDataset.add(newNode);

      const srcNodes = rawNodes.filter(n => n.version === baseVersion);
      srcNodes.forEach((src, idx) => {{
        const edge = {{
          id: `e_col_${{Date.now()}}_${{idx}}`,
          from: src.id,
          to: newId,
          label: "ColimitProjection",
          arrows: "to",
          color: {{ color: "#fb923c" }},
          width: 2.5,
          smooth: {{ type: "cubicBezier", forceDirection: "horizontal", roundness: 0.35 }}
        }};
        rawEdges.push(edge);
        edgesDataset.add(edge);
      }});

      populateDropdowns();
      updateJsonView();
      selectNode(newId);
    }}

    function populateDropdowns() {{
      const targetSelect = document.getElementById("node-selector");
      const currentSelected = targetSelect.value;
      targetSelect.innerHTML = '<option value="">-- 全ノード一覧 --</option>';
      rawNodes.forEach(n => {{
        targetSelect.innerHTML += `<option value="${{n.id}}">${{n.id}} (${{n.type}} / t=${{n.version}})</option>`;
      }});
      if (currentSelected) targetSelect.value = currentSelected;

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
          "cat": "http://example.org/category#"
        }},
        "@graph": rawNodes.map(n => ({{
          "@id": n.rawId,
          "@type": n.type,
          "schema:name": n.title,
          "cat:version": n.version,
          "prov:wasDerivedFrom": rawEdges.filter(e => e.to === n.id).map(e => e.from)
        }}))
      }};
      document.getElementById("json-box").value = JSON.stringify(jsonLd, null, 2);
    }}

    function downloadJsonLd() {{
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(document.getElementById("json-box").value);
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", "categorical_provenance_full_snapshot.jsonld");
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    }}

    function switchTab(tabId) {{
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(b => b.getAttribute('onclick').includes(tabId));
      if (activeBtn) activeBtn.classList.add('active');
      document.getElementById(tabId).classList.add('active');
    }}

    let isPlaying = false;
    let playTimer = null;

    function togglePlay() {{
      isPlaying = !isPlaying;
      document.getElementById("play-btn").innerText = isPlaying ? "⏸" : "▶";
      if (isPlaying) {{
        playTimer = setInterval(() => {{
          let scrub = document.getElementById("time-scrubber");
          let val = parseFloat(scrub.value) + 1.0;
          if (val > 40) val = 0;
          scrub.value = val;
          onScrub(val);
        }}, 600);
      }} else {{
        clearInterval(playTimer);
      }}
    }}

    function onScrub(v) {{
      const tVal = parseFloat(v);
      document.getElementById("time-display").innerText = `t = ${{tVal.toFixed(1)}}`;
      
      nodesDataset.forEach(n => {{
        const orig = rawNodes.find(o => o.id === n.id);
        nodesDataset.update({{ id: n.id, hidden: orig.version > tVal }});
      }});

      const ticker = document.getElementById("synopsis-ticker");
      if (tVal < 10) ticker.innerText = `t=${{tVal}}: 1965年 初期実験開始。白金電極の腐食失敗アノマリーと大腸菌伸長データ群。`;
      else if (tVal < 20) ticker.innerText = `t=${{tVal}}: 1967年 観点転換関手(Shift)。電極腐食をIC50細胞分裂阻害能へ再解釈しシスプラチン標本合成。`;
      else if (tVal < 30) ticker.innerText = `t=${{tVal}}: 1969年 余極限合成。動物抗腫瘍試験と腎毒性限界の統合によるNature 1969論文創出。`;
      else if (tVal < 40) ticker.innerText = `t=${{tVal}}: 1999年 高次随伴関手。X線結晶構造解析によるDNA付加体の立体配座解明論文。`;
      else ticker.innerText = `t=40.0: 最新論文 (Adv Ther 2026) への全系譜が接続完了。40年間の全ルーツを遡及可能。`;
    }}

    function restartSimulation() {{
      document.getElementById("time-scrubber").value = 0;
      onScrub(0);
      if (!isPlaying) togglePlay();
    }}

    window.onload = function() {{
      populateDropdowns();
      updateJsonView();
      setTimeout(resetView, 300);
    }};
  </script>
</body>
</html>"""


class CustomHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/" or self.path.endswith(".html"):
            content = build_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        else:
            super().do_GET()


def main():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print("=" * 66)
        print(
            "[*] Categorical Provenance & Dynamic Metadata Master Explorer 起動"
        )
        print(f"[*] URL: http://localhost:{PORT}")
        print("[*] 終了するにはターミナルで Ctrl+C を押してください")
        print("=" * 66)

        # サーバー起動後に自動でブラウザを開く
        threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] サーバーを停止しました。")
            httpd.server_close()


if __name__ == "__main__":
    main()