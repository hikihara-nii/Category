"""
end_to_end_pipeline.py
======================
【統合実行パイプライン】
1. 研究者 (ORCID付)・DOI付きデータセット・失敗ログ・論文の BibTeX 入力
2. 前処理フィルター (BibTeX -> W3C PROV-O / SIO 準拠 JSON-LD スナップショット生成)
3. 圏論的動的メタデータ構築エンジン (Grothendieck 全圏 ∫D 構築、Kan拡大、観点転換関手、余極限合成)
4. 双方向プロバナンス追跡の検証 (最新成果から初期失敗・生データへの完全逆引き)
5. 研究者責任 (ORCID) の帰属検証
"""

import json
import os
import re
import networkx as nx

# =============================================================================
# Step 1: 研究者が準備する BibTeX 入力データ (DOI & ORCID 対応)
# =============================================================================
BIBTEX_INPUT = """
% --- [世代 t=0] 1965年 初期実験 ---
@dataset{Data_CellFilamentation_DOI,
  doi = {10.5281/zenodo.1234567},
  title = {E. coli Filamentation Assay Raw Microscopy Images and Cell Length Dataset},
  author = {Rosenberg, Barnett and Van Camp, Loretta},
  orcid = {0000-0002-1825-0097; 0000-0001-5109-3700},
  publisher = {Zenodo},
  year = {1965},
  sio_value = {300x length without division}
}

@dataset{Exp_Fail_ElectrodeCorrosion_DOI,
  doi = {10.5281/zenodo.7654321},
  title = {Platinum Electrode Corrosion & Soluble Byproduct Anomaly Log},
  author = {Rosenberg, Barnett},
  orcid = {0000-0002-1825-0097},
  publisher = {Zenodo (Negative Results Archive)},
  year = {1965},
  type = {FailedData},
  fail_reason = {Inert Pt electrode corroded in NH4Cl broth; formed soluble inorganic byproduct}
}

@article{Nature_1965_Rosenberg,
  doi = {10.1038/205698a0},
  title = {Inhibition of Cell Division in Escherichia coli by Electrolysis},
  author = {Rosenberg, Barnett and Van Camp, Loretta and Krigas, Thomas},
  orcid = {0000-0002-1825-0097; 0000-0001-5109-3700; 0000-0003-1234-5678},
  journal = {Nature},
  year = {1965},
  uses_data = {Data_CellFilamentation_DOI; Exp_Fail_ElectrodeCorrosion_DOI}
}

% --- [世代 t=10] 1967年 観点転換・再解釈データ ---
@dataset{Data_PtCytotoxicity_Threshold_DOI,
  doi = {10.5281/zenodo.8888888},
  title = {Pt Complex Anti-Mitotic Activity Curve & IC50 Threshold Dataset},
  author = {Rosenberg, Barnett},
  orcid = {0000-0002-1825-0097},
  publisher = {Zenodo},
  year = {1967},
  type = {ThermalLimit},
  derived_from = {Exp_Fail_ElectrodeCorrosion_DOI},
  reinterpretation_note = {Re-evaluated corrosion byproduct as potent chemical inhibitor of chromosomal division},
  sio_value = {IC50 = 2.5 ug/mL}
}

@misc{Material_Synthesized_Cisplatin,
  title = {cis-diamminedichloroplatinum(II) [Pure Synthetic Specimen]},
  author = {Rosenberg, Barnett},
  orcid = {0000-0002-1825-0097},
  year = {1967},
  type = {NewMaterial}
}

% --- [世代 t=20] 1969年 余極限合成新論文 ---
@dataset{Data_Sarcoma180_TumorRegression_DOI,
  doi = {10.5281/zenodo.9999999},
  title = {In Vivo Sarcoma 180 Complete Tumor Regression Curve},
  author = {Rosenberg, Barnett and Van Camp, Loretta},
  orcid = {0000-0002-1825-0097; 0000-0001-5109-3700},
  publisher = {Zenodo},
  year = {1969},
  sio_value = {100% cure rate at 8 mg/kg}
}

@article{Nature_1969_Rosenberg,
  doi = {10.1038/222385a0},
  title = {Platinum Compounds: a New Class of Potent Antitumour Agents},
  author = {Rosenberg, Barnett and Van Camp, Loretta and Trosko, James E. and Mansour, Virginia H.},
  orcid = {0000-0002-1825-0097; 0000-0001-5109-3700; 0000-0002-9999-1111; 0000-0002-8888-2222},
  journal = {Nature},
  year = {1969},
  uses_data = {Data_PtCytotoxicity_Threshold_DOI; Material_Synthesized_Cisplatin; Data_Sarcoma180_TumorRegression_DOI},
  derived_from = {Nature_1965_Rosenberg}
}
"""

