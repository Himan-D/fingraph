from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from neo4j import GraphDatabase


SCRIPT_NAME = "enrich_articles_finance_relations"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
SAFE_TEXT_PATTERN = re.compile(r"[^a-z0-9]+")
COMPANY_SUFFIX_PATTERN = re.compile(
    r"\b(limited|ltd|inc|corp|corporation|company|co|plc)\b",
    re.IGNORECASE,
)

GENERIC_SINGLE_WORD_ALIASES = {
    "auto",
    "bank",
    "banks",
    "bharat",
    "capital",
    "consumer",
    "energy",
    "finance",
    "financial",
    "goods",
    "healthcare",
    "india",
    "indian",
    "industries",
    "industry",
    "materials",
    "metals",
    "petroleum",
    "services",
    "technology",
    "telecommunication",
}

WEAK_SECTOR_KEYWORDS = {
    "bank",
    "banking",
    "digital",
    "energy",
    "finance",
    "gas",
    "hospital",
    "logistics",
    "medical",
    "oil",
    "petroleum",
    "services",
    "technology",
    "transport",
    "vehicle",
    "vehicles",
}

SKIP_PARAGRAPH_MARKERS = (
    "story continues below",
    "subscribe to see fewer ads",
    "follow us on",
    "top categories",
    "trending news",
    "latest stories",
    "download apps",
    "express group",
    "quick links",
)

SECTOR_KEYWORD_MAP = {
    "Automobile": [
        "automobile",
        "automotive",
        "vehicle",
        "vehicles",
        "passenger vehicle",
        "commercial vehicle",
        "ev",
        "electric vehicle",
        "tyre",
        "two wheeler",
        "truck",
    ],
    "Capital Goods": [
        "capital goods",
        "engineering",
        "infrastructure",
        "industrial equipment",
        "heavy electricals",
        "manufacturing equipment",
        "epc",
        "defence equipment",
        "indian railways",
        "railways",
        "railway",
        "signalling",
        "signal system",
        "locomotive",
        "rolling stock",
    ],
    "Consumer Goods": [
        "consumer goods",
        "consumer demand",
        "durable goods",
        "appliances",
        "retail demand",
        "electronics",
    ],
    "Energy": [
        "energy",
        "power sector",
        "electricity",
        "renewable",
        "solar",
        "wind power",
        "transmission",
        "oil",
        "gas",
        "petroleum",
        "refinery",
    ],
    "FMCG": [
        "fmcg",
        "consumer staples",
        "packaged food",
        "food products",
        "beverage",
        "daily use products",
    ],
    "Financial Services": [
        "financial services",
        "banking",
        "bank",
        "nbfc",
        "insurance",
        "credit",
        "loan",
        "lending",
        "finance",
        "income tax",
        "tax rule",
        "tax rules",
        "tax act",
        "tds",
        "tcs",
        "tax audit",
        "pan",
        "tan",
        "rbi",
    ],
    "Healthcare": [
        "healthcare",
        "hospital",
        "pharma",
        "pharmaceutical",
        "drug",
        "medicine",
        "medical",
        "diagnostic",
    ],
    "Materials": [
        "materials",
        "cement",
        "chemical",
        "chemicals",
        "fertilizer",
        "construction material",
        "paint",
    ],
    "Metals": [
        "metals",
        "metal",
        "steel",
        "aluminium",
        "copper",
        "mining",
        "ore",
    ],
    "Services": [
        "services sector",
        "ports",
        "logistics",
        "shipping",
        "cargo",
        "aviation",
        "airport",
        "transport",
        "warehouse",
    ],
    "Technology": [
        "technology",
        "tech sector",
        "software",
        "it services",
        "digital",
        "cloud",
        "ai",
        "artificial intelligence",
        "semiconductor",
    ],
    "Telecommunication": [
        "telecommunication",
        "telecom",
        "mobile network",
        "broadband",
        "5g",
        "spectrum",
        "telecom sector",
    ],
}


@dataclass(frozen=True)
class ArticleRecord:
    graphml_id: str
    title: str
    url: str


