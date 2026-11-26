from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Room


def list_rooms(session: Session, offset: int, size: int) -> tuple[list[Room], int]:
    # ORDER BY garante a mesma ordem entre páginas; total vem do COUNT
    items = list(
        session.scalars(select(Room).order_by(Room.id).offset(offset).limit(size))
    )
    total = session.scalar(select(func.count()).select_from(Room)) or 0
    return items, total


def get_room(session: Session, room_id: int) -> Room | None:
    return session.get(Room, room_id)


def get_room_by_name(session: Session, name: str) -> Room | None:
    return session.scalar(select(Room).where(Room.name == name))
