from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Room


def list_rooms(session: Session) -> list[Room]:
    return list(session.scalars(select(Room).order_by(Room.id)))


def get_room(session: Session, room_id: int) -> Room | None:
    return session.get(Room, room_id)


def get_room_by_name(session: Session, name: str) -> Room | None:
    return session.scalar(select(Room).where(Room.name == name))
