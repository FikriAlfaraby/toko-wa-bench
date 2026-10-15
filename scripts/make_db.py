"""Write data/toko_wa/db.json from toko_wa.seed.

uv run python scripts/make_db.py
"""

from toko_wa.paths import DB_PATH
from toko_wa.seed import build

if __name__ == "__main__":
    db = build()
    db.dump(str(DB_PATH), indent=1, ensure_ascii=False)
    counts = {name: len(getattr(db, name)) for name in ("customers", "products", "orders", "transfers")}
    print(f"{DB_PATH.name}: " + ", ".join(f"{n} {name}" for name, n in counts.items()))
