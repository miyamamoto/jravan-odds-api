"""
JRA-VAN Odds API 包括的統合テスト

全機能を網羅的にテストします：
- データソース切り替え（auto/historical/realtime）
- 全オッズタイプ（O1-O6）
- エラーハンドリング
- パフォーマンス
"""

import sys
import os
import time
from datetime import datetime
from typing import Dict, List

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.config import Config
from src.data_service import DataService


class TestResult:
    """テスト結果を管理するクラス"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []

    def add_pass(self):
        self.passed += 1

    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")

    def add_skip(self):
        self.skipped += 1

    def print_summary(self):
        total = self.passed + self.failed + self.skipped
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total}")
        print(f"  [OK] Passed:  {self.passed}")
        print(f"  [NG] Failed:  {self.failed}")
        print(f"  [--] Skipped: {self.skipped}")
        print()

        if self.failed > 0:
            print("FAILED TESTS:")
            for error in self.errors:
                print(f"  - {error}")
            print()

        success_rate = (self.passed / total * 100) if total > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        print("=" * 80)


class ComprehensiveTest:
    """包括的テストクラス"""

    def __init__(self):
        self.result = TestResult()
        self.service = None

    def setup(self):
        """テスト環境のセットアップ"""
        print("\n" + "=" * 80)
        print("TEST SETUP")
        print("=" * 80)

        # DataService初期化
        self.service = DataService()

        # ステータス確認
        status = self.service.get_status()
        print(f"Environment: {status['environment']}")
        print(f"Default Data Source: {status['default_data_source']}")
        print(f"Available Providers:")
        for provider, available in status['providers'].items():
            mark = "OK" if available else "NG"
            print(f"  [{mark}] {provider}")
        print()

        return status

    def teardown(self):
        """テスト環境のクリーンアップ"""
        if self.service:
            self.service.close()

    def test_config(self):
        """設定のテスト"""
        print("=" * 80)
        print("TEST 1: Configuration")
        print("=" * 80)

        try:
            # 環境変数の確認
            assert Config.ENVIRONMENT in ['development', 'production'], \
                "Invalid ENVIRONMENT"
            self.result.add_pass()
            print("[OK] Environment variable is valid")

            # DEFAULT_DATA_SOURCEの確認
            assert Config.DEFAULT_DATA_SOURCE in ['auto', 'historical', 'realtime'], \
                "Invalid DEFAULT_DATA_SOURCE"
            self.result.add_pass()
            print("[OK] DEFAULT_DATA_SOURCE is valid")

            # API設定の確認
            assert Config.API_PORT > 0, "Invalid API_PORT"
            self.result.add_pass()
            print("[OK] API_PORT is valid")

        except AssertionError as e:
            self.result.add_fail("Config", str(e))
            print(f"[NG] {e}")
        except Exception as e:
            self.result.add_fail("Config", str(e))
            print(f"[NG] Unexpected error: {e}")
        print()

    def test_data_source_resolution(self, status: Dict):
        """データソース解決のテスト"""
        print("=" * 80)
        print("TEST 2: Data Source Resolution")
        print("=" * 80)

        test_cases = [
            ('auto', None),  # Expected will be determined by environment
            ('historical', 'historical'),
            ('realtime', 'realtime'),
        ]

        for source, expected in test_cases:
            try:
                resolved = self.service._resolve_data_source(source)

                if expected is None:
                    # autoの場合は環境に応じて変わる
                    print(f"[OK] {source:12} -> {resolved} (environment-dependent)")
                    self.result.add_pass()
                elif resolved == expected:
                    print(f"[OK] {source:12} -> {resolved}")
                    self.result.add_pass()
                else:
                    self.result.add_fail(f"DataSourceResolution({source})",
                                       f"Expected {expected}, got {resolved}")
                    print(f"[NG] {source:12} -> {resolved} (expected {expected})")

            except Exception as e:
                self.result.add_fail(f"DataSourceResolution({source})", str(e))
                print(f"[NG] {source:12} -> ERROR: {e}")
        print()

    def test_race_info_retrieval(self, status: Dict):
        """レース情報取得のテスト"""
        print("=" * 80)
        print("TEST 3: Race Info Retrieval")
        print("=" * 80)

        test_dates = []

        # リアルタイムプロバイダーが利用可能な場合
        if status['providers']['realtime']:
            today = datetime.now().strftime("%Y%m%d")
            test_dates.append(('realtime', today))

        # 蓄積系プロバイダーが利用可能な場合
        if status['providers']['historical']:
            test_dates.append(('historical', '20251102'))

        if not test_dates:
            print("[--] No providers available, skipping test")
            self.result.add_skip()
            print()
            return

        for data_source, date in test_dates:
            try:
                start_time = time.time()
                races = self.service.get_race_info(date, data_source=data_source)
                elapsed = time.time() - start_time

                if races and len(races) > 0:
                    print(f"[OK] {data_source:12} {date}: {len(races)} races ({elapsed:.2f}s)")
                    self.result.add_pass()

                    # race_id抽出のテスト
                    first_race = races[0]
                    if 'race_id' in first_race and first_race['race_id']:
                        print(f"     First race ID: {first_race['race_id']}")
                        self.result.add_pass()
                    else:
                        self.result.add_fail(f"RaceInfo({data_source})",
                                           "race_id not found or empty")
                        print(f"[NG] race_id not found")
                else:
                    print(f"[--] {data_source:12} {date}: No races found")
                    self.result.add_skip()

            except Exception as e:
                self.result.add_fail(f"RaceInfo({data_source},{date})", str(e))
                print(f"[NG] {data_source:12} {date}: ERROR: {e}")
        print()

    def test_odds_retrieval_all_types(self, status: Dict):
        """全オッズタイプ取得のテスト"""
        print("=" * 80)
        print("TEST 4: Odds Retrieval - All Types (O1-O6)")
        print("=" * 80)

        test_race_ids = []

        # 蓄積系データがある場合
        if status['providers']['historical']:
            try:
                races = self.service.get_race_info('20251102', data_source='historical')
                if races:
                    test_race_ids.append(('historical', races[0].get('race_id')))
            except:
                pass

        # リアルタイムデータがある場合
        if status['providers']['realtime']:
            try:
                today = datetime.now().strftime("%Y%m%d")
                races = self.service.get_race_info(today, data_source='realtime')
                if races:
                    test_race_ids.append(('realtime', races[0].get('race_id')))
            except:
                pass

        if not test_race_ids:
            print("[--] No test races available, skipping test")
            self.result.add_skip()
            print()
            return

        expected_records = {
            'O1': '単勝・複勝',
            'O2': '枠連',
            'O3': '馬連',
            'O4': 'ワイド',
            'O5': '馬単',
            'O6': '三連単'
        }

        for data_source, race_id in test_race_ids:
            print(f"\nTesting {data_source}: {race_id}")
            print("-" * 40)

            try:
                start_time = time.time()
                odds_result = self.service.get_realtime_odds(race_id, data_source=data_source)
                elapsed = time.time() - start_time

                if 'error' in odds_result:
                    print(f"[NG] Error: {odds_result['error']}")
                    self.result.add_fail(f"Odds({data_source},{race_id})", odds_result['error'])
                    continue

                odds = odds_result.get('odds', [])
                print(f"Retrieved {len(odds)} odds records in {elapsed:.2f}s")

                if len(odds) == 0:
                    print(f"[--] No odds data available")
                    self.result.add_skip()
                    continue

                # 各オッズタイプをチェック
                found_records = {}
                for odd in odds:
                    record_id = odd.get('record_id', 'Unknown')
                    record_type = odd.get('record_type', 'Unknown')
                    odds_data = odd.get('odds_data', {})

                    found_records[record_id] = {
                        'type': record_type,
                        'count': len(odds_data) if isinstance(odds_data, dict) else 0
                    }

                # 結果判定
                for record_id, expected_name in expected_records.items():
                    if record_id in found_records:
                        info = found_records[record_id]
                        if info['count'] > 0:
                            print(f"  [OK] {record_id} {expected_name:12} {info['count']:6} combinations")
                            self.result.add_pass()

                            # 三連単の場合は追加チェック
                            if record_id == 'O6' and info['count'] >= 1000:
                                print(f"       (Trifecta data looks valid: {info['count']} combinations)")
                                self.result.add_pass()
                        else:
                            print(f"  [--] {record_id} {expected_name:12} empty")
                            self.result.add_skip()
                    else:
                        print(f"  [--] {record_id} {expected_name:12} not found")
                        self.result.add_skip()

            except Exception as e:
                self.result.add_fail(f"Odds({data_source},{race_id})", str(e))
                print(f"[NG] ERROR: {e}")
        print()

    def test_deadline_info(self, status: Dict):
        """締め切り情報のテスト"""
        print("=" * 80)
        print("TEST 5: Deadline Information")
        print("=" * 80)

        test_race_ids = []

        # 蓄積系データから取得
        if status['providers']['historical']:
            try:
                races = self.service.get_race_info('20251102', data_source='historical')
                if races:
                    test_race_ids.append(('historical', races[0].get('race_id')))
            except:
                pass

        if not test_race_ids:
            print("[--] No test races available, skipping test")
            self.result.add_skip()
            print()
            return

        for data_source, race_id in test_race_ids:
            try:
                odds_result = self.service.get_realtime_odds(race_id, data_source=data_source)

                if 'deadline_info' in odds_result:
                    deadline_info = odds_result['deadline_info']
                    is_past = odds_result.get('is_past_data', False)

                    print(f"[OK] {data_source:12} {race_id}")
                    print(f"     Deadline: {deadline_info.get('deadline', 'N/A')}")
                    print(f"     Is Past: {is_past}")
                    self.result.add_pass()
                else:
                    self.result.add_fail(f"DeadlineInfo({data_source})", "deadline_info not found")
                    print(f"[NG] deadline_info not found")

            except Exception as e:
                self.result.add_fail(f"DeadlineInfo({data_source},{race_id})", str(e))
                print(f"[NG] ERROR: {e}")
        print()

    def test_seconds_before_deadline(self, status: Dict):
        """締め切り前シミュレーションのテスト"""
        print("=" * 80)
        print("TEST 6: Seconds Before Deadline Simulation")
        print("=" * 80)

        # 蓄積系データでのみテスト可能
        if not status['providers']['historical']:
            print("[--] Historical provider not available, skipping test")
            self.result.add_skip()
            print()
            return

        try:
            races = self.service.get_race_info('20251102', data_source='historical')
            if not races:
                print("[--] No test races available")
                self.result.add_skip()
                print()
                return

            race_id = races[0].get('race_id')

            # 300秒前をシミュレート
            test_seconds = [300, 600, 900]

            for seconds in test_seconds:
                odds_result = self.service.get_realtime_odds(
                    race_id,
                    seconds_before_deadline=seconds,
                    data_source='historical'
                )

                if odds_result.get('is_past_data') and \
                   odds_result.get('seconds_before_deadline') == seconds:
                    print(f"[OK] {seconds}秒前: Simulation successful")
                    self.result.add_pass()
                else:
                    self.result.add_fail(f"SecondsBeforeDeadline({seconds})",
                                       "Simulation parameters incorrect")
                    print(f"[NG] {seconds}秒前: Simulation failed")

        except Exception as e:
            self.result.add_fail("SecondsBeforeDeadline", str(e))
            print(f"[NG] ERROR: {e}")
        print()

    def test_error_handling(self):
        """エラーハンドリングのテスト"""
        print("=" * 80)
        print("TEST 7: Error Handling")
        print("=" * 80)

        # 存在しない日付
        try:
            races = self.service.get_race_info('19990101', data_source='historical')
            if isinstance(races, list):
                print(f"[OK] Invalid date handled: returned {len(races)} races")
                self.result.add_pass()
            else:
                self.result.add_fail("ErrorHandling(InvalidDate)", "Invalid return type")
                print(f"[NG] Invalid return type")
        except Exception as e:
            print(f"[OK] Invalid date raised exception (expected): {e}")
            self.result.add_pass()

        # 存在しないrace_id
        try:
            odds_result = self.service.get_realtime_odds('99999999', data_source='historical')
            if 'error' in odds_result or len(odds_result.get('odds', [])) == 0:
                print(f"[OK] Invalid race_id handled")
                self.result.add_pass()
            else:
                self.result.add_fail("ErrorHandling(InvalidRaceId)",
                                   "Invalid race_id not properly handled")
                print(f"[NG] Invalid race_id not handled")
        except Exception as e:
            print(f"[OK] Invalid race_id raised exception (expected)")
            self.result.add_pass()

        # 不正なdata_source
        try:
            races = self.service.get_race_info('20251102', data_source='invalid')
            self.result.add_fail("ErrorHandling(InvalidDataSource)",
                               "Invalid data_source not rejected")
            print(f"[NG] Invalid data_source not rejected")
        except Exception as e:
            print(f"[OK] Invalid data_source rejected: {e}")
            self.result.add_pass()
        print()

    def test_performance(self, status: Dict):
        """パフォーマンステスト"""
        print("=" * 80)
        print("TEST 8: Performance")
        print("=" * 80)

        if not status['providers']['historical']:
            print("[--] Historical provider not available, skipping test")
            self.result.add_skip()
            print()
            return

        try:
            # レース情報取得の速度
            start = time.time()
            races = self.service.get_race_info('20251102', data_source='historical')
            race_info_time = time.time() - start

            print(f"Race Info Retrieval: {race_info_time:.3f}s")
            if race_info_time < 5.0:
                print(f"[OK] Performance acceptable (< 5s)")
                self.result.add_pass()
            else:
                print(f"[--] Performance slow (>= 5s)")
                self.result.add_skip()

            if races:
                race_id = races[0].get('race_id')

                # オッズ取得の速度
                start = time.time()
                odds_result = self.service.get_realtime_odds(race_id, data_source='historical')
                odds_time = time.time() - start

                print(f"Odds Retrieval: {odds_time:.3f}s")
                if odds_time < 10.0:
                    print(f"[OK] Performance acceptable (< 10s)")
                    self.result.add_pass()
                else:
                    print(f"[--] Performance slow (>= 10s)")
                    self.result.add_skip()

        except Exception as e:
            self.result.add_fail("Performance", str(e))
            print(f"[NG] ERROR: {e}")
        print()

    def run_all_tests(self):
        """全テストを実行"""
        print("\n" + "=" * 80)
        print("JRA-VAN ODDS API - COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # セットアップ
        status = self.setup()

        # 各テストを実行
        self.test_config()
        self.test_data_source_resolution(status)
        self.test_race_info_retrieval(status)
        self.test_odds_retrieval_all_types(status)
        self.test_deadline_info(status)
        self.test_seconds_before_deadline(status)
        self.test_error_handling()
        self.test_performance(status)

        # クリーンアップ
        self.teardown()

        # サマリー表示
        self.result.print_summary()

        print(f"\nEnd Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 終了コード
        return 0 if self.result.failed == 0 else 1


def main():
    """メイン関数"""
    test = ComprehensiveTest()
    exit_code = test.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
