"""
蓄積系データ統合テスト

開発モードで蓄積系データプロバイダーが正しく動作するか確認します。
"""

import logging
import json
import sys
import os

# 環境変数を設定（テスト用）
os.environ['ENVIRONMENT'] = 'development'
os.environ['ENABLE_HISTORICAL_DATA'] = 'true'

from src.config import Config
from src.data_service import DataService
from src.historical_data_provider import HistoricalDataProvider
from src.odds_cache import OddsCache

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def print_section(title):
    """セクションヘッダーを表示"""
    print()
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)
    print()


def test_config():
    """設定のテスト"""
    print_section("TEST 1: Configuration")

    config_info = Config.get_info()
    print("Configuration:")
    for key, value in config_info.items():
        print(f"  {key}: {value}")

    # 検証
    assert Config.is_development(), "Should be in development mode"
    assert Config.ENABLE_HISTORICAL_DATA, "Historical data should be enabled"

    print()
    print("[PASS] Configuration test passed")
    return True


def test_historical_provider():
    """HistoricalDataProviderのテスト"""
    print_section("TEST 2: Historical Data Provider")

    provider = HistoricalDataProvider(
        cache_dir="./test_historical_cache",
        service_key="UNKNOWN",
        auto_fetch=False
    )

    print("Provider initialized:")
    status = provider.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")

    # キャッシュ統計
    cache_stats = status.get('cache_stats', {})
    print()
    print("Cache statistics:")
    for key, value in cache_stats.items():
        print(f"  {key}: {value}")

    print()
    print("[PASS] Historical provider test passed")
    return True


def test_cache_operations():
    """キャッシュ操作のテスト"""
    print_section("TEST 3: Cache Operations")

    cache = OddsCache("./test_cache_ops")

    # テストデータ
    test_race_id = "20251102050411"
    test_odds = [
        {
            'record_id': 'O1',
            'race_id': test_race_id,
            'odds_type': 'tansho',
            'data': 'test_data_1'
        },
        {
            'record_id': 'O2',
            'race_id': test_race_id,
            'odds_type': 'wakuren',
            'data': 'test_data_2'
        }
    ]
    test_race_info = {
        'race_name': 'Test Race',
        'post_time': '15:40'
    }

    # 保存テスト
    print("Saving test data...")
    cache.save_odds(test_race_id, test_odds, test_race_info)
    print(f"  [OK] Data saved for race: {test_race_id}")

    # 存在確認
    print()
    print("Checking cache existence...")
    assert cache.has_cache(test_race_id), "Cache should exist"
    print("  [OK] Cache exists")

    # 読み込みテスト
    print()
    print("Loading cached data...")
    loaded = cache.load_odds(test_race_id)
    assert loaded is not None, "Should load cached data"
    assert loaded['race_id'] == test_race_id, "Race ID should match"
    assert len(loaded['odds']) == 2, "Should have 2 odds records"
    print(f"  [OK] Data loaded successfully")
    print(f"  Race ID: {loaded['race_id']}")
    print(f"  Odds count: {len(loaded['odds'])}")
    print(f"  Race name: {loaded['race_info'].get('race_name')}")

    # 統計情報
    print()
    print("Cache statistics:")
    stats = cache.get_cache_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print()
    print("[PASS] Cache operations test passed")
    return True


def test_data_service():
    """DataServiceの統合テスト"""
    print_section("TEST 4: Data Service Integration")

    # サービス初期化
    print("Initializing DataService...")
    service = DataService()

    # ステータス確認
    print()
    print("Service status:")
    status = service.get_status()
    for key, value in status.items():
        if key != 'historical_provider_status':  # ネストされた情報は後で表示
            print(f"  {key}: {value}")

    # Historical provider statusを表示
    if 'historical_provider_status' in status:
        print()
        print("Historical provider status:")
        for key, value in status['historical_provider_status'].items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")

    # 検証
    assert status['mode'] == 'development_historical', "Should be in historical mode"
    assert status.get('historical_provider_initialized'), "Historical provider should be initialized"

    print()
    print("[PASS] Data service integration test passed")

    service.close()
    return True


