from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Room
from app.repositories import room_repository
from app.schemas.room import RoomIn

DUPLICATE_NAME = "Já existe uma sala com esse nome."


def list_rooms(session: Session) -> list[Room]:
    return room_repository.list_rooms(session)


def get_room(session: Session, room_id: int) -> Room:
    room = room_repository.get_room(session, room_id)
    if room is None:
        raise NotFoundError("Sala não encontrada.")
    return room


def create_room(session: Session, data: RoomIn) -> Room:
    if room_repository.get_room_by_name(session, data.name):
        raise ConflictError(DUPLICATE_NAME)

    room = Room(**data.model_dump())
    session.add(room)
    _commit(session, DUPLICATE_NAME)
    return room


def update_room(session: Session, room_id: int, data: RoomIn) -> Room:
    room = get_room(session, room_id)
    same_name = room_repository.get_room_by_name(session, data.name)
    if same_name is not None and same_name.id != room.id:
        raise ConflictError(DUPLICATE_NAME)

    for field, value in data.model_dump().items():
        setattr(room, field, value)
    _commit(session, DUPLICATE_NAME)
    return room


def delete_room(session: Session, room_id: int) -> None:
    room = get_room(session, room_id)
    session.delete(room)
    _commit(session, "A sala possui reservas vinculadas e não pode ser excluída.")


def _commit(session: Session, conflict_message: str) -> None:
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ConflictError(conflict_message)
