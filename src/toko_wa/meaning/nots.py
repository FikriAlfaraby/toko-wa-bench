"""A not lost or added. Indonesian says many nots English says with other words, and says some
things with a not that English says without one; both sides are listed here with the English each
may take, and each is checked in its own sentence."""

import re

from toko_wa.meaning.text import ADDRESS, IC, aligned, clauses, sentences, units

_NO = r"(?:tidak|tdk|ga|gak|nggak|ngga|enggak|engga|gk|ndak|nda)"
# Nots English says with other words: (the line, the English it may take, the problem).
IDIOMS = [
    (
        rf"\b{_NO}\s+(?:apa-apa|apa2|papa|masalah)\b|\b{_NO}\s+ada\s+masalah\b|\b(?:gapapa|gpp)\b",
        r"\bfine\b|\bok(?:ay)?\b|alright|all right|no (?:problem"
        r"|worries|issue)|not a problem|doesn['’]t matter|no harm"
        r"|no big deal|all good|\bcool\b",
        "the line says it's fine (tidak apa-apa) and the gloss does not",
    ),
    (
        r"\b(?:jangan|jgn)\s+(?:ragu|sungkan|segan)\b",
        r"feel free|(?:don['’]t|do not) hesitate|free to",
        "the line says feel free (jangan ragu) and the gloss does not",
    ),
    (
        r"\b(?:jangan|jgn)\s+lupa\b",
        r"remember|(?:don['’]t|do not) forget|be sure|make sure",
        "the line says don't forget (jangan lupa) and the gloss does not",
    ),
    (
        rf"\b(?:jangan|jgn)\s+(?:khawatir|kuatir)\b|\b{_NO}\s+perlu\s+khawatir\b",
        r"(?:don['’]t|do not|no need to|not to|never) worry"
        r"|rest assured|no worries|no problem|nothing to worry",
        "the line says don't worry and the gloss does not",
    ),
    (
        rf"\b{_NO}\s+(?:salah|keliru)\b",
        r"\bright\b|correct|accurate|make sure|\bsure\b|(?:n['’]t"
        r"|\bnot\b|\bno\b|avoid\w*)[^.!?]{0,40}\b(?:wrong|mistake\w*)",
        "the line says right (tidak salah) and the gloss does not",
    ),
    (
        rf"\b{_NO}\s+lama\b",
        r"soon|quick\w*|short\w*|not (?:for )?long|won['’]t (?:take"
        r"|be) long|shortly|moment|minute|\ba bit\b|\bjust\b",
        "the line says soon (ga lama) and the gloss does not",
    ),
    (
        r"\bbelum lama\b",
        r"recent\w*|just|while ago|not long ago|lately",
        "the line says recently (belum lama) and the gloss does not",
    ),
    (
        rf"\b{_NO}\s+usah\b|\bgausah\b",
        r"no need|(?:don['’]t|do not) need|(?:don['’]t|do not) have to"
        r"|that['’]s ok|fine|(?:don['’]t|do not) bother"
        r"|not necessary|never ?mind|it['’]s ok|no thanks|(?:don['’]t|do not) worry|skip",
        "the line says no need (ga usah) and the gloss does not",
    ),
    (
        rf"\b{_NO}\s+(?:sampai|sampe)\s+(?=\d|Rp)",
        r"under|less than|fewer than|within|not even|below",
        "the line says under (tidak sampai) and the gloss does not",
    ),
    (
        rf"\b{_NO}\s+lebih\s+dari\s+(?=\d|Rp)",
        r"at (?:the )?most|up to|no more than|not more than|maximum|max\b|or less",
        "the line says at most (tidak lebih dari) and the gloss does not",
    ),
]
NOT_IDIOM = re.compile("|".join(f"(?:{said})" for said, _, _ in IDIOMS), IC)
_STOCK_OUT = r"(?:habis|abis|kosong|ludes|kehabisan)"
# Nots and the like the English may say with one particular word, checked in their own sentence.
PAIRS = [
    (
        r"\b(?:ga|gak|nggak|ngga|enggak|engga|gk|tidak|tdk|ndak|belum|blm)\s+jadi\b",
        # the words that carry a not come first, so "won't … after all" uses up the won't
        r"won['’]t|will not|no longer|cancel\w*|changed? (?:my"
        r"|your|our|their|his|her) mind|never ?mind|decided against"
        r"|call(?:ed)? (?:it )?off|drop\w*|\boff\b|scratch that|after all|\bnot\b|n['’]t\b|\bno\b",
        "the line calls something off (ga jadi) and the gloss does not",
    ),
    (
        r"\bbelum\s+termasuk\b",
        r"exclud\w*|not (?:yet )?includ\w*|before|without|plus|on top"
        r"|n['’]t\b|to be added|still to|extra|additional|separate",
        "the line says not yet included and the gloss does not",
    ),
    (
        r"\b(?:tidak|tdk|ga|gak|nggak|belum)\s+(?:sama|sesuai|cocok)\b",
        r"differ\w*|mismatch\w*|wrong|incorrect|\bnot\b|n['’]t\b|short|\boff\b",
        "the line says something does not match and the gloss does not",
    ),
    (
        rf"\b(?:stok\w*|ukuran|size|warna|varian)\b[^.!?\n]{{0,30}}\b{_STOCK_OUT}\b|\b{_STOCK_OUT}\b[^.!?\n]{{0,12}}\bstok\w*"
        rf"|(?-i:\b(?:XS|S|M|L|XL|XXL)\b)[^.!?\n]{{0,15}}\b{_STOCK_OUT}\b"
        r"|\bsold out\b|\b(?:euweuh|gada|gaada)\s+stok\w*",
        r"\bout\b|sold out|ran out|run out|none left|unavailable|empty|gone|\bno\b|\bnot\b|n['’]t\b",
        "the line says out of stock and the gloss does not",
    ),
    (
        r"\b(?:tidak|tdk|ga|gak|nggak)\s+(?:berlaku|valid|aktif)\b",
        r"expired|invalid|inactive|no longer|\bnot\b|n['’]t\b",
        "the line says not valid and the gloss does not",
    ),
    (
        r"\btanpa\b",
        r"without|w/o|\bsans\b|\bno\b|\bnot\b|n['’]t\b|free|minus|exclud\w*|until|unless",
        "the line says without (tanpa) and the gloss does not",
    ),
    (
        r"\bdibatalkan\b|\bbatal\b",
        r"no longer|cancel\w*|void|called off|drop\w*|stop\w*"
        r"|gave up|changed? (?:my|your|our|their|his|her) mind"
        r"|decided against|scrap\w*|axed",
        "the line says cancelled and the gloss does not",
    ),
    (
        r"\bberakhir\b",
        r"\bend\w*|expired|over\b|closed|no longer|finish\w*|run its course|wrapped up",
        "the line says ended and the gloss does not",
    ),
    (
        r"\b(?:menolak|ditolak|tolak)\b",
        r"won['’]t|will not|refus\w*|declin\w*|reject\w*"
        r"|turn\w*\b.{0,30}\bdown|den(?:y|ies|ied)|\bnot\b|n['’]t\b|\bno\b",
        "the line says refused and the gloss does not",
    ),
    (
        r"\bnanti\s+dulu\b",
        r"not (?:right )?now|not yet|later|hold on|wait|think (?:about )?it|let me think",
        "the line says not now (nanti dulu) and the gloss does not",
    ),
    (
        r"\b(?:kalau|kalo|klo|jika)\s+(?:belum|blm|tidak|tdk|ga|gak|nggak|enggak)\b(?=\s*[,.]|\s*$)",
        r"otherwise|if not|or else|\bnot\b|n['’]t\b|\bno\b",
        "the line says otherwise (kalau belum) and the gloss does not",
    ),
    # not yet, said as "still waiting", "awaiting payment", "in transit"
    (
        r"\b(?:belum|blm|belom)\s+(?:dibayar|bayar|lunas|sampai|sampe"
        r"|tiba|diproses|selesai|dikirim|ada kabar|ada update)\b",
        r"awaiting|waiting|pending|in transit|on (?:its|the) way"
        r"|in progress|partial|unsettled|unpaid|outstanding|\bnot\b"
        r"|n['’]t\b|\bno\b",
        "the line says not yet and the gloss does not",
    ),
    # said without a not in Indonesian, often with one in English
    (
        r"\bdaripada\b",
        r"n['’]t\b|\bnot\b|instead|rather|than|so that|avoid",
        "the line says rather than (daripada) and the gloss does not",
    ),
    (
        r"\bkurang\s+(?:suka|cocok|paham|jelas|tahu|tau|yakin|pas|bagus|nyaman)\b",
        r"n['’]t\b|\bnot\b|dislike|less|unsure|unclear|uncomfortable|poor\w*|\bbad\b",
        "the line says not quite (kurang) and the gloss does not",
    ),
    (
        r"\btakut\b",
        r"afraid|worr\w*|fear\w*|scared|n['’]t\b|\bnot\b|avoid",
        "the line says afraid (takut) and the gloss does not",
    ),
    (
        r"\b(?:kalau|kalo|jika|bila)\s+berkenan\b",
        r"(?:don['’]t|do not) mind|if you(?:['’]d)? like|willing"
        r"|if (?:it['’]s|that['’]s) (?:ok|okay|fine)|if you wish|please|works? for you|alternatively"
        r"|suits? you"
        r"|convenient",
        "the line says if you're willing (kalau berkenan) and the gloss does not",
    ),
    (
        r"\bpaling\s+lambat\b",
        r"no later than|no more than|at the latest|\bby\b|within|latest|before|deadline",
        "the line says at the latest (paling lambat) and the gloss does not",
    ),
]
# A not that only asks: "bisa ga dikirim" (can it be shipped?), "ada gak", "aya teu"; read so only
# in a sentence that ends with "?" or with no mark. "udah transfer belum?" asks with its last word.
ASKING_NOT = re.compile(
    r"\b(?:bisa|bs|boleh|ada|aya|mau|ready)\s+(?:\w+\s+)?(?:ga|gak|nggak|ngga|enggak|engga|gk|teu)\b", IC
)
_TAG_NOT = re.compile(
    rf"\b(?:belum|blm|belom|ga|gak|nggak|ngga|enggak|engga|gk|tidak|teu|bukan|bkn)(?:\s+(?:ya|sih|{ADDRESS}))*+\s*\?",
    IC,
)
DONE_YET = re.compile(
    rf"\b(?:udah|sudah|udh|sdh|tos)\b[^,;]*\b(?:belum|blm|belom)(?:\s+(?:ya|sih|{ADDRESS}))*+\s*$"
    r"|\b(?:udah|sudah|udh|sdh|tos)\s+\w+\s+(?:belum|blm|belom)\b",
    IC,
)
_NOT_WORD = re.compile(
    r"\b(?:tidak|tdk|tdak|tak|belum|blm|belom|bukan|bkn|jangan|jgn|teu|henteu|moal|mboten|boten|ora|ndak|nda|kagak|kaga"
    r"|gaada|gada|gabisa|gamau|gaboleh|gabole|euweuh|ulah)\b"
    r"|\btong\s+(?=\w)|\bg\s+(?=bisa|ada|mau|boleh|jadi|usah)|\bgx\b"
    r"|\b(?:ga|gak|nggak|ngga|ngak|nggk|enggak|engga|enggk|gk)\s+(?!(?:yg|yang|sih|ya|deh|nih|dong|kok|kak|ka|gan|min)\b)[a-z]",
    IC,
)
# In Sundanese, can (teu acan) is "not yet"; read so only in a Sundanese line.
SUNDANESE = re.compile(
    r"\b(?:tiasa|punten|muhun|mangga|abdi|nuhun|kumaha|upami|kanggo|nganggo|dinten|hoyong|badé|bade|ayeuna|parantos"
    r"|atuh|wae|hiji|tilu|pikeun|nalika|anu|sareng|kalayan|saméméh|teu|didamel|dijieun|ditetepkeun|wartosan)\b",
    IC,
)
_NOT_YET_SUNDANESE = re.compile(r"\bcan\b|(?<!teu )\bacan\b", IC)  # "teu acan" is one not
# Ga on its own at the start of a clause answers "no".
_NO_ANSWER = re.compile(r"^(?:ga|gak|nggak|ngga|enggak|engga|gk)\b", IC)
EN_NOT = re.compile(
    r"\b(?:not|no|never|none|nothing|nobody|nowhere|cannot|neither|without|nope)\b|n['’]t\b", IC
)
_EN_NOT_WORD = re.compile(
    r"\b(?:invalid|incorrect|inactive|incomplete|unavailable|unable|unpaid|unreadable|unclear|unknown|unsure|undecided"
    r"|uncertain|unconfirmed|unverified|unregistered|unlisted|unsupported|impossible|missing|different|differs|expired"
    r"|pending|outstanding|excluding|instead|fail\w*|lack\w*"
    r"|yet to|uncomfortable|unhappy|unsatisfied|dissatisfied"
    r"|inconvenien\w*|opaque|short|off-limits)\b"
    r"|\bnon-\w|\bout of stock\b|\bsold out\b|\bran out\b|\brun out\b"
    r"|\bhold off\b|\blocked out\b|\bn/a\b|\boff the table\b",
    IC,
)
# English words that answer an Indonesian word that is not a not: different for beda, wrong for salah.
_ANSWERS = [
    (r"\b(?:beda|berbeda|lain|lainnya)\b", r"\bdiffer\w*"),
    (r"\b(?:salah|keliru)\b", r"\bwrong\b|\bincorrect\b"),
    (r"\b(?:gagal)\b", r"\bfail\w*"),
    (r"\b(?:kurang|sisa)\b", r"\bshort\b|\black\w*|\bmissing\b|\boutstanding\b"),
    (r"\b(?:menunggu|tertunda|diproses|proses)\b", r"\bpending\b"),
    (r"\b(?:hilang)\b", r"\bmissing\b"),
    (r"\b(?:kedaluwarsa|kadaluarsa|kadaluwarsa)\b", r"\bexpired\b"),
    (r"\b(?:saja|aja|ganti|gantinya)\b", r"\binstead\b"),
]
# "tracking no.", "No. 18", "No Pesanan": a number, not a not.
NUMBER_NO = re.compile(
    r"\b(?:tracking|order|account|phone|reference|ref|receipt|serial|item|invoice|house|unit|room)\s+no\b[.·]?"
    r"|\bno[.·]\s*|\bno\s*(?=\d)|\bno\s+(?=pesanan|resi|rekening|rek|hp|telp|telepon|wa|referensi|polisi|urut|antrian)",
    IC,
)
# English that says not where the line has none: "no problem", "don't hesitate", "…, wasn't it?",
# and one not said again over "and"/"or" ("No order has been changed, and no payment confirmed").
_EN_IDIOM = re.compile(
    r"\bno (?:problem|worries|need|rush|big deal|issue)\b|\bnot (?:at all"
    r"|a problem)\b|\bdon['’]t (?:hesitate|forget|worry|mention it)\b"
    r"|\bcan['’]t wait\b|\bnever ?mind\b|\bno (?:later|earlier"
    r"|more|less|fewer) than\b|\bnot only\b|\bwhy not\b|\bnot bad\b"
    r"|,\s*(?:is|was|are|were|do|does|did|wo|ca|have|has|had|should|would|could)n['’]t\s+(?:it|they|you|he|she|we|there|that)\b"
    r"|\b(?:and|or)\s+(?:no|not|never)\b|\bnor\b",
    IC,
)


