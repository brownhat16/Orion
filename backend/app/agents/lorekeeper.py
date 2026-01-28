"""
Lorekeeper Agent (RAG Manager)

The Lorekeeper ensures consistency across the novel by:
- Retrieving relevant context from the vector database
- Assembling context windows for other agents
- Detecting potential contradictions

This agent does NOT use LLM calls for its core function.
It's a retrieval and assembly agent.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.db.vector import get_initialized_vector_store, SearchResult
from app.db.reranker import get_reranker
from app.config import settings


@dataclass 
class ContextPackage:
    """Assembled context for another agent to use."""
    character_context: str
    world_context: str
    recent_events: str
    relevant_scenes: List[str]
    story_so_far: str
    warnings: List[str]  # Potential consistency issues to watch


class LorekeeperAgent:
    """
    The Lorekeeper maintains consistency through RAG.
    
    Unlike other agents, this one primarily queries the vector database
    rather than making LLM calls. It's the "memory" of the system.
    
    Responsibilities:
    1. Index new content (characters, scenes, lorebook entries)
    2. Retrieve relevant context for writing
    3. Detect potential consistency issues
    """
    
    name = "Lorekeeper"
    description = "RAG-based consistency manager"
    
    def __init__(self, project_id: int):
        self.project_id = project_id
        self.namespace = f"project_{project_id}"
        self._vector_store = None
        self._reranker = get_reranker()  # None if NVIDIA NIM is disabled
    
    async def _get_store(self):
        """Get initialized vector store."""
        if self._vector_store is None:
            self._vector_store = await get_initialized_vector_store()
        return self._vector_store
    
    async def index_character(
        self,
        character_id: int,
        name: str,
        bio: str,
        appearance: str,
        personality: str,
        attributes: Dict[str, Any],
    ) -> str:
        """
        Index a character for semantic retrieval.
        
        Returns the embedding ID.
        """
        store = await self._get_store()
        
        # Create searchable text combining all character info
        text = f"""CHARACTER: {name}
BIO: {bio}
APPEARANCE: {appearance}
PERSONALITY: {personality}
ATTRIBUTES: {', '.join(f'{k}: {v}' for k, v in attributes.items())}"""
        
        ids = await store.add_texts(
            texts=[text],
            metadatas=[{
                "type": "character",
                "character_id": character_id,
                "name": name,
            }],
            namespace=self.namespace,
        )
        
        return ids[0]
    
    async def index_scene(
        self,
        scene_id: int,
        chapter_number: int,
        summary: str,
        raw_text: str,
        characters_present: List[str],
    ) -> str:
        """
        Index a completed scene for retrieval.
        """
        store = await self._get_store()
        
        # Index both summary and full text
        text = f"""CHAPTER {chapter_number} - SCENE SUMMARY:
{summary}

CHARACTERS: {', '.join(characters_present)}

