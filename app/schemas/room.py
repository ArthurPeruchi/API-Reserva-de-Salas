from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)]
Location = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class RoomIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Name
    capacity: int = Field(gt=0, le=10_000)
    location: Location


class RoomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    capacity: int
    location: str
