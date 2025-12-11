from pydantic import BaseModel


class PreSignedFileBody(BaseModel):
    station_id: str
    camera_id: str
    date: str
    max_size_mb: int