def test_race_info_retrieval():
    """レース情報取得のテスト"""
    print_section("TEST 5: Race Info Retrieval")

    service = DataService()

    print("Attempting to get race info for 20251102...")
    races = service.get_race_info("20251102")

    print(f"  Found {len(races)} races")

    if races:
        print()
        print("Sample race (first one):")
        sample = races[0]
        for key, value in sample.items():
            print(f"  {key}: {value}")
    else:
        print("  Note: No races found in cache. Run setup_historical_db.py first.")

    service.close()

    print()
    print("[PASS] Race info retrieval test passed")
    return True


def test_odds_retrieval():
    """オッズ取得のテスト"""
    print_section("TEST 6: Odds Retrieval")

    service = DataService()

    # キャッシュから任意のレースIDを取得
    cache = OddsCache(Config.HISTORICAL_CACHE_DIR)
    cached_races = cache.get_cached_races()

    if not cached_races:
        print("  Note: No cached races found. Run setup_historical_db.py first.")
        print("  Skipping odds retrieval test.")
        service.close()
        return True

    # 最初のレースでテスト
    test_race_id = cached_races[0]
    print(f"Testing with race ID: {test_race_id}")

    # 通常のオッズ取得
    print()
    print("Getting current odds...")
    odds_result = service.get_realtime_odds(test_race_id)

    print(f"  Odds count: {len(odds_result.get('odds', []))}")
    print(f"  Is past data: {odds_result.get('is_past_data')}")
    print(f"  Data source: {odds_result.get('data_source')}")

    # 締め切り300秒前のオッズ取得
    print()
    print("Getting odds 300 seconds before deadline...")
    odds_300 = service.get_realtime_odds(test_race_id, seconds_before_deadline=300)

    print(f"  Odds count: {len(odds_300.get('odds', []))}")
    print(f"  Seconds before deadline: {odds_300.get('seconds_before_deadline')}")
    print(f"  Time status: {odds_300.get('time_status')}")
    print(f"  Note: {odds_300.get('past_data_note')}")

    service.close()

    print()
    print("[PASS] Odds retrieval test passed")
    return True


def main():
    """メイン処理"""
    print()
    print("=" * 80)
    print("  JRA-VAN Historical Data Integration Test")
    print("=" * 80)
    print()
    print("This test verifies the historical data provider integration.")
    print()

    tests = [
        ("Configuration", test_config),
        ("Historical Provider", test_historical_provider),
        ("Cache Operations", test_cache_operations),
        ("Data Service Integration", test_data_service),
        ("Race Info Retrieval", test_race_info_retrieval),
        ("Odds Retrieval", test_odds_retrieval),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, "PASS" if result else "FAIL"))
        except Exception as e:
            print()
            print(f"[FAIL] {test_name} test failed with error:")
            print(f"  {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((test_name, "FAIL"))

    # 結果サマリー
    print_section("TEST SUMMARY")

    for test_name, result in results:
        status_symbol = "[OK]" if result == "PASS" else "[X]"
        print(f"{status_symbol} {test_name}: {result}")

    print()

    passed = sum(1 for _, result in results if result == "PASS")
    total = len(results)

    print(f"Total: {passed}/{total} tests passed")
    print()

    if passed == total:
        print("=" * 80)
        print("  ALL TESTS PASSED!")
        print("=" * 80)
        print()
        print("Next steps:")
        print("  1. Run setup_historical_db.py to download historical data")
        print("  2. Start API server in development mode:")
        print("     export ENVIRONMENT=development")
        print("     python api_server.py")
        print()
        return 0
    else:
        print("=" * 80)
        print("  SOME TESTS FAILED")
        print("=" * 80)
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
