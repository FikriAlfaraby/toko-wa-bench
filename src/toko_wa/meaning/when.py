"""When: a day of the week and whether it is next or last, a month, tomorrow or yesterday and their
order, the time of day, an hour and its half of the day, and a span of days, weeks or hours."""

import re

from toko_wa.meaning.text import IC, dedup, plain

_WEEKDAY = r"(?:senin|selasa|rabu|kamis|jum['’]?at|sabtu)"
_DAYS = [
    ("Monday", r"\bsenin\b", r"\bmon(?:day)?s?\b"),
    ("Tuesday", r"\bselasa\b", r"\btue(?:s|sday)?s?\b"),
    ("Wednesday", r"\brabu\b", r"\bwed(?:nesday)?s?\b"),
    ("Thursday", r"\bkamis\b", r"\bthu(?:r|rs|rsday)?s?\b"),
    ("Friday", r"\bjum['’]?at\b", r"\bfri(?:day)?s?\b"),
    ("Saturday", r"\bsabtu\b", r"\bsat(?:urday)?s?\b"),
    # minggu is also "week" (minggu ini, minggu yang lalu, minggu-minggu ini); Minggu on its own,
    # hari minggu, or minggu after another day ("sabtu atau minggu", "SABTU MINGGU LIBUR") is Sunday
    (
        "Sunday",
        r"\b[Hh]ari\s+[Mm]inggu\b"
        r"|\bMinggu\b(?!-|\s+(?:ini|depan\w*|lalu|yang|kemarin|kemaren|pertama|kedua|ketiga|keempat|terakhir|berikutnya|ke)\b)"
        rf"|(?i:{_WEEKDAY}\s*(?:(?:atau|dan|,|-|/|sampai|s/d|hingga)\s*)?minggu)\b",
        r"\bsun(?:day)?s?\b",
    ),
]
_NEXT = r"depan|besok|nanti"
_LAST = r"lalu|kemarin|kemaren"
_MONTHS = [
    ("January", r"\bjanuari\b|\bjan\b(?=\s*\d)|(?<=\d\s)jan\b", r"\bjan(?:uary)?\b"),
    ("February", r"\bfebruari\b|\bfeb\b(?=\s*\d)|(?<=\d\s)feb\b", r"\bfeb(?:ruary)?\b"),
    ("March", r"\bmaret\b", r"\bmarch\b"),
    ("April", r"\bapril\b|\bapr\b(?=\s*\d)|(?<=\d\s)apr\b", r"\bapr(?:il)?\b"),
    ("May", r"\bmei\b", r"\bMay\b(?=\s+\d)|(?<=\d\s)May\b"),
    ("June", r"\bjuni\b|(?<=\d\s)jun\b", r"\bjune\b"),
    ("July", r"\bjuli\b|(?<=\d\s)jul\b", r"\bjuly\b"),
    ("August", r"\bagustus\b|(?<=\d\s)ag[ut]s?\b", r"\baug(?:ust)?\b"),
    ("September", r"\bseptember\b|(?<=\d\s)sept?\b", r"\bsept?(?:ember)?\b"),
    ("October", r"\boktober\b|\bokt\b", r"\boct(?:ober)?\b"),
    ("November", r"\bnovember\b|(?<=\d\s)nov\b", r"\bnov(?:ember)?\b"),
    ("December", r"\bdesember\b|(?<=\d\s)des\b", r"\bdec(?:ember)?\b"),
]
# A weekday followed by besok is the coming one ("Senin besok"), not tomorrow.
_DAY_BESOK = re.compile(rf"\b(?:{_WEEKDAY}|minggu)\s+besok\b", IC)
_RELATIVE = [
    ("tomorrow", r"\b(?:besok|bsk|esok)\b", r"(?<!after )tomorrow|tmrw|\btmr\b|next day|following day"),
    (
        "yesterday",
        r"\b(?:kemarin|kemaren|kmrn)\b",
        r"(?<!before )yesterday|\blast\b|the other day|previous|earlier|day before|a day ago",
    ),
    (
        "today",
        r"(?<![\d·]\s)(?<![\d·])\b(?:hari ini|hr ini|hri ini)\b",
        r"today|\bthis\b|\bnow\b|same.day|right away|immediately",
    ),
    ("the day after tomorrow", r"\blusa\b", r"day after tomorrow|in (?:two|2) days"),
]
# Weeks, months and years before or after this one: the English names the same one.
_SPANS_AROUND = [
    ("this week", r"\b(?:minggu|pekan)\s+ini\b", r"\bthis week\b|these (?:past )?weeks"),
    ("this weekend", r"\b(?:weekend|wiken|akhir\s+pekan|akhir\s+minggu)\s+ini\b", r"\bthis weekend\b"),
    ("next week", r"\b(?:minggu|pekan)\s+depan\w*\b", r"\b(?:next|following|coming) week\b"),
    (
        "last week",
        r"\b(?:minggu|pekan)\s+(?:yang\s+)?(?:lalu|kemarin|kemaren)\b",
        r"\b(?:last|previous|past) week\b",
    ),
    ("this month", r"\bbulan\s+ini\b", r"\bthis month\b"),
    ("next month", r"\bbulan\s+depan\b", r"\b(?:next|following|coming) month\b"),
    ("last month", r"\bbulan\s+(?:yang\s+)?(?:lalu|kemarin)\b", r"\b(?:last|previous|past) month\b"),
    ("this year", r"\b(?:tahun|taun|thn)\s+ini\b", r"\bthis year\b"),
    ("next year", r"\b(?:tahun|taun|thn)\s+depan\b", r"\b(?:next|following|coming) year\b"),
    (
        "last year",
        r"\b(?:tahun|taun|thn)\s+(?:yang\s+)?(?:lalu|kemarin)\b",
        r"\b(?:last|previous|past) year\b",
    ),
]
_AM = r"\d\s*a\.?m\b"
_PM = r"\d\s*p\.?m\b"
_PERIODS = {
    "pagi": rf"morning|{_AM}|dawn|early|first thing",
    "siang": rf"noon|midday|afternoon|lunch|daytime|\bday\b|{_PM}|hello|\bhi\b",
    "sore": rf"afternoon|evening|{_PM}",
    "malam": rf"evening|night|tonight|{_PM}|{_AM}|midnight",
    "subuh": rf"dawn|morning|{_AM}",
}
_PERIOD_WORD = re.compile(r"\b(pagi|siang|sore|malam|malem|mlm|semalam|subuh|tidur|bobo)\b", IC)
_EN_PERIODS = {
    "morning": ("pagi", "subuh"),
    "afternoon": ("siang", "sore"),
    "evening": ("sore", "malam"),
    "night": ("malam", "tidur", "bobo"),
    "tonight": ("malam",),
    "noon": ("siang",),
    "midday": ("siang",),
}
_CLOCK = re.compile(r"\b(?:jam|pukul|jm)\s*\d", IC)
# "jam 7 malam", and the second hour of a range without its "jam": "jam 8 pagi sampai 10 malam"
_HOUR = re.compile(
    r"(?:\b(?:jam|pukul|jm)\s*|\b(?:sampai|hingga|s/d|atau|dan)\s+|[-–]\s*)(\d{1,2})(?:[·:]\d{2})?(?:an)?\s+(?:\w+\s+)?"
    r"(pagi|siang|sore|malam|malem|mlm)\b",
    IC,
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
# "3 hari", "2-3 hari", "1x24 jam" are spans; "2026 jam 14.00" is a date before a clock time
_SPAN = re.compile(
    r"(?<![\d·.:-])(\d+(?:\s*[-–x]\s*\d+)?)\s*(hari|minggu|bulan|jam(?!\s*\d)|menit|tahun|detik)\b"
    r"|\b(beberapa|bbrp|satu|dua|tiga|empat|lima|enam|tujuh|sepuluh)\s+(hari|minggu|bulan|jam|menit|tahun|detik)\b"
    r"|\b(se)(hari|minggu|bulan|jam|menit|tahun)\b",
    IC,
)
_EN_SPAN = re.compile(
    r"\b(\d+(?:\s*(?:-|–|to)\s*\d+)?|an?|one|two|three|four"
    r"|five|six|seven|ten|a few|several|a couple of)[\s-]*"
    r"(?:(?:business|working|calendar|full|more)\s+)?(day|week|month|hour|minute|year|second)s?\b"
    r"|\b(\d+)\s*(h|hr|min)s?\b(?!\.\s*[a-z])",
    IC,
)
_EN_UNIT = {"h": "hour", "hr": "hour", "min": "minute"}
_WORD_NUMBER = {
    "satu": "1",
    "se": "1",
    "an": "1",
    "a": "1",
    "one": "1",
    "dua": "2",
    "two": "2",
    "tiga": "3",
    "three": "3",
}


def _days_in(text: str, said: bool) -> list[str]:
    hits = []
    for day, indonesian, english in _DAYS:
        pattern, flags = (indonesian, 0 if day == "Sunday" else IC) if said else (english, IC)
        hits += [(m.start(), day) for m in re.finditer(pattern, text, flags)]
    return [day for _, day in sorted(hits)]


def _days(line: str, gloss: str) -> list[str]:
    found = []
    weekend = re.search(r"\bsabtu\b.{0,12}\bminggu\b", line, IC) and re.search(r"\bweekends?\b", gloss, IC)
    weekdays = re.search(r"\bsenin\b.{0,12}\bjum['’]?at\b", line, IC) and re.search(
        r"\bweekdays?\b", gloss, IC
    )
    said_days, wrote_days = _days_in(line, said=True), _days_in(gloss, said=False)
    for day, said, meant in _DAYS:
        skip = (weekend and day in ("Saturday", "Sunday")) or (weekdays and day in ("Monday", "Friday"))
        if skip:
            continue
        if day in said_days and day not in wrote_days:
            found.append(f"{day} is missing")
        elif day in wrote_days and day not in said_days:
            found.append(f"the gloss adds {day}")
        elif day in said_days:
            found += _which_one(day, said, meant, line, gloss)
    if (
        not (weekend or weekdays)
        and len(said_days) >= 2
        and len(wrote_days) >= 2
        and dedup(said_days) != dedup(wrote_days)
    ):
        found.append("the days come in another order")
    for month, said, meant in _MONTHS:
        flags = 0 if month == "May" else IC
        if re.search(said, line, IC) and not re.search(meant, gloss, flags):
            found.append(f"{month} is missing")
        elif re.search(meant, gloss, flags) and not re.search(said, line, IC):
            found.append(f"the gloss adds {month}")
    return found


def _which_one(day: str, said: str, meant: str, line: str, gloss: str) -> list[str]:
    """ "Jumat depan" is next Friday, "Senin lalu" last Monday, plain "Jumat" neither."""
    flags = 0 if day == "Sunday" else IC
    after = [m.group(1) or "" for m in re.finditer(rf"(?:{said})(?:\s+(\w+))?", line, flags)]
    ahead = any(re.fullmatch(_NEXT, w, IC) for w in after)
    # "Jumat depan" is next Friday, never this one; "Senin besok" may be this coming Monday, or tomorrow
    this_one = r"|this|tomorrow,?" if not any(re.fullmatch(r"depan\w*", w, IC) for w in after) else ""
    behind = any(re.fullmatch(_LAST, w, IC) for w in after)
    found = []
    if re.search(rf"\b(?:next|coming|following)\s+(?:{meant})", gloss, IC) and not ahead:
        found.append(f"the gloss says next {day} and the line does not")
    if re.search(rf"\b(?:last|previous|past)\s+(?:{meant})", gloss, IC) and not behind:
        found.append(f"the gloss says last {day} and the line does not")
    if ahead and not re.search(
        rf"\b(?:next|coming|following{this_one})\s+(?:{meant})|(?:{meant})\s+(?:next|after)", gloss, IC
    ):
        found.append(f"the line says the coming {day} and the gloss does not")
    if behind and not re.search(
        rf"\b(?:last|previous|past)\s+(?:{meant})|(?:{meant})\s+(?:last|before)", gloss, IC
    ):
        found.append(f"the line says last {day} and the gloss does not")
    return found


def _relative(line: str, gloss: str) -> list[str]:
    found = []
    text = _DAY_BESOK.sub(" ", line)
    said_order, wrote_order = [], []
    for name, said, meant in _RELATIVE:
        if re.search(said, text, IC) and not re.search(meant, gloss, IC):
            found.append(f"the line says {name} and the gloss does not")
        said_order += [(m.start(), name) for m in re.finditer(said, text, IC)]
        wrote_order += [
            (m.start(), name) for m in re.finditer(rf"\b(?<!after )(?<!before ){name}\b", gloss, IC)
        ]
    for said, word in (
        (r"\b(?:kemarin|kemaren|kmrn|semalam|tadi malam)\b", "yesterday"),
        (r"\b(?:besok|bsk|esok|lusa)\b", "tomorrow"),  # in the line as written: "Jumat besok" may be tomorrow
        (r"\blusa\b", "day after tomorrow"),
        (r"\bkemarin\s+lusa\b", "day before yesterday"),
    ):
        if re.search(rf"\b{word}\b", gloss, IC) and not re.search(said, line, IC):
            found.append(f"the gloss says {word} and the line does not")
    said_names = [n for _, n in sorted(said_order)]
    wrote_names = [n for _, n in sorted(wrote_order)]
    if len(set(said_names)) >= 2 and len(set(wrote_names)) >= 2 and dedup(said_names) != dedup(wrote_names):
        found.append("tomorrow, today and yesterday come in another order")
    for name, said, meant in _SPANS_AROUND:
        if re.search(said, line, IC) and not re.search(meant, gloss, IC):
            found.append(f"the line says {name} and the gloss does not")
        elif re.search(meant, gloss, IC) and not re.search(said, line, IC):
            found.append(f"the gloss says {name} and the line does not")
    return found


def _periods(line: str, gloss: str) -> list[str]:
    found = []
    said = {
        ("malam" if w.lower() in ("malem", "mlm", "semalam") else w.lower())
        for w in _PERIOD_WORD.findall(line)
    }
    for period in sorted(said & set(_PERIODS)):
        if not re.search(_PERIODS[period], gloss, IC):
            found.append(f"the line says {period} and the gloss names another time of day")
    if not _CLOCK.search(line):
        for word, periods in _EN_PERIODS.items():
            if re.search(rf"\b{word}\b", gloss, IC) and not said & set(periods):
                found.append(f"the gloss names a time of day the line does not ({word})")
    said_order = [
        ("malam" if w.lower() in ("malem", "mlm", "semalam") else w.lower())
        for w in _PERIOD_WORD.findall(line)
    ]
    said_order = [w for w in said_order if w in _PERIODS]
    wrote_order = []
    for m in re.finditer(r"\b(" + "|".join(_EN_PERIODS) + r")\b", gloss, IC):
        candidates = [p for p in _EN_PERIODS[m.group(1).lower()] if p in said_order]
        if len(candidates) == 1:
            wrote_order.append(candidates[0])
    if len(set(said_order)) >= 2 and len(set(wrote_order)) >= 2 and dedup(said_order) != dedup(wrote_order):
        found.append("the times of day come in another order")
    return found


def _half_of_day(h: int, period: str) -> str | None:
    """am or pm for "jam {h} {period}", None where Indonesian leaves it open."""
    if period == "pagi":
        return "am" if 1 <= h <= 11 else None
    if period == "siang":
        return "am" if h in (10, 11) else "pm" if h == 12 or 1 <= h <= 5 else None
    if period == "sore":
        return "pm" if 1 <= h <= 8 else None
    return "pm" if 6 <= h <= 11 else "am" if h == 12 or 1 <= h <= 4 else None


def _hours(line: str, gloss: str) -> list[str]:
    expected, said_order = [], []
    for hour, period in _HOUR.findall(plain(line)):
        half = _half_of_day(int(hour), "malam" if period.lower() in ("malem", "mlm") else period.lower())
        if half:
            expected.append((int(hour), half))
            said_order.append((int(hour), half))
    for m in re.finditer(r"(?<![\d·])([01]\d|2[0-3])[·:]([0-5]\d)(?![\d·])", plain(line)):
        h24 = int(m.group(1))
        expected.append((h24 % 12 or 12, "am" if h24 < 12 else "pm"))
    written = [
        (int(h) % 12 or 12, a.lower() + "m")
        for h, a in re.findall(r"\b(\d{1,2})(?:[:.]\d{2})?\s?([ap])\.?m\b\.?", gloss, IC)
    ]
    wrote_order = list(written)
    written += [
        (int(h) % 12 or 12, "am" if part.lower() == "in the morning" else "pm")
        for h, part in re.findall(
            r"\b(\d{1,2})(?:[:.]\d{2})?\s+(?:o['’]clock\s+)?(in the morning"
            r"|in the afternoon|in the evening|at night)\b",
            gloss,
            IC,
        )
    ]
    found = []
    for hour in sorted({h for h, _ in written} & {h for h, _ in expected}):
        want = {half for h, half in expected if h == hour}
        got = {half for h, half in written if h == hour}
        if got - want:
            found.append(f"jam {hour} turned into the wrong half of the day ({sorted(got - want)[0]})")
        elif want - got:
            found.append(
                f"jam {hour} turned into the wrong half of the day (its {sorted(want - got)[0]} is missing)"
            )
    if (
        not found
        and len(said_order) >= 2
        and sorted(said_order) == sorted(wrote_order)
        and said_order != wrote_order
    ):
        found.append("the hours come in another order")
    return found


def _spans(line: str, gloss: str) -> list[str]:
    said, wrote = [], []
    # "salah satu jam" is one of the times, "No. 12 hari ini" a house number before today
    text = re.sub(r"\bsalah\s+satu\b|\b(?:No|Blok|Km|Lt|Kav)[·.]?\s*\d+\w*", " ", plain(line), flags=IC)
    for groups in _SPAN.findall(text):
        number, unit = next((groups[i], groups[i + 1]) for i in (0, 2, 4) if groups[i + 1])
        said.append(
            (_WORD_NUMBER.get(number.lower(), re.sub(r"\s*[-–]\s*", "-", number)), _UNITS[unit.lower()])
        )
    for a, b, c, d in _EN_SPAN.findall(gloss):
        number, unit = (a, b) if b else (c, _EN_UNIT[d.lower()])
        wrote.append(
            (_WORD_NUMBER.get(number.lower(), re.sub(r"\s*(?:to|–|-)\s*", "-", number)), unit.lower())
        )
    found = [f"a span in {unit}s is missing" for unit in sorted({u for _, u in said} - {u for _, u in wrote})]
    if said:
        found += [
            f"the gloss gives a span in {unit}s the line does not"
            for unit in sorted({u for _, u in wrote} - {u for _, u in said})
        ]
    if (
        not found
        and said
        and wrote
        and sorted(said) != sorted(wrote)
        and {n for n, _ in said} == {n for n, _ in wrote}
    ):
        found.append("the spans swapped their numbers")
    return found


def when(line: str, gloss: str) -> list[str]:
    return (
        _days(line, gloss)
        + _relative(line, gloss)
        + _periods(line, gloss)
        + _hours(line, gloss)
        + _spans(line, gloss)
    )
