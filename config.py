"""
設定ファイル

環境変数またはこのファイルで設定を管理
"""

import os
from enum import Enum


class Environment(str, Enum):
    """実行環境"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class Config:
    """アプリケーション設定"""

    # 環境設定
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

    # JRA-VAN設定
    JRAVAN_SERVICE_KEY = os.getenv("JRAVAN_SERVICE_KEY", "UNKNOWN")

    # API設定
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_TITLE = "JRA-VAN Odds API"
    API_VERSION = "1.0.0"
    API_DESCRIPTION = "JRA-VAN競馬リアルタイムオッズ取得API"

    # CORS設定
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

    # データキャッシュ設定
    ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    CACHE_DIR = os.getenv("CACHE_DIR", "./cache")
    CACHE_TTL = int(os.getenv("CACHE_TTL", "60"))  # 秒

    # データ保存設定
    ENABLE_DATA_SAVE = os.getenv("ENABLE_DATA_SAVE", "true").lower() == "true"
    DATA_DIR = os.getenv("DATA_DIR", "./data")

    # WebSocket設定
    WS_PING_INTERVAL = int(os.getenv("WS_PING_INTERVAL", "30"))  # 秒
    WS_PING_TIMEOUT = int(os.getenv("WS_PING_TIMEOUT", "10"))  # 秒

    # リアルタイム更新設定
    REALTIME_UPDATE_INTERVAL = int(os.getenv("REALTIME_UPDATE_INTERVAL", "10"))  # 秒

    # ログ設定
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "jravan_api.log")

    # 開発モード設定
    USE_MOCK_DATA = ENVIRONMENT == Environment.DEVELOPMENT
    MOCK_DATA_FILE = os.getenv("MOCK_DATA_FILE", "./mock_data/sample_odds.json")

    @classmethod
    def is_development(cls) -> bool:
        """開発環境かどうか"""
        return cls.ENVIRONMENT == Environment.DEVELOPMENT

    @classmethod
    def is_production(cls) -> bool:
        """本番環境かどうか"""
        return cls.ENVIRONMENT == Environment.PRODUCTION

    @classmethod
    def get_info(cls) -> dict:
        """設定情報を取得"""
        return {
            "environment": cls.ENVIRONMENT,
            "use_mock_data": cls.USE_MOCK_DATA,
            "cache_enabled": cls.ENABLE_CACHE,
            "data_save_enabled": cls.ENABLE_DATA_SAVE,
            "api_host": cls.API_HOST,
            "api_port": cls.API_PORT,
        }


# 環境変数からの設定読み込み
def load_env_file(filepath: str = ".env"):
    """
    .envファイルから環境変数を読み込む

    Args:
        filepath: .envファイルのパス
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    except FileNotFoundError:
        pass  # .envファイルがなければスキップ


# .envファイルの読み込みを試行
load_env_file()