_GENERIC = {r"\bnot\b", r"n['’]t\b", r"\bno\b"}


def _own_word(meant: str, english: str) -> re.Match | None:
    """The first of a pair's own English words, in the order the pair lists them, that the English
    uses ("without" before "free" for tanpa)."""
    for alternative in _specific(meant).split("\x00"):
        match = re.search(alternative, english, IC)
        if match:
            return match
    return None


def _specific(meant: str) -> str:
    """A pair's English alternatives without the plain nots that answer any pair, joined by NUL so
    each can be tried in turn."""
    alternatives, depth, start = [], 0, 0
    for i, ch in enumerate(meant):
        if ch == "(" and (i == 0 or meant[i - 1] != "\\"):
            depth += 1
        elif ch == ")" and meant[i - 1] != "\\":
            depth -= 1
        elif ch == "|" and depth == 0:
            alternatives.append(meant[start:i])
            start = i + 1
    alternatives.append(meant[start:])
    kept = [a for a in alternatives if a not in _GENERIC]
    return "\x00".join(kept) if kept else r"(?!)"


def _strip_asking(text: str) -> tuple[str, int]:
    """The text with the nots that only ask set aside, and how many there were."""
    out, asking = [], 0
    for body, end in sentences(text):
        if end in ("?", ""):
            body, n = ASKING_NOT.subn(lambda m: m.group(0).split()[0], body)
            asking += n
            body, n = _TAG_NOT.subn("?", body + ("?" if end == "?" else ""))
            asking += n
        kept = []
        for clause in clauses(body):
            done_yet = DONE_YET.search(clause)
            if done_yet and end in ("?", ""):
                asking += 1
                clause = clause[: done_yet.start()] + re.sub(
                    r"\b(?:belum|blm|belom)\b", " ", done_yet.group(0), flags=IC
                )
            kept.append(clause)
        out.append(", ".join(kept))
    return ". ".join(out), asking


