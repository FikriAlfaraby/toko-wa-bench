"""English that stops before the end of its line: a trailing comma, or a last word that never ends an
English sentence ("…pass it on to the")."""

import re

from toko_wa.meaning.text import EMOJI, IC, STOP

# Words no English sentence ends with. A preposition may end a question ("Where should I send it to"),
# so prepositions count only when the sentence does not open with a question word.
_ARTICLE_END = re.compile(
    r"\b(?:the|a|an|and|or|your|my|our|their|than|but|if|as|is|are|was|were|will|be)$", IC
)
_PREPOSITION_END = re.compile(r"\b(?:to|of|with|for|in|on|at|by|from|into)$", IC)
_QUESTION_START = re.compile(r"(?:^|[.!?]\s+)(?:what|where|when|who|whom|whose|which|why|how)\b[^.!?]*$", IC)


def _tail(text: str) -> str:
    return re.sub(r"[\s*_`]+$", "", EMOJI.sub(" ", text.replace(STOP, " ")).rstrip())


def _dangling(text: str) -> bool:
    return bool(
        _ARTICLE_END.search(text) or (_PREPOSITION_END.search(text) and not _QUESTION_START.search(text))
    )


def cut_short(line: str, gloss: str) -> list[str]:
    said, wrote = _tail(line), _tail(gloss)
    if _dangling(wrote) and not _dangling(said):
        return ["the gloss stops before the end of the line"]
    if not re.search(r"[.?!)\"”']$", said):
        return []
    if re.search(r"[,;—–-]$", wrote) or (
        wrote.endswith(":") and not re.search(r"\bberikut\b|antara lain", line, IC)
    ):
        return ["the gloss stops before the end of the line"]
    return []
