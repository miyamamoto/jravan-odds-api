"""
包括的テスト（historical provider有効版）
"""

import sys
import os

# 環境変数を設定してhistoricalデータを有効化
os.environ['ENABLE_HISTORICAL_DATA'] = 'true'
os.environ['HISTORICAL_CACHE_DIR'] = './historical_cache'

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# test_comprehensive.pyのテストクラスをインポート
from test_comprehensive import ComprehensiveTest

def main():
    """メイン関数"""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE TEST WITH HISTORICAL PROVIDER ENABLED")
    print("=" * 80)
    print()

    test = ComprehensiveTest()
    exit_code = test.run_all_tests()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
