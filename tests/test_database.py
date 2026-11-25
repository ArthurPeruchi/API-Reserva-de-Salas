from datetime import datetime, timedelta

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.infrastructure.database import create_database_engine
from app.models import Reservation, Room, User


@pytest.fixture
def migrated_engine(tmp_path, monkeypatch):
    engine = create_database_engine(f"sqlite:///{tmp_path / 'test.db'}")
    # Alembic lê o mesmo engine isolado usado nas verificações.
    monkeypatch.setattr("app.infrastructure.database.engine", engine)
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    yield engine, config
    engine.dispose()


def test_migration_round_trip(migrated_engine):
    engine, config = migrated_engine
    assert {"users", "rooms", "reservations"} <= set(inspect(engine).get_table_names())
    command.check(config)
    command.downgrade(config, "base")
    assert set(inspect(engine).get_table_names()) == {"alembic_version"}
    command.upgrade(config, "head")
    assert {"users", "rooms", "reservations"} <= set(inspect(engine).get_table_names())


def test_email_unique(migrated_engine):
    engine, _ = migrated_engine
    with Session(engine) as session:
        session.add(User(name="A", email="a@example.com", password_hash="test-hash"))
        session.commit()
        session.add(User(name="B", email="a@example.com", password_hash="test-hash"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        assert len(session.scalars(select(User)).all()) == 1


def test_room_name_unique(migrated_engine):
    engine, _ = migrated_engine
    with Session(engine) as session:
        session.add(Room(name="Sala 101", capacity=30, location="Bloco A"))
        session.commit()
        session.add(Room(name="Sala 101", capacity=40, location="Bloco B"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        room = session.scalars(select(Room)).one()
        assert (room.name, room.capacity, room.location) == ("Sala 101", 30, "Bloco A")


def test_unique_room_migration_preserves_rooms_and_reservations(migrated_engine):
    engine, config = migrated_engine
    command.downgrade(config, "0001")
    with Session(engine) as session:
        room = Room(name="Sala existente", capacity=20, location="Bloco A")
        user = User(name="A", email="a@example.com", password_hash="test-hash")
        reservation = Reservation(
            room=room, user=user, start=datetime(2030, 1, 1, 10),
            end=datetime(2030, 1, 1, 11), reason="Aula",
        )
        session.add(reservation)
        session.commit()
        room_id, reservation_id = room.id, reservation.id

    for revision in ("head", "0001", "head"):
        command.upgrade(config, revision) if revision == "head" else command.downgrade(config, revision)
        with Session(engine) as session:
            assert session.get(Room, room_id).name == "Sala existente"
            assert session.get(Reservation, reservation_id).room_id == room_id
            assert session.connection().exec_driver_sql("PRAGMA foreign_key_check").all() == []
    command.check(config)


def test_unique_room_migration_rejects_existing_duplicates_without_deleting(migrated_engine):
    engine, config = migrated_engine
    command.downgrade(config, "0001")
    with Session(engine) as session:
        session.add_all([
            Room(name="Duplicada", capacity=20, location="Bloco A"),
            Room(name="Duplicada", capacity=30, location="Bloco B"),
        ])
        session.commit()
    with pytest.raises(IntegrityError):
        command.upgrade(config, "head")
    with Session(engine) as session:
        assert len(session.scalars(select(Room)).all()) == 2
        assert session.connection().exec_driver_sql("SELECT version_num FROM alembic_version").scalar() == "0001"


def test_reservation_requires_existing_parents(migrated_engine):
    engine, _ = migrated_engine
    with Session(engine) as session:
        assert session.connection().exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
        session.add(Reservation(
            room_id=999, user_id=999, start=datetime(2030, 1, 1, 10),
            end=datetime(2030, 1, 1, 11), reason="Teste",
        ))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


@pytest.mark.parametrize("loaded", [False, True])
def test_room_with_reservations_cannot_be_deleted(migrated_engine, loaded):
    engine, _ = migrated_engine
    with Session(engine) as session:
        room = Room(name="Laboratório", capacity=20, location="Bloco A")
        user = User(name="A", email="a@example.com", password_hash="test-hash")
        start = datetime(2030, 1, 1, 10)
        reservation = Reservation(
            room=room, user=user, start=start, end=start + timedelta(hours=1),
            reason="Aula",
        )
        session.add(reservation)
        session.commit()
        room_id, reservation_id = room.id, reservation.id
        if loaded:
            assert room.reservations == [reservation]
        session.delete(room)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        assert session.get(Room, room_id) is not None
        assert session.get(Reservation, reservation_id).room_id == room_id
