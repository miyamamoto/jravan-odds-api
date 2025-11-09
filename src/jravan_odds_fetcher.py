"""
JRA-VAN リアルタイムオッズ取得スクリプト

このスクリプトはJRA-VAN Data Lab のJV-Linkを使用して
競馬のリアルタイムオッズデータを取得します。

注意:
- 32bit版のPythonが必要です
- JRA-VAN Data Labの会員登録が必要です
- JV-Linkがインストールされている必要があります
"""

import win32com.client
import sys
from datetime import datetime
from typing import Optional, Dict, List

from .odds_parser import parse_odds_record


class JRAVANOddsFetcher:
    """JRA-VANからオッズデータを取得するクラス"""

    def __init__(self, service_key: str = "UNKNOWN"):
        """
        初期化

        Args:
            service_key: JRA-VANのサービスキー（このパラメータは使用されません）
                        実際のサービスキーはJV-Link設定ツールで設定します
                        JVInitには常に'UNKNOWN'を渡します
        """
        # JV-Link設定ツールでサービスキーを設定している場合、
        # JVInitには'UNKNOWN'を渡すのが正しい実装方法
        self.service_key = 'UNKNOWN'
        self.jvlink = None
        self.is_initialized = False

    def initialize(self) -> bool:
        """
        JV-Linkの初期化

        Returns:
            bool: 初期化が成功したかどうか
        """
        try:
            # JV-LinkのCOMオブジェクトを作成
            self.jvlink = win32com.client.Dispatch('JVDTLab.JVLink')

            # 初期化
            ret = self.jvlink.JVInit(self.service_key)
            if ret != 0:
                print(f"JVInit エラー: {ret}")
                return False

            # UI設定はJV-Link設定ツールで事前に行うため、ここでは呼び出さない
            # ret = self.jvlink.JVSetUIProperties()

            self.is_initialized = True
            print("JV-Link初期化完了")
            return True

        except Exception as e:
            print(f"初期化エラー: {e}")
            print("32bit版Pythonを使用していることを確認してください")
            print("JV-Linkがインストールされていることを確認してください")
            return False

    def get_realtime_odds(self, race_id: str) -> List[Dict]:
        """
        リアルタイムオッズを取得

        Args:
            race_id: レースID (例: "2024010105010211")
                    形式: YYYYMMDDJJKKRR
                    YYYY: 年, MM: 月, DD: 日
                    JJ: 場コード, KK: 回次, RR: レース番号

        Returns:
            List[Dict]: オッズデータのリスト
        """
        if not self.is_initialized:
            print("JV-Linkが初期化されていません")
            return []

        odds_data = []

        try:
            # 速報系データを開く (0B30: 全賭式オッズ - O1〜O6全て)
            dataspec = "0B30"
            ret = self.jvlink.JVRTOpen(dataspec, race_id)

            if isinstance(ret, tuple):
                returncode = ret[0]
            else:
                returncode = ret

            if returncode < 0:
                print(f"JVRTOpen エラー: {returncode}")
                return []

            print(f"データ取得開始: レースID={race_id}")

            # データを読み込み
            while True:
                ret = self.jvlink.JVRead("", 102890, "")

                if isinstance(ret, tuple):
                    returncode = ret[0]
                    buff = ret[1] if len(ret) > 1 else ""
                else:
                    returncode = ret
                    buff = ""

                # 読み込み完了
                if returncode == 0:
                    break

                # データが存在しない
                if returncode < 0:
                    print(f"JVRead エラー: {returncode}")
                    break

                # レコードIDを取得
                if len(buff) < 2:
                    continue

                rec_id = buff[0:2]

                # オッズデータ (O1-O6) の処理
                if rec_id in ['O1', 'O2', 'O3', 'O4', 'O5', 'O6']:
                    odds_info = self._parse_odds_record(rec_id, buff)
                    if odds_info:
                        odds_data.append(odds_info)
                        print(f"  取得: {rec_id} - {odds_info.get('type', 'Unknown')}")

            # クローズ
            self.jvlink.JVClose()
            print(f"データ取得完了: {len(odds_data)}件")

        except Exception as e:
            print(f"オッズ取得エラー: {e}")

        return odds_data

    def _parse_odds_record(self, rec_id: str, buff: str) -> Optional[Dict]:
        """
        オッズレコードをパース

        Args:
            rec_id: レコードID
            buff: データバッファ

        Returns:
            Optional[Dict]: パースされたオッズ情報
        """
        try:
            # odds_parser.pyのparse_odds_record関数を使用
            parsed_data = parse_odds_record(rec_id, buff)

            if parsed_data:
                # タイムスタンプを追加
                parsed_data['timestamp'] = datetime.now().isoformat()
                return parsed_data

            # パースに失敗した場合は基本情報のみ返す
            odds_info = {
                'record_id': rec_id,
                'record_type': self._get_record_type_name(rec_id),
                'raw_data': buff[:100],
                'timestamp': datetime.now().isoformat()
            }

            # タイプ名を設定
            if rec_id == 'O1':
                odds_info['type'] = '単勝・複勝'
            elif rec_id == 'O2':
                odds_info['type'] = '枠連'
            elif rec_id == 'O3':
                odds_info['type'] = '馬連'
            elif rec_id == 'O4':
                odds_info['type'] = 'ワイド'
            elif rec_id == 'O5':
                odds_info['type'] = '馬単'
            elif rec_id == 'O6':
                odds_info['type'] = '三連複・三連単'

            return odds_info

        except Exception as e:
            print(f"パースエラー ({rec_id}): {e}")
            return None

    def _get_record_type_name(self, rec_id: str) -> str:
        """レコードIDから名称を取得"""
        record_types = {
            'O1': '単勝・複勝オッズ',
            'O2': '枠連オッズ',
            'O3': '馬連オッズ',
            'O4': 'ワイドオッズ',
            'O5': '馬単オッズ',
            'O6': '三連複・三連単オッズ'
        }
        return record_types.get(rec_id, '未知')

    def get_race_info(self, date: str) -> List[Dict]:
        """
        指定日のレース情報を取得

        Args:
            date: 日付 (YYYYMMDD形式)

        Returns:
            List[Dict]: レース情報のリスト
        """
        if not self.is_initialized:
            print("JV-Linkが初期化されていません")
            return []

        race_info_list = []

        try:
            # 速報系データを開く (0B12: 速報レース詳細)
            dataspec = "0B12"
            ret = self.jvlink.JVRTOpen(dataspec, date)

            if isinstance(ret, tuple):
                returncode = ret[0]
            else:
                returncode = ret

            if returncode < 0:
                print(f"JVRTOpen エラー: {returncode}")
                return []

            print(f"レース情報取得開始: {date}")

            # データを読み込み
            while True:
                ret = self.jvlink.JVRead("", 102890, "")

                if isinstance(ret, tuple):
                    returncode = ret[0]
                    buff = ret[1] if len(ret) > 1 else ""
                else:
                    returncode = ret
                    buff = ""

                if returncode == 0:
                    break

                if returncode < 0:
                    break

                if len(buff) >= 2:
                    rec_id = buff[0:2]
                    if rec_id == 'RA':  # レース詳細
                        # RAレコードからrace_idを抽出
                        # レースキー位置: 12-27 (16バイト)
                        if len(buff) >= 28:
                            race_id = buff[11:27].strip()  # 位置12-27（0-indexed: 11-27）
                        else:
                            race_id = ''

                        race_info = {
                            'record_id': rec_id,
                            'race_id': race_id,
                            'raw_data': buff
                        }
                        race_info_list.append(race_info)

            self.jvlink.JVClose()
            print(f"レース情報取得完了: {len(race_info_list)}件")

        except Exception as e:
            print(f"レース情報取得エラー: {e}")

        return race_info_list

    def close(self):
        """リソースの解放"""
        if self.jvlink:
            try:
                self.jvlink.JVClose()
            except:
                pass
        print("JV-Link終了")


