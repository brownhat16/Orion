"""
Editor Agent

The quality control agent that reviews and critiques generated prose.
Checks for:
- Technical issues (passive voice, repetition)
- Consistency with lorebook
- Pacing and engagement
- Show vs tell adherence
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

from app.agents.base import BaseAgent
from app.config import settings


class IssueSeverity(str, Enum):
    """Severity of an editing issue."""
    CRITICAL = "critical"  # Must fix - breaks story or is factually wrong
    MAJOR = "major"        # Should fix - significantly impacts quality
    MINOR = "minor"        # Nice to fix - polish issue
    SUGGESTION = "suggestion"  # Optional improvement


class EditingIssue(BaseModel):
    """A single issue found during editing."""
    severity: str = Field(description="critical, major, minor, or suggestion")
    category: str = Field(description="consistency, pacing, prose_quality, show_dont_tell, dialogue, etc.")
    quote: str = Field(description="The problematic text (if applicable)")
    issue: str = Field(description="What's wrong")
    suggestion: str = Field(description="How to fix it")


class EditingReport(BaseModel):
    """Complete editing report for a piece of prose."""
    overall_quality: int = Field(description="1-10 rating", ge=1, le=10)
    issues: List[EditingIssue] = Field(description="List of issues found")
    strengths: List[str] = Field(description="What works well")
    recommend_rewrite: bool = Field(description="Should this be rewritten?")
    summary: str = Field(description="Brief overall assessment")


class EditorAgent(BaseAgent):
    """
    The Editor reviews and critiques prose quality.
    
    Categories checked:
    1. CONSISTENCY - Does it match established facts?
    2. PACING - Is it too fast/slow?
    3. PROSE QUALITY - Is the writing strong?
    4. SHOW DON'T TELL - Are emotions shown through action?
    5. DIALOGUE - Is it natural and purposeful?
    6. POV - Does it maintain point of view?
    7. REPETITION - Word/phrase repetition
    8. PASSIVE VOICE - Overuse of passive constructions
    """
    
    name = "Editor"
    description = "Quality control and prose critic"
    
    @property
    def system_prompt(self) -> str:
        return """You are the Editor, a ruthless but fair critic with high standards.

Your job is to identify issues in prose while acknowledging what works well.
You must balance encouragement with necessary criticism.

**CRITICAL ISSUES (must fix):**
- Factual contradictions with established story
- Character acting out of established character
- Internal logic failures
- POV violations
- Timeline errors

**MAJOR ISSUES (should fix):**
- Telling instead of showing for important emotions
- Rushed pacing through significant moments
- Wooden or expository dialogue
- Repetitive sentence structure
- Missing sensory grounding

**MINOR ISSUES (nice to fix):**
- Occasional passive voice
- Single word repetition
- Missing variety in dialogue tags
- Minor flow issues

**SUGGESTIONS:**
- Alternative word choices
- Opportunities for deeper characterization
- Places to add subtext

**YOUR APPROACH:**
1. Read for story first - does it work?
2. Check consistency with provided context
3. Analyze prose craft
4. Note specific quotes with issues
5. Provide actionable fixes

Be constructive. Your goal is to make the work better, not to tear it down.
A score of 7/10 is good. 8/10 is very good. 9/10 is exceptional."""
    
    async def review_prose(
        self,
        prose: str,
        beat_description: str,
        character_context: str,
        world_context: str,
        lorebook_facts: List[str],
        style_guide: Optional[str] = None,
    ) -> EditingReport:
        """
        Review a piece of generated prose.
        
        Args:
            prose: The prose to review
            beat_description: What was supposed to happen
            character_context: Character information for consistency
            world_context: World-building facts
            lorebook_facts: Specific facts to check against
            style_guide: Optional style to match
            
        Returns:
            EditingReport with issues and assessment
        """
        context = f"""**BEAT REQUIREMENT:**
{beat_description}

**CHARACTER CONTEXT:**
{character_context}

**WORLD CONTEXT:**
{world_context}

**FACTS TO CHECK (Lorebook):**
{chr(10).join(f"- {fact}" for fact in lorebook_facts)}

{f"**STYLE TO MATCH:**{chr(10)}{style_guide}" if style_guide else ""}"""

        user_message = f"""Review this prose:

---
{prose}
---

Evaluate for:
1. CONSISTENCY with the lorebook facts
2. PACING - does it rush or drag?
3. PROSE QUALITY - strong verbs, varied sentences, sensory details
4. SHOW DON'T TELL - emotions through action, not exposition
5. DIALOGUE - natural, purposeful, with action beats
6. POV - maintained throughout
7. REPETITION - word or phrase
8. Does it accomplish what the beat required?

Provide an overall quality score (1-10) and determine if a rewrite is needed.
A rewrite should only be recommended for scores below 6 or critical issues."""

        return await self.invoke_structured(user_message, EditingReport, context=context)
    
    async def check_consistency(
        self,
        prose: str,
        lorebook_facts: List[str],
    ) -> List[EditingIssue]:
        """
        Focused consistency check against lorebook.
        
        This is a faster check than full review, used for
        final pass before saving.
        """
        user_message = f"""Check this prose for consistency violations:

**PROSE:**
{prose}

**ESTABLISHED FACTS:**
{chr(10).join(f"- {fact}" for fact in lorebook_facts)}

Only report CRITICAL or MAJOR issues where the prose contradicts established facts.
If everything is consistent, return an empty list."""

        response = await self.invoke(user_message)
        
        # Parse response for issues
        # In production, use structured output
        return []
    
    async def suggest_improvements(
        self,
        prose: str,
        focus_areas: List[str],
    ) -> str:
        """
        Get improvement suggestions for specific areas.
        
        Useful for iterative polishing.
        """
        user_message = f"""Suggest improvements for this prose:

{prose}

Focus on these areas:
{chr(10).join(f"- {area}" for area in focus_areas)}

For each area, provide specific, actionable suggestions with examples."""

        response = await self.invoke(user_message)
        return response.content
    
    async def final_polish_check(
        self,
        chapter_text: str,
    ) -> EditingReport:
        """
        Final quality check on complete chapter.
        
        Looks for issues that only appear at chapter level:
        - Repeated phrases across scenes
        - Pacing consistency
        - Thematic coherence
        """
        user_message = f"""Perform a final polish check on this complete chapter:

---
{chapter_text}
---

Look for:
1. Phrases or descriptions repeated too often across the chapter
2. Pacing consistency - does the chapter flow well as a whole?
3. Character voice consistency - do characters sound the same throughout?
4. Thematic elements - are they woven consistently?
5. Opening hook - does the chapter start strong?
6. Closing hook - does it compel reading on?

Provide an overall chapter quality score and key issues to address."""

        return await self.invoke_structured(user_message, EditingReport)
