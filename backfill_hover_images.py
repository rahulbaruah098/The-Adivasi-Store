# backfill_hover_images.py
# Run: python3 backfill_hover_images.py
#
# Updates existing DB products:
# - sets Product.image_hover_url based on catalog images.hover
# - matches existing rows by image_url (front image path)
# - does not create duplicates

from app import app, db, Product
from product_catalogs import (
    WOMEN_PRODUCTS, MEN_PRODUCTS, KIDS_PRODUCTS, ORNAMENT_PRODUCTS, ACCESSORY_PRODUCTS
)

DRY_RUN = False  # True => no DB write


def all_items():
    return WOMEN_PRODUCTS + MEN_PRODUCTS + KIDS_PRODUCTS + ORNAMENT_PRODUCTS + ACCESSORY_PRODUCTS


def main():
    with app.app_context():
        items = all_items()

        # Build map: front_path -> hover_path
        front_to_hover = {}
        for it in items:
            images = it.get("images") or {}
            front = (images.get("primary") or "").strip()
            hover = (images.get("hover") or "").strip() or front
            if front:
                front_to_hover[front] = hover

        updated = 0
        missing = 0

        # Only update rows that have image_url and empty hover (or always overwrite if you want)
        rows = Product.query.all()
        for p in rows:
            front = (p.image_url or "").strip()
            if not front:
                continue

            hover = front_to_hover.get(front)
            if not hover:
                missing += 1
                continue

            # ✅ overwrite if empty, or overwrite always
            # If you want ALWAYS override, remove this if condition
            if p.image_hover_url and p.image_hover_url.strip():
                continue

            if DRY_RUN:
                print(f"[DRY] update {p.id} {p.slug} -> hover={hover}")
            else:
                p.image_hover_url = hover
                updated += 1

        if not DRY_RUN:
            db.session.commit()

        print("✅ Done")
        print("Updated:", updated)
        print("No catalog match:", missing)


if __name__ == "__main__":
    main()