from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.infrastructure.database import Base, engine
from app.models import Reservation, Room, User

URL = "/api/rooms"
ROOM = {"name": "Sala 101", "capacity": 30, "location": "Bloco A"}


@pytest.fixture
def users(client):
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        admin = User(name="Admin", email="admin@example.com", password_hash="x", role="admin")
        common = User(name="Comum", email="comum@example.com", password_hash="x", role="user")
        session.add_all([admin, common])
        session.commit()
        ids = {"admin": admin.id, "user": common.id}
    yield ids
    Base.metadata.drop_all(engine)


@pytest.fixture
def admin(users):
    return {"X-User-Id": str(users["admin"])}


def create(client, admin, **overrides):
    response = client.post(URL, json={**ROOM, **overrides}, headers=admin)
    assert response.status_code == 201, response.text
    return response.json()


def test_full_crud_flow(client, admin):
    created = create(client, admin, name="  Sala 101  ")
    assert created == {"id": created["id"], **ROOM}  # nome sem espaços extras

    assert client.get(URL).json() == {"data": [created], "page": 1, "size": 10, "total": 1}
    assert client.get(f"{URL}/{created['id']}").json() == created

    changes = {"name": "Lab 1", "capacity": 20, "location": "Bloco B"}
    response = client.put(f"{URL}/{created['id']}", json=changes, headers=admin)
    assert response.status_code == 200
    assert response.json() == {"id": created["id"], **changes}

    response = client.delete(f"{URL}/{created['id']}", headers=admin)
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(URL).json()["data"] == []


def test_list_is_paginated(client, admin):
    for number in range(1, 4):
        create(client, admin, name=f"Sala {number}")

    response = client.get(URL, params={"page": 2, "size": 2})
    assert response.status_code == 200
    body = response.json()
    assert [room["name"] for room in body["data"]] == ["Sala 3"]
    assert (body["page"], body["size"], body["total"]) == (2, 2, 3)

    assert client.get(URL, params={"page": 3, "size": 2}).json()["data"] == []
    assert client.get(URL, params={"page": 0}).status_code == 422
    assert client.get(URL, params={"size": 101}).status_code == 422


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_missing_room_returns_404(client, admin, method):
    response = client.request(method, f"{URL}/999", json=ROOM, headers=admin)
    assert response.status_code == 404
    assert response.json() == {"status": 404, "message": "Sala não encontrada."}


@pytest.mark.parametrize("payload", [
    {**ROOM, "capacity": 0},
    {**ROOM, "capacity": "muitos"},
    {**ROOM, "name": "   "},
    {**ROOM, "name": "x" * 151},
    {**ROOM, "extra": True},
    {"name": "Sala sem capacidade", "location": "Bloco A"},
])
def test_invalid_payload_returns_422(client, admin, payload):
    response = client.post(URL, json=payload, headers=admin)
    assert response.status_code == 422
    assert response.json()["message"] == "Dados inválidos."


def test_validation_errors_are_listed_by_field(client, admin):
    response = client.post(URL, json={**ROOM, "name": "", "capacity": 0}, headers=admin)
    assert response.json()["errors"] == [
        {"field": "name", "message": "Deve ter no mínimo 1 caractere(s)."},
        {"field": "capacity", "message": "Deve ser maior que 0."},
    ]


def test_duplicate_name_returns_409(client, admin):
    create(client, admin)
    other = create(client, admin, name="Sala 102")

    assert client.post(URL, json=ROOM, headers=admin).status_code == 409
    response = client.put(f"{URL}/{other['id']}", json=ROOM, headers=admin)
    assert response.status_code == 409
    assert response.json() == {"status": 409, "message": "Já existe uma sala com esse nome."}

    # Manter o próprio nome numa atualização não é conflito.
    response = client.put(f"{URL}/{other['id']}", json={**ROOM, "name": "Sala 102"}, headers=admin)
    assert response.status_code == 200


def test_room_with_reservations_cannot_be_deleted(client, admin, users):
    room = create(client, admin)
    with Session(engine) as session:
        session.add(Reservation(
            room_id=room["id"], user_id=users["user"], reason="Aula",
            start=datetime(2030, 1, 1, 10), end=datetime(2030, 1, 1, 11),
        ))
        session.commit()

    response = client.delete(f"{URL}/{room['id']}", headers=admin)
    assert response.status_code == 409
    assert response.json() == {"status": 409, "message": "A sala possui reservas."}
    assert client.get(f"{URL}/{room['id']}").status_code == 200


@pytest.mark.parametrize("headers,expected", [
    ({}, 401),
    ({"X-User-Id": "999"}, 401),
    ("user", 403),
])
def test_write_routes_require_admin(client, users, headers, expected):
    if headers == "user":
        headers = {"X-User-Id": str(users["user"])}
    with Session(engine) as session:
        session.add(Room(**ROOM))
        session.commit()

    for response in (
        client.post(URL, json={**ROOM, "name": "Nova"}, headers=headers),
        client.put(f"{URL}/1", json=ROOM, headers=headers),
        client.delete(f"{URL}/1", headers=headers),
    ):
        assert response.status_code == expected
        assert response.json()["status"] == expected
    # Leitura continua pública e nada foi alterado.
    assert client.get(URL).json()["data"] == [{"id": 1, **ROOM}]
