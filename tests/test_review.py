"""The hand review covers exactly the failed conversations, and every quote is in its conversation."""

import gzip
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = json.loads((ROOT / "review" / "2026-10-15.json").read_text(encoding="utf-8"))["items"]
README = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())
CAUSES = {"context lost", "laundered", "agent error", "simulated customer", "judge"}


def runs():
    for model in ("gpt-6-luna", "gemini-3.8-flash"):
        for strategy in ("full", "drop", "summary", "facts"):
            raw = gzip.decompress((ROOT / "runs" / f"exp1-{model}-{strategy}.json.gz").read_bytes())
            for sim in json.loads(raw)["simulations"]:
                yield (model, strategy, sim["task_id"], sim["trial"]), sim


SIMS = dict(runs())


def texts(sim: dict) -> list[str]:
    """What a quote may come from: messages, tool-call arguments, compaction notes; bold markers removed."""
    out = []
    for m in sim["messages"]:
        out.append(m.get("content") or "")
        out += [json.dumps(c.get("arguments"), ensure_ascii=False) for c in m.get("tool_calls") or []]
        out.append(
            (((m.get("raw_data") or {}).get("toko_context") or {}).get("compaction") or {}).get("note") or ""
        )
    return [t.replace("**", "") for t in out]


def test_the_review_covers_every_failed_conversation_once_and_nothing_else():
    failed = {key for key, sim in SIMS.items() if sim["reward_info"]["reward"] != 1.0}
    keys = [(i["model"], i["strategy"], i["task"], i["trial"]) for i in REVIEW]
    assert len(keys) == len(set(keys))
    assert set(keys) == failed


def test_every_quote_is_word_for_word_in_its_conversation():
    for item in REVIEW:
        sim = SIMS[(item["model"], item["strategy"], item["task"], item["trial"])]
        assert item["cause"] in CAUSES, item["cause"]
        assert len(item["note"]) > 20, item
        assert any(item["quote"] in t for t in texts(sim)), item


def test_the_readme_counts_the_causes():
    n = Counter(i["cause"] for i in REVIEW)
    assert (
        f"{n['context lost']} lost a detail through the strategy and {n['laundered']} were laundered"
        in README
    )
    assert f"{n['agent error']} were agent mistakes" in README
    assert f"{n['simulated customer']} were the simulated customer" in README
    assert f"{n['judge']} were the judge" in README
    drop = Counter(i["cause"] for i in REVIEW if i["strategy"] == "drop")
    assert f"{drop['context lost']} of drop's {sum(drop.values())} failures lost a detail" in README
