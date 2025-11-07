"""
モックデータプロバイダー

開発環境で使用するモックデータを提供
"""

import json
import random
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path


class MockDataProvider:
    """モックデータプロバイダークラス"""

    def __init__(self, mock_data_file: str = "./mock_data/sample_odds.json"):
        """
        初期化

        Args:
            mock_data_file: モックデータファイルのパス
        """
        self.mock_data_file = mock_data_file
        self.mock_data = self._load_mock_data()

    def _load_mock_data(self) -> Dict:
        """モックデータを読み込み"""
        try:
            filepath = Path(self.mock_data_file)
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"モックデータファイルが見つかりません: {self.mock_data_file}")
                return self._generate_default_mock_data()
        except Exception as e:
            print(f"モックデータ読み込みエラー: {e}")
            return self._generate_default_mock_data()

    def _generate_default_mock_data(self) -> Dict:
        """デフォルトのモックデータを生成"""
        return {
            "races": {},
            "race_schedules": {}
        }

    def get_race_info(self, date: str) -> List[Dict]:
        """
        指定日のレース情報を取得（モック）

        Args:
            date: 日付 (YYYYMMDD形式)

        Returns:
            List[Dict]: レース情報のリスト
        """
        race_ids = self.mock_data.get("race_schedules", {}).get(date, [])

        race_info_list = []
        for race_id in race_ids:
            race = self.mock_data.get("races", {}).get(race_id)
            if race:
                race_info_list.append({
                    'race_id': race_id,
                    'race_name': race.get('race_name', ''),
                    'race_number': race.get('race_number', 0),
                    'venue': race.get('venue', ''),
                    'post_time': race.get('post_time', ''),
                    'distance': race.get('distance', 0),
                    'track_type': race.get('track_type', '')
                })

        return race_info_list

    def get_realtime_odds(self, race_id: str) -> List[Dict]:
        """
        リアルタイムオッズを取得（モック）

        Args:
            race_id: レースID

        Returns:
            List[Dict]: オッズデータのリスト
        """
        race = self.mock_data.get("races", {}).get(race_id)

        if not race:
            return []

        odds_dict = race.get("odds", {})
        odds_list = []

        for record_id, odds_data in odds_dict.items():
            # オッズをランダムに変動させる（リアルタイム感を出すため）
            varied_odds = self._add_odds_variation(odds_data.copy())
            varied_odds['mock'] = True
            varied_odds['timestamp'] = datetime.now().isoformat()
            odds_list.append(varied_odds)

        return odds_list

    def _add_odds_variation(self, odds_data: Dict) -> Dict:
        """
        オッズにランダムな変動を加える

        Args:
            odds_data: オッズデータ

        Returns:
            Dict: 変動を加えたオッズデータ
        """
        record_id = odds_data.get('record_id', '')

        # 単勝・複勝
        if record_id == 'O1':
            if 'tansho' in odds_data:
                for item in odds_data['tansho']:
                    variation = random.uniform(0.95, 1.05)
                    item['odds'] = round(item['odds'] * variation, 1)

            if 'fukusho' in odds_data:
                for item in odds_data['fukusho']:
                    variation = random.uniform(0.95, 1.05)
                    item['odds_min'] = round(item['odds_min'] * variation, 1)
                    item['odds_max'] = round(item['odds_max'] * variation, 1)

        # その他のオッズタイプ
        elif 'combinations' in odds_data:
            for item in odds_data['combinations']:
                variation = random.uniform(0.9, 1.1)
                if 'odds' in item:
                    item['odds'] = round(item['odds'] * variation, 1)
                if 'odds_min' in item:
                    item['odds_min'] = round(item['odds_min'] * variation, 1)
                if 'odds_max' in item:
                    item['odds_max'] = round(item['odds_max'] * variation, 1)

        # 時刻を現在時刻に更新
        now = datetime.now()
        odds_data['odds_time'] = now.strftime("%H%M%S")
        odds_data['odds_time_formatted'] = now.strftime("%H:%M:%S")
        odds_data['parsed_at'] = now.isoformat()

        return odds_data

    def get_race_detail(self, race_id: str) -> Optional[Dict]:
        """
        レース詳細情報を取得

        Args:
            race_id: レースID

        Returns:
            Optional[Dict]: レース詳細情報
        """
        return self.mock_data.get("races", {}).get(race_id)

    def list_available_races(self) -> List[str]:
        """利用可能なレースIDのリストを取得"""
        return list(self.mock_data.get("races", {}).keys())

    def list_available_dates(self) -> List[str]:
        """利用可能な日付のリストを取得"""
        return list(self.mock_data.get("race_schedules", {}).keys())

    def generate_race_id(
        self,
        date: str,
        venue_code: str = "05",
        kai: str = "01",
        nichi: str = "01",
        race_num: str = "01"
    ) -> str:
        """
        レースIDを生成

        Args:
            date: 日付 (YYYYMMDD)
            venue_code: 場コード
            kai: 回次
            nichi: 日次
            race_num: レース番号

        Returns:
            str: レースID
        """
        return f"{date}{venue_code}{kai}{nichi}{race_num}"

    def add_mock_race(self, race_id: str, race_data: Dict):
        """
        モックレースを追加

        Args:
            race_id: レースID
            race_data: レースデータ
        """
        if "races" not in self.mock_data:
            self.mock_data["races"] = {}

        self.mock_data["races"][race_id] = race_data

        # スケジュールも更新
        date = race_id[:8]
        if "race_schedules" not in self.mock_data:
            self.mock_data["race_schedules"] = {}

        if date not in self.mock_data["race_schedules"]:
            self.mock_data["race_schedules"][date] = []

        if race_id not in self.mock_data["race_schedules"][date]:
            self.mock_data["race_schedules"][date].append(race_id)

    def save_mock_data(self):
        """モックデータをファイルに保存"""
        try:
            filepath = Path(self.mock_data_file)
            filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.mock_data, f, ensure_ascii=False, indent=2)

            print(f"モックデータを保存しました: {self.mock_data_file}")
        except Exception as e:
            print(f"モックデータ保存エラー: {e}")


# グローバルインスタンス
_mock_provider = None


def get_mock_provider(mock_data_file: str = "./mock_data/sample_odds.json") -> MockDataProvider:
    """
    モックプロバイダーのシングルトンインスタンスを取得

    Args:
        mock_data_file: モックデータファイルのパス

    Returns:
        MockDataProvider: モックプロバイダー
    """
    global _mock_provider
    if _mock_provider is None:
        _mock_provider = MockDataProvider(mock_data_file)
    return _mock_provider


if __name__ == "__main__":
    # テスト
    provider = MockDataProvider()

    print("利用可能な日付:")
    print(provider.list_available_dates())

    print("\n利用可能なレース:")
    print(provider.list_available_races())

    print("\n2024年1月1日のレース情報:")
    races = provider.get_race_info("20240101")
    for race in races:
        print(f"  {race['race_id']}: {race['race_name']}")

    print("\nオッズ取得テスト:")
    odds = provider.get_realtime_odds("2024010105010101")
    for odd in odds:
        print(f"  {odd['record_type']}: {odd.get('odds_time_formatted', '')}")
