"""
SQLAlchemy Database Models

Core entities for the novel generation system:
- Project: Top-level container for a novel
- Character: Character profiles with embeddings
- Chapter: High-level chapter metadata
- Scene: Individual scenes within chapters
- Beat: Atomic story units within scenes
- LorebookEntry: World-building knowledge base
- TokenUsage: Cost tracking
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
    JSON, Boolean, Float, Enum, Index
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class ProjectStatus(str, PyEnum):
    """Status of a novel project."""
    DRAFT = "draft"
    OUTLINING = "outlining"
    OUTLINE_APPROVED = "outline_approved"
    GENERATING = "generating"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ChapterStatus(str, PyEnum):
    """Status of a chapter."""
    PENDING = "pending"
    BEATS_GENERATED = "beats_generated"
    WRITING = "writing"
    EDITING = "editing"
    COMPLETED = "completed"
    FAILED = "failed"


class Project(Base):
    """A novel project - the top-level container."""
    
    __tablename__ = "projects"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Core metadata
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    genre: Mapped[str] = mapped_column(String(100), nullable=False)
    premise: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Style configuration
    style_guide: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pov: Mapped[str] = mapped_column(String(50), default="third_limited")  # first, third_limited, third_omniscient
    
    # World-building (JSON for flexibility)
    world_rules: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Generated content
    outline: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    story_so_far: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Rolling summary
    
    # Status tracking
    status: Mapped[str] = mapped_column(String(50), default=ProjectStatus.DRAFT.value)
    current_chapter: Mapped[int] = mapped_column(Integer, default=0)
    total_words: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Relationships
    characters: Mapped[List["Character"]] = relationship(
        "Character", back_populates="project", cascade="all, delete-orphan"
    )
    chapters: Mapped[List["Chapter"]] = relationship(
        "Chapter", back_populates="project", cascade="all, delete-orphan", order_by="Chapter.order"
    )
    lorebook_entries: Mapped[List["LorebookEntry"]] = relationship(
        "LorebookEntry", back_populates="project", cascade="all, delete-orphan"
    )
    token_usages: Mapped[List["TokenUsage"]] = relationship(
        "TokenUsage", back_populates="project", cascade="all, delete-orphan"
    )


class Character(Base):
    """A character in the novel with semantic embedding for RAG."""
    
    __tablename__ = "characters"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    
    # Core info
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)  # protagonist, antagonist, supporting, etc.
    
    # Detailed profile
    bio: Mapped[str] = mapped_column(Text, nullable=False)
    appearance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    personality: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    backstory: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Flexible attributes (JSON)
    attributes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # e.g., {"age": 32, "occupation": "detective", "eye_color": "blue", "relationships": {...}}
    
    # Psychological state (can evolve)
    current_state: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Vector DB reference
    embedding_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Relationship
    project: Mapped["Project"] = relationship("Project", back_populates="characters")
    
    __table_args__ = (
        Index("idx_character_project_name", "project_id", "name"),
    )


class Chapter(Base):
    """A chapter in the novel."""
    
    __tablename__ = "chapters"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Planning
    summary: Mapped[str] = mapped_column(Text, nullable=False)  # What should happen
    goals: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Chapter objectives
    
    # Generated content
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default=ChapterStatus.PENDING.value)
    
    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="chapters")
    scenes: Mapped[List["Scene"]] = relationship(
        "Scene", back_populates="chapter", cascade="all, delete-orphan", order_by="Scene.order"
    )
    
    __table_args__ = (
        Index("idx_chapter_project_order", "project_id", "order"),
    )


class Scene(Base):
    """A scene within a chapter."""
    
    __tablename__ = "scenes"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapters.id"), nullable=False)
    
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Setting
    location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    time_of_day: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Generated content
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Vector DB reference for similarity search
    embedding_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending")
    
    # Relationship
    chapter: Mapped["Chapter"] = relationship("Chapter", back_populates="scenes")
    beats: Mapped[List["Beat"]] = relationship(
        "Beat", back_populates="scene", cascade="all, delete-orphan", order_by="Beat.order"
    )


class Beat(Base):
    """An atomic story beat - the smallest unit of narrative."""
    
    __tablename__ = "beats"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"), nullable=False)
    
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    beat_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # e.g., "action", "dialogue", "description", "internal_thought", "revelation"
    
    # Generated prose
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Editor feedback
    editor_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    revision_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending")
    # pending, written, editing, approved, rejected
    
    # Relationship
    scene: Mapped["Scene"] = relationship("Scene", back_populates="beats")


class LorebookEntry(Base):
    """
    World-building knowledge base entry.
    Used for RAG to maintain consistency across the novel.
    """
    
    __tablename__ = "lorebook_entries"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    
    entity_name: Mapped[str] = mapped_column(String(300), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # e.g., "location", "organization", "technology", "magic_system", "event", "relationship"
    
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Additional structured data
    entry_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # When this fact becomes relevant (for timeline-aware retrieval)
    introduced_in_chapter: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Vector DB reference
    embedding_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Relationship
    project: Mapped["Project"] = relationship("Project", back_populates="lorebook_entries")
    
    __table_args__ = (
        Index("idx_lorebook_project_type", "project_id", "entity_type"),
    )


class TokenUsage(Base):
    """
    Track token usage per agent call for cost monitoring.
    Essential for production to prevent runaway costs.
    """
    
    __tablename__ = "token_usages"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Cost in USD (approximate)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Context
    chapter_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    beat_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationship
    project: Mapped["Project"] = relationship("Project", back_populates="token_usages")
