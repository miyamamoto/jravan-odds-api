# セットアップガイド

このガイドでは、JRA-VAN オッズ取得スクリプトを使用するための詳細なセットアップ手順を説明します。

## ステップ1: JRA-VAN Data Lab会員登録

### 1.1 会員登録

1. JRA-VAN公式サイトにアクセス
   https://jra-van.jp/

2. 「JRA-VAN Data Lab」を選択

3. 新規会員登録を実施
   - 月額料金: ¥980（税込）
   - クレジットカードまたは銀行振込

4. 登録完了後、会員IDとパスワードを控える

### 1.2 JV-Linkのダウンロードとインストール

1. 会員ページにログイン

2. 「開発キット」セクションから「JV-Link」をダウンロード

3. ダウンロードしたインストーラーを実行
   - 管理者権限で実行
   - デフォルト設定でインストールを推奨

4. インストール完了を確認

## ステップ2: Python環境の準備

### 2.1 32bit版Pythonのインストール

**重要: 必ず32bit版をインストールしてください**

#### オプションA: 新規インストール

1. Python公式サイトにアクセス
   https://www.python.org/downloads/

2. 最新の安定版をクリック
   （Python 3.10以降を推奨）

3. ダウンロードページで「Windows installer (32-bit)」を選択

4. インストーラーを実行
   - **重要**: "Add Python to PATH" にチェック
   - "Install Now" をクリック

5. インストール完了後、コマンドプロンプトで確認
   ```cmd
   python --version
   python -c "import struct; print(f'{struct.calcsize(\"P\") * 8}bit')"
   ```
   → "32bit" と表示されればOK

#### オプションB: 既存の64bit版と共存

既に64bit版Pythonがインストールされている場合でも、32bit版を追加インストールできます。

1. 32bit版Pythonを別のディレクトリにインストール
   - 例: `C:\Python32\` または `C:\Python310-32\`

2. インストール時に "Add Python to PATH" の**チェックを外す**

3. 専用の起動方法を設定
   ```cmd
   # 直接パス指定で実行
   C:\Python310-32\python.exe --version

   # エイリアスを設定（PowerShell）
   Set-Alias python32 "C:\Python310-32\python.exe"
   ```

### 2.2 仮想環境の作成（推奨）

プロジェクト専用の環境を作成することを推奨します。

```cmd
# プロジェクトディレクトリに移動
cd C:\Users\mitsu\jravan_odds_fetcher

# 仮想環境を作成（32bit Pythonで実行）
C:\Python310-32\python.exe -m venv venv32

# 仮想環境をアクティベート
venv32\Scripts\activate

# Pythonのビット数を確認
python -c "import struct; print(f'{struct.calcsize(\"P\") * 8}bit')"
```

## ステップ3: 必要なライブラリのインストール

### 3.1 pywin32のインストール

```cmd
# 仮想環境がアクティブな状態で
pip install pywin32

# または
pip install -r requirements.txt
```

### 3.2 インストールの確認

```cmd
python -c "import win32com.client; print('pywin32 インストール成功')"
```

## ステップ4: 動作確認

### 4.1 基本動作テスト

```cmd
# メインスクリプトを実行
python jravan_odds_fetcher.py
```

以下のような出力が表示されれば成功：
```
============================================================
JRA-VAN リアルタイムオッズ取得スクリプト
============================================================

Python: 32bit版
JV-Link初期化完了
...
```

### 4.2 サンプルスクリプトの実行

```cmd
# 使用例スクリプトを実行
python example_usage.py
```

対話形式で様々な機能を試せます。

## トラブルシューティング

### 問題1: "初期化に失敗しました"

#### 原因と対処法

**原因1: JV-Linkがインストールされていない**
```
対処: ステップ1.2を再確認
```

**原因2: 64bit版Pythonを使用している**
```cmd
# 確認
python -c "import struct; print(struct.calcsize('P') * 8)"

# 対処: 32bit版Pythonを使用
```

**原因3: pywin32がインストールされていない**
```cmd
# 確認
python -c "import win32com.client"

# 対処
pip install pywin32
```

### 問題2: "JVInit エラー: -1"

#### 原因と対処法

**原因: JRA-VAN会員登録が完了していない**
```
対処: 会員登録を完了し、JV-Linkで認証を実施
```

JV-Linkの認証方法：
1. スタートメニューから「JV-Link設定」を起動
2. 会員IDとパスワードを入力
3. 「接続テスト」を実行
4. 成功を確認

### 問題3: "モジュール 'win32com' がありません"

```cmd
# pywin32を再インストール
pip uninstall pywin32
pip install pywin32

# post-installスクリプトを実行
python venv32/Scripts/pywin32_postinstall.py -install
```

### 問題4: データが取得できない

#### 確認ポイント

1. **レースIDの形式**
   ```python
   # 正: YYYYMMDDJJKKRR (14桁)
   race_id = "2024010105010201"

   # 誤: 数字以外が含まれる、桁数が違う
   ```

2. **開催日・時刻**
   - 競馬開催日であるか
   - オッズ発表時刻（通常10:00以降）

3. **ネットワーク接続**
   ```cmd
   ping jra-van.jp
   ```

## ステップ5: カスタマイズ

### 5.1 サービスキーの設定

デフォルトでは "UNKNOWN" を使用していますが、JRA-VANから発行されたサービスキーがある場合は変更できます。

```python
# jravan_odds_fetcher.py の main() 関数内
fetcher = JRAVANOddsFetcher(service_key="YOUR_SERVICE_KEY")
```

### 5.2 ログ出力の追加

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='jravan.log'
)
```

### 5.3 データの保存

取得したオッズデータをJSONやCSVで保存する例：

```python
import json

# オッズデータを取得
odds_data = fetcher.get_realtime_odds(race_id)

# JSONで保存
with open(f'odds_{race_id}.json', 'w', encoding='utf-8') as f:
    json.dump(odds_data, f, ensure_ascii=False, indent=2)
```

## よくある質問（FAQ）

### Q1: 64bit版Pythonでは本当に動作しませんか？

A: はい、JV-Linkは32bit COMコンポーネントのため、64bit版Pythonでは動作しません。ただし、ラッパーを作成するなどの方法で回避できる場合があります（上級者向け）。

### Q2: Macやlinuxで使用できますか？

A: JV-LinkはWindows専用です。仮想マシン（VirtualBox、VMwareなど）でWindowsを実行すれば使用可能です。

### Q3: 過去のオッズデータは取得できますか？

A: リアルタイムオッズ取得はレース当日が基本です。過去データは蓄積系データ（JVOpen）を使用する必要があります。

### Q4: 商用利用は可能ですか？

A: JRA-VANの利用規約を確認し、必要に応じて商用ライセンスを取得してください。

### Q5: 取得したデータの更新頻度は？

A: JRA-VANのサーバー更新頻度に依存します（通常1～2分間隔）。頻繁すぎるアクセスはサーバー負荷となるため、適切な間隔を空けてください。

## 次のステップ

セットアップが完了したら：

1. `example_usage.py` で各機能を試す
2. `odds_parser.py` を参考に、必要なパース処理を実装
3. 自分のアプリケーションに組み込む

## サポート

- JRA-VAN公式サポート: https://jra-van.jp/dlb/support/
- 開発者コミュニティ: https://developer.jra-van.jp/

## 関連ドキュメント

- [README.md](README.md) - 基本的な使い方
- [JV-Link仕様書](https://jra-van.jp/dlb/sdv/) - 詳細な仕様（会員限定）
