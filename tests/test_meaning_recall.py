"""How much of a change of meaning the checks catch on the real English lines: each line is changed one
way at a time (a not taken out, a not put in, a question made a statement, a statement made a
question) and the checks must flag the changed line. The README quotes these floors."""

import json
import re

import pytest

from toko_wa.glosses import load
from toko_wa.meaning import problems

FLOORS = {
    "a not taken out": 0.80,
    "a not put in": 0.95,
    "a question made a statement": 0.93,
    "a statement made a question": 0.93,
}
_NOT_IN = re.compile(
    r"\b(?:tidak|tdk|belum|blm|bukan|jangan|ga|gak|nggak|teu|tanpa|batal|habis|kosong)\b", re.IGNORECASE
)
_TAKE_OUT = [
    (
        r"\b(is|are|was|were|do|does|did|can|could|has|have|had|wo|should|would)n['’]t\b",
        lambda m: {"wo": "will"}.get(m.group(1), m.group(1)),
    ),
    (r"\bcannot\b", lambda m: "can"),
    (r"\bnot\s+", lambda m: ""),
    (r"\bno\s+(?=\w)", lambda m: "a "),
]


def _pairs() -> list[tuple[str, str]]:
    out = []
    for line, gloss in load().items():
        if not gloss:
            continue
        try:
            said, meant = json.loads(line), json.loads(gloss)
        except json.JSONDecodeError:  # text, or JSON with text after it
            out.append((line, gloss))
            continue
        if isinstance(said, dict) and isinstance(said.get("message"), str) and isinstance(meant, dict):
            out.append((said["message"], meant["message"]))
    return out


def _mutants(kind: str, pairs: list[tuple[str, str]]):
    for line, gloss in pairs:
        if kind == "a not taken out":
            for pattern, put in _TAKE_OUT:
                for m in re.finditer(pattern, gloss):
                    changed = gloss[: m.start()] + put(m) + gloss[m.end() :]
                    if changed != gloss:
                        yield line, changed
        elif kind == "a not put in" and not _NOT_IN.search(line):
            m = re.search(r"\b(?:is|are|was|were|can|will|has|have)\b", gloss)
            if m:
                yield line, gloss[: m.end()] + " not" + gloss[m.end() :]
        elif kind == "a question made a statement" and "?" in line and gloss.rstrip().endswith("?"):
            yield line, gloss.rstrip()[:-1] + "."
        elif (
            kind == "a statement made a question" and "?" not in line + gloss and gloss.rstrip().endswith(".")
        ):
            yield line, gloss.rstrip()[:-1] + "?"


@pytest.mark.parametrize("kind", list(FLOORS))
def test_the_checks_catch_a_change_of_meaning_in_real_lines(kind):
    mutants = list(_mutants(kind, _pairs()))
    caught = sum(bool(problems(line, gloss)) for line, gloss in mutants)
    assert len(mutants) > 500
    assert caught / len(mutants) >= FLOORS[kind], f"{kind}: {caught} of {len(mutants)}"
