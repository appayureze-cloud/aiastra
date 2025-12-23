"""
Product Mapping System for Medicine Names to Shopify Variant IDs
"""

from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

class ProductMapper:
    """Maps medicine names to Shopify variant IDs and manages product catalog"""
    
    def __init__(self):
        # Real Shopify products from Ayureze Healthcare catalog
        # SKUs and prices from actual product export
        self.medicine_mapping: Dict[str, Dict] = {
            # Biotics Life Products
            "bioticslife cisplus max": {
                "variant_id": "AEBIO1008",
                "product_title": "Bioticslife Cisplus Max 10 nos",
                "price": "₹390.00",
                "available": True,
                "description": "Bone strengthener and fracture healer"
            },
            "cisplus max": {
                "variant_id": "AEBIO1008", 
                "product_title": "Bioticslife Cisplus Max 10 nos",
                "price": "₹390.00",
                "available": True
            },
            "bioticslife duraslim": {
                "variant_id": "AEBIO1009",
                "product_title": "Bioticslife Duraslim 20 nos", 
                "price": "₹560.00",
                "available": True,
                "description": "Weight loss supplement"
            },
            "duraslim": {
                "variant_id": "AEBIO1009",
                "product_title": "Bioticslife Duraslim 20 nos",
                "price": "₹560.00", 
                "available": True
            },
            "bioticslife extranz": {
                "variant_id": "AEBIO1010",
                "product_title": "Bioticslife Extranz 20 nos",
                "price": "₹290.00",
                "available": True,
                "description": "Hair health supplement"
            },
            "extranz": {
                "variant_id": "AEBIO1010",
                "product_title": "Bioticslife Extranz 20 nos", 
                "price": "₹290.00",
                "available": True
            },
            "bioticslife feelcalm": {
                "variant_id": "AEBIO1011",
                "product_title": "Bioticslife Feelcalm 10 nos",
                "price": "₹150.00", 
                "available": True,
                "description": "Natural sleep aid"
            },
            "feelcalm": {
                "variant_id": "AEBIO1011",
                "product_title": "Bioticslife Feelcalm 10 nos",
                "price": "₹150.00",
                "available": True
            },
            "bioticslife greyforte plus": {
                "variant_id": "AEBIO1012",
                "product_title": "Bioticslife Greyforte Plus 20 nos",
                "price": "₹550.00",
                "available": True,
                "description": "Pain relief and neuropathy support"
            },
            "greyforte plus": {
                "variant_id": "AEBIO1012",
                "product_title": "Bioticslife Greyforte Plus 20 nos", 
                "price": "₹550.00",
                "available": True
            },
            "bioticslife greygen": {
                "variant_id": "AEBIO1013",
                "product_title": "Bioticslife Greygen 10 nos",
                "price": "₹220.00",
                "available": True,
                "description": "Brain tonic and cognitive support"
            },
            "greygen": {
                "variant_id": "AEBIO1013",
                "product_title": "Bioticslife Greygen 10 nos",
                "price": "₹220.00",
                "available": True
            },
            "bioticslife hepa ok": {
                "variant_id": "AEBIO1014", 
                "product_title": "Bioticslife Hepa Ok 10 nos",
                "price": "₹135.00",
                "available": True,
                "description": "Liver detox and support"
            },
            "hepa ok": {
                "variant_id": "AEBIO1014",
                "product_title": "Bioticslife Hepa Ok 10 nos",
                "price": "₹135.00",
                "available": True
            },
            "bioticslife jointup2": {
                "variant_id": "AEBIO1015",
                "product_title": "Bioticslife Jointup2 20 nos", 
                "price": "₹840.00",
                "available": True,
                "description": "Joint health and mobility"
            },
            "jointup2": {
                "variant_id": "AEBIO1015",
                "product_title": "Bioticslife Jointup2 20 nos",
                "price": "₹840.00",
                "available": True
            },
            "bioticslife normofem d": {
                "variant_id": "AEBIO1016",
                "product_title": "Bioticslife Normofem D 10 nos",
                "price": "₹280.00",
                "available": True,
                "description": "PCOS and hormonal balance"
            },
            "normofem d": {
                "variant_id": "AEBIO1016",
                "product_title": "Bioticslife Normofem D 10 nos",
                "price": "₹280.00",
                "available": True
            },
            "bioticslife stonaway": {
                "variant_id": "AEBIO1018",
                "product_title": "Bioticslife Stonaway 10nos",
                "price": "₹210.00", 
                "available": True,
                "description": "Kidney stone prevention"
            },
            "stonaway": {
                "variant_id": "AEBIO1018",
                "product_title": "Bioticslife Stonaway 10nos",
                "price": "₹210.00",
                "available": True
            },
            "bioticslife thyrowave": {
                "variant_id": "AEBIO1019",
                "product_title": "Bioticslife Thyrowave 20 nos",
                "price": "₹280.00",
                "available": True,
                "description": "Thyroid support"
            },
            "thyrowave": {
                "variant_id": "AEBIO1019",
                "product_title": "Bioticslife Thyrowave 20 nos",
                "price": "₹280.00", 
                "available": True
            },
            "bioticslife utibio": {
                "variant_id": "AEBIO1020",
                "product_title": "Bioticslife Utibio 10 nos",
                "price": "₹270.00",
                "available": True,
                "description": "Urinary tract health"
            },
            "utibio": {
                "variant_id": "AEBIO1020",
                "product_title": "Bioticslife Utibio 10 nos",
                "price": "₹270.00",
                "available": True
            },
            "bioticslife vericolyte": {
                "variant_id": "AEBIO1021",
                "product_title": "Bioticslife Vericolyte 20 nos",
                "price": "₹570.00",
                "available": True,
                "description": "Varicose veins treatment"
            },
            "vericolyte": {
                "variant_id": "AEBIO1021", 
                "product_title": "Bioticslife Vericolyte 20 nos",
                "price": "₹570.00",
                "available": True
            },
            # Charak Products
            "addyzoa capsule": {
                "variant_id": "AECHK1001",
                "product_title": "Addyzoa Capsule 20 nos",
                "price": "₹220.00",
                "available": True,
                "description": "Male fertility support"
            },
            "addyzoa": {
                "variant_id": "AECHK1001",
                "product_title": "Addyzoa Capsule 20 nos",
                "price": "₹220.00",
                "available": True
            },
            "calcury tablet": {
                "variant_id": "AECHK1002",
                "product_title": "Calcury Tablet 60 nos",
                "price": "₹190.00",
                "available": True,
                "description": "Kidney health support"
            },
            "calcury": {
                "variant_id": "AECHK1002", 
                "product_title": "Calcury Tablet 60 nos",
                "price": "₹190.00",
                "available": True
            },
            "chropaxe tablet": {
                "variant_id": "AECHK1003",
                "product_title": "Chropaxe Tablet 30 nos",
                "price": "₹270.00",
                "available": True,
                "description": "Chronic pain management"
            },
            "chropaxe": {
                "variant_id": "AECHK1003",
                "product_title": "Chropaxe Tablet 30 nos",
                "price": "₹270.00",
                "available": True
            },
            
            # Additional Ayurvedic Medicines from Store Expansion
            "aaragwadham kashaayam tabletg": {
                "variant_id": "AEKST1001",
                "product_title": "Aaragwadham Kashaayam Tabletg 10 nos",
                "price": "₹32.00",
                "available": True
            },
            "abhayarishtam": {
                "variant_id": "AEAA1001",
                "product_title": "Abhayarishtam",
                "price": "₹95.00",
                "available": True
            },
            "addyzoa capsule": {
                "variant_id": "AECHK1001",
                "product_title": "Addyzoa Capsule 20 nos",
                "price": "₹220.00",
                "available": True
            },
            "aimil aswagandha capsule": {
                "variant_id": "AEAIM1004",
                "product_title": "Aimil Aswagandha Capsule 60 nos",
                "price": "₹297.00",
                "available": True
            },
            "aimil garcinia cambogia capsules": {
                "variant_id": "AEAIM1005",
                "product_title": "Aimil Garcinia Cambogia Capsules 60 nos",
                "price": "₹306.00",
                "available": True
            },
            "aimil neem tablet": {
                "variant_id": "AEAIM1027",
                "product_title": "Aimil Neem Tablet",
                "price": "₹118.00",
                "available": True
            },
            "aimil relaxo tablets": {
                "variant_id": "AEAIM1007",
                "product_title": "Aimil Relaxo Tablets 100nos",
                "price": "₹421.00",
                "available": True
            },
            "aimil trima lip tablet": {
                "variant_id": "AEAIM1034",
                "product_title": "Aimil Trima Lip Tablet 60nos",
                "price": "₹399.00",
                "available": True
            },
            "aimil zymnet tablets": {
                "variant_id": "AEAIM1010",
                "product_title": "Aimil Zymnet Tablets",
                "price": "₹465.00",
                "available": True
            },
            "alsarex tablet": {
                "variant_id": "AECHK1029",
                "product_title": "Alsarex Tablet",
                "price": "₹211.00",
                "available": True
            },
            "amlycure d.s. capsule": {
                "variant_id": "AEAIM1011",
                "product_title": "Amlycure D.S. Capsule",
                "price": "₹198.00",
                "available": True
            },
            "amlycure d.s. syrup": {
                "variant_id": "AEAIM1013",
                "product_title": "Amlycure D.S. Syrup",
                "price": "₹166.00",
                "available": True
            },
            "amroid tablets": {
                "variant_id": "AEAIM1014",
                "product_title": "Amroid Tablets",
                "price": "₹360.00",
                "available": True
            },
            "amrutharishtam": {
                "variant_id": "AEAA1002",
                "product_title": "Amrutharishtam",
                "price": "₹100.00",
                "available": True
            },
            "amruthotharam kashaayam tablet": {
                "variant_id": "AEKST1002",
                "product_title": "Amruthotharam Kashaayam Tablet",
                "price": "₹25.00",
                "available": True
            },
            "amycordial forte syrup": {
                "variant_id": "AEAIM1015",
                "product_title": "Amycordial Forte Syrup",
                "price": "₹374.00",
                "available": True
            },
            "amydio forte syrup": {
                "variant_id": "AEAIM1016",
                "product_title": "Amydio Forte Syrup",
                "price": "₹128.00",
                "available": True
            },
            "amypure syrup": {
                "variant_id": "AEAIM1017",
                "product_title": "Amypure Syrup",
                "price": "₹226.00",
                "available": True
            },
            "ashvagandha tablet": {
                "variant_id": "AEAIM1018",
                "product_title": "Ashvagandha Tablet",
                "price": "₹85.00",
                "available": True
            },
            "asokarishtam": {
                "variant_id": "AEAA1003",
                "product_title": "Asokarishtam",
                "price": "₹82.00",
                "available": True
            },
            "aswagandharishta": {
                "variant_id": "AEAA1004",
                "product_title": "Aswagandharishta",
                "price": "₹82.00",
                "available": True
            },
            "aswagandharista liquid": {
                "variant_id": "AEAA1005",
                "product_title": "Aswagandharista Liquid",
                "price": "₹92.00",
                "available": True
            },
            "brahmi ghrita": {
                "variant_id": "AEAA1006",
                "product_title": "Brahmi Ghrita",
                "price": "₹125.00",
                "available": True
            },
            "brahmi vati": {
                "variant_id": "AEAA1007",
                "product_title": "Brahmi Vati",
                "price": "₹45.00",
                "available": True
            },
            "chandanasava": {
                "variant_id": "AEAA1008",
                "product_title": "Chandanasava",
                "price": "₹88.00",
                "available": True
            }
        }
        
        # Alternative medicine suggestions
        self.alternatives: Dict[str, List[str]] = {
            "ashwagandha": ["ashwagandha churna", "ashwagandha tablets", "ashwagandha capsules"],
            "triphala": ["triphala tablets", "triphala churna", "triphala powder"],
            "brahmi": ["brahmi oil", "brahmi tablets", "brahmi powder"],
            "turmeric": ["turmeric powder", "turmeric capsules", "curcumin tablets"]
        }
    
    def normalize_medicine_name(self, medicine_name: str) -> str:
        """Normalize medicine name for mapping lookup"""
        return medicine_name.lower().strip()
    
    def get_variant_id(self, medicine_name: str) -> Optional[int]:
        """Get Shopify variant ID for a medicine"""
        normalized_name = self.normalize_medicine_name(medicine_name)
        mapping = self.medicine_mapping.get(normalized_name)
        
        if mapping and mapping.get("available", False):
            return mapping["variant_id"]
        
        return None
    
    def get_product_info(self, medicine_name: str) -> Dict:
        """Get complete product information for a medicine"""
        normalized_name = self.normalize_medicine_name(medicine_name)
        mapping = self.medicine_mapping.get(normalized_name)
        
        if mapping:
            return {
                "medicine_name": medicine_name,
                "shopify_variant_id": mapping["variant_id"],
                "shopify_product_title": mapping["product_title"],
                "price": mapping.get("price"),
                "is_available": mapping.get("available", False),
                "suggested_alternatives": self.get_alternatives(medicine_name)
            }
        
        return {
            "medicine_name": medicine_name,
            "shopify_variant_id": None,
            "shopify_product_title": None,
            "price": None,
            "is_available": False,
            "suggested_alternatives": self.get_alternatives(medicine_name)
        }
    
    def get_alternatives(self, medicine_name: str) -> List[str]:
        """Get alternative medicine suggestions"""
        normalized_name = self.normalize_medicine_name(medicine_name)
        
        # Find base medicine name (remove common suffixes)
        base_name = normalized_name
        for suffix in [" churna", " tablets", " capsules", " powder", " oil", " syrup", " juice"]:
            if normalized_name.endswith(suffix):
                base_name = normalized_name.replace(suffix, "").strip()
                break
        
        return self.alternatives.get(base_name, [])
    
    def batch_lookup(self, medicine_names: List[str]) -> Dict[str, Dict]:
        """Perform batch lookup for multiple medicines"""
        results = {}
        
        for medicine in medicine_names:
            results[medicine] = self.get_product_info(medicine)
            
        return results
    
    def add_medicine_mapping(self, medicine_name: str, variant_id: int, 
                           product_title: str, price: Optional[str] = None, available: bool = True):
        """Add new medicine mapping (for admin/setup purposes)"""
        normalized_name = self.normalize_medicine_name(medicine_name)
        
        self.medicine_mapping[normalized_name] = {
            "variant_id": variant_id,
            "product_title": product_title,
            "price": price,
            "available": available
        }
        
        logger.info(f"Added mapping: {medicine_name} -> {variant_id}")
    
    def get_all_medicines(self) -> List[Dict]:
        """Get list of all available medicines"""
        medicines = []
        
        for name, info in self.medicine_mapping.items():
            if info.get("available", False):
                medicines.append({
                    "name": name.title(),
                    "variant_id": info["variant_id"],
                    "title": info["product_title"],
                    "price": info.get("price")
                })
        
        return medicines

# Global product mapper instance
product_mapper = ProductMapper()