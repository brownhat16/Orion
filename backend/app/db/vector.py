"""
Vector Database Integration

Abstraction layer for semantic search using ChromaDB (local) or Pinecone (cloud).
Used by the Lorekeeper agent for RAG-based context retrieval.
"""

import hashlib
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

import httpx

from app.config import settings


class NVIDIAEmbeddingFunction:
    """
    NVIDIA NIM BGE-M3 embedding function for ChromaDB.
    
    Compatible with ChromaDB's EmbeddingFunction interface.
    """
    
    def __init__(self, base_url: str, model: str = "baai/bge-m3"):
        self.base_url = base_url.rstrip("/")
        self.model = model
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        """Synchronous embedding for ChromaDB compatibility."""
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.base_url}/embeddings",
                json={"input": input, "model": self.model},
                headers={"Authorization": f"Bearer {settings.ngc_api_key}"},
            )
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]
    
    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """Async embedding for batch processing."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                json={"input": texts, "model": self.model},
                headers={"Authorization": f"Bearer {settings.ngc_api_key}"},
            )
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]
    
    async def aembed_query(self, text: str) -> List[float]:
        """Async embedding for a single query."""
        embeddings = await self.aembed_documents([text])
        return embeddings[0]


@dataclass
class SearchResult:
    """A single search result from the vector database."""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float


class VectorStore(ABC):
    """Abstract base class for vector stores."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the vector store connection."""
        pass
    
    @abstractmethod
    async def add_texts(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        namespace: str = "default",
    ) -> List[str]:
        """
        Add texts to the vector store.
        
        Args:
            texts: List of text content to embed
            metadatas: List of metadata dicts for each text
            namespace: Namespace/collection for isolation (e.g., project_id)
            
        Returns:
            List of generated IDs
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        namespace: str = "default",
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Search for similar texts.
        
        Args:
            query: The search query
            namespace: Namespace to search in
            top_k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of search results
        """
        pass
    
    @abstractmethod
    async def delete(
        self,
        ids: List[str],
        namespace: str = "default",
    ) -> None:
        """Delete vectors by ID."""
        pass
    
    @abstractmethod
    async def delete_namespace(self, namespace: str) -> None:
        """Delete all vectors in a namespace."""
        pass


class ChromaDBStore(VectorStore):
    """
    ChromaDB implementation for local development.
    Lightweight, embedded vector database.
    """
    
    def __init__(self):
        self._client = None
        self._embedding_function = None
    
    async def initialize(self) -> None:
        """Initialize ChromaDB with embeddings."""
        import chromadb
        from chromadb.config import Settings as ChromaSettings
        
        self._client = chromadb.PersistentClient(
            path=settings.chromadb_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        
        # Use NVIDIA NIM BGE-M3 embeddings if enabled
        if settings.nvidia_nim_enabled:
            self._embedding_function = NVIDIAEmbeddingFunction(
                base_url=settings.nvidia_embeddings_url,
                model=settings.embedding_model,
            )
        # Fallback to OpenAI embeddings
        elif settings.openai_api_key:
            from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
            self._embedding_function = OpenAIEmbeddingFunction(
                api_key=settings.openai_api_key,
                model_name="text-embedding-3-small",
            )
        else:
            # Fallback to default sentence-transformers
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
            self._embedding_function = DefaultEmbeddingFunction()
    
    def _get_collection(self, namespace: str):
        """Get or create a collection for the namespace."""
        return self._client.get_or_create_collection(
            name=f"novel_{namespace}",
            embedding_function=self._embedding_function,
            metadata={"hnsw:space": "cosine"},
        )
    
    async def add_texts(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        namespace: str = "default",
    ) -> List[str]:
        """Add texts to ChromaDB."""
        collection = self._get_collection(namespace)
        
        # Generate deterministic IDs from content
        ids = [
            hashlib.md5(f"{namespace}:{text[:100]}:{i}".encode()).hexdigest()
            for i, text in enumerate(texts)
        ]
        
        collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids,
        )
        
        return ids
    
    async def search(
        self,
        query: str,
        namespace: str = "default",
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search ChromaDB for similar texts."""
        collection = self._get_collection(namespace)
        
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where=filter,
            include=["documents", "metadatas", "distances"],
        )
        
        search_results = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                search_results.append(SearchResult(
                    id=results["ids"][0][i],
                    content=doc,
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    score=1 - results["distances"][0][i],  # Convert distance to similarity
                ))
        
        return search_results
    
    async def delete(
        self,
        ids: List[str],
        namespace: str = "default",
    ) -> None:
        """Delete vectors from ChromaDB."""
        collection = self._get_collection(namespace)
        collection.delete(ids=ids)
    
    async def delete_namespace(self, namespace: str) -> None:
        """Delete entire collection."""
        try:
            self._client.delete_collection(f"novel_{namespace}")
        except ValueError:
            pass  # Collection doesn't exist


class PineconeStore(VectorStore):
    """
    Pinecone implementation for production.
    Cloud-hosted, scalable vector database.
    """
    
    def __init__(self):
        self._client = None
        self._index = None
        self._embeddings = None
    
    async def initialize(self) -> None:
        """Initialize Pinecone connection."""
        from pinecone import Pinecone
        from langchain_openai import OpenAIEmbeddings
        
        self._client = Pinecone(api_key=settings.pinecone_api_key)
        self._index = self._client.Index(settings.pinecone_index)
        
        # Use OpenAI for embeddings
        self._embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=settings.openai_api_key,
        )
    
    async def add_texts(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        namespace: str = "default",
    ) -> List[str]:
        """Add texts to Pinecone."""
        # Generate embeddings
        embeddings = await self._embeddings.aembed_documents(texts)
        
        # Generate IDs
        ids = [
            hashlib.md5(f"{namespace}:{text[:100]}:{i}".encode()).hexdigest()
            for i, text in enumerate(texts)
        ]
        
        # Prepare vectors
        vectors = []
        for i, (id_, emb, text, meta) in enumerate(zip(ids, embeddings, texts, metadatas)):
            meta["text"] = text  # Store original text in metadata
            vectors.append({
                "id": id_,
                "values": emb,
                "metadata": meta,
            })
        
        # Upsert in batches
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self._index.upsert(vectors=batch, namespace=namespace)
        
        return ids
    
    async def search(
        self,
        query: str,
        namespace: str = "default",
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search Pinecone for similar texts."""
        # Generate query embedding
        query_embedding = await self._embeddings.aembed_query(query)
        
        # Search
        results = self._index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=namespace,
            filter=filter,
            include_metadata=True,
        )
        
        search_results = []
        for match in results.matches:
            search_results.append(SearchResult(
                id=match.id,
                content=match.metadata.get("text", ""),
                metadata={k: v for k, v in match.metadata.items() if k != "text"},
                score=match.score,
            ))
        
        return search_results
    
    async def delete(
        self,
        ids: List[str],
        namespace: str = "default",
    ) -> None:
        """Delete vectors from Pinecone."""
        self._index.delete(ids=ids, namespace=namespace)
    
    async def delete_namespace(self, namespace: str) -> None:
        """Delete all vectors in a namespace."""
        self._index.delete(delete_all=True, namespace=namespace)


# Factory function
def get_vector_store() -> VectorStore:
    """Get the configured vector store implementation."""
    if settings.vector_db_type == "pinecone":
        return PineconeStore()
    else:
        return ChromaDBStore()


# Singleton instance
_vector_store: Optional[VectorStore] = None


async def get_initialized_vector_store() -> VectorStore:
    """Get an initialized vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = get_vector_store()
        await _vector_store.initialize()
    return _vector_store
