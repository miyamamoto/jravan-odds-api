"""
historicalデータソースでの動作確認テスト
"""

import sys
import os

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 環境変数を設定してhistoricalデータを有効化
os.environ['ENABLE_HISTORICAL_DATA'] = 'true'
os.environ['HISTORICAL_CACHE_DIR'] = './historical_cache'

from src.config import Config
from src.data_service import DataService

def main():
    """メインテスト"""
    print("\n" + "=" * 80)
    print("Historical Data Source Test")
    print("=" * 80 + "\n")

    print(f"ENABLE_HISTORICAL_DATA: {Config.ENABLE_HISTORICAL_DATA}")
    print(f"HISTORICAL_CACHE_DIR: {Config.HISTORICAL_CACHE_DIR}")
    print()

    # DataService初期化
    service = DataService()

    status = service.get_status()
    print("Service Status:")
    print(f"  Environment: {status['environment']}")
    print(f"  Default Data Source: {status['default_data_source']}")
    print(f"  Providers: {status['providers']}")
    print()

    # 過去データが存在する日付でテスト
    test_date = "20251102"

    print("=" * 80)
    print(f"Test 1: data_source='historical' ({test_date})")
    print("=" * 80)
    try:
        races = service.get_race_info(test_date, data_source='historical')
        print(f"SUCCESS: {len(races)} races found")
        if races:
            print(f"First race: {races[0].get('race_id', 'N/A')}")
    except Exception as e:
        print(f"ERROR: {e}")
    print()

    print("=" * 80)
    print(f"Test 2: data_source='realtime' ({test_date})")
    print("=" * 80)
    try:
        races = service.get_race_info(test_date, data_source='realtime')
        print(f"SUCCESS: {len(races)} races found")
        if races:
            print(f"First race: {races[0].get('race_id', 'N/A')}")
    except Exception as e:
        print(f"ERROR: {e}")
    print()

    print("=" * 80)
    print(f"Test 3: data_source='auto' (should use historical in dev mode)")
    print("=" * 80)
    try:
        resolved = service._resolve_data_source('auto')
        print(f"Resolved to: {resolved}")
        races = service.get_race_info(test_date, data_source='auto')
        print(f"SUCCESS: {len(races)} races found")
    except Exception as e:
        print(f"ERROR: {e}")
    print()

    # オッズ取得テスト
    if service.historical_provider:
        print("=" * 80)
        print("Test 4: Get Odds with data_source='historical'")
        print("=" * 80)
        try:
            races = service.get_race_info(test_date, data_source='historical')
            if races:
                race_id = races[0].get('race_id')
                print(f"Testing race_id: {race_id}")

                odds_result = service.get_realtime_odds(
                    race_id,
                    data_source='historical'
                )

                odds = odds_result.get('odds', [])
                print(f"SUCCESS: {len(odds)} odds records found")

                # 三連単オッズの確認
                for odd in odds:
                    if odd.get('record_id') == 'O6':
                        odds_data = odd.get('odds_data', {})
                        print(f"Trifecta (O6): {len(odds_data)} combinations")
                        # サンプル表示
                        if odds_data:
                            sample = list(odds_data.items())[:3]
                            for combo, value in sample:
                                print(f"  {combo}: {value:.1f}倍")
                        break
        except Exception as e:
            print(f"ERROR: {e}")
        print()

    # クリーンアップ
    service.close()

    print("=" * 80)
    print("Test Completed")
    print("=" * 80)

if __name__ == "__main__":
    main()
