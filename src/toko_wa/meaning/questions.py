"""A statement turned into a question, or a question into a statement. Indonesian chat often asks
without a "?", and "ya" may only soften a sentence or ask "…, okay?"; English may split one question
in two, ask for a choice ("JNE or J&T?"), or say a request as a polite question."""

import re

from toko_wa.meaning.nots import ASKING_NOT, DONE_YET, NOT_IDIOM
from toko_wa.meaning.text import ADDRESS, IC, TAG, clauses, sentences

_GA = r"(?:ga|gak|nggak|ngga|enggak|engga|gk)"
QUESTION_WORD = re.compile(
    r"\b(?:berapa|brp|kapan|kpn|gimana|gmn|bagaimana|apakah|kenapa|knp|mengapa|dimana|di mana|kemana|mana"
    r"|siapa|sapa|apa(?![-\s]*(?:apa|aja|saja|pun|adanya|lagi)\b)|sabaraha|naon|iraha|kumaha|saha|piro|opo|endi|pundi)\b"
    rf"|\bapa\s+(?:aja|saja)(?:\s+(?:ya|sih|skrg|sekarang|{ADDRESS}))*+\s*$|^masa\b|\bkan\b"
    rf"|\b{_GA}(?:\s+(?:sih|ya|{ADDRESS}))*+\s*$|\b(?:ga|gak|nggak)\s+(?:yg|yang|sih)\b",
    IC,
)
# The question words and forms a line cannot drop: an English line for "bisa COD ga kak" must ask.
_PLAIN_QUESTION = re.compile(
    r"\b(?:berapa|brp|kapan|kpn|gimana|gmn|bagaimana|apakah"
    r"|kenapa|knp|mengapa|dimana|di mana|siapa|sabaraha|naon"
    r"|iraha|kumaha)\b"
    rf"|\b{_GA}(?:\s+(?:sih|ya|{ADDRESS}))*+\s*$|\bapa(?:\s+(?:aja|saja))?(?:\s+{ADDRESS})?+\s*$",
    IC,
)
# A question word inside a statement: "menanyakan apakah …" (asks whether …).
_EMBEDDED = re.compile(
    r"\b(?:menanyakan|nanya|tanya|bertanya|mengecek|cek|memastikan|pastikan|tahu|tau|lihat|liat|konfirmasi)\b.*"
    r"\b(?:apakah|berapa|brp|kapan|bagaimana|gimana|siapa|dimana|di mana|apa)\b",
    IC,
)
# "kok blm nyampe" (why hasn't it arrived): a question even before a full stop; "ga lama kok" only stresses.
_WHY = re.compile(r"\bkok\s+(?!(?:kak|ka|gan|sis|mas|mbak|ya|sih)\b)\w", IC)
_ENDS_ASKING = re.compile(
    rf"\b(?:bisa|bs|boleh|ready|ada|aya|kah|sama|masih)(?:\s+(?:ga|gak|nggak|sih|{ADDRESS}))*+\s*$", IC
)
_OPENS_ASKING = re.compile(
    rf"^(?:{ADDRESS}\s*,?\s*)?(?:ada|aya|bisa|boleh|masih|msh|ready|mau|udah|sudah|jadi|beneran|bener)\b", IC
)
_ENDS_TAG = re.compile(rf"\b{TAG}\s*$", IC)
_LINE_REQUEST = re.compile(
    r"\b(?:mohon|tolong|minta|konfirmasi\w*|pilih\w*|kabari\w*|kabarin|infokan|diinfokan|info|kirim\w*|balas|silakan"
    r"|share|cek)\b",
    IC,
)
# A request the line makes of the reader: a request word, or a verb that opens the clause.
_LINE_ASKS_READER = re.compile(
    r"\b(?:tolong|minta|mohon|dong|silakan|coba|bantu\w*|dibantu|kabari\w*|kabarin|balas|bales|konfirmasi\w*|aja|saja)\b"
    r"|^(?:kirim\w*|pilih\w*|ganti|cek\w*|tunggu|ketik\w*|isi|transfer)\b",
    IC,
)
_LINE_ASKS_LEAVE = re.compile(r"\b(?:boleh|izin|bisa saya|bisa kami|saya boleh|kami boleh)\b", IC)
_EN_TAG_QUESTION = re.compile(
    r"(?:^|[,—–-][\"”’']?)\s*(?:okay|ok|right|yeah|yes|alright|all right|correct|got it|sound good|good|deal"
    r"|is that (?:okay|ok|alright|all right|fine|right)|does that work)\s*$"
    r"|,\s*(?:is|was|are|were|do|does|did|wo|ca|have|has|had)n['’]t\s+(?:it|they|you|he|she|we|there|that)\s*$"
    r"|^(?:is that (?:okay|ok|alright|all right|fine|right)|does that work|okay|right|deal)\s*$",
    IC,
)
_EN_REQUEST = re.compile(
    r"\b(?:please|kindly)\b|^(?:let (?:me|us) know|tell (?:me|us)|send|choose|pick|select|confirm|reply)\b",
    IC,
)
_EN_POLITE_YOU = re.compile(
    r"^(?:could|can|would|will) you\b|^(?:would you )?mind\b|^why not\b"
    r"|^(?:which|what)\b.*\b(?:would you like|do you want|would you prefer|do you prefer)\b",
    IC,
)
_EN_POLITE_ME = re.compile(r"^(?:could|can|may|shall) (?:i|we)\b", IC)
_EN_ASKING = re.compile(
    r"^(?:(?:so|and|but|oh|then|okay|ok|well|hmm),?\s+)?"
    r"(?:what|where|when|who|whom|whose|which|why|how|is|are|was|were|do|does|did|can|could|would|will|shall|should|may)\b",
    IC,
)


