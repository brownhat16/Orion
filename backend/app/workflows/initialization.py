"""
Initialization Workflow

Phase 1 of novel generation - creates the "Bible" (outline, characters, world).
Includes human-in-the-loop approval.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.architect import ArchitectAgent, NovelBible
from app.agents.lorekeeper import LorekeeperAgent
from app.db.models import Project, Character, Chapter, LorebookEntry


class InitializationWorkflow:
    """
    Handles the initialization phase:
    1. Generate novel bible from premise
    2. Store in database
    3. Index in vector database
    4. Await human approval
    """
    
    def __init__(self, project_id: int, db: AsyncSession):
        self.project_id = project_id
        self.db = db
        self.architect = ArchitectAgent()
    
    async def generate_bible(
        self,
        premise: str,
        genre: str,
        num_chapters: int = 20,
        additional_instructions: Optional[str] = None,
    ) -> NovelBible:
        """
        Generate the novel bible from a premise.
        
        This is the first step - creates everything needed to start writing.
        """
        bible = await self.architect.create_novel_bible(
            premise=premise,
            genre=genre,
            num_chapters=num_chapters,
            additional_instructions=additional_instructions,
        )
        
        return bible
    
    async def save_bible_to_db(
        self,
        bible: NovelBible,
    ) -> None:
        """
        Persist the generated bible to the database.
        
        Creates:
        - Updates Project with outline
        - Character records
        - Chapter records
        - Lorebook entries for world rules
        """
        # Get project
        project = await self.db.get(Project, self.project_id)
        if not project:
            raise ValueError(f"Project {self.project_id} not found")
        
        # Update project
        project.title = bible.title
        project.outline = {
            "logline": bible.logline,
            "synopsis": bible.synopsis,
            "themes": bible.themes,
            "tone": bible.tone,
            "setting": bible.setting,
        }
        project.status = "outline_pending_approval"
        
        # Create characters
        for char in bible.characters:
            db_char = Character(
                project_id=self.project_id,
                name=char.name,
                role=char.role,
                bio=char.backstory,
                appearance=char.appearance,
                personality=char.personality,
                attributes={
                    "age": char.age,
                    "occupation": char.occupation,
                    "motivation": char.motivation,
                    "arc": char.arc,
                    "relationships": char.relationships,
                },
            )
            self.db.add(db_char)
        
        # Create chapters
        for chap in bible.chapters:
            db_chapter = Chapter(
                project_id=self.project_id,
                order=chap.number,
                title=chap.title,
                summary=chap.summary,
                goals="\n".join(chap.key_events),
                status="pending",
            )
            self.db.add(db_chapter)
        
        # Create lorebook entries for world rules
        for rule in bible.world_rules:
            entry = LorebookEntry(
                project_id=self.project_id,
                entity_name=rule.name,
                entity_type=rule.category,
                description=rule.description,
                metadata={"constraints": rule.constraints},
            )
            self.db.add(entry)
        
        await self.db.commit()
    
    async def index_in_vector_db(self) -> None:
        """
        Index all created entities in the vector database.
        
        This enables RAG-based retrieval during writing.
        """
        from sqlalchemy import select
        
        lorekeeper = LorekeeperAgent(self.project_id)
        
        # Index characters
        result = await self.db.execute(
            select(Character).where(Character.project_id == self.project_id)
        )
        characters = result.scalars().all()
        
        for char in characters:
            embedding_id = await lorekeeper.index_character(
                character_id=char.id,
                name=char.name,
                bio=char.bio,
                appearance=char.appearance or "",
                personality=char.personality or "",
                attributes=char.attributes or {},
            )
            char.embedding_id = embedding_id
        
        # Index lorebook entries
        result = await self.db.execute(
            select(LorebookEntry).where(LorebookEntry.project_id == self.project_id)
        )
        entries = result.scalars().all()
        
        for entry in entries:
            embedding_id = await lorekeeper.index_lorebook_entry(
                entry_id=entry.id,
                entity_name=entry.entity_name,
                entity_type=entry.entity_type,
                description=entry.description,
            )
            entry.embedding_id = embedding_id
        
        await self.db.commit()
    
    async def run(
        self,
        premise: str,
        genre: str,
        num_chapters: int = 20,
        additional_instructions: Optional[str] = None,
    ) -> NovelBible:
        """
        Run the complete initialization workflow.
        
        Returns the bible for human review before approval.
        """
        # Generate
        bible = await self.generate_bible(
            premise=premise,
            genre=genre,
            num_chapters=num_chapters,
            additional_instructions=additional_instructions,
        )
        
        # Save to DB
        await self.save_bible_to_db(bible)
        
        # Index in vector DB
        await self.index_in_vector_db()
        
        return bible
    
    async def approve_outline(self) -> None:
        """Mark the outline as approved, enabling chapter generation."""
        project = await self.db.get(Project, self.project_id)
        if not project:
            raise ValueError(f"Project {self.project_id} not found")
        
        project.status = "outline_approved"
        await self.db.commit()
    
    async def revise_outline(self, feedback: str) -> NovelBible:
        """
        Revise the outline based on user feedback.
        
        Regenerates and updates the database.
        """
        # Get current bible from project
        project = await self.db.get(Project, self.project_id)
        if not project or not project.outline:
            raise ValueError("No outline to revise")
        
        # Use architect to revise
        # This would need to reconstruct the current bible from DB
        # For now, placeholder
        
        # Re-save and re-index
        # ...
        
        return None  # Placeholder
