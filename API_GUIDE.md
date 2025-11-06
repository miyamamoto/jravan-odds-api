# JRA-VAN Odds API 使用ガイド

## 概要

JRA-VAN Odds APIは、競馬のリアルタイムオッズ情報を取得するためのREST APIおよびWebSocketサーバーです。

### 主な機能

- ✅ REST APIによるオッズ取得
- ✅ WebSocketによるリアルタイムオッズ配信
- ✅ 開発モード（モックデータ）と本番モード（JRA-VAN）の切り替え
- ✅ オッズデータの自動保存
- ✅ CORS対応

## セットアップ

### 1. 依存ライブラリのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境設定

`.env`ファイルを作成（`.env.example`を参考）：

```bash
# 開発環境（モックデータ使用）
ENVIRONMENT=development

# 本番環境（JRA-VAN使用）
# ENVIRONMENT=production
# JRAVAN_SERVICE_KEY=YOUR_KEY

API_HOST=0.0.0.0
API_PORT=8000
```

### 3. サーバー起動

```bash
# 開発モード（モックデータ）
python api_server.py

# または uvicornで直接起動
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

サーバーが起動すると、以下のURLでアクセスできます：
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## REST API エンドポイント

### ルート

**GET /** - API情報

```bash
curl http://localhost:8000/
```

レスポンス:
```json
{
  "message": "JRA-VAN Odds API",
  "version": "1.0.0",
  "environment": "development",
  "endpoints": {...}
}
```

### ヘルスチェック

**GET /api/health** - サーバーの健全性チェック

```bash
curl http://localhost:8000/api/health
```

レスポンス:
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T10:00:00",
  "environment": "development"
}
```

### システムステータス

**GET /api/status** - システム状態取得

```bash
curl http://localhost:8000/api/status
```

レスポンス:
```json
{
  "service_status": {
    "mode": "mock",
    "jravan_available": false,
    "jravan_initialized": false,
    "mock_provider_initialized": true,
    "data_save_enabled": true,
    "cache_enabled": true
  },
  "config": {...},
  "timestamp": "2024-01-01T10:00:00"
}
```

### レース情報取得

**GET /api/races/{date}** - 指定日のレース一覧

パラメータ:
- `date`: 日付（YYYYMMDD形式）

```bash
curl http://localhost:8000/api/races/20240101
```

レスポンス:
```json
{
  "date": "20240101",
  "races": [
    {
      "race_id": "2024010105010101",
      "race_name": "3歳未勝利",
      "race_number": 1,
      "venue": "東京",
      "post_time": "10:00",
      "distance": 1600,
      "track_type": "芝"
    }
  ],
  "count": 1
}
```

### オッズ取得

**GET /api/odds/{race_id}** - 指定レースのオッズ取得

パラメータ:
- `race_id`: レースID（14桁）
- `save` (optional): データを保存するか（true/false）

```bash
curl http://localhost:8000/api/odds/2024010105010101

# データを保存する場合
curl http://localhost:8000/api/odds/2024010105010101?save=true
```

レスポンス:
```json
{
  "race_id": "2024010105010101",
  "odds": [
    {
      "record_type": "単勝・複勝オッズ",
      "record_id": "O1",
      "odds_time_formatted": "09:58:30",
      "tansho": [
        {"umaban": 1, "odds": 2.5},
        {"umaban": 2, "odds": 5.2}
      ],
      "fukusho": [
        {"umaban": 1, "odds_min": 1.2, "odds_max": 1.5}
      ]
    }
  ],
  "count": 6,
  "timestamp": "2024-01-01T10:00:00"
}
```

### レース詳細

**GET /api/race/{race_id}** - レース詳細情報

```bash
curl http://localhost:8000/api/race/2024010105010101
```

レスポンス:
```json
{
  "race_id": "2024010105010101",
  "race_name": "3歳未勝利",
  "date": "20240101",
  "venue": "東京",
  "horses": [
    {"umaban": 1, "horse_name": "サンプルホース1", "jockey": "騎手A"}
  ],
  "odds": {...}
}
```

