import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

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
