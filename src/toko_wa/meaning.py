"""Meaning checks for an English line written for an Indonesian one: what numbers, codes and names
cannot show. A "not", a question or a statement, a day of the week or a relative day, the time of
day, a span of days or hours, and English that stops before the end of its line.

Indonesian chat leaves much unmarked: a question often has no "?" ("bisa ga kak"), "ya" may only
soften a sentence or ask "…, okay?", and many nots are idioms ("jangan ragu", feel free). Each check
knows those habits; the tests hold them to real lines, and to the wrong English an
independent review wrote to slip past them. A JSON object is checked string by string.
"""

import json
import re

_IC = re.IGNORECASE
STOP = "###STOP###"
_EMOJI = re.compile("[\U0001f000-\U0001faff☀-➿️~]+")
_ADDRESS = r"(?:kak|ka|kakak|mbak|mba|mas|gan|min|pak|bu|sis|bang|teh|akang|kang|om|tante)(?:\s+[A-Z][a-z]+)?"
_TAG = rf"(?:ya+h?|nya|kan|kah)(?:\s+{_ADDRESS})*"


def _plain(text: str) -> str:
    """The text as the checks read it: no stop marker, emoji or Markdown emphasis; the dots and commas
    inside numbers made neutral, so Rp150.000 ends no sentence; runs of ? and ! read as one mark; and
    "…? (A / B)?" read as one question."""
    t = _EMOJI.sub(" ", text.replace(STOP, " "))
    t = re.sub(r"[*_`]+", "", t)
    t = re.sub(r"(?<=\d)[.,:](?=\d)", "·", t)
    t = re.sub(r"[?!]*\?[?!]*", "?", t)
    return re.sub(r"\?(\s*\([^()]*\))\?", r"?\1", t)


def _sentences(text: str) -> list[tuple[str, str]]:
    """Each sentence as (body, end): end is ".", "!", "?" or "" when the writer left none."""
    return [
        (m.group(1).strip(), m.group(2)[:1])
        for m in re.finditer(r"([^.!?\n]+)([.!?]*)", text)
        if m.group(1).strip()
    ]


def _clauses(body: str) -> list[str]:
    return [c.strip() for c in re.split(r"[,;—–]|\s-\s", body) if c.strip()]


# --- not ------------------------------------------------------------------------------------------

