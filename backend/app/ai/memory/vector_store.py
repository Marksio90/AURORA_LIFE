"""
Vector Store for AI Agent Memory

Implements semantic search and retrieval using vector databases:
- ChromaDB (embedded, local)
- Qdrant (scalable, production-ready)

Enables:
- Long-term memory for agents
- Semantic search over past events
- Context retrieval for RAG
"""
import numpy as np
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path
import json

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class VectorStore:
    """
    Unified interface for vector databases.

    Supports ChromaDB and Qdrant backends.
    """

    def __init__(
        self,
        backend: str = "chromadb",
        collection_name: str = "aurora_memory",
        embedding_model: str = "all-MiniLM-L6-v2",
        persist_directory: Optional[Path] = None,
        qdrant_url: Optional[str] = None
    ):
        """
        Initialize vector store.

        Args:
            backend: 'chromadb' or 'qdrant'
            collection_name: Name of collection
            embedding_model: Sentence transformer model name
            persist_directory: Directory for ChromaDB persistence
            qdrant_url: URL for Qdrant server (or :memory: for in-memory)
        """
        self.backend = backend
        self.collection_name = collection_name

        # Initialize embedding model
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self.embedder = SentenceTransformer(embedding_model)
            self.embedding_dim = self.embedder.get_sentence_embedding_dimension()
        else:
            raise ImportError("sentence-transformers not installed")

        # Initialize backend
        if backend == "chromadb":
            self._init_chromadb(persist_directory)
        elif backend == "qdrant":
            self._init_qdrant(qdrant_url)
        else:
            raise ValueError(f"Unknown backend: {backend}")

    def _init_chromadb(self, persist_directory: Optional[Path]):
        """Initialize ChromaDB."""
        if not CHROMA_AVAILABLE:
            raise ImportError("chromadb not installed. Install with: pip install chromadb")

        if persist_directory:
            persist_directory.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=str(persist_directory),
                settings=Settings(anonymized_telemetry=False)
            )
        else:
            self.client = chromadb.Client()

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def _init_qdrant(self, qdrant_url: Optional[str]):
        """Initialize Qdrant."""
        if not QDRANT_AVAILABLE:
            raise ImportError("qdrant-client not installed. Install with: pip install qdrant-client")

        # Connect to Qdrant
        if qdrant_url:
            self.client = QdrantClient(url=qdrant_url)
        else:
            # In-memory mode
            self.client = QdrantClient(":memory:")

        # Create collection if not exists
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )

    def add_memory(
        self,
        text: str,
        metadata: Dict[str, Any],
        id: Optional[str] = None
    ) -> str:
        """
        Add a memory to the vector store.

        Args:
            text: Text content to store
            metadata: Associated metadata (user_id, timestamp, category, etc.)
            id: Optional unique ID

        Returns:
            ID of stored memory
        """
        # Generate embedding
        embedding = self.embedder.encode(text).tolist()

        # Generate ID if not provided
        if id is None:
            id = f"{metadata.get('user_id', 'unknown')}_{datetime.now().timestamp()}"

        # Add timestamp if not present
        if 'timestamp' not in metadata:
            metadata['timestamp'] = datetime.now().isoformat()

        # Store based on backend
        if self.backend == "chromadb":
            self.collection.add(
                ids=[id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata]
            )

        elif self.backend == "qdrant":
            # Convert metadata to Qdrant format
            payload = {
                'text': text,
                **metadata
            }

            point = PointStruct(
                id=id,
                vector=embedding,
                payload=payload
            )

            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )

        return id

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar memories.

        Args:
            query: Search query
            top_k: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {'user_id': 123})

        Returns:
            List of matching memories with scores
        """
        # Generate query embedding
        query_embedding = self.embedder.encode(query).tolist()

        # Search based on backend
        if self.backend == "chromadb":
            # Build where clause for filtering
            where = filter_metadata if filter_metadata else None

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where
            )

            # Format results
            memories = []
            for i in range(len(results['ids'][0])):
                memories.append({
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'score': 1 - results['distances'][0][i]  # Convert distance to similarity
                })

            return memories

        elif self.backend == "qdrant":
            # Build filter
            query_filter = None
            if filter_metadata:
                conditions = [
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                    for key, value in filter_metadata.items()
                ]
                query_filter = Filter(must=conditions)

            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=query_filter,
                limit=top_k
            )

            # Format results
            memories = []
            for result in results:
                memories.append({
                    'id': result.id,
                    'text': result.payload.get('text', ''),
                    'metadata': {k: v for k, v in result.payload.items() if k != 'text'},
                    'score': result.score
                })

            return memories

    def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific memory by ID.

        Args:
            id: Memory ID

        Returns:
            Memory dict or None
        """
        if self.backend == "chromadb":
            result = self.collection.get(ids=[id])

            if result['ids']:
                return {
                    'id': result['ids'][0],
                    'text': result['documents'][0],
                    'metadata': result['metadatas'][0]
                }
            return None

        elif self.backend == "qdrant":
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[id]
            )

            if result:
                point = result[0]
                return {
                    'id': point.id,
                    'text': point.payload.get('text', ''),
                    'metadata': {k: v for k, v in point.payload.items() if k != 'text'}
                }
            return None

    def delete(self, id: str):
        """
        Delete a memory.

        Args:
            id: Memory ID
        """
        if self.backend == "chromadb":
            self.collection.delete(ids=[id])

        elif self.backend == "qdrant":
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[id]
            )

    def count(self) -> int:
        """Get total number of memories."""
        if self.backend == "chromadb":
            return self.collection.count()

        elif self.backend == "qdrant":
            info = self.client.get_collection(self.collection_name)
            return info.points_count

    def clear(self):
        """Clear all memories."""
        if self.backend == "chromadb":
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

        elif self.backend == "qdrant":
            self.client.delete_collection(self.collection_name)
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )


