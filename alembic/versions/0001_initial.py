"""Cria usuários, salas e reservas."""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(5), server_default="user", nullable=False),
        sa.CheckConstraint("role IN ('user', 'admin')", name="ck_users_role"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("location", sa.String(255), nullable=False),
    )
    op.create_table(
        "reservations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["room_id"], ["rooms.id"], name="fk_reservations_room", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_reservations_user", ondelete="RESTRICT"
        ),
    )
    op.create_index("ix_reservations_room_id", "reservations", ["room_id"])
    op.create_index("ix_reservations_user_id", "reservations", ["user_id"])


def downgrade():
    op.drop_index("ix_reservations_user_id", table_name="reservations")
    op.drop_index("ix_reservations_room_id", table_name="reservations")
    op.drop_table("reservations")
    op.drop_table("rooms")
    op.drop_table("users")
