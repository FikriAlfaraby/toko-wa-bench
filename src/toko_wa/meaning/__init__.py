"""Meaning checks for an English line written for an Indonesian one: what numbers, codes and names
cannot show. A not lost or added (nots.py), an opposite (opposites.py), a statement made a question
or the reverse (questions.py), a day, month, relative day, time of day, hour or span (when.py), and
English that stops before the end of its line (ending.py).

A message is compared line by line, and sentence by sentence where the English keeps the sentences,
so a not or an opposite must sit in the right sentence. The tests hold the checks to real lines and
to the wrong English two independent reviews wrote to slip past them. A JSON object is checked
string by string; a line that only starts like JSON is read as text.
"""

import json

from toko_wa.meaning import ending, nots, opposites, questions, text, when


def _text_problems(line: str, gloss: str) -> list[str]:
    said, wrote = text.plain(line), text.plain(gloss)
    found = nots.nots(said, wrote) + opposites.opposites(said, wrote) + questions.questions(said, wrote)
    found += when.when(text.LABELS.sub(" ", line), text.LABELS.sub(" ", gloss)) + ending.cut_short(
        line, gloss
    )
    return list(dict.fromkeys(found))


def _string_pairs(said: object, meant: object, path: str):
    if isinstance(said, str) and isinstance(meant, str):
        yield path, said, meant
    elif isinstance(said, dict) and isinstance(meant, dict):
        for key in said:
            if key in meant:
                yield from _string_pairs(said[key], meant[key], f"{path}.{key}" if path else key)
    elif isinstance(said, list) and isinstance(meant, list) and len(said) == len(meant):
        for i, (a, b) in enumerate(zip(said, meant, strict=True)):
            yield from _string_pairs(a, b, f"{path}[{i}]")


def problems(line: str, gloss: str) -> list[str]:
    """What the gloss gets wrong about the line's meaning."""
    if line.lstrip().startswith("{"):
        try:
            said, meant = json.loads(line), json.loads(gloss)
        except json.JSONDecodeError:
            return _text_problems(line, gloss)
        return [
            f"{path}: {p}"
            for path, a, b in _string_pairs(said, meant, "")
            if a != b
            for p in _text_problems(a, b)
        ]
    return _text_problems(line, gloss)