class MemoryManager:
    """
    High-level memory management for AI agents.

    Organizes memories into categories:
    - Episodic: Past events, experiences
    - Semantic: Facts, knowledge
    - Procedural: How-to, routines
    """

    def __init__(self, vector_store: VectorStore):
        """
        Initialize memory manager.

        Args:
            vector_store: Configured vector store instance
        """
        self.vector_store = vector_store

    def add_episodic_memory(
        self,
        user_id: int,
        event_text: str,
        event_type: str,
        timestamp: Optional[datetime] = None
    ) -> str:
        """
        Add an episodic memory (past event).

        Args:
            user_id: User ID
            event_text: Description of event
            event_type: Type of event (e.g., 'mood', 'activity', 'social')
            timestamp: When event occurred

        Returns:
            Memory ID
        """
        metadata = {
            'user_id': user_id,
            'memory_type': 'episodic',
            'event_type': event_type,
            'timestamp': (timestamp or datetime.now()).isoformat()
        }

        return self.vector_store.add_memory(event_text, metadata)

    def add_semantic_memory(
        self,
        user_id: int,
        fact: str,
        category: str
    ) -> str:
        """
        Add semantic memory (knowledge, fact).

        Args:
            user_id: User ID
            fact: Fact or knowledge
            category: Category of knowledge

        Returns:
            Memory ID
        """
        metadata = {
            'user_id': user_id,
            'memory_type': 'semantic',
            'category': category,
            'timestamp': datetime.now().isoformat()
        }

        return self.vector_store.add_memory(fact, metadata)

    def recall(
        self,
        user_id: int,
        query: str,
        memory_type: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recall relevant memories.

        Args:
            user_id: User ID
            query: What to recall
            memory_type: Optional filter ('episodic', 'semantic', 'procedural')
            top_k: Number of memories to retrieve

        Returns:
            List of relevant memories
        """
        # Build filter
        filter_metadata = {'user_id': user_id}
        if memory_type:
            filter_metadata['memory_type'] = memory_type

        return self.vector_store.search(query, top_k=top_k, filter_metadata=filter_metadata)

    def get_recent_memories(
        self,
        user_id: int,
        limit: int = 10,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get most recent memories.

        Args:
            user_id: User ID
            limit: Number of memories
            memory_type: Optional filter

        Returns:
            Recent memories sorted by timestamp
        """
        # Search with empty query to get any memories
        filter_metadata = {'user_id': user_id}
        if memory_type:
            filter_metadata['memory_type'] = memory_type

        memories = self.vector_store.search(
            query="",  # Empty query
            top_k=limit * 2,  # Get more than needed
            filter_metadata=filter_metadata
        )

        # Sort by timestamp
        memories.sort(
            key=lambda m: m['metadata'].get('timestamp', ''),
            reverse=True
        )

        return memories[:limit]

    def summarize_memories(
        self,
        user_id: int,
        topic: str,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Get summary of memories about a topic.

        Args:
            user_id: User ID
            topic: Topic to summarize
            top_k: Number of memories to include

        Returns:
            Summary with key memories
        """
        memories = self.recall(user_id, topic, top_k=top_k)

        # Group by type
        by_type = {}
        for memory in memories:
            mem_type = memory['metadata'].get('memory_type', 'unknown')
            if mem_type not in by_type:
                by_type[mem_type] = []
            by_type[mem_type].append(memory)

        return {
            'topic': topic,
            'total_memories': len(memories),
            'by_type': by_type,
            'most_relevant': memories[:3] if memories else []
        }
