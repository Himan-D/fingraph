from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from core.services.graph_service import get_graph_service

router = APIRouter()


@router.get("/company/{symbol}")
async def get_company_graph(symbol: str):
    """Get company relationships from knowledge graph"""
    try:
        graph_service = get_graph_service()
        result = await graph_service.get_company_graph(symbol.upper())
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/promoter/{name}")
async def get_promoter_network(name: str):
    """Get all companies by promoter"""
    try:
        graph_service = get_graph_service()
        result = await graph_service.get_promoter_network(name)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/sector/{sector}")
async def get_sector_graph(sector: str):
    """Get sector relationships"""
    try:
        graph_service = get_graph_service()
        result = await graph_service.get_sector_graph(sector)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/promoters")
async def get_all_promoters():
    """Get list of all promoters"""
    from core.services.graph_service import SAMPLE_GRAPH_DATA

    promoters = []
    for name, companies in SAMPLE_GRAPH_DATA["promoters"].items():
        total_mc = sum(
            SAMPLE_GRAPH_DATA["companies"].get(c, {}).get("market_cap", 0)
            for c in companies
        )
        promoters.append(
            {
                "name": name,
                "companies": companies,
                "total_market_cap": total_mc,
            }
        )

    return {"success": True, "data": promoters}


@router.get("/sectors")
async def get_all_sectors():
    """Get list of all sectors"""
    from core.services.graph_service import SAMPLE_GRAPH_DATA

    sectors = []
    for name, data in SAMPLE_GRAPH_DATA["sectors"].items():
        companies = data.get("companies", [])
        total_mc = sum(
            SAMPLE_GRAPH_DATA["companies"].get(c, {}).get("market_cap", 0)
            for c in companies
        )
        sectors.append(
            {
                "name": name,
                "companies": companies,
                "company_count": len(companies),
                "total_market_cap": total_mc,
                "index": data.get("index"),
            }
        )

    return {"success": True, "data": sectors}


@router.get("/full")
async def get_full_graph():
    """Get complete knowledge graph"""
    try:
        graph_service = get_graph_service()
        result = await graph_service.get_full_graph()
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/search")
async def search_graph(q: str):
    """Search knowledge graph"""
    try:
        graph_service = get_graph_service()
        results = await graph_service.search(q)
        return {"success": True, "data": results}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/kmp")
async def get_kmp():
    """Get key managerial personnel"""
    from core.services.graph_service import SAMPLE_GRAPH_DATA

    return {"success": True, "data": SAMPLE_GRAPH_DATA["kmp"]}


@router.get("/indices")
async def get_indices_graph():
    """Get indices with constituents"""
    from core.services.graph_service import SAMPLE_GRAPH_DATA

    indices = []
    for idx, data in SAMPLE_GRAPH_DATA["indices"].items():
        # Find companies in this index
        constituents = []
        for rel in SAMPLE_GRAPH_DATA["relationships"]:
            if rel.get("type") == "PART_OF_INDEX" and rel["to"] == idx:
                company = SAMPLE_GRAPH_DATA["companies"].get(rel["from"], {})
                constituents.append(
                    {
                        "symbol": rel["from"],
                        "name": company.get("name", rel["from"]),
                        "weight": rel.get("weight", 0),
                    }
                )

        indices.append(
            {
                "symbol": idx,
                "name": data.get("name", idx),
                "value": data.get("value", 0),
                "constituents": sorted(
                    constituents, key=lambda x: x["weight"], reverse=True
                ),
            }
        )

    return {"success": True, "data": indices}


@router.post("/query")
async def query_graph(cypher: str):
    """Execute custom Cypher query (if Neo4j configured)"""
    return {
        "success": False,
        "error": "Custom Cypher queries require Neo4j configuration",
    }
