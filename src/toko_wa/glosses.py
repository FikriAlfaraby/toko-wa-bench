"""English glosses for readers who do not read Indonesian.

data/glosses-en.json pairs every Indonesian line the replay shows (the earlier chats, what the
customer and the agent said, the agents' notes, the quotes in the review) with an English line.
`problems` checks that a gloss says the same thing: no Indonesian left, every number, ID, code and
name kept. The agents never see a gloss; nothing in the domain reads the file.
"""

import gzip
import json
import re
from pathlib import Path

from toko_wa.context import NOTE_HEADER

ROOT = Path(__file__).resolve().parents[2]
GLOSSES_PATH = ROOT / "data" / "glosses-en.json"
STOP = "###STOP###"

# Chat words in Indonesian (and a few in Sundanese and Javanese) that English never uses. A line with
# one of them needs a gloss; a gloss with one of them is not finished. Left out on purpose: words
# that are also English or appear in names here ("item", "jam", "dr", "kos", "gratis").
INDONESIAN = re.compile(
    r"\b("
    r"yang|yg|dan|di|ke|dari|untuk|utk|buat|dengan|dgn|ini|itu|tidak|tdk|nggak|ngga|gak|ga|gk|enggak|"
    r"ya|iya|kak|ka|kakak|sudah|udah|udh|sdh|belum|blm|bisa|ada|aku|saya|sy|kamu|mau|juga|atau|kalau|"
    r"kalo|klo|jadi|jd|sama|lagi|apa|gimana|dong|aja|tapi|tp|karena|krn|akan|harus|pada|dalam|adalah|"
    r"bahwa|hari|besok|kemarin|kmrn|terima|kasih|makasih|silakan|mohon|tolong|pesanan|alamat|kirim|"
    r"bayar|ongkir|berapa|boleh|kok|sih|deh|nih|tuh|banget|sekarang|nanti|tadi|dulu|lebih|kurang|"
    r"semua|minta|pakai|pake|dapat|dapet|potongan|rekening|resi|paket|barang|harga|ukuran|warna|"
    r"hitam|putih|stok|habis|tersedia|mutasi|unik|kode|tiasa|muhun|teu|atuh|punten|nuhun|nggih|"
    r"mboten|sampun|matur|monggo|siap|baik|dikirim|dibayar|dibantu|ditunggu|sampai|sampe|lihat|liat|"
    r"cek|bentar|sebentar|bagaimana|kenapa|kapan|mana|banyak|sedikit|tinggal|masih|sedang|hanya|cuma|"
    r"saja|kami|kita|anda|dia|mereka|terus|trus|lalu|jangan|jgn"
    r")\b",
    re.IGNORECASE,
)

# Place names a gloss may also give in their English form.
PLACES = {"Jakarta Selatan": ("Jakarta Selatan", "South Jakarta")}
# Order, item and transfer IDs (ORD-1002, KS-HTM-L, TRF-501) and codes with a digit (GAJIAN10).
ID_OR_CODE = re.compile(
    r"\b(?:[A-Z]{2,}-[A-Z0-9-]*\d[A-Z0-9-]*|[A-Z]{2,}-[A-Z]+-[A-Z]+|[A-Z]+\d+[A-Z0-9]*)\b"
)
NUMBER = re.compile(r"\d+(?:[.,:/]\d+)*")
# In chat Indonesian a 2 after a word repeats the word: tanya2 is tanya-tanya (ask around), not two.
REPEAT = re.compile(r"(?<=[a-z])2\b")


def is_indonesian(text: str) -> bool:
    return bool(INDONESIAN.search(text))


def _digits(text: str) -> list[str]:
    return [re.sub(r"\D", "", n) for n in NUMBER.findall(REPEAT.sub("", text))]


def _kept(number: str, english: list[str]) -> bool:
    """227rb may become 227k or 227,000; 1,5jt may become 1.5 million. Nothing else changes."""
    return any(e == number or (e.startswith(number) and set(e[len(number) :]) == {"0"}) for e in english)


