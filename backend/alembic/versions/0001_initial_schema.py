"""Initial schema — all tables from postgres_models.py

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(20), unique=True, nullable=False, index=True),
        sa.Column("nse_code", sa.String(20)),
        sa.Column("bse_code", sa.String(20)),
        sa.Column("name", sa.String(500)),
        sa.Column("isin", sa.String(50)),
        sa.Column("sector", sa.String(100)),
        sa.Column("industry", sa.String(200)),
        sa.Column("market_cap", sa.Float),
        sa.Column("description", sa.Text),
        sa.Column("listing_date", sa.Date),
        sa.Column("face_value", sa.Float, default=10.0),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "stock_quotes",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer, index=True),
        sa.Column("timestamp", sa.DateTime, nullable=False, index=True),
        sa.Column("open", sa.Float),
        sa.Column("high", sa.Float),
        sa.Column("low", sa.Float),
        sa.Column("close", sa.Float),
        sa.Column("volume", sa.BigInteger),
        sa.Column("delivery", sa.BigInteger),
        sa.Column("vwap", sa.Float),
        sa.Column("turnover", sa.Float),
    )

    op.create_table(
        "fundamentals",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer, index=True),
        sa.Column("quarter", sa.String(10)),
        sa.Column("fiscal_year", sa.Integer),
        sa.Column("revenue", sa.Float),
        sa.Column("profit", sa.Float),
        sa.Column("eps", sa.Float),
        sa.Column("pe", sa.Float),
        sa.Column("pb", sa.Float),
        sa.Column("roe", sa.Float),
        sa.Column("roce", sa.Float),
        sa.Column("debt_equity", sa.Float),
        sa.Column("current_ratio", sa.Float),
        sa.Column("gross_margin", sa.Float),
        sa.Column("net_margin", sa.Float),
        sa.Column("dividend_yield", sa.Float),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "shareholding",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer, index=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("promoter", sa.Float),
        sa.Column("fii", sa.Float),
        sa.Column("dii", sa.Float),
        sa.Column("public", sa.Float),
        sa.Column("total_shares", sa.Float),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "corporate_actions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer, index=True),
        sa.Column("action_type", sa.String(50)),
        sa.Column("record_date", sa.Date),
        sa.Column("ex_date", sa.Date),
        sa.Column("ratio", sa.String(50)),
        sa.Column("price", sa.Float),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "deals",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer, index=True),
        sa.Column("deal_date", sa.Date),
        sa.Column("deal_type", sa.String(20)),
        sa.Column("buyer_name", sa.String(500)),
        sa.Column("seller_name", sa.String(500)),
        sa.Column("quantity", sa.BigInteger),
        sa.Column("price", sa.Float),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "mf_holdings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer, index=True),
        sa.Column("mf_name", sa.String(200)),
        sa.Column("quarter", sa.String(10)),
        sa.Column("year", sa.Integer),
        sa.Column("quantity", sa.BigInteger),
        sa.Column("change_qq", sa.BigInteger),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "news_articles",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("headline", sa.Text),
        sa.Column("summary", sa.Text),
        sa.Column("source", sa.String(100)),
        sa.Column("url", sa.String(1000)),
        sa.Column("published_at", sa.DateTime),
        sa.Column("sentiment", sa.String(20)),
        sa.Column("related_symbols", sa.JSON),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "watchlists",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(100)),
        sa.Column("name", sa.String(100)),
        sa.Column("symbols", sa.JSON),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("watchlists")
    op.drop_table("news_articles")
    op.drop_table("mf_holdings")
    op.drop_table("deals")
    op.drop_table("corporate_actions")
    op.drop_table("shareholding")
    op.drop_table("fundamentals")
    op.drop_table("stock_quotes")
    op.drop_table("companies")
