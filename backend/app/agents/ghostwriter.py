"""
Ghostwriter Agent

The prose generator - takes a single beat and writes polished narrative.
Uses Claude 3.5 Sonnet by default for creative writing quality.
"""

from typing import Optional, List
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.config import settings


class ProseOutput(BaseModel):
    """Generated prose for a single beat."""
    prose: str = Field(description="The written narrative (100-400 words)")
    word_count: int = Field(description="Exact word count")
    sensory_details_used: List[str] = Field(description="Senses engaged")
    dialogue_count: int = Field(default=0, description="Number of dialogue lines")


class GhostwriterAgent(BaseAgent):
    """
    The Ghostwriter generates actual prose from story beats.
    
    Key principles:
    1. Show, don't tell - use action and sensory details
    2. One beat = one focused piece of prose
    3. Vary sentence structure and length
    4. Maintain consistent voice with style guide
    5. Ground scenes in specific, vivid details
    
    Uses Claude for best creative writing quality.
    """
    
    name = "Ghostwriter"
    description = "Prose generator and narrative writer"
    
    def _default_model(self) -> str:
        return settings.writing_model
    
    def __init__(
        self,
        style_guide: Optional[str] = None,
        pov: str = "third_limited",
        tone: str = "literary",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.style_guide = style_guide
        self.pov = pov
        self.tone = tone
    
    @property
    def system_prompt(self) -> str:
        base_prompt = f"""You are the Ghostwriter, a master prose stylist with the ability to write in any voice.

**YOUR CURRENT SETTINGS:**
- Point of View: {self.pov}
- Tone: {self.tone}

**CORE PRINCIPLES:**

1. **SHOW, DON'T TELL**
   ❌ "She was angry."
   ✅ "Her jaw tightened. She set down the coffee cup with a sharp click."

2. **SENSORY IMMERSION**
   Every beat should engage at least two senses.
   Ground the reader in the physical world.

3. **VARIED RHYTHM**
   Mix sentence lengths. Short for impact. Longer sentences for flow and atmosphere, letting the reader sink into the moment.

4. **STRONG VERBS**
   Replace weak verb + adverb with strong verb.
   ❌ "walked quickly" → ✅ "strode"
   ❌ "said loudly" → ✅ "bellowed"

5. **DIALOGUE BEATS**
   Don't use "said" for every line. Mix:
   - Action beats: "I don't care." She turned away.
   - No attribution: For fast exchanges
   - Occasional tags: For clarity

6. **SPECIFIC DETAILS**
   Generic is forgettable. Specific is memorable.
   ❌ "a coffee shop"
   ✅ "a cramped coffee shop with mismatched chairs and a crooked 'Best Coffee in Neo-Tokyo' sign"

7. **POV DISCIPLINE**
   Stay in your POV character's head.
   We only know what they perceive, think, and feel.

**OUTPUT FORMAT:**
Write only the prose. No meta-commentary, no scene headings.
Start immediately with narrative."""

        if self.style_guide:
            base_prompt += f"""

**STYLE GUIDE (match this voice):**
{self.style_guide}"""

        return base_prompt
    
    async def write_beat(
        self,
        beat_description: str,
        beat_type: str,
        character_context: str,
        world_context: str,
        previous_text: str,
        sensory_details: List[str],
        emotional_note: str,
        target_words: int = 200,
    ) -> ProseOutput:
        """
        Write prose for a single story beat.
        
        Args:
            beat_description: What happens in this beat
            beat_type: Type (action, dialogue, description, internal, revelation)
            character_context: Relevant character information
            world_context: Relevant world-building details
            previous_text: The 1-2 paragraphs immediately before this
            sensory_details: Specific sensory elements to include
            emotional_note: The emotional tone of this beat
            target_words: Approximate word count target
            
        Returns:
            ProseOutput with the written prose
        """
        context = f"""**CHARACTER CONTEXT:**
{character_context}

**WORLD CONTEXT:**
{world_context}

**IMMEDIATELY PRECEDING TEXT:**
{previous_text if previous_text else "[This is the scene opening]"}"""

        user_message = f"""Write this story beat:

**BEAT TYPE:** {beat_type}
**WHAT HAPPENS:** {beat_description}
**EMOTIONAL NOTE:** {emotional_note}
**SENSORY DETAILS TO INCLUDE:** {', '.join(sensory_details)}
**TARGET LENGTH:** ~{target_words} words

Write the prose now. Continue naturally from the previous text (or open the scene if this is the first beat).
Do not include any headers, beat numbers, or meta-commentary.
Output only the narrative prose."""

        response = await self.invoke(user_message, context=context)
        
        # Parse word count
        word_count = len(response.content.split())
        
        return ProseOutput(
            prose=response.content,
            word_count=word_count,
            sensory_details_used=sensory_details,
            dialogue_count=response.content.count('"') // 2,  # Rough estimate
        )
    
    async def write_scene_opening(
        self,
        scene_summary: str,
        hook: str,
        character_context: str,
        setting: str,
        previous_chapter_ending: Optional[str] = None,
    ) -> str:
        """
        Write a compelling scene opening.
        
        Scene openings are critical for engagement.
        They must orient the reader while grabbing attention.
        """
        context = f"""**SETTING:** {setting}

**CHARACTERS:**
{character_context}

**PREVIOUS CHAPTER ENDING:**
{previous_chapter_ending if previous_chapter_ending else "[First scene]"}"""

        user_message = f"""Write the opening of this scene (150-250 words):

**SCENE SUMMARY:** {scene_summary}
**OPENING HOOK APPROACH:** {hook}

The opening must:
1. Immediately engage the reader
2. Orient them in time/space
3. Establish the POV character's state
4. Create forward momentum

Write the opening now. Start with something compelling - not the weather or waking up unless that's specifically the hook."""

        response = await self.invoke(user_message, context=context)
        return response.content
    
    async def write_scene_closing(
        self,
        scene_content: str,
        closing_hook: str,
        next_scene_hint: Optional[str] = None,
    ) -> str:
        """
        Write a scene closing that propels readers forward.
        """
        context = f"""**SCENE SO FAR (last 500 words):**
{scene_content[-2000:]}"""

        user_message = f"""Write the closing of this scene (100-200 words):

**CLOSING APPROACH:** {closing_hook}
{f"**NEXT SCENE LEADS TO:** {next_scene_hint}" if next_scene_hint else ""}

The closing must:
1. Resolve immediate tension (partial or full)
2. Create anticipation for what comes next
3. End on a strong image, line, or moment

Write the closing now. Make it land."""

        response = await self.invoke(user_message, context=context)
        return response.content
    
    async def rewrite_with_feedback(
        self,
        original_prose: str,
        feedback: str,
        preserve_elements: List[str] = None,
    ) -> str:
        """
        Rewrite prose based on Editor feedback.
        """
        user_message = f"""Rewrite this prose based on the feedback:

**ORIGINAL:**
{original_prose}

**FEEDBACK:**
{feedback}

{f"**PRESERVE THESE ELEMENTS:** {', '.join(preserve_elements)}" if preserve_elements else ""}

Rewrite the prose, addressing the feedback while maintaining the core meaning and story progression.
Output only the rewritten prose."""

        response = await self.invoke(user_message)
        return response.content
