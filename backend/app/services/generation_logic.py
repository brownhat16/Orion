"""
Core generation logic decoupled from Celery.
Used by both Celery tasks (production) and FastAPI BackgroundTasks (lite mode).
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.config import settings
from app.db.models import Project
from app.workflows.initialization import InitializationWorkflow
from app.workflows.chapter_loop import ChapterLoopWorkflow, ChapterProgress

# In-memory pause signals for Lite Mode / Single Worker
_pause_signals: set = set()

def signal_pause(project_id: int):
    """Signal a project to pause."""
    try:
        # Try Redis first if available
        from app.tasks.celery_app import signal_pause as redis_signal
        redis_signal(project_id)
    except:
        # Fallback to in-memory
        _pause_signals.add(project_id)

def check_pause(project_id: int) -> bool:
    """Check if a project should pause."""
    try:
        from app.tasks.celery_app import check_pause as redis_check
        if redis_check(project_id):
            return True
    except:
        pass
    return project_id in _pause_signals

def clear_pause(project_id: int):
    """Clear pause signal."""
    try:
        from app.tasks.celery_app import clear_pause as redis_clear
        redis_clear(project_id)
    except:
        pass
    _pause_signals.discard(project_id)


async def generate_outline_logic(
    project_id: int,
    num_chapters: int = 20,
    additional_instructions: Optional[str] = None,
):
    """Core logic for outline generation."""
    try:
        engine = create_async_engine(settings.database_url)
        # Use a new session factory for this background task
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        
        async with async_session() as db:
            # Get project
            project = await db.get(Project, project_id)
            if not project:
                print(f"Project {project_id} not found")
                return
            
            # Run initialization workflow
            workflow = InitializationWorkflow(project_id, db)
            
            bible = await workflow.run(
                premise=project.premise,
                genre=project.genre,
                num_chapters=num_chapters,
                additional_instructions=additional_instructions,
            )
            
            # Update status
            project.status = "outline_pending_approval"
            await db.commit()
            
            print(f"Outline generated for project {project_id}")
            
    except Exception as e:
        print(f"Error generating outline for {project_id}: {e}")
        # Could update project status to error here


async def generate_chapters_logic(
    project_id: int,
    start_chapter: Optional[int] = None,
    progress_callback_func = None # Optional callback for updates
):
    """Core logic for chapter generation."""
    try:
        engine = create_async_engine(settings.database_url)
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        
        async with async_session() as db:
            project = await db.get(Project, project_id)
            if not project:
                return
            
            workflow = ChapterLoopWorkflow(
                project_id=project_id,
                db=db,
                style_guide=project.style_guide,
                pov=project.pov,
                tone=project.tone,
            )
            
            def local_progress_callback(progress: ChapterProgress):
                # Check pause
                if check_pause(project_id):
                    clear_pause(project_id)
                    raise InterruptedError("Generation paused by user")
                
                # If we had a websocket manager, we'd emit here
                # For now, just logging
                print(f"Progress Project {project_id}: Chapter {progress.chapter_number}, Beat {progress.completed_beats}/{progress.total_beats}")
                
            
            try:
                await workflow.generate_all_chapters(
                    start_chapter=start_chapter or 1,
                    progress_callback=local_progress_callback,
                )
                print(f"Chapters generated for project {project_id}")
                
            except InterruptedError:
                project.status = "paused"
                await db.commit()
                print(f"Generation paused for project {project_id}")
                
    except Exception as e:
        print(f"Error generating chapters for {project_id}: {e}")


async def revise_outline_logic(
    project_id: int,
    feedback: str
):
    """Core logic for outline revision."""
    try:
        engine = create_async_engine(settings.database_url)
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        
        async with async_session() as db:
            workflow = InitializationWorkflow(project_id, db)
            await workflow.revise_outline(feedback)
            print(f"Outline revised for project {project_id}")
            
    except Exception as e:
        print(f"Error revising outline for {project_id}: {e}")