def names(db: dict) -> list[str]:
    """Names a gloss must keep when its line has them: people (full and first names), cities,
    couriers, banks, promo codes and product names."""
    out = set()
    for c in db["customers"].values():
        out.add(c["name"])
        out.add(c["name"].removeprefix("Hj. ").split()[0])
    for rate in db["shipping_rates"]:
        out.update((rate["city"], rate["courier"]))
    out.update(t["bank"] for t in db["transfers"].values())
    out.update(db["promos"])
    out.update(p["name"] for p in db["products"].values())
    return sorted(out, key=len, reverse=True)


def problems(line: str, gloss: str | None, keep: list[str]) -> list[str]:
    """Why a gloss does not stand for its line in English; empty when it does."""
    if gloss is None:
        return ["the line is Indonesian but has no gloss"] if is_indonesian(line) else []
    found = []
    if not gloss.strip() or gloss.strip() == line.strip():
        return ["the gloss is empty or repeats the line"]
    # Codes and names are kept as written, so set them aside before looking for Indonesian words.
    plain = gloss
    for name in keep:
        plain = plain.replace(name, " ")
    plain = ID_OR_CODE.sub(" ", plain)
    left = INDONESIAN.search(plain)
    if left:
        found.append(f"the gloss still has the Indonesian word '{left.group(0)}'")
    english, said = _digits(gloss), _digits(line)
    for n in said:
        if not _kept(n, english):
            found.append(f"the number {n} is missing")
    for e in english:
        if not any(_kept(n, [e]) for n in said):
            found.append(f"the gloss adds the number {e}")
    if REPEAT.search(gloss):
        found.append("the gloss keeps a repeated word written with 2 (tanya2 means ask around)")
    for code in ID_OR_CODE.findall(line):
        if code not in gloss:
            found.append(f"{code} is missing")
    for name in keep:
        if re.search(rf"(?<!\w){re.escape(name)}(?!\w)", line):
            if not any(form in gloss for form in PLACES.get(name, (name,))):
                found.append(f"{name} is missing")
    if not line.lstrip().startswith("{") and line.count('"') % 2 != gloss.count('"') % 2:
        found.append("the gloss has a stray quote mark")
    if (STOP in line) != (STOP in gloss):
        found.append(f"{STOP} must be kept exactly where the line has it")
    if line.lstrip().startswith("{"):
        try:
            said = json.loads(line)
        except json.JSONDecodeError:
            said = None
        if isinstance(said, dict):
            try:
                meant = json.loads(gloss)
            except json.JSONDecodeError:
                meant = None
            if not isinstance(meant, dict) or set(meant) != set(said):
                found.append(
                    "the line is a JSON object: the gloss must be the same object with its text in English"
                )
    if len(line) >= 40 and not 0.35 <= len(gloss) / len(line) <= 2.5:
        found.append(f"the gloss is {len(gloss)} characters for a line of {len(line)}")
    return list(dict.fromkeys(found))


def _note(message: dict) -> str | None:
    return (((message.get("raw_data") or {}).get("toko_context") or {}).get("compaction") or {}).get("note")


def shown_lines(root: Path = ROOT) -> list[str]:
    """Every distinct line the replay shows a reader, in the order first seen: the earlier chats,
    the line drop leaves, what the customer and the agent said, the notes, the review's quotes."""
    seen: dict[str, None] = {}

    def add(text: str | None) -> None:
        if text and text.replace(STOP, "").strip():
            seen.setdefault(text, None)

    tasks = [
        t
        for t in json.loads((root / "data/toko_wa/tasks.json").read_text(encoding="utf-8"))
        if not t["id"].startswith("smoke")
    ]
    history_len = {}
    for task in tasks:
        history = (task.get("initial_state") or {}).get("message_history") or []
        history_len[task["id"]] = len(history)
        for message in history:
            add(message.get("content"))
    add(NOTE_HEADER["drop"])
    for path in sorted((root / "runs").glob("exp1-*.json.gz")):
        for sim in json.loads(gzip.decompress(path.read_bytes()))["simulations"]:
            for message in sim["messages"][history_len[sim["task_id"]] :]:
                if message["role"] in ("user", "assistant"):
                    add(message.get("content"))
                add(_note(message))
    for item in json.loads((root / "review/2026-10-15.json").read_text(encoding="utf-8"))["items"]:
        add(item["quote"])
    return list(seen)


def load(root: Path = ROOT) -> dict[str, str | None]:
    return json.loads((root / "data" / "glosses-en.json").read_text(encoding="utf-8"))["glosses"]
