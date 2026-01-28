"""
Celery Application Configuration

Task queue for long-running generation tasks.
"""

from celery import Celery
from typing import Optional

from app.config import settings


# Create Celery app
celery_app = Celery(
    "novel_ai",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,  # Don't prefetch, tasks are long
    task_acks_late=True,  # Ack after completion for reliability
)

# Pause signals (in production, use Redis pub/sub)
_pause_signals: set = set()


def signal_pause(project_id: int):
    """Signal a project to pause."""
    _pause_signals.add(project_id)


def check_pause(project_id: int) -> bool:
    """Check if a project should pause."""
    return project_id in _pause_signals


def clear_pause(project_id: int):
    """Clear pause signal after pausing."""
    _pause_signals.discard(project_id)


# ==================== TASKS ====================

@celery_app.task(bind=True, name="generate_outline")
def generate_outline_task(
    self,
    project_id: int,
    num_chapters: int = 20,
    additional_instructions: Optional[str] = None,
):
    """
    Generate the novel outline (Bible).
    
    This task:
    1. Creates the novel bible via Architect agent
    2. Saves to database
    3. Indexes in vector database
    4. Updates project status to await approval
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    
    from app.config import settings
    from app.db.models import Project
    from app.workflows.initialization import InitializationWorkflow
    
    async def run():
        # Create async session for this task
        engine = create_async_engine(settings.database_url)
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        
        async with async_session() as db:
            # Get project
            project = await db.get(Project, project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
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
            
            return {
                "project_id": project_id,
                "title": bible.title,
                "chapters": len(bible.chapters),
                "characters": len(bible.characters),
            }
    
    return asyncio.run(run())


@celery_app.task(bind=True, name="generate_chapters")
def generate_chapters_task(
    self,
    project_id: int,
    start_chapter: Optional[int] = None,
):
    """
    Generate novel chapters.
    
    This task:
    1. Runs the chapter loop for each chapter
    2. Updates progress via WebSocket
    3. Handles pause signals
    4. Updates project status on completion
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    
    from app.config import settings
    from app.db.models import Project
    from app.workflows.chapter_loop import ChapterLoopWorkflow, ChapterProgress
    
    async def run():
        engine = create_async_engine(settings.database_url)
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        
        async with async_session() as db:
            project = await db.get(Project, project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            workflow = ChapterLoopWorkflow(
                project_id=project_id,
                db=db,
                style_guide=project.style_guide,
                pov=project.pov,
                tone=project.tone,
            )
            
            def progress_callback(progress: ChapterProgress):
                # Update task state for monitoring
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "chapter": progress.chapter_number,
                        "beats_complete": progress.completed_beats,
                        "total_beats": progress.total_beats,
                        "word_count": progress.current_word_count,
                    }
                )
                
                # Check for pause signal
                if check_pause(project_id):
                    clear_pause(project_id)
                    raise InterruptedError("Generation paused by user")
            
            try:
                results = await workflow.generate_all_chapters(
                    start_chapter=start_chapter or 1,
                    progress_callback=progress_callback,
                )
                
                return {
                    "project_id": project_id,
                    "chapters_generated": len(results),
                    "total_words": sum(len(text.split()) for text in results.values()),
                }
            
            except InterruptedError:
                # Handle pause
                project.status = "paused"
                await db.commit()
                return {"project_id": project_id, "status": "paused"}
    
    return asyncio.run(run())


@celery_app.task(bind=True, name="revise_outline")
def revise_outline_task(
    self,
    project_id: int,
    feedback: str,
):
    """Revise the outline based on user feedback."""
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    
    from app.config import settings
    from app.db.models import Project
    from app.workflows.initialization import InitializationWorkflow
    
    async def run():
        engine = create_async_engine(settings.database_url)
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        
        async with async_session() as db:
            workflow = InitializationWorkflow(project_id, db)
            bible = await workflow.revise_outline(feedback)
            
            return {
                "project_id": project_id,
                "status": "outline_pending_approval",
            }
    
    return asyncio.run(run())
