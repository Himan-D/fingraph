from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from config import settings

qdrant_client = None


def init_qdrant():
    global qdrant_client
    qdrant_client = QdrantClient(url=settings.QDRANT_URL)
    return qdrant_client


def get_qdrant():
    return qdrant_client


def create_collection(name: str, vector_size: int = 1536):
    """Create a collection for vector storage"""
    collections = qdrant_client.get_collections().collections
    if name not in [c.name for c in collections]:
        qdrant_client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
    return name


def upsert_vectors(collection_name: str, vectors: list, payloads: list, ids: list):
    """Insert vectors into collection"""
    from qdrant_client.models import PointStruct

    points = [
        PointStruct(id=i, vector=v, payload=p)
        for i, v, p in zip(ids, vectors, payloads)
    ]
    qdrant_client.upsert(collection_name=collection_name, points=points)


def search_vectors(collection_name: str, query_vector: list, limit: int = 5):
    """Search similar vectors"""
    results = qdrant_client.search(
        collection_name=collection_name, query_vector=query_vector, limit=limit
    )
    return results
