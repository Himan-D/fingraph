"""Add commodity, social, and pipeline tables

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
        sa.Column("commodity_id", sa.Integer, index=True),
        sa.Column("timestamp", sa.DateTime, nullable=False, index=True),
        sa.Column("open", sa.Float),
        sa.Column("high", sa.Float),
        sa.Column("low", sa.Float),
        sa.Column("close", sa.Float),
        sa.Column("settlement", sa.Float),
        sa.Column("previous_close", sa.Float),
        sa.Column("change", sa.Float),
        sa.Column("change_pct", sa.Float),
        sa.Column("volume", sa.BigInteger),
        sa.Column("open_interest", sa.BigInteger),
        sa.Column("delivery", sa.Float),
        sa.Column("turnover", sa.Float),
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
        sa.Column("sentiment_score", sa.Float),
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
        sa.Column("sentiment_score", sa.Float),
        sa.Column("mention_count", sa.Integer, default=0),
        sa.Column("bullish_count", sa.Integer, default=0),
        sa.Column("bearish_count", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "index_quotes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(20), index=True),
        sa.Column("name", sa.String(100)),
        sa.Column("price", sa.Float),
        sa.Column("change", sa.Float),
        sa.Column("pct_change", sa.Float),
        sa.Column("timestamp", sa.DateTime, nullable=False, index=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "option_chain_records",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(20), index=True),
        sa.Column("expiry_date", sa.Date),
        sa.Column("strike_price", sa.Float),
        sa.Column("option_type", sa.String(5)),
        sa.Column("last_price", sa.Float),
        sa.Column("open_interest", sa.BigInteger),
        sa.Column("volume", sa.BigInteger),
        sa.Column("iv", sa.Float),
        sa.Column("delta", sa.Float),
        sa.Column("gamma", sa.Float),
        sa.Column("theta", sa.Float),
        sa.Column("vega", sa.Float),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "stock_inventory",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(20), unique=True, nullable=False, index=True),
        sa.Column("is_active", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("stock_inventory")
    op.drop_table("option_chain_records")
    op.drop_table("index_quotes")
    op.drop_table("social_sentiment")
    op.drop_table("reddit_posts")
    op.drop_table("twitter_posts")
    op.drop_table("commodity_sentiment")
    op.drop_table("commodity_news")
    op.drop_table("commodity_prices")
    op.drop_table("commodities")
