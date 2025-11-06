"""
タイムマネージャー

レースの締め切り時刻管理と過去データ判定
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class TimeManager:
    """時刻管理クラス"""

    @staticmethod
    def parse_race_datetime(race_id: str, post_time: str) -> Optional[datetime]:
        """
        レースIDと発走時刻からdatetimeオブジェクトを生成

        Args:
            race_id: レースID (YYYYMMDDJJKKRR)
            post_time: 発走時刻 (HH:MM形式)

        Returns:
            Optional[datetime]: 発走時刻のdatetime
        """
        try:
            # レースIDから日付を抽出
            date_str = race_id[:8]  # YYYYMMDD
            year = int(date_str[0:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])

            # 発走時刻をパース
            time_parts = post_time.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1])

            return datetime(year, month, day, hour, minute)

        except Exception as e:
            logger.error(f"日時パースエラー: {e}")
            return None

    @staticmethod
    def calculate_deadline(post_time: datetime, margin_seconds: int = 60) -> datetime:
        """
        オッズ締め切り時刻を計算

        通常、発走時刻の少し前（デフォルト60秒前）がオッズ締め切り

        Args:
            post_time: 発走時刻
            margin_seconds: 発走前の余裕秒数

        Returns:
            datetime: 締め切り時刻
        """
        return post_time - timedelta(seconds=margin_seconds)

    @staticmethod
    def is_past_race(deadline: datetime, current_time: Optional[datetime] = None) -> bool:
        """
        過去のレースかどうか判定

        Args:
            deadline: 締め切り時刻
            current_time: 現在時刻（指定しない場合は実際の現在時刻）

        Returns:
            bool: 過去のレースならTrue
        """
        if current_time is None:
            current_time = datetime.now()

        return current_time > deadline

    @staticmethod
    def get_seconds_until_deadline(
        deadline: datetime,
        current_time: Optional[datetime] = None
    ) -> int:
        """
        締め切りまでの残り秒数を取得

        Args:
            deadline: 締め切り時刻
            current_time: 現在時刻（指定しない場合は実際の現在時刻）

        Returns:
            int: 残り秒数（負の場合は締め切り後）
        """
        if current_time is None:
            current_time = datetime.now()

        delta = deadline - current_time
        return int(delta.total_seconds())

    @staticmethod
    def get_time_before_deadline(
        deadline: datetime,
        seconds_before: int
    ) -> datetime:
        """
        締め切りn秒前の時刻を取得

        Args:
            deadline: 締め切り時刻
            seconds_before: 締め切りの何秒前か

        Returns:
            datetime: 締め切りn秒前の時刻
        """
        return deadline - timedelta(seconds=seconds_before)

    @staticmethod
    def get_deadline_info(
        race_id: str,
        post_time: str,
        current_time: Optional[datetime] = None,
        deadline_margin: int = 60
    ) -> Dict:
        """
        締め切り情報を取得

        Args:
            race_id: レースID
            post_time: 発走時刻
            current_time: 現在時刻
            deadline_margin: 締め切り余裕時間（秒）

        Returns:
            Dict: 締め切り情報
        """
        if current_time is None:
            current_time = datetime.now()

        post_datetime = TimeManager.parse_race_datetime(race_id, post_time)

        if not post_datetime:
            return {
                'error': '日時パースエラー',
                'is_past': False,
                'seconds_until_deadline': None
            }

        deadline = TimeManager.calculate_deadline(post_datetime, deadline_margin)
        is_past = TimeManager.is_past_race(deadline, current_time)
        seconds_until = TimeManager.get_seconds_until_deadline(deadline, current_time)

        return {
            'post_time': post_datetime.isoformat(),
            'deadline': deadline.isoformat(),
            'current_time': current_time.isoformat(),
            'is_past': is_past,
            'seconds_until_deadline': seconds_until,
            'status': 'past' if is_past else 'active',
            'deadline_margin_seconds': deadline_margin
        }

    @staticmethod
    def format_time_status(seconds_until: int) -> str:
        """
        締め切りまでの時間を人間が読める形式に変換

        Args:
            seconds_until: 締め切りまでの秒数

        Returns:
            str: フォーマットされた文字列
        """
        if seconds_until < 0:
            abs_seconds = abs(seconds_until)
            if abs_seconds < 60:
                return f"締め切り後 {abs_seconds}秒"
            elif abs_seconds < 3600:
                minutes = abs_seconds // 60
                return f"締め切り後 {minutes}分"
            else:
                hours = abs_seconds // 3600
                return f"締め切り後 {hours}時間"
        else:
            if seconds_until < 60:
                return f"締め切りまで {seconds_until}秒"
            elif seconds_until < 3600:
                minutes = seconds_until // 60
                seconds = seconds_until % 60
                return f"締め切りまで {minutes}分{seconds}秒"
            else:
                hours = seconds_until // 3600
                minutes = (seconds_until % 3600) // 60
                return f"締め切りまで {hours}時間{minutes}分"


class HistoricalOddsSimulator:
    """過去オッズシミュレーター"""

    @staticmethod
    def simulate_odds_at_time(
        current_odds: Dict,
        target_seconds_before: int,
        variance_factor: float = 0.1
    ) -> Dict:
        """
        指定時刻のオッズをシミュレート

        締め切り前のオッズは、現在のオッズから逆算してシミュレート

        Args:
            current_odds: 現在のオッズ
            target_seconds_before: 締め切りの何秒前のオッズか
            variance_factor: 変動係数（0.1 = ±10%）

        Returns:
            Dict: シミュレートされたオッズ
        """
        import copy
        import random

        simulated = copy.deepcopy(current_odds)

        # 時間が遡るほど変動を大きくする
        # 締め切り直前: 変動小
        # 締め切り遠い: 変動大
        time_factor = min(target_seconds_before / 3600.0, 1.0)  # 最大1時間
        variance = variance_factor * (1.0 + time_factor)

        record_id = simulated.get('record_id', '')

        # 単勝・複勝
        if record_id == 'O1':
            # 単勝オッズ
            if 'tansho' in simulated:
                for item in simulated['tansho']:
                    base_odds = item['odds']
                    variation = random.uniform(1.0 - variance, 1.0 + variance)
                    item['odds'] = round(base_odds * variation, 1)

            # 複勝オッズ
            if 'fukusho' in simulated:
                for item in simulated['fukusho']:
                    variation = random.uniform(1.0 - variance, 1.0 + variance)
                    item['odds_min'] = round(item['odds_min'] * variation, 1)
                    item['odds_max'] = round(item['odds_max'] * variation, 1)

        # その他のオッズ
        elif 'combinations' in simulated:
            for item in simulated['combinations']:
                variation = random.uniform(1.0 - variance, 1.0 + variance)
                if 'odds' in item:
                    item['odds'] = round(item['odds'] * variation, 1)
                if 'odds_min' in item:
                    item['odds_min'] = round(item['odds_min'] * variation, 1)
                if 'odds_max' in item:
                    item['odds_max'] = round(item['odds_max'] * variation, 1)

        # メタ情報を追加
        simulated['simulated'] = True
        simulated['target_seconds_before_deadline'] = target_seconds_before
        simulated['variance_applied'] = variance

        return simulated


if __name__ == "__main__":
    # テスト
    import json

    tm = TimeManager()

    # テスト1: 締め切り情報取得
    print("=== 締め切り情報テスト ===")
    race_id = "2024010105010101"
    post_time = "10:00"

    info = tm.get_deadline_info(race_id, post_time)
    print(json.dumps(info, indent=2, ensure_ascii=False))

    # テスト2: 時刻表示
    print("\n=== 時刻表示テスト ===")
    test_seconds = [30, 120, 3600, -60, -3600]
    for seconds in test_seconds:
        status = tm.format_time_status(seconds)
        print(f"{seconds}秒 → {status}")

    # テスト3: オッズシミュレート
    print("\n=== オッズシミュレーション ===")
    sample_odds = {
        'record_id': 'O1',
        'tansho': [
            {'umaban': 1, 'odds': 2.5},
            {'umaban': 2, 'odds': 5.0}
        ]
    }

    simulator = HistoricalOddsSimulator()
    simulated = simulator.simulate_odds_at_time(sample_odds, 300)  # 5分前

    print("元のオッズ:")
    print(json.dumps(sample_odds, indent=2, ensure_ascii=False))
    print("\n5分前のシミュレート:")
    print(json.dumps(simulated, indent=2, ensure_ascii=False))
