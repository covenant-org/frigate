"""Station apis."""

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from frigate.api.defs.request.clip import PreSignedFileBody
from frigate.api.defs.tags import Tags
from frigate.api.providers.base import FileMetadata

logger = logging.getLogger(__name__)

router = APIRouter(tags=[Tags.clip])


@router.post("/pre-sign")
async def pre_sign(
    request: Request,
    body: PreSignedFileBody,
):
    metadata = FileMetadata()
    metadata.max_size_mb = body.max_size_mb
    metadata.camera_id = body.camera_id
    metadata.date = body.date
    metadata.station_id = body.station_id
    metadata.name = body.station_id

    result = request.app.file_provider.presigned_url(metadata)
    return JSONResponse(content={"url": result.url})
