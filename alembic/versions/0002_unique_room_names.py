"""Impede nomes duplicados de salas sem recriar a tabela referenciada por reservas."""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_rooms_name", "rooms", ["name"], unique=True)


def downgrade():
    op.drop_index("ix_rooms_name", table_name="rooms")
