"""Add commodity tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-08 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "commodities",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(20), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("exchange", sa.String(20)),
        sa.Column("category", sa.String(50)),
        sa.Column("unit", sa.String(20)),
        sa.Column("description", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "commodity_prices",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "commodity_id",
            sa.Integer,
            sa.ForeignKey("commodities.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("timestamp", sa.DateTime, nullable=False, index=True),
        sa.Column("open", sa.Numeric(12, 2)),
        sa.Column("high", sa.Numeric(12, 2)),
        sa.Column("low", sa.Numeric(12, 2)),
        sa.Column("close", sa.Numeric(12, 2)),
        sa.Column("settlement", sa.Numeric(12, 2)),
        sa.Column("previous_close", sa.Numeric(12, 2)),
        sa.Column("change", sa.Numeric(12, 2)),
        sa.Column("change_pct", sa.Numeric(8, 2)),
        sa.Column("volume", sa.BigInteger),
        sa.Column("open_interest", sa.BigInteger),
        sa.Column("delivery", sa.Numeric(8, 2)),
        sa.Column("turnover", sa.Numeric(12, 2)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "commodity_news",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("headline", sa.Text),
        sa.Column("summary", sa.Text),
        sa.Column("source", sa.String(100)),
        sa.Column("url", sa.String(1000)),
        sa.Column("commodities", sa.JSON),
        sa.Column("published_at", sa.DateTime),
        sa.Column("sentiment", sa.String(20)),
        sa.Column("tags", sa.JSON),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "commodity_sentiment",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("commodity_symbol", sa.String(20), index=True),
        sa.Column("date", sa.Date, index=True),
        sa.Column("source", sa.String(20)),
        sa.Column("sentiment_score", sa.Numeric(8, 2)),
        sa.Column("mention_count", sa.Integer, default=0),
        sa.Column("bullish_count", sa.Integer, default=0),
        sa.Column("bearish_count", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "twitter_posts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("post_id", sa.String(100), unique=True),
        sa.Column("username", sa.String(100), index=True),
        sa.Column("text", sa.Text),
        sa.Column("source", sa.String(50)),
        sa.Column("symbol", sa.String(20)),
        sa.Column("timestamp", sa.DateTime, index=True),
        sa.Column("likes", sa.Integer, default=0),
        sa.Column("retweets", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "reddit_posts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("post_id", sa.String(100), unique=True),
        sa.Column("title", sa.Text),
        sa.Column("text", sa.Text),
        sa.Column("author", sa.String(100), index=True),
        sa.Column("subreddit", sa.String(50), index=True),
        sa.Column("url", sa.String(1000)),
        sa.Column("score", sa.Integer, default=0),
        sa.Column("num_comments", sa.Integer, default=0),
        sa.Column("symbols", sa.JSON),
        sa.Column("timestamp", sa.DateTime, index=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "social_sentiment",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(20), index=True),
        sa.Column("date", sa.Date, index=True),
        sa.Column("source", sa.String(20)),
        sa.Column("sentiment_score", sa.Numeric(8, 2)),
        sa.Column("mention_count", sa.Integer, default=0),
        sa.Column("bullish_count", sa.Integer, default=0),
        sa.Column("bearish_count", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("social_sentiment")
    op.drop_table("reddit_posts")
    op.drop_table("twitter_posts")
    op.drop_table("commodity_sentiment")
    op.drop_table("commodity_news")
    op.drop_table("commodity_prices")
    op.drop_table("commodities")
