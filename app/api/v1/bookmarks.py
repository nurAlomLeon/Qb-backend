from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_tenant
from app.models.university import University
from app.models.user import User
from app.schemas.common import Envelope, MessageOut
from app.schemas.user import BookmarkCreateIn, BookmarkOut
from app.services import bookmarks as bookmark_service
from app.services import content as content_service

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


@router.get("", response_model=Envelope[List[BookmarkOut]])
def list_bookmarks(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Envelope[List[BookmarkOut]]:
    return Envelope(data=bookmark_service.list_bookmarks(db, user))


@router.post("", response_model=Envelope[BookmarkOut], status_code=201)
def create_bookmark(
    payload: BookmarkCreateIn,
    db: Session = Depends(get_db),
    tenant: University = Depends(get_tenant),
    user: User = Depends(get_current_user),
) -> Envelope[BookmarkOut]:
    question = content_service.get_question(db, tenant.id, payload.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found.")
    return Envelope(data=bookmark_service.add_bookmark(db, user, question))


@router.delete("/{question_id}", status_code=204)
def delete_bookmark(
    question_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    removed = bookmark_service.remove_bookmark(db, user, question_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Bookmark not found.")
    return Response(status_code=204)


@router.delete("", response_model=Envelope[MessageOut])
def clear_bookmarks(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Envelope[MessageOut]:
    count = bookmark_service.clear_bookmarks(db, user)
    return Envelope(
        data=MessageOut(message="Cleared {count} bookmarks.".format(count=count))
    )
