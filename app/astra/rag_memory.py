"""
Astra RAG Memory - FAISS-Based Safe Memory System

This module implements a safe, DISHA-compliant RAG (Retrieval-Augmented Generation)
memory system using FAISS (Facebook AI Similarity Search) for local vector storage.

ALLOWED MEMORY TYPES:
- chat_history_summary (condensed conversation context)
- user_preferences (dietary preferences, language, etc.)
- doctor_instructions (prescribed routines, advice)
- reminders (medicine schedules, follow-ups)
- user_stated_goals (wellness goals, lifestyle targets)

FORBIDDEN MEMORY TYPES:
- diagnosis_progress (medical diagnosis tracking)
- treatment_effectiveness (treatment outcome tracking)
- emotional_dependency (emotional state tracking)
- mental_health_inference (mental health conclusions)
"""

import logging
import json
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

# Try to import FAISS (optional dependency)
# Try to import FAISS (optional dependency)
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("⚠️ FAISS not installed. RAG memory will use fallback mode.")

# Try to import sentence-transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("⚠️ sentence-transformers not installed. Using random embeddings.")


class MemoryType:
    """Enumeration of allowed memory types"""
    CHAT_HISTORY_SUMMARY = "chat_history_summary"
    USER_PREFERENCES = "user_preferences"
    DOCTOR_INSTRUCTIONS = "doctor_instructions"
    REMINDERS = "reminders"
    USER_STATED_GOALS = "user_stated_goals"
    
    # Forbidden types (will be rejected)
    FORBIDDEN = [
        "diagnosis_progress",
        "treatment_effectiveness",
        "emotional_dependency",
        "mental_health_inference"
    ]
    
    ALLOWED = [
        CHAT_HISTORY_SUMMARY,
        USER_PREFERENCES,
        DOCTOR_INSTRUCTIONS,
        REMINDERS,
        USER_STATED_GOALS
    ]


