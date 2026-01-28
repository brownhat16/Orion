"""
Test Suite for Agents

Unit tests for the agent system.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.agents.base import BaseAgent, AgentResponse, count_tokens, estimate_cost
from app.agents.architect import ArchitectAgent, NovelBible
from app.agents.beater import BeaterAgent, SceneBeats
from app.agents.ghostwriter import GhostwriterAgent
from app.agents.editor import EditorAgent, EditingReport


class TestTokenCounting:
    """Tests for token counting utilities."""
    
    def test_count_tokens_basic(self):
        """Test basic token counting."""
        text = "Hello, world!"
        tokens = count_tokens(text)
        assert tokens > 0
        assert tokens < 10
    
    def test_count_tokens_empty(self):
        """Test empty string."""
        assert count_tokens("") == 0
    
    def test_estimate_cost_gpt4(self):
        """Test cost estimation for GPT-4o."""
        cost = estimate_cost("gpt-4o", 1000, 500)
        assert cost > 0
        # ~$0.0025 input + ~$0.005 output
        assert cost < 0.01
    
    def test_estimate_cost_claude(self):
        """Test cost estimation for Claude."""
        cost = estimate_cost("claude-3-5-sonnet-20241022", 1000, 500)
        assert cost > 0


class TestArchitectAgent:
    """Tests for the Architect agent."""
    
    @pytest.fixture
    def architect(self):
        return ArchitectAgent()
    
    def test_system_prompt(self, architect):
        """Test that system prompt exists and is meaningful."""
        prompt = architect.system_prompt
        assert len(prompt) > 100
        assert "story" in prompt.lower() or "novel" in prompt.lower()
    
    @pytest.mark.asyncio
    @patch.object(ArchitectAgent, 'invoke_structured')
    async def test_create_novel_bible(self, mock_invoke, architect):
        """Test novel bible creation."""
        mock_bible = NovelBible(
            title="Test Novel",
            genre="Fantasy",
            subgenres=["Adventure"],
            logline="A hero's journey",
            synopsis="A young hero...",
            themes=["courage"],
            tone="Epic",
            setting="Medieval kingdom",
            characters=[],
            world_rules=[],
            chapters=[],
        )
        mock_invoke.return_value = mock_bible
        
        bible = await architect.create_novel_bible(
            premise="A young hero saves the kingdom",
            genre="Fantasy",
            num_chapters=10,
        )
        
        assert bible.title == "Test Novel"
        assert bible.genre == "Fantasy"
        mock_invoke.assert_called_once()


class TestBeaterAgent:
    """Tests for the Beater agent."""
    
    @pytest.fixture
    def beater(self):
        return BeaterAgent()
    
    def test_system_prompt(self, beater):
        """Test that system prompt exists."""
        prompt = beater.system_prompt
        assert len(prompt) > 100
        assert "beat" in prompt.lower()
    
    @pytest.mark.asyncio
    @patch.object(BeaterAgent, 'invoke_structured')
    async def test_generate_beats(self, mock_invoke, beater):
        """Test beat generation."""
        mock_beats = SceneBeats(
            scene_summary="Test scene",
            opening_hook="Door slams open",
            closing_hook="Cliffhanger",
            beats=[],
        )
        mock_invoke.return_value = mock_beats
        
        beats = await beater.generate_beats(
            scene_summary="Hero enters castle",
            chapter_context="Beginning of story",
            character_states={"Hero": "anxious"},
            target_word_count=2000,
        )
        
        assert beats.scene_summary == "Test scene"


class TestGhostwriterAgent:
    """Tests for the Ghostwriter agent."""
    
    @pytest.fixture
    def ghostwriter(self):
        return GhostwriterAgent(
            style_guide="Literary fiction style",
            pov="third_limited",
            tone="atmospheric",
        )
    
    def test_system_prompt_includes_settings(self, ghostwriter):
        """Test that system prompt includes POV and tone."""
        prompt = ghostwriter.system_prompt
        assert "third_limited" in prompt
        assert "atmospheric" in prompt
        assert "Literary fiction style" in prompt
    
    @pytest.mark.asyncio
    @patch.object(GhostwriterAgent, 'invoke')
    async def test_write_beat(self, mock_invoke, ghostwriter):
        """Test beat writing."""
        mock_response = AgentResponse(
            content="The door creaked open...",
            model="claude-3-5-sonnet",
            input_tokens=100,
            output_tokens=50,
            estimated_cost=0.001,
        )
        mock_invoke.return_value = mock_response
        
        output = await ghostwriter.write_beat(
            beat_description="Character enters room",
            beat_type="action",
            character_context="John is nervous",
            world_context="Victorian mansion",
            previous_text="",
            sensory_details=["creaking floor", "dim light"],
            emotional_note="tension",
        )
        
        assert output.prose == "The door creaked open..."
        assert output.word_count > 0


class TestEditorAgent:
    """Tests for the Editor agent."""
    
    @pytest.fixture
    def editor(self):
        return EditorAgent()
    
    def test_system_prompt(self, editor):
        """Test that system prompt exists."""
        prompt = editor.system_prompt
        assert len(prompt) > 100
        assert "critic" in prompt.lower() or "review" in prompt.lower()
    
    @pytest.mark.asyncio
    @patch.object(EditorAgent, 'invoke_structured')
    async def test_review_prose(self, mock_invoke, editor):
        """Test prose review."""
        mock_report = EditingReport(
            overall_quality=7,
            issues=[],
            strengths=["Good pacing"],
            recommend_rewrite=False,
            summary="Solid prose with minor issues",
        )
        mock_invoke.return_value = mock_report
        
        report = await editor.review_prose(
            prose="The hero walked forward carefully.",
            beat_description="Hero advances",
            character_context="Hero is cautious",
            world_context="Dangerous dungeon",
            lorebook_facts=["Hero has sword"],
        )
        
        assert report.overall_quality == 7
        assert report.recommend_rewrite is False


class TestAgentIntegration:
    """Integration tests for agent interactions."""
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires API keys")
    async def test_full_beat_cycle(self):
        """
        Test a full beat cycle: Beater -> Ghostwriter -> Editor.
        
        This test requires actual API keys and is skipped by default.
        Enable for integration testing.
        """
        beater = BeaterAgent()
        ghostwriter = GhostwriterAgent()
        editor = EditorAgent()
        
        # Generate beats
        beats = await beater.generate_beats(
            scene_summary="Hero discovers a clue",
            chapter_context="Detective story, chapter 1",
            character_states={"Detective": "curious"},
        )
        
        assert len(beats.beats) > 0
        
        # Write first beat
        first_beat = beats.beats[0]
        prose = await ghostwriter.write_beat(
            beat_description=first_beat.description,
            beat_type=first_beat.beat_type,
            character_context="Detective is experienced",
            world_context="Noir setting",
            previous_text="",
            sensory_details=first_beat.sensory_details,
            emotional_note=first_beat.emotional_note,
        )
        
        assert len(prose.prose) > 50
        
        # Edit
        report = await editor.review_prose(
            prose=prose.prose,
            beat_description=first_beat.description,
            character_context="Detective is experienced",
            world_context="Noir setting",
            lorebook_facts=[],
        )
        
        assert report.overall_quality >= 1
        assert report.overall_quality <= 10
