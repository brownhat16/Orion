"""
Generation API Routes

Control novel generation - start, stop, pause, resume.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import Project, Chapter, ProjectStatus


router = APIRouter()


# ==================== SCHEMAS ====================

class GenerateRequest(BaseModel):
    """Request to start generation."""
    num_chapters: int = Field(default=20, ge=5, le=50)
    additional_instructions: Optional[str] = None


class GenerateOutlineRequest(BaseModel):
    """Request to generate/regenerate outline."""
    num_chapters: int = Field(default=20, ge=5, le=50)
    additional_instructions: Optional[str] = None


class GenerationStatus(BaseModel):
    """Current generation status."""
    project_id: int
    status: str
    phase: str
    current_chapter: int
    total_chapters: int
    current_chapter_progress: Optional[dict] = None
    total_words: int
    tokens_used: int
    estimated_cost: float


class ChapterGenerateRequest(BaseModel):
    """Request to generate a specific chapter."""
    chapter_number: int = Field(..., ge=1)


# ==================== ROUTES ====================

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from app.services import generation_logic

@router.post("/{project_id}/generate-outline")
async def generate_outline(
    project_id: int,
    request: GenerateOutlineRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate the novel outline (Bible).
    
    This is Phase 1 - creates characters, world, and chapter summaries.
    The project must be in DRAFT status.
    Returns immediately; use GET /status to track progress.
    """
    project = await db.get(Project, project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project.status not in [ProjectStatus.DRAFT.value, "outline_rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot generate outline: project is in '{project.status}' state"
        )
    
    # Update status
    project.status = ProjectStatus.OUTLINING.value
    await db.commit()
    
    # Try async task queue, fallback to background threads (Lite Mode)
    try:
        from app.tasks.celery_app import generate_outline_task
        task = generate_outline_task.delay(
            project_id=project_id,
            num_chapters=request.num_chapters,
            additional_instructions=request.additional_instructions,
        )
        return {
            "message": "Outline generation started",
            "task_id": task.id,
            "project_id": project_id,
            "mode": "production (celery)"
        }
    except Exception:
        # Fallback to local background task
        background_tasks.add_task(
            generation_logic.generate_outline_logic,
            project_id=project_id,
            num_chapters=request.num_chapters,
            additional_instructions=request.additional_instructions
        )
        return {
            "message": "Outline generation started (Lite Mode)",
            "task_id": None,
            "project_id": project_id,
            "mode": "lite (background_thread)",
            "note": "Running in free tier mode without Redis."
        }


@router.post("/{project_id}/generate-chapters")
async def generate_chapters(
    project_id: int,
    background_tasks: BackgroundTasks,
    request: Optional[ChapterGenerateRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Start chapter generation.
    """
    project = await db.get(Project, project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project.status != ProjectStatus.OUTLINE_APPROVED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot generate: outline must be approved first (current: {project.status})"
        )
    
    # Update status
    project.status = ProjectStatus.GENERATING.value
    await db.commit()
    
    # Try async task queue with fallback
    try:
        from app.tasks.celery_app import generate_chapters_task
        task = generate_chapters_task.delay(
            project_id=project_id,
            start_chapter=request.chapter_number if request else None,
        )
        return {
            "message": "Chapter generation started",
            "task_id": task.id,
            "project_id": project_id,
            "mode": "production (celery)"
        }
    except Exception:
        background_tasks.add_task(
            generation_logic.generate_chapters_logic,
            project_id=project_id,
            start_chapter=request.chapter_number if request else None,
        )
        return {
            "message": "Chapter generation started (Lite Mode)",
            "task_id": None,
            "project_id": project_id,
            "mode": "lite (background_thread)",
            "note": "Running in free tier mode without Redis."
        }


@router.post("/{project_id}/pause")
async def pause_generation(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Pause ongoing generation.
    """
    project = await db.get(Project, project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project.status != ProjectStatus.GENERATING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No generation in progress"
        )
    
    project.status = ProjectStatus.PAUSED.value
    await db.commit()
    
    # Signal the running task to stop (works for both modes)
    generation_logic.signal_pause(project_id)
    
    return {"message": "Pause signal sent", "project_id": project_id}


@router.post("/{project_id}/resume")
async def resume_generation(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Resume paused generation."""
    project = await db.get(Project, project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project.status != ProjectStatus.PAUSED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project is not paused"
        )
    
    project.status = ProjectStatus.GENERATING.value
    await db.commit()
    
    # Queue resumption (with fallback)
    try:
        from app.tasks.celery_app import generate_chapters_task
        task = generate_chapters_task.delay(
            project_id=project_id,
            start_chapter=project.current_chapter + 1,
        )
        return {
            "message": "Generation resumed",
            "task_id": task.id,
            "project_id": project_id,
            "mode": "production (celery)"
        }
    except Exception:
        background_tasks.add_task(
            generation_logic.generate_chapters_logic,
            project_id=project_id,
            start_chapter=project.current_chapter + 1,
        )
        return {
            "message": "Resume queued (Lite Mode)",
            "task_id": None,
            "project_id": project_id,
            "mode": "lite (background_thread)"
        }


@router.get("/{project_id}/status", response_model=GenerationStatus)
async def get_generation_status(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get current generation status.
    
    Includes progress, word count, and cost estimation.
    """
    project = await db.get(Project, project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get chapter count
    result = await db.execute(
        select(Chapter).where(Chapter.project_id == project_id)
    )
    chapters = result.scalars().all()
    
    # Calculate phase
    if project.status == ProjectStatus.OUTLINING.value:
        phase = "outline_generation"
    elif project.status == "outline_pending_approval":
        phase = "awaiting_approval"
    elif project.status == ProjectStatus.GENERATING.value:
        phase = "chapter_generation"
    elif project.status == ProjectStatus.COMPLETED.value:
        phase = "completed"
    else:
        phase = project.status
    
    # Get current chapter progress
    current_progress = None
    if project.status == ProjectStatus.GENERATING.value and chapters:
        current_chapter = next(
            (c for c in chapters if c.status == "generating"),
            None
        )
        if current_chapter:
            current_progress = {
                "chapter_number": current_chapter.order,
                "title": current_chapter.title,
                "status": current_chapter.status,
            }
    
    # Estimate cost (rough, would be more accurate with actual token tracking)
    estimated_cost = (project.total_tokens_used or 0) / 1_000_000 * 10  # ~$10/1M tokens avg
    
    return GenerationStatus(
        project_id=project_id,
        status=project.status,
        phase=phase,
        current_chapter=project.current_chapter or 0,
        total_chapters=len(chapters),
        current_chapter_progress=current_progress,
        total_words=project.total_words or 0,
        tokens_used=project.total_tokens_used or 0,
        estimated_cost=estimated_cost,
    )


@router.get("/{project_id}/cost-estimate")
async def estimate_cost(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Estimate the cost to complete generation.
    
    Based on remaining chapters and average tokens per chapter.
    """
    project = await db.get(Project, project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get chapter stats
    result = await db.execute(
        select(Chapter).where(Chapter.project_id == project_id)
    )
    chapters = result.scalars().all()
    
    completed = [c for c in chapters if c.status == "completed"]
    pending = [c for c in chapters if c.status == "pending"]
    
    # Calculate averages
    if completed:
        avg_words = sum(c.word_count for c in completed) / len(completed)
        avg_tokens = (project.total_tokens_used or 0) / len(completed) if completed else 50000
    else:
        avg_words = 2500
        avg_tokens = 50000  # Rough estimate
    
    remaining_chapters = len(pending)
    estimated_tokens = remaining_chapters * avg_tokens
    
    # Cost per million tokens (approximate)
    cost_per_million = {
        "input": 3.0,   # Average of GPT-4o and Claude
        "output": 12.0,
    }
    
    # Assume 70% input, 30% output
    estimated_cost = (
        estimated_tokens * 0.7 * cost_per_million["input"] / 1_000_000 +
        estimated_tokens * 0.3 * cost_per_million["output"] / 1_000_000
    )
    
    return {
        "remaining_chapters": remaining_chapters,
        "estimated_words": int(remaining_chapters * avg_words),
        "estimated_tokens": int(estimated_tokens),
        "estimated_cost_usd": round(estimated_cost, 2),
        "cost_so_far_usd": round((project.total_tokens_used or 0) / 1_000_000 * 10, 2),
    }
