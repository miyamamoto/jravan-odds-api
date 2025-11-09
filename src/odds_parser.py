"""
JRA-VANオッズデータ詳細パーサー

各オッズレコード（O1-O6）の詳細なパース処理を実装
"""

from typing import Dict, List, Optional
from datetime import datetime


class OddsParser:
    """オッズデータのパーサークラス"""

    @staticmethod
    def parse_tansho_fukusho(buff: str) -> Dict:
        """
        単勝・複勝オッズ（O1レコード）をパース

        レコード仕様:
        - レコード種別ID: 位置1-2
        - データ区分: 位置3
        - レースキー: 位置4-19
        - オッズ時刻: 位置20-25
        - 単勝馬番・オッズ: 複数エントリ
        - 複勝馬番・オッズ: 複数エントリ

        Args:
            buff: データバッファ

        Returns:
            Dict: パースされた単勝・複勝オッズ
        """
        try:
            odds_data = {
                'record_type': '単勝・複勝オッズ',
                'record_id': buff[0:2].strip(),
                'data_kbn': buff[2:3].strip(),
                'race_key': buff[3:19].strip(),
                'odds_time': buff[19:25].strip(),
                'tansho': [],
                'fukusho': [],
                'parsed_at': datetime.now().isoformat()
            }

            # オッズ時刻をフォーマット
            if len(odds_data['odds_time']) == 6:
                time_str = odds_data['odds_time']
                odds_data['odds_time_formatted'] = f"{time_str[0:2]}:{time_str[2:4]}:{time_str[4:6]}"

            # 単勝オッズ部分のパース (位置26以降)
            # 実際の仕様に基づいて実装が必要
            # ここでは基本構造のみ示す
            tansho_start = 25
            for i in range(18):  # 最大18頭
                pos = tansho_start + (i * 7)
                if pos + 7 <= len(buff):
                    umaban = buff[pos:pos+2].strip()
                    odds = buff[pos+2:pos+7].strip()
                    if umaban and odds:
                        try:
                            odds_data['tansho'].append({
                                'umaban': int(umaban),
                                'odds': float(odds) / 10  # オッズは10倍値で格納
                            })
                        except ValueError:
                            continue

            # 複勝オッズ部分のパース
            fukusho_start = tansho_start + (18 * 7)
            for i in range(18):  # 最大18頭
                pos = fukusho_start + (i * 14)
                if pos + 14 <= len(buff):
                    umaban = buff[pos:pos+2].strip()
                    odds_min = buff[pos+2:pos+7].strip()
                    odds_max = buff[pos+7:pos+12].strip()
                    if umaban and odds_min and odds_max:
                        try:
                            odds_data['fukusho'].append({
                                'umaban': int(umaban),
                                'odds_min': float(odds_min) / 10,
                                'odds_max': float(odds_max) / 10
                            })
                        except ValueError:
                            continue

            return odds_data

        except Exception as e:
            return {
                'error': f'パースエラー: {e}',
                'raw_data': buff[:100]
            }

    @staticmethod
    def parse_wakuren(buff: str) -> Dict:
        """
        枠連オッズ（O2レコード）をパース

        Args:
            buff: データバッファ

        Returns:
            Dict: パースされた枠連オッズ
        """
        try:
            odds_data = {
                'record_type': '枠連オッズ',
                'record_id': buff[0:2].strip(),
                'data_kbn': buff[2:3].strip(),
                'race_key': buff[3:19].strip(),
                'odds_time': buff[19:25].strip(),
                'combinations': [],
                'parsed_at': datetime.now().isoformat()
            }

            # オッズ時刻をフォーマット
            if len(odds_data['odds_time']) == 6:
                time_str = odds_data['odds_time']
                odds_data['odds_time_formatted'] = f"{time_str[0:2]}:{time_str[2:4]}:{time_str[4:6]}"

            # 枠連オッズの組み合わせをパース
            # 実際の仕様書に基づいた実装が必要
            odds_start = 25
            combination_count = 36  # 枠連は最大36通り (8枠の組み合わせ)

            for i in range(combination_count):
                pos = odds_start + (i * 9)
                if pos + 9 <= len(buff):
                    waku1 = buff[pos:pos+1].strip()
                    waku2 = buff[pos+1:pos+2].strip()
                    odds = buff[pos+2:pos+7].strip()

                    if waku1 and waku2 and odds:
                        try:
                            odds_data['combinations'].append({
                                'waku1': int(waku1),
                                'waku2': int(waku2),
                                'odds': float(odds) / 10
                            })
                        except ValueError:
                            continue

            return odds_data

        except Exception as e:
            return {
                'error': f'パースエラー: {e}',
                'raw_data': buff[:100]
            }

    @staticmethod
    def parse_umaren(buff: str) -> Dict:
        """
        馬連オッズ（O3レコード）をパース

        Args:
            buff: データバッファ

        Returns:
            Dict: パースされた馬連オッズ
        """
        try:
            odds_data = {
                'record_type': '馬連オッズ',
                'record_id': buff[0:2].strip(),
                'data_kbn': buff[2:3].strip(),
                'race_key': buff[3:19].strip(),
                'odds_time': buff[19:25].strip(),
                'combinations': [],
                'parsed_at': datetime.now().isoformat()
            }

            return odds_data

        except Exception as e:
            return {
                'error': f'パースエラー: {e}',
                'raw_data': buff[:100]
            }

    @staticmethod
    def parse_wide(buff: str) -> Dict:
        """
        ワイドオッズ（O4レコード）をパース

        Args:
            buff: データバッファ

        Returns:
            Dict: パースされたワイドオッズ
        """
        try:
            odds_data = {
                'record_type': 'ワイドオッズ',
                'record_id': buff[0:2].strip(),
                'data_kbn': buff[2:3].strip(),
                'race_key': buff[3:19].strip(),
                'odds_time': buff[19:25].strip(),
                'combinations': [],
                'parsed_at': datetime.now().isoformat()
            }

            return odds_data

        except Exception as e:
            return {
                'error': f'パースエラー: {e}',
                'raw_data': buff[:100]
            }

    @staticmethod
    def parse_umatan(buff: str) -> Dict:
        """
        馬単オッズ（O5レコード）をパース

        Args:
            buff: データバッファ

        Returns:
            Dict: パースされた馬単オッズ
        """
        try:
            odds_data = {
                'record_type': '馬単オッズ',
                'record_id': buff[0:2].strip(),
                'data_kbn': buff[2:3].strip(),
                'race_key': buff[3:19].strip(),
                'odds_time': buff[19:25].strip(),
                'combinations': [],
                'parsed_at': datetime.now().isoformat()
            }

            return odds_data

        except Exception as e:
            return {
                'error': f'パースエラー: {e}',
                'raw_data': buff[:100]
            }

    @staticmethod
    def parse_sanrenpuku_sanrentan(buff: str) -> Dict:
        """
        三連複・三連単オッズ（O6レコード）をパース

        Args:
            buff: データバッファ

        Returns:
            Dict: パースされた三連複・三連単オッズ
        """
        try:
            # ヘッダー情報
            odds_data = {
                'record_type': '三連複・三連単オッズ',
                'record_id': buff[0:2].strip(),
                'data_kbn': buff[2:3].strip(),
                'race_key': buff[3:19].strip(),
                'odds_time': buff[19:25].strip() if len(buff) > 25 else '',
                'odds_data': {},
                'parsed_at': datetime.now().isoformat()
            }

            # オッズデータ部分の開始位置（ヘッダー40バイト）
            HEADER_LEN = 40
            ENTRY_LEN = 17  # 馬番6バイト + その他4バイト + オッズ7バイト

            if len(buff) <= HEADER_LEN:
                return odds_data

            odds_part = buff[HEADER_LEN:]

            # エントリをパース
            num_entries = len(odds_part) // ENTRY_LEN

            for i in range(num_entries):
                start = i * ENTRY_LEN
                end = start + ENTRY_LEN

                if end > len(odds_part):
                    break

                entry = odds_part[start:end]

                # 馬番（2バイト × 3）
                uma1 = entry[0:2].strip()
                uma2 = entry[2:4].strip()
                uma3 = entry[4:6].strip()

                # オッズ値（位置6-13の7バイト、10で割る）
                odds_str = entry[6:13].strip()

                if uma1 and uma2 and uma3 and odds_str:
                    try:
                        # 馬番の組み合わせをキーに
                        combo_key = f"{uma1}-{uma2}-{uma3}"

                        # オッズ値を計算
                        odds_value = float(odds_str) / 10.0

                        # 0.0倍のデータは除外（発売されていない組み合わせ）
                        if odds_value > 0.0:
                            odds_data['odds_data'][combo_key] = odds_value

                    except ValueError:
                        # パースエラーはスキップ
                        continue

            return odds_data

        except Exception as e:
            return {
                'error': f'パースエラー: {e}',
                'raw_data': buff[:100]
            }


