"""
data_centric_bibtex_processor.py
================================
論文だけでなく「データセット(DOI付)」や「失敗データ」も一級市民として同列処理し、
ORCID(責任研究者)や来歴エッジ(PROV-O/SIO)を自動構成する完全前処理フィルター
"""

import json
import os
import re


class DataCentricBibtexProcessor:

    def __init__(self):
        self.entry_pattern = re.compile(
            r"@(\w+)\s*\{\s*([^,]+),\s*(.*?)\s*\n\}", re.DOTALL
        )

    def parse_bibtex(self, bib_text: str) -> list:
        cleaned_text = re.sub(r"%.*$", "", bib_text, flags=re.MULTILINE)
        entries = []
        for match in self.entry_pattern.finditer(cleaned_text):
            entry_type = match.group(1).lower()
            cite_key = match.group(2).strip()
            body = match.group(3)

            fields = {"entry_type": entry_type, "cite_key": cite_key}
            raw_fields = re.findall(
                r'(\w+)\s*=\s*([\{"][^"\}]*[\}"]|\d+|[^\s,]+)', body
            )
            for k, v in raw_fields:
                key = k.strip().lower()
                val = v.strip().strip('{}"\'')
                val = re.sub(r"[\{\}]", "", val)
                fields[key] = val
            entries.append(fields)
        return entries

    def convert_to_pipeline_nodes(
        self, entries: list, version_t: int = 0
    ) -> list:
        nodes = []
        agents_registered = set()

        for entry in entries:
            key = entry.get("cite_key")
            entry_type = entry.get("entry_type", "misc")
            custom_type = entry.get("type", "")
            title = entry.get("title", key)
            year = entry.get("year", "")
            doi = entry.get("doi", "")
            publisher = entry.get("publisher", "")

            # -------------------------------------------------------------
            # 1. ノード種別の厳密な自動判定 (データと論文の同列扱い)
            # -------------------------------------------------------------
            if custom_type == "FailedData" or "fail" in key.lower():
                node_type = "FailedData"
            elif custom_type == "ThermalLimit" or "limit" in key.lower():
                node_type = "ThermalLimit"
            elif entry_type in ["dataset", "data", "misc"] or "data" in key.lower():
                node_type = "Data"
            elif entry_type in ["article", "book", "inproceedings"]:
                node_type = "Paper" if version_t == 0 else "NewPaper"
            else:
                node_type = "Entity"

            node = {
                "@id": key,
                "cat:type": node_type,
                "schema:name": f"{title} ({year})" if year else title,
                "schema:datePublished": year,
            }

            # DOI とリポジトリ情報の付与
            if doi:
                node["schema:identifier"] = f"https://doi.org/{doi}"
                node["datacite:doi"] = doi
            if publisher:
                node["schema:publisher"] = publisher

            # 測定値・失敗理由・観点転換ノートの付与 (SIO / Category)
            if "sio_value" in entry:
                node["sio:has-value"] = entry["sio_value"]
            if "fail_reason" in entry:
                node["cat:failureReason"] = entry["fail_reason"]
            if "reinterpretation_note" in entry:
                node["cat:reinterpretationNote"] = entry["reinterpretation_note"]

            # -------------------------------------------------------------
            # 2. 研究者 (ORCID) の抽出と責任帰属 (prov:wasAttributedTo)
            # -------------------------------------------------------------
            authors = [
                a.strip() for a in entry.get("author", "").split(" and ") if a
            ]
            orcids = [
                o.strip() for o in entry.get("orcid", "").split(";") if o
            ]

            attributed_agents = []
            for idx, author_name in enumerate(authors):
                orcid_id = orcids[idx] if idx < len(orcids) else None

                if orcid_id:
                    agent_id = f"orcid:{orcid_id}"
                    agent_label = f"{author_name} (ORCID: {orcid_id})"
                else:
                    clean_name = re.sub(
                        r"[^a-zA-Z0-9_]", "", author_name.replace(" ", "_")
                    )
                    agent_id = f"agent:{clean_name}"
                    agent_label = author_name

                attributed_agents.append({"@id": agent_id})

                # 研究者ノード (prov:Agent) を未登録なら作成
                if agent_id not in agents_registered:
                    agents_registered.add(agent_id)
                    agent_node = {
                        "@id": agent_id,
                        "cat:type": "Researcher",
                        "schema:name": agent_label,
                        "@type": "prov:Agent",
                    }
                    if orcid_id:
                        agent_node["schema:identifier"] = (
                            f"https://orcid.org/{orcid_id}"
                        )
                        agent_node["orcid:id"] = orcid_id
                    nodes.append(agent_node)

            if attributed_agents:
                node["prov:wasAttributedTo"] = attributed_agents

            # -------------------------------------------------------------
            # 3. データ間の有向射 (依存・派生関係)
            # -------------------------------------------------------------
            # 論文が利用しているデータ (uses_data -> schema:hasPart)
            if "uses_data" in entry:
                node["schema:hasPart"] = [
                    {"@id": d.strip()}
                    for d in entry["uses_data"].split(";")
                    if d
                ]

            # データ同士の派生・観点転換 (derived_from -> prov:wasDerivedFrom)
            if "derived_from" in entry:
                node["prov:wasDerivedFrom"] = [
                    {"@id": d.strip()}
                    for d in entry["derived_from"].split(";")
                    if d
                ]

            nodes.append(node)

        return nodes


