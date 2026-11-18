from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base

if TYPE_CHECKING:
    from .room import Room
    from .user import User


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", name="fk_reservations_room", ondelete="RESTRICT"),
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_reservations_user", ondelete="RESTRICT"),
        index=True,
    )
    start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str] = mapped_column(Text)

    room: Mapped["Room"] = relationship(back_populates="reservations")
    user: Mapped["User"] = relationship(back_populates="reservations")
