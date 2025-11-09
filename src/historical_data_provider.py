"""
蓄積系データプロバイダー

開発モード用のデータプロバイダー
過去のオッズデータをキャッシュから提供し、締め切り前n秒のデータをシミュレート
"""

import logging
from typing import Dict, List, Optional
from pathlib import Path

from .historical_fetcher import HistoricalOddsFetcher
from .odds_cache import OddsCache
from .time_manager import TimeManager, HistoricalOddsSimulator
from .odds_parser import parse_odds_record

logger = logging.getLogger(__name__)


class HistoricalDataProvider:
    """開発モード用のデータプロバイダー"""

    def __init__(
        self,
        cache_dir: str = "./historical_cache",
        service_key: str = "UNKNOWN",
        auto_fetch: bool = False
    ):
        """
        初期化

        Args:
            cache_dir: キャッシュディレクトリ
            service_key: JRA-VANサービスキー
            auto_fetch: キャッシュがない場合に自動取得するか
        """
        self.cache = OddsCache(cache_dir)
        self.fetcher = None
        self.service_key = service_key
        self.auto_fetch = auto_fetch
        self.fetcher_initialized = False

    def _ensure_fetcher(self) -> bool:
        """フェッチャーの初期化を確保"""
        if self.fetcher_initialized:
            return True

        if not self.auto_fetch:
            return False

        try:
            self.fetcher = HistoricalOddsFetcher(self.service_key)
            self.fetcher_initialized = self.fetcher.initialize()
            return self.fetcher_initialized
        except Exception as e:
            logger.error(f"Failed to initialize fetcher: {e}")
            return False

    def get_race_info(self, date: str) -> List[Dict]:
        """
        指定日のレース情報を取得

        Args:
            date: 日付 (YYYYMMDD)

        Returns:
            List[Dict]: レース情報のリスト
        """
        logger.info(f"Getting race info for date: {date}")

        # キャッシュから取得を試みる
        cached_races = self.cache.get_cached_races(date)

        if cached_races:
            logger.info(f"Found {len(cached_races)} races in cache")
            races = []
            for race_id in cached_races:
                cached_data = self.cache.load_odds(race_id)
                if cached_data and cached_data.get('race_info'):
                    race_info = cached_data['race_info']
                    race_info['race_id'] = race_id
                    races.append(race_info)
            return races

        # キャッシュにない場合、フェッチャーで取得
        if self.auto_fetch and self._ensure_fetcher():
            logger.info(f"Cache miss for {date}, fetching race data from JV-Link")

            # レース情報を取得
            raw_data = self.fetcher.get_race_data(date)
            races = []
            race_dict = {}

            # レコードIDの統計を取る
            record_id_counts = {}
            for data in raw_data:
                rid = data['record_id']
                record_id_counts[rid] = record_id_counts.get(rid, 0) + 1
                # レースレコードを処理（RA, H1, H6, JG）
                if data['record_id'] in ['RA', 'H1', 'H6', 'JG']:
                    race_info = self._parse_race_info(data['raw_data'], data['record_id'])
                    if race_info:
                        race_id = race_info.get('race_id')
                        if race_id and race_id not in race_dict:  # 重複を避ける
                            races.append(race_info)
                            race_dict[race_id] = race_info

            logger.info(f"Record ID counts: {record_id_counts}")
            logger.info(f"Parsed {len(races)} unique races")

            # JGレコードからオッズデータも抽出してキャッシュに保存
            if races:
                logger.info(f"Extracting odds data from {len(raw_data)} JG records")

                # レースIDごとにグループ化（JGレコードから）
                odds_by_race = {}
                for data in raw_data:
                    if data['record_id'] == 'JG':
                        parsed = parse_odds_record(data['record_id'], data['raw_data'])
                        if parsed and not parsed.get('error'):
                            race_id = parsed.get('race_id', '')
                            if race_id:
                                if race_id not in odds_by_race:
                                    odds_by_race[race_id] = []
                                odds_by_race[race_id].append(parsed)

                # キャッシュに保存
                for race_id, odds_list in odds_by_race.items():
                    race_info = race_dict.get(race_id, {})
                    # post_timeをrace_infoから取得
                    if not race_info.get('post_time') and odds_list:
                        race_info['post_time'] = odds_list[0].get('post_time', '10:00')
                    self.cache.save_odds(race_id, odds_list, race_info)
                    logger.info(f"Cached {len(odds_list)} odds records for race {race_id}")

            return races

        logger.warning(f"No race data available for {date} (auto_fetch={self.auto_fetch})")
        return []

    def _parse_race_info(self, raw_data: str, record_id: str = 'RA') -> Optional[Dict]:
        """
        レース情報レコードをパース（簡易版）

        Args:
            raw_data: 生データ
            record_id: レコードID ('RA', 'H1', 'JG', etc.)

        Returns:
            Optional[Dict]: パースされたレース情報
        """
        try:
            if len(raw_data) < 30:
                return None

            # JGレコード（時系列オッズ情報）の場合
            if record_id == 'JG':
                # JGレコードフォーマット:
                # JG[2] + データ区分[1] + 年月日[8] + レースID[16] + ...
                # 位置: 0-1=JG, 2=データ区分, 3-10=年月日, 11-26=レースID
                if len(raw_data) < 27:
                    return None

                race_id = raw_data[11:27].strip() if len(raw_data) > 27 else ""

                return {
                    'race_id': race_id,
                    'race_name': '',  # JGレコードにはレース名がない
                    'post_time': '10:00',  # デフォルト値
                    'record_id': record_id,
                    'raw_data': raw_data
                }

            # H1レコード（馬毎レース情報）の場合
            elif record_id in ['H1', 'H6']:
                # H1レコードフォーマット:
                # H1[2] + データ区分[1] + 年月日[8] + レースID[16] + ...
                # 位置: 0-1=H1, 2=データ区分, 3-10=年月日, 11-26=レースID
                if len(raw_data) < 27:
                    return None

                race_id = raw_data[11:27].strip() if len(raw_data) > 27 else ""

                return {
                    'race_id': race_id,
                    'race_name': '',  # H1レコードにはレース名がない
                    'record_id': record_id,
                    'raw_data': raw_data
                }

            # RAレコード（レース詳細）の場合
            else:
                if len(raw_data) < 50:
                    return None

                # レースID: 位置11-26
                race_id = raw_data[11:27].strip() if len(raw_data) > 27 else ""

                # レース名: 位置112-162（推定）
                race_name = raw_data[112:162].strip() if len(raw_data) > 162 else ""

                return {
                    'race_id': race_id,
                    'race_name': race_name,
                    'record_id': 'RA',
                    'raw_data': raw_data
                }

        except Exception as e:
            logger.error(f"Failed to parse race info ({record_id}): {e}")
            return None

    def get_realtime_odds(
        self,
        race_id: str,
        seconds_before_deadline: Optional[int] = None
    ) -> Dict:
        """
        過去のオッズデータを取得

        Args:
            race_id: レースID
            seconds_before_deadline: 締め切り前の秒数（Noneの場合は最新）

        Returns:
            Dict: オッズデータと締め切り情報
        """
        logger.info(f"Getting odds for race: {race_id}, seconds_before: {seconds_before_deadline}")

        # キャッシュから取得
        cached_data = self.cache.load_odds(race_id)

        if not cached_data:
            # キャッシュにない場合
            if self.auto_fetch and self._ensure_fetcher():
                logger.info("Cache miss, fetching from JV-Link")
                cached_data = self._fetch_and_cache_odds(race_id)
            else:
                logger.warning(f"No cached data for race: {race_id}")
                return {
                    'odds': [],
                    'error': 'No cached data available',
                    'is_past_data': True
                }

        # オッズデータを取得
        odds_data = cached_data.get('odds', [])
        race_info = cached_data.get('race_info', {})

        # 締め切り情報を取得
        post_time = race_info.get('post_time', '10:00')
        deadline_info = TimeManager.get_deadline_info(race_id, post_time)

        # seconds_before_deadlineが指定されている場合
        if seconds_before_deadline is not None and seconds_before_deadline > 0:
            # 時系列データがある場合
            if cached_data.get('data_type') == 'time_series':
                odds_timeline = cached_data.get('odds_timeline', [])
                simulator = HistoricalOddsSimulator()
                target_odds = simulator.get_odds_at_time(odds_timeline, seconds_before_deadline)

                if target_odds:
                    odds_data = target_odds
                else:
                    # 時系列データから取得できない場合、シミュレート
                    odds_data = [
                        simulator.simulate_odds_at_time(odds, seconds_before_deadline)
                        for odds in odds_data
                    ]
            else:
                # 通常のキャッシュデータの場合、シミュレート
                simulator = HistoricalOddsSimulator()
                odds_data = [
                    simulator.simulate_odds_at_time(odds, seconds_before_deadline)
                    for odds in odds_data
                ]

            return {
                'odds': odds_data,
                'deadline_info': deadline_info,
                'is_past_data': True,
                'data_source': 'historical_cache',
                'past_data_note': f'これは過去のデータです（締め切り{seconds_before_deadline}秒前のシミュレーション）',
                'seconds_before_deadline': seconds_before_deadline,
                'time_status': TimeManager.format_time_status(-seconds_before_deadline)
            }

        # 指定なしの場合は最新（締め切り直前）のデータ
        return {
            'odds': odds_data,
            'deadline_info': deadline_info,
            'is_past_data': True,
            'data_source': 'historical_cache',
            'past_data_note': 'これは過去のデータです（キャッシュから取得）',
            'time_status': deadline_info.get('status', 'past')
        }

    def _fetch_and_cache_odds(self, race_id: str) -> Optional[Dict]:
        """
        JV-Linkからオッズを取得してキャッシュ

        Args:
            race_id: レースID

        Returns:
            Optional[Dict]: 取得したデータ
        """
        try:
            # 日付を抽出
            date = race_id[:8]

            # オッズデータを取得
            raw_data = self.fetcher.get_odds_data(date)

            if not raw_data:
                logger.warning(f"No odds data fetched for {race_id}")
                return None

            # パースして保存
            odds_list = []
            for data in raw_data:
                parsed = parse_odds_record(data['record_id'], data['raw_data'])
                if parsed:
                    odds_list.append(parsed)

            if odds_list:
                # キャッシュに保存
                self.cache.save_odds(race_id, odds_list)

                return {
                    'race_id': race_id,
                    'odds': odds_list,
                    'race_info': {}
                }

            return None

        except Exception as e:
            logger.error(f"Failed to fetch and cache odds: {e}")
            return None

    def refresh_cache(self, race_id: str) -> bool:
        """
        特定レースのキャッシュを更新

        Args:
            race_id: レースID

        Returns:
            bool: 成功すればTrue
        """
        if not self._ensure_fetcher():
            return False

        result = self._fetch_and_cache_odds(race_id)
        return result is not None

    def get_race_detail(self, race_id: str) -> Optional[Dict]:
        """
        レース詳細情報を取得

        Args:
            race_id: レースID

        Returns:
            Optional[Dict]: レース詳細
        """
        cached_data = self.cache.load_odds(race_id)

        if cached_data:
            return {
                'race_id': race_id,
                'race_info': cached_data.get('race_info', {}),
                'odds_count': len(cached_data.get('odds', [])),
                'cached_at': cached_data.get('cached_at'),
                'data_source': 'historical_cache'
            }

        return None

    def close(self):
        """リソースの解放"""
        if self.fetcher:
            self.fetcher.close()

    def get_status(self) -> Dict:
        """
        プロバイダーの状態を取得

        Returns:
            Dict: 状態情報
        """
        cache_stats = self.cache.get_cache_stats()

        return {
            'provider_type': 'historical',
            'fetcher_initialized': self.fetcher_initialized,
            'auto_fetch': self.auto_fetch,
            'cache_stats': cache_stats
        }


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Historical Data Provider Test")
    print("=" * 80)

    provider = HistoricalDataProvider(cache_dir="./test_historical_cache")

    print("\nProvider status:")
    status = provider.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")

    # レース情報取得テスト
    print("\nGetting race info for 20251102:")
    races = provider.get_race_info("20251102")
    print(f"Found {len(races)} races")

    provider.close()
    print("\nTest completed")
