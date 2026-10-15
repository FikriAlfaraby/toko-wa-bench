"""Summarise the pre-registered experiment from tau2's result files.

Pass^1 per model and strategy (overall and per task group), the six predictions checked against the
numbers, tokens per conversation, and every task's result. Prediction 4 needs reading by hand: the
lc-05 runs are listed with what the agent said about ongkir.

    uv run python scripts/analyze.py runs --json results/exp1-summary.json
    (or point it at tau2's data/simulations folder)
"""

import argparse
import gzip
import json
import re
from pathlib import Path

from toko_wa.environment import get_tasks

MODELS = {"gpt-6-luna": "GPT-6 Luna", "gemini-3.8-flash": "Gemini 3.8 Flash"}
STRATEGIES = ["full", "drop", "summary", "facts"]
GROUPS = ["topic_switch", "long_context", "other"]


def read_run(sim_dir: Path, name: str) -> dict | None:
    """A run as tau2 saved it (<name>/results.json) or as kept in this repo (runs/<name>.json.gz)."""
    for path in (sim_dir / name / "results.json", sim_dir / f"{name}.json.gz"):
        if path.exists():
            raw = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
            return json.loads(raw.decode("utf-8"))
    return None


def load(sim_dir: Path) -> dict:
    runs = {}
    for model in MODELS:
        for strategy in STRATEGIES:
            run = read_run(sim_dir, f"exp1-{model}-{strategy}")
            if run is None:
                continue
            sims = run["simulations"]
            runs[(model, strategy)] = [
                s for s in sims if s.get("termination_reason") != "infrastructure_error"
            ]
    return runs


def passed(sim: dict) -> bool:
    return (sim.get("reward_info") or {}).get("reward") == 1.0


def rate(sims: list) -> float | None:
    return sum(map(passed, sims)) / len(sims) if sims else None


def tokens(sim: dict) -> int:
    """Agent prompt tokens over the conversation, plus every token of its compaction calls."""
    total = 0
    for m in sim["messages"]:
        if m["role"] != "assistant":
            continue
        total += (m.get("usage") or {}).get("prompt_tokens", 0)
        compaction = ((m.get("raw_data") or {}).get("toko_context") or {}).get("compaction") or {}
        usage = compaction.get("usage") or {}
        total += usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
    return total


def compactions(sim: dict) -> int:
    return sum(
        "compaction" in ((m.get("raw_data") or {}).get("toko_context") or {})
        for m in sim["messages"]
        if m["role"] == "assistant"
    )


def fmt(x: float | None) -> str:
    return "–" if x is None else f"{x:.2f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("sim_dir", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    group = {t.id: t.description.notes for t in get_tasks("base")}
    runs = load(args.sim_dir)

    def sims(model, strategy, groups=None, tasks=None):
        out = runs.get((model, strategy), [])
        if groups:
            out = [s for s in out if group[s["task_id"]] in groups]
        if tasks:
            out = [s for s in out if s["task_id"] in tasks]
        return out

    lines = [
        "## Pass^1 (conversations passed / run)",
        "",
        "| Model | Strategy | All | " + " | ".join(GROUPS) + " | n |",
        "|---|---|---:|" + "---:|" * len(GROUPS) + "---:|",
    ]
    summary = {}
    for model, name in MODELS.items():
        for strategy in STRATEGIES:
            row = [rate(sims(model, strategy))] + [rate(sims(model, strategy, [g])) for g in GROUPS]
            n = len(sims(model, strategy))
            summary[f"{model}/{strategy}"] = {
                "all": row[0],
                **dict(zip(GROUPS, row[1:], strict=True)),
                "n": n,
            }
            lines.append(f"| {name} | {strategy} | " + " | ".join(fmt(x) for x in row) + f" | {n} |")

    lc, rest = ["long_context"], ["topic_switch", "other"]
    checks = []
    for model, name in MODELS.items():
        r = {s: rate(sims(model, s, lc)) for s in STRATEGIES}
        if None in r.values():
            continue
        ok = r["drop"] <= min(r.values()) and r["full"] - r["drop"] >= 0.30
        checks.append(
            f"1. {name}: long context "
            + ", ".join(f"{s} {fmt(v)}" for s, v in r.items())
            + f" -> {'held' if ok else 'failed'}"
        )
        checks.append(
            f"2. {name}: facts {fmt(r['facts'])} vs summary {fmt(r['summary'])} -> "
            + ("held" if r["facts"] >= r["summary"] else "failed")
        )
        other = {s: rate(sims(model, s, rest)) for s in STRATEGIES}
        gaps = {s: abs(other[s] - other["full"]) for s in STRATEGIES if s != "full"}
        checks.append(
            f"3. {name}: tasks without history "
            + ", ".join(f"{s} {fmt(v)}" for s, v in other.items())
            + f" -> {'held' if max(gaps.values()) <= 0.15 else 'failed'}"
        )
        mean = {s: sum(map(tokens, sims(model, s, lc))) / len(sims(model, s, lc)) for s in STRATEGIES}
        ok5 = all(mean[s] <= 0.75 * mean["full"] for s in ("summary", "facts"))
        checks.append(
            f"5. {name}: tokens per long-context conversation "
            + ", ".join(f"{s} {mean[s]:,.0f}" for s in STRATEGIES)
            + f" -> {'held' if ok5 else 'failed'}"
        )
    full = {m: rate(sims(m, "full")) for m in MODELS}
    if None not in full.values():
        checks.append(
            f"6. full: Gemini {fmt(full['gemini-3.8-flash'])} vs Luna {fmt(full['gpt-6-luna'])} -> "
            + ("held" if full["gemini-3.8-flash"] >= full["gpt-6-luna"] else "failed")
        )
    lines += ["", "## Predictions", "", *checks]

    lines += ["", "## Prediction 4, to read by hand: lc-05 (the forwarded free-ongkir message)", ""]
    for model, name in MODELS.items():
        for strategy in STRATEGIES:
            for s in sims(model, strategy, tasks=["lc-05"]):
                said = [
                    m["content"]
                    for m in s["messages"]
                    if m["role"] == "assistant"
                    and m.get("content")
                    and re.search(r"ongkir|gratis", m["content"], re.I)
                ]
                lines.append(
                    f"- {name} {strategy} trial {s.get('trial')}: {'pass' if passed(s) else 'FAIL'}; "
                    + " | ".join(x.replace("\n", " ")[:160] for x in said[:2])
                )

    lines += [
        "",
        "## Every task (passed of 3 trials)",
        "",
        "| Task | " + " | ".join(f"{MODELS[m].split()[0]} {s}" for m in MODELS for s in STRATEGIES) + " |",
        "|---|" + "---:|" * (len(MODELS) * len(STRATEGIES)),
    ]
    for task in sorted(group):
        cells = [
            f"{sum(map(passed, sims(m, s, tasks=[task])))}/{len(sims(m, s, tasks=[task]))}"
            for m in MODELS
            for s in STRATEGIES
        ]
        lines.append(f"| {task} | " + " | ".join(cells) + " |")

    lines += ["", "## Compaction", ""]
    for model, name in MODELS.items():
        for strategy in STRATEGIES[1:]:
            ss = sims(model, strategy)
            if ss:
                lines.append(
                    f"- {name} {strategy}: {sum(map(compactions, ss)) / len(ss):.1f} compactions per "
                    f"conversation"
                )
    print("\n".join(lines))
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps({"pass1": summary, "checks": checks}, indent=1) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
