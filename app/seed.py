"""Execute com python -m app.seed após aplicar as migrations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.database import SessionLocal
from app.models import Room, User


ROOMS = (
    {"name": "Sala 101", "capacity": 30, "location": "Bloco A - 1º andar"},
    {"name": "Sala 102", "capacity": 40, "location": "Bloco A - 1º andar"},
    {"name": "Laboratório de Informática", "capacity": 25, "location": "Bloco B - Térreo"},
    {"name": "Sala de Reuniões", "capacity": 10, "location": "Bloco C - Térreo"},
)


def seed_database(session: Session, settings: Settings) -> tuple[int, int]:
    """Insere os registros ausentes; a transação é controlada pelo chamador."""
    if not settings.admin_email or not settings.admin_email.strip() or not settings.admin_password:
        raise ValueError("Configure ADMIN_EMAIL e ADMIN_PASSWORD no .env antes de rodar o seed.")

    users_created = 0
    rooms_created = 0
    admin = session.scalar(select(User).where(User.email == settings.admin_email))
    if admin is None:
        session.add(User(
            name="Administrador",
            email=settings.admin_email,
            password_hash=hash_password(settings.admin_password),
            role="admin",
        ))
        users_created = 1

    for room_data in ROOMS:
        room = session.scalar(select(Room).where(Room.name == room_data["name"]))
        if room is None:
            session.add(Room(**room_data))
            rooms_created += 1

    session.flush()
    return users_created, rooms_created


def main() -> None:
    with SessionLocal.begin() as session:
        users_created, rooms_created = seed_database(session, get_settings())
    print(f"Seed concluído: {users_created} administrador(es) e {rooms_created} sala(s) criados.")


if __name__ == "__main__":
    main()
