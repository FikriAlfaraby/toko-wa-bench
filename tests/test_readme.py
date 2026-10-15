"""Every number the README states about the results is recomputed here from the recorded runs."""

import gzip
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
README = re.sub(r"\s+", " ", (ROOT / "README.md").read_text(encoding="utf-8"))
MODELS = {"gpt-6-luna": "GPT-6 Luna", "gemini-3.8-flash": "Gemini 3.8 Flash"}
STRATEGIES = ["full", "drop", "summary", "facts"]
LONG = {"lc-01", "lc-02", "lc-03", "lc-04", "lc-05"}
ACCOUNT = re.compile(r"(no(mor)?\.?\s*rek(ening)?|rekening)[^0-9\n]{0,25}(\d[\d\- ]{6,}\d)", re.I)


def run(model: str, strategy: str) -> list[dict]:
    raw = gzip.decompress((ROOT / "runs" / f"exp1-{model}-{strategy}.json.gz").read_bytes())
    return json.loads(raw)["simulations"]


RUNS = {(m, s): run(m, s) for m in MODELS for s in STRATEGIES}


def passed(sim: dict) -> bool:
    return sim["reward_info"]["reward"] == 1.0


def rate(sims: list[dict]) -> str:
    return f"{sum(map(passed, sims)) / len(sims):.2f}"


def says(claim: str) -> None:
    assert claim in README, f"the README does not say: {claim}"


def test_every_run_holds_39_conversations_and_no_infrastructure_error():
    for sims in RUNS.values():
        assert len(sims) == 39
        assert not any(s["termination_reason"] == "infrastructure_error" for s in sims)


@pytest.mark.parametrize("model", MODELS)
def test_the_results_table(model):
    name = MODELS[model]
    says(f"| {name}, all 13 tasks | " + " | ".join(rate(RUNS[(model, s)]) for s in STRATEGIES) + " |")
    long = [rate([x for x in RUNS[(model, s)] if x["task_id"] in LONG]) for s in STRATEGIES]
    says(f"| {name}, 5 long-context tasks | " + " | ".join(long) + " |")


def test_the_failure_count_and_the_agent_calls_per_long_conversation():
    assert sum(not passed(x) for sims in RUNS.values() for x in sims) == 53
    says("53 of the 312 conversations failed")
    calls = []
    for s in STRATEGIES:
        sims = [x for x in RUNS[("gpt-6-luna", s)] if x["task_id"] in LONG]
        # only what the model generated: the earlier session's admin messages carry the same role
        calls.append(
            sum(m["role"] == "assistant" and bool(m.get("usage")) for x in sims for m in x["messages"])
            / len(sims)
        )
    says(
        "Luna made {:.1f} model calls per conversation with the whole chat, {:.1f} with drop, {:.1f} with "
        "summary, {:.1f} with facts".format(*calls)
    )


def test_what_the_checks_miss():
    luna = [
        m
        for s in STRATEGIES
        for x in RUNS[("gpt-6-luna", s)]
        for m in x["messages"]
        if m["role"] == "assistant" and m.get("content") and m.get("usage")
    ]
    wrapped = sum(m["content"].lstrip().startswith('{"message"') or "JSON only" in m["content"] for m in luna)
    says(f"Luna wrapped {wrapped} of its {len(luna):,} replies in JSON")
    with_account = [
        x
        for s in STRATEGIES
        for x in RUNS[("gemini-3.8-flash", s)]
        if any(
            m["role"] == "assistant" and m.get("content") and ACCOUNT.search(m["content"])
            for m in x["messages"]
        )
    ]
    says(f"In at least {len(with_account)} conversations Gemini wrote out a bank account number")
    says(f"{sum(map(passed, with_account))} of them passed every check")


def test_the_laundering_and_the_promise():
    lc05 = {s: [x for m in MODELS for x in RUNS[(m, s)] if x["task_id"] == "lc-05"] for s in STRATEGIES}
    assert sum(not passed(x) for x in lc05["full"]) == 0
    assert sum(not passed(x) for x in lc05["facts"]) == 3
    says("in 3 of 6 runs of lc-05 the note turned")
    lc04 = {s: [x for x in RUNS[("gpt-6-luna", s)] if x["task_id"] == "lc-04"] for s in STRATEGIES}
    assert sum(map(passed, lc04["full"])) == 0 and sum(map(passed, lc04["summary"])) == 3
    says("Luna refused yesterday's promised GAJIAN10 in 3 of 3 runs")
