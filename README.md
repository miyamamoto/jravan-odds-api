# JRA-VAN Odds API

JRA-VAN Data Labから競馬のリアルタイムオッズを取得するREST APIサーバー。

## 主な機能

- 🚀 REST API（FastAPI）
- 📡 WebSocketでリアルタイム配信
- 🔧 開発/本番モード切り替え
- 💾 過去データ対応（蓄積系）

## クイックスタート

### 1. インストール

```bash
pip install -r requirements.txt
```

### 2. サーバー起動

```bash
# 開発モード（モックデータ）
export ENVIRONMENT=development
python run.py

# 本番モード（JRA-VAN接続）
export ENVIRONMENT=production
python run.py
```

APIドキュメント: http://localhost:8000/docs

## 必要な環境

### 開発モード
- Python 3.10+
- FastAPI、uvicorn

### 本番モード
- Python 3.10 **（32bit版）**
- pywin32
- JRA-VAN Data Lab会員（¥980/月）
- JV-Link（Windows専用）

## ディレクトリ構造

```
jravan_odds_fetcher/
├── src/                  # メインコード
│   ├── api_server.py     # APIサーバー
│   ├── config.py         # 設定
│   ├── data_service.py   # データサービス
│   └── ...
├── tests/                # テスト
├── scripts/              # ツール
├── run.py               # 起動スクリプト
└── requirements.txt
```

## APIエンドポイント

| エンドポイント | 説明 |
|-------------|------|
| `GET /health` | ヘルスチェック |
| `GET /api/status` | サーバーステータス |
| `GET /api/races/{date}` | レース一覧（YYYYMMDD） |
| `GET /api/odds/{race_id}` | オッズ取得 |
| `WebSocket /ws/odds/{race_id}` | リアルタイム配信 |

### 使用例

```bash
# レース一覧
curl http://localhost:8000/api/races/20251102

# オッズ取得
curl http://localhost:8000/api/odds/2025110205041101

# 締め切り300秒前のオッズ（開発モード）
curl "http://localhost:8000/api/odds/2025110205041101?seconds_before_deadline=300"
```

## 開発モード：過去データ

開発モードでは過去のオッズデータを使用できます。

### セットアップ

**方法1: 手動セットアップ（推奨）**

```bash
# 過去データをダウンロード
python -m scripts.setup_historical_db 20251102

# 日付範囲指定
python -m scripts.setup_historical_db 20251101 --end-date 20251107
```

**方法2: 自動取得**

キャッシュにデータがない場合、自動的にJRA-VANから取得：

```bash
# .env
HISTORICAL_AUTO_FETCH=true
JRAVAN_SERVICE_KEY=YOUR_KEY

# サーバー起動
python run.py
```

詳細: [AUTO_FETCH_GUIDE.md](AUTO_FETCH_GUIDE.md)

### 使用方法

```bash
export ENVIRONMENT=development
python run.py

# 過去のオッズを取得
curl http://localhost:8000/api/odds/2025110205041101

# 締め切り前をシミュレート
curl "http://localhost:8000/api/odds/2025110205041101?seconds_before_deadline=300"
```

詳細: [HISTORICAL_DATA_USAGE.md](HISTORICAL_DATA_USAGE.md)

## テスト

```bash
# 統合テスト
python -m tests.test_historical_integration

# 全テスト
pytest tests/
```

## 環境変数

`.env`ファイルで設定可能：

```bash
# 実行環境
ENVIRONMENT=development            # development または production

# JRA-VAN設定（本番モード）
JRAVAN_SERVICE_KEY=YOUR_KEY

# API設定
API_HOST=0.0.0.0
API_PORT=8000

# 蓄積系データ設定（開発モード）
ENABLE_HISTORICAL_DATA=true
HISTORICAL_CACHE_DIR=./historical_cache
```

## レースID形式

```
YYYYMMDDJJKKRR
  YYYY: 年
  MM: 月
  DD: 日
  JJ: 場コード（05=東京、06=中山、等）
  KK: 回次
  RR: レース番号
```

例: `2025110205041101` = 2025年11月2日 東京5回4日目 1レース

## トラブルシューティング

### ModuleNotFoundError: No module named 'src'

プロジェクトのルートから実行してください：
```bash
cd /path/to/jravan_odds_fetcher
python run.py
```

### ポート8000が使用中

```bash
# 別のポートを使用
export API_PORT=8001
python run.py
```

### JVInit error（本番モード）

- 32bit Pythonを使用しているか確認
  ```bash
  python -c "import struct; print(f'{struct.calcsize(\"P\") * 8}bit')"
  ```
- JV-Linkがインストールされているか確認
- JRA-VAN会員が有効か確認

## 参考ドキュメント

- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - プロジェクト構造
- [HISTORICAL_DATA_USAGE.md](HISTORICAL_DATA_USAGE.md) - 過去データ詳細
- [AUTO_FETCH_GUIDE.md](AUTO_FETCH_GUIDE.md) - 自動取得機能
- [JRA-VAN公式](https://jra-van.jp/dlb/)

## ライセンス

このプロジェクトはサンプルコードです。JRA-VANの利用規約に従ってご使用ください。

## 免責事項

- このコードの使用により生じた損害について、作者は一切の責任を負いません
- JRA-VANサービス仕様変更により動作しなくなる可能性があります
- データの正確性は保証できません
- 実際の馬券購入には公式データを確認してください