def parse_jg_record(buff: str) -> Dict:
    """
    時系列オッズ情報（JGレコード）をパース

    Args:
        buff: データバッファ

    Returns:
        Dict: パースされた時系列オッズデータ
    """
    try:
        # JGレコードフォーマット:
        # JG[2] + データ区分[1] + 年月日[8] + レースID[16] + 発走時刻[4] + オッズ時刻[6] + データ...
        if len(buff) < 50:
            return None

        race_id = buff[11:27].strip() if len(buff) > 27 else ""
        post_time_raw = buff[27:31] if len(buff) > 31 else "1000"
        post_time = f"{post_time_raw[:2]}:{post_time_raw[2:]}" if len(post_time_raw) == 4 else "10:00"
        odds_time = buff[31:37] if len(buff) > 37 else ""

        # 時刻フォーマット
        odds_time_formatted = ""
        if len(odds_time) == 6:
            odds_time_formatted = f"{odds_time[0:2]}:{odds_time[2:4]}:{odds_time[4:6]}"

        return {
            'record_type': '時系列オッズ',
            'record_id': 'JG',
            'race_id': race_id,
            'post_time': post_time,
            'odds_time': odds_time,
            'odds_time_formatted': odds_time_formatted,
            'tansho': [],  # JGレコードには簡易オッズ情報が含まれる
            'fukusho': [],
            'raw_data': buff,
            'parsed_at': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'error': f'JGレコードパースエラー: {e}',
            'raw_data': buff[:100] if len(buff) > 100 else buff
        }


def parse_odds_record(record_id: str, buff: str) -> Dict:
    """
    オッズレコードをパース（統合関数）

    Args:
        record_id: レコードID (O1-O6, JG)
        buff: データバッファ

    Returns:
        Dict: パースされたオッズデータ
    """
    # JGレコードの場合
    if record_id == 'JG':
        return parse_jg_record(buff)

    parser = OddsParser()

    parsers = {
        'O1': parser.parse_tansho_fukusho,
        'O2': parser.parse_wakuren,
        'O3': parser.parse_umaren,
        'O4': parser.parse_wide,
        'O5': parser.parse_umatan,
        'O6': parser.parse_sanrenpuku_sanrentan
    }

    parser_func = parsers.get(record_id)
    if parser_func:
        return parser_func(buff)
    else:
        return {
            'error': f'未対応のレコードID: {record_id}',
            'raw_data': buff[:100]
        }


if __name__ == "__main__":
    # テスト用
    print("オッズパーサーモジュール")
    print("各レコードタイプのパーサーを提供します")
