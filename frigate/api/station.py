"""Station apis."""

import logging

from fastapi import APIRouter, Request
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
