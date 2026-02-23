# seed_products_from_product_catalogs.py
# Run: python3 seed_products_from_product_catalogs.py
#
# Reads product_catalogs.py lists and inserts into DB Product table
# - maps catalog fields -> DB Product fields
# - inserts ALL items (even duplicate IDs) by generating unique slugs
# - default stock = 10
# - safe to re-run: skips rows if that exact slug already exists

import re
from typing import List, Dict, Any

# Import your Flask app + db + Product model
from app import app, db, Product

# Import catalog lists (IMPORTANT: use LISTS, not ALL_PRODUCTS dict)
from product_catalogs import (
    WOMEN_PRODUCTS,
    MEN_PRODUCTS,
    KIDS_PRODUCTS,
    ORNAMENT_PRODUCTS,
    ACCESSORY_PRODUCTS,
    ACCESSORY_CATEGORIES,
)

DEFAULT_STOCK = 10
DRY_RUN = False          # True = just print what would be inserted
SKIP_IF_EXISTS = True    # True = do not update existing rows


def _slugify(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


def _unique_slug(base: str) -> str:
    """
    Ensure slug is unique in Product table. If taken, append -2, -3, ...
    """
    base = base or "product"
    candidate = base
    i = 2
    while Product.query.filter_by(slug=candidate).first() is not None:
        candidate = f"{base}-{i}"
        i += 1
    return candidate


def _pick_category(item: Dict[str, Any]) -> str:
    """
    DB field: category (your mega-menu category names)

    Catalog provides:
      - menu_category (best)
      - type (sometimes same as category)
      - category_label (more like subcategory)
    We choose the first non-empty.
    """
    for k in ("menu_category", "type", "category_label"):
        v = (item.get(k) or "").strip()
        if v:
            return v

    # fallback if nothing present
    return "Accessories"


def _image_primary(item: Dict[str, Any]) -> str:
    images = item.get("images") or {}
    return (images.get("primary") or "").strip()


def _image_hover(item: Dict[str, Any]) -> str:
    """
    Back/hover image from catalog.
    If missing, fallback to primary.
    """
    images = item.get("images") or {}
    hover = (images.get("hover") or "").strip()
    if hover:
        return hover
    return _image_primary(item)


def _all_items() -> List[Dict[str, Any]]:
    # Use lists so duplicates don’t get overwritten (ALL_PRODUCTS dict would lose them)
    return WOMEN_PRODUCTS + MEN_PRODUCTS + KIDS_PRODUCTS + ORNAMENT_PRODUCTS + ACCESSORY_PRODUCTS


def _map_to_db_fields(item: Dict[str, Any], idx: int) -> Dict[str, Any]:
    """
    Map product_catalogs.py fields -> DB Product fields.

    DB Product fields (expected):
      name, slug, price, stock, category, description, sizes, colors,
      image_url, image_hover_url, is_active
    """
    name = (item.get("name") or "").strip() or "Untitled Product"
    price = float(item.get("price") or 0)
    category = _pick_category(item)

    # ✅ front/back exactly like old catalog structure
    image_url = _image_primary(item)         # front
    image_hover_url = _image_hover(item)     # back (fallback to front)

    # Build a stable base slug:
    # - prefer catalog "id" + idx because some catalog ids repeat (hasli/accessory-shawl)
    # - idx ensures ALL products can be inserted uniquely
    raw_id = (item.get("id") or "").strip()
    base = _slugify(raw_id) if raw_id else _slugify(name)
    base = base or "product"
    base = f"{base}-{idx}"  # makes sure duplicates still insert

    return {
        "name": name,
        "slug": base,                # will be uniquified below
        "price": price,
        "stock": DEFAULT_STOCK,      # your requirement
        "category": category,
        "description": "",           # catalog doesn’t provide; keep blank
        "sizes": "",                 # keep blank (or extend later)
        "colors": "",                # keep blank (or extend later)
        "image_url": image_url,              # ✅ front
        "image_hover_url": image_hover_url,  # ✅ back
        "is_active": True,
    }


def main():
    with app.app_context():
        items = _all_items()

        created = 0
        skipped = 0
        category_warnings = 0

        for idx, it in enumerate(items, start=1):
            data = _map_to_db_fields(it, idx)

            # Optional: warn if category isn't in your mega-menu list
            # (does NOT block insert; just helps you detect mismatches)
            if data["category"] not in ACCESSORY_CATEGORIES:
                category_warnings += 1
                # print(f"⚠️ Category not in menu list: {data['category']} for {data['name']}")

            # Ensure final unique slug in DB
            final_slug = _unique_slug(data["slug"])

            if SKIP_IF_EXISTS and Product.query.filter_by(slug=final_slug).first():
                skipped += 1
                continue

            p = Product(
                name=data["name"],
                slug=final_slug,
                price=data["price"],
                stock=data["stock"],
                category=data["category"],
                description=data["description"],
                sizes=data["sizes"],
                colors=data["colors"],
                image_url=data["image_url"],
                image_hover_url=data["image_hover_url"],  # ✅ NEW
                is_active=data["is_active"],
            )

            if DRY_RUN:
                print(
                    f"[DRY] {p.slug} | {p.name} | {p.category} | Rs {p.price} | "
                    f"stock {p.stock} | front={bool(p.image_url)} | back={bool(p.image_hover_url)}"
                )
            else:
                db.session.add(p)
                created += 1

        if not DRY_RUN:
            db.session.commit()

        print("✅ Seeding finished")
        print(f"Inserted: {created}")
        print(f"Skipped: {skipped}")
        print(f"Category warnings: {category_warnings} (insert still happened)")


if __name__ == "__main__":
    main()