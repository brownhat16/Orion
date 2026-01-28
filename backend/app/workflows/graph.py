"""
LangGraph Novel Workflow

Defines the main state machine for novel generation.
Uses LangGraph for orchestrating the multi-agent system.
"""

from typing import TypedDict, List, Optional, Annotated, Literal
from enum import Enum
from dataclasses import dataclass, field

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from app.agents.architect import NovelBible, ChapterOutline
from app.agents.beater import SceneBeats, StoryBeat


class WorkflowPhase(str, Enum):
    """Current phase in the novel generation workflow."""
    INITIALIZATION = "initialization"
    AWAITING_APPROVAL = "awaiting_approval"
    CHAPTER_GENERATION = "chapter_generation"
    BEAT_WRITING = "beat_writing"
    EDITING = "editing"
    MEMORY_UPDATE = "memory_update"
    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"


class NovelState(TypedDict):
    """
    State object passed through the workflow.
    
    LangGraph uses this to track progress and pass data between nodes.
    """
    # Project metadata
    project_id: int
    user_id: str
    
    # Current phase
    phase: str
    
    # Bible (created in initialization)
    bible: Optional[dict]  # NovelBible as dict for serialization
    
    # Current progress
    current_chapter_idx: int
    current_scene_idx: int
    current_beat_idx: int
    
    # Working data
    current_chapter_outline: Optional[dict]
    current_scene_beats: Optional[dict]
    current_beat: Optional[dict]
    current_prose: Optional[str]
    
    # Context window
    story_so_far: str
    recent_scenes: List[str]  # Last 2-3 scenes for continuity
    
    # Accumulated content
    chapter_content: str  # Current chapter being built
    
    # Editor feedback
    editor_report: Optional[dict]
    revision_count: int
    
    # Token tracking
    total_tokens_used: int
    
    # Control flags
    needs_human_approval: bool
    should_pause: bool
    error_message: Optional[str]
    
    # Messages for debugging
    messages: Annotated[list, add_messages]


def create_initial_state(project_id: int, user_id: str) -> NovelState:
    """Create initial state for a new novel generation."""
    return NovelState(
        project_id=project_id,
        user_id=user_id,
        phase=WorkflowPhase.INITIALIZATION.value,
        bible=None,
        current_chapter_idx=0,
        current_scene_idx=0,
        current_beat_idx=0,
        current_chapter_outline=None,
        current_scene_beats=None,
        current_beat=None,
        current_prose=None,
        story_so_far="",
        recent_scenes=[],
        chapter_content="",
        editor_report=None,
        revision_count=0,
        total_tokens_used=0,
        needs_human_approval=False,
        should_pause=False,
        error_message=None,
        messages=[],
    )


