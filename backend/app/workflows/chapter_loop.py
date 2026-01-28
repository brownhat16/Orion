"""
Chapter Loop Workflow

Phase 2 of novel generation - the main production loop.
Generates one chapter at a time with beat-by-beat prose generation.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.lorekeeper import LorekeeperAgent, ContextPackage
from app.agents.beater import BeaterAgent, SceneBeats
from app.agents.ghostwriter import GhostwriterAgent
from app.agents.editor import EditorAgent, EditingReport
from app.db.models import Project, Chapter, Scene, Beat, Character


@dataclass
class ChapterProgress:
    """Track progress through a chapter."""
    chapter_id: int
    chapter_number: int
    total_beats: int
    completed_beats: int
    current_word_count: int
    status: str
    current_beat_description: Optional[str] = None


class ChapterLoopWorkflow:
    """
    Handles the chapter generation loop:
    
    For each chapter:
    1. Fetch context from Lorekeeper
    2. Generate beats via Beater
    3. For each beat:
       - Write prose via Ghostwriter
       - Review via Editor
       - Rewrite if needed
    4. Update memory (story_so_far, index scenes)
    """
    
    def __init__(
        self,
        project_id: int,
        db: AsyncSession,
        style_guide: Optional[str] = None,
        pov: str = "third_limited",
        tone: str = "literary",
    ):
        self.project_id = project_id
        self.db = db
        
        # Initialize agents
        self.lorekeeper = LorekeeperAgent(project_id)
        self.beater = BeaterAgent()
        self.ghostwriter = GhostwriterAgent(
            style_guide=style_guide,
            pov=pov,
            tone=tone,
        )
        self.editor = EditorAgent()
        
        # Configuration
        self.max_revisions = 3
        self.min_acceptable_quality = 6
    
    async def _get_project(self) -> Project:
        """Get the project."""
        project = await self.db.get(Project, self.project_id)
        if not project:
            raise ValueError(f"Project {self.project_id} not found")
        return project
    
    async def _get_chapter(self, chapter_number: int) -> Chapter:
        """Get a specific chapter."""
        result = await self.db.execute(
            select(Chapter)
            .where(Chapter.project_id == self.project_id)
            .where(Chapter.order == chapter_number)
        )
        chapter = result.scalar_one_or_none()
        if not chapter:
            raise ValueError(f"Chapter {chapter_number} not found")
        return chapter
    
    async def _get_character_names(self, chapter: Chapter) -> List[str]:
        """Extract character names relevant to a chapter."""
        # In a real implementation, this would parse the chapter summary
        # or use stored metadata
        result = await self.db.execute(
            select(Character.name).where(Character.project_id == self.project_id)
        )
        return [r[0] for r in result.all()]
    
    async def generate_chapter(
        self,
        chapter_number: int,
        progress_callback: Optional[callable] = None,
    ) -> str:
        """
        Generate a complete chapter.
        
        Args:
            chapter_number: Which chapter to generate (1-indexed)
            progress_callback: Optional callback for progress updates
            
        Returns:
            The complete chapter text
        """
        project = await self._get_project()
        chapter = await self._get_chapter(chapter_number)
        
        # Update chapter status
        chapter.status = "generating"
        from datetime import datetime
        chapter.started_at = datetime.utcnow()
        await self.db.commit()
        
        # Step 1: Fetch context
        character_names = await self._get_character_names(chapter)
        context = await self.lorekeeper.assemble_context_for_writing(
            beat_description=chapter.summary,
            character_names=character_names,
            current_chapter=chapter_number,
            story_so_far=project.story_so_far or "",
        )
        
        # Step 2: Generate beats
        beats_result = await self.beater.generate_beats(
            scene_summary=chapter.summary,
            chapter_context=project.story_so_far or "",
            character_states={},  # Would extract from context
            target_word_count=2500,
        )
        
        # Store beats in database
        for i, beat_data in enumerate(beats_result.beats):
            # Create scene if needed (simplification - 1 scene per chapter for now)
            result = await self.db.execute(
                select(Scene).where(Scene.chapter_id == chapter.id)
            )
            scene = result.scalar_one_or_none()
            if not scene:
                scene = Scene(
                    chapter_id=chapter.id,
                    order=1,
                    summary=chapter.summary,
                )
                self.db.add(scene)
                await self.db.commit()
            
            db_beat = Beat(
                scene_id=scene.id,
                order=i + 1,
                description=beat_data.description,
                beat_type=beat_data.beat_type,
                status="pending",
            )
            self.db.add(db_beat)
        
        await self.db.commit()
        
        # Step 3: Write each beat
        chapter_text = ""
        
        result = await self.db.execute(
            select(Beat)
            .join(Scene)
            .where(Scene.chapter_id == chapter.id)
            .order_by(Beat.order)
        )
        beats = result.scalars().all()
        
        for i, beat in enumerate(beats):
            if progress_callback:
                progress_callback(ChapterProgress(
                    chapter_id=chapter.id,
                    chapter_number=chapter_number,
                    total_beats=len(beats),
                    completed_beats=i,
                    current_word_count=len(chapter_text.split()),
                    status="writing",
                    current_beat_description=beat.description,
                ))
            
            # Write beat with edit loop
            beat_text = await self._write_beat_with_editing(
                beat=beat,
                context=context,
                previous_text=chapter_text[-2000:] if chapter_text else "",
            )
            
            # Append to chapter
            chapter_text += "\n\n" + beat_text if chapter_text else beat_text
            
            # Update beat in DB
            beat.raw_text = beat_text
            beat.word_count = len(beat_text.split())
            beat.status = "completed"
            await self.db.commit()
        
        # Step 4: Finalize chapter
        chapter.raw_text = chapter_text
        chapter.word_count = len(chapter_text.split())
        chapter.status = "completed"
        chapter.completed_at = datetime.utcnow()
        
        # Update project progress
        project.current_chapter = chapter_number
        project.total_words = (project.total_words or 0) + chapter.word_count
        
        # Update story_so_far with chapter summary
        summary = await self._summarize_chapter(chapter_text)
        project.story_so_far = (project.story_so_far or "") + f"\n\nChapter {chapter_number}: {summary}"
        
        await self.db.commit()
        
        # Index the completed chapter in vector DB
        await self._index_chapter(chapter)
        
        return chapter_text
    
    async def _write_beat_with_editing(
        self,
        beat: Beat,
        context: ContextPackage,
        previous_text: str,
    ) -> str:
        """
        Write a beat with edit-revision loop.
        
        Attempts up to max_revisions if quality is below threshold.
        """
        # Extract sensory details (would come from beat generation)
        sensory_details = []  # Placeholder
        
        # Initial write
        output = await self.ghostwriter.write_beat(
            beat_description=beat.description,
            beat_type=beat.beat_type or "action",
            character_context=context.character_context,
            world_context=context.world_context,
            previous_text=previous_text,
            sensory_details=sensory_details,
            emotional_note="",  # Would come from beat data
        )
        
        prose = output.prose
        revision_count = 0
        
        # Edit loop
        while revision_count < self.max_revisions:
            # Get editor review
            report = await self.editor.review_prose(
                prose=prose,
                beat_description=beat.description,
                character_context=context.character_context,
                world_context=context.world_context,
                lorebook_facts=[],  # Would extract from context
            )
            
            # Check if acceptable
            if report.overall_quality >= self.min_acceptable_quality:
                break
            
            if not report.recommend_rewrite:
                break
            
            # Rewrite based on feedback
            feedback = report.summary + "\n" + "\n".join(
                f"- {issue.issue}: {issue.suggestion}"
                for issue in report.issues
                if issue.severity in ["critical", "major"]
            )
            
            prose = await self.ghostwriter.rewrite_with_feedback(
                original_prose=prose,
                feedback=feedback,
            )
            
            revision_count += 1
            beat.revision_count = revision_count
        
        return prose
    
    async def _summarize_chapter(self, chapter_text: str) -> str:
        """Generate a brief summary of the chapter for story_so_far."""
        # Would use an LLM call here
        # For now, simple truncation
        words = chapter_text.split()[:50]
        return " ".join(words) + "..."
    
    async def _index_chapter(self, chapter: Chapter) -> None:
        """Index the completed chapter in vector database."""
        result = await self.db.execute(
            select(Scene).where(Scene.chapter_id == chapter.id)
        )
        scenes = result.scalars().all()
        
        for scene in scenes:
            if scene.raw_text:
                await self.lorekeeper.index_scene(
                    scene_id=scene.id,
                    chapter_number=chapter.order,
                    summary=scene.summary,
                    raw_text=scene.raw_text,
                    characters_present=[],  # Would extract
                )
    
    async def generate_all_chapters(
        self,
        start_chapter: int = 1,
        progress_callback: Optional[callable] = None,
    ) -> Dict[int, str]:
        """
        Generate all remaining chapters.
        
        Args:
            start_chapter: Which chapter to start from
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dict mapping chapter number to chapter text
        """
        project = await self._get_project()
        
        result = await self.db.execute(
            select(Chapter)
            .where(Chapter.project_id == self.project_id)
            .where(Chapter.order >= start_chapter)
            .where(Chapter.status == "pending")
            .order_by(Chapter.order)
        )
        chapters = result.scalars().all()
        
        results = {}
        for chapter in chapters:
            text = await self.generate_chapter(
                chapter_number=chapter.order,
                progress_callback=progress_callback,
            )
            results[chapter.order] = text
        
        # Mark project as complete
        project.status = "completed"
        await self.db.commit()
        
        return results
