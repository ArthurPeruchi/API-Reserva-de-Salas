from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base

if TYPE_CHECKING:
    from .reservation import Reservation


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    capacity: Mapped[int]
    location: Mapped[str] = mapped_column(String(255))

    reservations: Mapped[list["Reservation"]] = relationship(
        back_populates="room", passive_deletes="all"
    )
