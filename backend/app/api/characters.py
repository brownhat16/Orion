"""
Characters API Routes

CRUD operations for characters.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import Character, Project

router = APIRouter()


# ==================== SCHEMAS ====================

class CharacterCreate(BaseModel):
    """Schema for creating a new character."""
    project_id: int
    name: str = Field(..., min_length=1, max_length=200)
    role: str = Field(..., min_length=1, max_length=100)
    bio: str = Field(..., min_length=10)
    appearance: Optional[str] = None
    personality: Optional[str] = None
    backstory: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None


class CharacterUpdate(BaseModel):
    """Schema for updating a character."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    role: Optional[str] = Field(None, min_length=1, max_length=100)
    bio: Optional[str] = Field(None, min_length=10)
    appearance: Optional[str] = None
    personality: Optional[str] = None
    backstory: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None


class CharacterResponse(BaseModel):
    """Character response schema."""
    id: int
    project_id: int
    name: str
    role: str
    bio: str
    appearance: Optional[str] = None
    personality: Optional[str] = None
    backstory: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


# ==================== ROUTES ====================

@router.post("/", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
async def create_character(
    character_data: CharacterCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new character manually."""
    project = await db.get(Project, character_data.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    new_character = Character(
        project_id=character_data.project_id,
        name=character_data.name,
        role=character_data.role,
        bio=character_data.bio,
        appearance=character_data.appearance,
        personality=character_data.personality,
        backstory=character_data.backstory,
        attributes=character_data.attributes
    )
    
    db.add(new_character)
    await db.commit()
    await db.refresh(new_character)
    
    return new_character


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a single character."""
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
    return character


@router.patch("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: int,
    updates: CharacterUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update character details."""
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
        
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(character, field, value)
        
    await db.commit()
    await db.refresh(character)
    return character


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(
    character_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a character."""
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
        
    await db.delete(character)
    await db.commit()
