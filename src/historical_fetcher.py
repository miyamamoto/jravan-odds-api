"""
JRA-VAN 蓄積系データ取得モジュール

JVOpenを使用して過去のオッズデータを取得します。
32bit Pythonが必要です。
"""

import win32com.client
import logging
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class HistoricalOddsFetcher:
    """JRA-VANから蓄積系データを取得するクラス"""

    # データ種別コード（JVOpen用）
    DATASPEC_RACE_INFO = "RACE"     # レース情報
    DATASPEC_RESULTS = "DIFF"       # 成績・差分データ
    DATASPEC_ODDS = "NVO"           # オッズデータ（過去の速報系オッズ）
    DATASPEC_DIFF = "DIFF"          # 差分データ
    DATASPEC_SNAP = "SNAP"          # スナップショット
    DATASPEC_TOKU = "TOKU"          # 特殊データ
    DATASPEC_NVO = "NVO"            # 過去の速報系データ
    DATASPEC_0B11 = "0B11"          # 速報オッズ（単勝・複勝）
    DATASPEC_0B30 = "0B30"          # 速報オッズ（全賭式: O1〜O6全て）
    DATASPEC_0B31 = "0B31"          # 速報オッズ（単勝のみ: O1）

    # オプション
    OPTION_NORMAL = 1               # 通常データ取得
    OPTION_SETUP = 3                # セットアップ（初回）
    OPTION_SETUP_DIALOG = 4         # セットアップ（ダイアログ表示）

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
                logger.error(f"JVInit error: {ret}")
                return False

            # UI設定はJV-Link設定ツールで事前に行うため、ここでは呼び出さない
            # self.jvlink.JVSetUIProperties()

            self.is_initialized = True
            logger.info("JV-Link initialized (historical mode)")
            return True

        except Exception as e:
            logger.error(f"Initialization error: {e}")
            return False

    def setup_database(
        self,
        start_date: str,
        end_date: Optional[str] = None,
        dataspec: str = DATASPEC_RACE_INFO,
        show_dialog: bool = False
    ) -> Tuple[bool, int]:
        """
        蓄積系データベースの初回セットアップ

        Args:
            start_date: 開始日 (YYYYMMDD)
            end_date: 終了日 (YYYYMMDD、Noneの場合はstart_dateのみ)
            dataspec: データ種別
            show_dialog: セットアップダイアログを表示するか

        Returns:
            Tuple[bool, int]: (成功/失敗, ダウンロード件数)
        """
        if not self.is_initialized:
            logger.error("JV-Link not initialized")
            return False, 0

        try:
            option = self.OPTION_SETUP_DIALOG if show_dialog else self.OPTION_SETUP

            # fromtimeをYYYYMMDDhhmmss形式に変換
            fromtime = start_date + "000000" if len(start_date) == 8 else start_date

            logger.info(f"Starting database setup: {start_date} - {end_date or start_date}")
            logger.info(f"Data spec: {dataspec}, Option: {option}, FromTime: {fromtime}")

            # JVOpenでセットアップ
            ret = self.jvlink.JVOpen(dataspec, fromtime, option)

            if isinstance(ret, tuple):
                returncode = ret[0]
                readcount = ret[1] if len(ret) > 1 else 0
            else:
                returncode = ret
                readcount = 0

            if returncode < 0:
                logger.error(f"JVOpen setup error: {returncode}")
                return False, 0

            logger.info(f"Setup initiated successfully. Expected records: {readcount}")

            # ダウンロード件数がある場合、ダウンロード完了を待つ
            if isinstance(ret, tuple) and len(ret) > 2:
                downloadcount = ret[2]
                if downloadcount > 0:
                    logger.info(f"Waiting for download to complete ({downloadcount} files)...")
                    while True:
                        status = self.jvlink.JVStatus()
                        if status < 0:
                            logger.error(f"JVStatus error: {status}")
                            break
                        if status >= downloadcount:
                            logger.info("Download completed")
                            break
                        time.sleep(2)

            # データを読み込み（進捗確認用）
            total_records = 0
            while True:
                ret = self.jvlink.JVRead("", 102890, "")

                if isinstance(ret, tuple):
                    returncode = ret[0]
                else:
                    returncode = ret

                if returncode == 0:
                    break

                if returncode < 0:
                    logger.warning(f"JVRead error during setup: {returncode}")
                    break

                total_records += 1

                if total_records % 100 == 0:
                    logger.info(f"Setup progress: {total_records} records processed")

            # Close
            self.jvlink.JVClose()

            logger.info(f"Setup completed. Total records: {total_records}")
            return True, total_records

        except Exception as e:
            logger.error(f"Setup error: {e}")
            return False, 0

    def get_data(
        self,
        start_date: str,
        dataspec: str = DATASPEC_RACE_INFO,
        option: int = OPTION_NORMAL,
        max_records: Optional[int] = None
    ) -> List[Dict]:
        """
        蓄積系データを取得

        Args:
            start_date: 開始日 (YYYYMMDD)
            dataspec: データ種別
            option: オプション (1=通常, 3=セットアップ)
            max_records: 最大取得レコード数（Noneの場合は全件）

        Returns:
            List[Dict]: 取得したデータのリスト
        """
        if not self.is_initialized:
            logger.error("JV-Link not initialized")
            return []

        data_list = []

        try:
            # fromtimeをYYYYMMDDhhmmss形式に変換
            fromtime = start_date + "000000" if len(start_date) == 8 else start_date

            logger.info(f"Fetching data: date={start_date}, spec={dataspec}, fromtime={fromtime}")

            # JVOpenでデータ取得開始
            ret = self.jvlink.JVOpen(dataspec, fromtime, option)

            if isinstance(ret, tuple):
                returncode = ret[0]
                readcount = ret[1] if len(ret) > 1 else 0
            else:
                returncode = ret
                readcount = 0

            if returncode < 0:
                logger.error(f"JVOpen error: {returncode}")
                return []

            logger.info(f"JVOpen success. Expected records: {readcount}")

            # ダウンロード件数がある場合、ダウンロード完了を待つ
            if isinstance(ret, tuple) and len(ret) > 2:
                downloadcount = ret[2]
                if downloadcount > 0:
                    logger.info(f"Waiting for download to complete ({downloadcount} files)...")
                    while True:
                        status = self.jvlink.JVStatus()
                        if status < 0:
                            logger.error(f"JVStatus error: {status}")
                            break
                        if status >= downloadcount:
                            logger.info("Download completed")
                            break
                        time.sleep(2)

            # データを読み込み
            record_count = 0
            while True:
                if max_records and record_count >= max_records:
                    logger.info(f"Reached max records limit: {max_records}")
                    break

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

                # エラー
                if returncode < 0:
                    logger.warning(f"JVRead error: {returncode}")
                    break

                # データを保存
                if len(buff) >= 2:
                    record_id = buff[:2]
                    data_list.append({
                        'record_id': record_id,
                        'raw_data': buff,
                        'length': len(buff)
                    })

                record_count += 1

                if record_count % 100 == 0:
                    logger.debug(f"Progress: {record_count} records")

            # Close
            self.jvlink.JVClose()

            logger.info(f"Data fetch completed. Total records: {len(data_list)}")
            return data_list

        except Exception as e:
            logger.error(f"Data fetch error: {e}")
            return []

    def get_race_data(self, start_date: str, end_date: Optional[str] = None) -> List[Dict]:
        """
        レース情報を取得

        Args:
            start_date: 開始日 (YYYYMMDD)
            end_date: 終了日 (YYYYMMDD、Noneの場合はstart_dateのみ)

        Returns:
            List[Dict]: レース情報のリスト
        """
        return self.get_data(start_date, self.DATASPEC_RACE_INFO)

    def get_odds_data(self, start_date: str, end_date: Optional[str] = None) -> List[Dict]:
        """
        オッズデータを取得

        Args:
            start_date: 開始日 (YYYYMMDD)
            end_date: 終了日 (YYYYMMDD、Noneの場合はstart_dateのみ)

        Returns:
            List[Dict]: オッズデータのリスト
        """
        return self.get_data(start_date, self.DATASPEC_ODDS)

    def close(self):
        """リソースの解放"""
        if self.jvlink:
            try:
                self.jvlink.JVClose()
            except:
                pass

    def get_status(self) -> Dict:
        """
        フェッチャーの状態を取得

        Returns:
            Dict: 状態情報
        """
        return {
            'initialized': self.is_initialized,
            'service_key': self.service_key if self.service_key != "UNKNOWN" else "Not Set",
        }


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Historical Odds Fetcher Test")
    print("=" * 80)

    fetcher = HistoricalOddsFetcher()

    if not fetcher.initialize():
        print("Failed to initialize JV-Link")
        exit(1)

    print("\nStatus:")
    print(fetcher.get_status())

    # 最近のレース情報を取得してみる
    print("\nFetching recent race data (11/2)...")
    races = fetcher.get_race_data("20251102", max_records=10)
    print(f"Found {len(races)} records")

    if races:
        print("\nFirst race:")
        print(f"  Record ID: {races[0]['record_id']}")
        print(f"  Data length: {races[0]['length']}")
        print(f"  Preview: {races[0]['raw_data'][:100]}...")

    fetcher.close()
    print("\nTest completed")
