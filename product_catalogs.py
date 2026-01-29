"""
Initial full product catalog.
Mirrors shop.html exactly.
NO deduplication. NO cleanup.
"""

# ======================================================
# 1. MENU CATEGORIES (exact match)
# ======================================================

ACCESSORY_CATEGORIES = [
    "Saree",
    "Bandi",
    "Bags",
    "Gamosa",
    "Shawl",
    "Kurta Pyjama for Kids",
    "Dhoti for kids",
    "Sitapati",
    "Jhumka",
    "Chandrahaar",
    "Hashli",
    "Baju",
    "Khongso",
    "Poyori",
]

# ======================================================
# 2. METADATA PROFILES
# ======================================================

WOMEN_SAREE = dict(
    audience="women",
    type="Saree",
    menu_category="Saree",
    category_label="Handloom Saree",
)

WOMEN_BAG = dict(
    audience="women",
    type="Bag",
    menu_category="Bags",
    category_label="Bag",
)

MEN_BANDI = dict(
    audience="men",
    type="Bandi",
    menu_category="Bandi",
    category_label="Men Shirt",
)

MEN_BAG = dict(
    audience="men",
    type="Bag",
    menu_category="Bags",
    category_label="Bag",
)

KIDS_KURTA = dict(
    audience="kids",
    type="Kurta Pyjama for Kids",
    menu_category="Kurta Pyjama for Kids",
    category_label="Kids Kurta",
)

ORNAMENT = dict(
    audience="women",
    type="Jewellery",
    menu_category=None,
    category_label="Jewellery",
)

ACCESSORY = dict(
    audience="unisex",
    type="Accessory",
    menu_category=None,
    category_label="Accessory",
)

# ======================================================
# 3. WOMEN PRODUCTS (ALL)
# ======================================================

