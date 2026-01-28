"""
Base Agent Class

Foundation for all specialized agents in the novel generation system.
Provides LLM abstraction, prompt management, and token tracking.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Literal
from dataclasses import dataclass, field
import tiktoken

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.language_models import BaseChatModel

from app.config import settings


@dataclass
class AgentResponse:
    """Structured response from an agent."""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TokenCounter:
    """Track token usage across calls."""
    input_tokens: int = 0
    output_tokens: int = 0
    
    def add(self, input_tokens: int, output_tokens: int):
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
    
    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens


# Approximate cost per 1M tokens (as of 2024)
MODEL_COSTS = {
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
    "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in USD for a given model and token count."""
    costs = MODEL_COSTS.get(model, {"input": 5.0, "output": 15.0})
    return (
        (input_tokens / 1_000_000) * costs["input"] +
        (output_tokens / 1_000_000) * costs["output"]
    )


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count tokens in text using tiktoken."""
    try:
        encoder = tiktoken.encoding_for_model(model)
    except KeyError:
        encoder = tiktoken.get_encoding("cl100k_base")
    return len(encoder.encode(text))


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    Provides:
    - LLM client selection (OpenAI or Anthropic)
    - Prompt template management
    - Token tracking and cost estimation
    - Structured response handling
    """
    
    name: str = "BaseAgent"
    description: str = "Base agent class"
    
    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        self.model = model or self._default_model()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.token_counter = TokenCounter()
        
        # Initialize LLM client
        self._llm = self._create_llm()
    
    def _default_model(self) -> str:
        """Get the default model for this agent type."""
        return settings.writing_model
    
    def _create_llm(self) -> BaseChatModel:
        """Create the appropriate LLM client based on configuration."""
        # Use NVIDIA NIM if enabled
        if settings.nvidia_nim_enabled:
            return ChatOpenAI(
                model=self.model,
                openai_api_key=settings.ngc_api_key or "not-needed",
                openai_api_base=settings.nvidia_llm_url,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        
        # Fallback to Anthropic for Claude models
        if self.model.startswith("claude"):
            return ChatAnthropic(
                model=self.model,
                anthropic_api_key=settings.anthropic_api_key,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        
        # Fallback to OpenAI
        return ChatOpenAI(
            model=self.model,
            openai_api_key=settings.openai_api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """The system prompt defining this agent's persona and behavior."""
        pass
    
    async def invoke(
        self,
        user_message: str,
        context: Optional[str] = None,
        additional_messages: Optional[List[Dict[str, str]]] = None,
    ) -> AgentResponse:
        """
        Invoke the agent with a user message.
        
        Args:
            user_message: The primary instruction/query
            context: Optional context to prepend
            additional_messages: Optional list of {"role": "user/assistant", "content": "..."}
            
        Returns:
            AgentResponse with content and token usage
        """
        # Build message list
        messages = [SystemMessage(content=self.system_prompt)]
        
        # Add conversation history if provided
        if additional_messages:
            for msg in additional_messages:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        # Build final user message with context
        final_message = ""
        if context:
            final_message = f"<context>\n{context}\n</context>\n\n"
        final_message += user_message
        
        messages.append(HumanMessage(content=final_message))
        
        # Count input tokens
        input_text = self.system_prompt + final_message
        if additional_messages:
            input_text += "".join(m["content"] for m in additional_messages)
        input_tokens = count_tokens(input_text, self.model)
        
        # Invoke LLM
        response = await self._llm.ainvoke(messages)
        content = response.content
        
        # Count output tokens
        output_tokens = count_tokens(content, self.model)
        
        # Track usage
        self.token_counter.add(input_tokens, output_tokens)
        
        return AgentResponse(
            content=content,
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=estimate_cost(self.model, input_tokens, output_tokens),
        )
    
    async def invoke_structured(
        self,
        user_message: str,
        output_schema: type,
        context: Optional[str] = None,
    ) -> Any:
        """
        Invoke with structured output parsing.
        
        Uses LangChain's with_structured_output for reliable JSON parsing.
        """
        structured_llm = self._llm.with_structured_output(output_schema)
        
        messages = [
            SystemMessage(content=self.system_prompt),
        ]
        
        final_message = ""
        if context:
            final_message = f"<context>\n{context}\n</context>\n\n"
        final_message += user_message
        messages.append(HumanMessage(content=final_message))
        
        result = await structured_llm.ainvoke(messages)
        return result
    
    def reset_token_counter(self):
        """Reset the token counter."""
        self.token_counter = TokenCounter()
