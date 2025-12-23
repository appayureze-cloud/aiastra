"""
Dynamic Shopify API Integration Service
Fetches medicine catalog directly from Shopify store in real-time
"""

import os
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class ShopifyAPIService:
    """Real-time Shopify API integration for dynamic medicine catalog"""
    
    def __init__(self):
        self.shop_url = os.getenv("SHOPIFY_SHOP_URL")
        self.access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
        
        self.enabled = bool(self.shop_url and self.access_token)
        
        # Initialize base_url even if disabled to prevent AttributeError
        self.base_url = None
        self.headers = {}
        
        if not self.enabled:
            logger.warning("Shopify credentials not found. Shopify integration will be disabled.")
            return
            
        # Clean up shop URL format
        if not self.shop_url.startswith("https://"):
            self.shop_url = f"https://{self.shop_url}"
        if not self.shop_url.endswith(".myshopify.com"):
            if not self.shop_url.endswith(".myshopify.com/"):
                self.shop_url = f"{self.shop_url.rstrip('/')}.myshopify.com"
        
        self.api_version = "2023-10"
        self.base_url = f"{self.shop_url}/admin/api/{self.api_version}"
        
        self.headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }
        
        logger.info(f"Shopify API service initialized for: {self.shop_url}")
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[requests.Response]:
        """Make authenticated request to Shopify API"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params or {})
            
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                logger.warning("Shopify API rate limit reached, retrying...")
                # Simple rate limit handling
                import time
                time.sleep(2)
                return self._make_request(endpoint, params)
            else:
                logger.error(f"Shopify API error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Shopify API request failed: {e}")
            return None
    
    def get_all_products(self) -> List[Dict]:
        """Fetch all products from Shopify store with pagination"""
        all_products = []
        page_info = None
        
        while True:
            if not page_info:
                # First request: include status filter
                params = {
                    "limit": 250,
                    "status": "active"
                }
            else:
                # Subsequent requests: only limit and page_info allowed
                params = {
                    "limit": 250,
                    "page_info": page_info
                }
            
            response = self._make_request("products.json", params)
            
            if not response:
                break
                
            data = response.json()
            if "products" not in data:
                break
            
            products = data["products"]
            all_products.extend(products)
            
            # Get next page info from Link header if available
            page_info = self._extract_next_page_info(response)
            if not page_info:
                break
        
        logger.info(f"Fetched {len(all_products)} products from Shopify")
        return all_products
    
    def _extract_next_page_info(self, response: requests.Response) -> Optional[str]:
        """Extract next page info for pagination from Link header"""
        link_header = response.headers.get("Link")
        if not link_header:
            return None
            
        # Link header format: <https://.../products.json?page_info=xxx>; rel="next"
        links = link_header.split(",")
        for link in links:
            if 'rel="next"' in link:
                try:
                    # Extract URL part
                    url_part = link.split(";")[0].strip("<> ")
                    
                    # Extract page_info parameter
                    from urllib.parse import urlparse, parse_qs
                    parsed = urlparse(url_part)
                    params = parse_qs(parsed.query)
                    
                    if "page_info" in params:
                        return params["page_info"][0]
                except Exception as e:
                    logger.warning(f"Failed to parse Link header: {e}")
        
        return None
    
    def format_medicine_catalog(self) -> List[Dict]:
        """Format Shopify products into medicine catalog format"""
        products = self.get_all_products()
        medicine_catalog = []
        
        for product in products:
            try:
                # Get first variant for pricing
                variant = product.get("variants", [{}])[0]
                
                medicine_info = {
                    "name": product.get("title", "").strip(),
                    "variant_id": str(variant.get("id", "")),
                    "product_id": str(product.get("id", "")),
                    "title": product.get("title", "").strip(),
                    "price": f"₹{float(variant.get('price', 0)):.2f}",
                    "available": variant.get("inventory_quantity", 0) > 0 if variant.get("inventory_management") else True,
                    "sku": variant.get("sku", ""),
                    "inventory_quantity": variant.get("inventory_quantity", 0),
                    "weight": variant.get("weight", 0),
                    "requires_shipping": variant.get("requires_shipping", True),
                    "taxable": variant.get("taxable", True),
                    "product_type": product.get("product_type", ""),
                    "vendor": product.get("vendor", ""),
                    "tags": product.get("tags", "").split(",") if product.get("tags") else [],
                    "created_at": product.get("created_at", ""),
                    "updated_at": product.get("updated_at", ""),
                    "description": product.get("body_html", ""),
                    "handle": product.get("handle", "")
                }
                
                medicine_catalog.append(medicine_info)
                
            except Exception as e:
                logger.warning(f"Error processing product {product.get('title', 'Unknown')}: {e}")
                continue
        
        # Sort by name for consistency
        medicine_catalog.sort(key=lambda x: x["name"].lower())
        
        logger.info(f"Formatted {len(medicine_catalog)} medicines from Shopify catalog")
        return medicine_catalog
    
    def get_product_by_name(self, medicine_name: str) -> Optional[Dict]:
        """Find specific product by name"""
        products = self.format_medicine_catalog()
        
        # Normalize search term
        search_term = medicine_name.lower().strip()
        
        # First try exact match
        for product in products:
            if product["name"].lower() == search_term:
                return product
        
        # Then try partial match
        for product in products:
            if search_term in product["name"].lower():
                return product
        
        return None
    
    def get_product_info(self, medicine_name: str) -> Dict:
        """Get complete product information for a medicine"""
        product = self.get_product_by_name(medicine_name)
        
        if product:
            return {
                "medicine_name": medicine_name,
                "shopify_variant_id": product["variant_id"],
                "shopify_product_id": product["product_id"],
                "shopify_product_title": product["title"],
                "price": product["price"],
                "is_available": product["available"],
                "sku": product["sku"],
                "inventory_quantity": product["inventory_quantity"],
                "product_type": product["product_type"],
                "vendor": product["vendor"],
                "tags": product["tags"],
                "suggested_alternatives": self._get_similar_products(medicine_name)
            }
        
        return {
            "medicine_name": medicine_name,
            "shopify_variant_id": None,
            "shopify_product_id": None,
            "shopify_product_title": None,
            "price": None,
            "is_available": False,
            "sku": None,
            "inventory_quantity": 0,
            "product_type": None,
            "vendor": None,
            "tags": [],
            "suggested_alternatives": self._get_similar_products(medicine_name)
        }
    
    def _get_similar_products(self, medicine_name: str, limit: int = 5) -> List[Dict]:
        """Get similar products for suggestions"""
        try:
            products = self.format_medicine_catalog()
            search_terms = medicine_name.lower().split()
            
            similar_products = []
            for product in products[:limit]:  # Limit for performance
                name_words = product["name"].lower().split()
                
                # Simple similarity check
                common_words = set(search_terms) & set(name_words)
                if common_words and product["available"]:
                    similar_products.append({
                        "name": product["name"],
                        "variant_id": product["variant_id"],
                        "price": product["price"]
                    })
            
            return similar_products[:limit]
            
        except Exception as e:
            logger.warning(f"Error finding similar products: {e}")
            return []
    
    def health_check(self) -> Dict:
        """Check Shopify API connectivity"""
        try:
            response = self._make_request("shop.json")
            if response:
                data = response.json()
                if "shop" in data:
                    shop_info = data["shop"]
                    return {
                        "status": "connected",
                        "shop_name": shop_info.get("name", "Unknown"),
                        "shop_domain": shop_info.get("domain", "Unknown"),
                        "currency": shop_info.get("currency", "Unknown"),
                        "timezone": shop_info.get("iana_timezone", "Unknown"),
                        "last_checked": datetime.now().isoformat()
                    }
            
            return {
                "status": "error",
                "message": "Failed to connect to Shopify API",
                "last_checked": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Shopify API health check failed: {str(e)}",
                "last_checked": datetime.now().isoformat()
            }

# Global instance for API access
shopify_api = ShopifyAPIService()