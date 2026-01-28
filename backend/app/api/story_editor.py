"""
Story Editor API Routes

Line-by-line story writing with AI suggestions.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import asyncio

from app.db.session import get_db
from app.db.models import Project, Chapter
from app.agents.ghostwriter import GhostwriterAgent
from app.agents.lorekeeper import LorekeeperAgent


router = APIRouter()


# ==================== SCHEMAS ====================

class SuggestRequest(BaseModel):
    """Request for AI suggestions."""
    current_text: str = Field(default="", description="The story content so far")
    chapter_id: Optional[int] = Field(default=None, description="Current chapter ID")
    num_suggestions: int = Field(default=3, ge=1, le=5, description="Number of suggestions")
    context_hint: Optional[str] = Field(default=None, description="Optional hint for the AI")


class Suggestion(BaseModel):
    """A single AI suggestion."""
    id: int
    content: str
    reasoning: str


class SuggestResponse(BaseModel):
    """Response with multiple suggestions."""
    suggestions: List[Suggestion]


class SaveLineRequest(BaseModel):
    """Request to save a line of story."""
    chapter_id: int
    content: str
    line_index: Optional[int] = None  # None means append


class StoryContent(BaseModel):
    """Full story content as lines."""
    chapter_id: int
    chapter_title: str
    lines: List[str]
    total_words: int


# ==================== ROUTES ====================

@router.post("/{project_id}/suggest", response_model=SuggestResponse)
async def get_suggestions(
    project_id: int,
    request: SuggestRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Get AI suggestions for the next line/paragraph of the story.
    
    Returns multiple options the user can choose from, edit, or regenerate.
    """
    project = await db.get(Project, project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get character and world context using Lorekeeper
    lorekeeper = LorekeeperAgent(project_id=project_id)
    
    # Get context from the project outline if available
    character_context = ""
    world_context = ""
    
    if project.outline:
        if isinstance(project.outline, dict):
            character_context = project.outline.get("characters_summary", "")
            world_context = project.outline.get("world_summary", "")
    
    # Try to get richer context from vector store
    try:
        if request.current_text:
            # Use last 500 chars as query
            query = request.current_text[-500:] if len(request.current_text) > 500 else request.current_text
            world_context_rag = await lorekeeper.get_world_context(query, top_k=3)
            if world_context_rag:
                world_context = world_context_rag
    except Exception:
        pass  # Fall back to outline context
    
    # Create Ghostwriter agent for suggestions
    ghostwriter = GhostwriterAgent(
        pov="third_limited",
        tone=project.genre or "literary",
    )
    
    # Generate multiple suggestions
    suggestions = []
    
    for i in range(request.num_suggestions):
        try:
            suggestion_prompt = f"""Continue this story with one paragraph (2-4 sentences):

**STORY SO FAR:**
{request.current_text if request.current_text else "[This is the beginning of the story. Write an engaging opening.]"}

{f"**CHARACTER CONTEXT:** {character_context}" if character_context else ""}
{f"**WORLD CONTEXT:** {world_context}" if world_context else ""}
{f"**ADDITIONAL GUIDANCE:** {request.context_hint}" if request.context_hint else ""}

Write the next paragraph. Make it {['vivid and sensory', 'action-driven', 'emotionally resonant'][i % 3]}.
Be creative and different from other suggestions.
Output ONLY the paragraph, no explanation."""

            response = await ghostwriter.invoke(suggestion_prompt)
            
            # Clean up the response
            content = response.content.strip()
            
            # Generate reasoning
            reasoning_types = [
                "Focuses on sensory details and atmosphere",
                "Advances the plot with action",
                "Deepens emotional connection with characters"
            ]
            
            suggestions.append(Suggestion(
                id=i + 1,
                content=content,
                reasoning=reasoning_types[i % 3]
            ))
        except Exception as e:
            # If generation fails, add a placeholder
            suggestions.append(Suggestion(
                id=i + 1,
                content=f"[Generation failed: {str(e)[:50]}]",
                reasoning="Error occurred during generation"
            ))
    
    return SuggestResponse(suggestions=suggestions)


@router.post("/{project_id}/suggest/stream")
async def get_suggestions_stream(
    project_id: int,
    request: SuggestRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Stream AI suggestions as they're generated.
    
    Uses Server-Sent Events format.
    """
    project = await db.get(Project, project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    async def generate():
        ghostwriter = GhostwriterAgent(
            pov="third_limited",
            tone=project.genre or "literary",
        )
        
        for i in range(request.num_suggestions):
            yield f"data: {json.dumps({'event': 'start', 'suggestion_id': i + 1})}\n\n"
            
            try:
                suggestion_prompt = f"""Continue this story with one paragraph (2-4 sentences):

**STORY SO FAR:**
{request.current_text if request.current_text else "[Beginning of story - write an engaging opening.]"}

Write the next paragraph. Be creative. Output ONLY the paragraph."""

                response = await ghostwriter.invoke(suggestion_prompt)
                content = response.content.strip()
                
                yield f"data: {json.dumps({'event': 'complete', 'suggestion_id': i + 1, 'content': content})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'event': 'error', 'suggestion_id': i + 1, 'error': str(e)[:100]})}\n\n"
            
            await asyncio.sleep(0.1)  # Small delay between suggestions
        
        yield f"data: {json.dumps({'event': 'done'})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/{project_id}/save-line")
async def save_line(
    project_id: int,
    request: SaveLineRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Save a line/paragraph to the story.
    """
    project = await db.get(Project, project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    chapter = await db.get(Chapter, request.chapter_id)
    
    if not chapter or chapter.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    
    # Get current content
    current_content = chapter.raw_text or ""
    lines = current_content.split("\n\n") if current_content else []
    
    # Add or update line
    if request.line_index is not None and request.line_index < len(lines):
        lines[request.line_index] = request.content
    else:
        lines.append(request.content)
    
    # Update chapter
    chapter.raw_text = "\n\n".join(lines)
    chapter.word_count = len(chapter.raw_text.split())
    
    # Update project totals
    result = await db.execute(
        select(Chapter).where(Chapter.project_id == project_id)
    )
    all_chapters = result.scalars().all()
    project.total_words = sum(c.word_count or 0 for c in all_chapters)
    
    await db.commit()
    
    return {
        "message": "Line saved",
        "chapter_id": chapter.id,
        "line_count": len(lines),
        "word_count": chapter.word_count,
    }


@router.get("/{project_id}/chapter/{chapter_id}/content", response_model=StoryContent)
async def get_chapter_content(
    project_id: int,
    chapter_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the full content of a chapter as lines.
    """
    project = await db.get(Project, project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    chapter = await db.get(Chapter, chapter_id)
    
    if not chapter or chapter.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    
    content = chapter.raw_text or ""
    lines = content.split("\n\n") if content else []
    
    return StoryContent(
        chapter_id=chapter.id,
        chapter_title=chapter.title or f"Chapter {chapter.order}",
        lines=lines,
        total_words=chapter.word_count or 0,
    )


@router.post("/{project_id}/create-draft-chapter")
async def create_draft_chapter(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new draft chapter for writing.
    """
    project = await db.get(Project, project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get highest chapter order
    result = await db.execute(
        select(Chapter)
        .where(Chapter.project_id == project_id)
        .order_by(Chapter.order.desc())
    )
    chapters = result.scalars().all()
    next_order = (chapters[0].order + 1) if chapters else 1
    
    # Create new chapter
    new_chapter = Chapter(
        project_id=project_id,
        order=next_order,
        title=f"Chapter {next_order}",
        summary="Draft chapter - add summary",
        raw_text="",
        status="draft",
        word_count=0,
    )
    
    db.add(new_chapter)
    await db.commit()
    await db.refresh(new_chapter)
    
    return {
        "message": "Draft chapter created",
        "chapter": {
            "id": new_chapter.id,
            "order": new_chapter.order,
            "title": new_chapter.title,
        }
    }
