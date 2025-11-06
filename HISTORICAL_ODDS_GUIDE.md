# 過去データ・締め切り前データ取得ガイド

## 概要

このAPIでは、以下の機能をサポートしています：

1. **過去データの明示**: レースが締め切り後の場合、明示的に「過去のデータです」と表示
2. **締め切り前n秒のデータ取得**: 締め切りの何秒前のオッズを取得するか指定可能
3. **締め切り情報の提供**: 発走時刻、締め切り時刻、残り時間などの詳細情報

これらの機能は、開発・テスト・バックテスト時に非常に便利です。

## 使用方法

### 1. 通常のオッズ取得（最新データ）

```bash
curl http://localhost:8000/api/odds/2024010105010101
```

レスポンス:
```json
{
  "race_id": "2024010105010101",
  "odds": [...],
  "count": 6,
  "timestamp": "2024-01-01T10:00:00",
  "is_past_data": false,
  "deadline_info": {
    "post_time": "2024-01-01T10:00:00",
    "deadline": "2024-01-01T09:59:00",
    "current_time": "2024-01-01T09:55:00",
    "is_past": false,
    "seconds_until_deadline": 240,
    "status": "active",
    "deadline_margin_seconds": 60
  }
}
```

### 2. 締め切り前n秒のデータ取得

```bash
# 締め切り300秒(5分)前のオッズを取得
curl "http://localhost:8000/api/odds/2024010105010101?seconds_before_deadline=300"

# 締め切り600秒(10分)前のオッズを取得
curl "http://localhost:8000/api/odds/2024010105010101?seconds_before_deadline=600"

# 締め切り60秒(1分)前のオッズを取得
curl "http://localhost:8000/api/odds/2024010105010101?seconds_before_deadline=60"
```

レスポンス:
```json
{
  "race_id": "2024010105010101",
  "odds": [...],
  "count": 6,
  "timestamp": "2024-01-01T10:00:00",
  "is_past_data": true,
  "warning": "これは過去のデータです（締め切り300秒前のシミュレーション）",
  "time_status": "締め切りまで 5分0秒",
  "seconds_before_deadline": 300,
  "deadline_info": {...}
}
```

**重要**: `is_past_data: true` と `warning` フィールドで、これが過去データであることが明示されます。

### 3. 過去レースのデータ取得

締め切り後のレースの場合、自動的に過去データとして識別されます。

```bash
# 既に締め切りが過ぎたレース
curl http://localhost:8000/api/odds/2024010105010101
```

レスポンス:
```json
{
  "race_id": "2024010105010101",
  "odds": [...],
  "count": 6,
  "timestamp": "2024-01-01T11:00:00",
  "is_past_data": true,
  "warning": "これは過去のデータです（締め切り後3600秒経過）",
  "time_status": "締め切り後 1時間",
  "deadline_info": {
    "post_time": "2024-01-01T10:00:00",
    "deadline": "2024-01-01T09:59:00",
    "current_time": "2024-01-01T11:00:00",
    "is_past": true,
    "seconds_until_deadline": -3600,
    "status": "past"
  }
}
```

## 締め切り情報の詳細

### deadline_info フィールド

| フィールド | 説明 | 例 |
|-----------|------|-----|
| post_time | 発走時刻 | "2024-01-01T10:00:00" |
| deadline | 締め切り時刻（発走60秒前） | "2024-01-01T09:59:00" |
| current_time | 現在時刻 | "2024-01-01T09:55:00" |
| is_past | 過去レースか | false / true |
| seconds_until_deadline | 締め切りまでの秒数（負の場合は締め切り後） | 240 / -3600 |
| status | ステータス | "active" / "past" |
| deadline_margin_seconds | 締め切り余裕時間 | 60 |

### time_status フィールド

人間が読みやすい形式での時刻表示：

- `"締め切りまで 4分0秒"`
- `"締め切りまで 1時間30分"`
- `"締め切り後 1時間"`
- `"締め切り後 5分"`

## 実用例

### 例1: バックテスト用データ収集

```python
import requests
import time

race_id = "2024010105010101"

# 締め切り前の複数時点でオッズを取得
time_points = [3600, 1800, 900, 600, 300, 60]  # 60分前、30分前、15分前、10分前、5分前、1分前

for seconds_before in time_points:
    response = requests.get(
        f"http://localhost:8000/api/odds/{race_id}",
        params={'seconds_before_deadline': seconds_before}
    )

    data = response.json()

    if data['is_past_data']:
        print(f"✓ {data['time_status']}: {data['warning']}")
        print(f"  オッズ件数: {data['count']}")

    time.sleep(1)  # サーバー負荷軽減
```

出力:
```
✓ 締め切りまで 1時間0分: これは過去のデータです（締め切り3600秒前のシミュレーション）
  オッズ件数: 6
✓ 締め切りまで 30分0秒: これは過去のデータです（締め切り1800秒前のシミュレーション）
  オッズ件数: 6
...
```

### 例2: オッズ変動分析

```python
import requests
import pandas as pd

race_id = "2024010105010101"

# 時系列でオッズを取得
time_series_data = []

for seconds_before in range(3600, 0, -60):  # 60分前から1分ごと
    response = requests.get(
        f"http://localhost:8000/api/odds/{race_id}",
        params={'seconds_before_deadline': seconds_before}
    )

    data = response.json()

    # 単勝オッズを抽出
    for odds_item in data['odds']:
        if odds_item['record_id'] == 'O1':
            for tansho in odds_item.get('tansho', []):
                time_series_data.append({
                    'seconds_before': seconds_before,
                    'umaban': tansho['umaban'],
                    'odds': tansho['odds']
                })

# DataFrameに変換して分析
df = pd.DataFrame(time_series_data)
print(df.head())

# オッズ変動をグラフ化
import matplotlib.pyplot as plt

for umaban in df['umaban'].unique():
    horse_data = df[df['umaban'] == umaban]
    plt.plot(horse_data['seconds_before'], horse_data['odds'], label=f'{umaban}番')

plt.xlabel('締め切りまでの時間（秒）')
plt.ylabel('単勝オッズ')
plt.legend()
plt.title('オッズ変動')
plt.show()
```