_NO = r"(?:tidak|tdk|ga|gak|nggak|ngga|enggak|engga|gk|ndak|nda)"
# Nots English says with other words, each with the English it may take: tidak apa-apa (it's fine),
# jangan ragu (feel free), tidak salah (right), ga lama (soon), ga usah (no need), tidak sampai 2 jam
# (under 2 hours), belum lama (recently).
_IDIOMS = [
    (
        rf"\b{_NO}\s+(?:apa-apa|apa2|papa|masalah)\b|\b{_NO}\s+ada\s+masalah\b|\b(?:gapapa|gpp)\b",
        r"\bfine\b|\bok(?:ay)?\b|alright|all right|no (?:problem|worries)|not a problem"
        r"|doesn['’]t matter|no harm",
        "the line says it's fine (tidak apa-apa) and the gloss does not",
    ),
    (
        r"\b(?:jangan|jgn)\s+(?:ragu|sungkan|segan)\b",
        r"feel free|(?:don['’]t|do not) hesitate|free to",
        "the line says feel free (jangan ragu) and the gloss does not",
    ),
    (
        r"\b(?:jangan|jgn)\s+lupa\b",
        r"remember|(?:don['’]t|do not) forget|be sure",
        "the line says don't forget (jangan lupa) and the gloss does not",
    ),
    (
        rf"\b(?:jangan|jgn)\s+(?:khawatir|kuatir)\b|\b{_NO}\s+perlu\s+khawatir\b",
        r"worr\w*|rest assured|no need",
        "the line says don't worry and the gloss does not",
    ),
    (
        rf"\b{_NO}\s+(?:salah|keliru)\b",
        r"\bright\b|correct|accurate|wrong|mistake|make sure|sure",
        "the line says right (tidak salah) and the gloss does not",
    ),
    (
        rf"\b{_NO}\s+lama\b|\bbelum lama\b",
        r"soon|quick\w*|short\w*|recent\w*|not long|won['’]t take long|shortly|just",
        "the line says soon (ga lama) and the gloss does not",
    ),
    (
        rf"\b{_NO}\s+usah\b|\bgausah\b",
        r"no need|(?:don['’]t|do not) need|that['’]s ok|fine|(?:don['’]t|do not) bother|not necessary"
        r"|never ?mind|it['’]s ok|no thanks",
        "the line says no need (ga usah) and the gloss does not",
    ),
    (
        rf"\b{_NO}\s+(?:sampai|sampe)\s+(?=\d|Rp)",
        r"under|less than|fewer than|within|not even|below",
        "the line says under (tidak sampai) and the gloss does not",
    ),
    (
        rf"\b{_NO}\s+lebih\s+dari\s+(?=\d|Rp)",
        r"at most|up to|no more than|not more than|maximum|max\b|or less",
        "the line says at most (tidak lebih dari) and the gloss does not",
    ),
]
_NOT_IDIOM = re.compile("|".join(f"(?:{said})" for said, _, _ in _IDIOMS), _IC)
# A not that only asks: "bisa ga" (can or not), "ada gak", "aya teu", "udah transfer belum?".
_ASKING_NOT = re.compile(
    r"\b(?:bisa|bs|boleh|ada|aya|mau|udah|sudah|udh|sdh|tos|masih|jadi|ready)\s+"
    r"(?:ga|gak|nggak|ngga|enggak|engga|gk|tidak|teu|belum|blm)\b",
    _IC,
)
_TAG_NOT = re.compile(
    rf"\b(?:belum|blm|belom|ga|gak|nggak|ngga|enggak|engga|gk|tidak|teu)(?:\s+(?:ya|sih|{_ADDRESS}))*\s*\?",
    _IC,
)
_DONE_YET = re.compile(
    rf"\b(?:udah|sudah|udh|sdh|tos)\b.*\b(?:belum|blm|belom)(?:\s+(?:ya|sih|{_ADDRESS}))*\s*$"
    r"|\b(?:udah|sudah|udh|sdh|tos)\s+\w+\s+(?:belum|blm|belom)\b",
    _IC,
)
# Nots the English may say with one particular word, checked on their own.
_NOT_PAIRS = [
    (
        r"\b(?:ga|gak|nggak|ngga|enggak|engga|gk|tidak|tdk|ndak|belum|blm)\s+jadi\b",
        r"cancel\w*|changed? (?:my|your|our|their|his|her) mind|never ?mind|after all|no longer"
        r"|won['’]t|will not"
        r"|decided against|call(?:ed)? (?:it )?off|drop\w*|\bnot\b|n['’]t\b|\bno\b",
        "the line calls something off (ga jadi) and the gloss does not",
    ),
    (
        r"\bbelum\s+termasuk\b",
        r"exclud\w*|not includ\w*|before|without|plus|on top|n['’]t\b",
        "the line says not yet included and the gloss does not",
    ),
    (
        r"\b(?:tidak|tdk|ga|gak|nggak)\s+(?:sama|sesuai|cocok)\b",
        r"differ\w*|mismatch\w*|wrong|incorrect|\bnot\b|n['’]t\b",
        "the line says something does not match and the gloss does not",
    ),
    (
        r"\b(?:stok\w*|ukuran|size|warna|varian)\b[^.!?\n]{0,30}\b(?:habis|kosong)\b"
        r"|\b(?:habis|kosong)\b[^.!?\n]{0,12}\bstok\w*|\bsold out\b",
        r"out of stock|sold out|ran out|run out|none left|unavailable|empty|gone|\bno\b|\bnot\b|n['’]t\b",
        "the line says out of stock and the gloss does not",
    ),
    (
        r"\b(?:tidak|tdk|ga|gak|nggak)\s+(?:berlaku|valid|aktif)\b",
        r"expired|invalid|inactive|no longer|\bnot\b|n['’]t\b",
        "the line says not valid and the gloss does not",
    ),
    (
        r"\btanpa\b",
        r"without|\bno\b|\bnot\b|n['’]t\b|free|minus|exclud\w*",
        "the line says without (tanpa) and the gloss does not",
    ),
    (
        r"\bdibatalkan\b|\bbatal\b",
        r"cancel\w*|void|called off|drop\w*|stop\w*|gave up|changed? (?:my|your|our|their|his|her) mind"
        r"|decided against|no longer",
        "the line says cancelled and the gloss does not",
    ),
    (
        r"\bnanti\s+dulu\b",
        r"not (?:right )?now|not yet|later|hold on|wait",
        "the line says not now (nanti dulu) and the gloss does not",
    ),
    (
        r"\b(?:kalau|kalo|klo|jika)\s+(?:belum|blm|tidak|tdk|ga|gak|nggak|enggak)\b(?=\s*[,.]|\s*$)",
        r"otherwise|if not|or else|\bnot\b|n['’]t\b|\bno\b",
        "the line says otherwise (kalau belum) and the gloss does not",
    ),
    (
        r"\bberakhir\b",
        r"\bend\w*|expired|over\b|closed|no longer|finish\w*",
        "the line says ended and the gloss does not",
    ),
    (
        r"\b(?:menolak|ditolak|tolak)\b",
        r"refus\w*|declin\w*|reject\w*|turn\w* down|won['’]t|will not|\bnot\b|n['’]t\b|\bno\b",
        "the line says refused and the gloss does not",
    ),
]
_NOT_WORD = re.compile(
    r"\b(?:tidak|tdk|tak|belum|blm|belom|bukan|bkn|jangan|jgn|teu|henteu|moal|mboten|ora|ndak|nda|kagak|gaada|gabisa|gamau)\b"
    r"|\btong\s+(?=\w)"
    r"|\b(?:ga|gak|nggak|ngga|enggak|engga|gk)\s+(?!(?:yg|yang|sih|ya|deh|nih|dong|kok|kak|ka|gan|min)\b)[a-z]",
    _IC,
)
# In Sundanese, can (teu acan) is "not yet"; read so only in a Sundanese line.
_SUNDANESE = re.compile(
    r"\b(?:tiasa|punten|muhun|mangga|abdi|nuhun|kumaha|upami|kanggo|nganggo|dinten|hoyong|badé|bade|ayeuna|parantos"
    r"|atuh|wae|hiji|tilu|pikeun|nalika|anu|sareng|kalayan|saméméh|teu|didamel|dijieun|ditetepkeun|wartosan)\b",
    _IC,
)
_NOT_YET_SUNDANESE = re.compile(r"\b(?:can|acan)\b", _IC)
# Ga on its own at the start of a clause answers "no".
_NO_ANSWER = re.compile(r"^(?:ga|gak|nggak|ngga|enggak|engga|gk)\b", _IC)
_EN_NOT = re.compile(
    r"\b(?:not|no|never|none|nothing|nobody|nowhere|cannot|neither|nor|without)\b|n['’]t\b", _IC
)
_EN_NOT_WORD = re.compile(
    r"\b(?:invalid|incorrect|inactive|incomplete|unavailable|unable|unpaid|unreadable|unclear|unknown|unsure|undecided"
    r"|uncertain|unconfirmed|unverified|missing|different|differs|expired|pending|outstanding|excluding|except|instead"
    r"|wrong|fail\w*|lack\w*|yet to|uncomfortable|unhappy|unsatisfied|dissatisfied|inconvenien\w*|opaque)\b"
    r"|\bnon-\w|\bout of stock\b|\bsold out\b|\bran out\b|\brun out\b|\bhold off\b",
    _IC,
)
# "tracking no.", "No. 18": a number, not a not.
_NUMBER_NO = re.compile(
    r"\b(?:tracking|order|account|phone|reference|ref|receipt|serial|item|invoice|house|unit|room)\s+no\b\.?|\bno\.?\s*(?=\d)",
    _IC,
)
# English that says not where the line has none: "no problem", "don't hesitate".
_EN_IDIOM = re.compile(
    r"\bno (?:problem|worries|need|rush)\b|\bnot at all\b|\bdon['’]t (?:hesitate|forget|worry)\b"
    r"|\bcan['’]t wait\b"
    r"|\bnever ?mind\b|\bno later than\b|\bnot only\b",
    _IC,
)


