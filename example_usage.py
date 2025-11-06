"""
JRA-VAN オッズ取得の使用例

このスクリプトは、jravan_odds_fetcherの具体的な使用方法を示すサンプルです。
"""

from jravan_odds_fetcher import JRAVANOddsFetcher
from odds_parser import parse_odds_record
from datetime import datetime, timedelta
import time


def example1_get_today_races():
    """例1: 今日のレース情報を取得"""
    print("\n" + "=" * 60)
    print("例1: 今日のレース情報を取得")
    print("=" * 60 + "\n")

    fetcher = JRAVANOddsFetcher()

    if not fetcher.initialize():
        print("初期化に失敗しました")
        return

    # 今日の日付を取得
    today = datetime.now().strftime("%Y%m%d")
    print(f"対象日: {today}")

    # レース情報を取得
    race_info = fetcher.get_race_info(today)

    if race_info:
        print(f"取得したレース数: {len(race_info)}")
        # 最初の5件を表示
        for i, race in enumerate(race_info[:5], 1):
            print(f"{i}. レース情報取得成功")
    else:
        print("レース情報が取得できませんでした")
        print("（開催日でない、またはオッズ発表前の可能性があります）")

    fetcher.close()


def example2_get_specific_race_odds():
    """例2: 特定レースのオッズを取得"""
    print("\n" + "=" * 60)
    print("例2: 特定レースのオッズを取得")
    print("=" * 60 + "\n")

    fetcher = JRAVANOddsFetcher()

    if not fetcher.initialize():
        print("初期化に失敗しました")
        return

    # レースIDを指定（例: 今日の東京1回1日目 1レース）
    today = datetime.now().strftime("%Y%m%d")
    race_id = f"{today}05010101"  # 東京1回1日目 1レース

    print(f"レースID: {race_id}")
    print(f"  日付: {today}")
    print(f"  場所: 東京")
    print(f"  回次: 1回1日目")
    print(f"  レース番号: 1R")
    print()

    # オッズを取得
    odds_data = fetcher.get_realtime_odds(race_id)

    if odds_data:
        print(f"取得したオッズデータ数: {len(odds_data)}")
        for odds in odds_data:
            print(f"  - {odds['type']}")
    else:
        print("オッズデータが取得できませんでした")
        print("（レースが存在しない、またはオッズ発表前の可能性があります）")

    fetcher.close()


def example3_parse_tansho_fukusho():
    """例3: 単勝・複勝オッズを詳細にパース"""
    print("\n" + "=" * 60)
    print("例3: 単勝・複勝オッズを詳細にパース")
    print("=" * 60 + "\n")

    fetcher = JRAVANOddsFetcher()

    if not fetcher.initialize():
        print("初期化に失敗しました")
        return

    # レースIDを指定
    today = datetime.now().strftime("%Y%m%d")
    race_id = f"{today}05010101"

    print(f"レースID: {race_id}\n")

    # オッズを取得
    odds_data = fetcher.get_realtime_odds(race_id)

    # 単勝・複勝オッズを探してパース
    for odds in odds_data:
        if odds['record_id'] == 'O1':
            print("単勝・複勝オッズを発見！")

            # 詳細パース
            raw_data = odds.get('raw_data', '')
            parsed = parse_odds_record('O1', raw_data)

            if 'error' not in parsed:
                print(f"オッズ時刻: {parsed.get('odds_time_formatted', '不明')}")

                # 単勝オッズ
                tansho_list = parsed.get('tansho', [])
                if tansho_list:
                    print("\n【単勝オッズ】")
                    for tansho in tansho_list:
                        print(f"  {tansho['umaban']:2d}番: {tansho['odds']:6.1f}倍")

                # 複勝オッズ
                fukusho_list = parsed.get('fukusho', [])
                if fukusho_list:
                    print("\n【複勝オッズ】")
                    for fukusho in fukusho_list:
                        print(f"  {fukusho['umaban']:2d}番: {fukusho['odds_min']:5.1f} - {fukusho['odds_max']:5.1f}倍")
            else:
                print(f"パースエラー: {parsed['error']}")
            break
    else:
        print("単勝・複勝オッズが見つかりませんでした")

    fetcher.close()