WOMEN_PRODUCTS = [
    {
        "id": "women-saree-1",
        "name": "LAL PARH SAREE",
        "price": 599,
        "badge": "New Drop",
        "images": {
            "primary": "/static/images/adivasi/laalparsaree1f.jpeg",
            "hover": "/static/images/adivasi/laalpaarsaree1b.jpeg",
        },
        **WOMEN_SAREE,
    },
    {
        "id": "women-saree-2",
        "name": "LAL PARH SAREE",
        "price": 599,
        "badge": "Limited",
        "images": {
            "primary": "/static/images/adivasi/laalpaarsaree2f.jpeg",
            "hover": "/static/images/adivasi/laalpaarsaree2b.jpeg",
        },
        **WOMEN_SAREE,
    },
    {
        "id": "women-saree-3",
        "name": "HARA PARH SAREE",
        "price": 699,
        "images": {
            "primary": "/static/images/adivasi/haraparasaree3f.jpeg",
            "hover": "/static/images/adivasi/haraparasaree3f.jpeg",
        },
        **WOMEN_SAREE,
    },
    {
        "id": "women-saree-4",
        "name": "LAL PARH SAREE",
        "price": 599,
        "images": {
            "primary": "/static/images/adivasi/laalpaarsaree4f.jpeg",
            "hover": "/static/images/adivasi/laalpaarsaree4b.jpeg",
        },
        **WOMEN_SAREE,
    },
    {
        "id": "women-saree-5",
        "name": "LAL PARH SAREE",
        "price": 599,
        "images": {
            "primary": "/static/images/adivasi/laalpaarsaree5.jpeg",
            "hover": "/static/images/adivasi/laalpaarsaree5.jpeg",
        },
        **WOMEN_SAREE,
    },
    {
        "id": "women-saree-6",
        "name": "LAL PARH SAREE",
        "price": 599,
        "images": {
            "primary": "/static/images/adivasi/laalpaarsaree7f.jpeg",
            "hover": "/static/images/adivasi/laalpaarsaree7f.jpeg",
        },
        **WOMEN_SAREE,
    },
    {
        "id": "women-saree-7",
        "name": "LAL PARH SAREE",
        "price": 599,
        "images": {
            "primary": "/static/images/adivasi/laalpaarsaree6f.jpeg",
            "hover": "/static/images/adivasi/laalpaarsaree6f.jpeg",
        },
        **WOMEN_SAREE,
    },
    {
        "id": "women-saree-8",
        "name": "MAROON SAREE",
        "price": 599,
        "images": {
            "primary": "/static/images/adivasi/Maroonsaree.jpeg",
            "hover": "/static/images/adivasi/Maroonsaree.jpeg",
        },
        **WOMEN_SAREE,
    },

    # Bags
    {
        "id": "women-bag-1",
        "name": "LADIES HANDBAG",
        "price": 399,
        "images": {
            "primary": "/static/images/adivasi/bag1f.jpeg",
            "hover": "/static/images/adivasi/bag1b.jpeg",
        },
        **WOMEN_BAG,
    },
    {
        "id": "women-bag-2",
        "name": "LADIES HANDBAG",
        "price": 399,
        "images": {
            "primary": "/static/images/adivasi/bag2f.jpeg",
            "hover": "/static/images/adivasi/bag2b.jpeg",
        },
        **WOMEN_BAG,
    },
    {
        "id": "women-bag-3",
        "name": "LADIES HANDBAG",
        "price": 399,
        "images": {
            "primary": "/static/images/adivasi/bag3f.jpeg",
            "hover": "/static/images/adivasi/bag3b.jpeg",
        },
        **WOMEN_BAG,
    },
    {
        "id": "women-bag-4",
        "name": "LADIES HANDBAG",
        "price": 399,
        "images": {
            "primary": "/static/images/adivasi/bag4f.jpeg",
            "hover": "/static/images/adivasi/bag4f.jpeg",
        },
        **WOMEN_BAG,
    },
    {
        "id": "women-bag-5",
        "name": "LADIES HANDBAG",
        "price": 399,
        "images": {
            "primary": "/static/images/adivasi/bag5f.jpeg",
            "hover": "/static/images/adivasi/bag5f.jpeg",
        },
        **WOMEN_BAG,
    },
    {
        "id": "women-bag-6",
        "name": "LADIES HANDBAG",
        "price": 599,
        "images": {
            "primary": "/static/images/adivasi/bag6f.jpeg",
            "hover": "/static/images/adivasi/bag6b.jpeg",
        },
        **WOMEN_BAG,
    },
    {
        "id": "women-bag-7",
        "name": "LADIES HANDBAG",
        "price": 599,
        "images": {
            "primary": "/static/images/adivasi/bag7f.jpeg",
            "hover": "/static/images/adivasi/bag7b.jpeg",
        },
        **WOMEN_BAG,
    },
    {
        "id": "women-bag-8",
        "name": "LADIES TOTE BAG",
        "price": 599,
        "images": {
            "primary": "/static/images/adivasi/bag8f.jpeg",
            "hover": "/static/images/adivasi/bag8b.jpeg",
        },
        **WOMEN_BAG,
    },
    {
        "id": "women-bag-9",
        "name": "LADIES TOTE BAG",
        "price": 599,
        "images": {
            "primary": "/static/images/adivasi/bag9b.jpeg",
            "hover": "/static/images/adivasi/bag9f.jpeg",
        },
        **WOMEN_BAG,
    },
]

# ======================================================
# 4. MEN PRODUCTS (ALL)
# ======================================================