def _nots(line: str, gloss: str) -> list[str]:
    found = [
        problem
        for said, meant, problem in _IDIOMS
        if re.search(said, line, _IC) and not re.search(meant, gloss, _IC)
    ]
    text, idioms = _NOT_IDIOM.subn(" ", line)
    text, asking = _ASKING_NOT.subn(lambda m: m.group(0).split()[0], text)
    text, tags = _TAG_NOT.subn("?", text)
    pairs = 0
    for said, meant, problem in _NOT_PAIRS:
        if re.search(said, text, _IC):
            pairs += 1
            if not re.search(meant, gloss, _IC):
                found.append(problem)
            text = re.sub(said, " ", text, flags=_IC)
    sundanese = bool(_SUNDANESE.search(line))
    english = _NUMBER_NO.sub(" ", gloss)
    said_total = 0
    # Line breaks are kept in every gloss, so each line of a message is compared with its own English,
    # sentence by sentence when both have as many sentences. A sentence may say two nots with one
    # ("isn't available or listed"), so each sentence needs a not, not as many.
    for part, wrote in (
        zip(text.split("\n"), english.split("\n"), strict=True)
        if text.count("\n") == english.count("\n")
        else [(text, english)]
    ):
        said_sentences = [
            sum(_count_nots(c, sundanese) for c in _clauses(body)) for body, _ in _sentences(part)
        ]
        wrote_sentences = [
            len(_EN_NOT.findall(body)) + len(_EN_NOT_WORD.findall(body)) for body, _ in _sentences(wrote)
        ]
        said_total += sum(said_sentences)
        pairs_of = (
            zip(said_sentences, wrote_sentences, strict=True)
            if len(said_sentences) == len(wrote_sentences)
            else [(sum(said_sentences), sum(wrote_sentences))]
        )
        if any(s and not w for s, w in pairs_of):
            found.append("the line says not (belum, bukan, tidak…) and the gloss does not")
            break
    strong = len(_EN_NOT.findall(english))
    if not said_total and not pairs and strong - len(_EN_IDIOM.findall(english)) > idioms + asking + tags:
        found.append("the gloss says not and the line does not")
    return found


