"""
bibtex_to_pipeline_json.py
==========================
BibTeX 形式のテキストをパースし、圏論的動的メタデータパイプライン用の
JSON-LD スナップショット形式へ変換・注入する前処理フィルター
(外部ライブラリ不要: Python標準ライブラリのみで動作)
"""

import json
import os
import re
import sys


class BibtexPreprocessor:

    def __init__(self):
        # 簡易 BibTeX パーサー用正規表現
        self.entry_pattern = re.compile(
            r"@(\w+)\s*\{\s*([^,]+),\s*(.*?)\s*\n\}", re.DOTALL
        )
        self.field_pattern = re.compile(
            r'(\w+)\s*=\s*[\{"\']?(.*?)[\}"\']?\s*(?:,|$)', re.DOTALL
        )

    def parse_bibtex(self, bib_text: str) -> list:
        """BibTeX 文字列を辞書のリストに変換"""
        entries = []
        # コメント行や余分な空白を除去
        cleaned_text = re.sub(r"%.*$", "", bib_text, flags=re.MULTILINE)

        for match in self.entry_pattern.finditer(cleaned_text):
            entry_type = match.group(1).lower()
            cite_key = match.group(2).strip()
            body = match.group(3)

            fields = {"entry_type": entry_type, "cite_key": cite_key}

            # 各フィールドを抽出
            # カンマ区切りに対応したフィールド分割
            raw_fields = re.findall(
                r'(\w+)\s*=\s*([\{"][^"\}]*[\}"]|\d+|[^\s,]+)', body
            )
            for k, v in raw_fields:
                key = k.strip().lower()
                val = v.strip().strip('{}"\'')
                # 波括弧による大文字保持などを除去
                val = re.sub(r"[\{\}]", "", val)
                fields[key] = val

            entries.append(fields)
        return entries

    def convert_to_jsonld_snapshot(
        self,
        bib_entries: list,
        version_t: int = 0,
        stage_description: str = "",
        perspective_shifts: list = None,
        higher_functors: list = None,
    ) -> dict:
        """
        BibTeX 解析結果を categorical_framework が要求する
        単一の「時間スナップショット (Snapshot)」形式へ変換
        """
        graph_nodes = []

        for entry in bib_entries:
            key = entry.get("cite_key", "Paper_Unknown")
            title = entry.get("title", key)
            year = entry.get("year", "")
            author = entry.get("author", "")

            # 論文ノード (Paper) のベース定義
            paper_node = {
                "@id": key,
                "cat:type": "Paper" if version_t == 0 else "NewPaper",
                "schema:name": f"{title} ({year})" if year else title,
                "schema:datePublished": year,
            }

            if author:
                authors = [a.strip() for a in author.split(" and ")]
                paper_node["prov:wasAssociatedWith"] = authors

            if "journal" in entry:
                paper_node["schema:isPartOf"] = entry["journal"]
            if "doi" in entry:
                paper_node["schema:identifier"] = f"https://doi.org/{entry['doi']}"

            # --- 拡張メタデータ属性 (BibTeX のオプショナルフィールドから抽出) ---
            has_parts = []

            # 1. 付随データ (data フィールド)
            if "data" in entry:
                data_ids = [d.strip() for d in entry["data"].split(";")]
                for d_id in data_ids:
                    has_parts.append({"@id": d_id})
                    # 付随するデータセットノードも自動生成
                    graph_nodes.append({
                        "@id": d_id,
                        "cat:type": "Data",
                        "schema:name": f"Measurement Dataset ({d_id})",
                        "sio:has-value": entry.get(
                            f"{d_id.lower()}_val", "raw experimental values"
                        ),
                    })

            # 2. 失敗データ (failed フィールド)
            if "failed" in entry:
                fail_ids = [f.strip() for f in entry["failed"].split(";")]
                for f_id in fail_ids:
                    has_parts.append({"@id": f_id})
                    reason = entry.get(
                        "fail_reason", "Unexpected anomaly or breakdown"
                    )
                    graph_nodes.append({
                        "@id": f_id,
                        "cat:type": "FailedData",
                        "schema:name": f"Failure/Anomaly Log ({f_id})",
                        "cat:failureReason": reason,
                    })

            # 3. 供試材料 (material フィールド)
            if "material" in entry:
                mat_ids = [m.strip() for m in entry["material"].split(";")]
                for m_id in mat_ids:
                    has_parts.append({"@id": m_id})
                    graph_nodes.append({
                        "@id": m_id,
                        "cat:type": "Material",
                        "schema:name": f"Specimen/Sample ({m_id})",
                    })

            # 4. 引用先行研究 (citation フィールド)
            if "citation" in entry:
                cites = [c.strip() for c in entry["citation"].split(";")]
                paper_node["schema:citation"] = [{"@id": c} for c in cites]
                for c in cites:
                    graph_nodes.append({
                        "@id": c,
                        "cat:type": "Reference",
                        "schema:name": f"Prior Cited Literature ({c})",
                    })

            # 5. 起源・派生元 (derived_from フィールド)
            if "derived_from" in entry:
                derived_ids = [
                    d.strip() for d in entry["derived_from"].split(";")
                ]
                paper_node["prov:wasDerivedFrom"] = [
                    {"@id": d} for d in derived_ids
                ]

            if has_parts:
                paper_node["schema:hasPart"] = has_parts

            graph_nodes.append(paper_node)

        snapshot = {
            "version": version_t,
            "description": (
                stage_description or f"Snapshot generated at t={version_t}"
            ),
            "@graph": graph_nodes,
        }

        if perspective_shifts:
            snapshot["perspective_shifts"] = perspective_shifts
        if higher_functors:
            snapshot["higher_functors"] = higher_functors

        return snapshot

    def build_full_pipeline_json(
        self,
        snapshots: list,
        title: str = "Pipeline from BibTeX",
        description: str = "",
    ) -> dict:
        """複数世代のスナップショットをまとめて完全なパイプライン JSON を構築"""
        return {
            "metadata": {"title": title, "description": description},
            "snapshots": snapshots,
        }


