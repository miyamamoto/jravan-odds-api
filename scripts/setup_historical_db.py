"""
JRA-VAN 蓄積系データベースセットアップツール

開発モード用に過去のオッズデータをダウンロードしてキャッシュに保存します。
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

from src.historical_fetcher import HistoricalOddsFetcher
from src.odds_cache import OddsCache
from src.odds_parser import parse_odds_record
from src.config import Config

logger = logging.getLogger(__name__)


def setup_database(
    service_key: str,
    start_date: str,
    end_date: str = None,
    cache_dir: str = "./historical_cache",
    show_dialog: bool = False,
    dataspec: str = "0B31"
) -> bool:
    """
    蓄積系データベースをセットアップしてキャッシュに保存

    Args:
        service_key: JRA-VANサービスキー
        start_date: 開始日 (YYYYMMDD)
        end_date: 終了日 (YYYYMMDD、Noneの場合はstart_dateのみ)
        cache_dir: キャッシュディレクトリ
        show_dialog: セットアップダイアログを表示するか
        dataspec: データ種別

    Returns:
        bool: 成功すればTrue
    """
    print("=" * 80)
    print("JRA-VAN Historical Database Setup")
    print("=" * 80)
    print(f"Start date: {start_date}")
    print(f"End date: {end_date or start_date}")
    print(f"Data spec: {dataspec}")
    print(f"Cache directory: {cache_dir}")
    print("=" * 80)
    print()

    # フェッチャーを初期化
    fetcher = HistoricalOddsFetcher(service_key)

    if not fetcher.initialize():
        logger.error("Failed to initialize JV-Link")
        return False

    print("[OK] JV-Link initialized successfully")
    print()

    # キャッシュを初期化
    cache = OddsCache(cache_dir)
    print(f"[OK] Cache initialized at {cache_dir}")
    print()

    # キャッシュの存在確認
    dates = generate_date_range(start_date, end_date)
    cache_exists = False
    for date in dates:
        cached_races = cache.get_cached_races(date)
        if cached_races:
            cache_exists = True
            print(f"[INFO] Found existing cache for {date} ({len(cached_races)} races)")

    if cache_exists:
        print()
        print("[INFO] Cache already exists. Skipping database setup.")
        print("[INFO] If you want to re-download data, delete the cache directory first.")
        print()
        success = True
        record_count = 0
    else:
        # データベースセットアップ
        print("Starting database setup...")
        print("Note: This may take several minutes for the first time.")
        print()

        success, record_count = fetcher.setup_database(
            start_date=start_date,
            end_date=end_date,
            dataspec=dataspec,
            show_dialog=show_dialog
        )

    if not success:
        logger.error("Database setup failed")
        fetcher.close()
        return False

    print()
    print(f"[OK] Database setup completed. Total records: {record_count}")
    print()

    # データを取得してキャッシュに保存
    print("Fetching and caching odds data...")
    print()

    try:
        # 日付範囲を生成
        dates = generate_date_range(start_date, end_date)

        total_races = 0
        for date in dates:
            print(f"Processing date: {date}")

            # レース情報を取得
            race_data = fetcher.get_race_data(date)
            race_dict = {}

            for data in race_data:
                # RA (レース詳細) または H1 (馬毎レース情報) からレース情報を抽出
                if data['record_id'] in ['RA', 'H1', 'H6']:
                    race_info = parse_race_info_simple(data['raw_data'], data['record_id'])
                    if race_info:
                        race_id = race_info['race_id']
                        if race_id not in race_dict:  # 重複を避ける
                            race_dict[race_id] = race_info

            print(f"  Found {len(race_dict)} races")

            # 注意: 蓄積系データにはリアルタイムオッズは含まれないため、
            # レース情報のみをキャッシュします
            # オッズデータはリアルタイム取得時に速報系データ（JVRTOpen）から取得されます

            # レース情報のみをキャッシュに保存
            for race_id, race_info in race_dict.items():
                # 空のオッズリストでキャッシュ（レース情報のみ）
                cache.save_odds(race_id, [], race_info)
                total_races += 1

            print(f"  Cached {len(race_dict)} races (race info only)")
            print()

        print("=" * 80)
        print(f"[SUCCESS] Setup completed!")
        print(f"Total races cached: {total_races}")
        print()

        # キャッシュ統計を表示
        stats = cache.get_cache_stats()
        print("Cache statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print()

        return True

    except Exception as e:
        logger.error(f"Error during data fetch: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        fetcher.close()


def parse_race_info_simple(raw_data: str, record_id: str = 'RA') -> dict:
    """
    レース情報レコードを簡易パース

    Args:
        raw_data: 生データ
        record_id: レコードID ('RA', 'H1', etc.)

    Returns:
        dict: レース情報
    """
    try:
        if len(raw_data) < 30:
            return None

        # H1レコード（馬毎レース情報）の場合
        if record_id == 'H1' or record_id == 'H6':
            # H1レコードフォーマット:
            # H1[2] + データ区分[1] + 年月日[8] + レースID[16] + ...
            # 位置: 0-1=H1, 2=データ区分, 3-10=年月日, 11-26=レースID
            if len(raw_data) < 27:
                return None

            race_id = raw_data[11:27].strip() if len(raw_data) > 27 else ""

            return {
                'race_id': race_id,
                'race_name': '',  # H1レコードにはレース名がない
                'post_time': '',   # H1レコードには発走時刻がない
                'record_id': record_id
            }

        # RAレコード（レース詳細）の場合
        else:
            # レースID: 位置11-26
            race_id = raw_data[11:27].strip() if len(raw_data) > 27 else ""

            # 発走時刻: 位置42-45 (HHMM形式)
            post_time_raw = raw_data[42:46] if len(raw_data) > 46 else "1000"
            post_time = f"{post_time_raw[:2]}:{post_time_raw[2:]}"

            # レース名: 位置112-162
            race_name = raw_data[112:162].strip() if len(raw_data) > 162 else ""

            return {
                'race_id': race_id,
                'race_name': race_name,
                'post_time': post_time,
                'record_id': 'RA'
            }

    except Exception as e:
        logger.warning(f"Failed to parse race info ({record_id}): {e}")
        return None


def generate_date_range(start_date: str, end_date: str = None) -> list:
    """
    日付範囲を生成

    Args:
        start_date: 開始日 (YYYYMMDD)
        end_date: 終了日 (YYYYMMDD、Noneの場合はstart_dateのみ)

    Returns:
        list: 日付のリスト
    """
    if not end_date:
        return [start_date]

    try:
        start = datetime.strptime(start_date, "%Y%m%d")
        end = datetime.strptime(end_date, "%Y%m%d")

        dates = []
        current = start
        while current <= end:
            dates.append(current.strftime("%Y%m%d"))
            current += timedelta(days=1)

        return dates

    except Exception as e:
        logger.error(f"Date range generation error: {e}")
        return [start_date]


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="JRA-VAN Historical Database Setup Tool"
    )

    parser.add_argument(
        "start_date",
        help="Start date (YYYYMMDD format)"
    )

    parser.add_argument(
        "--end-date",
        help="End date (YYYYMMDD format, optional)",
        default=None
    )

    parser.add_argument(
        "--service-key",
        help="JRA-VAN service key (default: from config)",
        default=Config.JRAVAN_SERVICE_KEY
    )

    parser.add_argument(
        "--cache-dir",
        help="Cache directory (default: ./historical_cache)",
        default="./historical_cache"
    )

    parser.add_argument(
        "--dataspec",
        help="Data specification code (default: RACE for race info, DIFF for all data)",
        default="RACE"
    )

    parser.add_argument(
        "--show-dialog",
        help="Show JV-Link setup dialog",
        action="store_true"
    )

    parser.add_argument(
        "--log-level",
        help="Log level (default: INFO)",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO"
    )

    args = parser.parse_args()

    # ロギング設定
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 日付フォーマットチェック
    try:
        datetime.strptime(args.start_date, "%Y%m%d")
        if args.end_date:
            datetime.strptime(args.end_date, "%Y%m%d")
    except ValueError:
        print("Error: Invalid date format. Use YYYYMMDD format.")
        return 1

    # セットアップ実行
    success = setup_database(
        service_key=args.service_key,
        start_date=args.start_date,
        end_date=args.end_date,
        cache_dir=args.cache_dir,
        show_dialog=args.show_dialog,
        dataspec=args.dataspec
    )

    if success:
        print()
        print("=" * 80)
        print("Setup completed successfully!")
        print()
        print("You can now run the API server in development mode:")
        print("  export ENVIRONMENT=development")
        print("  python api_server.py")
        print()
        return 0
    else:
        print()
        print("=" * 80)
        print("Setup failed. Please check the logs for details.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