def _count_nots(clause: str, sundanese: bool) -> int:
    done_yet = _DONE_YET.search(clause)
    if done_yet:  # "udah transfer belum": the belum asks
        clause = clause[: done_yet.start()] + re.sub(
            r"\b(?:belum|blm|belom)\b", " ", done_yet.group(0), flags=_IC
        )
    n = len(_NOT_WORD.findall(clause)) + bool(_NO_ANSWER.search(clause) and not _NOT_WORD.match(clause))
    return n + (len(_NOT_YET_SUNDANESE.findall(clause)) if sundanese else 0)


# --- questions ------------------------------------------------------------------------------------

_QUESTION_WORD = re.compile(
    r"\b(?:berapa|brp|kapan|kpn|gimana|gmn|bagaimana|apakah|kenapa|knp|mengapa|dimana|di mana|kemana|mana"
    r"|siapa|sapa"
    r"|apa(?![-\s]*(?:apa|aja|saja|pun|adanya|lagi)\b)|apa\s+(?:aja|saja)\s*$|sabaraha|naon|iraha|kumaha|saha|piro|opo|endi|pundi)\b"
    r"|^masa\b|\bkan\b"
    rf"|\b(?:ga|gak|nggak|ngga|enggak|engga|gk)(?:\s+(?:sih|ya|{_ADDRESS}))*\s*$|\b(?:ga|gak|nggak)\s+(?:yg|yang|sih)\b",
    _IC,
)
# "kok blm nyampe" (why hasn't it arrived): a question even before a full stop; "ga lama kok" only stresses.
_WHY = re.compile(r"\bkok\s+(?!(?:kak|ka|gan|sis|mas|mbak|ya|sih)\b)\w", _IC)
_ENDS_ASKING = re.compile(
    rf"\b(?:bisa|bs|boleh|ready|ada|aya|kah)(?:\s+(?:ga|gak|nggak|sih|{_ADDRESS}))*\s*$", _IC
)
_OPENS_ASKING = re.compile(rf"^(?:{_ADDRESS}\s*,?\s*)?(?:ada|aya|bisa|boleh|masih|msh|ready)\b", _IC)
_ENDS_TAG = re.compile(rf"\b{_TAG}\s*$", _IC)
_LINE_REQUEST = re.compile(
    r"\b(?:mohon|tolong|minta|konfirmasi\w*|pilih\w*|kabari\w*|kabarin|infokan|diinfokan|info|kirim\w*|balas|silakan|share|cek)\b",
    _IC,
)
_EN_TAG_QUESTION = re.compile(
    r"(?:^|[,—–-][\"”’']?)\s*(?:okay|ok|right|yeah|yes|alright|all right|correct|got it|sound good)\s*$", _IC
)
# A request said as a question ("Could you change the address?") for a request the line makes.
_EN_POLITE = re.compile(r"^(?:could|can|would|will) you\b|^(?:could|can|may) (?:i|we)\b", _IC)
_LINE_ASKS_FOR = re.compile(
    r"\b(?:tolong|minta|mohon|dong|aja|saja|kabari\w*|kabarin|kirim\w*|ganti|bantu\w*|dibantu|cek\w*|pilih\w*|balas|bales|konfirmasi\w*)\b",
    _IC,
)
_EN_REQUEST = re.compile(
    r"\b(?:please|kindly)\b|^(?:let (?:me|us) know|tell (?:me|us)|send|choose|pick|select|confirm|reply)\b",
    _IC,
)


