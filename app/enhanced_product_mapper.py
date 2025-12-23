"""
Enhanced Product Mapper
Combines static mapping with dynamic Shopify API lookups and intelligent search
"""

import logging
import re
from typing import Optional, Dict, List, Tuple
from difflib import SequenceMatcher
from app.all_products_mapping import ProductMapper as StaticMapper
from app.shopify_api_service import ShopifyAPIService

logger = logging.getLogger(__name__)

class EnhancedProductMapper:
    """Enhanced product mapper with fuzzy matching and dynamic API integration"""
    
    def __init__(self):
        self.static_mapper = StaticMapper()
        self.shopify_api = ShopifyAPIService()
        self._dynamic_cache = {}
        self._cache_loaded = False
        
    def normalize_name(self, name: str) -> str:
        """Normalize medicine name for better matching"""
        if not name:
            return ""
            
        # Convert to lowercase
        normalized = name.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove common variations and punctuation
        normalized = re.sub(r'[.,\-_()[\]{}]', '', normalized)
        
        # Handle common spelling variations
        replacements = {
            'churna': 'churna',
            'choornam': 'churna',
            'arishtam': 'arishtam',
            'arishta': 'arishtam',
            'kashaayam': 'kashayam',
            'kashayam': 'kashayam',
            'ghritam': 'ghritam',
            'ghrita': 'ghritam',
            'tailam': 'tailam',
            'taila': 'tailam'
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
            
        return normalized
    
    def calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity score between two medicine names"""
        norm1 = self.normalize_name(name1)
        norm2 = self.normalize_name(name2)
        
        # Use difflib for sequence matching
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def load_dynamic_cache(self):
        """Load dynamic product catalog from Shopify API"""
        if self._cache_loaded:
            return
        
        # Check if Shopify API is enabled
        if not hasattr(self.shopify_api, 'enabled') or not self.shopify_api.enabled:
            logger.warning("Shopify API is disabled. Dynamic cache will be empty.")
            self._cache_loaded = True
            return
            
        try:
            logger.info("Loading dynamic product catalog from Shopify API...")
            catalog = self.shopify_api.format_medicine_catalog()
            
            for product in catalog:
                # Index by normalized name
                normalized_name = self.normalize_name(product["name"])
                self._dynamic_cache[normalized_name] = {
                    "variant_id": product["variant_id"],
                    "product_title": product["title"],
                    "price": product["price"],
                    "available": product["available"],
                    "sku": product["sku"],
                    "original_name": product["name"]
                }
            
            self._cache_loaded = True
            logger.info(f"Loaded {len(self._dynamic_cache)} products into dynamic cache")
            
        except Exception as e:
            logger.error(f"Failed to load dynamic product catalog: {e}")
            self._cache_loaded = True  # Mark as loaded to prevent retry loops
    
    def get_variant_id_static(self, medicine_name: str) -> Optional[str]:
        """Get variant ID using static mapping"""
        try:
            return self.static_mapper.get_variant_id(medicine_name)
        except Exception as e:
            logger.debug(f"Static mapping failed for {medicine_name}: {e}")
            return None
    
    def get_variant_id_dynamic(self, medicine_name: str) -> Optional[str]:
        """Get variant ID using dynamic API mapping"""
        self.load_dynamic_cache()
        
        normalized_search = self.normalize_name(medicine_name)
        
        # Exact match first
        if normalized_search in self._dynamic_cache:
            return self._dynamic_cache[normalized_search]["variant_id"]
        
        # Fuzzy matching with similarity threshold
        best_match = None
        best_score = 0.0
        threshold = 0.8  # 80% similarity threshold
        
        for cached_name, product_info in self._dynamic_cache.items():
            similarity = self.calculate_similarity(medicine_name, product_info["original_name"])
            
            if similarity > best_score and similarity >= threshold:
                best_score = similarity
                best_match = product_info
        
        if best_match:
            logger.info(f"Found fuzzy match for '{medicine_name}': '{best_match['original_name']}' (similarity: {best_score:.2f})")
            return best_match["variant_id"]
        
        return None
    
    def get_variant_id_with_alternatives(self, medicine_name: str) -> Tuple[Optional[str], List[str]]:
        """Get variant ID with alternative suggestions"""
        # Try exact static mapping first
        variant_id = self.get_variant_id_static(medicine_name)
        if variant_id:
            return variant_id, []
        
        # Try dynamic mapping with fuzzy matching
        variant_id = self.get_variant_id_dynamic(medicine_name)
        if variant_id:
            return variant_id, []
        
        # Find similar alternatives
        alternatives = self.find_similar_products(medicine_name)
        return None, alternatives
    
    def get_variant_id(self, medicine_name: str) -> Optional[str]:
        """Main method to get variant ID - tries multiple strategies"""
        variant_id, _ = self.get_variant_id_with_alternatives(medicine_name)
        return variant_id
    
    def find_similar_products(self, medicine_name: str, limit: int = 5) -> List[str]:
        """Find similar products for suggestions"""
        self.load_dynamic_cache()
        
        similarities = []
        for cached_name, product_info in self._dynamic_cache.items():
            similarity = self.calculate_similarity(medicine_name, product_info["original_name"])
            if similarity > 0.3:  # Minimum 30% similarity for suggestions
                similarities.append((similarity, product_info["original_name"]))
        
        # Sort by similarity and return top matches
        similarities.sort(reverse=True)
        return [name for _, name in similarities[:limit]]
    
    def get_product_info(self, medicine_name: str) -> Dict:
        """Get comprehensive product information"""
        self.load_dynamic_cache()
        
        # Try to get variant ID
        variant_id, alternatives = self.get_variant_id_with_alternatives(medicine_name)
        
        if variant_id:
            # Find product details
            normalized_search = self.normalize_name(medicine_name)
            
            # Search in dynamic cache
            for cached_name, product_info in self._dynamic_cache.items():
                if product_info["variant_id"] == variant_id:
                    return {
                        "medicine_name": medicine_name,
                        "shopify_variant_id": variant_id,
                        "shopify_product_title": product_info["product_title"],
                        "price": product_info["price"],
                        "is_available": product_info["available"],
                        "sku": product_info["sku"],
                        "suggested_alternatives": alternatives
                    }
        
        # Product not found
        return {
            "medicine_name": medicine_name,
            "shopify_variant_id": None,
            "shopify_product_title": None,
            "price": None,
            "is_available": False,
            "sku": None,
            "suggested_alternatives": alternatives
        }
    
    def get_mapping_stats(self) -> Dict:
        """Get statistics about the mapping system"""
        self.load_dynamic_cache()
        
        return {
            "static_products": len(self.static_mapper.medicine_mapping) if hasattr(self.static_mapper, 'medicine_mapping') else 0,
            "dynamic_products": len(self._dynamic_cache),
            "cache_loaded": self._cache_loaded
        }

# Create global instance
enhanced_product_mapper = EnhancedProductMapper()