@dataclass(frozen=True)
class CompanyRecord:
    symbol: str
    name: str
    sector: str
    aliases: tuple[str, ...]


def _normalize_text(value: str) -> str:
    cleaned = value.lower().replace("&", " and ")
    cleaned = SAFE_TEXT_PATTERN.sub(" ", cleaned)
    return " ".join(cleaned.split())


def _normalize_company_name(value: str) -> str:
    cleaned = COMPANY_SUFFIX_PATTERN.sub(" ", value)
    return _normalize_text(cleaned)


def _phrase_hits(text: str, phrase: str) -> int:
    if not text or not phrase:
        return 0
    return f" {text} ".count(f" {phrase} ")


def _company_aliases(symbol: str, name: str) -> tuple[str, ...]:
    base_name = _normalize_company_name(name)
    aliases: set[str] = set()
    if base_name:
        aliases.add(base_name)
        aliases.add(base_name.replace(" and ", " "))

    symbol_alias = _normalize_text(symbol.replace("_", " "))
    if len(symbol_alias.replace(" ", "")) >= 3:
        aliases.add(symbol_alias)

    tokens = [token for token in base_name.split() if token]
    if len(tokens) >= 2 and all(token not in {"and", "of"} for token in tokens[:2]):
        aliases.add(" ".join(tokens[:2]))
    if len(tokens) >= 3 and all(token not in {"and", "of"} for token in tokens[:3]):
        aliases.add(" ".join(tokens[:3]))

    cleaned_aliases = []
    for alias in aliases:
        alias = " ".join(alias.split())
        if len(alias) < 4:
            continue
        if " " not in alias and alias in GENERIC_SINGLE_WORD_ALIASES:
            continue
        cleaned_aliases.append(alias)

    return tuple(sorted(set(cleaned_aliases), key=lambda item: (-len(item), item)))


def _load_settings() -> tuple[str, str, str, str]:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    uri = os.getenv("NEO4J_URI", "").strip()
    username = (os.getenv("NEO4J_USERNAME", "") or os.getenv("NEO4J_USER", "")).strip()
    password = os.getenv("NEO4J_PASSWORD", "").strip()
    database = (os.getenv("NEO4J_DATABASE", "") or "neo4j").strip()
    if not uri or not username or not password:
        raise RuntimeError("Neo4j credentials are incomplete in backend/.env")
    return uri, username, password, database


def _load_graph_inventory(
    driver: Any,
    database: str,
    limit: int | None,
) -> tuple[list[ArticleRecord], list[CompanyRecord], list[str]]:
    article_limit = "" if limit is None else "LIMIT $limit"
    with driver.session(database=database) as session:
        article_rows = session.run(
            f"""
            MATCH (a:Article)
            WHERE a.import_source = 'articles_graph.graphml'
              AND a.url IS NOT NULL
            RETURN a.graphml_id AS graphml_id,
                   coalesce(a.title, a.display_name, a.graphml_id) AS title,
                   a.url AS url
            ORDER BY a.graphml_id
            {article_limit}
            """,
            limit=limit,
        ).data()
        company_rows = session.run(
            """
            MATCH (c:Company)
            RETURN c.symbol AS symbol,
                   coalesce(c.name, c.symbol) AS name,
                   coalesce(c.sector, '') AS sector
            ORDER BY c.symbol
            """
        ).data()
        sector_rows = session.run(
            """
            MATCH (s:Sector)
            RETURN s.name AS name
            ORDER BY s.name
            """
        ).data()

    articles = [
        ArticleRecord(
            graphml_id=row["graphml_id"],
            title=row.get("title") or row["graphml_id"],
            url=row["url"],
        )
        for row in article_rows
    ]
    companies = [
        CompanyRecord(
            symbol=row["symbol"],
            name=row["name"],
            sector=row.get("sector") or "",
            aliases=_company_aliases(row["symbol"], row["name"]),
        )
        for row in company_rows
    ]
    sectors = [row["name"] for row in sector_rows]
    return articles, companies, sectors


