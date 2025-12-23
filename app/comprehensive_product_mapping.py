"""
Comprehensive Product Mapping System - All Ayureze Healthcare Products
"""

from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

class ProductMapper:
    """Maps all products to Shopify variant IDs"""
    
    def __init__(self):
        self.medicine_mapping: Dict[str, Dict] = {
            "aadarisahacharadi kashayam": {
                "variant_id": "AEKS1002",
                "product_title": "Aadarisahacharadi Kashayam",
                "price": "₹180.00",
                "available": True
            },
            "aaragwadham kashaayam tabletg": {
                "variant_id": "AEKST1001",
                "product_title": "Aaragwadham Kashaayam Tabletg 10 nos",
                "price": "₹32.00",
                "available": True
            },
            "aaragwadhamahaatiktaka ghrutam": {
                "variant_id": "AEGM1001",
                "product_title": "Aaragwadhamahaatiktaka ghrutam",
                "price": "₹205.00",
                "available": True
            },
            "abhayarishtam": {
                "variant_id": "AEAA1001",
                "product_title": "Abhayarishtam",
                "price": "₹95.00",
                "available": True
            },
            "acilans capsule": {
                "variant_id": "AEATR1002",
                "product_title": "Acilans Capsule 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "aclear capsule": {
                "variant_id": "AEATR1001",
                "product_title": "Aclear Capsule 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "aclear topical": {
                "variant_id": "AEATR1019",
                "product_title": "Aclear Topical 20g",
                "price": "₹0.00",
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
            "aimil semento forte granules": {
                "variant_id": "AEAIM1008",
                "product_title": "Aimil Semento Forte Granules",
                "price": "₹2000.00",
                "available": True
            },
            "aimil shilajit gold capsuls": {
                "variant_id": "AEAIM1009",
                "product_title": "Aimil Shilajit Gold Capsuls 20 nos",
                "price": "₹490.00",
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
            "allerkhand choornam": {
                "variant_id": "AECH1001",
                "product_title": "Allerkhand Choornam 50 gm",
                "price": "₹90.00",
                "available": True
            },
            "aloes compound": {
                "variant_id": "AEALR001",
                "product_title": "Aloes Compound",
                "price": "₹0.00",
                "available": True
            },
            "alsarex tablet": {
                "variant_id": "AECHK1029",
                "product_title": "Alsarex Tablet 60 nos",
                "price": "₹211.00",
                "available": True
            },
            "aluritic tab": {
                "variant_id": "AEALR1002",
                "product_title": "Aluritic Tab",
                "price": "₹0.00",
                "available": True
            },
            "amavatari kashayam": {
                "variant_id": "AEKS1001",
                "product_title": "Amavatari Kashayam",
                "price": "₹175.00",
                "available": True
            },
            "amlycure d.s. capsule": {
                "variant_id": "AEAIM1011",
                "product_title": "Amlycure D.S. Capsule 20 nos",
                "price": "₹198.00",
                "available": True
            },
            "amlycure d.s. syrup": {
                "variant_id": "AEAIM1013",
                "product_title": "Amlycure D.S. Syrup 100ml",
                "price": "₹166.00",
                "available": True
            },
            "amree plus": {
                "variant_id": "AEAIM1012",
                "product_title": "Amree Plus",
                "price": "₹164.00",
                "available": True
            },
            "amree plus granules (30sachets)": {
                "variant_id": "AEAIM1001",
                "product_title": "Amree Plus Granules (30sachets)",
                "price": "₹561.00",
                "available": True
            },
            "amrita bhallataka lehyam": {
                "variant_id": "AESG1001",
                "product_title": "Amrita Bhallataka Lehyam 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "amrithotharam kashayam": {
                "variant_id": "AEKS1003",
                "product_title": "Amrithotharam Kashayam",
                "price": "₹150.00",
                "available": True
            },
            "amroid ointment": {
                "variant_id": "AEAIM1002",
                "product_title": "Amroid Ointment 20g",
                "price": "₹126.00",
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
                "product_title": "Amruthotharam Kashaayam Tablet 10 nos",
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
                "product_title": "Amypure Syrup 200ml",
                "price": "₹226.00",
                "available": True
            },
            "amyron syrup": {
                "variant_id": "AEAIM1003",
                "product_title": "Amyron Syrup 200ml",
                "price": "₹185.00",
                "available": True
            },
            "amyron tablets": {
                "variant_id": "AEAIM1018",
                "product_title": "Amyron Tablets",
                "price": "₹198.00",
                "available": True
            },
            "amystop-g capsules": {
                "variant_id": "AEAIM1019",
                "product_title": "Amystop-G Capsules",
                "price": "₹196.00",
                "available": True
            },
            "anu tailam": {
                "variant_id": "AETL1001",
                "product_title": "Anu Tailam 200 ml",
                "price": "₹90.00",
                "available": True
            },
            "aragwadharishtam": {
                "variant_id": "AEAA1003",
                "product_title": "Aragwadharishtam",
                "price": "₹110.00",
                "available": True
            },
            "aravindasavam": {
                "variant_id": "AEAA1004",
                "product_title": "Aravindasavam",
                "price": "₹100.00",
                "available": True
            },
            "arimedadi tailam": {
                "variant_id": "AETL1002",
                "product_title": "Arimedadi Tailam 200 ml",
                "price": "₹160.00",
                "available": True
            },
            "arjin tab": {
                "variant_id": "AEALR1003",
                "product_title": "Arjin Tab",
                "price": "₹0.00",
                "available": True
            },
            "arjunarishtam (partharishtam)": {
                "variant_id": "AEAA1005",
                "product_title": "Arjunarishtam (Partharishtam)",
                "price": "₹110.00",
                "available": True
            },
            "arukaladi tailam": {
                "variant_id": "AETL1003",
                "product_title": "Arukaladi Tailam 200 ml",
                "price": "₹145.00",
                "available": True
            },
            "asanailadi tailam": {
                "variant_id": "AETL1006",
                "product_title": "Asanailadi Tailam 200 ml",
                "price": "₹205.00",
                "available": True
            },
            "asanamanjishtadi kera tailam": {
                "variant_id": "AETL1004",
                "product_title": "Asanamanjishtadi Kera Tailam 200 ml",
                "price": "₹210.00",
                "available": True
            },
            "asanavilwadi kera tailam": {
                "variant_id": "AETL1005",
                "product_title": "Asanavilwadi Kera Tailam 200 ml",
                "price": "₹180.00",
                "available": True
            },
            "asaneladi yamakam": {
                "variant_id": "AETL1007",
                "product_title": "Asaneladi Yamakam 200 ml",
                "price": "₹205.00",
                "available": True
            },
            "ashoka ghrutham": {
                "variant_id": "AEGM1002",
                "product_title": "Ashoka Ghrutham",
                "price": "₹225.00",
                "available": True
            },
            "ashokarishtam": {
                "variant_id": "AEAA1006",
                "product_title": "Ashokarishtam",
                "price": "₹135.00",
                "available": True
            },
            "ashtachoornam": {
                "variant_id": "AECH1002",
                "product_title": "Ashtachoornam 50 gm",
                "price": "₹90.00",
                "available": True
            },
            "ashtavargam kashaayam tablet": {
                "variant_id": "AEKST1003",
                "product_title": "Ashtavargam Kashaayam Tablet 10 nos",
                "price": "₹30.00",
                "available": True
            },
            "ashtavargam kashayam": {
                "variant_id": "AEKS1004",
                "product_title": "Ashtavargam Kashayam",
                "price": "₹160.00",
                "available": True
            },
            "aswagandha choornam": {
                "variant_id": "AECH1003",
                "product_title": "Aswagandha Choornam 50 gm",
                "price": "₹90.00",
                "available": True
            },
            "aswagandharishtam": {
                "variant_id": "AEAA1007",
                "product_title": "Aswagandharishtam",
                "price": "₹200.00",
                "available": True
            },
            "atrisor capsule": {
                "variant_id": "AEATR1003",
                "product_title": "Atrisor Capsule 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "atrisor soap": {
                "variant_id": "AEATR1028",
                "product_title": "Atrisor Soap",
                "price": "₹0.00",
                "available": True
            },
            "atrisor topical": {
                "variant_id": "AEATR1020",
                "product_title": "Atrisor Topical 20g",
                "price": "₹0.00",
                "available": True
            },
            "atrivit capsule": {
                "variant_id": "AEATR1004",
                "product_title": "Atrivit Capsule 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "avipathi choornam": {
                "variant_id": "AECH1004",
                "product_title": "Avipathi Choornam 50 gm",
                "price": "₹80.00",
                "available": True
            },
            "ayapon tab": {
                "variant_id": "AEALR1004",
                "product_title": "Ayapon Tab",
                "price": "₹0.00",
                "available": True
            },
            "ayaskruthi": {
                "variant_id": "AEAA1008",
                "product_title": "Ayaskruthi",
                "price": "₹130.00",
                "available": True
            },
            "bala tailam": {
                "variant_id": "AETL1008",
                "product_title": "Bala Tailam 10 ml",
                "price": "₹65.00",
                "available": True
            },
            "baladhathryadi tailam": {
                "variant_id": "AETL1009",
                "product_title": "Baladhathryadi Tailam 200 ml",
                "price": "₹260.00",
                "available": True
            },
            "balaguloochyadi tailam": {
                "variant_id": "AETL1010",
                "product_title": "Balaguloochyadi Tailam 200 ml",
                "price": "₹185.00",
                "available": True
            },
            "balahatadi kera thailam": {
                "variant_id": "AETL1012",
                "product_title": "Balahatadi Kera Thailam 200 ml",
                "price": "₹185.00",
                "available": True
            },
            "balahatadi tailam": {
                "variant_id": "AETL1011",
                "product_title": "Balahatadi Tailam 200 ml",
                "price": "₹150.00",
                "available": True
            },
            "balarishtam": {
                "variant_id": "AEAA1009",
                "product_title": "Balarishtam",
                "price": "₹130.00",
                "available": True
            },
            "balaswagandhadi tailam": {
                "variant_id": "AETL1013",
                "product_title": "Balaswagandhadi Tailam 200 ml",
                "price": "₹240.00",
                "available": True
            },
            "balatailam 21 avartita softgel capsule": {
                "variant_id": "AESG1002",
                "product_title": "BalaTailam 21 Avartita Softgel Capsule 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "bangshil": {
                "variant_id": "AEALR1005",
                "product_title": "Bangshil",
                "price": "₹0.00",
                "available": True
            },
            "bgr-34 tablets": {
                "variant_id": "AEAIM1020",
                "product_title": "BGR-34 Tablets",
                "price": "₹660.00",
                "available": True
            },
            "bhadradarvadi kashayam": {
                "variant_id": "AEKS1005",
                "product_title": "Bhadradarvadi Kashayam",
                "price": "₹160.00",
                "available": True
            },
            "bhringamalakadi tailam": {
                "variant_id": "AETL1014",
                "product_title": "Bhringamalakadi Tailam 200 ml",
                "price": "₹205.00",
                "available": True
            },
            "bhringarasava": {
                "variant_id": "AEAA1010",
                "product_title": "Bhringarasava",
                "price": "₹165.00",
                "available": True
            },
            "bio flake c3 400": {
                "variant_id": "AEAAX1001",
                "product_title": "Bio Flake C3 400 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "bioticslife arthrofree": {
                "variant_id": "AEBIO1001",
                "product_title": "Bioticslife Arthrofree 10 nos",
                "price": "₹195.00",
                "available": True
            },
            "bioticslife ayushcal": {
                "variant_id": "AEBIO1002",
                "product_title": "Bioticslife Ayushcal 10 nos",
                "price": "₹135.00",
                "available": True
            },
            "bioticslife biomucos": {
                "variant_id": "AEBIO1003",
                "product_title": "Bioticslife Biomucos 10 nos",
                "price": "₹364.00",
                "available": True
            },
            "bioticslife biomucos n syrup": {
                "variant_id": "AEBIO1004",
                "product_title": "Bioticslife Biomucos N Syrup 100ml",
                "price": "₹0.00",
                "available": True
            },
            "bioticslife bonboom": {
                "variant_id": "AEBIO1005",
                "product_title": "Bioticslife Bonboom 10nos",
                "price": "₹0.00",
                "available": True
            },
            "bioticslife bromtryp forte": {
                "variant_id": "AEBIO1006",
                "product_title": "Bioticslife Bromtryp Forte 10 nos",
                "price": "₹400.00",
                "available": True
            },
            "bioticslife cameomax": {
                "variant_id": "AEBIO1007",
                "product_title": "Bioticslife Cameomax 10 nos",
                "price": "₹470.00",
                "available": True
            },
            "bioticslife cisplus max": {
                "variant_id": "AEBIO1008",
                "product_title": "Bioticslife Cisplus Max 10 nos",
                "price": "₹390.00",
                "available": True
            },
            "bioticslife duraslim": {
                "variant_id": "AEBIO1009",
                "product_title": "Bioticslife Duraslim 20 nos",
                "price": "₹560.00",
                "available": True
            },
            "bioticslife extranz": {
                "variant_id": "AEBIO1010",
                "product_title": "Bioticslife Extranz 20 nos",
                "price": "₹290.00",
                "available": True
            },
            "bioticslife feelcalm": {
                "variant_id": "AEBIO1011",
                "product_title": "Bioticslife Feelcalm 10 nos",
                "price": "₹150.00",
                "available": True
            },
            "bioticslife greyforte plus": {
                "variant_id": "AEBIO1012",
                "product_title": "Bioticslife Greyforte Plus 20 nos",
                "price": "₹550.00",
                "available": True
            },
            "bioticslife greygen": {
                "variant_id": "AEBIO1013",
                "product_title": "Bioticslife Greygen 10 nos",
                "price": "₹220.00",
                "available": True
            },
            "bioticslife hepa ok": {
                "variant_id": "AEBIO1014",
                "product_title": "Bioticslife Hepa Ok 10 nos",
                "price": "₹135.00",
                "available": True
            },
            "bioticslife jointup2": {
                "variant_id": "AEBIO1015",
                "product_title": "Bioticslife Jointup2 20 nos",
                "price": "₹840.00",
                "available": True
            },
            "bioticslife nomolines": {
                "variant_id": "AEBIO1017",
                "product_title": "Bioticslife Nomolines 60g",
                "price": "₹330.00",
                "available": True
            },
            "bioticslife normofem d": {
                "variant_id": "AEBIO1016",
                "product_title": "Bioticslife Normofem D 10 nos",
                "price": "₹280.00",
                "available": True
            },
            "bioticslife stonaway": {
                "variant_id": "AEBIO1018",
                "product_title": "Bioticslife Stonaway 10nos",
                "price": "₹210.00",
                "available": True
            },
            "bioticslife thyrowave": {
                "variant_id": "AEBIO1019",
                "product_title": "Bioticslife Thyrowave 20 nos",
                "price": "₹280.00",
                "available": True
            },
            "bioticslife utibio": {
                "variant_id": "AEBIO1020",
                "product_title": "Bioticslife Utibio 10 nos",
                "price": "₹270.00",
                "available": True
            },
            "bioticslife vericolyte": {
                "variant_id": "AEBIO1021",
                "product_title": "Bioticslife Vericolyte 20 nos",
                "price": "₹570.00",
                "available": True
            },
            "bioticslife vericolyte gel": {
                "variant_id": "AEBIO1022",
                "product_title": "Bioticslife Vericolyte Gel 30g",
                "price": "₹170.00",
                "available": True
            },
            "biotis rb net syrup": {
                "variant_id": "AEBIS1001",
                "product_title": "Biotis Rb Net Syrup",
                "price": "₹0.00",
                "available": True
            },
            "boniheal suspension": {
                "variant_id": "AEAIM1021",
                "product_title": "Boniheal Suspension",
                "price": "₹481.00",
                "available": True
,
            "brahmee ghrutam": {
                "variant_id": "AEGM1004",
                "product_title": "Brahmee ghrutam",
                "price": "₹225.00",
                "available": True
            },
            "brahmighritam saptavarti": {
                "variant_id": "AESG1003",
                "product_title": "Brahmighritam Saptavarti 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "brihath danthapala tailam": {
                "variant_id": "AETL1015",
                "product_title": "Brihath Danthapala Tailam 100 ml",
                "price": "₹150.00",
                "available": True
            },
            "bronchosap granules": {
                "variant_id": "AECH1005",
                "product_title": "Bronchosap Granules 100 gm",
                "price": "₹120.00",
                "available": True
            },
            "bruhathyadi kashayam": {
                "variant_id": "AEKS1006",
                "product_title": "Bruhathyadi Kashayam",
                "price": "₹150.00",
                "available": True
            },
            "calcury tablet": {
                "variant_id": "AECHK1002",
                "product_title": "Calcury Tablet 60 nos",
                "price": "₹190.00",
                "available": True
            },
            "cephagraine nasal drops": {
                "variant_id": "AECHK1025",
                "product_title": "Cephagraine Nasal Drops 15 ml",
                "price": "₹73.00",
                "available": True
            },
            "cephagraine tablet": {
                "variant_id": "AECHK1024",
                "product_title": "Cephagraine Tablet 60 nos",
                "price": "₹203.00",
                "available": True
            },
            "chandanadi tailam": {
                "variant_id": "AETL1017",
                "product_title": "Chandanadi Tailam 200 ml",
                "price": "₹340.00",
                "available": True
            },
            "chandanasavam": {
                "variant_id": "AEAA1011",
                "product_title": "Chandanasavam",
                "price": "₹90.00",
                "available": True
            },
            "chemparuthyadi kera tailam": {
                "variant_id": "AETL1016",
                "product_title": "Chemparuthyadi Kera Tailam 200 ml",
                "price": "₹150.00",
                "available": True
            },
            "chinchadi thailam": {
                "variant_id": "AETL1018",
                "product_title": "Chinchadi Thailam 200 ml",
                "price": "₹200.00",
                "available": True
            },
            "chiruvilwaadi kashaayam tablet": {
                "variant_id": "AEKST1004",
                "product_title": "Chiruvilwaadi Kashaayam Tablet 10 nos",
                "price": "₹35.00",
                "available": True
            },
            "chiruvilwadi kashayam": {
                "variant_id": "AEKS1007",
                "product_title": "Chiruvilwadi Kashayam",
                "price": "₹200.00",
                "available": True
            },
            "chropaxe tablet": {
                "variant_id": "AECHK1003",
                "product_title": "Chropaxe Tablet 30 nos",
                "price": "₹270.00",
                "available": True
            },
            "curc newten": {
                "variant_id": "AEAAX1028",
                "product_title": "Curc Newten 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "cystolib nutra": {
                "variant_id": "AECHK1026",
                "product_title": "Cystolib Nutra 30 nos",
                "price": "₹280.00",
                "available": True
            },
            "daadeemaadi ghrutam": {
                "variant_id": "AEGM1003",
                "product_title": "Daadeemaadi ghrutam",
                "price": "₹225.00",
                "available": True
            },
            "dadimashtaka churna": {
                "variant_id": "AECH1006",
                "product_title": "Dadimashtaka Churna 50 gm",
                "price": "₹70.00",
                "available": True
            },
            "danwantararishtam": {
                "variant_id": "AEAA1014",
                "product_title": "Danwantararishtam",
                "price": "₹115.00",
                "available": True
            },
            "dasamoolajeerakarishtam": {
                "variant_id": "AEAA1012",
                "product_title": "Dasamoolajeerakarishtam",
                "price": "₹135.00",
                "available": True
            },
            "dasamoolakatuthrayam kashayam": {
                "variant_id": "AEKS1008",
                "product_title": "Dasamoolakatuthrayam Kashayam",
                "price": "₹180.00",
                "available": True
            },
            "dasamoolam kashayam": {
                "variant_id": "AEKS1009",
                "product_title": "Dasamoolam Kashayam",
                "price": "₹160.00",
                "available": True
            },
            "dasamoolarishtam": {
                "variant_id": "AEAA1013",
                "product_title": "Dasamoolarishtam",
                "price": "₹120.00",
                "available": True
            },
            "dashamoola katuthrayam kashaayam tablet": {
                "variant_id": "AEKST1005",
                "product_title": "Dashamoola katuthrayam Kashaayam Tablet 10 nos",
                "price": "₹40.00",
                "available": True
            },
            "dekofcyn tab": {
                "variant_id": "AEALR1006",
                "product_title": "Dekofcyn Tab",
                "price": "₹0.00",
                "available": True
            },
            "dhanadanayanaadi kashaayam tablet": {
                "variant_id": "AEKST1006",
                "product_title": "Dhanadanayanaadi Kashaayam Tablet 10 nos",
                "price": "₹30.00",
                "available": True
            },
            "dhanadanayanadi kashayam": {
                "variant_id": "AEKS1010",
                "product_title": "Dhanadanayanadi Kashayam",
                "price": "₹200.00",
                "available": True
            },
            "dhanvantaram 101 avartita": {
                "variant_id": "AESG1004",
                "product_title": "Dhanvantaram 101 Avartita 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "dhanvantaram mezhukupakam": {
                "variant_id": "AETL1019",
                "product_title": "Dhanvantaram Mezhukupakam 200 ml",
                "price": "₹250.00",
                "available": True
            },
            "dhanwantaram kuzhampu": {
                "variant_id": "AETL1023",
                "product_title": "Dhanwantaram Kuzhampu 200 ml",
                "price": "₹180.00",
                "available": True
            },
            "dhanwantharam 101": {
                "variant_id": "AETL1024",
                "product_title": "Dhanwantharam 101 10 ml",
                "price": "₹145.00",
                "available": True
            },
            "dhanwantharam 3 aavarthi": {
                "variant_id": "AETL1021",
                "product_title": "Dhanwantharam 3 Aavarthi 100 ml",
                "price": "₹195.00",
                "available": True
            },
            "dhanwantharam 41 aavarthi": {
                "variant_id": "AETL1022",
                "product_title": "Dhanwantharam 41 Aavarthi 10 ml",
                "price": "₹100.00",
                "available": True
            },
            "dhanwantharam kashaayam tablet": {
                "variant_id": "AEKST1007",
                "product_title": "Dhanwantharam Kashaayam Tablet 10 nos",
                "price": "₹40.00",
                "available": True
            },
            "dhanwantharam kashayam": {
                "variant_id": "AEKS1011",
                "product_title": "Dhanwantharam Kashayam",
                "price": "₹195.00",
                "available": True
            },
            "dhatryarishtam (nellikasavam)": {
                "variant_id": "AEAA1015",
                "product_title": "Dhatryarishtam (Nellikasavam)",
                "price": "₹170.00",
                "available": True
            },
            "dhurdhurapatradi kera tailam": {
                "variant_id": "AETL1025",
                "product_title": "Dhurdhurapatradi Kera Tailam 200 ml",
                "price": "₹200.00",
                "available": True
            },
            "dinesavalyadi kera tailam": {
                "variant_id": "AETL1026",
                "product_title": "Dinesavalyadi Kera Tailam 200 ml",
                "price": "₹200.00",
                "available": True
            },
            "dinesavalyadi kuzhampu": {
                "variant_id": "AETL1027",
                "product_title": "Dinesavalyadi Kuzhampu 200 ml",
                "price": "₹155.00",
                "available": True
            },
            "draakshaadi kashaayam tablet": {
                "variant_id": "AEKST1008",
                "product_title": "Draakshaadi Kashaayam Tablet 10 nos",
                "price": "₹40.00",
                "available": True
            },
            "drakshadi kashayam": {
                "variant_id": "AEKS1012",
                "product_title": "Drakshadi Kashayam",
                "price": "₹200.00",
                "available": True
            },
            "draksharishtam": {
                "variant_id": "AEAA1016",
                "product_title": "Draksharishtam",
                "price": "₹140.00",
                "available": True
            },
            "duralabarishtam": {
                "variant_id": "AEAA1017",
                "product_title": "Duralabarishtam",
                "price": "₹110.00",
                "available": True
            },
            "durvadi kera thailam": {
                "variant_id": "AETL1028",
                "product_title": "Durvadi Kera Thailam 200 ml",
                "price": "₹190.00",
                "available": True
            },
            "dusparsakadi kashayam": {
                "variant_id": "AEKS1013",
                "product_title": "Dusparsakadi Kashayam",
                "price": "₹200.00",
                "available": True
            },
            "eladi choornam": {
                "variant_id": "AECH1007",
                "product_title": "Eladi Choornam 50 gm",
                "price": "₹100.00",
                "available": True
            },
            "eladi kera tailam": {
                "variant_id": "AETL1029",
                "product_title": "Eladi Kera Tailam 200 ml",
                "price": "₹210.00",
                "available": True
            },
            "elakanadi kashayam": {
                "variant_id": "AEKS1014",
                "product_title": "Elakanadi Kashayam",
                "price": "₹170.00",
                "available": True
            },
            "endotone capsules": {
                "variant_id": "AECHK1004",
                "product_title": "Endotone Capsules 20 nos",
                "price": "₹188.00",
                "available": True
            },
            "enzorux plus": {
                "variant_id": "AEAAX1002",
                "product_title": "Enzorux Plus 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "evanova capsule": {
                "variant_id": "AECHK1005",
                "product_title": "Evanova Capsule 20 nos",
                "price": "₹173.00",
                "available": True
            },
            "evenshade cream": {
                "variant_id": "AECHK1030",
                "product_title": "Evenshade Cream 30 g",
                "price": "₹139.00",
                "available": True
            },
            "exoskin cream": {
                "variant_id": "AEAIM1022",
                "product_title": "Exoskin Cream",
                "price": "₹298.00",
                "available": True
            },
            "extrammune tablet (immunity booster)": {
                "variant_id": "AECHK1006",
                "product_title": "Extrammune Tablet (Immunity Booster) 30 nos",
                "price": "₹130.00",
                "available": True
            },
            "femicalm capsule": {
                "variant_id": "AEATR1005",
                "product_title": "Femicalm Capsule 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "femiplex gel": {
                "variant_id": "AECHK1007",
                "product_title": "Femiplex Gel 30 g",
                "price": "₹99.00",
                "available": True
            },
            "fibrohep": {
                "variant_id": "AEAAX1003",
                "product_title": "Fibrohep 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "fortege tab": {
                "variant_id": "AEALR1007",
                "product_title": "Fortege Tab",
                "price": "₹0.00",
                "available": True
            },
            "g32 tab": {
                "variant_id": "AEALR1008",
                "product_title": "G32 Tab",
                "price": "₹0.00",
                "available": True
            },
            "gandha tailam softgel capsule": {
                "variant_id": "AESG1005",
                "product_title": "Gandha Tailam Softgel Capsule 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "gandharavahastadi taila 21 avartita": {
                "variant_id": "AESG1006",
                "product_title": "Gandharavahastadi Taila 21 Avartita 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "gandharvahastadi eranda tailam": {
                "variant_id": "AETL1030",
                "product_title": "Gandharvahastadi Eranda Tailam 50 ml",
                "price": "₹50.00",
                "available": True
            },
            "gandharvahasthadi eranada tailam": {
                "variant_id": "AETL1031",
                "product_title": "Gandharvahasthadi Eranada Tailam 200 ml",
                "price": "₹140.00",
                "available": True
            },
            "gandharvahasthadi kashayam": {
                "variant_id": "AEKS1015",
                "product_title": "Gandharvahasthadi Kashayam",
                "price": "₹150.00",
                "available": True
            },
            "gandharwahasthaadi kashaayam tablet": {
                "variant_id": "AEKST1009",
                "product_title": "Gandharwahasthaadi Kashaayam Tablet 10 nos",
                "price": "₹30.00",
                "available": True
            },
            "glukostat capsule": {
                "variant_id": "AEATR1006",
                "product_title": "Glukostat Capsule 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "gokshura choornam": {
                "variant_id": "AECH1008",
                "product_title": "Gokshura Choornam 50 gm",
                "price": "₹90.00",
                "available": True
            },
            "grey smart dine": {
                "variant_id": "AEAAX1005",
                "product_title": "Grey Smart Dine 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "grey smart md": {
                "variant_id": "AEAAX1004",
                "product_title": "Grey Smart MD 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "grey smart pn": {
                "variant_id": "AEAAX1006",
                "product_title": "Grey Smart PN 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "guggulu panchapala choornam": {
                "variant_id": "AECH1009",
                "product_title": "Guggulu Panchapala Choornam 50 gm",
                "price": "₹100.00",
                "available": True
            },
            "guggulu tiktaka ghritham saptavarti": {
                "variant_id": "AESG1007",
                "product_title": "Guggulu Tiktaka Ghritham Saptavarti 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "gulgulasavam": {
                "variant_id": "AEAA1018",
                "product_title": "Gulgulasavam",
                "price": "₹150.00",
                "available": True
            },
            "gulgulu thikthakam kashaayam tablet": {
                "variant_id": "AEKST1010",
                "product_title": "Gulgulu thikthakam Kashaayam Tablet 10 nos",
                "price": "₹50.00",
                "available": True
            },
            "gulguluthikthakam kashayam": {
                "variant_id": "AEKS1016",
                "product_title": "Gulguluthikthakam Kashayam",
                "price": "₹240.00",
                "available": True
            },
            "gulgulutiktaka ghrutam": {
                "variant_id": "AEGM1005",
                "product_title": "Gulgulutiktaka ghrutam",
                "price": "₹310.00",
                "available": True
            },
            "guloochyaadi kashaayam tablet": {
                "variant_id": "AEKST1011",
                "product_title": "Guloochyaadi Kashaayam Tablet 10 nos",
                "price": "₹45.00",
                "available": True
            },
            "guloochyadi kashayam": {
                "variant_id": "AEKS1017",
                "product_title": "Guloochyadi Kashayam",
                "price": "₹210.00",
                "available": True
            },
            "gum tone gel": {
                "variant_id": "AECHK1008",
                "product_title": "Gum Tone Gel 50 g",
                "price": "₹88.00",
                "available": True
            },
            "haridrakhandam choornam": {
                "variant_id": "AECH1010",
                "product_title": "Haridrakhandam Choornam 50 gm",
                "price": "₹80.00",
                "available": True
            },
            "hinguthriguna tailam": {
                "variant_id": "AETL1032",
                "product_title": "Hinguthriguna Tailam 200 ml",
                "price": "₹270.00",
                "available": True
            },
            "hinguvachadi choornam": {
                "variant_id": "AECH1011",
                "product_title": "Hinguvachadi Choornam 50 gm",
                "price": "₹85.00",
                "available": True
            },
            "hyponidd tablet": {
                "variant_id": "AECHK1010",
                "product_title": "Hyponidd Tablet 30 nos",
                "price": "₹140.00",
                "available": True
            },
            "igealt 16b sachets": {
                "variant_id": "AEAAX1021",
                "product_title": "IGEALT 16b Sachets",
                "price": "₹396.00",
                "available": True
            },
            "indukaanta ghrutam": {
                "variant_id": "AEGM1006",
                "product_title": "Indukaanta ghrutam",
                "price": "₹250.00",
                "available": True
            },
            "indukaantham kashaayam tablet": {
                "variant_id": "AEKST1012",
                "product_title": "Indukaantham Kashaayam Tablet 10 nos",
                "price": "₹35.00",
                "available": True
            },
            "indukanta ghrita saptavartita": {
                "variant_id": "AESG1008",
                "product_title": "Indukanta Ghrita Saptavartita 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "indukantham kashayam": {
                "variant_id": "AEKS1018",
                "product_title": "Indukantham Kashayam",
                "price": "₹150.00",
                "available": True
            },
            "jaatiaadi ghrutam": {
                "variant_id": "AEGM1007",
                "product_title": "Jaatiaadi ghrutam 50g",
                "price": "₹80.00",
                "available": True
            },
            "jatamayadi choornam": {
                "variant_id": "AECH1012",
                "product_title": "Jatamayadi Choornam 50 gm",
                "price": "₹70.00",
                "available": True
            },
            "jathyadi kera tailam": {
                "variant_id": "AETL1033",
                "product_title": "Jathyadi Kera Tailam 200 ml",
                "price": "₹180.00",
                "available": True
            },
            "jeerakarishtam": {
                "variant_id": "AEAA1019",
                "product_title": "Jeerakarishtam",
                "price": "₹150.00",
                "available": True
            },
            "jeevantyadi ghritam saptavarti": {
                "variant_id": "AESG1009",
                "product_title": "Jeevantyadi Ghritam Saptavarti 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "jufex forte syrup": {
                "variant_id": "AEAIM1023",
                "product_title": "Jufex Forte Syrup 100ml",
                "price": "₹158.00",
                "available": True
            },
            "jyotishmati tailam": {
                "variant_id": "AESG1010",
                "product_title": "Jyotishmati Tailam 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "k.g.tone forte syrup": {
                "variant_id": "AEAIM1024",
                "product_title": "K.G.Tone Forte Syrup 100ml",
                "price": "₹143.00",
                "available": True
            },
            "kalasakadi kashayam": {
                "variant_id": "AEKS1019",
                "product_title": "Kalasakadi Kashayam",
                "price": "₹140.00",
                "available": True
            },
            "kalyanaka ghrutam": {
                "variant_id": "AEGM1008",
                "product_title": "Kalyanaka ghrutam",
                "price": "₹230.00",
                "available": True
            },
            "kanakasavam": {
                "variant_id": "AEAA1020",
                "product_title": "Kanakasavam",
                "price": "₹95.00",
                "available": True
            },
            "karkidaka kanji (oushada kanji kit)": {
                "variant_id": "AECH1013",
                "product_title": "Karkidaka Kanji (Oushada Kanji Kit)",
                "price": "₹230.00",
                "available": True
            },
            "karpasasthyadi tailam": {
                "variant_id": "AETL1034",
                "product_title": "Karpasasthyadi Tailam 200 ml",
                "price": "₹195.00",
                "available": True
            },
            "karpooradi choornam": {
                "variant_id": "AECH1014",
                "product_title": "Karpooradi Choornam 50 gm",
                "price": "₹80.00",
                "available": True
            },
            "karpuradi tailam": {
                "variant_id": "AETL1035",
                "product_title": "Karpuradi Tailam 200 ml",
                "price": "₹160.00",
                "available": True
            },
            "katakakhadiradi kashayam": {
                "variant_id": "AEKS1046",
                "product_title": "Katakakhadiradi Kashayam",
                "price": "₹130.00",
                "available": True
            },
            "kayathirumeni tailam": {
                "variant_id": "AETL1036",
                "product_title": "Kayathirumeni Tailam 200 ml",
                "price": "₹200.00",
                "available": True
            },
            "kera tailam – virgin coconut oil": {
                "variant_id": "AESG1011",
                "product_title": "Kera Tailam – Virgin Coconut Oil 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "khadirarishtam": {
                "variant_id": "AEAA1021",
                "product_title": "Khadirarishtam",
                "price": "₹135.00",
                "available": True
            },
            "kineaz balm": {
                "variant_id": "AEATR1021",
                "product_title": "Kineaz BALM 20g",
                "price": "₹0.00",
                "available": True
            },
            "kineaz capsule": {
                "variant_id": "AEATR1007",
                "product_title": "Kineaz Capsule 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "kofol ayurvedic sip – instant kadha": {
                "variant_id": "AECHK1011",
                "product_title": "Kofol Ayurvedic Sip – Instant Kadha",
                "price": "₹100.00",
                "available": True
            },
            "kofol immunity tablets (60 tab)": {
                "variant_id": "AECHK1013",
                "product_title": "KOFOL Immunity Tablets (60 Tab)",
                "price": "₹220.00",
                "available": True
            },
            "kofol roll on": {
                "variant_id": "AECHK1012",
                "product_title": "Kofol Roll On 10 ml",
                "price": "₹60.00",
                "available": True
            },
            "kofol rub 20.5 g": {
                "variant_id": "AECHK1014",
                "product_title": "Kofol Rub 20.5 g",
                "price": "₹63.00",
                "available": True
            },
            "kolakulathadi choornam": {
                "variant_id": "AECH1015",
                "product_title": "Kolakulathadi Choornam 100 gm",
                "price": "₹90.00",
                "available": True
            },
            "kottamchukkadi choornam": {
                "variant_id": "AECH1016",
                "product_title": "Kottamchukkadi Choornam 100 gm",
                "price": "₹100.00",
                "available": True
            },
            "kottamchukkadi tailam": {
                "variant_id": "AETL1037",
                "product_title": "Kottamchukkadi Tailam 200 ml",
                "price": "₹150.00",
                "available": True
            },
            "ksharatailam -": {
                "variant_id": "AETL1038",
                "product_title": "Ksharatailam - 10 ml",
                "price": "₹40.00",
                "available": True
            },
            "ksheerabala 101 avarti": {
                "variant_id": "AESG1012",
                "product_title": "Ksheerabala 101 Avarti 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "kshirabala 101": {
                "variant_id": "AETL1039",
                "product_title": "Kshirabala 101",
                "price": "₹125.00",
                "available": True
            },
            "kshirabala 21 -": {
                "variant_id": "AETL1040",
                "product_title": "Kshirabala 21 - 50 ml",
                "price": "₹205.00",
                "available": True
            },
            "kshirabala 7 -": {
                "variant_id": "AETL1041",
                "product_title": "Kshirabala 7 - 50 ml",
                "price": "₹140.00",
                "available": True
            },
            "kumaryasavam": {
                "variant_id": "AEAA1022",
                "product_title": "Kumaryasavam",
                "price": "₹120.00",
                "available": True
            },
            "kuntalakantitailam": {
                "variant_id": "AETL1042",
                "product_title": "Kuntalakantitailam 200 ml",
                "price": "₹255.00",
                "available": True
            },
            "kutajarishtam": {
                "variant_id": "AEAA1023",
                "product_title": "Kutajarishtam",
                "price": "₹110.00",
                "available": True
            },
            "lakshadi kera tailam": {
                "variant_id": "AETL1043",
                "product_title": "Lakshadi Kera Tailam 200 ml",
                "price": "₹190.00",
                "available": True
            },
            "lakshamanarishtam": {
                "variant_id": "AEAA1024",
                "product_title": "Lakshamanarishtam",
                "price": "₹120.00",
                "available": True
            },
            "lasoonairandadi kashayam": {
                "variant_id": "AEKS1020",
                "product_title": "Lasoonairandadi Kashayam",
                "price": "₹155.00",
                "available": True
            },
            "lasuna tailam - garlic oil": {
                "variant_id": "AESG1013",
                "product_title": "Lasuna Tailam - Garlic Oil 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "leptaden tab": {
                "variant_id": "AEALR1009",
                "product_title": "Leptaden Tab",
                "price": "₹0.00",
                "available": True
            },
            "livomyn tablet": {
                "variant_id": "AECHK1015",
                "product_title": "Livomyn Tablet 30 nos",
                "price": "₹132.00",
                "available": True
            },
            "lodhrasavam": {
                "variant_id": "AEAA1025",
                "product_title": "Lodhrasavam",
                "price": "₹120.00",
                "available": True
            },
            "lohasavam": {
                "variant_id": "AEAA1026",
                "product_title": "Lohasavam",
                "price": "₹110.00",
                "available": True
            },
            "lomasathana tailam": {
                "variant_id": "AETL1044",
                "product_title": "Lomasathana Tailam 25 ml",
                "price": "₹150.00",
                "available": True
            },
            "lukoskin combo- ointment 40gm + oral liquid": {
                "variant_id": "AEAIM1025",
                "product_title": "Lukoskin Combo- Ointment 40gm + Oral Liquid 100ml",
                "price": "₹935.00",
                "available": True
            },
            "m-ceaz capsule": {
                "variant_id": "AEATR1008",
                "product_title": "M-ceaz Capsule 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "m2 tone forte syrup": {
                "variant_id": "AECHK1017",
                "product_title": "M2 Tone Forte Syrup 200 ml",
                "price": "₹166.00",
                "available": True
            },
            "m2 tone tablet": {
                "variant_id": "AECHK1016",
                "product_title": "M2 Tone Tablet 30 nos",
                "price": "₹197.00",
                "available": True
            },
            "madhuyashtyadi tailam": {
                "variant_id": "AETL1046",
                "product_title": "Madhuyashtyadi Tailam 200 ml",
                "price": "₹240.00",
                "available": True
            },
            "mahaamanjjishtaadi kashaayam tablet": {
                "variant_id": "AEKST1013",
                "product_title": "Mahaamanjjishtaadi Kashaayam Tablet 10 nos",
                "price": "₹40.00",
                "available": True
            },
            "mahaaraasnaadi ghrutam": {
                "variant_id": "AEGM1009",
                "product_title": "Mahaaraasnaadi ghrutam",
                "price": "₹225.00",
                "available": True
            },
            "mahaaraasnaadi kashaayam tablet": {
                "variant_id": "AEKST1014",
                "product_title": "Mahaaraasnaadi Kashaayam Tablet 10 nos",
                "price": "₹55.00",
                "available": True
            },
            "mahaasneham": {
                "variant_id": "AEGM1010",
                "product_title": "Mahaasneham",
                "price": "₹250.00",
                "available": True
            },
            "mahaathikthakam kashaayam tablet": {
                "variant_id": "AEKST1015",
                "product_title": "Mahaathikthakam Kashaayam Tablet 10 nos",
                "price": "₹55.00",
                "available": True
            },
            "mahaatiktakaghrutam": {
                "variant_id": "AEGM1011",
                "product_title": "Mahaatiktakaghrutam",
                "price": "₹265.00",
                "available": True
            },
            "miniscar cream": {
                "variant_id": "AECHK1027",
                "product_title": "Miniscar Cream 30 g",
                "price": "₹125.00",
                "available": True
            },
            "mishrakasneham": {
                "variant_id": "AEGM1012",
                "product_title": "Mishrakasneham 50g",
                "price": "₹85.00",
                "available": True
            },
            "moish moisturizer": {
                "variant_id": "AEATR1022",
                "product_title": "Moish Moisturizer",
                "price": "₹0.00",
                "available": True
            },
            "motilact capsule": {
                "variant_id": "AEATR1009",
                "product_title": "Motilact Capsule 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "muscalt forte tablet": {
                "variant_id": "AEAIM1026",
                "product_title": "Muscalt Forte Tablet",
                "price": "₹180.00",
                "available": True
            },
            "naarasimharasaayanam": {
                "variant_id": "AEGM1013",
                "product_title": "Naarasimharasaayanam",
                "price": "₹155.00",
                "available": True
            },
            "neeri kft syrup sugarfree": {
                "variant_id": "AEAIM1029",
                "product_title": "Neeri KFT Syrup Sugarfree 200ml",
                "price": "₹625.00",
                "available": True
            },
            "neeri syrup": {
                "variant_id": "AEAIM1028",
                "product_title": "Neeri Syrup 100ml",
                "price": "₹164.00",
                "available": True
            },
            "neeri tablet": {
                "variant_id": "AEAIM1030",
                "product_title": "Neeri Tablet",
                "price": "₹206.00",
                "available": True
            },
            "neo tablet": {
                "variant_id": "AECLK1017",
                "product_title": "Neo Tablet 75 nos",
                "price": "₹155.00",
                "available": True
            },
            "numbflux oinment": {
                "variant_id": "AEAAX1007",
                "product_title": "Numbflux Oinment",
                "price": "₹0.00",
                "available": True
            },
            "obenyl tablet": {
                "variant_id": "AECLK1018",
                "product_title": "Obenyl Tablet 30 nos",
                "price": "₹97.00",
                "available": True
            },
            "obloz capsule": {
                "variant_id": "AEATR1010",
                "product_title": "Obloz Capsule 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "ojus tablet": {
                "variant_id": "AECHK1028",
                "product_title": "Ojus Tablet 30 nos",
                "price": "₹114.00",
                "available": True
            },
            "ostolief tablet": {
                "variant_id": "AECHK1019",
                "product_title": "Ostolief Tablet 30 nos",
                "price": "₹152.00",
                "available": True
            },
            "ostygen capsule": {
                "variant_id": "AEATR1011",
                "product_title": "Ostygen Capsule 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "panchagavya ghrutam": {
                "variant_id": "AEGM1014",
                "product_title": "Panchagavya ghrutam",
                "price": "₹225.00",
                "available": True
            },
            "pathyaapaada ghrutam": {
                "variant_id": "AEGM1015",
                "product_title": "Pathyaapaada Ghrutam",
                "price": "₹285.00",
                "available": True
            },
            "pigmento ointment": {
                "variant_id": "AECHK1020",
                "product_title": "Pigmento Ointment 50 g",
                "price": "₹158.00",
                "available": True
            },
            "pigmento tablet": {
                "variant_id": "AECHK1018",
                "product_title": "Pigmento Tablet 60 nos",
                "price": "₹252.00",
                "available": True
            },
            "plumotreatin": {
                "variant_id": "AEAAX1008",
                "product_title": "Plumotreatin 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "prosteez tablet": {
                "variant_id": "AECHK1021",
                "product_title": "Prosteez Tablet 20 nos",
                "price": "₹163.00",
                "available": True
            },
            "prunilol capsule": {
                "variant_id": "AEATR1012",
                "product_title": "Prunilol Capsule 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "prunilol topical": {
                "variant_id": "AEATR1023",
                "product_title": "Prunilol Topical 20g",
                "price": "₹0.00",
                "available": True
            },
            "pulvolax granules": {
                "variant_id": "AEAIM1031",
                "product_title": "Pulvolax Granules 100g",
                "price": "₹206.00",
                "available": True
            },
            "purodil gel": {
                "variant_id": "AEAIM1032",
                "product_title": "Purodil Gel",
                "price": "₹199.00",
                "available": True
            },
            "purodil tablets": {
                "variant_id": "AEAIM1033",
                "product_title": "Purodil Tablets",
                "price": "₹220.00",
                "available": True
            },
            "r.compound tab": {
                "variant_id": "AEALR1010",
                "product_title": "R.Compound Tab",
                "price": "₹0.00",
                "available": True
            },
            "raasnaadi ghrutam": {
                "variant_id": "AEGM1016",
                "product_title": "Raasnaadi ghrutam",
                "price": "₹305.00",
                "available": True
            },
            "retreve capsule": {
                "variant_id": "AEATR1013",
                "product_title": "Retreve Capsule 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "rhinorm capsule": {
                "variant_id": "AEATR1014",
                "product_title": "Rhinorm Capsule 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "rilanx capsule": {
                "variant_id": "AEATR1015",
                "product_title": "Rilanx Capsule 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "ruxo newten": {
                "variant_id": "AEAAX1009",
                "product_title": "Ruxo Newten 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "saaraswata ghrutam": {
                "variant_id": "AEGM1017",
                "product_title": "Saaraswata ghrutam",
                "price": "₹225.00",
                "available": True
            },
            "scurfol topical": {
                "variant_id": "AEATR1024",
                "product_title": "Scurfol Topical 20g",
                "price": "₹0.00",
                "available": True
            },
            "shataavaree ghrutam": {
                "variant_id": "AEGM1019",
                "product_title": "Shataavaree ghrutam",
                "price": "₹205.00",
                "available": True
            },
            "shatpala ghrutam": {
                "variant_id": "AEGM1018",
                "product_title": "Shatpala ghrutam",
                "price": "₹205.00",
                "available": True
            },
            "silnoscar gel": {
                "variant_id": "AEAAX1023",
                "product_title": "Silnoscar Gel",
                "price": "₹890.00",
                "available": True
            },
            "spazex capsule": {
                "variant_id": "AEATR1016",
                "product_title": "Spazex Capsule 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "stay bio nmn": {
                "variant_id": "AEAAX1027",
                "product_title": "Stay Bio NMN 10 nos",
                "price": "₹660.00",
                "available": True
            },
            "staybio shot –": {
                "variant_id": "AEAAX1020",
                "product_title": "StayBio SHOT – 30ml",
                "price": "₹749.00",
                "available": True
            },
            "stoneflux": {
                "variant_id": "AEAAX1014",
                "product_title": "Stoneflux 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "stop ibs tablets": {
                "variant_id": "AECHK1031",
                "product_title": "Stop IBS Tablets 30 nos",
                "price": "₹312.00",
                "available": True
            },
            "sukhaprasooti ghrutam": {
                "variant_id": "AEGM1020",
                "product_title": "Sukhaprasooti ghrutam",
                "price": "₹265.00",
                "available": True
            },
            "sukumaaraghrutam": {
                "variant_id": "AEGM1021",
                "product_title": "Sukumaaraghrutam",
                "price": "₹315.00",
                "available": True
            },
            "takzema ointment": {
                "variant_id": "AECHK1033",
                "product_title": "Takzema Ointment 30 g",
                "price": "₹115.00",
                "available": True
            },
            "takzema tablets": {
                "variant_id": "AECHK1032",
                "product_title": "Takzema Tablets 30 nos",
                "price": "₹140.00",
                "available": True
            },
            "thickshoot care": {
                "variant_id": "AEAAX1010",
                "product_title": "Thickshoot Care 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "thickshoot hair serum": {
                "variant_id": "AEAAX1019",
                "product_title": "Thickshoot Hair Serum",
                "price": "₹0.00",
                "available": True
            },
            "thyroflux": {
                "variant_id": "AEAAX1011",
                "product_title": "Thyroflux 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "tiktaka ghrutam": {
                "variant_id": "AEGM1022",
                "product_title": "Tiktaka ghrutam",
                "price": "₹235.00",
                "available": True
            },
            "trichoderm topical": {
                "variant_id": "AEATR1025",
                "product_title": "Trichoderm Topical 20g",
                "price": "₹0.00",
                "available": True
            },
            "triphala ghrutam": {
                "variant_id": "AEGM1023",
                "product_title": "Triphala ghrutam",
                "price": "₹225.00",
                "available": True
            },
            "type 2d-fit": {
                "variant_id": "AEAAX1012",
                "product_title": "Type 2D-Fit 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "urtiplex anti-itch lotion": {
                "variant_id": "AECHK1034",
                "product_title": "Urtiplex Anti-itch Lotion 100 ml",
                "price": "₹185.00",
                "available": True
            },
            "v-rins topical": {
                "variant_id": "AEATR1026",
                "product_title": "V-Rins Topical 20g",
                "price": "₹0.00",
                "available": True
            },
            "varanaadi ghrutam": {
                "variant_id": "AEGM1024",
                "product_title": "Varanaadi ghrutam",
                "price": "₹200.00",
                "available": True
            },
            "vasosmart": {
                "variant_id": "AEAAX1013",
                "product_title": "Vasosmart 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "vastiaamayaantaka ghrutam": {
                "variant_id": "AEGM1025",
                "product_title": "Vastiaamayaantaka ghrutam",
                "price": "₹495.00",
                "available": True
            },
            "veinflux": {
                "variant_id": "AEAAX1015",
                "product_title": "Veinflux 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "veinflux fill –": {
                "variant_id": "AEAAX1026",
                "product_title": "Veinflux Fill – 5ml",
                "price": "₹625.00",
                "available": True
            },
            "veinflux gel": {
                "variant_id": "AEAAX1016",
                "product_title": "Veinflux gel",
                "price": "₹0.00",
                "available": True
            },
            "veinflux nc": {
                "variant_id": "AEAAX1017",
                "product_title": "Veinflux NC 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "veinflux rt": {
                "variant_id": "AEAAX1018",
                "product_title": "Veinflux RT 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "veinflux sheet (10 x 10 cm)": {
                "variant_id": "AEAAX1025",
                "product_title": "Veinflux Sheet (10 x 10 cm) 10 nos",
                "price": "₹416.00",
                "available": True
            },
            "veinflux swh cream": {
                "variant_id": "AEAAX1024",
                "product_title": "Veinflux Swh Cream",
                "price": "₹299.00",
                "available": True
            },
            "veinflux wrap": {
                "variant_id": "AEAAX1022",
                "product_title": "Veinflux Wrap",
                "price": "₹749.00",
                "available": True
            },
            "vidaariaadighrutam": {
                "variant_id": "AEGM1026",
                "product_title": "Vidaariaadighrutam",
                "price": "₹235.00",
                "available": True
            },
            "viscovas capsule": {
                "variant_id": "AEATR1018",
                "product_title": "Viscovas Capsule 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "vivadona capsule": {
                "variant_id": "AECHK1022",
                "product_title": "Vivadona Capsule 20 nos",
                "price": "₹195.00",
                "available": True
            },
            "vomiteb tablet": {
                "variant_id": "AECHK1023",
                "product_title": "Vomiteb Tablet 30 nos",
                "price": "₹100.00",
                "available": True
            },
            "vyridol capsule": {
                "variant_id": "AEATR1017",
                "product_title": "Vyridol Capsule 10 nos",
                "price": "₹0.00",
                "available": True
            },
            "zeptigo topical": {
                "variant_id": "AEATR1027",
                "product_title": "Zeptigo Topical 20g",
                "price": "₹0.00",
                "available": True
            },
            "zun d smart 2000 iu": {
                "variant_id": "AEAAX1029",
                "product_title": "Zun D Smart 2000 IU",
                "price": "₹97.00",
                "available": True
            },
           },
        }
    
    def normalize_medicine_name(self, medicine_name: str) -> str:
        return medicine_name.lower().strip()
    
    def get_variant_id(self, medicine_name: str) -> Optional[str]:
        normalized_name = self.normalize_medicine_name(medicine_name)
        mapping = self.medicine_mapping.get(normalized_name)
        if mapping and mapping.get("available", False):
            return mapping["variant_id"]
        return None
    
    def get_product_info(self, medicine_name: str) -> Dict:
        normalized_name = self.normalize_medicine_name(medicine_name)
        mapping = self.medicine_mapping.get(normalized_name)
        if mapping:
            return {
                "medicine_name": medicine_name,
                "shopify_variant_id": mapping["variant_id"],
                "shopify_product_title": mapping["product_title"],
                "price": mapping.get("price"),
                "is_available": mapping.get("available", False),
                "suggested_alternatives": []
            }
        return {
            "medicine_name": medicine_name,
            "shopify_variant_id": None,
            "shopify_product_title": None,
            "price": None,
            "is_available": False,
            "suggested_alternatives": []
        }
    
    def get_all_medicines(self) -> List[Dict]:
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

product_mapper = ProductMapper()
