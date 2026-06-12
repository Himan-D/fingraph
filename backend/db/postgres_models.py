from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    BigInteger,
    Text,
    JSON,
)
from sqlalchemy.sql import func
from db.postgres import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    nse_code = Column(String(20))
    bse_code = Column(String(20))
    name = Column(String(500))
    isin = Column(String(50))
    sector = Column(String(100))
    industry = Column(String(200))
    market_cap = Column(Float)
    description = Column(Text)
    listing_date = Column(Date)
    face_value = Column(Float, default=10.0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class StockQuote(Base):
    __tablename__ = "stock_quotes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(Integer, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(BigInteger)
    delivery = Column(BigInteger)
    vwap = Column(Float)
    turnover = Column(Float)


class Fundamental(Base):
    __tablename__ = "fundamentals"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, index=True)
    quarter = Column(String(10))
    fiscal_year = Column(Integer)
    revenue = Column(Float)
    profit = Column(Float)
    eps = Column(Float)
    pe = Column(Float)
    pb = Column(Float)
    roe = Column(Float)
    roce = Column(Float)
    debt_equity = Column(Float)
    current_ratio = Column(Float)
    gross_margin = Column(Float)
    net_margin = Column(Float)
    dividend_yield = Column(Float)
    created_at = Column(DateTime, server_default=func.now())


class Shareholding(Base):
    __tablename__ = "shareholding"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, index=True)
    date = Column(Date, nullable=False)
    promoter = Column(Float)
    fii = Column(Float)
    dii = Column(Float)
    public = Column(Float)
    total_shares = Column(Float)
    created_at = Column(DateTime, server_default=func.now())


class CorporateAction(Base):
    __tablename__ = "corporate_actions"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, index=True)
    action_type = Column(String(50))  # DIVIDEND, BONUS, SPLIT, RIGHTS, MERGER
    record_date = Column(Date)
    ex_date = Column(Date)
    ratio = Column(String(50))
    price = Column(Float)
    created_at = Column(DateTime, server_default=func.now())


class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, index=True)
    deal_date = Column(Date)
    deal_type = Column(String(20))  # BULK, BLOCK, SHORT
    buyer_name = Column(String(500))
    seller_name = Column(String(500))
    quantity = Column(BigInteger)
    price = Column(Float)
    created_at = Column(DateTime, server_default=func.now())


class MFHolding(Base):
    __tablename__ = "mf_holdings"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, index=True)
    mf_name = Column(String(200))
    quarter = Column(String(10))
    year = Column(Integer)
    quantity = Column(BigInteger)
    change_qq = Column(BigInteger)
    created_at = Column(DateTime, server_default=func.now())


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    headline = Column(Text)
    summary = Column(Text)
    source = Column(String(100))
    url = Column(String(1000))
    published_at = Column(DateTime)
    sentiment = Column(String(20))
    related_symbols = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())


class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100))
    name = Column(String(100))
    symbols = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())


class TwitterPost(Base):
    __tablename__ = "twitter_posts"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(String(100), unique=True)
    username = Column(String(100), index=True)
    text = Column(Text)
    source = Column(String(50))
    symbol = Column(String(20))
    timestamp = Column(DateTime, index=True)
    likes = Column(Integer, default=0)
    retweets = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class RedditPost(Base):
    __tablename__ = "reddit_posts"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(String(100), unique=True)
    title = Column(Text)
    text = Column(Text)
    author = Column(String(100), index=True)
    subreddit = Column(String(50), index=True)
    url = Column(String(1000))
    score = Column(Integer, default=0)
    num_comments = Column(Integer, default=0)
    symbols = Column(JSON)
    timestamp = Column(DateTime, index=True)
    created_at = Column(DateTime, server_default=func.now())


class SocialSentiment(Base):
    __tablename__ = "social_sentiment"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True)
    date = Column(Date, index=True)
    source = Column(String(20))
    sentiment_score = Column(Float)
    mention_count = Column(Integer, default=0)
    bullish_count = Column(Integer, default=0)
    bearish_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class Commodity(Base):
    __tablename__ = "commodities"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    exchange = Column(String(20))
    category = Column(String(50))
    unit = Column(String(20))
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class CommodityPrice(Base):
    __tablename__ = "commodity_prices"

    id = Column(Integer, primary_key=True, index=True)
    commodity_id = Column(Integer, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    settlement = Column(Float)
    previous_close = Column(Float)
    change = Column(Float)
    change_pct = Column(Float)
    volume = Column(BigInteger)
    open_interest = Column(BigInteger)
    delivery = Column(Float)
    turnover = Column(Float)
    created_at = Column(DateTime, server_default=func.now())


class CommodityNews(Base):
    __tablename__ = "commodity_news"

    id = Column(Integer, primary_key=True, index=True)
    headline = Column(Text)
    summary = Column(Text)
    source = Column(String(100))
    url = Column(String(1000))
    commodities = Column(JSON)
    published_at = Column(DateTime)
    sentiment = Column(String(20))
    tags = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())


class CommoditySentiment(Base):
    __tablename__ = "commodity_sentiment"

    id = Column(Integer, primary_key=True, index=True)
    commodity_symbol = Column(String(20), index=True)
    date = Column(Date, index=True)
    source = Column(String(20))
    sentiment_score = Column(Float)
    mention_count = Column(Integer, default=0)
    bullish_count = Column(Integer, default=0)
    bearish_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class IndexQuote(Base):
    __tablename__ = "index_quotes"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True)
    name = Column(String(100))
    price = Column(Float)
    change = Column(Float)
    pct_change = Column(Float)
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())


class OptionChainRecord(Base):
    __tablename__ = "option_chain_records"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True)
    expiry_date = Column(Date)
    strike_price = Column(Float)
    option_type = Column(String(5))
    last_price = Column(Float)
    open_interest = Column(BigInteger)
    volume = Column(BigInteger)
    iv = Column(Float)
    delta = Column(Float)
    gamma = Column(Float)
    theta = Column(Float)
    vega = Column(Float)
    created_at = Column(DateTime, server_default=func.now())


class StockInventory(Base):
    __tablename__ = "stock_inventory"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(200))
    plan = Column(String(20), default="FREE")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    title = Column(String(500))
    symbol = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, index=True, nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text)
    tool_calls = Column(JSON)
    tool_results = Column(JSON)
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class AIAlert(Base):
    __tablename__ = "ai_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    symbol = Column(String(20), index=True)
    alert_type = Column(String(50))
    severity = Column(String(20))
    title = Column(String(500))
    summary = Column(Text)
    data = Column(JSON)
    is_read = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class SavedScreener(Base):
    __tablename__ = "saved_screeners"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    title = Column(String(200), nullable=False)
    config = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AgentMemory(Base):
    __tablename__ = "agent_memory"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    memory_type = Column(String(50), index=True)
    key = Column(String(200), index=True)
    data = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
