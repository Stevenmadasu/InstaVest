"""Watchlist routes — SQL-backed database endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.repositories import watchlists_repository

router = APIRouter()


class WatchlistCreate(BaseModel):
    name: str


class WatchlistItemAdd(BaseModel):
    ticker: str


@router.get("")
def list_watchlists(user_id: int = 1, db: Session = Depends(get_db)):
    wls = watchlists_repository.list_watchlists(db, user_id=user_id)
    return [{"id": w.id, "name": w.name, "item_count": len(w.items)} for w in wls]


@router.post("")
def create_watchlist(data: WatchlistCreate, db: Session = Depends(get_db)):
    wl = watchlists_repository.create_watchlist(db, user_id=1, name=data.name)
    return {"id": wl.id, "name": wl.name}


@router.get("/{watchlist_id}")
def get_watchlist(watchlist_id: int, db: Session = Depends(get_db)):
    wl = watchlists_repository.get_watchlist(db, watchlist_id)
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return {
        "id": wl.id,
        "name": wl.name,
        "user_id": wl.user_id,
        "items": [item.ticker for item in wl.items]
    }


@router.post("/{watchlist_id}/items")
def add_watchlist_item(watchlist_id: int, data: WatchlistItemAdd, db: Session = Depends(get_db)):
    wl = watchlists_repository.get_watchlist(db, watchlist_id)
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    ticker = data.ticker.upper().strip()
    watchlists_repository.add_item(db, watchlist_id, ticker)
    return {"status": "added", "ticker": ticker}


@router.delete("/{watchlist_id}/items/{ticker}")
def remove_watchlist_item(watchlist_id: int, ticker: str, db: Session = Depends(get_db)):
    wl = watchlists_repository.get_watchlist(db, watchlist_id)
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    t = ticker.upper().strip()
    watchlists_repository.remove_item(db, watchlist_id, t)
    return {"status": "removed", "ticker": t}