# =========================================================================
# 実行テスト・JSON出力
# =========================================================================
if __name__ == "__main__":
    raw_bibtex_input = """
    % 1. DOI/ORCID付き正常データセット
    @dataset{Data_CellFilamentation_DOI,
      doi = {10.5281/zenodo.1234567},
      title = {E. coli Filamentation Assay Raw Microscopy Images and Cell Length Dataset},
      author = {Rosenberg, Barnett and Van Camp, Loretta},
      orcid = {0000-0002-1825-0097; 0000-0001-5109-3700},
      publisher = {Zenodo},
      year = {1965},
      sio_value = {300x length without division}
    }

    % 2. DOI/ORCID付き失敗データセット
    @dataset{Exp_Fail_ElectrodeCorrosion_DOI,
      doi = {10.5281/zenodo.7654321},
      title = {Platinum Electrode Corrosion Negative Result Log},
      author = {Rosenberg, Barnett},
      orcid = {0000-0002-1825-0097},
      publisher = {Zenodo (Negative Results Archive)},
      year = {1965},
      type = {FailedData},
      fail_reason = {Inert Pt electrode corroded in NH4Cl broth; formed soluble inorganic byproduct}
    }

    % 3. 論文 (上記データセットを利用)
    @article{Nature_1965_Rosenberg,
      doi = {10.1038/205698a0},
      title = {Inhibition of Cell Division in Escherichia coli by Electrolysis},
      author = {Rosenberg, Barnett and Van Camp, Loretta and Krigas, Thomas},
      orcid = {0000-0002-1825-0097; 0000-0001-5109-3700; 0000-0003-1234-5678},
      journal = {Nature},
      year = {1965},
      uses_data = {Data_CellFilamentation_DOI; Exp_Fail_ElectrodeCorrosion_DOI}
    }

    % 4. 失敗データを観点転換して得られた新データセット (データからデータへの派生)
    @dataset{Data_PtCytotoxicity_Threshold_DOI,
      doi = {10.5281/zenodo.8888888},
      title = {Pt Complex Anti-Mitotic Activity Curve & IC50 Threshold Dataset},
      author = {Rosenberg, Barnett},
      orcid = {0000-0002-1825-0097},
      publisher = {Zenodo},
      year = {1967},
      type = {ThermalLimit},
      derived_from = {Exp_Fail_ElectrodeCorrosion_DOI},
      reinterpretation_note = {Re-evaluated corrosion byproduct as potent chemical inhibitor of cell division},
      sio_value = {IC50 = 2.5 ug/mL}
    }
    """

    processor = DataCentricBibtexProcessor()
    parsed_entries = processor.parse_bibtex(raw_bibtex_input)
    generated_nodes = processor.convert_to_pipeline_nodes(
        parsed_entries, version_t=0
    )

    output_pipeline = {
        "metadata": {
            "title": "Data-Centric Provenance Pipeline",
            "description": "データセット・失敗ログをDOIおよびORCIDとともに一級市民として処理したメタデータ",
        },
        "snapshots": [
            {
                "version": 0,
                "description": "DOI・ORCID付きデータセットおよび論文の統合スナップショット",
                "@graph": generated_nodes,
            }
        ],
    }

    out_file = "data_centric_pipeline.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_pipeline, f, ensure_ascii=False, indent=2)

    print(f"[*] 変換完了: {out_file} を出力しました。\n")
    print(json.dumps(output_pipeline, ensure_ascii=False, indent=2))