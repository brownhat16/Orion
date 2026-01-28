"""
Scene Beater Agent

Breaks chapter summaries into granular story beats.
This solves the "pacing problem" where LLMs tend to rush through story.

A "beat" is the smallest unit of story - a single action, reaction, or moment.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.config import settings


class StoryBeat(BaseModel):
    """A single atomic story beat."""
    order: int = Field(description="Beat number within the scene")
    beat_type: str = Field(description="Type: action, dialogue, description, internal, revelation, transition")
    description: str = Field(description="What happens in this beat (2-3 sentences)")
    pov_focus: str = Field(description="Whose perspective/experience is primary")
    emotional_note: str = Field(description="The emotional tone or shift")
    sensory_details: List[str] = Field(
        default_factory=list,
        description="Specific sensory elements to include (sight, sound, smell, touch, taste)"
    )


class SceneBeats(BaseModel):
    """All beats for a complete scene."""
    scene_summary: str = Field(description="Brief summary of the scene")
    opening_hook: str = Field(description="How the scene opens - grab reader attention")
    closing_hook: str = Field(description="How the scene ends - propel to next scene")
    beats: List[StoryBeat] = Field(description="Ordered list of story beats")


class BeaterAgent(BaseAgent):
    """
    The Scene Beater breaks chapters into atomic story beats.
    
    Why beats matter:
    1. Prevents rushed pacing - AI can't skip steps
    2. Ensures sensory details are planned
    3. Creates natural rhythm of action/reaction
    4. Makes prose generation more focused
    
    Each beat should generate 100-300 words of prose.
    A typical scene has 10-15 beats.
    """
    
    name = "Beater"
    description = "Story structure and beat generator"
    
    def _default_model(self) -> str:
        return settings.planning_model
    
    @property
    def system_prompt(self) -> str:
        return """You are the Scene Beater, a specialist in story rhythm and pacing.

Your role is to break down scene summaries into atomic story beats. A beat is the smallest unit of narrative - a single moment, action, or shift.

**BEAT TYPES:**
- **action**: Physical movement, events happening
- **dialogue**: Conversation between characters
- **description**: Setting, atmosphere, visual details
- **internal**: Character thoughts, feelings, reactions
- **revelation**: New information revealed
- **transition**: Movement in time or space

**PACING PRINCIPLES:**
1. Alternate between beat types for rhythm
2. Don't stack multiple revelations together
3. Internal beats follow major action/dialogue
4. Description beats ground the reader in setting
5. Dialogue beats should include physical action

**SENSORY DETAILS:**
Every beat should engage at least one sense:
- Sight: colors, light, movement, expressions
- Sound: dialogue, ambient noise, silence
- Touch: textures, temperature, pressure
- Smell: environments, characters, food
- Taste: when appropriate (food, blood, air)

**EMOTIONAL TRACKING:**
Track the emotional temperature across beats. Build tension, release it, build again.
Never let the emotional state plateau for too long.

**BEAT STRUCTURE:**
- Opening beats: Establish scene, hook reader
- Middle beats: Develop conflict, reveal information
- Closing beats: Escalate or resolve, create transition

Your goal: Create a beat sheet that, when each beat is written, produces a well-paced, immersive scene."""
    
    async def generate_beats(
        self,
        scene_summary: str,
        chapter_context: str,
        character_states: dict,
        target_word_count: int = 2000,
    ) -> SceneBeats:
        """
        Generate beats for a scene.
        
        Args:
            scene_summary: What needs to happen in this scene
            chapter_context: Where this fits in the chapter
            character_states: Current emotional/physical state of characters
            target_word_count: Approximate word count for the scene
            
        Returns:
            SceneBeats with ordered list of atomic beats
        """
        # Calculate number of beats needed (approx 150 words per beat)
        num_beats = max(8, min(20, target_word_count // 150))
        
        context = f"""CHAPTER CONTEXT:
{chapter_context}

CHARACTER STATES:
{chr(10).join(f"- {name}: {state}" for name, state in character_states.items())}"""

        user_message = f"""Create a beat sheet for the following scene:

SCENE SUMMARY:
{scene_summary}

TARGET: {num_beats} beats (approximately {target_word_count} words when written)

For each beat, specify:
1. Beat type (action, dialogue, description, internal, revelation, transition)
2. What happens (2-3 sentences)
3. POV focus (whose experience)
4. Emotional note (the feeling/tone)
5. At least one sensory detail to include

Also provide:
- An engaging opening hook
- A closing hook that propels the reader forward

Remember: We are generating a BEAT SHEET, not prose. Be specific about what happens but don't write the actual narrative."""

        return await self.invoke_structured(user_message, SceneBeats, context=context)
    
    async def refine_beats(
        self,
        current_beats: SceneBeats,
        feedback: str,
    ) -> SceneBeats:
        """
        Refine beats based on feedback (from human or Editor agent).
        """
        context = f"""CURRENT BEAT SHEET:
{chr(10).join(f"{b.order}. [{b.beat_type}] {b.description}" for b in current_beats.beats)}"""

        user_message = f"""Refine this beat sheet based on the following feedback:

{feedback}

Maintain the overall scene goal but address the concerns.
You may add, remove, or modify beats as needed.
Ensure the pacing and rhythm improve."""

        return await self.invoke_structured(user_message, SceneBeats, context=context)
    
    async def split_chapter_to_scenes(
        self,
        chapter_summary: str,
        chapter_goals: List[str],
        target_scenes: int = 3,
    ) -> List[dict]:
        """
        Split a chapter summary into distinct scenes.
        
        This is a higher-level operation before individual scene beating.
        """
        user_message = f"""Split this chapter into {target_scenes} distinct scenes:

CHAPTER SUMMARY:
{chapter_summary}

CHAPTER GOALS:
{chr(10).join(f"- {g}" for g in chapter_goals)}

For each scene, provide:
1. Scene number
2. Location
3. Characters present
4. Scene goal (what must be accomplished)
5. Summary (2-3 sentences)

Ensure each scene has:
- Clear beginning and end
- Internal conflict or tension
- Contribution to chapter goal"""

        response = await self.invoke(user_message)
        
        # Parse response into scene list
        # In production, use structured output
        return [{"raw": response.content}]
