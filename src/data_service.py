"""
データサービス層

本番環境とモック環境を統一的に扱うサービス層
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from .config import Config
from .mock_provider import get_mock_provider
from .time_manager import TimeManager, HistoricalOddsSimulator
from .historical_data_provider import HistoricalDataProvider

# 本番環境ではjravan_odds_fetcherをインポート
try:
    from .jravan_odds_fetcher import JRAVANOddsFetcher
    JRAVAN_AVAILABLE = True
except ImportError:
    JRAVAN_AVAILABLE = False
    logging.warning("jravan_odds_fetcherがインポートできません。モックモードのみ使用可能です。")


logger = logging.getLogger(__name__)


class DataService:
    """データサービスクラス"""

    def __init__(self):
        """初期化 - 両方のプロバイダーを初期化（利用可能な場合）"""
        self.fetcher = None
        self.mock_provider = None
        self.historical_provider = None

        # 蓄積系データプロバイダーの初期化（常に試みる）
        if Config.ENABLE_HISTORICAL_DATA:
            try:
                logger.info("蓄積系データプロバイダーを初期化します")
                self.historical_provider = HistoricalDataProvider(
                    cache_dir=Config.HISTORICAL_CACHE_DIR,
                    service_key=Config.JRAVAN_SERVICE_KEY,
                    auto_fetch=Config.HISTORICAL_AUTO_FETCH
                )
                logger.info(f"蓄積系データプロバイダー初期化成功: {self.historical_provider.get_status()}")
            except Exception as e:
                logger.warning(f"蓄積系データプロバイダー初期化失敗: {e}")

        # リアルタイムプロバイダーの初期化（JV-Link利用可能時のみ）
        if JRAVAN_AVAILABLE:
            try:
                logger.info("リアルタイムデータプロバイダーを初期化します")
                self._initialize_jravan()
            except Exception as e:
                logger.warning(f"リアルタイムデータプロバイダー初期化失敗: {e}")

        # モックプロバイダーの初期化（開発用）
        if Config.USE_MOCK_DATA:
            logger.info("モックプロバイダーを初期化します")
            self.mock_provider = get_mock_provider(Config.MOCK_DATA_FILE)

        # 初期化状態をログ出力
        logger.info(f"データサービス初期化完了 - Historical: {self.historical_provider is not None}, "
                   f"Realtime: {self.fetcher is not None}, Mock: {self.mock_provider is not None}")

    def _initialize_jravan(self) -> bool:
        """JRA-VANを初期化"""
        try:
            self.fetcher = JRAVANOddsFetcher(Config.JRAVAN_SERVICE_KEY)
            if not self.fetcher.initialize():
                logger.error("JRA-VAN初期化に失敗しました")
                return False
            logger.info("JRA-VAN初期化成功")
            return True
        except Exception as e:
            logger.error(f"JRA-VAN初期化エラー: {e}")
            return False

    def _resolve_data_source(self, data_source: str) -> str:
        """
        データソースを解決

        Args:
            data_source: 指定されたデータソース ('auto', 'historical', 'realtime', 'mock')

        Returns:
            str: 解決されたデータソース
        """
        if data_source != 'auto':
            return data_source

        # autoの場合、環境変数とデフォルト設定から決定
        default = Config.DEFAULT_DATA_SOURCE

        if default == 'auto':
            # auto設定の場合、環境に応じて自動選択
            if Config.is_development():
                # 開発環境: 蓄積系データ優先、なければモック
                if self.historical_provider:
                    return 'historical'
                elif self.mock_provider:
                    return 'mock'
                elif self.fetcher:
                    return 'realtime'
            else:
                # 本番環境: リアルタイム優先
                if self.fetcher:
                    return 'realtime'
                elif self.historical_provider:
                    return 'historical'
        else:
            return default

        # フォールバック
        if self.historical_provider:
            return 'historical'
        elif self.fetcher:
            return 'realtime'
        elif self.mock_provider:
            return 'mock'

        raise RuntimeError("利用可能なデータプロバイダーがありません")

    def get_race_info(self, date: str, data_source: str = 'auto') -> List[Dict]:
        """
        指定日のレース情報を取得

        Args:
            date: 日付 (YYYYMMDD形式)
            data_source: データソース ('auto', 'historical', 'realtime')

        Returns:
            List[Dict]: レース情報のリスト
        """
        try:
            # データソースの決定
            source = self._resolve_data_source(data_source)

            if source == 'historical':
                if not self.historical_provider:
                    raise RuntimeError("蓄積系データプロバイダーが初期化されていません")
                return self.historical_provider.get_race_info(date)
            elif source == 'realtime':
                if not self.fetcher:
                    raise RuntimeError("リアルタイムデータプロバイダーが初期化されていません")
                return self.fetcher.get_race_info(date)
            elif source == 'mock':
                if not self.mock_provider:
                    raise RuntimeError("モックプロバイダーが初期化されていません")
                return self.mock_provider.get_race_info(date)
            else:
                raise ValueError(f"不正なデータソース: {source}")

        except Exception as e:
            logger.error(f"レース情報取得エラー: {e}")
            return []

    def get_realtime_odds(
        self,
        race_id: str,
        seconds_before_deadline: Optional[int] = None,
        data_source: str = 'auto'
    ) -> Dict:
        """
        リアルタイムオッズを取得

        Args:
            race_id: レースID
            seconds_before_deadline: 締め切りの何秒前のデータを取得するか（Noneの場合は最新）
            data_source: データソース ('auto', 'historical', 'realtime', 'mock')

        Returns:
            Dict: オッズデータと締め切り情報
                - odds: オッズデータのリスト
                - deadline_info: 締め切り情報
                - is_past_data: 過去データフラグ
                - seconds_before_deadline: 指定された秒数
        """
        try:
            # データソースの決定
            source = self._resolve_data_source(data_source)

            # 蓄積系データの場合、historical_providerに委譲
            if source == 'historical':
                if not self.historical_provider:
                    raise RuntimeError("蓄積系データプロバイダーが初期化されていません")
                return self.historical_provider.get_realtime_odds(
                    race_id,
                    seconds_before_deadline
                )

            # post_timeを取得（無限再帰を避けるためデフォルト値を使用）
            post_time = '10:00'

            # mockモードの場合はpost_timeを取得
            if source == 'mock' and self.mock_provider:
                race_detail = self.mock_provider.get_race_detail(race_id)
                if race_detail:
                    post_time = race_detail.get('post_time', '10:00')

            # 締め切り情報を取得
            deadline_info = TimeManager.get_deadline_info(race_id, post_time)
            is_past = deadline_info.get('is_past', False)

            # オッズデータを取得
            if source == 'mock':
                if not self.mock_provider:
                    raise RuntimeError("モックプロバイダーが初期化されていません")
                odds_data = self.mock_provider.get_realtime_odds(race_id)
            elif source == 'realtime':
                if not self.fetcher:
                    raise RuntimeError("リアルタイムデータプロバイダーが初期化されていません")
                odds_data = self.fetcher.get_realtime_odds(race_id)
            else:
                raise ValueError(f"不正なデータソース: {source}")

            # n秒前のデータをシミュレート
            if seconds_before_deadline is not None and seconds_before_deadline > 0:
                simulator = HistoricalOddsSimulator()
                odds_data = [
                    simulator.simulate_odds_at_time(odds, seconds_before_deadline)
                    for odds in odds_data
                ]

                # 過去データフラグを明示
                return {
                    'odds': odds_data,
                    'deadline_info': deadline_info,
                    'is_past_data': True,
                    'past_data_note': f'これは過去のデータです（締め切り{seconds_before_deadline}秒前のシミュレーション）',
                    'seconds_before_deadline': seconds_before_deadline,
                    'time_status': TimeManager.format_time_status(-seconds_before_deadline)
                }

            # 現在のデータ
            result = {
                'odds': odds_data,
                'deadline_info': deadline_info,
                'is_past_data': is_past,
                'seconds_before_deadline': None
            }

            # 過去データの場合は明示
            if is_past:
                seconds_after = abs(deadline_info.get('seconds_until_deadline', 0))
                result['past_data_note'] = f'これは過去のデータです（締め切り後{seconds_after}秒経過）'
                result['time_status'] = TimeManager.format_time_status(
                    deadline_info.get('seconds_until_deadline', 0)
                )

            return result

        except Exception as e:
            logger.error(f"オッズ取得エラー: {e}")
            return {
                'odds': [],
                'error': str(e),
                'is_past_data': False
            }

    def get_race_detail(self, race_id: str, data_source: str = 'auto') -> Optional[Dict]:
        """
        レース詳細情報を取得

        Args:
            race_id: レースID
            data_source: データソース ('auto', 'historical', 'realtime', 'mock')

        Returns:
            Optional[Dict]: レース詳細情報
        """
        try:
            # データソースの決定
            source = self._resolve_data_source(data_source)

            if source == 'historical':
                if not self.historical_provider:
                    raise RuntimeError("蓄積系データプロバイダーが初期化されていません")
                return self.historical_provider.get_race_detail(race_id)
            elif source == 'mock':
                if not self.mock_provider:
                    raise RuntimeError("モックプロバイダーが初期化されていません")
                return self.mock_provider.get_race_detail(race_id)
            elif source == 'realtime':
                # 本番環境の場合、オッズデータから情報を抽出
                odds_data = self.get_realtime_odds(race_id, data_source=source)
                if odds_data:
                    return {
                        'race_id': race_id,
                        'odds_count': len(odds_data),
                        'odds': odds_data
                    }
                return None
            else:
                raise ValueError(f"不正なデータソース: {source}")
        except Exception as e:
            logger.error(f"レース詳細取得エラー: {e}")
            return None

    def save_odds_data(self, race_id: str, odds_data: List[Dict]):
        """
        オッズデータを保存

        Args:
            race_id: レースID
            odds_data: オッズデータ
        """
        if not Config.ENABLE_DATA_SAVE:
            return

        try:
            data_dir = Path(Config.DATA_DIR)
            data_dir.mkdir(parents=True, exist_ok=True)

            # 日付ごとにディレクトリを分ける
            date = race_id[:8]
            date_dir = data_dir / date
            date_dir.mkdir(parents=True, exist_ok=True)

            # タイムスタンプ付きで保存
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{race_id}_{timestamp}.json"
            filepath = date_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'race_id': race_id,
                    'timestamp': datetime.now().isoformat(),
                    'odds': odds_data
                }, f, ensure_ascii=False, indent=2)

            logger.info(f"オッズデータを保存しました: {filepath}")

        except Exception as e:
            logger.error(f"オッズデータ保存エラー: {e}")

    def load_saved_odds(self, race_id: str, timestamp: Optional[str] = None) -> Optional[List[Dict]]:
        """
        保存されたオッズデータを読み込み

        Args:
            race_id: レースID
            timestamp: タイムスタンプ（指定しない場合は最新）

        Returns:
            Optional[List[Dict]]: オッズデータ
        """
        try:
            data_dir = Path(Config.DATA_DIR)
            date = race_id[:8]
            date_dir = data_dir / date

            if not date_dir.exists():
                return None

            # 該当レースのファイルを検索
            pattern = f"{race_id}_*.json"
            files = sorted(date_dir.glob(pattern), reverse=True)

            if not files:
                return None

            # 最新のファイルを読み込み
            with open(files[0], 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('odds', [])

        except Exception as e:
            logger.error(f"保存データ読み込みエラー: {e}")
            return None

    def close(self):
        """リソースの解放"""
        if self.fetcher:
            try:
                self.fetcher.close()
            except:
                pass
        if self.historical_provider:
            try:
                self.historical_provider.close()
            except:
                pass

    def get_status(self) -> Dict:
        """サービスの状態を取得"""
        status = {
            'jravan_available': JRAVAN_AVAILABLE,
            'data_save_enabled': Config.ENABLE_DATA_SAVE,
            'cache_enabled': Config.ENABLE_CACHE,
            'default_data_source': Config.DEFAULT_DATA_SOURCE,
            'environment': Config.ENVIRONMENT
        }

        # 各プロバイダーの初期化状態
        status['providers'] = {
            'historical': self.historical_provider is not None,
            'realtime': self.fetcher is not None,
            'mock': self.mock_provider is not None
        }

        # 蓄積系データプロバイダーのステータス
        if self.historical_provider:
            status['historical_provider_status'] = self.historical_provider.get_status()

        return status


# グローバルインスタンス
_data_service = None


def get_data_service() -> DataService:
    """
    データサービスのシングルトンインスタンスを取得

    Returns:
        DataService: データサービス
    """
    global _data_service
    if _data_service is None:
        _data_service = DataService()
    return _data_service


if __name__ == "__main__":
    # テスト
    logging.basicConfig(level=logging.INFO)

    service = DataService()

    print("サービス状態:")
    print(json.dumps(service.get_status(), indent=2, ensure_ascii=False))

    print("\nレース情報取得テスト:")
    races = service.get_race_info("20240101")
    print(f"取得件数: {len(races)}")

    if races:
        race_id = races[0].get('race_id')
        print(f"\nオッズ取得テスト: {race_id}")
        odds = service.get_realtime_odds(race_id)
        print(f"オッズ件数: {len(odds)}")

    service.close()
