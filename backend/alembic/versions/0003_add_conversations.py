"""Add conversations, messages, users, ai_alerts tables

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(200)),
        sa.Column("plan", sa.String(20), server_default="FREE"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, nullable=True),
        sa.Column("title", sa.String(500)),
        sa.Column("symbol", sa.String(20)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("conversation_id", sa.Integer, nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text),
        sa.Column("tool_calls", sa.JSON),
        sa.Column("tool_results", sa.JSON),
        sa.Column("tokens_used", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_messages_conversation_id", "messages", ["conversation_id"]
    )

    op.create_table(
        "ai_alerts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, nullable=True),
        sa.Column("symbol", sa.String(20)),
        sa.Column("alert_type", sa.String(50)),
        sa.Column("severity", sa.String(20)),
        sa.Column("title", sa.String(500)),
        sa.Column("summary", sa.Text),
        sa.Column("data", sa.JSON),
        sa.Column("is_read", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_ai_alerts_symbol", "ai_alerts", ["symbol"])
    op.create_index("ix_ai_alerts_user_id", "ai_alerts", ["user_id"])


def downgrade():
    op.drop_table("ai_alerts")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("users")
