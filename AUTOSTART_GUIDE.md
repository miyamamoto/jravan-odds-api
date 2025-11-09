# Windows自動起動設定ガイド

JRA-VAN Odds APIサーバーをWindows起動時に自動的に起動させる設定方法です。

## 概要

Windowsのタスクスケジューラーを使用して、システム起動時にAPIサーバーを自動起動します。

### 特徴

- ✅ Windows起動時に自動的にサーバーが起動
- ✅ ログファイルに自動記録（`logs/`ディレクトリ）
- ✅ ネットワーク接続待機機能
- ✅ クラッシュ時の自動再起動（最大3回、1分間隔）
- ✅ 簡単な有効化/無効化

## セットアップ手順

### 1. 管理者権限でPowerShellを起動

スタートメニューで「PowerShell」を検索し、右クリック→「管理者として実行」

### 2. スクリプトの実行ポリシーを確認

```powershell
Get-ExecutionPolicy
```

`Restricted`の場合は以下を実行：

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. プロジェクトディレクトリに移動

```powershell
cd C:\Users\mitsu\jravan_odds_fetcher
```

### 4. セットアップスクリプトを実行

```powershell
.\setup_autostart.ps1
```

スクリプトが以下を実行します：
- タスクスケジューラーに「JRA-VAN-Odds-API-Server」タスクを登録
- 起動トリガーを「システム起動時」に設定
- 現在のユーザーアカウントで実行するよう設定

### 5. 設定確認（オプション）

```powershell
.\check_autostart.ps1
```

## 管理コマンド

### 状態確認

```powershell
.\check_autostart.ps1
```

現在の設定状態、最終実行時刻、次回実行予定などを表示します。

### 自動起動を無効化

```powershell
.\disable_autostart.ps1
```

タスクを削除せずに無効化します（再度有効化可能）。

### 自動起動を有効化

```powershell
.\enable_autostart.ps1
```

無効化されたタスクを再度有効化します。

### 設定を削除

```powershell
.\remove_autostart.ps1
```

タスクスケジューラーからタスクを完全に削除します。

### 手動でサーバーを起動

```powershell
Start-ScheduledTask -TaskName "JRA-VAN-Odds-API-Server"
```

タスクスケジューラー経由で即座にサーバーを起動します（テスト用）。

## ログファイル

サーバーの起動ログは`logs/`ディレクトリに保存されます：

```
logs/
  server_20251109_160530.log
  server_20251110_091245.log
  ...
```

ファイル名形式：`server_YYYYMMDD_HHMMSS.log`

### ログの確認

```powershell
# 最新のログファイルを表示
Get-Content (Get-ChildItem logs\*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName

# リアルタイムでログを監視
Get-Content (Get-ChildItem logs\*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName -Wait
```

## トラブルシューティング

### タスクが実行されない

1. タスクスケジューラーを開く（`taskschd.msc`）
2. 「JRA-VAN-Odds-API-Server」タスクを探す
3. タスクを右クリック→「履歴」で実行履歴を確認

### エラーコードの確認

```powershell
.\check_autostart.ps1
```

「Last Result」が0以外の場合はエラーが発生しています。

一般的なエラーコード：
- `0x1` (1): 一般的なエラー
- `0x2` (2): ファイルが見つからない
- `0x41301`: タスクが現在実行中
- `0x800710E0`: タスクがまだ実行されていない

### Python/バッチファイルのパスエラー

`start_server.bat`を開いて以下を確認：
- Pythonのパスが正しいか
- プロジェクトディレクトリへの移動が正しいか

### ネットワーク接続エラー

タスク設定で「ネットワーク接続時のみ実行」が有効です。
ネットワークに接続していることを確認してください。

## 手動でタスクを確認/編集

タスクスケジューラーGUIで直接確認・編集：

```powershell
taskschd.msc
```

タスクスケジューラーライブラリ→「JRA-VAN-Odds-API-Server」

## セキュリティ注意事項

- タスクは現在のユーザーアカウントで実行されます
- 管理者権限が必要です（タスク登録時のみ）
- サーバー自体は通常のユーザー権限で実行されます

## アンインストール

自動起動を完全に削除：

```powershell
.\remove_autostart.ps1
```

または、タスクスケジューラーから手動で削除：

```powershell
Unregister-ScheduledTask -TaskName "JRA-VAN-Odds-API-Server" -Confirm:$false
```

## FAQ

### Q: サーバーが起動しているか確認するには？

A: ブラウザで http://localhost:8000/api/health にアクセスするか、以下を実行：

```powershell
Invoke-WebRequest -Uri http://localhost:8000/api/health
```

### Q: サーバーを停止するには？

A: タスクマネージャーで`python.exe`プロセスを終了、または：

```powershell
Stop-Process -Name python -Force
```

### Q: 複数のPythonバージョンがある場合は？

A: `start_server.bat`を編集して、使用するPythonのフルパスを指定：

```batch
C:\Python310-32\python.exe run.py
```

### Q: ポート8000が既に使用中の場合は？

A: `.env`ファイルで別のポートを指定：

```
API_PORT=8001
```
