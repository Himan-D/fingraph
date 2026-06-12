"""Add production indexes for hot paths

Revision ID: 0004
Revises: 0003
"""
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix_stock_quotes_company_timestamp",
        "stock_quotes",
        ["company_id", "timestamp"],
    )
    op.create_index(
        "ix_messages_conv_created",
        "messages",
        ["conversation_id", "created_at"],
    )
    op.create_index(
        "ix_ai_alerts_user_read",
        "ai_alerts",
        ["user_id", "is_read"],
    )
    op.create_index(
        "ix_news_published",
        "news_articles",
        ["published_at"],
    )
    op.create_index(
        "ix_social_sentiment_symbol_date",
        "social_sentiment",
        ["symbol", "date"],
    )
    op.create_index(
        "ix_fundamentals_company",
        "fundamentals",
        ["company_id"],
    )


def downgrade():
    op.drop_index("ix_fundamentals_company")
    op.drop_index("ix_social_sentiment_symbol_date")
    op.drop_index("ix_news_published")
    op.drop_index("ix_ai_alerts_user_read")
    op.drop_index("ix_messages_conv_created")
    op.drop_index("ix_stock_quotes_company_timestamp")