def _asks_without_mark(body: str, end: str) -> bool:
    """Whether a sentence the writer did not end with "?" still asks."""
    if _ASKING_NOT.search(body) or _WHY.search(body) or any(_DONE_YET.search(c) for c in _clauses(body)):
        return True
    if end:  # a full stop or "!" makes the rest a statement
        return False
    return bool(
        _QUESTION_WORD.search(body)
        or _ENDS_ASKING.search(body)
        or _OPENS_ASKING.search(body)
        or re.search(r"\batau\b", body, _IC)
    )


def _questions(line: str, gloss: str) -> list[str]:
    said, wrote = _sentences(_NOT_IDIOM.sub(" ", line)), _sentences(gloss)
    asked = sum(end == "?" for _, end in said)
    asks = sum(end == "?" for _, end in wrote)
    found = []
    requests_said = sum(end == "?" and bool(_LINE_REQUEST.search(body)) for body, end in said)
    requests_wrote = sum(end != "?" and bool(_EN_REQUEST.search(body)) for body, end in wrote)
    if asks + min(requests_said, requests_wrote) < asked:
        found.append("the line asks a question the gloss does not")
    unmarked = sum(end != "?" and _asks_without_mark(body, end) for body, end in said)
    tags = sum(end != "?" and bool(_ENDS_TAG.search(c)) for body, end in said for c in _clauses(body))
    tag_questions = sum(end == "?" and bool(_EN_TAG_QUESTION.search(body)) for body, end in wrote)
    choices = sum(end == "?" and " or " in f" {body} " and len(body.split()) <= 8 for body, end in wrote)
    # one question the English says in two: "Bagaimana Kak, apakah mau lanjut?" (What do you think? Go ahead?)
    split = sum(
        sum(
            bool(_QUESTION_WORD.search(c) or _ASKING_NOT.search(c) or _ENDS_TAG.search(c))
            for c in _clauses(body)[:-1]
        )
        for body, end in said
        if end == "?"
    )
    polite = min(
        sum(end != "?" and bool(_LINE_ASKS_FOR.search(body) or _ENDS_TAG.search(body)) for body, end in said),
        sum(end == "?" and bool(_EN_POLITE.search(body)) for body, end in wrote),
    )
    if asks - asked > unmarked + min(tags, tag_questions) + choices + split + polite:
        found.append("the gloss asks a question the line does not")
    return found


# --- days, times of day, spans --------------------------------------------------------------------

