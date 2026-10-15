"""An opposite: including or excluding, more or less, before or after, until or since, up or down,
free or charged, from one place or to it, X and not Y. Each word the line says needs one of its
English words in the same sentence, and must not come back as its opposite unless the line says that
opposite too."""

import re

from toko_wa.meaning.text import IC, aligned

_NOT_BEFORE = r"(?<!tidak )(?<!tdk )(?<!ga )(?<!gak )(?<!nggak )(?<!belum )(?<!bukan )"
_DATE_AFTER = (
    r"(?=tanggal|tgl|\d|akhir|awal|jam|pukul|hari|minggu|bulan|senin|selasa|rabu|kamis|jum['’]?at\b|sabtu)"
)
_RANGE = r"\d\s*(?:[ap]\.?m\.?)?\s*[-–]\s*\d"
# (what the line says, the English it needs, the English that says the opposite, what in a line
# allows that opposite, its name)
OPPOSITES = [
    (
        rf"{_NOT_BEFORE}\btermasuk\b",
        r"includ\w*|incl\b|\bwith\b|plus|on top|count\w*|consider\w*"
        r"|classif\w*|qualif\w*|makes it|falls under|among",
        r"exclud\w*|not (?:yet )?includ\w*",
        r"\b(?:belum|tidak|tdk|ga|gak|bukan)\s+termasuk\b",
        "including",
    ),
    (
        rf"{_NOT_BEFORE}\blebih\s+dari\b|\bdi\s+atas\s+(?=\d|Rp)|>\s*\d|\blebih\s+(?=Rp|\d)",
        r"more than|over\b|above|exceed\w*|longer than|beyond|after|plus|extra|too much",
        r"less than|under\b|below|fewer than|at most|short",
        r"\bkurang\b|\bdi\s+bawah\b|<|\bmaksimal\b|\bmaks\b",
        "more than",
    ),
    (
        r"\bkurang\s+dari\b|\bdi\s+bawah\s+(?=\d|Rp)|<\s*\d|\bkurang\s+(?=Rp|\d)",
        r"less than|under\b|below|fewer than|within|short|remaining"
        r"|still (?:need|owe|due)|outstanding|missing|minus",
        r"more than|over\b|above|at least|too much",
        r"\blebih\b|\bdi\s+atas\b|>|\bminimal\b|\bmin\b",
        "less than",
    ),
    (
        r"\bminimal\b|\bmin\.|\bmin·|\bpaling\s+sedikit\b|\bsekurang-kurangnya\b|\bminimum\b",
        r"at least|minimum|\bmin\b|or more",
        r"at most|maximum|\bmax\b|or less|no more than",
        r"\bmaksimal\b|\bmaks\b|\bpaling\s+banyak\b",
        "at least",
    ),
    (
        r"\bmaksimal\b|\bmaks\b|\bpaling\s+banyak\b",
        r"at most|maximum|\bmax\b|up to|or less|no more than|within",
        r"at least|minimum|\bmin\b|or more",
        r"\bminimal\b|\bmin\.|\bpaling\s+sedikit\b",
        "at most",
    ),
    (
        rf"{_NOT_BEFORE}\b(?:sampai|hingga|s/d)\s+{_DATE_AFTER}",
        r"until|till|through|\bto\b|up to|\bby\b|\bend\w*|before|within"
        rf"|\bthru\b|last\w*|as of|so far|weekdays?|weekends?|{_RANGE}",
        r"\bsince\b|starting|beginning|onward",
        r"\b(?:mulai|sejak)\b",
        "until",
    ),
    (
        rf"\b(?:sejak|semenjak)\s+{_DATE_AFTER}",
        r"since|from|starting|as of|beginning|effective|for",
        r"\buntil\b|\btill\b|\bthrough\b|ending",
        r"\b(?:sampai|hingga|s/d)\b",
        "since",
    ),
    (
        r"\bsebelum\b",
        r"before|prior|until|by\b|excluding|ahead|pre-|first|earlier",
        r"\bafter\b|afterwards|later",
        r"\b(?:setelah|sesudah|habis)\b",
        "before",
    ),
    (
        r"\b(?:setelah|sesudah)\b",
        r"after|once|then|later|following|when|as soon as|within"
        r"|of (?:delivery|receipt|receiving|arrival|purchase)",
        r"\bbefore\b|prior to",
        r"\bsebelum\b",
        "after",
    ),
    (
        r"\blunas\b",
        r"paid|settled|in full|complete\w*|cleared|payment",
        r"outstanding|partial|unpaid|owed|still due|pending|short",
        r"\b(?:belum|tidak|ke?kurang\w*)\b",
        "paid in full",
    ),
    (
        r"(?-i:\b[Gg]ratis\b)|\bfree\b",
        r"free|no charge|at no cost|waived|\bno\b.{0,20}\b(?:fee|cost|charge)",
        r"costs? extra|extra charge|surcharge|\bfee\b|\bcharged?\b",
        r"\b(?:tidak|bukan|belum|ga|gak|nggak|tanpa|biaya|bayar|ongkir)\b",
        "free",
    ),
    (
        r"\bdiskon\b|\bpotongan\b",
        r"discount|\boff\b|reduc\w*|\bcut\b|saving|deduct\w*|promo",
        r"surcharge|markup|premium|\bextra\b",
        r"\b(?:biaya|tambahan)\b",
        "a discount",
    ),
    (
        r"\b(?:harga|ongkir|biaya|tarif|total)\b[^.!?\n]{0,20}\bnaik\b|\bnaik\s+(?:jadi|menjadi|ke)\b",
        r"\bris\w*|\brose\b|\bup\b|increas\w*|higher|rais\w*|went up|climb\w*",
        r"\bdrop\w*|\bfell\b|\bfall\w*|\bdown\b|decreas\w*|lower\w*|reduc\w*",
        r"\bturun\b",
        "up",
    ),
    (
        r"\b(?:harga|ongkir|biaya|tarif|total)\b[^.!?\n]{0,20}\bturun\b|\bturun\s+(?:jadi|menjadi|ke)\b",
        r"\bdrop\w*|\bfell\b|\bfall\w*|\bdown\b|decreas\w*|lower\w*|reduc\w*|cut",
        r"\bris\w*|\brose\b|\bup\b|increas\w*|higher|rais\w*",
        r"\bnaik\b",
        "down",
    ),
    (
        r"\b(?:transfer|uang|dana|pembayaran)\b[^.!?\n]{0,20}\bmasuk\b|\bmasuk\b[^.!?\n]{0,12}\b(?:rekening|mutasi)\b",
        r"receiv\w*|came in|come in|incoming|arriv\w*|credited"
        r"|deposit\w*|appear\w*|come(?:s)? through|came through"
        r"|(?:in|on|into) (?:the|our|your) (?:\w+ )?(?:account|statement)|reflect\w*|show\w* up|landed",
        r"went out|gone out|sent out|outgoing|debited",
        r"\bkeluar\b",
        "received",
    ),
    (
        r"\b(?:tinggal|tersisa|sisa)\s+(?:sedikit|\d)",
        r"\bleft\b|remain\w*|\bonly\b|\bfew\b|limited|running low|\blow\b|still",
        r"plent\w*|lots of|\bmany\b|a lot|\bdown\b|abundant",
        r"\bbanyak\b",
        "only a few left",
    ),
]
# Adjectives: (Indonesian, its English, the opposite English, the opposite Indonesian, also on its own).
# Most are checked only in a comparison (lebih tebal, paling murah, termahal); a few that are seldom
# anything else are checked on their own too.
_ADJECTIVES = [
    ("besar", r"big|large|bigger|larger|loose|roomy", r"small|smaller|tight\w*", "kecil", False),
    ("kecil", r"small|smaller|tight\w*|snug", r"big|large|bigger|larger|loose", "besar", False),
    ("tebal", r"thick\w*|heav\w*|warm\w*", r"thin\w*|sheer", "tipis", True),
    ("tipis", r"thin\w*|light\w*|sheer", r"thick\w*|heav\w*", "tebal", True),
    ("mahal", r"expensive|pricier|costl\w*|high\w*|more", r"cheap\w*|affordable|inexpensive", "murah", True),
    ("murah", r"cheap\w*|affordable|low\w*|inexpensive|less", r"expensive|pricier|costl\w*", "mahal", True),
    ("cepat", r"fast\w*|quick\w*|sooner|early|earlier", r"slow\w*", "lambat", False),
    ("lambat", r"slow\w*|later|longer", r"fast\w*|quick\w*|sooner", "cepat", False),
    ("panjang", r"long\w*", r"short\w*", "pendek", False),
    ("pendek", r"short\w*", r"long\w*", "panjang", False),
]
_PLACE_WORDS = r"(?:[A-Z][a-z]+|gudang|toko|rumah|kantor|alamat)"


