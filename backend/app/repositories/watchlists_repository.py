"""
InstaVest — Watchlists Repository
"""
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from app.db.models import Watchlist, WatchlistItem


def list_watchlists(db: Session, user_id: int) -> list[Watchlist]:
    return (
        db.query(Watchlist)
        .filter(Watchlist.user_id == user_id)
        .options(joinedload(Watchlist.items))
        .all()
    )


def create_watchlist(db: Session, user_id: int, name: str) -> Watchlist:
    wl = Watchlist(user_id=user_id, name=name)
    db.add(wl)
    db.commit()
    db.refresh(wl)
    return wl


def get_watchlist(db: Session, watchlist_id: int) -> Watchlist | None:
    return (
        db.query(Watchlist)
        .filter(Watchlist.id == watchlist_id)
        .options(joinedload(Watchlist.items))
        .first()
    )


def add_item(db: Session, watchlist_id: int, ticker: str) -> WatchlistItem:
    ticker = ticker.upper().strip()
    existing = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.watchlist_id == watchlist_id, WatchlistItem.ticker == ticker)
        .first()
    )
    if existing:
        return existing
    item = WatchlistItem(watchlist_id=watchlist_id, ticker=ticker)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def remove_item(db: Session, watchlist_id: int, ticker: str) -> bool:
    ticker = ticker.upper().strip()
    item = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.watchlist_id == watchlist_id, WatchlistItem.ticker == ticker)
        .first()
    )
    if item:
        db.delete(item)
        db.commit()
        return True
    return False


def delete_watchlist(db: Session, watchlist_id: int) -> bool:
    wl = db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()
    if wl:
        db.delete(wl)
        db.commit()
        return True
    return False
