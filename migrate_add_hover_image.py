import sqlite3
from pathlib import Path

DB_PATH = Path("instance") / "adivasi_store.db"

def column_exists(cur, table, col):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    return col in cols

def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DB not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if not column_exists(cur, "product", "image_hover_url"):
        cur.execute("ALTER TABLE product ADD COLUMN image_hover_url VARCHAR(500)")
        print("✅ Added column: product.image_hover_url")
    else:
        print("ℹ️ Column already exists: product.image_hover_url")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()