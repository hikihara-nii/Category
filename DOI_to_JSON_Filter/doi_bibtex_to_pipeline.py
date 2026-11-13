"""
doi_bibtex_to_pipeline.py
=========================
DOI 付きデータセット・失敗ログ・論文の BibTeX を一括パースし、
圏論的動的メタデータパイプライン用の JSON-LD を生成する前処理フィルター
"""

import json
import os
import re


class DOIBibtexPipelineConverter:

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

    def convert_entries_to_nodes(self, entries: list, version_t: int = 0) -> list:
        """BibTeX のエントリ群を、型 (Paper / Data / FailedData) を自動判定してノード化"""
        nodes = []
        for entry in entries:
            key = entry.get("cite_key")
            entry_type = entry.get("entry_type", "misc")
            custom_type = entry.get("type", "").lower()
            title = entry.get("title", key)
            year = entry.get("year", "")
            doi = entry.get("doi", "")
            publisher = entry.get("publisher", "")

            # ノード種別の自動判定
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

            # DOI とリポジトリ情報の付与 (PROV-O / Schema.org)
            if doi:
                node["schema:identifier"] = f"https://doi.org/{doi}"
                node["datacite:doi"] = doi
            if publisher:
                node["schema:publisher"] = publisher

            # 著者情報の付与
            if "author" in entry:
                authors = [a.strip() for a in entry["author"].split(" and ")]
                node["prov:wasAssociatedWith"] = authors

            # 特殊属性 (SIO 値、失敗理由)
            if "sio_value" in entry:
                node["sio:has-value"] = entry["sio_value"]
            if "fail_reason" in entry:
                node["cat:failureReason"] = entry["fail_reason"]

            # データセット参照関係 (uses_data, schema:hasPart)
            has_parts = []
            if "uses_data" in entry:
                data_refs = [d.strip() for d in entry["uses_data"].split(";")]
                for d_ref in data_refs:
                    has_parts.append({"@id": d_ref})

            if "derived_from" in entry:
                d_refs = [d.strip() for d in entry["derived_from"].split(";")]
                node["prov:wasDerivedFrom"] = [{"@id": d} for d in d_refs]

            if has_parts:
                node["schema:hasPart"] = has_parts

            nodes.append(node)
        return nodes


# =========================================================================
# 実行検証
# =========================================================================
if __name__ == "__main__":
    # 研究者が用意する、DOI付きデータセットと論文の混合 BibTeX
    mixed_bibtex = """
    % DOI付き測定データセット (DataCite形式)
    @misc{Data_CellFilamentation_DOI,
      doi = {10.5281/zenodo.1234567},
      author = {Rosenberg, Barnett and Van Camp, Loretta},
      title = {E. coli Filamentation Assay Raw Microscopy Images and Cell Length Dataset},
      publisher = {Zenodo},
      year = {1965},
      type = {Dataset},
      sio_value = {300x length without division}
    }

    % DOI付き失敗実験データセット (ネガティブデータリポジトリ)
    @misc{Exp_Fail_ElectrodeCorrosion_DOI,
      doi = {10.5281/zenodo.7654321},
      author = {Rosenberg, Barnett},
      title = {Failed Platinum Electrolysis Run Log and Byproduct Precipitate Analysis},
      publisher = {Zenodo (Negative Results Collection)},
      year = {1965},
      type = {FailedData},
      fail_reason = {Inert Pt electrode corroded in NH4Cl broth; formed soluble inorganic byproduct}
    }

    % 論文 (上記2つの DOI データセットを利用)
    @article{Nature_1965_Rosenberg,
      doi = {10.1038/205698a0},
      author = {Rosenberg, Barnett and Van Camp, Loretta and Krigas, Thomas},
      title = {Inhibition of Cell Division in Escherichia coli by Electrolysis},
      journal = {Nature},
      year = {1965},
      uses_data = {Data_CellFilamentation_DOI; Exp_Fail_ElectrodeCorrosion_DOI}
    }
    """

    converter = DOIBibtexPipelineConverter()
    entries = converter.parse_bibtex(mixed_bibtex)
    nodes = converter.convert_entries_to_nodes(entries, version_t=0)

    snapshot_json = {
        "snapshots": [
            {
                "version": 0,
                "description": "t=0 [1965年] DOI付きデータセットと初期論文の統合スナップショット",
                "@graph": nodes,
            }
        ]
    }

    output_path = "dataset_doi_pipeline.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(snapshot_json, f, ensure_ascii=False, indent=2)

    print(f"[*] 変換完了: {output_path} を出力しました。")
    print(json.dumps(snapshot_json, ensure_ascii=False, indent=2))