MEN_PRODUCTS = [
    {
        "id": "men-bandi-1",
        "name": "Handloom Men's Bandi",
        "price": 999,
        "images": {
            "primary": "/static/images/adivasi/men1b.jpeg",
            "hover": "/static/images/adivasi/men1f.jpeg",
        },
        **MEN_BANDI,
    },
    {
        "id": "men-bandi-2",
        "name": "Man's Bandi",
        "price": 999,
        "images": {
            "primary": "/static/images/adivasi/men2f.jpeg",
            "hover": "/static/images/adivasi/men2b.jpeg",
        },
        **MEN_BANDI,
    },
    {
        "id": "men-bandi-3",
        "name": "Men's Bandi",
        "price": 1599,
        "images": {
            "primary": "/static/images/adivasi/men3ff.jpeg",
            "hover": "/static/images/adivasi/men3b.jpeg",
        },
        **MEN_BANDI,
    },
    {
        "id": "men-bandi-4",
        "name": "Men's Bandi",
        "price": 1599,
        "images": {
            "primary": "/static/images/adivasi/men4b.jpeg",
            "hover": "/static/images/adivasi/men4f.jpeg",
        },
        **MEN_BANDI,
    },
    {
        "id": "men-bandi-5",
        "name": "Men's Bandi",
        "price": 1599,
        "images": {
            "primary": "/static/images/adivasi/men5f.jpeg",
            "hover": "/static/images/adivasi/men5b.jpeg",
        },
        **MEN_BANDI,
    },
    {
        "id": "men-bandi-6",
        "name": "Men's Bandi",
        "price": 2299,
        "images": {
            "primary": "/static/images/adivasi/men6f.jpeg",
            "hover": "/static/images/adivasi/men6f.jpeg",
        },
        **MEN_BANDI,
    },
    {
        "id": "men-bag-1",
        "name": "Men's Bag",
        "price": 599,
        "images": {
            "primary": "/static/images/adivasi/menbag.jpeg",
            "hover": "/static/images/adivasi/menbag.jpeg",
        },
        **MEN_BAG,
    },
    {
        "id": "men-bag-2",
        "name": "Men's Bag",
        "price": 599,
        "images": {
            "primary": "/static/images/adivasi/menbag1.jpeg",
            "hover": "/static/images/adivasi/menbag1.jpeg",
        },
        **MEN_BAG,
    },
    {
        "id": "men-bag-3",
        "name": "Men's Bag",
        "price": 599,
        "images": {
            "primary": "/static/images/adivasi/menbag2.jpeg",
            "hover": "/static/images/adivasi/menbag2.jpeg",
        },
        **MEN_BAG,
    },
    {
        "id": "men-bag-4",
        "name": "Men's Bag",
        "price": 599,
        "images": {
            "primary": "/static/images/adivasi/menbag3.jpeg",
            "hover": "/static/images/adivasi/menbag3.jpeg",
        },
        **MEN_BAG,
    },
]

# ======================================================
# 5. KIDS PRODUCTS (ALL)
# ======================================================

KIDS_PRODUCTS = [
    {
        "id": "kids-bandi",
        "name": "Kid's Bandi (5–7 years)",
        "price": 599,
        "images": {
            "primary": "/static/images/adivasi/kids2f.jpeg",
            "hover": "/static/images/adivasi/kids2f.jpeg",
        },
        **KIDS_KURTA,
    },
    {
        "id": "kids-kurta-set",
        "name": "Kid's kurta pyjama set (5–7 years)",
        "price": 599,
        "images": {
            "primary": "/static/images/adivasi/kids1f.jpeg",
            "hover": "/static/images/adivasi/kids1b.jpeg",
        },
        **KIDS_KURTA,
    },
]

# ======================================================
# 6. ORNAMENTS & ACCESSORIES
# ======================================================

ORNAMENT_PRODUCTS = [
    {
        "id": "hasli", 
        "name": "Jhumka", 
        "price": 299,
        "images": {
            "primary": "/static/images/adivasi/hasli1f.jpeg",
            "hover": "/static/images/adivasi/hasli1f.jpeg",
        },
        **ORNAMENT,
    },
    {
        "id": "hasli", 
        "name": "Jhumka", 
        "price": 299,
        "images": {
            "primary": "/static/images/adivasi/hasli1b.jpeg",
            "hover": "/static/images/adivasi/hasli1b.jpeg",
        },
        **ORNAMENT,
    },
    {
        "id": "bala", 
        "name": "BALA", 
        "price": 299,
        "images": {
            "primary": "/static/images/adivasi/bala1f.jpeg",
            "hover": "/static/images/adivasi/bala1f.jpeg",
        },
        **ORNAMENT,
    },
    {
    "id": "baju", 
    "name": "Baju", 
    "price": 299,
    "images": {
        "primary": "/static/images/adivasi/baju1f.jpeg",
        "hover": "/static/images/adivasi/baju1b.jpeg",
        },
    **ORNAMENT,
    },
    {
        "id": "chandrahaar", 
        "name": "Chandrahaar", 
        "price": 349, 
        "images": {
            "primary": "/static/images/adivasi/chandra1b.jpeg",
            "hover": "/static/images/adivasi/chandra1f.jpeg",
        },   
        **ORNAMENT,
    },
]

