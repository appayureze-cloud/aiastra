"""
Conversation Pruning Service
Manages context window and prevents token limit issues
"""

import logging
from typing import List, Dict, Any, Optional
import tiktoken

logger = logging.getLogger(__name__)

class ConversationPruner:
    """Manages conversation history to stay within model context limits"""
    
    def __init__(self, model: str = "gpt-4"):
        self.model = model
        self.max_tokens = self._get_max_tokens(model)
        self.target_tokens = int(self.max_tokens * 0.7)  # Keep 70% for safety
        
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except:
            # Fallback to cl100k_base (GPT-4 encoding)
            self.encoding = tiktoken.get_encoding("cl100k_base")
        
        logger.info(f"✅ ConversationPruner initialized: max={self.max_tokens}, target={self.target_tokens}")
    
    def _get_max_tokens(self, model: str) -> int:
        """Get max context window for model"""
        model_limits = {
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-4-turbo": 128000,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384,
        }
        return model_limits.get(model, 8192)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.error(f"Token counting error: {e}")
            # Rough estimate: 1 token ~ 4 characters
            return len(text) // 4
    
    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Count total tokens in message list"""
        total = 0
        for message in messages:
            # Add tokens for message structure
            total += 4  # Every message has role, content, name, etc.
            total += self.count_tokens(message.get("content", ""))
        return total
    
    def prune_conversation(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Prune conversation to fit within context window
        
        Strategy:
        1. Always keep system prompt
        2. Always keep last N messages (most recent context)
        3. Summarize or remove old messages if needed
        """
        if not messages:
            return messages
        
        # Count current tokens
        current_tokens = self.count_messages_tokens(messages)
        
        if system_prompt:
            current_tokens += self.count_tokens(system_prompt)
        
        # If within limit, return as is
        if current_tokens <= self.target_tokens:
            logger.debug(f"✅ Conversation within limit: {current_tokens}/{self.target_tokens} tokens")
            return messages
        
        logger.warning(f"⚠️ Conversation too long: {current_tokens}/{self.target_tokens} tokens. Pruning...")
        
        # Keep last 10 messages (most recent context)
        keep_recent = 10
        recent_messages = messages[-keep_recent:] if len(messages) > keep_recent else messages
        
        # Count tokens in recent messages
        recent_tokens = self.count_messages_tokens(recent_messages)
        
        if system_prompt:
            recent_tokens += self.count_tokens(system_prompt)
        
        # If still too long, keep fewer messages
        if recent_tokens > self.target_tokens:
            keep_recent = 5
            recent_messages = messages[-keep_recent:]
            logger.warning(f"⚠️ Keeping only last {keep_recent} messages")
        
        # Optionally create summary of older messages
        if len(messages) > keep_recent:
            older_count = len(messages) - keep_recent
            summary_message = {
                "role": "system",
                "content": f"[Previous conversation summary: {older_count} earlier messages were exchanged about the user's health journey and symptoms]"
            }
            pruned_messages = [summary_message] + recent_messages
        else:
            pruned_messages = recent_messages
        
        final_tokens = self.count_messages_tokens(pruned_messages)
        logger.info(f"✅ Pruned conversation: {current_tokens} -> {final_tokens} tokens (kept {len(pruned_messages)} messages)")
        
        return pruned_messages
    
    def should_prune(self, messages: List[Dict[str, str]]) -> bool:
        """Check if conversation needs pruning"""
        current_tokens = self.count_messages_tokens(messages)
        return current_tokens > self.target_tokens

# Global instance
conversation_pruner = ConversationPruner()