def example4_multiple_races():
    """例4: 複数レースのオッズを順次取得"""
    print("\n" + "=" * 60)
    print("例4: 複数レースのオッズを順次取得")
    print("=" * 60 + "\n")

    fetcher = JRAVANOddsFetcher()

    if not fetcher.initialize():
        print("初期化に失敗しました")
        return

    today = datetime.now().strftime("%Y%m%d")

    # 東京競馬場の1～3レースのオッズを取得
    race_numbers = [1, 2, 3]

    for race_num in race_numbers:
        race_id = f"{today}0501{race_num:02d}01"  # 東京1回1日目 X レース
        print(f"レース{race_num}R (ID: {race_id})")

        odds_data = fetcher.get_realtime_odds(race_id)

        if odds_data:
            print(f"  取得成功: {len(odds_data)}種類のオッズ")
            for odds in odds_data:
                print(f"    - {odds['type']}")
        else:
            print("  取得失敗またはデータなし")

        print()

        # サーバーへの負荷を考慮して待機
        if race_num < len(race_numbers):
            print("  (3秒待機...)\n")
            time.sleep(3)

    fetcher.close()


def example5_odds_monitoring():
    """例5: オッズの変動を定期的に監視（デモ）"""
    print("\n" + "=" * 60)
    print("例5: オッズ変動監視（3回取得のデモ）")
    print("=" * 60 + "\n")

    fetcher = JRAVANOddsFetcher()

    if not fetcher.initialize():
        print("初期化に失敗しました")
        return

    today = datetime.now().strftime("%Y%m%d")
    race_id = f"{today}05010101"  # 東京1回1日目 1レース

    print(f"監視対象レース: {race_id}")
    print("10秒間隔で3回取得します\n")

    for i in range(3):
        print(f"[{i+1}回目] {datetime.now().strftime('%H:%M:%S')}")

        odds_data = fetcher.get_realtime_odds(race_id)

        if odds_data:
            print(f"  オッズデータ取得成功: {len(odds_data)}種類")

            # 単勝オッズのみ簡易表示
            for odds in odds_data:
                if odds['record_id'] == 'O1':
                    print(f"  単勝・複勝オッズを確認")
                    break
        else:
            print("  データなし")

        if i < 2:
            print("  (10秒待機...)\n")
            time.sleep(10)

    print("\n監視終了")
    fetcher.close()


def main():
    """メイン処理"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "JRA-VAN オッズ取得 サンプルスクリプト" + " " * 8 + "║")
    print("╚" + "=" * 58 + "╝")

    print("\n実行する例を選択してください：")
    print()
    print("  1. 今日のレース情報を取得")
    print("  2. 特定レースのオッズを取得")
    print("  3. 単勝・複勝オッズを詳細にパース")
    print("  4. 複数レースのオッズを順次取得")
    print("  5. オッズ変動監視（デモ）")
    print("  0. すべての例を実行")
    print()

    try:
        choice = input("選択 (0-5): ").strip()

        if choice == '1':
            example1_get_today_races()
        elif choice == '2':
            example2_get_specific_race_odds()
        elif choice == '3':
            example3_parse_tansho_fukusho()
        elif choice == '4':
            example4_multiple_races()
        elif choice == '5':
            example5_odds_monitoring()
        elif choice == '0':
            example1_get_today_races()
            example2_get_specific_race_odds()
            example3_parse_tansho_fukusho()
            example4_multiple_races()
            example5_odds_monitoring()
        else:
            print("無効な選択です")

    except KeyboardInterrupt:
        print("\n\n中断されました")
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")

    print("\n処理完了")


if __name__ == "__main__":
    main()
