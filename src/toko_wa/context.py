"""Four ways an agent can keep a long WhatsApp thread within a context budget.

- full: every message (the baseline; tau-bench's own agent does this).
- drop: when the conversation passes the budget, older messages are dropped.
- summary: older messages are replaced by a summary the same model writes (compaction).
- facts: older messages are replaced by a note of facts the same model keeps up to date.

Two moments trigger a cut. When a chat resumes after an earlier session (the task's starting
history: yesterday's or this morning's chat), the non-full strategies compact that whole earlier
session before the first reply, the way a WhatsApp agent reloads a thread the next day: drop sees
none of it, summary sees a summary, facts sees a note. Within a session, the budget applies.

The budget counts the conversation only (the policy and the tool list are fixed): about 2,000
tokens, what is left of an 8k context after a policy and 16 tool schemas of about 4k tokens and room
for the reply. Tokens are estimated as characters / 4, so every run cuts at the same place. After a
cut, the last ~800 tokens stay word for word, starting at a customer message so that no tool result
is separated from its call. Each compaction, with its note and the tokens it cost, is recorded on
the next agent message (raw_data["toko_context"]).
"""

from typing import Literal

from tau2.agent.llm_agent import LLMAgent, LLMAgentState
from tau2.data_model.message import Message, SystemMessage, UserMessage
from tau2.utils.llm_utils import generate

Strategy = Literal["full", "drop", "summary", "facts"]
BUDGET_TOKENS = 2_000
KEEP_TOKENS = 800

SUMMARY_PROMPT = """You are compacting the earlier part of a WhatsApp chat between a shop assistant
(assistant) and a customer (user), so that the assistant can continue the chat with less context.
Write a short summary in Indonesian of everything in the earlier part the assistant may still need:
what the customer asked for and decided, every detail they gave (addresses, sizes, colours,
quantities, couriers, payment methods, order numbers), corrections they made (give the final value),
what the shop promised or refused, and what is still open. If an earlier summary is given, merge it
in. Plain text, at most 200 words."""

FACTS_PROMPT = """You keep a note of facts for a shop assistant who continues a WhatsApp chat with a
customer; the earlier messages will be removed. Update the note from the messages below. One fact per
line, in Indonesian, as 'kategori: fakta'. Categories: pesanan (item, warna, ukuran, jumlah), alamat
atau tujuan, kurir, pembayaran, koreksi (the final value and what it replaced), janji atau penolakan
toko, nomor pesanan, masih terbuka. Copy names, numbers and amounts exactly. If the customer corrected
something, keep only the corrected value and say what it replaced. At most 25 lines."""

NOTE_PREFIX = "[Catatan otomatis dari sistem toko, bukan pesan pelanggan] "
NOTE_HEADER = {
    "drop": "[Sebagian pesan lama dalam percakapan ini tidak ditampilkan.]",
    "summary": "Ringkasan percakapan sebelumnya (dibuat otomatis karena percakapan panjang):\n",
    "facts": "Catatan fakta dari percakapan sebelumnya (dibuat otomatis karena percakapan panjang):\n",
}


def tokens(message: Message) -> int:
    """A fixed estimate of a message's size: characters of text and tool-call arguments, divided by 4."""
    size = len(message.content or "")
    for call in getattr(message, "tool_calls", None) or []:
        size += len(call.name) + len(str(call.arguments))
    return size // 4 + 4


def transcript(messages: list[Message]) -> str:
    lines = []
    for m in messages:
        if m.role == "tool":
            lines.append(f"[hasil alat] {m.content}")
        elif getattr(m, "tool_calls", None):
            lines.append(
                "[assistant memanggil] " + "; ".join(f"{c.name}({c.arguments})" for c in m.tool_calls)
            )
        else:
            lines.append(f"[{m.role}] {m.content}")
    return "\n".join(lines)


class ContextState(LLMAgentState):
    note: str | None = None
    cut: int = 0  # messages[:cut] are behind the note (or dropped)
    earlier: int = 0  # messages[:earlier] came from an earlier session (the task's starting history)
    resumed: bool = False  # whether the earlier session has been compacted yet


