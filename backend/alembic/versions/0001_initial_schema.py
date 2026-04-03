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
        sa.Column("name", sa.String(200)),
        sa.Column("sector", sa.String(100), index=True),
        sa.Column("industry", sa.String(100)),
        sa.Column("market_cap", sa.Numeric(20, 2)),
        sa.Column("description", sa.Text),
        sa.Column("isin", sa.String(20), unique=True),
        sa.Column("nse_symbol", sa.String(20)),
        sa.Column("bse_code", sa.String(10)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        "stock_quotes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("open", sa.Numeric(12, 2)),
        sa.Column("high", sa.Numeric(12, 2)),
        sa.Column("low", sa.Numeric(12, 2)),
        sa.Column("close", sa.Numeric(12, 2)),
        sa.Column("volume", sa.BigInteger),
        sa.Column("vwap", sa.Numeric(12, 2)),
        sa.Column("oi", sa.BigInteger),
    )
    op.create_index("ix_stock_quotes_company_ts", "stock_quotes", ["company_id", "timestamp"])

    op.create_table(
        "fundamentals",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("pe_ratio", sa.Numeric(10, 2)),
        sa.Column("pb_ratio", sa.Numeric(10, 2)),
        sa.Column("roe", sa.Numeric(10, 2)),
        sa.Column("roce", sa.Numeric(10, 2)),
        sa.Column("debt_to_equity", sa.Numeric(10, 2)),
        sa.Column("dividend_yield", sa.Numeric(10, 2)),
        sa.Column("eps", sa.Numeric(12, 2)),
        sa.Column("book_value", sa.Numeric(12, 2)),
        sa.Column("market_cap", sa.Numeric(20, 2)),
        sa.Column("revenue", sa.Numeric(20, 2)),
        sa.Column("net_profit", sa.Numeric(20, 2)),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "shareholdings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("quarter", sa.String(20)),
        sa.Column("promoter", sa.Numeric(7, 4)),
        sa.Column("fii", sa.Numeric(7, 4)),
        sa.Column("dii", sa.Numeric(7, 4)),
        sa.Column("public", sa.Numeric(7, 4)),
    )

    op.create_table(
        "corporate_actions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), index=True),
        sa.Column("action_type", sa.String(50)),
        sa.Column("ex_date", sa.DateTime),
        sa.Column("record_date", sa.DateTime),
        sa.Column("amount", sa.Numeric(12, 2)),
        sa.Column("remarks", sa.Text),
    )

    op.create_table(
        "deals",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), index=True),
        sa.Column("deal_type", sa.String(20)),
        sa.Column("date", sa.DateTime),
        sa.Column("buyer", sa.String(200)),
        sa.Column("seller", sa.String(200)),
        sa.Column("quantity", sa.BigInteger),
        sa.Column("price", sa.Numeric(12, 2)),
        sa.Column("value", sa.Numeric(20, 2)),
    )

    op.create_table(
        "mf_holdings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), index=True),
        sa.Column("fund_name", sa.String(200)),
        sa.Column("quantity", sa.BigInteger),
        sa.Column("change_qty", sa.BigInteger),
        sa.Column("quarter", sa.String(20)),
    )

    op.create_table(
        "news_articles",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("url", sa.String(2000), unique=True),
        sa.Column("source", sa.String(100)),
        sa.Column("published_at", sa.DateTime),
        sa.Column("summary", sa.Text),
        sa.Column("sentiment", sa.String(20), default="neutral"),
        sa.Column("symbols", sa.JSON),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_news_articles_published", "news_articles", ["published_at"])

    op.create_table(
        "watchlists",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("symbols", sa.JSON, default=list),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("watchlists")
    op.drop_table("news_articles")
    op.drop_table("mf_holdings")
    op.drop_table("deals")
    op.drop_table("corporate_actions")
    op.drop_table("shareholdings")
    op.drop_table("fundamentals")
    op.drop_index("ix_stock_quotes_company_ts", table_name="stock_quotes")
    op.drop_table("stock_quotes")
    op.drop_table("companies")
