# JRA-VAN リアルタイムオッズ取得API

JRA-VAN Data Lab のJV-Linkを使用して、競馬のリアルタイムオッズデータを取得するPythonスクリプト＆REST APIサーバーです。

## ✨ 主な機能

- 🚀 **REST API**: FastAPIベースのRESTful API
- 📡 **WebSocket**: リアルタイムオッズ配信
- 🔧 **開発モード**: JRA-VAN不要でテスト可能（モックデータ）
- 💾 **データ保存**: オッズデータの自動保存
- 📊 **CLIツール**: コマンドラインからの直接利用
- 🔄 **モード切替**: 開発/本番環境の簡単切り替え
- 🕐 **過去データ明示**: 過去データであることを明確に表示
- ⏱️ **締め切り前データ**: 締め切りn秒前のオッズを取得可能

## 🚀 クイックスタート

### APIサーバー（開発モード）

```bash
# インストール
pip install -r requirements.txt

# サーバー起動（モックデータ使用）
python api_server.py

# ブラウザで確認
# http://localhost:8000/docs
```

詳細は [QUICKSTART.md](QUICKSTART.md) を参照してください。

### CLIツール

```bash
# 直接実行
python jravan_odds_fetcher.py

# サンプル実行
python example_usage.py
```

## 必要な環境

### 1. JRA-VANの準備

- **JRA-VAN Data Lab会員登録**（有料）
  - 公式サイト: https://jra-van.jp/dlb/
  - 月額料金: ¥980（2024年時点）

- **JV-Linkのインストール**
  - JRA-VAN Data Labの会員ページからダウンロード
  - Windows専用（32bit COMコンポーネント）

### 2. Pythonの準備

**重要: 32bit版のPythonが必要です**

JV-Linkは32bit COMコンポーネントのため、64bit版Pythonでは動作しません。

#### 32bit版Pythonのインストール方法

1. Python公式サイトから32bit版をダウンロード
   - https://www.python.org/downloads/
   - "Windows installer (32-bit)" を選択

2. インストール時の注意
   - "Add Python to PATH" にチェック
   - 既存の64bit版と共存可能（異なるパスにインストール）

#### 使用中のPythonのビット数確認

```bash
python -c "import struct; print(f'{struct.calcsize(\"P\") * 8}bit')"
```

### 3. 必要なライブラリ

```bash
# 32bit版Pythonで実行
pip install pywin32
```

または

```bash
pip install -r requirements.txt
```

## ファイル構成

```
jravan_odds_fetcher/
├── jravan_odds_fetcher.py  # メインスクリプト
├── odds_parser.py          # オッズデータ詳細パーサー
├── requirements.txt        # 依存ライブラリ
└── README.md              # このファイル
```

## 使い方

### 基本的な使用方法

```bash
# 32bit版Pythonで実行
python jravan_odds_fetcher.py
```

### プログラムからの利用

```python
from jravan_odds_fetcher import JRAVANOddsFetcher
from datetime import datetime

# フェッチャーの初期化
fetcher = JRAVANOddsFetcher()
fetcher.initialize()

# 1. 今日のレース情報を取得
today = datetime.now().strftime("%Y%m%d")
race_info = fetcher.get_race_info(today)

# 2. 特定レースのオッズを取得
# レースID形式: YYYYMMDDJJKKRR
#   YYYY: 年
#   MM: 月
#   DD: 日
#   JJ: 場コード (05=東京, 06=中山, など)
#   KK: 回次
#   RR: レース番号

race_id = "2024010105010201"  # 2024年1月1日 東京1回2日目 1レース
odds_data = fetcher.get_realtime_odds(race_id)

# 結果の表示
for odds in odds_data:
    print(f"{odds['type']}: {odds['record_id']}")

# クリーンアップ
fetcher.close()
```

### 詳細なオッズパース

```python
from jravan_odds_fetcher import JRAVANOddsFetcher
from odds_parser import parse_odds_record

fetcher = JRAVANOddsFetcher()
fetcher.initialize()

# オッズ取得（生データ）
race_id = "2024010105010201"
raw_odds = fetcher.get_realtime_odds(race_id)

# 詳細パース
for odds in raw_odds:
    parsed = parse_odds_record(odds['record_id'], odds.get('raw_data', ''))

    # 単勝・複勝の場合
    if parsed.get('record_type') == '単勝・複勝オッズ':
        print("単勝オッズ:")
        for tansho in parsed.get('tansho', []):
            print(f"  {tansho['umaban']}番: {tansho['odds']}")

        print("複勝オッズ:")
        for fukusho in parsed.get('fukusho', []):
            print(f"  {fukusho['umaban']}番: {fukusho['odds_min']}-{fukusho['odds_max']}")

fetcher.close()
```

## レースIDの構成

レースIDは14桁の数字で構成されます：

```
YYYYMMDDJJKKRR
```

