"""
レース情報取得のデバッグ
"""

import sys
import os
from datetime import datetime

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.jravan_odds_fetcher import JRAVANOddsFetcher

def main():
    print("=" * 80)
    print("Race Info Debug Test")
    print("=" * 80)

    today = datetime.now().strftime("%Y%m%d")
    print(f"日付: {today}\n")

    fetcher = JRAVANOddsFetcher()

    if not fetcher.initialize():
        print("ERROR: JV-Link初期化失敗")
        return

    print("レース情報取得中...\n")
    races = fetcher.get_race_info(today)

    print(f"取得レース数: {len(races)}\n")

    if races:
        print("最初の3レースのデータ構造:")
        for i, race in enumerate(races[:3], 1):
            print(f"\nレース {i}:")
            for key, value in race.items():
                if key == 'raw_data':
                    print(f"  {key}: {value[:100]}...")  # 最初の100文字だけ表示
                else:
                    print(f"  {key}: {value}")

    fetcher.close()

if __name__ == "__main__":
    main()
