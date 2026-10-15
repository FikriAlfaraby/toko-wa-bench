"""Every task's reference actions run without an error on a fresh shop, and every task is reachable.

tau-bench builds the expected end state by replaying a task's reference actions. If one of them
fails, the grader drops it and expects an unchanged database, so a correct agent fails the task
(retail task 105 in tau-bench 1.0.1 is such a case). These tests stop that from happening here.
"""

import json

import pytest
from tau2.data_model.message import ToolCall

from toko_wa.environment import get_environment, get_tasks, get_tasks_split
from toko_wa.paths import TASKS_PATH

TASKS = get_tasks(None)
WRITES = {
    "create_order",
    "confirm_payment",
    "update_order_items",
    "update_order_address",
    "add_address",
    "cancel_order",
    "request_return",
}


def replay(task):
    env = get_environment()
    state = task.initial_state
    env.set_state(
        state.initialization_data if state else None,
        state.initialization_actions if state else None,
        state.message_history or [] if state else [],
    )
    before = env.get_db_hash()
    results = []
    for i, action in enumerate(task.evaluation_criteria.actions):
        call = ToolCall(id=f"ref-{i}", name=action.name, arguments=action.arguments, requestor="assistant")
        reply = env.get_response(call)
        results.append((action.name, reply))
    return env, before, results


def test_task_ids_are_unique_and_every_split_names_real_tasks():
    ids = [t.id for t in TASKS]
    assert len(ids) == len(set(ids))
    for name, members in get_tasks_split().items():
        assert set(members) <= set(ids), name
    assert set(get_tasks_split()["base"]) == {i for i in ids if not i.startswith("smoke")}


@pytest.mark.parametrize("task", TASKS, ids=[t.id for t in TASKS])
def test_reference_actions_run_without_error(task):
    env, before, results = replay(task)
    for name, reply in results:
        assert not reply.error, f"{task.id}: {name} failed: {reply.content}"
    wrote = any(name in WRITES for name, _ in results)
    assert (env.get_db_hash() != before) == wrote, (
        f"{task.id}: the database should change only if the task writes"
    )


@pytest.mark.parametrize("task", TASKS, ids=[t.id for t in TASKS])
def test_every_task_sets_the_chat_number_of_a_real_customer(task):
    phone = task.initial_state.initialization_data.agent_data["chat"]["phone"]
    env = get_environment()
    assert env.tools.find_customer_by_phone(phone)


def test_the_smoke_total_quoted_in_its_assertion_is_what_the_shop_charges():
    task = next(t for t in TASKS if t.id == "smoke-01")
    _, _, results = replay(task)
    order = json.loads(results[-1][1].content)
    assert order["total"] == 198_570
    assert "Rp198.570" in task.evaluation_criteria.nl_assertions[0]


def test_tasks_file_is_valid_json_with_indonesian_style_instructions():
    raw = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    for task in raw:
        assert "WhatsApp" in task["user_scenario"]["instructions"]["task_instructions"], task["id"]
