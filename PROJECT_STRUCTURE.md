# プロジェクト構造

JRA-VAN Odds APIのディレクトリ構造とモジュール説明。

## ディレクトリ構造

```
jravan_odds_fetcher/
├── src/                        # メインソースコード
│   ├── api_server.py          # FastAPI サーバー
│   ├── config.py              # 設定管理
│   ├── data_service.py        # データサービス層
│   ├── jravan_odds_fetcher.py # JVRTOpen（速報系）
│   ├── historical_fetcher.py  # JVOpen（蓄積系）
│   ├── historical_data_provider.py  # 過去データプロバイダー
│   ├── mock_provider.py       # モックデータ
│   ├── odds_cache.py          # キャッシュ管理
│   ├── odds_parser.py         # データパーサー
│   └── time_manager.py        # 時刻管理
│
├── tests/                      # テスト
│   ├── test_historical_integration.py
│   ├── test_dataspec.py
│   └── test_jvopen.py
│
├── scripts/                    # ツール
│   └── setup_historical_db.py # 蓄積系DBセットアップ
│
├── mock_data/                  # モックデータ
├── historical_cache/           # 蓄積系キャッシュ
├── data/                       # 保存データ
├── cache/                      # 一時キャッシュ
│
├── run.py                      # サーバー起動
├── requirements.txt            # 依存パッケージ
├── .env                        # 環境変数
└── README.md
```

## 主要モジュール

### api_server.py
FastAPIサーバー。REST APIとWebSocketを提供。

### data_service.py
データソースを統一的に扱うサービス層。
- 本番: JVRTOpenでリアルタイムデータ
- 開発（蓄積系）: JVOpenで過去データ
- 開発（モック）: 静的データ

### historical_data_provider.py
開発モード用プロバイダー。過去データとシミュレーション。

### jravan_odds_fetcher.py / historical_fetcher.py
JV-Linkラッパー（速報系/蓄積系）。

### odds_cache.py
JSON形式でキャッシュ管理。

### config.py
環境変数から設定読み込み。

## 実行方法

### サーバー起動

```bash
# 開発モード
export ENVIRONMENT=development
python run.py

# または
python -m src.api_server
```

### テスト実行

```bash
# 統合テスト
python -m tests.test_historical_integration

# pytest
pytest tests/
```

### スクリプト実行

```bash
python -m scripts.setup_historical_db 20251102
```

## インポートルール

### src/内
相対インポート：
```python
from .config import Config
```

### tests/, scripts/から
絶対インポート：
```python
from src.config import Config
```

## 環境変数

主な設定（`.env`）：

```bash
ENVIRONMENT=development
JRAVAN_SERVICE_KEY=YOUR_KEY
API_HOST=0.0.0.0
API_PORT=8000
ENABLE_HISTORICAL_DATA=true
HISTORICAL_CACHE_DIR=./historical_cache
```

## モード切り替え

| モード | データソース | JRA-VAN | Python |
|--------|------------|---------|--------|
| 開発（蓄積系） | 過去データ | 不要 | 64bit OK |
| 開発（モック） | 静的データ | 不要 | 64bit OK |
| 本番 | リアルタイム | 必要 | 32bit必須 |

## トラブルシューティング

### ModuleNotFoundError

プロジェクトのルートから実行：
```bash
cd /path/to/jravan_odds_fetcher
python run.py
```

### インポートエラー

モジュールとして実行：
```bash
python -m src.module_name  # OK
python src/module_name.py  # NG
```

## 参考

- [README.md](README.md) - メインドキュメント
- [HISTORICAL_DATA_USAGE.md](HISTORICAL_DATA_USAGE.md) - 過去データ
