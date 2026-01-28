"""
Chapters API Routes

CRUD operations for chapters.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import Chapter, Project

router = APIRouter()


# ==================== SCHEMAS ====================

class ChapterCreate(BaseModel):
    """Schema for creating a new chapter."""
    project_id: int
    title: str = Field(..., min_length=1, max_length=500)
    summary: str = Field(..., min_length=10)
    order: Optional[int] = None  # If None, appends to end


class ChapterUpdate(BaseModel):
    """Schema for updating a chapter."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    summary: Optional[str] = Field(None, min_length=10)
    order: Optional[int] = None
    status: Optional[str] = None


class ChapterResponse(BaseModel):
    """Chapter response schema."""
    id: int
    project_id: int
    order: int
    title: str
    summary: str
    status: str
    word_count: int
    
    class Config:
        from_attributes = True


# ==================== ROUTES ====================

@router.post("/", response_model=ChapterResponse, status_code=status.HTTP_201_CREATED)
async def create_chapter(
    chapter_data: ChapterCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new chapter manually."""
    project = await db.get(Project, chapter_data.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Determine order
    if chapter_data.order is None:
        result = await db.execute(
            select(Chapter)
            .where(Chapter.project_id == chapter_data.project_id)
            .order_by(Chapter.order.desc())
            .limit(1)
        )
        last_chapter = result.scalar_one_or_none()
        order = (last_chapter.order + 1) if last_chapter else 1
    else:
        order = chapter_data.order
        # Note: Handling order shifting would be complex, skipping for now
        # Assuming user/UI handles collisions or we allow duplicates temporarily

    new_chapter = Chapter(
        project_id=chapter_data.project_id,
        order=order,
        title=chapter_data.title,
        summary=chapter_data.summary,
        status="pending",
        word_count=0
    )
    
    db.add(new_chapter)
    await db.commit()
    await db.refresh(new_chapter)
    
    return new_chapter


@router.get("/{chapter_id}", response_model=ChapterResponse)
async def get_chapter(
    chapter_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a single chapter."""
    chapter = await db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    return chapter


@router.patch("/{chapter_id}", response_model=ChapterResponse)
async def update_chapter(
    chapter_id: int,
    updates: ChapterUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update chapter metdata."""
    chapter = await db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
        
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(chapter, field, value)
        
    await db.commit()
    await db.refresh(chapter)
    return chapter


@router.delete("/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chapter(
    chapter_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a chapter."""
    chapter = await db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
        
    await db.delete(chapter)
    await db.commit()
