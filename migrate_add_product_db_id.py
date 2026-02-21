import os
import sqlite3

DB_PATH = os.path.join("instance", "adivasi_store.db")  # adjust if yours differs


def column_exists(cur, table: str, column: str) -> bool:
    cur.execute(f"PRAGMA table_info({table});")
    cols = [row[1] for row in cur.fetchall()]  # row[1] = column name
    return column in cols


def add_column_if_missing(cur, table: str, column_def: str, column_name: str):
    if column_exists(cur, table, column_name):
        print(f"✅ {table}.{column_name} already exists")
        return
    cur.execute(f"ALTER TABLE {table} ADD COLUMN {column_def};")
    print(f"➕ Added {table}.{column_name}")


def main():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"DB not found at: {DB_PATH} (edit DB_PATH in script)")

    print("DB:", os.path.abspath(DB_PATH))

    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()

        # Add columns (safe to run multiple times)
        add_column_if_missing(cur, "cart_item", "product_db_id INTEGER", "product_db_id")
        add_column_if_missing(cur, "order_item", "product_db_id INTEGER", "product_db_id")

        con.commit()
        print("✅ Migration complete.")
    finally:
        con.close()


if __name__ == "__main__":
    main()