# =============================================================================
# Step 2: 前処理フィルター (BibTeX -> JSON-LD Pipeline Format)
# =============================================================================
class DataCentricBibtexProcessor:
    def __init__(self):
        self.entry_pattern = re.compile(r"@(\w+)\s*\{\s*([^,]+),\s*(.*?)\s*\n\}", re.DOTALL)

    def parse_bibtex(self, bib_text: str) -> list:
        cleaned = re.sub(r"%.*$", "", bib_text, flags=re.MULTILINE)
        entries = []
        for match in self.entry_pattern.finditer(cleaned):
            entry_type = match.group(1).lower()
            cite_key = match.group(2).strip()
            body = match.group(3)

            fields = {"entry_type": entry_type, "cite_key": cite_key}
            raw_fields = re.findall(r'(\w+)\s*=\s*([\{"][^"\}]*[\}"]|\d+|[^\s,]+)', body)
            for k, v in raw_fields:
                key = k.strip().lower()
                val = re.sub(r"[\{\}]", "", v.strip().strip('{}"\''))
                fields[key] = val
            entries.append(fields)
        return entries

    def convert_to_pipeline_snapshots(self, entries: list) -> list:
        snapshots_dict = {0: [], 10: [], 20: []}
        agents_registered = set()

        for entry in entries:
            key = entry.get("cite_key")
            entry_type = entry.get("entry_type", "misc")
            custom_type = entry.get("type", "")
            title = entry.get("title", key)
            year = entry.get("year", "1965")
            doi = entry.get("doi", "")
            publisher = entry.get("publisher", "")

            # 世代 version_t の決定
            v = 0
            if year == "1967":
                v = 10
            elif int(year) >= 1969:
                v = 20

            # データ・論文同列判定
            if custom_type == "FailedData" or "fail" in key.lower():
                node_type = "FailedData"
            elif custom_type == "ThermalLimit" or "limit" in key.lower() or "threshold" in key.lower():
                node_type = "ThermalLimit"
            elif custom_type == "NewMaterial" or "material" in key.lower():
                node_type = "NewMaterial" if v > 0 else "Material"
            elif entry_type in ["dataset", "data", "misc"] or "data" in key.lower():
                node_type = "Data"
            elif entry_type in ["article", "book", "inproceedings"]:
                node_type = "Paper" if v == 0 else "NewPaper"
            else:
                node_type = "Entity"

            node = {
                "@id": key,
                "cat:type": node_type,
                "schema:name": f"{title} ({year})" if year else title,
                "schema:datePublished": year
            }
            if doi:
                node["schema:identifier"] = f"https://doi.org/{doi}"
                node["datacite:doi"] = doi
            if publisher:
                node["schema:publisher"] = publisher
            if "sio_value" in entry:
                node["sio:has-value"] = entry["sio_value"]
            if "fail_reason" in entry:
                node["cat:failureReason"] = entry["fail_reason"]
            if "reinterpretation_note" in entry:
                node["cat:reinterpretationNote"] = entry["reinterpretation_note"]

            # ORCID と 研究者 (prov:Agent) 登録
            authors = [a.strip() for a in entry.get("author", "").split(" and ") if a]
            orcids = [o.strip() for o in entry.get("orcid", "").split(";") if o]

            attributed_agents = []
            for idx, a_name in enumerate(authors):
                orcid_id = orcids[idx] if idx < len(orcids) else None
                if orcid_id:
                    ag_id = f"orcid:{orcid_id}"
                    ag_name = f"{a_name} (ORCID: {orcid_id})"
                else:
                    clean_name = re.sub(r"[^a-zA-Z0-9_]", "", a_name.replace(" ", "_"))
                    ag_id = f"agent:{clean_name}"
                    ag_name = a_name

                attributed_agents.append({"@id": ag_id})

                if ag_id not in agents_registered:
                    agents_registered.add(ag_id)
                    snapshots_dict[v].append({
                        "@id": ag_id,
                        "cat:type": "Researcher",
                        "schema:name": ag_name,
                        "@type": "prov:Agent",
                        "orcid:id": orcid_id if orcid_id else ""
                    })

            if attributed_agents:
                node["prov:wasAttributedTo"] = attributed_agents

            # データ間の射 (uses_data, derived_from)
            if "uses_data" in entry:
                node["schema:hasPart"] = [{"@id": d.strip()} for d in entry["uses_data"].split(";") if d]
            if "derived_from" in entry:
                node["prov:wasDerivedFrom"] = [{"@id": d.strip()} for d in entry["derived_from"].split(";") if d]

            snapshots_dict[v].append(node)

        return [
            {"version": 0, "description": "t=0 [1965] 初期実験: 伸長測定データ、電極腐食失敗ログ、論文", "@graph": snapshots_dict[0]},
            {
                "version": 10,
                "description": "t=10 [1967] 観点転換: 腐食失敗から阻害活性IC50への再解釈データ、合成新材料",
                "@graph": snapshots_dict[10],
                "perspective_shifts": [
                    {
                        "source_id": "Exp_Fail_ElectrodeCorrosion_DOI",
                        "new_id": "Data_PtCytotoxicity_Threshold_DOI",
                        "new_type": "ThermalLimit",
                        "name": "Pt Complex Anti-Mitotic Activity (IC50 = 2.5 ug/mL)"
                    }
                ]
            },
            {
                "version": 20,
                "description": "t=20 [1969] 余極限合成: 動物試験データと再解釈データ統合による新論文創出",
                "@graph": snapshots_dict[20],
                "higher_functors": [
                    {"from": "Nature_1965_Rosenberg@t0", "to": "Nature_1969_Rosenberg@t20", "transform": "EvolvesFrom", "functor": "Lineage"},
                    {"from": "Data_PtCytotoxicity_Threshold_DOI@t10", "to": "Nature_1969_Rosenberg@t20", "transform": "Synthesize", "functor": "ColimitProjection"},
                    {"from": "Material_Synthesized_Cisplatin@t10", "to": "Nature_1969_Rosenberg@t20", "transform": "IntegrateNew", "functor": "Pushout"}
                ]
            }
        ]

