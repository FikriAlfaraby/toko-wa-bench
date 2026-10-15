"""Where the domain's data lives: this repo's data/toko_wa, not tau2's own data folder."""

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "toko_wa"
DB_PATH = DATA_DIR / "db.json"
POLICY_PATH = DATA_DIR / "policy.md"
TASKS_PATH = DATA_DIR / "tasks.json"
SPLIT_PATH = DATA_DIR / "split_tasks.json"