def main():
    """メイン処理"""
    print("=" * 60)
    print("JRA-VAN リアルタイムオッズ取得スクリプト")
    print("=" * 60)
    print()

    # Pythonのビット数をチェック
    import struct
    bits = struct.calcsize("P") * 8
    print(f"Python: {bits}bit版")
    if bits != 32:
        print("警告: 32bit版Pythonが必要です!")
        print("このスクリプトは正常に動作しない可能性があります")
    print()

    # フェッチャーの初期化
    fetcher = JRAVANOddsFetcher()

    if not fetcher.initialize():
        print("初期化に失敗しました")
        sys.exit(1)

    print()
    print("使用例:")
    print("1. 今日のレース情報を取得")
    print("2. 特定レースのオッズを取得")
    print()

    # 例1: 今日のレース情報を取得
    today = datetime.now().strftime("%Y%m%d")
    print(f"[例1] {today}のレース情報を取得...")
    race_info = fetcher.get_race_info(today)
    print()

    # 例2: 特定レースのオッズを取得
    # レースID形式: YYYYMMDDJJKKRR
    # 例: 2024年1月1日 東京1回1日目 1レース
    sample_race_id = f"{today}05010101"
    print(f"[例2] レースID {sample_race_id} のオッズを取得...")
    odds_data = fetcher.get_realtime_odds(sample_race_id)

    if odds_data:
        print()
        print("取得されたオッズデータ:")
        for i, odds in enumerate(odds_data[:3], 1):  # 最初の3件のみ表示
            print(f"{i}. {odds['type']}")
            print(f"   レコードID: {odds['record_id']}")
            print(f"   タイムスタンプ: {odds['timestamp']}")

    print()
    fetcher.close()
    print("処理完了")


if __name__ == "__main__":
    main()
