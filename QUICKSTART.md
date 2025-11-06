# クイックスタートガイド

JRA-VAN Odds APIを最速で試すためのガイドです。

## 🚀 5分で始める

### ステップ1: セットアップ

```bash
# プロジェクトディレクトリに移動
cd jravan_odds_fetcher

# 依存ライブラリをインストール
pip install -r requirements.txt
```

### ステップ2: サーバー起動（開発モード）

```bash
# 開発モードで起動（モックデータ使用）
python api_server.py
```

出力:
```
============================================================
JRA-VAN Odds API Server
============================================================
環境: development
ホスト: 0.0.0.0
ポート: 8000
モックモード: True
============================================================
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### ステップ3: APIを試す

新しいターミナルを開いて：

```bash
# ヘルスチェック
curl http://localhost:8000/api/health

# レース一覧取得
curl http://localhost:8000/api/races/20240101

# オッズ取得
curl http://localhost:8000/api/odds/2024010105010101
```

ブラウザで確認:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📊 開発モードの特徴

開発モードでは以下の利点があります：

✅ **JRA-VAN不要** - 会員登録やJV-Linkのインストール不要
✅ **64bit Python対応** - 通常のPython環境で動作
✅ **いつでもテスト可能** - レース開催日以外でもテスト可能
✅ **自動変動** - オッズは自動的に変動するため、リアルタイム感を再現

## 🎯 よく使うAPI

### 1. 今日のレース一覧

```bash
curl http://localhost:8000/api/races/20240101
```

### 2. オッズ取得

```bash
# 最新のオッズ
curl http://localhost:8000/api/odds/2024010105010101

# 締め切り5分(300秒)前のオッズ
curl "http://localhost:8000/api/odds/2024010105010101?seconds_before_deadline=300"
```

### 3. レース詳細

```bash
curl http://localhost:8000/api/race/2024010105010101
```

### 4. システムステータス

```bash
curl http://localhost:8000/api/status
```

## 🕐 過去データ・締め切り前データ取得

このAPIは、**過去のデータであることを明示**し、**締め切り前n秒のデータ**を取得できます。

### 過去データの明示

レスポンスに以下が含まれます：

```json
{
  "is_past_data": true,
  "warning": "これは過去のデータです（締め切り300秒前のシミュレーション）",
  "time_status": "締め切りまで 5分0秒",
  "deadline_info": {
    "is_past": false,
    "seconds_until_deadline": -300
  }
}
```

### 締め切り前n秒のデータ取得

```bash
# 締め切り10分(600秒)前
curl "http://localhost:8000/api/odds/2024010105010101?seconds_before_deadline=600"

# 締め切り1分(60秒)前
curl "http://localhost:8000/api/odds/2024010105010101?seconds_before_deadline=60"
```

詳細は [HISTORICAL_ODDS_GUIDE.md](HISTORICAL_ODDS_GUIDE.md) を参照。

## 🔌 WebSocketで接続

### ブラウザコンソールで試す

1. ブラウザで http://localhost:8000 を開く
2. DevTools（F12）を開く
3. Consoleタブで以下を実行：

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/odds/2024010105010101');

ws.onopen = () => console.log('接続成功');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('受信:', data.type, data.odds.length + '件');
};

// Ping送信（接続維持）
setInterval(() => ws.send('ping'), 30000);
```

## 🔄 モード切り替え

### 開発モード → 本番モード

`.env`ファイルを編集：

```bash
# 開発モード
ENVIRONMENT=development

# 本番モード（JRA-VAN使用）
# ENVIRONMENT=production
# JRAVAN_SERVICE_KEY=YOUR_KEY
```

**注意:** 本番モードには以下が必要です：
- JRA-VAN会員登録
- JV-Linkインストール
- 32bit Python環境

## 📝 Pythonから使用

### 例1: オッズ取得

```python
import requests

# レース情報取得
response = requests.get("http://localhost:8000/api/races/20240101")
races = response.json()['races']

# 最初のレースのオッズを取得
race_id = races[0]['race_id']
odds_response = requests.get(f"http://localhost:8000/api/odds/{race_id}")
odds = odds_response.json()

print(f"レース: {races[0]['race_name']}")
print(f"オッズ種類: {odds['count']}種類")

# 単勝オッズを表示
for item in odds['odds']:
    if item['record_id'] == 'O1':
        print("\n単勝オッズ:")
        for tansho in item['tansho']:
            print(f"  {tansho['umaban']}番: {tansho['odds']}倍")
```

### 例2: WebSocket接続

```python
import asyncio
import websockets
import json

async def receive_realtime_odds():
    uri = "ws://localhost:8000/ws/odds/2024010105010101"

    async with websockets.connect(uri) as websocket:
        print("リアルタイムオッズ受信開始...")

        while True:
            message = await websocket.recv()
            data = json.loads(message)

            print(f"\n[{data['timestamp']}] {data['type']}")
            print(f"オッズ件数: {len(data['odds'])}")

asyncio.run(receive_realtime_odds())
```

## 🛠️ トラブルシューティング

### "Address already in use"

ポートが使用中の場合、`.env`でポートを変更：

```bash
API_PORT=8001
```

### "Module not found"

依存ライブラリをインストール：

```bash
pip install -r requirements.txt
```

### オッズが取得できない

開発モードでは、`mock_data/sample_odds.json`に定義されたレースIDのみ使用可能です。

利用可能なレースID:
- `2024010105010101`
- `2024010105010102`

## 📚 次のステップ

1. **API_GUIDE.md** - 詳細なAPI仕様
2. **README.md** - 全体的な概要
3. **setup_guide.md** - 本番環境セットアップ

## 🎓 学習リソース

### ドキュメント
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### サンプルコード
- `example_usage.py` - CLI版のサンプル
- `API_GUIDE.md` の実用例セクション

### 設定
- `.env.example` - 環境変数テンプレート
- `config.py` - 設定項目一覧

## 💡 開発のヒント

### デバッグモード

```bash
# ログレベルを DEBUG に変更
LOG_LEVEL=DEBUG python api_server.py
```

### データ保存を有効化

```bash
# .env で設定
ENABLE_DATA_SAVE=true
DATA_DIR=./data
```

取得したオッズは`data/`ディレクトリに保存されます。

### 更新間隔の変更

WebSocketの更新間隔を変更：

```bash
# .env で設定（秒単位）
REALTIME_UPDATE_INTERVAL=5
```

## 🚀 デプロイ

### Dockerで実行

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV ENVIRONMENT=development
ENV API_PORT=8000

CMD ["python", "api_server.py"]
```

```bash
# ビルド
docker build -t jravan-api .

# 実行
docker run -p 8000:8000 -e ENVIRONMENT=development jravan-api
```

### systemdサービス

```ini
[Unit]
Description=JRA-VAN Odds API
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/jravan_odds_fetcher
Environment="ENVIRONMENT=production"
ExecStart=/usr/bin/python3 api_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📞 サポート

問題が発生した場合：

1. ログファイルを確認: `jravan_api.log`
2. 環境設定を確認: `.env`
3. システムステータスを確認: `GET /api/status`

## 🎉 完了！

これでJRA-VAN Odds APIを使い始める準備ができました。

より詳細な情報は `API_GUIDE.md` を参照してください。
