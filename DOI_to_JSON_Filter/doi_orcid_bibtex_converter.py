"""
doi_orcid_bibtex_converter.py
=============================
DOI付きデータセット・失敗ログ・論文の BibTeX から
研究者の ORCID を抽出・独立ノード化し、責任帰属 (prov:wasAttributedTo) を自動構築する前処理フィルター
"""

import json
import re


class DOIBibtexWithORCIDConverter:

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

    def convert_entries_to_nodes(
        self, entries: list, version_t: int = 0
    ) -> list:
        """
        BibTeX の各エントリをデータ/論文ノードに変換し、
        さらに ORCID を持つ研究者を独立した Agent ノードとして生成・結線する
        """
        nodes = []
        agents_registered = set()

        for entry in entries:
            key = entry.get("cite_key")
            entry_type = entry.get("entry_type", "misc")
            custom_type = entry.get("type", "").lower()
            title = entry.get("title", key)
            year = entry.get("year", "")
            doi = entry.get("doi", "")
            publisher = entry.get("publisher", "")

            # 1. ノード種別判定
            if "fail" in custom_type or "failed" in key.lower():
                node_type = "FailedData"
            elif (
                custom_type == "dataset"
                or entry_type in ["misc", "data", "dataset"]
                or "data" in key.lower()
            ):
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

            if doi:
                node["schema:identifier"] = f"https://doi.org/{doi}"
                node["datacite:doi"] = doi
            if publisher:
                node["schema:publisher"] = publisher
            if "sio_value" in entry:
                node["sio:has-value"] = entry["sio_value"]
            if "fail_reason" in entry:
                node["cat:failureReason"] = entry["fail_reason"]

            # 2. 研究者（ORCID）と責任帰属 (prov:wasAttributedTo) の構築
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
                    agent_id = f"agent:{re.sub(r'[^a-zA-Z0-9_]', '', author_name.replace(' ', '_'))}"
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
                # W3C PROV-O 規格: Entity -> Agent への責任帰属
                node["prov:wasAttributedTo"] = attributed_agents

            # 3. データセット参照 (schema:hasPart / prov:wasDerivedFrom)
            has_parts = []
            if "uses_data" in entry:
                for d_ref in [
                    d.strip() for d in entry["uses_data"].split(";") if d
                ]:
                    has_parts.append({"@id": d_ref})
            if has_parts:
                node["schema:hasPart"] = has_parts

            if "derived_from" in entry:
                node["prov:wasDerivedFrom"] = [
                    {"@id": d.strip()}
                    for d in entry["derived_from"].split(";")
                    if d
                ]

            nodes.append(node)

        return nodes


# =========================================================================
# 動作検証テスト
# =========================================================================
if __name__ == "__main__":
    sample_bibtex = """
    % 1. DOI & ORCID 付きの測定データセット
    @misc{Data_CellFilamentation_DOI,
      doi = {10.5281/zenodo.1234567},
      title = {E. coli Filamentation Assay Raw Dataset},
      author = {Rosenberg, Barnett and Van Camp, Loretta},
      orcid = {0000-0002-1825-0097; 0000-0001-5109-3700},
      publisher = {Zenodo},
      year = {1965},
      type = {Dataset},
      sio_value = {300x length without division}
    }

    % 2. 失敗データセット (実験責任者のORCID明記)
    @misc{Exp_Fail_ElectrodeCorrosion_DOI,
      doi = {10.5281/zenodo.7654321},
      title = {Platinum Electrode Corrosion Negative Result Log},
      author = {Rosenberg, Barnett},
      orcid = {0000-0002-1825-0097},
      publisher = {Zenodo (Negative Results Archive)},
      year = {1965},
      type = {FailedData},
      fail_reason = {Inert Pt electrode corroded in NH4Cl broth}
    }

    % 3. 論文 (データセットを参照)
    @article{Nature_1965_Rosenberg,
      doi = {10.1038/205698a0},
      title = {Inhibition of Cell Division in Escherichia coli by Electrolysis},
      author = {Rosenberg, Barnett and Van Camp, Loretta and Krigas, Thomas},
      orcid = {0000-0002-1825-0097; 0000-0001-5109-3700; 0000-0003-1234-5678},
      journal = {Nature},
      year = {1965},
      uses_data = {Data_CellFilamentation_DOI; Exp_Fail_ElectrodeCorrosion_DOI}
    }
    """

    converter = DOIBibtexWithORCIDConverter()
    entries = converter.parse_bibtex(sample_bibtex)
    nodes = converter.convert_entries_to_nodes(entries, version_t=0)

    output_data = {
        "metadata": {
            "title": "ORCID-Enabled Provenance Pipeline",
            "description": "研究者(ORCID)を独立したAgentとして組み込み、データの責任帰属を明確化したメタデータ",
        },
        "snapshots": [
            {
                "version": 0,
                "description": "t=0 [1965年] ORCID付き研究者・DOI付きデータ・初期論文の統合スナップショット",
                "@graph": nodes,
            }
        ],
    }

    output_file = "pipeline_with_orcid.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"[*] 変換完了: {output_file} を出力しました。\n")
    print(json.dumps(output_data, ensure_ascii=False, indent=2))