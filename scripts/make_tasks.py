"""Write data/toko_wa/tasks.json and split_tasks.json from data/toko_wa/task_specs.yaml.

Each task is a WhatsApp chat with one customer of Toko Rapi Bandung. The reference actions are
replayed on a fresh shop here, and every Rupiah amount an assertion quotes is read from that replay,
so no total in a task is computed by hand.

    uv run python scripts/make_tasks.py
"""

import json

import yaml

from toko_wa.paths import DATA_DIR, SPLIT_PATH, TASKS_PATH
from toko_wa.seed import build
from toko_wa.tools import TokoTools

SPECS_PATH = DATA_DIR / "task_specs.yaml"
WRITES = {
    "create_order",
    "confirm_payment",
    "update_order_items",
    "update_order_address",
    "add_address",
    "cancel_order",
    "request_return",
    "transfer_to_admin",
}


def rp(amount: int) -> str:
    return "Rp" + f"{amount:,}".replace(",", ".")


def replay(spec: dict) -> tuple[list, TokoTools]:
    """Run the reference actions on a fresh shop; return what each write returned, and the shop."""
    shop = TokoTools(build())
    shop.db.chat.phone = spec["phone"]
    writes = []
    for action in spec["actions"]:
        result = getattr(shop, action["name"])(**action["arguments"])
        if action["name"] in WRITES:
            writes.append(result)
    return writes, shop


def fill(text: str, writes: list, shop: TokoTools) -> str:
    """{total:N} is the total of the order the N-th write returned; {order:ID} is that order's total."""
    for i, result in enumerate(writes):
        if hasattr(result, "total"):
            text = text.replace(f"{{total:{i}}}", rp(result.total))
    for order_id, order in shop.db.orders.items():
        text = text.replace(f"{{order:{order_id}}}", rp(order.total))
    if "{" in text:
        raise ValueError(f"unfilled placeholder in: {text}")
    return text


def to_task(spec: dict, style: str, histories: dict) -> dict:
    writes, shop = replay(spec)
    history = None
    if spec.get("history"):
        history = [
            {"role": "user" if line["who"] == "customer" else "assistant", "content": line["text"]}
            for line in histories[spec["history"]]
        ]
    return {
        "id": spec["id"],
        "description": {"purpose": spec["purpose"], "relevant_policies": None, "notes": spec["group"]},
        "user_scenario": {
            "persona": spec["persona"],
            "instructions": {
                "domain": "toko_wa",
                "reason_for_call": spec["reason"],
                "known_info": spec["known"],
                "unknown_info": spec["unknown"] or None,
                "task_instructions": style,
            },
        },
        "initial_state": {
            "initialization_data": {"agent_data": {"chat": {"phone": spec["phone"]}}, "user_data": None},
            "initialization_actions": None,
            "message_history": history,
        },
        "evaluation_criteria": {
            "actions": [
                {
                    "action_id": f"{spec['id']}_{i}",
                    "name": a["name"],
                    "arguments": a["arguments"],
                    "info": None,
                }
                for i, a in enumerate(spec["actions"])
            ],
            "communicate_info": [],
            "nl_assertions": [fill(text, writes, shop) for text in spec["nl"]],
            "reward_basis": ["DB", "NL_ASSERTION"] if spec["nl"] else ["DB"],
        },
    }


def main() -> None:
    specs = yaml.safe_load(SPECS_PATH.read_text(encoding="utf-8"))
    existing = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    smoke = [t for t in existing if t["id"].startswith("smoke")]
    tasks = [to_task(spec, specs["style"], specs["histories"]) for spec in specs["tasks"]]
    TASKS_PATH.write_text(json.dumps(smoke + tasks, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    groups: dict[str, list[str]] = {}
    for spec in specs["tasks"]:
        groups.setdefault(spec["group"], []).append(spec["id"])
    splits = {"base": [t["id"] for t in tasks], **groups, "smoke": [t["id"] for t in smoke]}
    SPLIT_PATH.write_text(json.dumps(splits, indent=1) + "\n", encoding="utf-8")
    print(f"{TASKS_PATH.name}: {len(tasks)} tasks ({', '.join(f'{k} {len(v)}' for k, v in groups.items())})")


if __name__ == "__main__":
    main()
