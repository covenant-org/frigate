"""Station apis."""

import logging

from fastapi import APIRouter, Request, WebSocket
from fastapi.responses import JSONResponse

from frigate.api.defs.request.station import StationPostCreateBody
from frigate.api.defs.tags import Tags
from frigate.models import Station

logger = logging.getLogger(__name__)

router = APIRouter(tags=[Tags.station])


@router.post("/station")
async def create(
    _: Request,
    body: StationPostCreateBody,
):
    Station.create(id=body.id)
    return JSONResponse(content={"id": body.id})


@router.websocket("/station/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()