# =============================================================================
# Step 3: 圏論的動的メタデータ構築エンジン (Grothendieck 全圏 ∫D 構築)
# =============================================================================
class CategoricalProvenanceEngine:
    def __init__(self):
        self.G_total = nx.DiGraph()

    def process_pipeline(self, snapshots: list):
        for idx, snap in enumerate(snapshots):
            v = snap["version"]

            # 観点転換関手 (Perspective Shift)
            shifts = snap.get("perspective_shifts", [])
            if shifts and idx > 0:
                prev_v = snapshots[idx - 1]["version"]
                for s in shifts:
                    src_node = f"{s['source_id']}@t{prev_v}"
                    tgt_node = f"{s['new_id']}@t{v}"
                    if self.G_total.has_node(src_node):
                        self.G_total.add_node(
                            tgt_node,
                            rawId=s["new_id"],
                            type=s["new_type"],
                            version=v,
                            label=f"{s['name']}\n[t={v}]",
                            title=f"Reinterpreted: {s['name']}"
                        )
                        self.G_total.add_edge(src_node, tgt_node, edge_type="inter", transform="PerspectiveShift", functor="Reinterpretation")

            # ノードと同一時間層エッジの投入
            for node in snap.get("@graph", []):
                raw_id = node["@id"]
                node_id = f"{raw_id}@t{v}" if not raw_id.startswith("orcid:") and not raw_id.startswith("agent:") else raw_id
                node_type = node.get("cat:type", "Entity")
                name = node.get("schema:name", raw_id)

                self.G_total.add_node(
                    node_id,
                    rawId=raw_id,
                    type=node_type,
                    version=v if not raw_id.startswith("orcid:") else 0,
                    label=f"{name}\n[t={v}]" if not raw_id.startswith("orcid:") else name,
                    title=f"ID: {raw_id} | Type: {node_type}"
                )

                # 責任帰属エッジ (prov:wasAttributedTo)
                for ag in node.get("prov:wasAttributedTo", []):
                    self.G_total.add_edge(node_id, ag["@id"], edge_type="intra", relation="prov:wasAttributedTo")

                # データ利用エッジ (schema:hasPart)
                for part in node.get("schema:hasPart", []):
                    p_id = f"{part['@id']}@t{v}"
                    self.G_total.add_edge(node_id, p_id, edge_type="intra", relation="schema:hasPart")

                # データ派生エッジ (prov:wasDerivedFrom)
                for der in node.get("prov:wasDerivedFrom", []):
                    cand = [n for n in self.G_total.nodes() if self.G_total.nodes[n].get("rawId") == der["@id"]]
                    if cand:
                        self.G_total.add_edge(node_id, cand[-1], edge_type="inter", transform="wasDerivedFrom", functor="Lineage")

            # 高次関手射 (Higher Functors)
            for hf in snap.get("higher_functors", []):
                if self.G_total.has_node(hf["from"]) and self.G_total.has_node(hf["to"]):
                    self.G_total.add_edge(
                        hf["from"],
                        hf["to"],
                        edge_type="inter",
                        transform=hf.get("transform", "FunctorMapping"),
                        functor=hf.get("functor", "CategoricalMapping")
                    )

    def trace_ancestors(self, target_id: str):
        if not self.G_total.has_node(target_id):
            return []
        anc = nx.ancestors(self.G_total, target_id)
        return sorted(anc, key=lambda x: self.G_total.nodes[x].get("version", 0))

