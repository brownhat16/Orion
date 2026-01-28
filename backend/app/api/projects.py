"""
Projects API Routes

CRUD operations for novel projects.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import Project, Character, Chapter, ProjectStatus


router = APIRouter()


# ==================== SCHEMAS ====================

class ProjectCreate(BaseModel):
    """Schema for creating a new project."""
    title: str = Field(..., min_length=1, max_length=500)
    premise: str = Field(..., min_length=10)
    genre: str = Field(..., min_length=1, max_length=100)
    style_guide: Optional[str] = None
    tone: Optional[str] = "literary"
    pov: Optional[str] = "third_limited"


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    title: Optional[str] = None
    premise: Optional[str] = None
    style_guide: Optional[str] = None
    tone: Optional[str] = None


class CharacterResponse(BaseModel):
    """Character response schema."""
    id: int
    name: str
    role: str
    bio: str
    appearance: Optional[str] = None
    personality: Optional[str] = None
    
    class Config:
        from_attributes = True


class ChapterResponse(BaseModel):
    """Chapter response schema."""
    id: int
    order: int
    title: str
    summary: str
    status: str
    word_count: int
    
    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    """Full project response."""
    id: int
    title: str
    premise: str
    genre: str
    status: str
    current_chapter: int
    total_words: int
    total_tokens_used: int
    style_guide: Optional[str] = None
    tone: Optional[str] = None
    pov: Optional[str] = None
    outline: Optional[dict] = None
    
    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Simplified project for list views."""
    id: int
    title: str
    genre: str
    status: str
    total_words: int
    
    class Config:
        from_attributes = True


class OutlineApproval(BaseModel):
    """Schema for approving or revising outline."""
    approved: bool
    feedback: Optional[str] = None


# ==================== ROUTES ====================

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new novel project.
    
    This creates the project record but does not start generation.
    Use POST /projects/{id}/generate to start outline generation.
    """
    project = Project(
        user_id="default",  # Would come from auth
        title=project_data.title,
        premise=project_data.premise,
        genre=project_data.genre,
        style_guide=project_data.style_guide,
        tone=project_data.tone,
        pov=project_data.pov,
        status=ProjectStatus.DRAFT.value,
    )
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return project


@router.get("/", response_model=List[ProjectListResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List all projects for the current user."""
    result = await db.execute(
        select(Project)
        .where(Project.user_id == "default")  # Would filter by auth user
        .order_by(Project.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    projects = result.scalars().all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a single project by ID."""
    project = await db.get(Project, project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    updates: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update project metadata."""
    project = await db.get(Project, project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Apply updates
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    await db.commit()
    await db.refresh(project)
    
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a project and all associated data."""
    project = await db.get(Project, project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Delete from vector DB
    try:
        from app.agents.lorekeeper import LorekeeperAgent
        lorekeeper = LorekeeperAgent(project_id)
        await lorekeeper.delete_project_data()
    except Exception as e:
        # Log error but continue with DB deletion
        print(f"Failed to delete vector data for project {project_id}: {e}")
    
    # Delete from database (cascades to related entities)
    await db.delete(project)
    await db.commit()


@router.get("/{project_id}/characters", response_model=List[CharacterResponse])
async def get_project_characters(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all characters for a project."""
    result = await db.execute(
        select(Character)
        .where(Character.project_id == project_id)
        .order_by(Character.name)
    )
    
    return result.scalars().all()


@router.get("/{project_id}/chapters", response_model=List[ChapterResponse])
async def get_project_chapters(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all chapters for a project."""
    result = await db.execute(
        select(Chapter)
        .where(Chapter.project_id == project_id)
        .order_by(Chapter.order)
    )
    
    return result.scalars().all()


@router.get("/{project_id}/chapters/{chapter_number}")
async def get_chapter_content(
    project_id: int,
    chapter_number: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific chapter's content."""
    result = await db.execute(
        select(Chapter)
        .where(Chapter.project_id == project_id)
        .where(Chapter.order == chapter_number)
    )
    
    chapter = result.scalar_one_or_none()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    
    return {
        "id": chapter.id,
        "order": chapter.order,
        "title": chapter.title,
        "summary": chapter.summary,
        "content": chapter.raw_text,
        "word_count": chapter.word_count,
        "status": chapter.status,
    }


@router.post("/{project_id}/approve-outline", response_model=ProjectResponse)
async def approve_outline(
    project_id: int,
    approval: OutlineApproval,
    db: AsyncSession = Depends(get_db),
):
    """
    Approve or request revision of the generated outline.
    
    If approved, the project status changes to allow chapter generation.
    If not approved, feedback is used to regenerate the outline.
    """
    project = await db.get(Project, project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project.status != "outline_pending_approval":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project is in '{project.status}' state, not awaiting approval"
        )
    
    if approval.approved:
        project.status = ProjectStatus.OUTLINE_APPROVED.value
        await db.commit()
        await db.refresh(project)
        return project
    else:
        # Queue outline revision
        from app.tasks.celery_app import revise_outline_task
        revise_outline_task.delay(project_id, approval.feedback)
        
        return project


@router.get("/{project_id}/export")
async def export_manuscript(
    project_id: int,
    format: str = "markdown",
    db: AsyncSession = Depends(get_db),
):
    """
    Export the complete manuscript.
    
    Formats: markdown, txt, docx (future)
    """
    project = await db.get(Project, project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get all chapters
    result = await db.execute(
        select(Chapter)
        .where(Chapter.project_id == project_id)
        .where(Chapter.status == "completed")
        .order_by(Chapter.order)
    )
    
    chapters = result.scalars().all()
    
    if format == "markdown":
        content = f"# {project.title}\n\n"
        content += f"*{project.genre}*\n\n---\n\n"
        
        for chapter in chapters:
            content += f"## Chapter {chapter.order}: {chapter.title}\n\n"
            content += chapter.raw_text or ""
            content += "\n\n---\n\n"
        
        return {
            "filename": f"{project.title.replace(' ', '_')}.md",
            "content": content,
            "word_count": sum(c.word_count for c in chapters),
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format: {format}"
        )
