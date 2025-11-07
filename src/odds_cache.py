"""
オッズデータキャッシュ管理モジュール

過去のオッズデータをJSONファイルとしてキャッシュします。
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class OddsCache:
    """オッズデータのキャッシュ管理クラス"""

    def __init__(self, cache_dir: str = "./historical_cache"):
        """
        初期化

        Args:
            cache_dir: キャッシュディレクトリのパス
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # インデックスファイルのパス
        self.index_file = self.cache_dir / "cache_index.json"
        self.index = self._load_index()

    def _load_index(self) -> Dict:
        """
        キャッシュインデックスを読み込み

        Returns:
            Dict: インデックスデータ
        """
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load cache index: {e}")
                return {}
        return {}

    def _save_index(self):
        """キャッシュインデックスを保存"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")

    def _get_cache_path(self, race_id: str) -> Path:
        """
        レースIDからキャッシュファイルのパスを取得

        Args:
            race_id: レースID (YYYYMMDDJJKKRR)

        Returns:
            Path: キャッシュファイルのパス
        """
        # 日付でディレクトリを分ける
        date = race_id[:8]
        date_dir = self.cache_dir / date
        date_dir.mkdir(parents=True, exist_ok=True)

        return date_dir / f"{race_id}.json"

    def save_odds(
        self,
        race_id: str,
        odds_data: List[Dict],
        race_info: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ):
        """
        オッズデータをキャッシュに保存

        Args:
            race_id: レースID
            odds_data: オッズデータのリスト
            race_info: レース情報（オプション）
            metadata: メタデータ（オプション）
        """
        try:
            cache_path = self._get_cache_path(race_id)

            data = {
                'race_id': race_id,
                'cached_at': datetime.now().isoformat(),
                'race_info': race_info or {},
                'metadata': metadata or {},
                'odds': odds_data
            }

            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # インデックスを更新
            self.index[race_id] = {
                'cached_at': data['cached_at'],
                'file_path': str(cache_path),
                'odds_count': len(odds_data)
            }
            self._save_index()

            logger.info(f"Odds cached: {race_id} ({len(odds_data)} records)")

        except Exception as e:
            logger.error(f"Failed to save odds cache: {e}")

    def load_odds(self, race_id: str) -> Optional[Dict]:
        """
        キャッシュからオッズデータを読み込み

        Args:
            race_id: レースID

        Returns:
            Optional[Dict]: キャッシュされたデータ、存在しない場合はNone
        """
        try:
            cache_path = self._get_cache_path(race_id)

            if not cache_path.exists():
                logger.debug(f"Cache not found: {race_id}")
                return None

            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logger.info(f"Odds loaded from cache: {race_id}")
            return data

        except Exception as e:
            logger.error(f"Failed to load odds cache: {e}")
            return None

    def has_cache(self, race_id: str) -> bool:
        """
        指定レースのキャッシュが存在するか確認

        Args:
            race_id: レースID

        Returns:
            bool: キャッシュが存在すればTrue
        """
        return self._get_cache_path(race_id).exists()

    def delete_cache(self, race_id: str) -> bool:
        """
        キャッシュを削除

        Args:
            race_id: レースID

        Returns:
            bool: 削除に成功すればTrue
        """
        try:
            cache_path = self._get_cache_path(race_id)

            if cache_path.exists():
                cache_path.unlink()

                # インデックスからも削除
                if race_id in self.index:
                    del self.index[race_id]
                    self._save_index()

                logger.info(f"Cache deleted: {race_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to delete cache: {e}")
            return False

    def save_time_series_odds(
        self,
        race_id: str,
        time_series_data: List[Dict],
        race_info: Optional[Dict] = None
    ):
        """
        時系列オッズデータを保存

        Args:
            race_id: レースID
            time_series_data: 時系列オッズデータ
            race_info: レース情報（オプション）
        """
        try:
            cache_path = self._get_cache_path(race_id)

            data = {
                'race_id': race_id,
                'cached_at': datetime.now().isoformat(),
                'data_type': 'time_series',
                'race_info': race_info or {},
                'odds_timeline': time_series_data
            }

            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # インデックスを更新
            self.index[race_id] = {
                'cached_at': data['cached_at'],
                'file_path': str(cache_path),
                'data_type': 'time_series',
                'timeline_count': len(time_series_data)
            }
            self._save_index()

            logger.info(f"Time-series odds cached: {race_id} ({len(time_series_data)} points)")

        except Exception as e:
            logger.error(f"Failed to save time-series odds cache: {e}")

    def get_cached_races(self, date: Optional[str] = None) -> List[str]:
        """
        キャッシュされているレースIDのリストを取得

        Args:
            date: 日付（YYYYMMDD形式、Noneの場合は全レース）

        Returns:
            List[str]: レースIDのリスト
        """
        if date:
            return [race_id for race_id in self.index.keys() if race_id.startswith(date)]
        return list(self.index.keys())

    def get_cache_stats(self) -> Dict:
        """
        キャッシュの統計情報を取得

        Returns:
            Dict: 統計情報
        """
        total_races = len(self.index)
        dates = set(race_id[:8] for race_id in self.index.keys())

        return {
            'total_races': total_races,
            'total_dates': len(dates),
            'cache_dir': str(self.cache_dir),
            'index_file': str(self.index_file)
        }

    def clear_old_cache(self, days: int = 365):
        """
        古いキャッシュを削除

        Args:
            days: 保持する日数
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0

        for race_id, info in list(self.index.items()):
            try:
                cached_at = datetime.fromisoformat(info['cached_at'])
                if cached_at < cutoff_date:
                    if self.delete_cache(race_id):
                        deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to check cache age for {race_id}: {e}")

        logger.info(f"Cleared {deleted_count} old cache entries")


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Odds Cache Test")
    print("=" * 80)

    cache = OddsCache("./test_cache")

    # テストデータを保存
    test_race_id = "20251102050411"
    test_odds = [
        {'record_id': 'O1', 'type': 'tansho', 'data': 'test'},
        {'record_id': 'O2', 'type': 'wakuren', 'data': 'test'}
    ]
    test_race_info = {
        'race_name': 'Test Race',
        'post_time': '15:40'
    }

    print(f"\nSaving test data for race: {test_race_id}")
    cache.save_odds(test_race_id, test_odds, test_race_info)

    # キャッシュの確認
    print(f"\nCache exists: {cache.has_cache(test_race_id)}")

    # データを読み込み
    print("\nLoading cached data:")
    loaded_data = cache.load_odds(test_race_id)
    if loaded_data:
        print(f"  Race ID: {loaded_data['race_id']}")
        print(f"  Odds count: {len(loaded_data['odds'])}")
        print(f"  Race name: {loaded_data['race_info'].get('race_name')}")

    # 統計情報
    print("\nCache stats:")
    stats = cache.get_cache_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\nTest completed")