# =========================================================================
# 実行テスト・検証シナリオ
# =========================================================================
if __name__ == "__main__":
    # ユーザーが記入する BibTeX テキストの入力例
    # (通常の BibTeX に加え、data, failed, material, citation などの関係性をオプショナルに指定可能)
    sample_bibtex_t0 = """
    @article{Nature_1965_Rosenberg,
      title = {Inhibition of Cell Division in Escherichia coli by Electrolysis},
      author = {Rosenberg, Barnett and Van Camp, Loretta and Krigas, Thomas},
      journal = {Nature},
      year = {1965},
      doi = {10.1038/205698a0},
      data = {Data_CellFilamentation; Data_ElectricFieldGradient},
      failed = {Exp_Fail_ElectrodeCorrosion; Exp_Fail_LowPHPrecipitate},
      fail_reason = {Inert Pt electrode corroded in NH4Cl broth},
      material = {Material_EColi_B},
      citation = {Ref_Smith_1958; Ref_Phillips_1960}
    }
    """

    sample_bibtex_t20 = """
    @article{Nature_1969_Rosenberg,
      title = {Platinum Compounds: a New Class of Potent Antitumour Agents},
      author = {Rosenberg, Barnett and Van Camp, Loretta and Trosko, James E. and Mansour, Virginia H.},
      journal = {Nature},
      year = {1969},
      doi = {10.1038/222385a0},
      data = {Data_Sarcoma180_TumorRegression},
      derived_from = {Nature_1965_Rosenberg}
    }
    """

    preprocessor = BibtexPreprocessor()

    print("[*] BibTeX をパースしてスナップショットを生成中...")

    # t=0 のパースと変換
    entries_t0 = preprocessor.parse_bibtex(sample_bibtex_t0)
    snap_t0 = preprocessor.convert_to_jsonld_snapshot(
        entries_t0,
        version_t=0,
        stage_description="1965年 初期実験: 大腸菌電場印加実験と電極腐食失敗",
    )

    # t=10 の観点転換関手ルール（プログラム的または設定から付与）
    shifts_t10 = [{
        "source_id": "Exp_Fail_ElectrodeCorrosion",
        "new_id": "LimitEntry_PtCytotoxicity",
        "new_type": "ThermalLimit",
        "name": "Pt Complex Cell-Division Arrest Activity (IC50 Threshold)",
        "note": "Re-evaluated corrosion byproduct as potent chemical inhibitor",
    }]
    snap_t10 = {
        "version": 10,
        "description": "1967年 観点転換と新規シスプラチン合成",
        "perspective_shifts": shifts_t10,
        "@graph": [{
            "@id": "Material_Synthesized_Cisplatin",
            "cat:type": "NewMaterial",
            "schema:name": "cis-diamminedichloroplatinum(II) [Pure Specimen]",
        }],
    }

    # t=20 のパースと変換 (高次関手を含む)
    entries_t20 = preprocessor.parse_bibtex(sample_bibtex_t20)
    functors_t20 = [
        {
            "from": "LimitEntry_PtCytotoxicity@t10",
            "to": "Nature_1969_Rosenberg@t20",
            "transform": "Synthesize",
            "functor": "ColimitProjection",
        },
        {
            "from": "Nature_1965_Rosenberg@t0",
            "to": "Nature_1969_Rosenberg@t20",
            "transform": "EvolvesFrom",
            "functor": "Lineage",
        },
    ]
    snap_t20 = preprocessor.convert_to_jsonld_snapshot(
        entries_t20,
        version_t=20,
        stage_description="1969年 抗がん剤発見論文 (余極限合成)",
        higher_functors=functors_t20,
    )

    # 完全な入力 JSON ファイルとしてアセンブル
    pipeline_json = preprocessor.build_full_pipeline_json(
        snapshots=[snap_t0, snap_t10, snap_t20],
        title="BibTeX Generated Research Pipeline",
        description="BibTeX から自動生成された動的メタデータパイプライン定義",
    )

    # 出力
    output_filename = "pipeline_from_bibtex.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(pipeline_json, f, ensure_ascii=False, indent=2)

    print(f"[完了] JSON ファイルを出力しました: {output_filename}")