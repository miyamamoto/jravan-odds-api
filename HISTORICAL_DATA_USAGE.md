# 過去データ使用ガイド

開発モードで過去のオッズデータを使用する方法。

## 概要

- 過去のレースデータをキャッシュから提供
- 締め切り前n秒のオッズをシミュレート
- JRA-VAN接続不要でテスト可能

## セットアップ

### 1. データダウンロード

```bash
# 1日分
python -m scripts.setup_historical_db 20251102

# 複数日
python -m scripts.setup_historical_db 20251101 --end-date 20251107

# サービスキー指定
python -m scripts.setup_historical_db 20251102 --service-key YOUR_KEY
```

**注意**: 初回は数分～数十分かかります。

### 2. サーバー起動

```bash
export ENVIRONMENT=development
python run.py
```

## 使用例

### 過去のオッズを取得

```bash
# レース一覧
curl http://localhost:8000/api/races/20251102

# オッズ取得
curl http://localhost:8000/api/odds/2025110205041101
```

レスポンス:
```json
{
  "odds": [...],
  "is_past_data": true,
  "data_source": "historical_cache",
  "past_data_note": "これは過去のデータです（キャッシュから取得）"
}
```

### 締め切り前のシミュレーション

```bash
# 300秒前（5分前）
curl "http://localhost:8000/api/odds/2025110205041101?seconds_before_deadline=300"

# 600秒前（10分前）
curl "http://localhost:8000/api/odds/2025110205041101?seconds_before_deadline=600"
```

レスポンス:
```json
{
  "odds": [...],
  "is_past_data": true,
  "seconds_before_deadline": 300,
  "time_status": "締め切りまで 5分0秒",
  "past_data_note": "これは過去のデータです（締め切り300秒前のシミュレーション）"
}
```

## 設定

### 環境変数

```bash
# .env ファイル
ENVIRONMENT=development
ENABLE_HISTORICAL_DATA=true           # 蓄積系データを有効化
HISTORICAL_CACHE_DIR=./historical_cache
HISTORICAL_AUTO_FETCH=false           # キャッシュミス時の自動取得
```

### キャッシュ構造

```
historical_cache/
├── cache_index.json          # インデックス
└── 20251102/                 # 日付別
    ├── 2025110205041101.json # レース別データ
    └── ...
```

## 動作モード

### 開発モード（蓄積系）
- 過去データを使用
- JRA-VAN接続不要
- オッズシミュレーション可能

### 本番モード
- リアルタイムデータ
- JRA-VAN接続必要
- 実際のオッズを取得

## データ保持期間

- **JRA-VAN公式**: 約1年
- **時系列データ**: 単勝・複勝・枠連・馬連のみ
- それ以外はシミュレーション

## トラブルシューティング

### キャッシュがない

```bash
# データをダウンロード
python -m scripts.setup_historical_db 20251102
```

### JVOpen error -111/-112

データベースが初期化されていません：
```bash
python -m scripts.setup_historical_db 20251102 --show-dialog
```

### キャッシュクリア

```bash
# ディレクトリ削除
rm -rf ./historical_cache

# または365日以上前を削除
python -c "from src.odds_cache import OddsCache; OddsCache().clear_old_cache(365)"
```

## テスト

```bash
# 統合テスト実行
python -m tests.test_historical_integration
```

6つのテストが実行され、全て成功することを確認してください。

## 参考

- [README.md](README.md) - メインドキュメント
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - プロジェクト構造
