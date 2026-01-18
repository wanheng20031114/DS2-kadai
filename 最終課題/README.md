# TGS 2026 ホテル価格分析

## 概要
東京ゲームショウ (TGS) 2026 期間中の幕張メッセ周辺ホテル価格を分析し、イベント期間中の価格変動を検証するプロジェクト。

## 仮説
TGS 期間（2026/9/19-21）のホテル価格は通常期間と比較して大幅に上昇し、会場（海浜幕張駅）に近いホテルほど上昇率が高い。

## データソース
- 楽天トラベル (travel.rakuten.co.jp)

## セットアップ

```bash
# 仮想環境の作成（推奨）
python -m venv venv
venv\Scripts\activate  # Windows

# 依存パッケージのインストール
pip install -r requirements.txt
```

## 使用方法

### 1. データ収集
```bash
python src/scraper.py
```

### 2. データ分析
```bash
jupyter notebook notebooks/analysis.ipynb
```

## プロジェクト構造
```
最終課題/
├── README.md           # プロジェクト説明
├── requirements.txt    # 依存パッケージ
├── src/
│   ├── config.py       # 設定ファイル
│   ├── database.py     # DB操作クラス
│   └── scraper.py      # スクレイピング
├── data/
│   └── hotels.db       # SQLiteデータベース
└── notebooks/
    └── analysis.ipynb  # 分析ノートブック
```

## 注意事項
- スクレイピング時は `time.sleep()` を使用してサーバ負荷に配慮
- 楽天トラベルの利用規約を遵守

## ライセンス
学術目的でのみ使用