# =============================================================================
# Step 4: メイン実行と検証
# =============================================================================
def main():
    print("=" * 75)
    print("[Phase 1] BibTeX テキストの入力と前処理フィルターの実行")
    print("=" * 75)
    processor = DataCentricBibtexProcessor()
    parsed_entries = processor.parse_bibtex(BIBTEX_INPUT)
    print(f"[*] 抽出エントリ数: {len(parsed_entries)} 件 (論文、DOI付データ、失敗データ、再解釈データ)")

    snapshots = processor.convert_to_pipeline_snapshots(parsed_entries)
    full_pipeline_json = {
        "metadata": {
            "title": "Data-Centric Provenance & Categorical Lineage Pipeline",
            "description": "BibTeXから自動生成された動的メタデータパイプライン"
        },
        "snapshots": snapshots
    }

    output_json = "pipeline_generated_from_bibtex.json"
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(full_pipeline_json, f, ensure_ascii=False, indent=2)
    print(f"[✓] 前処理フィルター完了: {output_json} を生成しました。")

    print("\n" + "=" * 75)
    print("[Phase 2] 圏論的動的メタデータ構築エンジン (Grothendieck 全圏 ∫D) の処理")
    print("=" * 75)
    engine = CategoricalProvenanceEngine()
    engine.process_pipeline(snapshots)
    print(f"[*] 全圏ノード総数: {len(engine.G_total.nodes())} (論文、データ、失敗ログ、ORCID研究者)")
    print(f"[*] 全圏射(エッジ)総数: {len(engine.G_total.edges())} (同一時間内参照 + 時間関手射)")

    print("\n" + "=" * 75)
    print("[Phase 3] 双方向プロバナンス追跡の検証 (最終成果から初期データ・失敗ログへの逆引き)")
    print("=" * 75)
    final_target = "Nature_1969_Rosenberg@t20"
    print(f"[*] 探索ターゲット: 最終論文 '{final_target}'")
    ancestors = engine.trace_ancestors(final_target)
    
    print(f"[✓] 過去ルーツ ({len(ancestors)} 件) を完全遡及検出しました:")
    for a in ancestors:
        attr = engine.G_total.nodes[a]
        v = attr.get("version", 0)
        t_name = attr.get("type", "Entity")
        lbl = attr.get("label", a).split("\n")[0]
        print(f"    <- [t={v:02d}] {a:<36} | Type: {t_name:<12} | {lbl}")

    print("\n" + "=" * 75)
    print("[Phase 4] 研究者責任 (ORCID) の帰属検証")
    print("=" * 75)
    fail_node = "Exp_Fail_ElectrodeCorrosion_DOI@t0"
    agents = [v for u, v, d in engine.G_total.edges(data=True) if u == fail_node and d.get("relation") == "prov:wasAttributedTo"]
    print(f"[*] 失敗データ '{fail_node}' の責任研究者 (prov:wasAttributedTo):")
    for ag in agents:
        ag_attr = engine.G_total.nodes[ag]
        print(f"    -> 責任者: {ag_attr.get('label')} (識別子: {ag})")

if __name__ == "__main__":
    main()