"""tau-bench entry points for the toko_wa domain: the environment, the tasks and their splits."""

import json

from tau2.data_model.tasks import Task
from tau2.environment.environment import Environment

from toko_wa.data_model import TokoDB
from toko_wa.paths import DB_PATH, POLICY_PATH, SPLIT_PATH, TASKS_PATH
from toko_wa.tools import TokoTools

DOMAIN = "toko_wa"


def get_environment(db: TokoDB | None = None, solo_mode: bool = False) -> Environment:
    if solo_mode:
        raise ValueError("toko_wa does not support solo mode")
    db = db if db is not None else TokoDB.load(str(DB_PATH))
    return Environment(
        domain_name=DOMAIN, policy=POLICY_PATH.read_text(encoding="utf-8"), tools=TokoTools(db)
    )


def get_tasks_split() -> dict[str, list[str]]:
    return json.loads(SPLIT_PATH.read_text(encoding="utf-8"))


def get_tasks(task_split_name: str | None = "base") -> list[Task]:
    tasks = [Task.model_validate(t) for t in json.loads(TASKS_PATH.read_text(encoding="utf-8"))]
    if task_split_name is None:
        return tasks
    splits = get_tasks_split()
    if task_split_name not in splits:
        raise ValueError(f"Unknown task split {task_split_name!r}; known: {sorted(splits)}")
    return [t for t in tasks if t.id in splits[task_split_name]]