- **YYYY**: 年（4桁）
- **MM**: 月（2桁）
- **DD**: 日（2桁）
- **JJ**: 場コード（2桁）
  - 01: 札幌
  - 02: 函館
  - 03: 福島
  - 04: 新潟
  - 05: 東京
  - 06: 中山
  - 07: 中京
  - 08: 京都
  - 09: 阪神
  - 10: 小倉
- **KK**: 回次（2桁）
- **RR**: レース番号（2桁）

### レースID例

- `2024010105010201`: 2024年1月1日 東京1回2日目 1レース
- `2024032306050312`: 2024年3月23日 中山5回3日目 12レース

## オッズデータの種類

JV-Linkで取得できるオッズデータ（レコードID）：

- **O1**: 単勝・複勝オッズ
- **O2**: 枠連オッズ
- **O3**: 馬連オッズ
- **O4**: ワイドオッズ
- **O5**: 馬単オッズ
- **O6**: 三連複・三連単オッズ

## トラブルシューティング

### エラー: "初期化に失敗しました"

**原因:**
- JV-Linkがインストールされていない
- JRA-VAN会員登録が完了していない
- 64bit版Pythonを使用している

**対処法:**
1. JV-Linkがインストールされているか確認
2. 32bit版Pythonを使用しているか確認
   ```bash
   python -c "import struct; print(struct.calcsize('P') * 8)"
   ```
   → "32" と表示されればOK

### エラー: "JVRTOpen エラー: -1"

**原因:**
- ネットワーク接続の問題
- JRA-VAN会員の有効期限切れ
- 不正なレースID

**対処法:**
1. インターネット接続を確認
2. JRA-VAN会員ステータスを確認
3. レースIDの形式が正しいか確認

### データが取得できない

**原因:**
- 指定したレースが存在しない
- オッズ発表前の時間帯
- 過去のレースでオッズデータが削除されている

**対処法:**
1. レースIDを確認
2. レース当日のオッズ発表時間（通常10:00頃～）を確認
3. 最新のレースを指定

## 📡 API機能

このプロジェクトはREST APIサーバーも提供しています。

### APIエンドポイント

- `GET /api/health` - ヘルスチェック
- `GET /api/status` - システムステータス
- `GET /api/races/{date}` - 指定日のレース一覧
- `GET /api/odds/{race_id}` - オッズ取得
- `GET /api/race/{race_id}` - レース詳細
- `WebSocket /ws/odds/{race_id}` - リアルタイムオッズ配信

### 開発モード vs 本番モード

| 機能 | 開発モード | 本番モード |
|-----|----------|----------|
| JRA-VAN会員 | 不要 | 必要 |
| JV-Link | 不要 | 必要 |
| Python | 64bit OK | 32bit必須 |
| データ | モック | 実データ |
| 利用可能時期 | いつでも | レース開催時 |

### APIサーバー起動

```bash
# 開発モード（推奨）
python api_server.py

# ブラウザで確認
# http://localhost:8000/docs
```

詳細は以下を参照：
- [QUICKSTART.md](QUICKSTART.md) - 最速で始める
- [API_GUIDE.md](API_GUIDE.md) - 詳細なAPI仕様
- [HISTORICAL_ODDS_GUIDE.md](HISTORICAL_ODDS_GUIDE.md) - 過去データ・締め切り前データ取得ガイド

### 使用例

```python
import requests

# レース一覧取得
response = requests.get("http://localhost:8000/api/races/20240101")
races = response.json()['races']

# オッズ取得
race_id = races[0]['race_id']
odds = requests.get(f"http://localhost:8000/api/odds/{race_id}").json()

print(f"オッズ種類: {odds['count']}種類")
```

### WebSocket接続

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/odds/2024010105010101');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('オッズ更新:', data);
};
```

## 注意事項

### データ利用について

- JRA-VANのデータは**著作権で保護**されています
- 商用利用には別途契約が必要な場合があります
- データの再配布は禁止されています
- 利用規約を必ず確認してください

### 技術的制限

- **Windows専用**: JV-LinkはWindows専用COMコンポーネントです
- **32bit Python必須**: 64bit版では動作しません
- **リアルタイム性**: ネットワーク状況により遅延が発生する場合があります

### パフォーマンス

- 大量のレースデータを連続取得すると、サーバー負荷が高くなります
- 適切な間隔（数秒程度）を空けてリクエストしてください
- 必要なデータのみを取得するよう心がけてください

## 参考リンク

- [JRA-VAN Data Lab 公式サイト](https://jra-van.jp/dlb/)
- [JRA-VAN 開発者コミュニティ](https://developer.jra-van.jp/)
- [JV-Link 仕様書](https://jra-van.jp/dlb/sdv/) (会員限定)

## ライセンス

このスクリプトはサンプルコードです。自己責任でご使用ください。

## 免責事項

- このスクリプトの使用により生じた損害について、作者は一切の責任を負いません
- JRA-VANのサービス仕様変更により動作しなくなる可能性があります
- データの正確性については保証できません
- 実際の馬券購入等にご利用の際は、必ず公式データを確認してください
