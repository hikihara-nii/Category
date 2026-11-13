【Phase 1: 研究現場のBibTeX入力】
   ├─ DOI付き測定データセット (@dataset, Zenodo DOI)
   ├─ DOI付き失敗/アノマリーデータ (@dataset, type=FailedData, fail_reason)
   ├─ 観点転換された派生データ (@dataset, derived_from, IC50)
   ├─ 成果論文 (@article, uses_data)
   └─ 各エントリに責任研究者の ORCID を明記
         │
         ▼ (前処理フィルター: DataCentricBibtexProcessor)
【Phase 2: W3C PROV-O / SIO 準拠 JSON-LD スナップショット生成】
   ├─ データを論文と同等の「一級市民ノード」として展開
   ├─ ORCID を持つ研究者を独立した prov:Agent ノードとして生成
   └─ prov:wasAttributedTo（責任帰属射）を自動結線
         │
         ▼ (圏論エンジン: CategoricalProvenanceEngine)
【Phase 3: Grothendieck 全圏 (∫D) の構築 & 関手的データ移行】
   ├─ 左 Kan 拡大 (Σ_F): データの時間層 (t=0 -> t=10) への非破壊移行
   ├─ 観点転換関手 (Shift): 失敗ログ -> 活性限界値への再定義
   └─ 余極限合成 (Pushout): 新標本＋再解釈データから Nature 1969 論文を創出
         │
         ▼ (プロバナンス逆引き・責任検証)
【Phase 4: 完全遡及探索】
   └─ 1969年論文から、1965年の電極腐食失敗データおよび責任研究者(ORCID)まで100%逆引き完了