"""
JRA-VAN Odds API Server

FastAPIベースのREST APIサーバー
WebSocketによるリアルタイムオッズ配信をサポート
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .config import Config
from .data_service import get_data_service


class DataSourceEnum(str, Enum):
    """データソース選択"""
    AUTO = "auto"
    HISTORICAL = "historical"
    REALTIME = "realtime"
    MOCK = "mock"


# ロギング設定
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# FastAPIアプリケーション
app = FastAPI(
    title=Config.API_TITLE,
    version=Config.API_VERSION,
    description=Config.API_DESCRIPTION,
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# レスポンスモデル
class HealthResponse(BaseModel):
    """ヘルスチェックレスポンス"""
    status: str
    timestamp: str
    environment: str


class StatusResponse(BaseModel):
    """ステータスレスポンス"""
    service_status: Dict
    config: Dict
    timestamp: str


class RaceInfoResponse(BaseModel):
    """レース情報レスポンス"""
    date: str
    races: List[Dict]
    count: int


class OddsResponse(BaseModel):
    """オッズレスポンス"""
    race_id: str
    odds: List[Dict]
    count: int
    timestamp: str


class ErrorResponse(BaseModel):
    """エラーレスポンス"""
    error: str
    detail: Optional[str] = None
    timestamp: str


# WebSocket接続管理
class ConnectionManager:
    """WebSocket接続マネージャー"""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, race_id: str, websocket: WebSocket):
        """接続を追加"""
        await websocket.accept()
        if race_id not in self.active_connections:
            self.active_connections[race_id] = []
        self.active_connections[race_id].append(websocket)
        logger.info(f"WebSocket接続: race_id={race_id}, 接続数={len(self.active_connections[race_id])}")

    def disconnect(self, race_id: str, websocket: WebSocket):
        """接続を削除"""
        if race_id in self.active_connections:
            self.active_connections[race_id].remove(websocket)
            logger.info(f"WebSocket切断: race_id={race_id}, 接続数={len(self.active_connections[race_id])}")
            if not self.active_connections[race_id]:
                del self.active_connections[race_id]

    async def broadcast(self, race_id: str, message: dict):
        """指定レースの全接続にブロードキャスト"""
        if race_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[race_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"送信エラー: {e}")
                    disconnected.append(connection)

            # 切断されたコネクションを削除
            for conn in disconnected:
                self.disconnect(race_id, conn)


manager = ConnectionManager()


# データサービスの初期化
data_service = None


@app.on_event("startup")
async def startup_event():
    """起動時の処理"""
    global data_service
    logger.info("APIサーバーを起動します...")
    logger.info(f"環境: {Config.ENVIRONMENT}")
    logger.info(f"モックモード: {Config.USE_MOCK_DATA}")

    try:
        data_service = get_data_service()
        logger.info("データサービスの初期化完了")
    except Exception as e:
        logger.error(f"データサービス初期化エラー: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """終了時の処理"""
    logger.info("APIサーバーをシャットダウンします...")
    if data_service:
        data_service.close()


# REST API エンドポイント

@app.get("/", response_model=Dict)
async def root():
    """ルートエンドポイント"""
    return {
        "message": "JRA-VAN Odds API",
        "version": Config.API_VERSION,
        "environment": Config.ENVIRONMENT,
        "endpoints": {
            "health": "/api/health",
            "status": "/api/status",
            "races": "/api/races/{date}",
            "odds": "/api/odds/{race_id}",
            "race_detail": "/api/race/{race_id}",
            "websocket": "/ws/odds/{race_id}"
        }
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """ヘルスチェック"""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now().isoformat(),
        environment=Config.ENVIRONMENT
    )


@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """システムステータス"""
    return StatusResponse(
        service_status=data_service.get_status(),
        config=Config.get_info(),
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/races/{date}", response_model=RaceInfoResponse)
async def get_races(
    date: str,
    data_source: DataSourceEnum = Query(
        DataSourceEnum.AUTO,
        description="データソース (auto: 自動選択, historical: 過去データ, realtime: リアルタイム)"
    )
):
    """
    指定日のレース情報を取得

    Args:
        date: 日付 (YYYYMMDD形式)
        data_source: データソース
    """
    try:
        races = data_service.get_race_info(date, data_source=data_source.value)
        return RaceInfoResponse(
            date=date,
            races=races,
            count=len(races)
        )
    except Exception as e:
        logger.error(f"レース情報取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/odds/{race_id}")
async def get_odds(
    race_id: str,
    save: bool = Query(False, description="データを保存するか"),
    seconds_before_deadline: Optional[int] = Query(
        None,
        description="締め切りの何秒前のデータを取得するか（指定しない場合は最新データ）",
        ge=0
    ),
    data_source: DataSourceEnum = Query(
        DataSourceEnum.AUTO,
        description="データソース (auto: 自動選択, historical: 過去データ, realtime: リアルタイム)"
    )
):
    """
    指定レースのオッズを取得

    Args:
        race_id: レースID
        save: データを保存するか
        seconds_before_deadline: 締め切りの何秒前のデータを取得するか
        data_source: データソース
    """
    try:
        result = data_service.get_realtime_odds(
            race_id,
            seconds_before_deadline,
            data_source=data_source.value
        )

        if 'error' in result:
            raise HTTPException(
                status_code=404,
                detail=result['error']
            )

        odds_data = result.get('odds', [])

        if not odds_data:
            raise HTTPException(
                status_code=404,
                detail=f"レースID {race_id} のオッズが見つかりません"
            )

        # オッズデータを保存
        if save and Config.ENABLE_DATA_SAVE:
            data_service.save_odds_data(race_id, odds_data)

        # レスポンス構築
        response = {
            'race_id': race_id,
            'odds': odds_data,
            'count': len(odds_data),
            'timestamp': datetime.now().isoformat(),
            'is_past_data': result.get('is_past_data', False),
            'deadline_info': result.get('deadline_info', {}),
        }

        # 過去データの場合は警告メッセージを追加
        if result.get('past_data_note'):
            response['warning'] = result['past_data_note']
            response['time_status'] = result.get('time_status', '')

        if seconds_before_deadline is not None:
            response['seconds_before_deadline'] = seconds_before_deadline

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"オッズ取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/race/{race_id}")
async def get_race_detail(
    race_id: str,
    data_source: DataSourceEnum = Query(
        DataSourceEnum.AUTO,
        description="データソース (auto: 自動選択, historical: 過去データ, realtime: リアルタイム)"
    )
):
    """
    レース詳細情報を取得

    Args:
        race_id: レースID
        data_source: データソース
    """
    try:
        detail = data_service.get_race_detail(race_id, data_source=data_source.value)

        if not detail:
            raise HTTPException(
                status_code=404,
                detail=f"レースID {race_id} が見つかりません"
            )

        return detail

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"レース詳細取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/saved-odds/{race_id}")
async def get_saved_odds(race_id: str):
    """
    保存されたオッズデータを取得

    Args:
        race_id: レースID
    """
    try:
        odds = data_service.load_saved_odds(race_id)

        if not odds:
            raise HTTPException(
                status_code=404,
                detail=f"レースID {race_id} の保存データが見つかりません"
            )

        return {
            'race_id': race_id,
            'odds': odds,
            'count': len(odds)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存データ取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket エンドポイント

@app.websocket("/ws/odds/{race_id}")
async def websocket_odds(
    websocket: WebSocket,
    race_id: str,
    data_source: str = Query("auto", description="データソース")
):
    """
    リアルタイムオッズ配信WebSocket

    Args:
        websocket: WebSocket接続
        race_id: レースID
        data_source: データソース
    """
    await manager.connect(race_id, websocket)

    try:
        # 初回データ送信
        initial_result = data_service.get_realtime_odds(race_id, data_source=data_source)
        await websocket.send_json({
            'type': 'initial',
            'race_id': race_id,
            'odds': initial_result.get('odds', []),
            'is_past_data': initial_result.get('is_past_data', False),
            'deadline_info': initial_result.get('deadline_info', {}),
            'warning': initial_result.get('past_data_note'),
            'timestamp': datetime.now().isoformat()
        })

        # リアルタイム更新ループ
        while True:
            try:
                # クライアントからのメッセージを受信（ping/pong用）
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=Config.WS_PING_TIMEOUT
                )

                if data == "ping":
                    await websocket.send_text("pong")

            except asyncio.TimeoutError:
                # タイムアウト時は定期的にオッズを更新
                pass

            # オッズデータを取得して送信
            result = data_service.get_realtime_odds(race_id, data_source=data_source)
            if result.get('odds'):
                await websocket.send_json({
                    'type': 'update',
                    'race_id': race_id,
                    'odds': result.get('odds', []),
                    'is_past_data': result.get('is_past_data', False),
                    'deadline_info': result.get('deadline_info', {}),
                    'warning': result.get('past_data_note'),
                    'timestamp': datetime.now().isoformat()
                })

            # 更新間隔待機
            await asyncio.sleep(Config.REALTIME_UPDATE_INTERVAL)

    except WebSocketDisconnect:
        logger.info(f"WebSocket切断: race_id={race_id}")
        manager.disconnect(race_id, websocket)
    except Exception as e:
        logger.error(f"WebSocketエラー: {e}")
        manager.disconnect(race_id, websocket)


# エラーハンドラー

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """グローバル例外ハンドラー"""
    logger.error(f"予期しないエラー: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=str(exc),
            timestamp=datetime.now().isoformat()
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn

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