_WEEKDAY = r"(?:senin|selasa|rabu|kamis|jum['’]?at|sabtu)"
_DAYS = [
    ("Monday", r"\bsenin\b", r"\bmon(?:day)?\b"),
    ("Tuesday", r"\bselasa\b", r"\btue(?:s|sday)?\b"),
    ("Wednesday", r"\brabu\b", r"\bwed(?:nesday)?\b"),
    ("Thursday", r"\bkamis\b", r"\bthu(?:r|rs|rsday)?\b"),
    ("Friday", r"\bjum['’]?at\b", r"\bfri(?:day)?\b"),
    ("Saturday", r"\bsabtu\b", r"\bsat(?:urday)?\b"),
    # minggu is also "week" (minggu ini, minggu kemarin); Minggu on its own, hari minggu, or minggu
    # after another day ("sabtu atau minggu") is Sunday
    (
        "Sunday",
        rf"\b[Hh]ari\s+[Mm]inggu\b|\bMinggu\b(?!\s+(?:ini|depan|lalu|kemarin|kemaren|pertama|kedua|ketiga|keempat|terakhir|berikutnya|ke)\b)"
        rf"|(?i:{_WEEKDAY}\s*(?:(?:atau|dan|,|-|/|sampai|s/d|hingga)\s*)?)minggu\b",
        r"\bsun(?:day)?\b",
    ),
]
_RELATIVE = [
    (r"\b(?:besok|bsk|esok)\b", r"tomorrow|next day|following day", "tomorrow"),
    (r"\b(?:kemarin|kemaren|kmrn)\b", r"yesterday|\blast\b|the other day|previous|earlier", "yesterday"),
    (r"(?<![\d·]\s)(?<![\d·])\b(?:hari ini|hr ini|hri ini)\b", r"today|\bthis\b|\bnow\b|same.day", "today"),
    (r"\blusa\b", r"day after tomorrow|in (?:two|2) days", "the day after tomorrow"),
]
_PERIODS = {
    "pagi": r"morning|\ba\.?m\b|dawn|early",
    "siang": r"noon|midday|afternoon|lunch|daytime|\bday\b|\bp\.?m\b|hello|\bhi\b",
    "sore": r"afternoon|evening|\bp\.?m\b",
    "malam": r"evening|night|tonight|\bp\.?m\b|\ba\.?m\b|midnight",
    "subuh": r"dawn|morning|\ba\.?m\b",
}
_PERIOD_WORD = re.compile(r"\b(pagi|siang|sore|malam|malem|mlm|semalam|subuh|tidur|bobo)\b", _IC)
_EN_PERIODS = {
    "morning": ("pagi", "subuh"),
    "afternoon": ("siang", "sore"),
    "evening": ("sore", "malam"),
    "night": ("malam", "tidur", "bobo"),
    "tonight": ("malam",),
    "noon": ("siang",),
    "midday": ("siang",),
}
_CLOCK = re.compile(r"\b(?:jam|pukul|jm)\s*\d", _IC)
_HOUR = re.compile(
    r"\b(?:jam|pukul|jm)\s*(\d{1,2})(?:[·:]\d{2})?(?:an)?\s+(?:\w+\s+)?(pagi|siang|sore|malam|malem|mlm)\b",
    _IC,
)
_UNITS = {
    "hari": "day",
    "minggu": "week",
    "bulan": "month",
    "jam": "hour",
    "menit": "minute",
    "tahun": "year",
    "detik": "second",
}
_SPAN = re.compile(
    r"(?:(?<![\d·])\d+(?:\s*[-–x]\s*\d+)?|\b(?:beberapa|bbrp|satu|dua|tiga|empat|lima|enam|tujuh|sepuluh))\s*(hari|minggu|bulan|jam|menit|tahun|detik)\b"
    r"|\bse(hari|minggu|bulan|jam|menit|tahun)\b",
    _IC,
)
_EN_SPAN = re.compile(
    r"\b(?:\d+|an?|one|two|three|four|five|six|seven|ten|a few|several|a couple of)"
    r"(?:\s*(?:-|–|to)\s*\d+)?[\s-]*"
    r"(?:(?:business|working|calendar|full|more)\s+)?(day|week|month|hour|minute|year|second)s?\b",
    _IC,
)
_EN_UNIT = {"hr": "hour", "min": "minute"}


def _half_of_day(h: int, period: str) -> str | None:
    """am or pm for "jam {h} {period}", None where Indonesian leaves it open."""
    if period == "pagi":
        return "am" if 1 <= h <= 11 else None
    if period == "siang":
        return "am" if h in (10, 11) else "pm" if h == 12 or 1 <= h <= 5 else None
    if period == "sore":
        return "pm" if 1 <= h <= 8 else None
    return "pm" if 6 <= h <= 11 else "am" if h == 12 or 1 <= h <= 4 else None