### 例3: 締め切り間際のオッズ監視

```python
import requests
import time

race_id = "2024010105010101"

while True:
    response = requests.get(f"http://localhost:8000/api/odds/{race_id}")
    data = response.json()

    deadline_info = data['deadline_info']
    seconds_left = deadline_info['seconds_until_deadline']

    if seconds_left <= 0:
        print("⚠️ 締め切りを過ぎました")
        break

    print(f"締め切りまで: {data.get('time_status', '')} (残り{seconds_left}秒)")

    # 単勝オッズTOP3を表示
    for odds_item in data['odds']:
        if odds_item['record_id'] == 'O1':
            tansho = sorted(odds_item.get('tansho', []), key=lambda x: x['odds'])[:3]
            print("単勝オッズ TOP3:")
            for t in tansho:
                print(f"  {t['umaban']}番: {t['odds']}倍")

    print()
    time.sleep(10)  # 10秒ごとに更新
```

### 例4: 過去データ判定とアラート

```python
import requests

def fetch_odds_with_check(race_id, seconds_before=None):
    """
    オッズを取得し、過去データかどうかをチェック
    """
    params = {}
    if seconds_before:
        params['seconds_before_deadline'] = seconds_before

    response = requests.get(
        f"http://localhost:8000/api/odds/{race_id}",
        params=params
    )

    data = response.json()

    # 過去データの場合は警告
    if data.get('is_past_data'):
        print("⚠️ 警告:", data.get('warning'))
        print(f"📊 ステータス: {data.get('time_status')}")

        if data['deadline_info'].get('is_past'):
            print("❌ このレースは既に締め切られています")
        else:
            print(f"ℹ️  締め切り{data.get('seconds_before_deadline')}秒前のデータです")
    else:
        print("✅ 最新のオッズデータです")

    return data

# 使用例
print("=== 最新データ取得 ===")
fetch_odds_with_check("2024010105010101")

print("\n=== 5分前のデータ取得 ===")
fetch_odds_with_check("2024010105010101", seconds_before=300)
```

## WebSocketでの過去データ通知

WebSocket接続でも、過去データ情報が送信されます。

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/odds/2024010105010101');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  // 過去データチェック
  if (data.is_past_data) {
    console.warn('⚠️ 過去データ:', data.warning);
    console.log('ステータス:', data.time_status);
  }

  // 締め切り情報
  const deadline = data.deadline_info;
  if (deadline.is_past) {
    console.log('❌ 締め切り後');
  } else {
    console.log(`⏰ 締め切りまで ${deadline.seconds_until_deadline}秒`);
  }

  // オッズデータ
  console.log('オッズ件数:', data.odds.length);
};
```

## オッズシミュレーションの仕組み

`seconds_before_deadline`パラメータを指定した場合、以下のアルゴリズムでオッズがシミュレートされます：

1. **ベースオッズ**: 現在のオッズを基準とする
2. **変動係数**: 時間が遡るほど変動を大きくする
   - 締め切り直前: ±10%程度の変動
   - 1時間前: ±20%程度の変動
3. **ランダム性**: 各馬ごとに独立した変動を適用

これにより、実際のオッズ変動に近いデータが生成されます。

**注意**: シミュレートされたデータには `simulated: true` フラグが付きます。

## ベストプラクティス

### 1. 過去データフラグの確認

```python
def is_safe_to_bet(odds_response):
    """
    馬券購入可能かチェック
    """
    if odds_response.get('is_past_data'):
        print("⚠️ 過去データのため馬券購入不可")
        return False

    deadline_info = odds_response.get('deadline_info', {})
    seconds_left = deadline_info.get('seconds_until_deadline', 0)

    if seconds_left < 60:
        print("⚠️ 締め切り直前のため危険")
        return False

    return True
```

### 2. タイムアウト処理

```python
import requests
from requests.exceptions import Timeout

def fetch_odds_with_timeout(race_id, timeout=5):
    """
    タイムアウト付きでオッズ取得
    """
    try:
        response = requests.get(
            f"http://localhost:8000/api/odds/{race_id}",
            timeout=timeout
        )
        return response.json()
    except Timeout:
        print("⚠️ タイムアウト: サーバーの応答が遅すぎます")
        return None
```

### 3. エラーハンドリング

```python
def safe_fetch_odds(race_id, seconds_before=None):
    """
    安全なオッズ取得
    """
    try:
        params = {}
        if seconds_before:
            params['seconds_before_deadline'] = seconds_before

        response = requests.get(
            f"http://localhost:8000/api/odds/{race_id}",
            params=params
        )

        response.raise_for_status()
        data = response.json()

        # エラーチェック
        if 'error' in data:
            print(f"❌ エラー: {data['error']}")
            return None

        return data

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTPエラー: {e}")
        return None
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return None
```

## まとめ

この機能により、以下が実現できます：

✅ **開発・テストの容易化**: 実際のレース時間外でもテスト可能
✅ **バックテストの実施**: 過去の時点のオッズを再現して分析
✅ **安全性の向上**: 過去データであることが明示されるため、誤って古いデータで判断するリスクを軽減
✅ **オッズ変動分析**: 時系列でのオッズ変動を詳細に分析可能

詳細は[API_GUIDE.md](API_GUIDE.md)も参照してください。