def _extract_article_text(html: str, fallback_title: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    title = fallback_title
    for selector in (
        ("meta", {"property": "og:title"}),
        ("meta", {"name": "twitter:title"}),
    ):
        candidate = soup.find(selector[0], attrs=selector[1])
        if candidate and candidate.get("content"):
            title = candidate["content"].strip()
            break
    if not title and soup.title:
        title = soup.title.get_text(" ", strip=True)

    containers: list[Any] = []
    article_tag = soup.find("article")
    if article_tag is not None:
        containers.append(article_tag)
    containers.extend(
        soup.select(
            "main, div[itemprop='articleBody'], div.story_details, div.story, div.article-body"
        )
    )

    best_text = ""
    for container in containers:
        paragraphs: list[str] = []
        for paragraph in container.find_all("p"):
            text = " ".join(paragraph.get_text(" ", strip=True).split())
            if len(text) < 40:
                continue
            lower = text.lower()
            if any(marker in lower for marker in SKIP_PARAGRAPH_MARKERS):
                continue
            paragraphs.append(text)
        joined = "\n".join(paragraphs)
        if len(joined) > len(best_text):
            best_text = joined

    if not best_text:
        fallback_paragraphs: list[str] = []
        for paragraph in soup.find_all("p"):
            text = " ".join(paragraph.get_text(" ", strip=True).split())
            if len(text) < 40:
                continue
            lower = text.lower()
            if any(marker in lower for marker in SKIP_PARAGRAPH_MARKERS):
                continue
            fallback_paragraphs.append(text)
            if len(fallback_paragraphs) >= 20:
                break
        best_text = "\n".join(fallback_paragraphs)

    return title or fallback_title, best_text


async def _fetch_article_content(
    client: httpx.AsyncClient,
    article: ArticleRecord,
) -> dict[str, Any]:
    result = {
        "graphml_id": article.graphml_id,
        "url": article.url,
        "title": article.title,
        "body": "",
        "fetch_error": None,
    }
    try:
        response = await client.get(article.url, follow_redirects=True)
        response.raise_for_status()
        title, body = _extract_article_text(response.text, article.title)
        result["title"] = title
        result["body"] = body
    except Exception as exc:
        result["fetch_error"] = str(exc)
    return result


def _match_companies(
    article_title: str,
    article_body: str,
    companies: list[CompanyRecord],
    min_company_score: float,
) -> list[dict[str, Any]]:
    title_text = _normalize_text(article_title)
    body_text = _normalize_text(article_body)
    matches: list[dict[str, Any]] = []

    for company in companies:
        score = 0.0
        aliases: list[str] = []
        for alias in company.aliases:
            title_hits = _phrase_hits(title_text, alias)
            body_hits = _phrase_hits(body_text, alias)
            if not title_hits and not body_hits:
                continue
            aliases.append(alias)
            score += min(title_hits, 2) * 4.0
            score += min(body_hits, 3) * 2.0

        if score >= min_company_score:
            matches.append(
                {
                    "symbol": company.symbol,
                    "name": company.name,
                    "sector": company.sector,
                    "score": score,
                    "matched_aliases": sorted(set(aliases)),
                }
            )

    matches.sort(key=lambda item: (-item["score"], item["symbol"]))
    return matches[:3]


def _match_sectors(
    article_title: str,
    article_body: str,
    sectors: list[str],
    company_matches: list[dict[str, Any]],
    min_sector_score: float,
) -> list[dict[str, Any]]:
    title_text = _normalize_text(article_title)
    body_text = _normalize_text(article_body)
    matched_sector_companies: dict[str, list[str]] = {}
    for company in company_matches:
        sector = company.get("sector") or ""
        if sector:
            matched_sector_companies.setdefault(sector, []).append(company["symbol"])

    sector_matches: list[dict[str, Any]] = []
    for sector in sectors:
        score = 0.0
        keywords = {_normalize_text(sector)}
        keywords.update(
            _normalize_text(keyword)
            for keyword in SECTOR_KEYWORD_MAP.get(sector, [])
        )
        matched_keywords: list[str] = []

        if sector in matched_sector_companies:
            score += 4.0 * len(matched_sector_companies[sector])

        for keyword in keywords:
            if not keyword:
                continue
            title_hits = _phrase_hits(title_text, keyword)
            body_hits = _phrase_hits(body_text, keyword)
            if not title_hits and not body_hits:
                continue
            matched_keywords.append(keyword)
            score += min(title_hits, 2) * 2.5
            score += min(body_hits, 4) * 1.0

        unique_keywords = sorted(set(matched_keywords))
        has_company_signal = sector in matched_sector_companies
        has_strong_keyword = any(
            " " in keyword or keyword not in WEAK_SECTOR_KEYWORDS
            for keyword in unique_keywords
        )

        if (
            score >= min_sector_score
            and (
                has_company_signal
                or has_strong_keyword
                or (len(unique_keywords) >= 3 and score >= 8.0)
            )
        ):
            sector_matches.append(
                {
                    "sector": sector,
                    "score": score,
                    "matched_keywords": unique_keywords,
                    "company_symbols": matched_sector_companies.get(sector, []),
                }
            )

    sector_matches.sort(key=lambda item: (-item["score"], item["sector"]))
    return sector_matches[:4]


async def _analyze_articles(
    articles: list[ArticleRecord],
    companies: list[CompanyRecord],
    sectors: list[str],
    min_company_score: float,
    min_sector_score: float,
    concurrency: int,
) -> list[dict[str, Any]]:
    semaphore = asyncio.Semaphore(concurrency)
    timeout = httpx.Timeout(25.0, connect=10.0)
    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        async def process(article: ArticleRecord) -> dict[str, Any]:
            async with semaphore:
                fetched = await _fetch_article_content(client, article)
            company_matches = _match_companies(
                fetched["title"],
                fetched["body"],
                companies,
                min_company_score,
            )
            sector_matches = _match_sectors(
                fetched["title"],
                fetched["body"],
                sectors,
                company_matches,
                min_sector_score,
            )
            return {
                **fetched,
                "company_matches": company_matches,
                "sector_matches": sector_matches,
            }

        return await asyncio.gather(*(process(article) for article in articles))


def _delete_previous_edges(session: Any) -> None:
    session.run(
        """
        MATCH ()-[r]->()
        WHERE type(r) IN ['AFFECTS_COMPANY', 'RELEVANT_TO_SECTOR']
          AND r.created_by = $created_by
        DELETE r
        """,
        created_by=SCRIPT_NAME,
    ).consume()


def _persist_results(
    session: Any,
    analyses: list[dict[str, Any]],
    dry_run: bool,
) -> dict[str, Any]:
    created_company_edges = 0
    created_sector_edges = 0
    sample_articles: list[dict[str, Any]] = []

    if not dry_run:
        _delete_previous_edges(session)

    for analysis in analyses:
        article_id = analysis["graphml_id"]
        article_summary = {
            "graphml_id": article_id,
            "title": analysis["title"],
            "url": analysis["url"],
            "company_matches": [],
            "sector_matches": [],
            "fetch_error": analysis.get("fetch_error"),
        }

        for company_match in analysis["company_matches"]:
            article_summary["company_matches"].append(
                {
                    "symbol": company_match["symbol"],
                    "score": company_match["score"],
                    "matched_aliases": company_match["matched_aliases"],
                }
            )
            created_company_edges += 1
            if not dry_run:
                session.run(
                    """
                    MATCH (a:Article {graphml_id: $graphml_id})
                    MATCH (c:Company {symbol: $symbol})
                    MERGE (a)-[r:AFFECTS_COMPANY]->(c)
                    SET r.score = $score,
                        r.match_reason = 'article_content',
                        r.matched_aliases = $matched_aliases,
                        r.created_by = $created_by,
                        r.source_url = $source_url
                    """,
                    graphml_id=article_id,
                    symbol=company_match["symbol"],
                    score=company_match["score"],
                    matched_aliases=company_match["matched_aliases"],
                    created_by=SCRIPT_NAME,
                    source_url=analysis["url"],
                ).consume()

        for sector_match in analysis["sector_matches"]:
            article_summary["sector_matches"].append(
                {
                    "sector": sector_match["sector"],
                    "score": sector_match["score"],
                    "matched_keywords": sector_match["matched_keywords"],
                    "company_symbols": sector_match["company_symbols"],
                }
            )
            created_sector_edges += 1
            if not dry_run:
                session.run(
                    """
                    MATCH (a:Article {graphml_id: $graphml_id})
                    MATCH (s:Sector {name: $sector})
                    MERGE (a)-[r:RELEVANT_TO_SECTOR]->(s)
                    SET r.score = $score,
                        r.match_reason = 'article_content',
                        r.matched_keywords = $matched_keywords,
                        r.company_symbols = $company_symbols,
                        r.created_by = $created_by,
                        r.source_url = $source_url
                    """,
                    graphml_id=article_id,
                    sector=sector_match["sector"],
                    score=sector_match["score"],
                    matched_keywords=sector_match["matched_keywords"],
                    company_symbols=sector_match["company_symbols"],
                    created_by=SCRIPT_NAME,
                    source_url=analysis["url"],
                ).consume()

        if article_summary["company_matches"] or article_summary["sector_matches"]:
            sample_articles.append(article_summary)

    return {
        "created_company_edges": created_company_edges,
        "created_sector_edges": created_sector_edges,
        "matched_articles": len(sample_articles),
        "sample_articles": sample_articles[:8],
    }


async def run_enrichment(
    limit: int | None,
    min_company_score: float,
    min_sector_score: float,
    concurrency: int,
    dry_run: bool,
) -> dict[str, Any]:
    uri, username, password, database = _load_settings()
    driver = GraphDatabase.driver(uri, auth=(username, password))

    try:
        articles, companies, sectors = _load_graph_inventory(driver, database, limit)
        analyses = await _analyze_articles(
            articles,
            companies,
            sectors,
            min_company_score,
            min_sector_score,
            concurrency,
        )

        with driver.session(database=database) as session:
            persist_summary = _persist_results(session, analyses, dry_run)
            if dry_run:
                db_counts = None
            else:
                company_record = session.run(
                    """
                    MATCH (:Article)-[r:AFFECTS_COMPANY]->(:Company)
                    WHERE r.created_by = $created_by
                    RETURN count(r) AS count
                    """,
                    created_by=SCRIPT_NAME,
                ).single()
                sector_record = session.run(
                    """
                    MATCH (:Article)-[r:RELEVANT_TO_SECTOR]->(:Sector)
                    WHERE r.created_by = $created_by
                    RETURN count(r) AS count
                    """,
                    created_by=SCRIPT_NAME,
                ).single()
                db_counts = {
                    "affects_company_count": int(company_record["count"] if company_record else 0),
                    "relevant_to_sector_count": int(sector_record["count"] if sector_record else 0),
                }

        fetch_failures = sum(1 for analysis in analyses if analysis.get("fetch_error"))
        return {
            "database": database,
            "dry_run": dry_run,
            "articles_scanned": len(articles),
            "companies_loaded": len(companies),
            "sectors_loaded": len(sectors),
            "fetch_failures": fetch_failures,
            **persist_summary,
            "database_counts": db_counts,
        }
    finally:
        driver.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch article pages and create AFFECTS_COMPANY / RELEVANT_TO_SECTOR edges"
    )
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N articles")
    parser.add_argument("--min-company-score", type=float, default=4.0)
    parser.add_argument("--min-sector-score", type=float, default=4.0)
    parser.add_argument("--concurrency", type=int, default=6)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = asyncio.run(
        run_enrichment(
            limit=args.limit,
            min_company_score=args.min_company_score,
            min_sector_score=args.min_sector_score,
            concurrency=args.concurrency,
            dry_run=args.dry_run,
        )
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
