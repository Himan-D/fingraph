from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel

from db.postgres import get_db
from db.postgres_models import Watchlist

router = APIRouter()


class WatchlistCreate(BaseModel):
    name: str
    symbols: List[str]
    user_id: str = "default"


class WatchlistUpdate(BaseModel):
    name: str = None
    symbols: List[str] = None


@router.get("")
async def get_watchlists(user_id: str = "default", db: AsyncSession = Depends(get_db)):
    """Get all watchlists for user"""
    result = await db.execute(select(Watchlist).where(Watchlist.user_id == user_id))
    watchlists = result.scalars().all()

    return {
        "success": True,
        "data": [
            {
                "id": w.id,
                "name": w.name,
                "symbols": w.symbols,
            }
            for w in watchlists
        ],
    }


@router.get("/{watchlist_id}")
async def get_watchlist(watchlist_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific watchlist"""
    result = await db.execute(select(Watchlist).where(Watchlist.id == watchlist_id))
    watchlist = result.scalars().first()

    if not watchlist:
        return {"success": False, "error": "Watchlist not found"}

    return {
        "success": True,
        "data": {
            "id": watchlist.id,
            "name": watchlist.name,
            "symbols": watchlist.symbols,
        },
    }


@router.post("")
async def create_watchlist(data: WatchlistCreate, db: AsyncSession = Depends(get_db)):
    """Create a new watchlist"""
    watchlist = Watchlist(
        user_id=data.user_id,
        name=data.name,
        symbols=data.symbols,
    )
    db.add(watchlist)
    await db.commit()
    await db.refresh(watchlist)

    return {
        "success": True,
        "data": {
            "id": watchlist.id,
            "name": watchlist.name,
            "symbols": watchlist.symbols,
        },
    }


@router.put("/{watchlist_id}")
async def update_watchlist(
    watchlist_id: int, data: WatchlistUpdate, db: AsyncSession = Depends(get_db)
):
    """Update a watchlist"""
    result = await db.execute(select(Watchlist).where(Watchlist.id == watchlist_id))
    watchlist = result.scalars().first()

    if not watchlist:
        return {"success": False, "error": "Watchlist not found"}

    if data.name:
        watchlist.name = data.name
    if data.symbols:
        watchlist.symbols = data.symbols

    await db.commit()
    await db.refresh(watchlist)

    return {
        "success": True,
        "data": {
            "id": watchlist.id,
            "name": watchlist.name,
            "symbols": watchlist.symbols,
        },
    }


@router.delete("/{watchlist_id}")
async def delete_watchlist(watchlist_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a watchlist"""
    result = await db.execute(select(Watchlist).where(Watchlist.id == watchlist_id))
    watchlist = result.scalars().first()

    if not watchlist:
        return {"success": False, "error": "Watchlist not found"}

    await db.delete(watchlist)
    await db.commit()

    return {"success": True, "message": "Watchlist deleted"}
