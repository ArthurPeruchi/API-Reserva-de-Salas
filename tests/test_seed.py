import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app import seed
from app.core.security import hash_password, verify_password
from app.infrastructure.config import Settings
from app.infrastructure.database import Base, create_database_engine
from app.models import Room, User
from app.seed import ROOMS, seed_database


@pytest.fixture
def seed_engine():
    engine = create_database_engine("sqlite://")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def settings():
    return Settings(
        _env_file=None, database_url="sqlite://",
        admin_email="admin@example.com", admin_password="Senha-teste-123",
    )


def test_seed_preserves_existing_records_and_fills_missing_rooms(seed_engine, settings):
    original_hash = hash_password("senha-original")
    with Session(seed_engine) as session, session.begin():
        session.add(User(name="Admin existente", email=settings.admin_email,
                         password_hash=original_hash, role="admin"))
        session.add(Room(name=ROOMS[0]["name"], capacity=99, location="Local editado"))

    with Session(seed_engine) as session, session.begin():
        assert seed_database(session, settings) == (0, 3)

    with Session(seed_engine) as session, session.begin():
        assert seed_database(session, settings) == (0, 0)
        admin = session.scalar(select(User))
        assert admin.name == "Admin existente"
        assert admin.password_hash == original_hash
        rooms = session.scalars(select(Room)).all()
        assert len(rooms) == 4
        existing = next(room for room in rooms if room.name == ROOMS[0]["name"])
        assert (existing.capacity, existing.location) == (99, "Local editado")


@pytest.mark.parametrize("field", ["admin_email", "admin_password"])
def test_seed_requires_credentials_before_writing(seed_engine, settings, field):
    setattr(settings, field, None)
    with Session(seed_engine) as session:
        with pytest.raises(ValueError, match="ADMIN_EMAIL e ADMIN_PASSWORD"):
            seed_database(session, settings)
        assert session.scalars(select(User)).all() == []
        assert session.scalars(select(Room)).all() == []


@pytest.mark.parametrize("conflicting_model,expected_counts", [
    (Room, "1 administrador(es) e 3 sala(s)"),
    (User, "0 administrador(es) e 4 sala(s)"),
])
def test_seed_recovers_from_duplicate_insert(
    seed_engine, settings, monkeypatch, capsys, conflicting_model, expected_counts,
):
    with Session(seed_engine) as session, session.begin():
        if conflicting_model is Room:
            session.add(Room(name=ROOMS[0]["name"], capacity=99, location="Existente"))
        else:
            session.add(User(name="Existente", email=settings.admin_email,
                             password_hash="hash-preservado", role="admin"))

    original_scalar = Session.scalar
    stale_read = False

    def scalar_with_stale_read(session, statement, *args, **kwargs):
        nonlocal stale_read
        if not stale_read and statement.column_descriptions[0]["entity"] is conflicting_model:
            # Simula a consulta que não viu a inserção concorrente. O INSERT
            # seguinte deve provocar um IntegrityError real no banco.
            stale_read = True
            return None
        return original_scalar(session, statement, *args, **kwargs)

    monkeypatch.setattr(Session, "scalar", scalar_with_stale_read)
    monkeypatch.setattr(seed, "SessionLocal", sessionmaker(bind=seed_engine))
    monkeypatch.setattr(seed, "get_settings", lambda: settings)
    seed.main()
    assert stale_read
    assert expected_counts in capsys.readouterr().out
    with Session(seed_engine) as session:
        users = session.scalars(select(User)).all()
        rooms = session.scalars(select(Room)).all()
        assert len(users) == 1
        assert len(rooms) == 4
        assert {room.name for room in rooms} == {room["name"] for room in ROOMS}
        if conflicting_model is Room:
            existing = next(room for room in rooms if room.name == ROOMS[0]["name"])
            assert (existing.capacity, existing.location) == (99, "Existente")
        else:
            assert users[0].password_hash == "hash-preservado"


def test_seed_persistent_integrity_error_rolls_back_and_is_reported(
    seed_engine, settings, monkeypatch, capsys,
):
    attempts = 0

    def invalid_seed(session, settings):
        nonlocal attempts
        attempts += 1
        session.add(Room(name="Válida", capacity=20, location="Bloco A"))
        session.flush()
        session.add(Room(name="Inválida", capacity=None, location="Bloco A"))
        session.flush()

    monkeypatch.setattr(seed, "seed_database", invalid_seed)
    monkeypatch.setattr(seed, "SessionLocal", sessionmaker(bind=seed_engine))
    monkeypatch.setattr(seed, "get_settings", lambda: settings)
    with pytest.raises(IntegrityError):
        seed.main()
    assert attempts == len(ROOMS) + 2
    assert "Seed concluído" not in capsys.readouterr().out
    with Session(seed_engine) as session:
        assert session.scalars(select(Room)).all() == []


def test_seed_cli_reads_dotenv_and_is_idempotent(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    database_url = f"sqlite:///{tmp_path / 'seed.db'}"
    (tmp_path / ".env").write_text(
        f"DATABASE_URL={database_url}\n"
        "ADMIN_EMAIL=seed@example.com\nADMIN_PASSWORD=Senha-do-dotenv-123\n",
        encoding="utf-8",
    )
    env = {key: value for key, value in os.environ.items()
           if key.upper() not in {"DATABASE_URL", "ADMIN_EMAIL", "ADMIN_PASSWORD"}}
    env["PYTHONPATH"] = str(project_root)
    migration = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(project_root / "alembic.ini"),
         "upgrade", "head"], cwd=tmp_path, env=env, capture_output=True, text=True,
    )
    assert migration.returncode == 0, migration.stdout + migration.stderr

    hashes = []
    engine = create_database_engine(database_url)
    try:
        for expected_counts in ("1 administrador(es) e 4 sala(s)", "0 administrador(es) e 0 sala(s)"):
            result = subprocess.run(
                [sys.executable, "-m", "app.seed"], cwd=tmp_path, env=env,
                capture_output=True, text=True,
            )
            assert result.returncode == 0, result.stdout + result.stderr
            assert expected_counts in result.stdout
            with Session(engine) as session:
                users = session.scalars(select(User)).all()
                assert len(users) == 1
                admin = users[0]
                assert (admin.email, admin.role) == ("seed@example.com", "admin")
                assert admin.password_hash != "Senha-do-dotenv-123"
                assert verify_password("Senha-do-dotenv-123", admin.password_hash)
                hashes.append(admin.password_hash)
                rooms = session.scalars(select(Room)).all()
                assert {room.name for room in rooms} == {room["name"] for room in ROOMS}
                assert len(rooms) == 4
                assert all(room.capacity > 0 and room.location for room in rooms)
        assert hashes[0] == hashes[1]
    finally:
        engine.dispose()
