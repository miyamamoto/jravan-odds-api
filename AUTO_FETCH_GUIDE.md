# 自動取得機能ガイド

キャッシュにデータがない場合、自動的にJRA-VANサーバーから取得する機能。

## 機能概要

開発モードで、以下の場合に自動取得が動作：
- レース情報がキャッシュにない
- オッズデータがキャッシュにない

自動取得が有効の場合、JV-Linkを使用してデータを取得し、キャッシュに保存します。

## 設定方法

### .env ファイル

```bash
ENVIRONMENT=development
ENABLE_HISTORICAL_DATA=true
HISTORICAL_AUTO_FETCH=true        # 👈 これをtrueにする
JRAVAN_SERVICE_KEY=YOUR_KEY       # 👈 JRA-VANサービスキーが必要
```

### 注意事項

**自動取得を有効にする場合:**
- ✅ JRA-VAN会員である必要があります
- ✅ JV-Linkがインストールされている必要があります
- ✅ 32bit Pythonが必要です
- ⚠️ 初回取得時はデータベースセットアップが必要（数分かかる）

## 動作の流れ

### 1. レース情報取得時

```
リクエスト: GET /api/races/20251102
    ↓
キャッシュ確認
    ↓ キャッシュなし（auto_fetch=true）
JV-Linkでレース情報取得
    ↓
オッズデータも取得
    ↓
キャッシュに保存
    ↓
レスポンス返却
```

### 2. オッズ取得時

```
リクエスト: GET /api/odds/2025110205041101
    ↓
キャッシュ確認
    ↓ キャッシュなし（auto_fetch=true）
JV-Linkでオッズデータ取得
    ↓
キャッシュに保存
    ↓
レスポンス返却
```

## 使用例

### 自動取得有効

```bash
# .env
ENVIRONMENT=development
HISTORICAL_AUTO_FETCH=true
JRAVAN_SERVICE_KEY=YOUR_KEY

# サーバー起動
python run.py

# リクエスト（キャッシュになくても自動取得）
curl http://localhost:8000/api/races/20251102
```

初回は取得に時間がかかりますが、次回以降はキャッシュから高速に取得できます。

### 自動取得無効（デフォルト）

```bash
# .env
ENVIRONMENT=development
HISTORICAL_AUTO_FETCH=false

# サーバー起動
python run.py

# リクエスト（キャッシュにないとエラー）
curl http://localhost:8000/api/races/20251102
```

レスポンス:
```json
{
  "races": [],
  "message": "No race data available for 20251102"
}
```

この場合は、手動でセットアップが必要：
```bash
python -m scripts.setup_historical_db 20251102
```

## パフォーマンス

| 状況 | 自動取得OFF | 自動取得ON |
|-----|-----------|----------|
| キャッシュあり | 即座 | 即座 |
| キャッシュなし | エラー | 数秒～数分（初回） |
| 2回目以降 | エラー | 即座（キャッシュ） |

## トラブルシューティング

### 自動取得が動作しない

```bash
# ログを確認
tail -f jravan_api.log

# 確認ポイント
# 1. auto_fetch が true か？
# 2. JRAVAN_SERVICE_KEY が設定されているか？
# 3. JV-Link が初期化されたか？
```

ログ例:
```
INFO - Cache miss for 20251102, fetching race data from JV-Link
INFO - Fetching odds data for 12 races
INFO - Cached 6 odds for race 2025110205041101
```

### JVInit error

```
ERROR - Failed to initialize fetcher: JVInit error: -1
```

**原因:**
- JV-Linkがインストールされていない
- 64bit Pythonを使用している
- サービスキーが無効

**対処:**
1. 32bit Pythonを使用
2. JV-Linkをインストール
3. サービスキーを確認

### データが古い

```bash
# キャッシュをクリアして再取得
rm -rf ./historical_cache
# または
python -c "from src.odds_cache import OddsCache; OddsCache().clear_old_cache(0)"
```

## 推奨設定

### 開発時（ローカル）

```bash
ENVIRONMENT=development
HISTORICAL_AUTO_FETCH=false  # 手動セットアップ推奨
```

理由: 明示的にデータをセットアップする方が制御しやすい

### テスト環境

```bash
ENVIRONMENT=development
HISTORICAL_AUTO_FETCH=true   # 自動取得で便利
JRAVAN_SERVICE_KEY=YOUR_KEY
```

理由: テストデータを自動的に準備できる

### 本番環境

```bash
ENVIRONMENT=production
# HISTORICAL_AUTO_FETCHは使用されない（本番モードではリアルタイム取得）
```

## セキュリティ

- **サービスキーを.envファイルに保存**（.gitignoreに追加済み）
- **サービスキーをコードにハードコードしない**
- **環境変数を使用**

## 参考

- [README.md](README.md) - メインドキュメント
- [HISTORICAL_DATA_USAGE.md](HISTORICAL_DATA_USAGE.md) - 過去データ詳細
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - プロジェクト構造