ACCESSORY_PRODUCTS = [
    {
        "id": "accessory-shawl",
        "name": "SHAWL (MEN & WOMEN)", 
        "price": 399, 
        "images": {
            "primary": "/static/images/adivasi/shawl1f.jpeg",
            "hover": "/static/images/adivasi/shawl1f.jpeg",
        },
        **ACCESSORY,
    },
    {
        "id": "accessory-shawl",
        "name": "SHAWL (MEN & WOMEN)", 
        "price": 399, 
        "images": {
            "primary": "/static/images/adivasi/shawl2f.jpeg",
            "hover": "/static/images/adivasi/shawl2f.jpeg",
        },
        **ACCESSORY,
    },
    {
        "id": "accessory-shawl",
        "name": "HOMEMADE SHAWL (MEN & WOMEN)", 
        "price": 999, 
        "images": {
            "primary": "/static/images/adivasi/shawl3.jpeg",
            "hover": "/static/images/adivasi/shawl3.jpeg",
        },
        **ACCESSORY,
    },
    {
        "id": "accessory-shawl",
        "name": "HOMEMADE SHAWL (MEN & WOMEN)", 
        "price": 999, 
        "images": {
            "primary": "/static/images/adivasi/shawl4.jpeg",
            "hover": "/static/images/adivasi/shawl4.jpeg",
        },
        **ACCESSORY,
    },
    {
        "id": "accessory-shawl",
        "name": "HOMEMADE SHAWL (MEN & WOMEN)", 
        "price": 999, 
        "images": {
            "primary": "/static/images/adivasi/shawl5.jpeg",
            "hover": "/static/images/adivasi/shawl5.jpeg",
        },
        **ACCESSORY,
    }, 
   {
        "id": "accessory-shawl",
        "name": "HOMEMADE SHAWL (MEN & WOMEN)", 
        "price": 999, 
        "images": {
            "primary": "/static/images/adivasi/shawl6f.jpeg",
            "hover": "/static/images/adivasi/shawl6b.jpeg",
        },
        **ACCESSORY,
    },
   {
        "id": "accessory-shawl",
        "name": "HOMEMADE SHAWL (MEN & WOMEN)", 
        "price": 999, 
        "images": {
            "primary": "/static/images/adivasi/shawl7f.jpeg",
            "hover": "/static/images/adivasi/shawl7b.jpeg",
        },
        **ACCESSORY,
    },  
   {
        "id": "accessory-gamosa",
        "name": "Handmade Adivasi Gamosa", 
        "price": 249, 
        "images": {
            "primary": "/static/images/adivasi/gamosa1.jpeg",
            "hover": "/static/images/adivasi/gamosa1.jpeg",
        },
        **ACCESSORY,
    },
   {
        "id": "accessory-gamosa",
        "name": "Traditional Gamosa", 
        "price": 149, 
        "images": {
            "primary": "/static/images/adivasi/gamosa2.jpeg",
            "hover": "/static/images/adivasi/gamosa2.jpeg",
        },
        **ACCESSORY,
    },   
   {
        "id": "accessory-gamosa",
        "name": "Traditional Gamosa", 
        "price": 149, 
        "images": {
            "primary": "/static/images/adivasi/gamosa3.jpeg",
            "hover": "/static/images/adivasi/gamosa3.jpeg",
        },
        **ACCESSORY,
    },
   {
        "id": "accessory-gamosa",
        "name": "Traditional Gamosa", 
        "price": 269, 
        "images": {
            "primary": "/static/images/adivasi/gamosa4.jpeg",
            "hover": "/static/images/adivasi/gamosa4.jpeg",
        },
        **ACCESSORY,
    },    
           
]

# ======================================================
# 7. REGISTRIES
# ======================================================

ALL_PRODUCTS = {
    p["id"]: p
    for p in (
        WOMEN_PRODUCTS
        + MEN_PRODUCTS
        + KIDS_PRODUCTS
        + ORNAMENT_PRODUCTS
        + ACCESSORY_PRODUCTS
    )
}

SHOP_CATALOGS = [
    {"id": "women", "products": WOMEN_PRODUCTS},
    {"id": "men", "products": MEN_PRODUCTS},
    {"id": "kids", "products": KIDS_PRODUCTS},
    {"id": "ornaments", "products": ORNAMENT_PRODUCTS},
    {"id": "accessories", "products": ACCESSORY_PRODUCTS},
]
