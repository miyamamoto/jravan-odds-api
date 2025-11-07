"""
JRA-VAN 蓄積系データ（JVOpen）テスト

過去の時系列オッズを取得する
"""

import win32com.client
import sys

def test_jvopen(from_date, to_date, dataspec_list):
    """
    JVOpenで蓄積系データを取得する

    Args:
        from_date: 開始日（YYYYMMDD形式）
        to_date: 終了日（YYYYMMDD形式）
        dataspec_list: テストするデータ種別のリスト
    """
    try:
        # JV-Link初期化
        jvlink = win32com.client.Dispatch('JVDTLab.JVLink')
        ret = jvlink.JVInit("UNKNOWN")
        if ret != 0:
            print(f"JVInit error: {ret}")
            return

        print(f"期間: {from_date} - {to_date}\n")
        print("=" * 80)

        for dataspec in dataspec_list:
            print(f"\n[Data spec: {dataspec}]")
            print("-" * 80)

            try:
                # JVOpenを呼び出し
                # option: 1=通常データ, 3=セットアップ（初回のみ）
                option = 1

                ret = jvlink.JVOpen(dataspec, from_date, option)

                if isinstance(ret, tuple):
                    returncode = ret[0]
                    readcount = ret[1] if len(ret) > 1 else 0
                else:
                    returncode = ret
                    readcount = 0

                if returncode < 0:
                    print(f"  [X] JVOpen error: {returncode}")
                    print(f"     (-1: no data, -2: param error)")
                    continue

                print(f"  [OK] JVOpen success (return: {returncode}, count: {readcount})")

                # データ読み込み
                record_count = 0
                max_records = 10  # 最初の10レコードのみ表示

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
                        # レースIDを抽出（レコードによって位置が異なる）
                        race_id_pos = 11  # 多くのレコードでレースIDは11文字目から
                        race_id_preview = buff[race_id_pos:race_id_pos+16] if len(buff) > race_id_pos+16 else ""

                        print(f"  [Record {record_count}]: ID={record_id}, length={len(buff)}")
                        if race_id_preview:
                            print(f"     Race ID area: {race_id_preview}")
                        print(f"     Data preview: {buff[:80]}...")

                print(f"  [Total records]: {record_count}")

                # Close
                jvlink.JVClose()

            except Exception as e:
                print(f"  [ERROR]: {e}")
                import traceback
                traceback.print_exc()

        print("\n" + "=" * 80)
        print("Test completed")

    except Exception as e:
        print(f"Init error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # 11月2日のデータを取得
    from_date = "20251102"
    to_date = "20251102"

    # テストするデータ種別コード（蓄積系）
    # RA: レース情報
    # SE: 成績（確定後）
    # その他のオッズ関連
    dataspec_list = [
        "RA",    # レース情報（開催・レース）
        "SE",    # 成績（確定後）
        "0B31",  # 速報レース詳細（蓄積される可能性）
        "0B11",  # 速報レース情報（蓄積される可能性）
        "DIFF",  # 差分データ
    ]

    print("JRA-VAN JVOpen test (accumulated data)")
    print("=" * 80)
    test_jvopen(from_date, to_date, dataspec_list)