class ContextAgent(LLMAgent[ContextState]):
    def __init__(self, tools, domain_policy, llm, llm_args=None, strategy: Strategy = "full"):
        super().__init__(tools=tools, domain_policy=domain_policy, llm=llm, llm_args=llm_args)
        self.strategy = strategy

    def get_init_state(self, message_history: list[Message] | None = None) -> ContextState:
        base = super().get_init_state(message_history)
        return ContextState(
            system_messages=base.system_messages, messages=base.messages, earlier=len(message_history or [])
        )

    def _new_cut(self, state: ContextState) -> int | None:
        """Where the kept, word-for-word part starts: about KEEP_TOKENS back, at a customer message."""
        messages, kept, cut = state.messages, 0, len(state.messages)
        while cut > state.cut and kept < KEEP_TOKENS:
            cut -= 1
            kept += tokens(messages[cut])
        after = [i for i in range(cut, len(messages)) if isinstance(messages[i], UserMessage)]
        before = [i for i in range(state.cut + 1, cut) if isinstance(messages[i], UserMessage)]
        cut = after[0] if after else (before[-1] if before else None)
        return cut if cut is not None and cut > state.cut else None

    def _compact(self, state: ContextState) -> dict | None:
        if self.strategy == "full":
            return None
        if state.earlier and not state.resumed:
            # the chat resumes: the whole earlier session goes behind the note
            state.resumed, cut = True, state.earlier
        else:
            visible = state.messages[state.cut :]
            if sum(tokens(m) for m in visible) <= BUDGET_TOKENS:
                return None
            cut = self._new_cut(state)
            if cut is None:
                return None
        old = state.messages[state.cut : cut]
        record = {"strategy": self.strategy, "from": state.cut, "to": cut}
        if self.strategy in ("summary", "facts"):
            prompt = SUMMARY_PROMPT if self.strategy == "summary" else FACTS_PROMPT
            earlier = f"Catatan/ringkasan sebelumnya:\n{state.note}\n\n" if state.note else ""
            reply = generate(
                model=self.llm,
                messages=[
                    SystemMessage(role="system", content=prompt),
                    UserMessage(role="user", content=earlier + "Pesan-pesan:\n" + transcript(old)),
                ],
                call_name=f"context_{self.strategy}",
                **self.llm_args,
            )
            state.note = (reply.content or "").strip()
            record.update(note=state.note, usage=reply.usage, cost=reply.cost)
        state.cut = cut
        return record

    def _generate_next_message(self, message, state: ContextState):
        if isinstance(message, UserMessage) and message.is_audio:
            raise ValueError("User message cannot be audio.")
        if hasattr(message, "tool_messages"):
            state.messages.extend(message.tool_messages)
        else:
            state.messages.append(message)
        compaction = self._compact(state)
        context = list(state.system_messages)
        # The note opens the conversation, the way production agents carry a compaction summary
        # forward; as a second system message the model treated it as instructions, not as the chat.
        if state.cut and self.strategy == "drop":
            context.append(UserMessage(role="user", content=NOTE_PREFIX + NOTE_HEADER["drop"]))
        elif state.note:
            context.append(
                UserMessage(role="user", content=NOTE_PREFIX + NOTE_HEADER[self.strategy] + state.note)
            )
        visible = state.messages[state.cut :]
        context += visible
        reply = generate(
            model=self.llm, tools=self.tools, messages=context, call_name="agent_response", **self.llm_args
        )
        info = {
            "strategy": self.strategy,
            "visible_messages": len(visible),
            "visible_tokens": sum(tokens(m) for m in visible),
        }
        if compaction:
            info["compaction"] = compaction
        reply.raw_data = {**(reply.raw_data or {}), "toko_context": info}
        return reply


def factory(strategy: Strategy):
    def create(tools, domain_policy, **kwargs):
        return ContextAgent(tools, domain_policy, kwargs.get("llm"), kwargs.get("llm_args"), strategy)

    return create
