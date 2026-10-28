"""CRUD des tests du benchmark."""

from fastapi import APIRouter, HTTPException, Response, status
from sqlmodel import Session, col, or_, select

from app.deps import SessionDep
from app.models import (
    BenchItem,
    BenchItemCreate,
    BenchItemRead,
    BenchItemUpdate,
    Category,
    Split,
    Status,
    nfc,
    utcnow,
)
from app.testset import make_id_allocator

router = APIRouter(prefix="/api/tests", tags=["tests"])


def _get_or_404(session: Session, item_id: str) -> BenchItem:
    item = session.get(BenchItem, item_id)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"test « {item_id} » introuvable")
    return item


@router.get("", response_model=list[BenchItemRead])
def list_items(
    session: SessionDep,
    category: Category | None = None,
    status: Status | None = None,
    split: Split | None = None,
    q: str | None = None,
):
    stmt = select(BenchItem)
    if category:
        stmt = stmt.where(BenchItem.category == category)
    if status:
        stmt = stmt.where(BenchItem.status == status)
    if split:
        stmt = stmt.where(BenchItem.split == split)
    if q:
        like = f"%{nfc(q)}%"
        stmt = stmt.where(
            or_(
                col(BenchItem.id).ilike(like),
                col(BenchItem.prompt).ilike(like),
                col(BenchItem.source_text).ilike(like),
                col(BenchItem.notes).ilike(like),
            )
        )
    return session.exec(stmt.order_by(BenchItem.id)).all()


@router.get("/{item_id}", response_model=BenchItemRead)
def get_item(item_id: str, session: SessionDep):
    return _get_or_404(session, item_id)


@router.post("", response_model=BenchItemRead, status_code=status.HTTP_201_CREATED)
def create_item(payload: BenchItemCreate, session: SessionDep):
    if payload.id and session.get(BenchItem, payload.id):
        raise HTTPException(status.HTTP_409_CONFLICT, f"l'identifiant « {payload.id} » existe déjà")
    item_id = payload.id or make_id_allocator(session, reserved=set())(payload.category)
    now = utcnow()
    item = BenchItem(
        **payload.model_dump(exclude={"id", "created_at", "updated_at"}),
        id=item_id,
        created_at=now,
        updated_at=now,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put("/{item_id}", response_model=BenchItemRead)
def update_item(item_id: str, payload: BenchItemUpdate, session: SessionDep):
    item = _get_or_404(session, item_id)
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    item.updated_at = utcnow()
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: str, session: SessionDep):
    session.delete(_get_or_404(session, item_id))
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
