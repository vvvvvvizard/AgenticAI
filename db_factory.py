"""
Factory module for creating and managing vector database connections.
"""
from typing import Dict, Any, Optional
import json
import logging
from abc import ABC, abstractmethod
import faiss
import numpy as np
import pinecone
import weaviate
from sqlite3 import connect

logger = logging.getLogger(__name__)

class VectorDB(ABC):
    """Abstract base class for vector database implementations."""
    
    @abstractmethod
    def store_vectors(self, vectors: np.ndarray, metadata: Optional[Dict] = None) -> bool:
        """Store vectors with optional metadata."""
        pass
    
    @abstractmethod
    def search_vectors(self, query_vector: np.ndarray, top_k: int = 5) -> Dict[str, Any]:
        """Search for similar vectors."""
        pass

class SQLiteVectorDB(VectorDB):
    """SQLite implementation for vector storage."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialize_db()
    
    def _initialize_db(self):
        """Create necessary tables if they don't exist."""
        with connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vectors (
                    id INTEGER PRIMARY KEY,
                    embedding BLOB NOT NULL,
                    metadata TEXT
                )
            """)
    
    def store_vectors(self, vectors: np.ndarray, metadata: Optional[Dict] = None) -> bool:
        try:
            with connect(self.db_path) as conn:
                for i, vector in enumerate(vectors):
                    meta = json.dumps(metadata[i]) if metadata else None
                    conn.execute(
                        "INSERT INTO vectors (embedding, metadata) VALUES (?, ?)",
                        (vector.tobytes(), meta)
                    )
            return True
        except Exception as e:
            logger.error(f"Error storing vectors in SQLite: {str(e)}")
            return False
    
    def search_vectors(self, query_vector: np.ndarray, top_k: int = 5) -> Dict[str, Any]:
        """Basic vector search (not optimized for production use)."""
        try:
            results = []
            with connect(self.db_path) as conn:
                cursor = conn.execute("SELECT embedding, metadata FROM vectors")
                for row in cursor:
                    vector = np.frombuffer(row[0], dtype=np.float32)
                    distance = np.linalg.norm(query_vector - vector)
                    metadata = json.loads(row[1]) if row[1] else {}
                    results.append({
                        "distance": float(distance),
                        "metadata": metadata
                    })
            
            # Sort by distance and return top_k
            results.sort(key=lambda x: x["distance"])
            return {
                "matches": results[:top_k],
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error searching vectors in SQLite: {str(e)}")
            return {"status": "error", "error": str(e)}

class FAISSVectorDB(VectorDB):
    """FAISS implementation for vector search."""
    
    def __init__(self, dimension: int):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata_store = []
    
    def store_vectors(self, vectors: np.ndarray, metadata: Optional[Dict] = None) -> bool:
        try:
            if vectors.shape[1] != self.dimension:
                raise ValueError(f"Expected vectors of dimension {self.dimension}")
            
            self.index.add(vectors)
            if metadata:
                self.metadata_store.extend(metadata)
            return True
        except Exception as e:
            logger.error(f"Error storing vectors in FAISS: {str(e)}")
            return False
    
    def search_vectors(self, query_vector: np.ndarray, top_k: int = 5) -> Dict[str, Any]:
        try:
            distances, indices = self.index.search(
                query_vector.reshape(1, -1),
                top_k
            )
            
            matches = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                metadata = self.metadata_store[idx] if idx < len(self.metadata_store) else {}
                matches.append({
                    "id": int(idx),
                    "distance": float(distance),
                    "metadata": metadata
                })
            
            return {
                "matches": matches,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error searching vectors in FAISS: {str(e)}")
            return {"status": "error", "error": str(e)}

class PineconeVectorDB(VectorDB):
    """Pinecone implementation for vector search."""
    
    def __init__(self, api_key: str, environment: str, index_name: str):
        pinecone.init(api_key=api_key, environment=environment)
        self.index = pinecone.Index(index_name)
    
    def store_vectors(self, vectors: np.ndarray, metadata: Optional[Dict] = None) -> bool:
        try:
            vectors_with_ids = [
                (str(i), vector.tolist(), metadata[i] if metadata else {})
                for i, vector in enumerate(vectors)
            ]
            
            self.index.upsert(vectors=vectors_with_ids)
            return True
        except Exception as e:
            logger.error(f"Error storing vectors in Pinecone: {str(e)}")
            return False
    
    def search_vectors(self, query_vector: np.ndarray, top_k: int = 5) -> Dict[str, Any]:
        try:
            results = self.index.query(
                query_vector.tolist(),
                top_k=top_k,
                include_metadata=True
            )
            return {
                "matches": results.matches,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error searching vectors in Pinecone: {str(e)}")
            return {"status": "error", "error": str(e)}

def create_vector_db(config: Dict[str, Any]) -> VectorDB:
    """
    Factory function to create appropriate vector database instance.
    
    Args:
        config: Configuration dictionary containing database settings
        
    Returns:
        VectorDB instance based on configuration
    """
    db_type = config["type"]
    
    if db_type == "sqlite":
        return SQLiteVectorDB(config["location"])
    elif db_type == "faiss":
        return FAISSVectorDB(config.get("dimension", 768))  # Default to BERT dimension
    elif db_type == "pinecone":
        return PineconeVectorDB(
            config["api_key"],
            config["environment"],
            config.get("index_name", "default")
        )
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

# Example usage
if __name__ == "__main__":
    # Load configuration
    with open("config/vector_db_config.json", "r") as f:
        config = json.load(f)
    
    # Create database instance
    db_config = config["vector_databases"]["sqlite"]  # or "faiss", "pinecone"
    vector_db = create_vector_db(db_config)
    
    # Example vector operations
    vectors = np.random.rand(10, 768)  # 10 vectors of dimension 768
    metadata = [{"text": f"Document {i}"} for i in range(10)]
    
    # Store vectors
    success = vector_db.store_vectors(vectors, metadata)
    if success:
        logger.info("Vectors stored successfully")
    
    # Search vectors
    query = np.random.rand(768)
    results = vector_db.search_vectors(query, top_k=3)
    if results["status"] == "success":
        logger.info(f"Found {len(results['matches'])} matches")
