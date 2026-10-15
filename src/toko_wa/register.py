"""Register the toko_wa domain with tau-bench's registry, without changing tau-bench itself.
Import this module before running the tau2 CLI (scripts/run.py does)."""

from tau2.registry import registry

from toko_wa.context import factory
from toko_wa.environment import DOMAIN, get_environment, get_tasks, get_tasks_split

STRATEGIES = ("full", "drop", "summary", "facts")


def register() -> None:
    """The domain, and one agent per context strategy: --agent ctx_full, ctx_drop, ctx_summary, ctx_facts."""
    if DOMAIN in registry.get_domains():
        return
    registry.register_domain(get_environment, DOMAIN)
    registry.register_tasks(get_tasks, DOMAIN, get_task_splits=get_tasks_split)
    for strategy in STRATEGIES:
        registry.register_agent_factory(factory(strategy), f"ctx_{strategy}")
