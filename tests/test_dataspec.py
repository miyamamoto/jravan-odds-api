"""
JRA-VAN データ種別テストスクリプト

異なるデータ種別コードで過去レースのオッズを取得してみる
"""

import win32com.client
import sys

def test_dataspec(race_id, dataspec_list):
    """
    複数のデータ種別コードを試す

    Args:
        race_id: レースID
        dataspec_list: テストするデータ種別のリスト
    """
    try:
        # JV-Link初期化
        jvlink = win32com.client.Dispatch('JVDTLab.JVLink')
        ret = jvlink.JVInit("UNKNOWN")
        if ret != 0:
            print(f"JVInit エラー: {ret}")
            return

        print(f"レースID: {race_id}\n")
        print("=" * 80)

        for dataspec in dataspec_list:
            print(f"\n【データ種別: {dataspec}】")
            print("-" * 80)

            try:
                # JVRTOpenを呼び出し
                ret = jvlink.JVRTOpen(dataspec, race_id)

                if isinstance(ret, tuple):
                    returncode = ret[0]
                else:
                    returncode = ret

                if returncode < 0:
                    print(f"  [X] JVRTOpen error: {returncode}")
                    print(f"     (-1: no data, -2: param error, -3: init error etc)")
                    continue

                print(f"  [OK] JVRTOpen success (return: {returncode})")

                # データ読み込み
                record_count = 0
                max_records = 5  # 最初の5レコードのみ表示

                while True:
                    ret = jvlink.JVRead("", 102890, "")

                    if isinstance(ret, tuple):
                        returncode = ret[0]
                        buff = ret[1] if len(ret) > 1 else ""
                    else:
                        returncode = ret
                        buff = ""

                    # 読み込み完了
                    if returncode == 0:
                        break

                    # エラー
                    if returncode < 0:
                        print(f"  [!] JVRead error: {returncode}")
                        break

                    record_count += 1

                    # レコードIDとデータの先頭を表示
                    if record_count <= max_records and len(buff) >= 2:
                        record_id = buff[:2]
                        preview = buff[:100] if len(buff) > 100 else buff
                        print(f"  [Record{record_count}]: ID={record_id}, length={len(buff)}")
                        print(f"     preview: {preview}...")

                print(f"  [Total records]: {record_count}")

                # Close
                jvlink.JVClose()

            except Exception as e:
                print(f"  [ERROR]: {e}")

        print("\n" + "=" * 80)
        print("テスト完了")

    except Exception as e:
        print(f"初期化エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 11月2日の天皇賞（秋）のレースID
    # 2025年11月2日 東京5回4日目 11レース
    race_id = "20251102050411"

    # テストするデータ種別コード
    dataspec_list = [
        "0B11",  # 速報レース情報
        "0B12",  # 速報レース情報（成績確定後）
        "0B15",  # 速報レース情報（出走馬名表～）
        "0B20",  # 時系列オッズ（推定）
        "0B31",  # レース詳細・オッズ（現在使用中）
        "0B41",  # その他の可能性
    ]

    print("JRA-VAN データ種別テスト")
    print("=" * 80)
    test_dataspec(race_id, dataspec_list)
