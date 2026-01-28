"""
NVIDIA Reranker Integration

Client for NVIDIA NIM reranker API to improve RAG retrieval quality.
Uses the Llama 3.2 NV RerankQA model.
"""

from typing import List, Optional
from dataclasses import dataclass

import httpx

from app.config import settings


@dataclass
class RerankedResult:
    """A single reranked result."""
    text: str
    score: float
    original_index: int
    metadata: Optional[dict] = None


class NVIDIAReranker:
    """
    Client for NVIDIA NIM reranker API.
    
    The reranker takes a query and a list of passages, and returns
    the passages reranked by relevance to the query.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.nvidia_reranker_url).rstrip("/")
        self.model = model or settings.reranker_model
    
    async def rerank(
        self,
        query: str,
        passages: List[str],
        top_k: Optional[int] = None,
        metadata_list: Optional[List[dict]] = None,
    ) -> List[RerankedResult]:
        """
        Rerank passages by relevance to query.
        
        Args:
            query: The search query
            passages: List of text passages to rerank
            top_k: Number of top results to return (default: all)
            metadata_list: Optional metadata for each passage
            
        Returns:
            List of RerankedResult sorted by relevance score (descending)
        """
        if not passages:
            return []
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/ranking",
                json={
                    "model": self.model,
                    "query": {"text": query},
                    "passages": [{"text": p} for p in passages],
                    "truncate": "END",
                },
                headers={
                    "Authorization": f"Bearer {settings.ngc_api_key}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()
            
            # Parse rankings
            results = []
            rankings = data.get("rankings", [])
            
            for item in rankings:
                idx = item["index"]
                results.append(RerankedResult(
                    text=passages[idx],
                    score=item.get("logit", item.get("score", 0.0)),
                    original_index=idx,
                    metadata=metadata_list[idx] if metadata_list else None,
                ))
            
            # Sort by score descending (should already be sorted)
            results.sort(key=lambda x: x.score, reverse=True)
            
            # Limit to top_k if specified
            if top_k is not None:
                results = results[:top_k]
            
            return results
    
    def rerank_sync(
        self,
        query: str,
        passages: List[str],
        top_k: Optional[int] = None,
    ) -> List[RerankedResult]:
        """Synchronous version of rerank."""
        if not passages:
            return []
        
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.base_url}/ranking",
                json={
                    "model": self.model,
                    "query": {"text": query},
                    "passages": [{"text": p} for p in passages],
                    "truncate": "END",
                },
                headers={
                    "Authorization": f"Bearer {settings.ngc_api_key}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("rankings", []):
                idx = item["index"]
                results.append(RerankedResult(
                    text=passages[idx],
                    score=item.get("logit", item.get("score", 0.0)),
                    original_index=idx,
                ))
            
            results.sort(key=lambda x: x.score, reverse=True)
            
            if top_k is not None:
                results = results[:top_k]
            
            return results


# Singleton instance
_reranker: Optional[NVIDIAReranker] = None


def get_reranker() -> Optional[NVIDIAReranker]:
    """Get the reranker instance if NVIDIA NIM reranker is enabled."""
    global _reranker
    if not settings.nvidia_nim_enabled:
        return None
    if not getattr(settings, 'nvidia_reranker_enabled', False):
        return None  # Reranker not available via cloud API
    if _reranker is None:
        _reranker = NVIDIAReranker()
    return _reranker
