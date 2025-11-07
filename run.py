"""
JRA-VAN Odds API Server起動スクリプト
"""

if __name__ == "__main__":
    from src.api_server import app
    from src.config import Config
    import uvicorn
    import logging

    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("JRA-VAN Odds API Server")
    logger.info("=" * 60)
    logger.info(f"環境: {Config.ENVIRONMENT}")
    logger.info(f"ホスト: {Config.API_HOST}")
    logger.info(f"ポート: {Config.API_PORT}")
    logger.info(f"モックモード: {Config.USE_MOCK_DATA}")
    logger.info("=" * 60)

    uvicorn.run(
        app,
        host=Config.API_HOST,
        port=Config.API_PORT,
        log_level=Config.LOG_LEVEL.lower()
    )