### 保存されたオッズ取得

**GET /api/saved-odds/{race_id}** - 保存済みオッズデータ取得

```bash
curl http://localhost:8000/api/saved-odds/2024010105010101
```

## WebSocket API

### リアルタイムオッズ配信

**WebSocket /ws/odds/{race_id}** - オッズのリアルタイム配信

#### JavaScript例

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/odds/2024010105010101');

ws.onopen = () => {
  console.log('接続成功');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('オッズ更新:', data);

  if (data.type === 'initial') {
    console.log('初回データ:', data.odds);
  } else if (data.type === 'update') {
    console.log('更新データ:', data.odds);
  }
};

ws.onerror = (error) => {
  console.error('エラー:', error);
};

ws.onclose = () => {
  console.log('接続終了');
};

// Ping送信（接続維持）
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send('ping');
  }
}, 30000);
```

#### Python例

```python
import asyncio
import websockets
import json

async def receive_odds():
    uri = "ws://localhost:8000/ws/odds/2024010105010101"

    async with websockets.connect(uri) as websocket:
        print("接続成功")

        # Ping送信タスク
        async def send_ping():
            while True:
                await asyncio.sleep(30)
                await websocket.send("ping")

        asyncio.create_task(send_ping())

        # データ受信
        while True:
            message = await websocket.recv()
            data = json.loads(message)

            if data['type'] == 'initial':
                print("初回データ:", len(data['odds']))
            elif data['type'] == 'update':
                print("更新:", data['timestamp'])

asyncio.run(receive_odds())
```

### メッセージフォーマット

#### 初回データ
```json
{
  "type": "initial",
  "race_id": "2024010105010101",
  "odds": [...],
  "timestamp": "2024-01-01T10:00:00"
}
```

#### 更新データ
```json
{
  "type": "update",
  "race_id": "2024010105010101",
  "odds": [...],
  "timestamp": "2024-01-01T10:00:30"
}
```

## 開発モードと本番モード

### 開発モード（Development）

モックデータを使用するため、JRA-VAN会員登録やJV-Linkのインストールが不要です。

**設定:**
```bash
ENVIRONMENT=development
```

**特徴:**
- ✅ JRA-VAN不要
- ✅ 64bit Pythonで動作
- ✅ いつでもテスト可能
- ✅ オッズは自動的に変動
- ⚠️ 実際のデータではない

**使用例:**
```python
# .envで設定
ENVIRONMENT=development

# または環境変数で設定
export ENVIRONMENT=development
python api_server.py
```

### 本番モード（Production）

実際のJRA-VANからデータを取得します。

**設定:**
```bash
ENVIRONMENT=production
JRAVAN_SERVICE_KEY=YOUR_KEY
```

**前提条件:**
- ✅ JRA-VAN Data Lab会員登録
- ✅ JV-Linkインストール
- ✅ 32bit Python
- ✅ pywin32インストール

**使用例:**
```python
# .envで設定
ENVIRONMENT=production
JRAVAN_SERVICE_KEY=YOUR_SERVICE_KEY

# Windows 32bit環境で起動
python api_server.py
```

## レースIDの形式

レースIDは14桁の数字で構成されます：

```
YYYYMMDDJJKKRR
```

- **YYYY**: 年（4桁）
- **MM**: 月（2桁）
- **DD**: 日（2桁）
- **JJ**: 場コード（2桁）
  - 05: 東京
  - 06: 中山
  - など
- **KK**: 回次（2桁）
- **RR**: レース番号（2桁）

**例:**
- `2024010105010101`: 2024年1月1日 東京1回1日目 1レース
- `2024032306050312`: 2024年3月23日 中山5回3日目 12レース

## データ保存

オッズデータは自動的に保存できます。

**設定:**
```bash
ENABLE_DATA_SAVE=true
DATA_DIR=./data
```

**保存形式:**
```
data/
  └── 20240101/
      ├── 2024010105010101_095830.json
      ├── 2024010105010101_100000.json
      └── 2024010105010101_100030.json