def _when(line: str, gloss: str) -> list[str]:
    found = []
    weekend = re.search(r"\bsabtu\b.{0,12}\bminggu\b", line, _IC) and re.search(r"\bweekends?\b", gloss, _IC)
    weekdays = re.search(r"\bsenin\b.{0,12}\bjum['’]?at\b", line, _IC) and re.search(
        r"\bweekdays?\b", gloss, _IC
    )
    said_days, wrote_days = _days_in(line, said=True), _days_in(gloss, said=False)
    for day, _said, _meant in _DAYS:
        skip = (weekend and day in ("Saturday", "Sunday")) or (weekdays and day in ("Monday", "Friday"))
        if day in said_days and day not in wrote_days and not skip:
            found.append(f"{day} is missing")
        elif day in wrote_days and day not in said_days and not skip:
            found.append(f"the gloss adds {day}")
    if (
        not (weekend or weekdays)
        and len(said_days) >= 2
        and len(wrote_days) >= 2
        and _dedup(said_days) != _dedup(wrote_days)
    ):
        found.append("the days come in another order")
    for said, meant, name in _RELATIVE:
        if re.search(said, line, _IC) and not re.search(meant, gloss, _IC):
            found.append(f"the line says {name} and the gloss does not")
    for said, word in (
        (r"\b(?:kemarin|kemaren|kmrn|semalam|tadi malam)\b", "yesterday"),
        (r"\b(?:besok|bsk|esok|lusa)\b", "tomorrow"),
    ):
        if re.search(rf"\b{word}\b", gloss, _IC) and not re.search(said, line, _IC):
            found.append(f"the gloss says {word} and the line does not")
    found += _periods(line, gloss)
    found += _period_order(line, gloss)
    found += _hours(line, gloss)
    said_units = {_UNITS[(a or b).lower()] for a, b in _SPAN.findall(line)}
    wrote_units = {_EN_UNIT.get(u.lower(), u.lower()) for u in _EN_SPAN.findall(gloss)}
    for unit in sorted(said_units - wrote_units):
        found.append(f"a span in {unit}s is missing")
    for unit in sorted(wrote_units - said_units):
        if said_units:
            found.append(f"the gloss gives a span in {unit}s the line does not")
    return found


def _days_in(text: str, said: bool) -> list[str]:
    """The days of the week a text names, in order: Indonesian names in a line, English in a gloss."""
    hits = []
    for day, indonesian, english in _DAYS:
        pattern, flags = (indonesian, 0 if day == "Sunday" else _IC) if said else (english, _IC)
        hits += [(m.start(), day) for m in re.finditer(pattern, text, flags)]
    return [day for _, day in sorted(hits)]


def _dedup(days: list[str]) -> list[str]:
    return [d for i, d in enumerate(days) if i == 0 or days[i - 1] != d]


def _periods(line: str, gloss: str) -> list[str]:
    found = []
    said = {
        ("malam" if w.lower() in ("malem", "mlm", "semalam") else w.lower())
        for w in _PERIOD_WORD.findall(line)
    }
    for period in sorted(said & set(_PERIODS)):
        if not re.search(_PERIODS[period], gloss, _IC):
            found.append(f"the line says {period} and the gloss names another time of day")
    if not _CLOCK.search(line):
        for word, periods in _EN_PERIODS.items():
            if re.search(rf"\b{word}\b", gloss, _IC) and not said & set(periods):
                found.append(f"the gloss names a time of day the line does not ({word})")
    return found


def _period_order(line: str, gloss: str) -> list[str]:
    """ "Tutup sore, buka besok pagi" must not come back as "closes in the morning, opens in the evening"."""
    said = [
        ("malam" if w.lower() in ("malem", "mlm", "semalam") else w.lower())
        for w in _PERIOD_WORD.findall(line)
    ]
    said = [w for w in said if w in _PERIODS]
    wrote = []
    for m in re.finditer(r"\b(" + "|".join(_EN_PERIODS) + r")\b", gloss, _IC):
        candidates = [p for p in _EN_PERIODS[m.group(1).lower()] if p in said]
        if len(candidates) == 1:
            wrote.append(candidates[0])
    if len(set(said)) >= 2 and len(set(wrote)) >= 2 and _dedup(said) != _dedup(wrote):
        return ["the times of day come in another order"]
    return []