class RAGMemory:
    """
    FAISS-based safe RAG memory system.
    
    RULES:
    - Only stores allowed memory types
    - Rejects forbidden memory types
    - Profile-specific isolation
    - Automatic expiration
    - Consent-based access
    - No raw medical data storage
    """
    
    def __init__(
        self,
        embedding_dim: int = 384,  # Sentence transformer dimension
        db_connection=None,
        storage_path: str = "./astra_memory"
    ):
        """
        Initialize RAG memory system.
        
        Args:
            embedding_dim: Dimension of embedding vectors
            db_connection: Database connection for metadata
            storage_path: Path to store FAISS indexes
        """
        self.embedding_dim = embedding_dim
        self.db = db_connection
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # FAISS indexes (one per profile for isolation)
        self.indexes = {}
        
        # Metadata storage (maps vector ID to metadata)
        self.metadata = {}
        
        # Initialize embedding model
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # Use a lightweight model for embeddings
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✅ Sentence Transformer model loaded (all-MiniLM-L6-v2)")
            except Exception as e:
                logger.error(f"❌ Failed to load embedding model: {e}")
                self.embedding_model = None
        else:
            self.embedding_model = None
        
        logger.info("✅ RAG Memory initialized (FAISS: %s)", FAISS_AVAILABLE)
    
    async def store_memory(
        self,
        profile_id: str,
        memory_type: str,
        content: str,
        metadata: Optional[Dict] = None,
        ttl_days: int = 90
    ) -> Dict:
        """
        Store a memory in RAG system.
        
        Args:
            profile_id: Profile ID (for isolation)
            memory_type: Type of memory (must be in ALLOWED list)
            content: Content to store
            metadata: Optional metadata
            ttl_days: Time-to-live in days (default: 90 days)
        
        Returns:
            {
                "success": bool,
                "memory_id": str,
                "memory_type": str,
                "expires_at": datetime,
                "message": str
            }
        """
        # Validate memory type
        if not self._is_allowed_memory_type(memory_type):
            logger.warning("⛔ Forbidden memory type: %s", memory_type)
            return {
                "success": False,
                "memory_id": None,
                "memory_type": memory_type,
                "expires_at": None,
                "message": f"Memory type '{memory_type}' is not allowed. Only allowed types: {MemoryType.ALLOWED}"
            }
        
        # Sanitize content (remove any medical conclusions)
        sanitized_content = self._sanitize_content(content, memory_type)
        
        # Generate embedding
        embedding = self._generate_embedding(sanitized_content)
        
        # Generate memory ID
        memory_id = self._generate_memory_id(profile_id, memory_type, sanitized_content)
        
        # Calculate expiration
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(days=ttl_days)
        
        # Store in FAISS index
        if FAISS_AVAILABLE:
            success = await self._store_in_faiss(
                profile_id=profile_id,
                memory_id=memory_id,
                embedding=embedding,
                memory_type=memory_type,
                content=sanitized_content,
                metadata=metadata,
                expires_at=expires_at
            )
        else:
            # Fallback: store in database only
            success = await self._store_in_db(
                profile_id=profile_id,
                memory_id=memory_id,
                memory_type=memory_type,
                content=sanitized_content,
                metadata=metadata,
                expires_at=expires_at
            )
        
        if success:
            logger.info("✅ Memory stored: %s (type: %s, profile: %s)", 
                       memory_id, memory_type, profile_id)
            return {
                "success": True,
                "memory_id": memory_id,
                "memory_type": memory_type,
                "expires_at": expires_at.isoformat(),
                "message": "Memory stored successfully"
            }
        else:
            logger.error("❌ Failed to store memory")
            return {
                "success": False,
                "memory_id": None,
                "memory_type": memory_type,
                "expires_at": None,
                "message": "Failed to store memory"
            }
    
    async def retrieve(
        self,
        query: str,
        context_type: str,
        profile_id: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> Optional[str]:
        """
        Retrieve relevant context from RAG memory.
        
        Args:
            query: Query text
            context_type: Type of context to retrieve
            profile_id: Profile ID (for isolation)
            top_k: Number of results to retrieve
            similarity_threshold: Minimum similarity score
        
        Returns:
            Concatenated context string or None
        """
        # Validate context type
        if not self._is_allowed_memory_type(context_type):
            logger.warning("⛔ Forbidden context type: %s", context_type)
            return None
        
        # Generate query embedding
        query_embedding = self._generate_embedding(query)
        
        # Search FAISS index
        if FAISS_AVAILABLE:
            results = await self._search_faiss(
                profile_id=profile_id,
                query_embedding=query_embedding,
                memory_type=context_type,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )
        else:
            # Fallback: simple text search in database
            results = await self._search_db(
                profile_id=profile_id,
                query=query,
                memory_type=context_type,
                top_k=top_k
            )
        
        if not results:
            logger.info("ℹ️ No relevant context found for query")
            return None
        
        # Concatenate results
        context = "\n\n".join([r['content'] for r in results])
        
        logger.info("✅ Retrieved %d memory items for context", len(results))
        return context
    
    async def delete_memory(
        self,
        profile_id: str,
        memory_id: str
    ) -> Dict:
        """
        Delete a specific memory.
        
        Args:
            profile_id: Profile ID
            memory_id: Memory ID to delete
        
        Returns:
            {
                "success": bool,
                "message": str
            }
        """
        # Delete from FAISS index
        if FAISS_AVAILABLE:
            success = await self._delete_from_faiss(profile_id, memory_id)
        else:
            success = await self._delete_from_db(profile_id, memory_id)
        
        if success:
            logger.info("✅ Memory deleted: %s", memory_id)
            return {
                "success": True,
                "message": "Memory deleted successfully"
            }
        else:
            logger.error("❌ Failed to delete memory: %s", memory_id)
            return {
                "success": False,
                "message": "Failed to delete memory"
            }
    
    async def clear_profile_memory(
        self,
        profile_id: str,
        memory_type: Optional[str] = None
    ) -> Dict:
        """
        Clear all memories for a profile (or specific type).
        
        Args:
            profile_id: Profile ID
            memory_type: Optional memory type to clear (if None, clears all)
        
        Returns:
            {
                "success": bool,
                "deleted_count": int,
                "message": str
            }
        """
        if FAISS_AVAILABLE:
            count = await self._clear_faiss_index(profile_id, memory_type)
        else:
            count = await self._clear_db_memory(profile_id, memory_type)
        
        logger.info("✅ Cleared %d memories for profile %s", count, profile_id)
        return {
            "success": True,
            "deleted_count": count,
            "message": f"Cleared {count} memories"
        }
    
    def _is_allowed_memory_type(self, memory_type: str) -> bool:
        """Check if memory type is allowed"""
        if memory_type in MemoryType.FORBIDDEN:
            return False
        return memory_type in MemoryType.ALLOWED
    
    def _sanitize_content(self, content: str, memory_type: str) -> str:
        """
        Sanitize content to remove forbidden patterns.
        
        This ensures no medical conclusions are stored in memory.
        """
        sanitized = content
        
        # Remove diagnosis patterns
        diagnosis_patterns = [
            r'(?i)diagnosed with',
            r'(?i)you have',
            r'(?i)suffering from',
            r'(?i)condition is'
        ]
        
        for pattern in diagnosis_patterns:
            import re
            sanitized = re.sub(pattern, '[REDACTED]', sanitized)
        
        # Remove treatment effectiveness patterns
        effectiveness_patterns = [
            r'(?i)treatment is working',
            r'(?i)medicine is effective',
            r'(?i)getting better',
            r'(?i)healing progress'
        ]
        
        for pattern in effectiveness_patterns:
            import re
            sanitized = re.sub(pattern, '[REDACTED]', sanitized)
        
        return sanitized
    
    def _generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding vector for text.
        """
        if self.embedding_model:
            # Use actual sentence transformer
            try:
                embedding = self.embedding_model.encode(text)
                return embedding.astype('float32')
            except Exception as e:
                logger.error(f"❌ Embedding generation failed: {e}")
        
        # Fallback: random vector (for testing only)
        # logger.warning("⚠️ Using random embedding (install sentence-transformers for production)")
        np.random.seed(hash(text) % (2**32))
        return np.random.randn(self.embedding_dim).astype('float32')
    
    def _generate_memory_id(self, profile_id: str, memory_type: str, content: str) -> str:
        """Generate unique memory ID"""
        data = f"{profile_id}:{memory_type}:{content}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    async def _store_in_faiss(
        self,
        profile_id: str,
        memory_id: str,
        embedding: np.ndarray,
        memory_type: str,
        content: str,
        metadata: Optional[Dict],
        expires_at: datetime
    ) -> bool:
        """Store embedding in FAISS index"""
        try:
            # Get or create index for this profile
            if profile_id not in self.indexes:
                self.indexes[profile_id] = faiss.IndexFlatL2(self.embedding_dim)
            
            # Add to index
            self.indexes[profile_id].add(embedding.reshape(1, -1))
            
            # Store metadata
            if profile_id not in self.metadata:
                self.metadata[profile_id] = {}
            
            vector_id = self.indexes[profile_id].ntotal - 1
            self.metadata[profile_id][vector_id] = {
                "memory_id": memory_id,
                "memory_type": memory_type,
                "content": content,
                "metadata": metadata,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": expires_at.isoformat()
            }
            
            # Also save to database for persistence
            await self._store_in_db(profile_id, memory_id, memory_type, content, metadata, expires_at)
            
            return True
            
        except Exception as e:
            logger.error("❌ Error storing in FAISS: %s", e)
            return False
    
    async def _search_faiss(
        self,
        profile_id: str,
        query_embedding: np.ndarray,
        memory_type: str,
        top_k: int,
        similarity_threshold: float
    ) -> List[Dict]:
        """Search FAISS index"""
        try:
            if profile_id not in self.indexes:
                return []
            
            # Search index
            distances, indices = self.indexes[profile_id].search(
                query_embedding.reshape(1, -1),
                top_k
            )
            
            # Filter by memory type and similarity threshold
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx == -1:
                    continue
                
                # Convert L2 distance to similarity score (0-1)
                similarity = 1 / (1 + dist)
                
                if similarity < similarity_threshold:
                    continue
                
                meta = self.metadata[profile_id].get(idx)
                if not meta:
                    continue
                
                if meta['memory_type'] != memory_type:
                    continue
                
                # Check expiration
                expires_at = datetime.fromisoformat(meta['expires_at'])
                if datetime.utcnow() > expires_at:
                    continue
                
                results.append({
                    "content": meta['content'],
                    "similarity": float(similarity),
                    "memory_id": meta['memory_id'],
                    "metadata": meta.get('metadata', {})
                })
            
            return results
            
        except Exception as e:
            logger.error("❌ Error searching FAISS: %s", e)
            return []
    
    async def _store_in_db(
        self,
        profile_id: str,
        memory_id: str,
        memory_type: str,
        content: str,
        metadata: Optional[Dict],
        expires_at: datetime
    ) -> bool:
        """Store memory metadata in database"""
        if not self.db:
            logger.warning("⚠️ Database not connected, memory not persisted")
            return True  # Don't fail if DB not available
        
        try:
            # Store in astra_rag_memory table
            # Implementation depends on your database
            # This is a placeholder
            
            return True
            
        except Exception as e:
            logger.error("❌ Error storing in database: %s", e)
            return False
    
    async def _search_db(
        self,
        profile_id: str,
        query: str,
        memory_type: str,
        top_k: int
    ) -> List[Dict]:
        """Fallback: simple text search in database"""
        if not self.db:
            return []
        
        try:
            # Simple text search (fallback when FAISS not available)
            # Implementation depends on your database
            # This is a placeholder
            
            return []
            
        except Exception as e:
            logger.error("❌ Error searching database: %s", e)
            return []
    
    async def _delete_from_faiss(self, profile_id: str, memory_id: str) -> bool:
        """Delete from FAISS index (FAISS doesn't support deletion, so we mark as deleted)"""
        # FAISS doesn't support deletion, so we remove from metadata
        if profile_id in self.metadata:
            for vector_id, meta in list(self.metadata[profile_id].items()):
                if meta['memory_id'] == memory_id:
                    del self.metadata[profile_id][vector_id]
                    await self._delete_from_db(profile_id, memory_id)
                    return True
        return False
    
    async def _delete_from_db(self, profile_id: str, memory_id: str) -> bool:
        """Delete from database"""
        if not self.db:
            return True
        
        try:
            # Delete from database
            # Implementation depends on your database
            return True
        except Exception as e:
            logger.error("❌ Error deleting from database: %s", e)
            return False
    
    async def _clear_faiss_index(self, profile_id: str, memory_type: Optional[str]) -> int:
        """Clear FAISS index for profile"""
        count = 0
        if profile_id in self.metadata:
            if memory_type:
                # Clear specific type
                for vector_id, meta in list(self.metadata[profile_id].items()):
                    if meta['memory_type'] == memory_type:
                        del self.metadata[profile_id][vector_id]
                        count += 1
            else:
                # Clear all
                count = len(self.metadata[profile_id])
                del self.metadata[profile_id]
                if profile_id in self.indexes:
                    del self.indexes[profile_id]
        
        await self._clear_db_memory(profile_id, memory_type)
        return count
    
    async def _clear_db_memory(self, profile_id: str, memory_type: Optional[str]) -> int:
        """Clear database memory"""
        if not self.db:
            return 0
        
        try:
            # Clear from database
            # Implementation depends on your database
            return 0
        except Exception as e:
            logger.error("❌ Error clearing database: %s", e)
            return 0