def _count_said(text: str, sundanese: bool) -> int:
    n = 0
    for body, _ in sentences(text):
        for clause in clauses(body):
            n += len(_NOT_WORD.findall(clause)) + bool(
                _NO_ANSWER.search(clause) and not _NOT_WORD.match(clause)
            )
            n += len(_NOT_YET_SUNDANESE.findall(clause)) if sundanese else 0
    # English nots inside an Indonesian line ("Need verify not available") count too
    return n + len(EN_NOT.findall(NUMBER_NO.sub(" ", text)))


def _piece(said: str, wrote: str, sundanese: bool) -> tuple[list[str], int, int, int]:
    """(problems, nots the line says, nots the English says, nots the English adds beyond what the
    line's idioms and pairs allow) for one piece."""
    # "menolak/tidak melayani": two words for one not
    said = re.sub(r"\b\w+/(?=(?:tidak|tdk|ga|gak|belum)\b)", "", said, flags=IC)
    found = [
        problem for s, meant, problem in IDIOMS if re.search(s, said, IC) and not re.search(meant, wrote, IC)
    ]
    text, idioms = NOT_IDIOM.subn(" ", said)
    english = NUMBER_NO.sub(" ", wrote)
    pairs = 0
    for s, meant, problem in PAIRS:
        where = re.search(s, text, IC)
        if where:
            pairs += 1
            # A pair that says not ("belum sesuai") takes the plain not nearest the place it stands in
            # its sentence ("…, tetapi belum sesuai" is the later not); one that does not ("batal")
            # takes its own word ("canceled"), and a plain not only when that is missing.
            at = where.start() / max(len(text), 1)
            plain_nots = list(re.finditer(r"\bnot\b|n['’]t\b|\bno\b", english, IC))
            nearest = min(plain_nots, key=lambda m: abs(m.start() / max(len(english), 1) - at), default=None)
            own = _own_word(meant, english)
            if _NOT_WORD.search(where.group(0)) and not re.search(
                r"\bjadi\b|habis|abis|kosong|ludes", where.group(0), IC
            ):
                match = nearest or own
            else:
                match = own or (nearest if re.search(meant, english, IC) else None)
            if not match:
                found.append(problem)
            else:  # the English word that answers a pair answers no other not
                english = english[: match.start()] + " " + english[match.end() :]
            text = re.sub(s, " ", text, flags=IC)
    for indonesian, word in _ANSWERS:
        if re.search(indonesian, text, IC):
            english = re.sub(word, " ", english, count=1, flags=IC)
    text, asking = _strip_asking(text)
    if "(" not in english:  # a not repeated in brackets the English leaves out
        text = re.sub(r"\([^()]*\)", " ", text)
    said_nots = _count_said(text, sundanese)
    strong = len(EN_NOT.findall(english))
    # "isn't available or listed", "can't … until it is chosen": one English not for two
    joined = len(re.findall(r"(?:\bnot\b|n['’]t\b)[^.!?;]*?\b(?:or|nor)\b", english, IC))
    joined += len(re.findall(r"\b(?:until|unless)\b", english, IC))
    wrote_nots = strong + len(_EN_NOT_WORD.findall(english)) + joined
    # a pair already took its English word above, so only idioms and asking nots excuse a not here
    added = strong - len(_EN_IDIOM.findall(english)) - (said_nots + idioms + asking)
    return found, said_nots, wrote_nots, added


def nots(said: str, wrote: str) -> list[str]:
    """A not missing from its sentence, or added to one. A sentence may say two nots with one
    ("isn't available or listed"); a not may move into the next sentence when the English draws the
    line between sentences elsewhere."""
    sundanese = bool(SUNDANESE.search(said))
    found = []
    for line in aligned(said, wrote):
        pieces = [_piece(a, b, sundanese) for a, b in line]
        for i, ((problems, said_n, wrote_n, added), (a, b)) in enumerate(zip(pieces, line, strict=True)):
            found += problems
            neighbours = [pieces[j] for j in (i - 1, i + 1) if 0 <= j < len(pieces)]
            # a sentence keeps every not (two joined by "or" count as kept); a piece of several
            # sentences the English joined differently may lose one
            several = len(units(a)) > 1 and len(units(b)) != len(units(a))
            if said_n and (not wrote_n or wrote_n < said_n - (1 if several else 0)):
                if not any(n_wrote > n_said for _, n_said, n_wrote, _ in neighbours):
                    found.append("the line says not (belum, bukan, tidak…) and the gloss does not")
            if added > 0 and not any(n_said > n_wrote for _, n_said, n_wrote, _ in neighbours):
                found.append("the gloss says not and the line does not")
    return found
