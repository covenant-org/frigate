from pydantic import BaseModel

class StationPostCreateBody(BaseModel):
    id: str
