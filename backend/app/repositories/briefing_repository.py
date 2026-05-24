"""
InstaVest — Briefing & Checklist Repository
SQL-backed storage for user-specific morning briefing checklist items.
"""
from datetime import date as date_type, datetime
from sqlalchemy.orm import Session
from app.db.models import BriefingChecklistItem


def get_checklist_items(db: Session, user_id: int, date: date_type) -> list[BriefingChecklistItem]:
    return (
        db.query(BriefingChecklistItem)
        .filter(BriefingChecklistItem.user_id == user_id, BriefingChecklistItem.briefing_date == date)
        .order_by(BriefingChecklistItem.created_at.asc())
        .all()
    )


def upsert_checklist_item(
    db: Session,
    user_id: int,
    date: date_type,
    item_key: str,
    title: str,
    completed: bool = False,
) -> BriefingChecklistItem:
    existing = (
        db.query(BriefingChecklistItem)
        .filter(
            BriefingChecklistItem.user_id == user_id,
            BriefingChecklistItem.briefing_date == date,
            BriefingChecklistItem.item_key == item_key,
        )
        .first()
    )
    if existing:
        existing.title = title
        existing.completed = completed
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    item = BriefingChecklistItem(
        user_id=user_id,
        briefing_date=date,
        item_key=item_key,
        title=title,
        completed=completed,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def toggle_checklist_item(db: Session, item_id: int, completed: bool) -> BriefingChecklistItem | None:
    item = db.query(BriefingChecklistItem).filter(BriefingChecklistItem.id == item_id).first()
    if not item:
        return None
    item.completed = completed
    item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return item