```

各ファイルには以下が含まれます：
```json
{
  "race_id": "2024010105010101",
  "timestamp": "2024-01-01T10:00:00",
  "odds": [...]
}
```

## エラーハンドリング

### HTTPステータスコード

- `200`: 成功
- `404`: リソースが見つからない
- `500`: サーバーエラー

### エラーレスポンス

```json
{
  "error": "エラータイプ",
  "detail": "詳細メッセージ",
  "timestamp": "2024-01-01T10:00:00"
}
```

## 実用例

### 例1: 今日のレース一覧とオッズを取得

```python
import requests
from datetime import datetime

# 今日の日付
today = datetime.now().strftime("%Y%m%d")

# レース一覧取得
response = requests.get(f"http://localhost:8000/api/races/{today}")
races = response.json()['races']

print(f"本日のレース数: {len(races)}")

# 各レースのオッズを取得
for race in races:
    race_id = race['race_id']
    odds_response = requests.get(f"http://localhost:8000/api/odds/{race_id}")
    odds_data = odds_response.json()

    print(f"\n{race['race_name']} ({race['race_number']}R)")
    print(f"  オッズ種類数: {odds_data['count']}")
```

### 例2: WebSocketでリアルタイム監視

```python
import asyncio
import websockets
import json

async def monitor_odds(race_id):
    uri = f"ws://localhost:8000/ws/odds/{race_id}"

    async with websockets.connect(uri) as ws:
        print(f"レース {race_id} を監視開始")

        while True:
            message = await ws.recv()
            data = json.loads(message)

            # 単勝オッズのみ表示
            for odds in data['odds']:
                if odds['record_id'] == 'O1':
                    print(f"\n{data['timestamp']}")
                    for tansho in odds.get('tansho', [])[:5]:
                        print(f"  {tansho['umaban']}番: {tansho['odds']}倍")

# 実行
asyncio.run(monitor_odds("2024010105010101"))
```

### 例3: 定期的にオッズを保存

```python
import requests
import time

race_id = "2024010105010101"

while True:
    # オッズ取得＆保存
    response = requests.get(
        f"http://localhost:8000/api/odds/{race_id}",
        params={'save': True}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"保存: {data['timestamp']}")

    # 1分待機
    time.sleep(60)
```

## トラブルシューティング

### サーバーが起動しない

**原因:** ポートが既に使用中

**対処:**
```bash
# .envでポートを変更
API_PORT=8001
```

### オッズが取得できない

**開発モード:**
- `mock_data/sample_odds.json`が存在するか確認
- レースIDがモックデータに存在するか確認

**本番モード:**
- JV-Linkが初期化されているか確認
- レースIDが正しいか確認
- オッズ発表時間か確認

### WebSocketが切断される

**原因:** タイムアウト

**対処:**
```javascript
// 定期的にpingを送信
setInterval(() => {
  ws.send('ping');
}, 30000);
```

## 設定リファレンス

| 設定項目 | デフォルト値 | 説明 |
|---------|------------|------|
| ENVIRONMENT | development | 実行環境 |
| API_HOST | 0.0.0.0 | APIホスト |
| API_PORT | 8000 | APIポート |
| CORS_ORIGINS | * | CORS許可オリジン |
| ENABLE_DATA_SAVE | true | データ保存の有効化 |
| DATA_DIR | ./data | データ保存ディレクトリ |
| REALTIME_UPDATE_INTERVAL | 10 | 更新間隔（秒） |
| LOG_LEVEL | INFO | ログレベル |

## 参考リンク

- FastAPI ドキュメント: https://fastapi.tiangolo.com/
- WebSocket: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
- JRA-VAN: https://jra-van.jp/