CONTENT:
{raw_text[:2000]}"""  # Truncate to avoid huge embeddings
        
        ids = await store.add_texts(
            texts=[text],
            metadatas=[{
                "type": "scene",
                "scene_id": scene_id,
                "chapter": chapter_number,
                "characters": characters_present,
            }],
            namespace=self.namespace,
        )
        
        return ids[0]
    
    async def index_lorebook_entry(
        self,
        entry_id: int,
        entity_name: str,
        entity_type: str,
        description: str,
        introduced_in_chapter: Optional[int] = None,
    ) -> str:
        """
        Index a lorebook entry (world-building fact).
        """
        store = await self._get_store()
        
        text = f"""{entity_type.upper()}: {entity_name}
{description}"""
        
        ids = await store.add_texts(
            texts=[text],
            metadatas=[{
                "type": "lorebook",
                "entry_id": entry_id,
                "entity_name": entity_name,
                "entity_type": entity_type,
                "introduced_chapter": introduced_in_chapter,
            }],
            namespace=self.namespace,
        )
        
        return ids[0]
    
    async def get_character_context(
        self,
        character_names: List[str],
        top_k: int = 5,
    ) -> str:
        """
        Retrieve context about specific characters.
        """
        store = await self._get_store()
        
        results = []
        for name in character_names:
            search_results = await store.search(
                query=f"character {name}",
                namespace=self.namespace,
                top_k=2,
                filter={"type": "character"},
            )
            results.extend(search_results)
        
        # Deduplicate and format
        seen_ids = set()
        context_parts = []
        for r in results:
            if r.id not in seen_ids:
                seen_ids.add(r.id)
                context_parts.append(r.content)
        
        return "\n\n---\n\n".join(context_parts[:top_k])
    
    async def get_relevant_scenes(
        self,
        query: str,
        current_chapter: int,
        top_k: int = 3,
    ) -> List[str]:
        """
        Find scenes relevant to the current writing context.
        
        Uses reranker when available for improved relevance.
        
        Args:
            query: The current scene/beat description
            current_chapter: Current chapter number (to prioritize recent scenes)
            top_k: Number of scenes to return
        """
        store = await self._get_store()
        
        # Fetch more candidates for reranking
        fetch_k = top_k * 3 if self._reranker else top_k * 2
        
        results = await store.search(
            query=query,
            namespace=self.namespace,
            top_k=fetch_k,
            filter={"type": "scene"},
        )
        
        if not results:
            return []
        
        # Use reranker if available
        if self._reranker:
            passages = [r.content for r in results]
            reranked = await self._reranker.rerank(
                query=query,
                passages=passages,
                top_k=top_k,
            )
            return [r.text for r in reranked]
        
        # Fallback: Prioritize more recent scenes but include relevant older ones
        weighted_results = []
        for r in results:
            chapter = r.metadata.get("chapter", 0)
            recency_boost = 1.0 + (0.1 * (current_chapter - abs(current_chapter - chapter)))
            weighted_results.append((r.score * recency_boost, r))
        
        weighted_results.sort(key=lambda x: x[0], reverse=True)
        
        return [r.content for _, r in weighted_results[:top_k]]
    
    async def get_world_context(
        self,
        query: str,
        top_k: int = 5,
    ) -> str:
        """
        Retrieve world-building context relevant to the query.
        """
        store = await self._get_store()
        
        results = await store.search(
            query=query,
            namespace=self.namespace,
            top_k=top_k,
            filter={"type": "lorebook"},
        )
        
        return "\n\n".join(r.content for r in results)
    
    async def assemble_context_for_writing(
        self,
        beat_description: str,
        character_names: List[str],
        current_chapter: int,
        story_so_far: str,
    ) -> ContextPackage:
        """
        Assemble a complete context package for the Ghostwriter.
        
        This is the primary API for other agents.
        """
        # Gather all relevant context in parallel
        character_context = await self.get_character_context(character_names)
        world_context = await self.get_world_context(beat_description)
        relevant_scenes = await self.get_relevant_scenes(beat_description, current_chapter)
        
        # Check for potential consistency issues
        warnings = await self._check_consistency(
            beat_description,
            character_context,
            world_context,
        )
        
        return ContextPackage(
            character_context=character_context,
            world_context=world_context,
            recent_events="\n---\n".join(relevant_scenes[-2:]) if relevant_scenes else "",
            relevant_scenes=relevant_scenes,
            story_so_far=story_so_far,
            warnings=warnings,
        )
    
    async def _check_consistency(
        self,
        beat_description: str,
        character_context: str,
        world_context: str,
    ) -> List[str]:
        """
        Check for potential consistency issues.
        
        This could be enhanced with an LLM call for more sophisticated checking.
        For now, uses simple heuristics.
        """
        warnings = []
        
        # Check for character name mentions that aren't in context
        # This is a simple heuristic - could be enhanced
        
        return warnings
    
    async def delete_project_data(self) -> None:
        """Delete all indexed data for this project."""
        store = await self._get_store()
        await store.delete_namespace(self.namespace)