def _opposites_in(said: str, wrote: str) -> list[str]:
    found = []
    for line_says, needs, opposite, allows, name in OPPOSITES:
        if not re.search(line_says, said, IC):
            continue
        if not re.search(needs, wrote, IC):
            found.append(f"the line says {name} and the gloss does not")
        elif re.search(opposite, wrote, IC) and not re.search(allows, said, IC):
            found.append(f"the gloss says the opposite of {name}")
    said = re.sub(r"\bpaling\s+lambat\b", " ", said, flags=IC)  # at the latest, a deadline
    for adjective, english, opposite, opposite_said, alone in _ADJECTIVES:
        compared = rf"\b(?:lebih|paling)\s+{adjective}\b|\bter{adjective}\b"
        if re.search(compared if not alone else rf"{compared}|\b{adjective}\b", said, IC):
            if not re.search(rf"\b(?:{english})\b", wrote, IC):
                found.append(f"the line says {adjective} and the gloss does not")
            elif re.search(rf"\b(?:{opposite})\b", wrote, IC) and not re.search(
                rf"\b{opposite_said}\b", said, IC
            ):
                found.append(f"the gloss says the opposite of {adjective}")
    return found


def _direction(said: str, wrote: str) -> list[str]:
    """ "dari Jakarta ke Bandung" must not come back as "from Bandung to Jakarta"."""
    found = []
    origins = set(re.findall(rf"\bdari\s+(?:\w+\s+)?({_PLACE_WORDS})", said))
    targets = set(re.findall(rf"\bke\s+(?:\w+\s+)?({_PLACE_WORDS})", said))
    wrote_from = set(re.findall(r"\bfrom\s+(?:the\s+)?(?:\w+\s+)?([A-Z][a-z]+)", wrote))
    wrote_to = set(re.findall(r"\b(?:to|into)\s+(?:the\s+)?(?:\w+\s+)?([A-Z][a-z]+)", wrote))
    for place in origins & (wrote_to - wrote_from) - targets:
        found.append(f"the line says from {place} and the gloss says to it")
    for place in targets & (wrote_from - wrote_to) - origins:
        found.append(f"the line says to {place} and the gloss says from it")
    return found