def _asks_without_mark(body: str, end: str) -> bool:
    """Whether a sentence the writer did not end with "?" may still ask."""
    if end in ("", "?") and (ASKING_NOT.search(body) or any(DONE_YET.search(c) for c in clauses(body))):
        return True
    if _WHY.search(body):
        return True
    if end:  # a full stop or "!" makes the rest a statement
        return False
    return bool(
        QUESTION_WORD.search(body)
        or _ENDS_ASKING.search(body)
        or _OPENS_ASKING.search(body)
        or re.search(r"\batau\b", body, IC)
    )


def _must_ask(body: str, end: str) -> bool:
    """Whether an unmarked sentence asks so plainly that its English must ask too. A sentence that
    ends with ":" introduces a list the question goes on after."""
    if end or body.rstrip().endswith(":") or _EMBEDDED.search(body):
        return False
    return bool(
        ASKING_NOT.search(body)
        or _WHY.search(body)
        or _PLAIN_QUESTION.search(body)
        or any(DONE_YET.search(c) for c in clauses(body))
    )


def questions(line: str, gloss: str) -> list[str]:
    said = sentences(NOT_IDIOM.sub(" ", line))
    # an English question the writer left without "?" ("What is your name") still asks
    wrote = [(body, "?" if not end and _EN_ASKING.search(body) else end) for body, end in sentences(gloss)]
    asked = sum(end == "?" for _, end in said)
    asks = sum(end == "?" for _, end in wrote)
    found = []
    requests_said = sum(
        (end == "?" or _must_ask(body, end)) and bool(_LINE_REQUEST.search(body)) for body, end in said
    )
    requests_wrote = sum(end != "?" and bool(_EN_REQUEST.search(body)) for body, end in wrote)
    must = asked + sum(end != "?" and _must_ask(body, end) for body, end in said)
    if asks + min(requests_said, requests_wrote) < must:
        found.append("the line asks a question the gloss does not")
    unmarked = sum(end != "?" and _asks_without_mark(body, end) for body, end in said)
    tags = sum(end != "?" and bool(_ENDS_TAG.search(c)) for body, end in said for c in clauses(body))
    tag_questions = sum(end == "?" and bool(_EN_TAG_QUESTION.search(body)) for body, end in wrote)
    # "Which courier? JNE or J&T?" for one question with atau
    choices = min(
        sum(end == "?" and " or " in f" {body} " and len(body.split()) <= 8 for body, end in wrote),
        sum(end == "?" and bool(re.search(r"\batau\b", body, IC)) for body, end in said),
    )
    # one question the English says in two: "Bagaimana Kak, apakah mau lanjut?" (What do you think? Go ahead?)
    split = sum(
        sum(
            bool(QUESTION_WORD.search(c) or ASKING_NOT.search(c) or _ENDS_TAG.search(c))
            for c in clauses(body)[:-1]
        )
        for body, end in said
        if end == "?"
    )
    # a request said as a polite question: "kirim fotonya ya" (Mind sending the photo?)
    polite = min(
        sum(end != "?" and any(_LINE_ASKS_READER.search(c) for c in clauses(body)) for body, end in said),
        sum(end == "?" and bool(_EN_POLITE_YOU.search(body)) for body, end in wrote),
    ) + min(
        sum(end != "?" and bool(_LINE_ASKS_LEAVE.search(body)) for body, end in said),
        sum(end == "?" and bool(_EN_POLITE_ME.search(body)) for body, end in wrote),
    )
    if asks - asked > unmarked + min(tags, tag_questions) + choices + split + polite:
        found.append("the gloss asks a question the line does not")
    return found
