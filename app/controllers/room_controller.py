from fastapi import APIRouter, Depends, Response, status

from app.controllers.dependencies import DbSession, get_pagination, require_admin
from app.schemas.common import Page, PaginationParams
from app.schemas.room import RoomIn, RoomOut
from app.usecases import room_usecases

router = APIRouter(prefix="/api/rooms", tags=["Salas"])

ADMIN_ONLY = [Depends(require_admin)]


@router.get("", response_model=Page[RoomOut])
def list_rooms(
    session: DbSession,
    pagination: PaginationParams = Depends(get_pagination),
):
    items, total = room_usecases.list_rooms(session, pagination)
    return Page(data=items, page=pagination.page, size=pagination.size, total=total)


@router.get("/{room_id}", response_model=RoomOut)
def get_room(room_id: int, session: DbSession):
    return room_usecases.get_room(session, room_id)


@router.post("", response_model=RoomOut, status_code=status.HTTP_201_CREATED, dependencies=ADMIN_ONLY)
def create_room(data: RoomIn, session: DbSession):
    return room_usecases.create_room(session, data)


@router.put("/{room_id}", response_model=RoomOut, dependencies=ADMIN_ONLY)
def update_room(room_id: int, data: RoomIn, session: DbSession):
    return room_usecases.update_room(session, room_id, data)


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=ADMIN_ONLY)
def delete_room(room_id: int, session: DbSession):
    room_usecases.delete_room(session, room_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
