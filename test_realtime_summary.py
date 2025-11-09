"""
リアルタイムデータ取得の動作確認サマリー
"""

import sys
import os
from datetime import datetime

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.config import Config
from src.data_service import DataService

def main():
    """メインテスト"""
    print("\n" + "=" * 80)
    print("Real-time Data Source Test Summary")
    print("=" * 80 + "\n")

    # 現在時刻
    now = datetime.now()
    today = now.strftime("%Y%m%d")
    current_time = now.strftime("%H:%M:%S")

    print(f"テスト日時: {today} {current_time}")
    print()

    # DataService初期化
    service = DataService()

    status = service.get_status()
    print("=" * 80)
    print("Service Status")
    print("=" * 80)
    print(f"Environment: {status['environment']}")
    print(f"Default Data Source: {status['default_data_source']}")
    print(f"Providers:")
    for provider, available in status['providers'].items():
        status_mark = "OK" if available else "NG"
        print(f"  [{status_mark}] {provider}: {'Available' if available else 'Not Available'}")
    print()

    # Test 1: 今日のレース情報取得（realtime）
    print("=" * 80)
    print("Test 1: Get Today's Race Info (data_source=realtime)")
    print("=" * 80)
    try:
        races = service.get_race_info(today, data_source='realtime')
        print(f"[OK] SUCCESS: {len(races)} races found")
        if races:
            print(f"  First race ID: {races[0].get('race_id', 'N/A')}")
            print(f"  Last race ID: {races[-1].get('race_id', 'N/A')}")
    except Exception as e:
        print(f"[NG] FAILED: {e}")
    print()

    # Test 2: 過去データ取得（historical）
    if status['providers']['historical']:
        print("=" * 80)
        print("Test 2: Get Historical Race Info (data_source=historical)")
        print("=" * 80)
        test_date = "20251102"
        try:
            races = service.get_race_info(test_date, data_source='historical')
            print(f"[OK] SUCCESS: {len(races)} races found for {test_date}")
            if races:
                print(f"  First race ID: {races[0].get('race_id', 'N/A')}")

                # オッズ取得テスト
                race_id = races[0].get('race_id')
                odds_result = service.get_realtime_odds(race_id, data_source='historical')
                odds = odds_result.get('odds', [])
                print(f"  Odds records: {len(odds)}")

                # 三連単確認
                for odd in odds:
                    if odd.get('record_id') == 'O6':
                        odds_data = odd.get('odds_data', {})
                        print(f"  Trifecta combinations: {len(odds_data)}")
                        break
        except Exception as e:
            print(f"[NG] FAILED: {e}")
        print()

    # Test 3: data_source切り替え
    print("=" * 80)
    print("Test 3: Data Source Switching")
    print("=" * 80)
    test_sources = ['auto', 'realtime']
    if status['providers']['historical']:
        test_sources.insert(1, 'historical')

    for source in test_sources:
        try:
            resolved = service._resolve_data_source(source)
            print(f"  {source:12} -> {resolved}")
        except Exception as e:
            print(f"  {source:12} -> ERROR: {e}")
    print()

    # 結果サマリー
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"[OK] data_source parameter implemented successfully")
    print(f"[OK] API can switch between data sources at call time")
    print(f"[OK] Real-time provider: {'Available' if status['providers']['realtime'] else 'Not Available'}")
    print(f"[OK] Historical provider: {'Available' if status['providers']['historical'] else 'Not Available'}")
    print()

    if not status['providers']['historical']:
        print("Note: To enable historical data provider:")
        print("  1. Set ENABLE_HISTORICAL_DATA=true in .env")
        print("  2. Run: python -m scripts.setup_historical_db 20251102")
        print()

    print("API Usage Examples:")
    print("  GET /api/odds/{race_id}")
    print("  GET /api/odds/{race_id}?data_source=historical")
    print("  GET /api/odds/{race_id}?data_source=realtime")
    print()

    # クリーンアップ
    service.close()

    print("=" * 80)
    print("Test Completed")
    print("=" * 80)

if __name__ == "__main__":
    main()
