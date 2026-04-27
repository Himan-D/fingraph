"""
Qdrant Vector Search Service - Semantic search for financial documents
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from config import settings
import json

logger = logging.getLogger(__name__)


class VectorSearchService:
    """Vector search for financial intelligence"""
    
    def __init__(self):
        self.client: Optional[QdrantClient] = None
        self.collection_name = "financial_documents"
        self.embedding_size = 1536  # OpenAI ada-002
    
    async def init(self):
        """Initialize Qdrant client"""
        try:
            if settings.QDRANT_URL:
                self.client = QdrantClient(url=settings.QDRANT_URL)
            else:
                self.client = QdrantClient(host="localhost", port=6333)
            
            await self._ensure_collection()
            logger.info("Qdrant initialized")
        except Exception as e:
            logger.warning(f"Qdrant init failed: {e}")
            self.client = None
    
    async def _ensure_collection(self):
        """Ensure collection exists"""
        try:
            collections = self.client.get_collections().collections
            names = [c.name for c in collections]
            
            if self.collection_name not in names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
        except Exception as e:
            logger.warning(f"Collection check failed: {e}")
    
    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ):
        """Add documents to vector store"""
        if not self.client:
            await self.init()
            if not self.client:
                return
        
        points = []
        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            point = PointStruct(
                id=doc.get("id", i),
                vector=embedding,
                payload={
                    "document_type": doc.get("type", "news"),
                    "title": doc.get("title", ""),
                    "content": doc.get("content", ""),
                    "symbols": doc.get("symbols", []),
                    "source": doc.get("source", ""),
                    "timestamp": doc.get("timestamp", ""),
                    "sentiment": doc.get("sentiment", "neutral"),
                    "url": doc.get("url", "")
                }
            )
            points.append(point)
        
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Added {len(points)} documents to vector store")
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
    
    async def semantic_search(
        self,
        query: str,
        embedding: List[float],
        limit: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Semantic search"""
        if not self.client:
            return []
        
        search_filter = None
        if filters:
            conditions = []
            if "symbols" in filters:
                conditions.append(
                    FieldCondition(
                        key="symbols",
                        match=MatchValue(value=filters["symbols"])
                    )
                )
            if "document_type" in filters:
                conditions.append(
                    FieldCondition(
                        key="document_type",
                        match=MatchValue(value=filters["document_type"])
                    )
                )
            if conditions:
                search_filter = Filter(must=conditions)
        
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                query_filter=search_filter,
                limit=limit
            )
            
            return [
                {
                    "id": r.id,
                    "score": r.score,
                    "title": r.payload.get("title"),
                    "content": r.payload.get("content"),
                    "symbols": r.payload.get("symbols", []),
                    "source": r.payload.get("source"),
                    "timestamp": r.payload.get("timestamp"),
                    "sentiment": r.payload.get("sentiment"),
                    "url": r.payload.get("url")
                }
                for r in results
            ]
        except Exception as e:
            logger.warning(f"Search failed: {e}")
            return []
    
    async def search_by_symbol(
        self,
        symbol: str,
        limit: int = 20
    ) -> List[Dict]:
        """Search documents related to a symbol"""
        if not self.client:
            return []
        
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=[0.0] * self.embedding_size,  # Placeholder
                query_filter=Filter(
                    must=[FieldCondition(key="symbols", match=MatchValue(value=symbol))]
                ),
                limit=limit
            )
            
            return [
                {
                    "title": r.payload.get("title"),
                    "content": r.payload.get("content"),
                    "score": r.score,
                    "source": r.payload.get("source"),
                    "timestamp": r.payload.get("timestamp")
                }
                for r in results
            ]
        except Exception as e:
            logger.warning(f"Symbol search failed: {e}")
            return []


class EmbeddingGenerator:
    """Generate embeddings for documents"""
    
    def __init__(self):
        self.model = "text-embedding-ada-002"
    
    async def generate(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings"""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = await client.embeddings.create(
                model=self.model,
                input=texts
            )
            
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}")
            return [[0.0] * 1536 for _ in texts]
    
    async def generate_query_embedding(self, query: str) -> List[float]:
        """Generate single query embedding"""
        embeddings = await self.generate([query])
        return embeddings[0] if embeddings else [0.0] * 1536


class SemanticSearchPipeline:
    """Complete semantic search pipeline"""
    
    def __init__(self):
        self.vector_search = VectorSearchService()
        self.embedding_generator = EmbeddingGenerator()
    
    async def init(self):
        """Initialize pipeline"""
        await self.vector_search.init()
    
    async def search(
        self,
        query: str,
        symbols: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Search documents semantically"""
        embedding = await self.embedding_generator.generate_query_embedding(query)
        
        filters = {}
        if symbols:
            filters["symbols"] = symbols[0] if len(symbols) == 1 else None
        
        return await self.vector_search.semantic_search(
            query, embedding, limit, filters
        )
    
    async def index_documents(
        self,
        documents: List[Dict[str, Any]]
    ):
        """Index documents with embeddings"""
        texts = [
            f"{doc.get('title', '')} {doc.get('content', '')}"
            for doc in documents
        ]
        
        embeddings = await self.embedding_generator.generate(texts)
        
        await self.vector_search.add_documents(documents, embeddings)


async def get_vector_search() -> VectorSearchService:
    """Get vector search service"""
    service = VectorSearchService()
    await service.init()
    return service


if __name__ == "__main__":
    import asyncio
    
    async def main():
        pipeline = SemanticSearchPipeline()
        await pipeline.init()
        
        results = await pipeline.search(" RBI interest rate decision impact")
        print(f"Found {len(results)} results")
    
    asyncio.run(main())