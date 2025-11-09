"""
data_sourceパラメータ切り替え機能のテスト
"""

import sys
import os

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.config import Config
from src.data_service import DataService

def test_config():
    """設定のテスト"""
    print("=" * 80)
    print("Config Test")
    print("=" * 80)

    print(f"ENVIRONMENT: {Config.ENVIRONMENT}")
    print(f"DEFAULT_DATA_SOURCE: {Config.DEFAULT_DATA_SOURCE}")
    print(f"ENABLE_HISTORICAL_DATA: {Config.ENABLE_HISTORICAL_DATA}")
    print(f"USE_MOCK_DATA: {Config.USE_MOCK_DATA}")
    print()

def test_data_service_init():
    """DataService初期化のテスト"""
    print("=" * 80)
    print("DataService Initialization Test")
    print("=" * 80)

    service = DataService()

    print(f"Historical Provider: {service.historical_provider is not None}")
    print(f"Realtime Provider: {service.fetcher is not None}")
    print(f"Mock Provider: {service.mock_provider is not None}")
    print()

    status = service.get_status()
    print("Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    print()

    return service

def test_data_source_resolution(service):
    """データソース解決のテスト"""
    print("=" * 80)
    print("Data Source Resolution Test")
    print("=" * 80)

    test_cases = ['auto', 'historical', 'realtime', 'mock']

    for source in test_cases:
        try:
            resolved = service._resolve_data_source(source)
            print(f"  {source:12} -> {resolved}")
        except Exception as e:
            print(f"  {source:12} -> ERROR: {e}")
    print()

def test_race_info_with_data_source(service):
    """レース情報取得のテスト（data_sourceパラメータ付き）"""
    print("=" * 80)
    print("Race Info Fetch Test (with data_source parameter)")
    print("=" * 80)

    test_date = "20251102"  # 過去の日付

    # 'auto'でテスト
    print(f"Testing with data_source='auto':")
    try:
        races = service.get_race_info(test_date, data_source='auto')
        print(f"  Result: {len(races)} races found")
    except Exception as e:
        print(f"  Error: {e}")

    # 'historical'でテスト（蓄積系データがある場合）
    if service.historical_provider:
        print(f"\nTesting with data_source='historical':")
        try:
            races = service.get_race_info(test_date, data_source='historical')
            print(f"  Result: {len(races)} races found")
        except Exception as e:
            print(f"  Error: {e}")

    print()

def main():
    """メインテスト"""
    print("\n" + "=" * 80)
    print("Data Source Switching Implementation Test")
    print("=" * 80 + "\n")

    # 1. Config確認
    test_config()

    # 2. DataService初期化確認
    service = test_data_service_init()

    # 3. データソース解決ロジック確認
    test_data_source_resolution(service)

    # 4. 実際のAPI呼び出しテスト
    test_race_info_with_data_source(service)

    # クリーンアップ
    service.close()

    print("=" * 80)
    print("Test Completed")
    print("=" * 80)

if __name__ == "__main__":
    main()
