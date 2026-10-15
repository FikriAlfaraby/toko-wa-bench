"""The context strategies cut at the same place every run, never split a tool call from its result,
and send the model exactly the note plus the kept messages. No model is called: generate is faked."""

import pytest
from tau2.data_model.message import AssistantMessage, ToolCall, ToolMessage, UserMessage

import toko_wa.context as ctx


class FakeGenerate:
    """Stands in for tau2's generate: returns a fixed note for compaction calls, 'ok' otherwise."""

    def __init__(self):
        self.calls = []

    def __call__(self, model, messages, call_name, tools=None, **kwargs):
        self.calls.append((call_name, messages))
        text = "pesanan: hoodie maroon L (mengganti M)" if call_name.startswith("context_") else "ok"
        return AssistantMessage(
            role="assistant", content=text, usage={"prompt_tokens": 10, "completion_tokens": 5}
        )


@pytest.fixture
def fake(monkeypatch):
    fake = FakeGenerate()
    monkeypatch.setattr(ctx, "generate", fake)
    return fake


def chat(turns: int, size: int = 400) -> list:
    """turns x (customer, agent tool call, tool result, agent reply), each text about size characters."""
    out = []
    for i in range(turns):
        out.append(UserMessage(role="user", content=f"pelanggan {i} " + "x" * size))
        out.append(
            AssistantMessage(
                role="assistant",
                content=None,
                tool_calls=[ToolCall(id=f"c{i}", name="get_order", arguments={"order_id": "ORD-1"})],
            )
        )
        out.append(ToolMessage(id=f"c{i}", role="tool", content="y" * size))
        out.append(AssistantMessage(role="assistant", content=f"admin {i} " + "z" * size))
    return out


def agent(strategy):
    return ctx.ContextAgent(tools=[], domain_policy="SOP", llm="openai/test", llm_args={}, strategy=strategy)


def test_token_estimate_counts_text_and_tool_arguments():
    call = AssistantMessage(
        role="assistant",
        content=None,
        tool_calls=[ToolCall(id="1", name="get_order", arguments={"order_id": "ORD-1001"})],
    )
    assert ctx.tokens(UserMessage(role="user", content="a" * 400)) == 104
    assert ctx.tokens(call) == (len("get_order") + len("{'order_id': 'ORD-1001'}")) // 4 + 4


@pytest.mark.parametrize("strategy", ["drop", "summary", "facts"])
def test_a_long_chat_is_cut_at_a_customer_message_and_stays_under_the_budget(fake, strategy):
    a = agent(strategy)
    state = a.get_init_state(chat(12))
    a._generate_next_message(UserMessage(role="user", content="jadi ya kak"), state)
    assert state.cut > 0 and isinstance(state.messages[state.cut], UserMessage)
    visible = state.messages[state.cut :]
    assert sum(ctx.tokens(m) for m in visible) <= ctx.BUDGET_TOKENS
    sent = fake.calls[-1][1]
    assert sent[-len(visible) :] == visible
    assert not any(isinstance(m, ToolMessage) for m in sent[: len(sent) - len(visible)])


def test_full_never_cuts_and_short_chats_are_left_alone(fake):
    a = agent("full")
    state = a.get_init_state(chat(12))
    a._generate_next_message(UserMessage(role="user", content="jadi ya kak"), state)
    assert state.cut == 0 and len(fake.calls) == 1
    b = agent("summary")
    short = b.get_init_state([])  # a new chat: nothing from an earlier session, far under the budget
    b._generate_next_message(UserMessage(role="user", content="jadi ya kak"), short)
    assert short.cut == 0 and short.note is None


def test_summary_and_facts_send_their_note_and_record_what_it_cost(fake):
    for strategy in ("summary", "facts"):
        a = agent(strategy)
        state = a.get_init_state(chat(12))
        reply = a._generate_next_message(UserMessage(role="user", content="jadi ya kak"), state)
        assert state.note == "pesanan: hoodie maroon L (mengganti M)"
        sent = fake.calls[-1][1]
        assert (
            sent[1].role == "user"
            and sent[1].content.startswith(ctx.NOTE_PREFIX)
            and state.note in sent[1].content
        )
        record = reply.raw_data["toko_context"]["compaction"]
        assert record["strategy"] == strategy and record["usage"] == {
            "prompt_tokens": 10,
            "completion_tokens": 5,
        }


def test_drop_says_that_older_messages_are_hidden_and_keeps_no_note(fake):
    a = agent("drop")
    state = a.get_init_state(chat(12))
    a._generate_next_message(UserMessage(role="user", content="jadi ya kak"), state)
    sent = fake.calls[-1][1]
    assert state.note is None
    assert sent[1].role == "user" and sent[1].content == ctx.NOTE_PREFIX + ctx.NOTE_HEADER["drop"]
    assert [c for c, _ in fake.calls] == ["agent_response"]


def test_the_same_chat_is_cut_at_the_same_place_every_time(fake):
    cuts = set()
    for _ in range(3):
        a = agent("drop")
        state = a.get_init_state(chat(12))
        a._generate_next_message(UserMessage(role="user", content="jadi ya kak"), state)
        cuts.add(state.cut)
    assert len(cuts) == 1


def test_a_resumed_chat_compacts_the_earlier_session_before_the_first_reply(fake):
    for strategy in ("drop", "summary", "facts"):
        a = agent(strategy)
        state = a.get_init_state(chat(2))
        a._generate_next_message(UserMessage(role="user", content="kak jadi ya yg kemarin"), state)
        assert state.cut == state.earlier == 8
        assert fake.calls[-1][1][-1].content == "kak jadi ya yg kemarin"
    full = agent("full")
    state = full.get_init_state(chat(2))
    full._generate_next_message(UserMessage(role="user", content="kak jadi ya yg kemarin"), state)
    assert state.cut == 0 and len(fake.calls[-1][1]) == 1 + 8 + 1