_COLOURS = {
    "hitam": "black",
    "item": "black",
    "putih": "white",
    "merah": "red",
    "biru": "blue",
    "hijau": "green",
    "abu": "gr[ae]y",
    "abu-abu": "gr[ae]y",
    "coklat": "brown",
    "cokelat": "brown",
    "kuning": "yellow",
    "cream": "cream",
    "maroon": "maroon",
    "navy": "navy",
    "pink": "pink",
}


def _not_this(said: str, wrote: str) -> list[str]:
    """ "hitam, bukan putih" (black, not white) must keep which one it is not."""
    found = []
    for word in re.findall(r"\bbukan\s+(?:ukuran\s+|warna\s+|yang\s+)?([A-Za-z-]+)", said, IC):
        size = re.fullmatch(r"(?:XS|S|M|L|XL|XXL)", word)
        english = f"(?-i:{word})" if size else _COLOURS.get(word.lower())
        not_it = rf"\b(?:not|n['’]t|rather than|instead of|but not|other than)\b[^.!?]{{0,25}}\b{english}\b"
        if english and not re.search(not_it, wrote, IC):
            found.append(f"the line says not {word} and the gloss does not")
    return found


def _ago(said: str, wrote: str) -> list[str]:
    """ "dalam 3 hari" (in 3 days) is ahead; "3 hari lalu" (3 days ago) is behind."""
    span = r"(?:\d+|beberapa|se)\s*(?:hari|minggu|bulan|jam|menit|tahun)"
    if re.search(rf"\bdalam\s+{span}|{span}\s+lagi\b", said, IC) and re.search(r"\bago\b", wrote, IC):
        return ["the line says in days to come and the gloss says ago"]
    if re.search(rf"{span}\s+(?:yang\s+)?lalu\b", said, IC) and not re.search(
        r"\bago\b|earlier|before|previous|last", wrote, IC
    ):
        return ["the line says ago and the gloss does not"]
    return []


def opposites(said: str, wrote: str) -> list[str]:
    found = []
    for line in aligned(said, wrote):
        for a, b in line:
            found += _opposites_in(a, b) + _direction(a, b) + _not_this(a, b) + _ago(a, b)
    return found