def _hours(line: str, gloss: str) -> list[str]:
    found = []
    expected: dict[tuple[int, str], int] = {}
    for hour, period in _HOUR.findall(_plain(line)):
        half = _half_of_day(int(hour), "malam" if period.lower() in ("malem", "mlm") else period.lower())
        if half:
            expected[(int(hour), half)] = expected.get((int(hour), half), 0) + 1
    for m in re.finditer(r"(?<![\d·])([01]\d|2[0-3])[·:]([0-5]\d)(?![\d·])", _plain(line)):
        h24 = int(m.group(1))
        h12 = h24 % 12 or 12
        expected[(h12, "am" if h24 < 12 else "pm")] = expected.get((h12, "am" if h24 < 12 else "pm"), 0) + 1
    written: dict[tuple[int, str], int] = {}
    for hour, half in re.findall(r"\b(\d{1,2})(?:[:.]\d{2})?\s?([ap])\.?m\b\.?", gloss, _IC):
        key = (int(hour) % 12 or 12, half.lower() + "m")
        written[key] = written.get(key, 0) + 1
    for hour, part in re.findall(
        r"\b(\d{1,2})(?:[:.]\d{2})?\s+(?:o['’]clock\s+)?"
        r"(in the morning|in the afternoon|in the evening|at night)\b",
        gloss,
        _IC,
    ):
        key = (int(hour) % 12 or 12, "am" if part.lower() == "in the morning" else "pm")
        written[key] = written.get(key, 0) + 1
    for (hour, half), n in written.items():
        if (hour, half) not in expected and any(h == hour for h, _ in expected) and n > 0:
            found.append(f"jam {hour} turned into the wrong half of the day ({half})")
    said_order = [
        (int(h), _half_of_day(int(h), "malam" if p.lower() in ("malem", "mlm") else p.lower()))
        for h, p in _HOUR.findall(_plain(line))
    ]
    wrote_order = [
        (int(h) % 12 or 12, a.lower() + "m")
        for h, a in re.findall(r"\b(\d{1,2})(?:[:.]\d{2})?\s?([ap])\.?m\b", gloss, _IC)
    ]
    if (
        not found
        and len(said_order) >= 2
        and sorted(said_order) == sorted(wrote_order)
        and said_order != wrote_order
    ):
        found.append("the hours come in another order")
    return found


# --- the end of the line --------------------------------------------------------------------------

_DANGLING = re.compile(
    r"\b(?:the|a|an|to|of|and|or|with|for|in|on|at|by|from|that|which|who|is|are|was|were|will|be|your|my|our|their|this|as|than|but|if|so)$",
    _IC,
)


def _tail(text: str) -> str:
    return re.sub(r"[\s*_`]+$", "", _EMOJI.sub(" ", text.replace(STOP, " ")).rstrip())


def _cut_short(line: str, gloss: str) -> list[str]:
    said, wrote = _tail(line), _tail(gloss)
    if _DANGLING.search(wrote) and not _DANGLING.search(said):
        return ["the gloss stops before the end of the line"]
    if not re.search(r"[.?!)\"”']$", said):
        return []
    if re.search(r"[,;—–-]$", wrote) or (
        wrote.endswith(":") and not re.search(r"\bberikut\b|antara lain", line, _IC)
    ):
        return ["the gloss stops before the end of the line"]
    return []


# --- entry point ----------------------------------------------------------------------------------


def _text_problems(line: str, gloss: str) -> list[str]:
    return (
        _nots(_plain(line), _plain(gloss))
        + _questions(_plain(line), _plain(gloss))
        + _when(line, gloss)
        + _cut_short(line, gloss)
    )


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
    """What the gloss gets wrong about the line's meaning; for a JSON object, string by string."""
    if line.lstrip().startswith("{"):
        try:
            said, meant = json.loads(line), json.loads(gloss)
        except json.JSONDecodeError:
            return []
        return [
            f"{path}: {p}"
            for path, a, b in _string_pairs(said, meant, "")
            if a != b
            for p in _text_problems(a, b)
        ]
    return _text_problems(line, gloss)