class NovelWorkflow:
    """
    Main workflow orchestrator for novel generation.
    
    The workflow follows this high-level pattern:
    
    1. INITIALIZATION
       - Generate novel bible (outline, characters, world)
       - Wait for human approval
    
    2. CHAPTER LOOP (for each chapter)
       - Fetch context from Lorekeeper
       - Generate beats via Beater
       
       3. BEAT LOOP (for each beat)
          - Generate prose via Ghostwriter
          - Review via Editor
          - Rewrite if needed
       
       - Update memory (story_so_far, index scenes)
    
    4. COMPLETION
       - Final review
       - Export
    """
    
    def __init__(self, project_id: int, user_id: str):
        self.project_id = project_id
        self.user_id = user_id
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        
        # Create graph with state type
        workflow = StateGraph(NovelState)
        
        # Add nodes
        workflow.add_node("initialize", self._node_initialize)
        workflow.add_node("await_approval", self._node_await_approval)
        workflow.add_node("prepare_chapter", self._node_prepare_chapter)
        workflow.add_node("generate_beats", self._node_generate_beats)
        workflow.add_node("write_beat", self._node_write_beat)
        workflow.add_node("edit_beat", self._node_edit_beat)
        workflow.add_node("update_memory", self._node_update_memory)
        workflow.add_node("finalize_chapter", self._node_finalize_chapter)
        workflow.add_node("handle_error", self._node_handle_error)
        
        # Set entry point
        workflow.set_entry_point("initialize")
        
        # Add edges
        workflow.add_edge("initialize", "await_approval")
        
        # Conditional edge after approval
        workflow.add_conditional_edges(
            "await_approval",
            self._route_after_approval,
            {
                "continue": "prepare_chapter",
                "wait": "await_approval",
                "abort": END,
            }
        )
        
        workflow.add_edge("prepare_chapter", "generate_beats")
        workflow.add_edge("generate_beats", "write_beat")
        
        # Conditional edge after writing
        workflow.add_conditional_edges(
            "write_beat",
            self._route_after_write,
            {
                "edit": "edit_beat",
                "error": "handle_error",
            }
        )
        
        # Conditional edge after editing
        workflow.add_conditional_edges(
            "edit_beat",
            self._route_after_edit,
            {
                "accept": "update_memory",
                "rewrite": "write_beat",
                "error": "handle_error",
            }
        )
        
        # After memory update
        workflow.add_conditional_edges(
            "update_memory",
            self._route_after_memory_update,
            {
                "next_beat": "write_beat",
                "end_scene": "finalize_chapter",
                "pause": END,
            }
        )
        
        # After finalizing chapter
        workflow.add_conditional_edges(
            "finalize_chapter",
            self._route_after_chapter,
            {
                "next_chapter": "prepare_chapter",
                "done": END,
                "pause": END,
            }
        )
        
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    # ==================== NODE IMPLEMENTATIONS ====================
    
    async def _node_initialize(self, state: NovelState) -> dict:
        """Initialize the novel - generate bible."""
        from app.agents.architect import ArchitectAgent
        
        # This would be called with premise from the project
        # For now, return state update
        return {
            "phase": WorkflowPhase.AWAITING_APPROVAL.value,
            "needs_human_approval": True,
            "messages": [{"role": "system", "content": "Novel bible generated. Awaiting approval."}],
        }
    
    async def _node_await_approval(self, state: NovelState) -> dict:
        """Wait for human approval of the outline."""
        # In actual implementation, this checks a database flag
        # or receives input from an external system
        return state
    
    async def _node_prepare_chapter(self, state: NovelState) -> dict:
        """Prepare context for chapter generation."""
        from app.agents.lorekeeper import LorekeeperAgent
        
        chapter_idx = state["current_chapter_idx"]
        bible = state.get("bible", {})
        chapters = bible.get("chapters", [])
        
        if chapter_idx >= len(chapters):
            return {"phase": WorkflowPhase.COMPLETED.value}
        
        chapter = chapters[chapter_idx]
        
        return {
            "current_chapter_outline": chapter,
            "current_scene_idx": 0,
            "chapter_content": "",
            "phase": WorkflowPhase.CHAPTER_GENERATION.value,
        }
    
    async def _node_generate_beats(self, state: NovelState) -> dict:
        """Generate beats for the current scene."""
        from app.agents.beater import BeaterAgent
        
        beater = BeaterAgent()
        chapter_outline = state.get("current_chapter_outline", {})
        
        # Generate beats
        beats = await beater.generate_beats(
            scene_summary=chapter_outline.get("summary", ""),
            chapter_context=state.get("story_so_far", ""),
            character_states={},  # Would fetch from lorekeeper
            target_word_count=2500,
        )
        
        return {
            "current_scene_beats": beats.model_dump() if hasattr(beats, 'model_dump') else beats,
            "current_beat_idx": 0,
            "phase": WorkflowPhase.BEAT_WRITING.value,
        }
    
    async def _node_write_beat(self, state: NovelState) -> dict:
        """Write prose for the current beat."""
        from app.agents.ghostwriter import GhostwriterAgent
        
        beats = state.get("current_scene_beats", {})
        beat_list = beats.get("beats", [])
        beat_idx = state.get("current_beat_idx", 0)
        
        if beat_idx >= len(beat_list):
            return {"phase": WorkflowPhase.MEMORY_UPDATE.value}
        
        beat = beat_list[beat_idx]
        
        ghostwriter = GhostwriterAgent()
        
        output = await ghostwriter.write_beat(
            beat_description=beat.get("description", ""),
            beat_type=beat.get("beat_type", "action"),
            character_context="",  # Would fetch from lorekeeper
            world_context="",
            previous_text=state.get("chapter_content", "")[-1000:],
            sensory_details=beat.get("sensory_details", []),
            emotional_note=beat.get("emotional_note", ""),
        )
        
        return {
            "current_prose": output.prose,
            "current_beat": beat,
            "total_tokens_used": state.get("total_tokens_used", 0) + output.input_tokens + output.output_tokens,
            "phase": WorkflowPhase.EDITING.value,
        }
    
    async def _node_edit_beat(self, state: NovelState) -> dict:
        """Edit the current beat's prose."""
        from app.agents.editor import EditorAgent
        
        editor = EditorAgent()
        
        report = await editor.review_prose(
            prose=state.get("current_prose", ""),
            beat_description=state.get("current_beat", {}).get("description", ""),
            character_context="",
            world_context="",
            lorebook_facts=[],
        )
        
        return {
            "editor_report": report.model_dump() if hasattr(report, 'model_dump') else report,
            "revision_count": state.get("revision_count", 0) + 1,
        }
    
    async def _node_update_memory(self, state: NovelState) -> dict:
        """Update memory after successful beat."""
        prose = state.get("current_prose", "")
        chapter_content = state.get("chapter_content", "")
        
        return {
            "chapter_content": chapter_content + "\n\n" + prose,
            "current_beat_idx": state.get("current_beat_idx", 0) + 1,
            "revision_count": 0,
        }
    
    async def _node_finalize_chapter(self, state: NovelState) -> dict:
        """Finalize the current chapter."""
        # Update story_so_far with chapter summary
        # Index chapter in vector DB
        
        return {
            "current_chapter_idx": state.get("current_chapter_idx", 0) + 1,
            "current_scene_idx": 0,
            "current_beat_idx": 0,
            "recent_scenes": [],  # Reset for new chapter
        }
    
    async def _node_handle_error(self, state: NovelState) -> dict:
        """Handle errors in the workflow."""
        return {
            "phase": WorkflowPhase.FAILED.value,
        }
    
    # ==================== ROUTING FUNCTIONS ====================
    
    def _route_after_approval(self, state: NovelState) -> str:
        """Route after approval check."""
        if state.get("should_pause"):
            return "abort"
        if state.get("needs_human_approval"):
            return "wait"
        return "continue"
    
    def _route_after_write(self, state: NovelState) -> str:
        """Route after writing a beat."""
        if state.get("error_message"):
            return "error"
        return "edit"
    
    def _route_after_edit(self, state: NovelState) -> str:
        """Route after editing."""
        report = state.get("editor_report", {})
        revision_count = state.get("revision_count", 0)
        
        if state.get("error_message"):
            return "error"
        
        # Accept if quality is good enough or max revisions reached
        if report.get("overall_quality", 0) >= 6 or revision_count >= 3:
            return "accept"
        
        if report.get("recommend_rewrite"):
            return "rewrite"
        
        return "accept"
    
    def _route_after_memory_update(self, state: NovelState) -> str:
        """Route after memory update."""
        if state.get("should_pause"):
            return "pause"
        
        beats = state.get("current_scene_beats", {})
        beat_list = beats.get("beats", [])
        beat_idx = state.get("current_beat_idx", 0)
        
        if beat_idx < len(beat_list):
            return "next_beat"
        
        return "end_scene"
    
    def _route_after_chapter(self, state: NovelState) -> str:
        """Route after completing a chapter."""
        if state.get("should_pause"):
            return "pause"
        
        bible = state.get("bible", {})
        chapters = bible.get("chapters", [])
        chapter_idx = state.get("current_chapter_idx", 0)
        
        if chapter_idx < len(chapters):
            return "next_chapter"
        
        return "done"
    
    # ==================== PUBLIC API ====================
    
    async def run(self, initial_state: Optional[NovelState] = None) -> NovelState:
        """Run the workflow from initial or resumed state."""
        state = initial_state or create_initial_state(self.project_id, self.user_id)
        
        async for event in self.graph.astream(state):
            # Each event is a state update
            pass
        
        return state
    
    async def resume(self, state: NovelState) -> NovelState:
        """Resume a paused workflow."""
        state["should_pause"] = False
        state["needs_human_approval"] = False
        return await self.run(state)
