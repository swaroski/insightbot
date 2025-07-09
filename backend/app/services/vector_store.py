import os
import pickle
import uuid
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import faiss
from openai import OpenAI
from loguru import logger
from app.config import settings
from app.models.schemas import Source


class VectorStore:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.index: Optional[faiss.IndexFlatIP] = None
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.embeddings_dim = 1536  # OpenAI embedding dimension
        
        # Create directories if they don't exist
        os.makedirs(settings.faiss_index_path, exist_ok=True)
        os.makedirs(settings.upload_dir, exist_ok=True)
        
        # Load existing index if available
        self.load_index()
    
    def load_index(self) -> None:
        """Load FAISS index and documents from disk"""
        try:
            index_path = os.path.join(settings.faiss_index_path, "faiss_index.bin")
            docs_path = os.path.join(settings.faiss_index_path, "documents.pkl")
            
            if os.path.exists(index_path) and os.path.exists(docs_path):
                self.index = faiss.read_index(index_path)
                with open(docs_path, "rb") as f:
                    self.documents = pickle.load(f)
                logger.info(f"Loaded FAISS index with {len(self.documents)} documents")
            else:
                self.index = faiss.IndexFlatIP(self.embeddings_dim)
                logger.info("Created new FAISS index")
        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}")
            self.index = faiss.IndexFlatIP(self.embeddings_dim)
    
    def save_index(self) -> None:
        """Save FAISS index and documents to disk"""
        try:
            index_path = os.path.join(settings.faiss_index_path, "faiss_index.bin")
            docs_path = os.path.join(settings.faiss_index_path, "documents.pkl")
            
            faiss.write_index(self.index, index_path)
            with open(docs_path, "wb") as f:
                pickle.dump(self.documents, f)
            logger.info("Saved FAISS index and documents")
        except Exception as e:
            logger.error(f"Error saving FAISS index: {e}")
    
    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for a list of texts using OpenAI"""
        try:
            response = self.client.embeddings.create(
                model=settings.embedding_model,
                input=texts
            )
            embeddings = [data.embedding for data in response.data]
            return np.array(embeddings, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            raise
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def add_document(self, content: str, filename: str, metadata: Dict[str, Any] = None) -> str:
        """Add a document to the vector store"""
        try:
            document_id = str(uuid.uuid4())
            
            # Chunk the document
            chunks = self.chunk_text(content)
            
            # Get embeddings for all chunks
            embeddings = self.get_embeddings(chunks)
            
            # Add to FAISS index
            self.index.add(embeddings)
            
            # Store document metadata
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_{i}"
                self.documents[chunk_id] = {
                    "document_id": document_id,
                    "filename": filename,
                    "content": chunk,
                    "chunk_index": i,
                    "metadata": metadata or {}
                }
            
            # Save index
            self.save_index()
            
            logger.info(f"Added document {filename} with {len(chunks)} chunks")
            return document_id
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise
    
    def search(self, query: str, k: int = 5, score_threshold: float = 0.7) -> List[Source]:
        """Search for relevant documents"""
        try:
            if self.index.ntotal == 0:
                logger.warning("No documents in index")
                return []
            
            # Get query embedding
            query_embedding = self.get_embeddings([query])
            
            # Search FAISS index
            scores, indices = self.index.search(query_embedding, k)
            
            # Convert results to Source objects
            sources = []
            chunk_ids = list(self.documents.keys())
            
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1 or score < score_threshold:
                    continue
                
                if idx < len(chunk_ids):
                    chunk_id = chunk_ids[idx]
                    doc_info = self.documents[chunk_id]
                    
                    source = Source(
                        content=doc_info["content"],
                        filename=doc_info["filename"],
                        page=doc_info.get("chunk_index"),
                        relevance_score=float(score)
                    )
                    sources.append(source)
            
            # Sort by relevance score
            sources.sort(key=lambda x: x.relevance_score, reverse=True)
            
            logger.info(f"Found {len(sources)} relevant sources for query")
            return sources
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            raise
    
    def get_document_count(self) -> int:
        """Get the total number of documents in the index"""
        return len(set(doc["document_id"] for doc in self.documents.values()))
    
    def get_chunk_count(self) -> int:
        """Get the total number of chunks in the index"""
        return len(self.documents)
    
    def remove_document(self, document_id: str) -> bool:
        """Remove a document from the vector store"""
        try:
            # Find chunks belonging to this document
            chunks_to_remove = [
                chunk_id for chunk_id, doc_info in self.documents.items()
                if doc_info["document_id"] == document_id
            ]
            
            if not chunks_to_remove:
                logger.warning(f"Document {document_id} not found")
                return False
            
            # Remove chunks from documents dict
            for chunk_id in chunks_to_remove:
                del self.documents[chunk_id]
            
            # Note: FAISS doesn't support removing individual vectors efficiently
            # For production, consider using a different vector store or rebuilding index
            logger.warning("Document metadata removed, but FAISS index not rebuilt")
            
            # Save updated documents
            self.save_index()
            
            logger.info(f"Removed document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing document: {e}")
            return False


# Global vector store instance
vector_store = VectorStore()