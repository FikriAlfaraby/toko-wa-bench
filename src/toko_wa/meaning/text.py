"""How the meaning checks read a line and its English: plain text, sentences, clauses, and the pieces
of a message that face each other in the two languages."""

import re

IC = re.IGNORECASE
STOP = "###STOP###"
EMOJI = re.compile("[\U0001f000-\U0001faff\u2600-\u27bf\ufe0f~]+")
# A form of address, and a name after it written with a capital ("kak Dimas"). The name is matched
# case-sensitively and every repeat is possessive, so a run of "kak kak kak" cannot backtrack.
ADDRESS = (
    r"(?:kakak|kak|ka|mbak|mba|mas|gan|min|pak|bu|sis|bang|teh|akang|kang|om|tante)\b(?-i:\s+[A-Z][a-z]+)?+"
)
# A tag that ends a sentence and may soften it or ask "…, okay?"
TAG = rf"(?:ya+h?|nya|kan|kah|bukan|bkn)(?:\s+{ADDRESS})*+"
# Abbreviations whose full stop ends no sentence: "Jl. Kemang No. 18", "min. belanja".
_ABBREVIATION = re.compile(
    r"\b(No|Jl|Jln|Kav|Blok|Km|Lt|Rt|Rw|Kec|Kab|Kel|Gg|Komp|Hj|Dr|Mr|Mrs|Ms|St|Tlp|Telp|min|maks|max)\.", IC
)
# The note labels name both sides ("shop's promise or refusal"); they are not what a line says.
LABELS = re.compile(r"janji atau penolakan toko\s*:|shop['’]s promise or refusal\s*:", IC)


def plain(text: str) -> str:
    """The text as the checks read it: no labels, stop marker, emoji or Markdown emphasis; the dots
    and commas inside numbers and abbreviations made neutral, so Rp150.000 ends no sentence; runs of
    ? and ! read as one mark; and "…? (A / B)?" read as one question."""
    t = LABELS.sub(" ", EMOJI.sub(" ", text.replace(STOP, " ")))
    t = re.sub(r"[*_`]+", "", t)
    t = re.sub(r"(?<=\d)[.,:](?=\d)", "·", t)
    t = _ABBREVIATION.sub(r"\1·", t)
    t = re.sub(r"[?!]*\?[?!]*", "?", t)
    return re.sub(r"\?(\s*\([^()]*\))\?", r"?\1", t)


def sentences(text: str) -> list[tuple[str, str]]:
    """Each sentence as (body, end): end is ".", "!", "?" or "" when the writer left none."""
    return [
        (m.group(1).strip(), m.group(2)[:1])
        for m in re.finditer(r"([^.!?\n]+)([.!?]*)", text)
        if m.group(1).strip()
    ]


def clauses(body: str) -> list[str]:
    return [c.strip() for c in re.split(r"[,;—–]|\s-\s", body) if c.strip()]


def units(text: str) -> list[str]:
    """Sentences for aligning a line with its English, ";" counted as a sentence end on both sides."""
    return [m.group(0).strip() for m in re.finditer(r"[^.!?;\n]+[.!?;]*", text) if m.group(0).strip(" .!?;")]


def aligned(said: str, wrote: str) -> list[list[tuple[str, str]]]:
    """The pieces of a message that face each other, grouped by line: every gloss keeps the line
    breaks, so each line meets its own English; within a line, each sentence meets its own when both
    have as many, and otherwise the line is one piece. Pieces already in English are left out."""
    lines = (
        zip(said.split("\n"), wrote.split("\n"), strict=True)
        if said.count("\n") == wrote.count("\n")
        else [(said, wrote)]
    )
    out = []
    for a, b in lines:
        ua, ub = units(a), units(b)
        pairs = list(zip(ua, ub, strict=True)) if len(ua) == len(ub) else [(a, b)]
        out.append([(x, y) for x, y in pairs if x.strip() != y.strip()])
    return out


def dedup(items: list) -> list:
    """The items without a repeat of the one before."""
    return [d for i, d in enumerate(items) if i == 0 or items[i - 1] != d]
