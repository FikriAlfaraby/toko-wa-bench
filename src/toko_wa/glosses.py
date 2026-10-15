"""English glosses for readers who do not read Indonesian.

data/glosses-en.json pairs every line the replay shows (the earlier chats, what the customer and
the agent said, the arguments the agent passed to tools and what the tools returned, the agents'
notes, the quotes in the review) with an English line, or with null for a line that has no
Indonesian in it. `problems` checks that a gloss says the same thing: no Indonesian left; every
number with its unit, every order, item and promo code, and every name the shop's data knows kept;
line breaks and length about the same. These checks cannot see every change of meaning (which item
a number belongs to, a place the shop's data does not know), so the lines a finding rests on are
also pinned by hand in tests/test_glosses.py. The agents never see a gloss; nothing in the domain
reads the file.
"""

import gzip
import json
import re
from decimal import Decimal
from pathlib import Path

from toko_wa.context import NOTE_HEADER

ROOT = Path(__file__).resolve().parents[2]
GLOSSES_PATH = ROOT / "data" / "glosses-en.json"
STOP = "###STOP###"

# Indonesian chat words (and a few Sundanese and Javanese ones) that English never uses. Left out on
# purpose: words that are also English or part of names here ("item", "jam", "dr", "kos", "gratis",
# "kaos", "polos").
_WORDS = (
    "yang yg dan di ke dari untuk utk buat dengan dgn ini itu tidak tdk nggak ngga gak ga gk enggak ya iya "
    "kak ka kakak sudah udah udh sdh belum blm bisa ada aku saya sy kamu mau juga atau kalau kalo klo jadi "
    "jd sama lagi apa gimana dong aja tapi tp karena krn akan harus pada dalam adalah bahwa hari besok "
    "kemarin kmrn terima kasih makasih silakan mohon tolong pesanan alamat kirim bayar ongkir berapa brp "
    "boleh kok sih deh nih tuh banget sekarang skrg nanti tadi dulu lebih kurang semua minta pakai pake "
    "dapat dapet potongan rekening resi paket barang harga ukuran warna hitam putih merah hijau biru kuning "
    "abu coklat cokelat stok habis tersedia mutasi unik kode tiasa muhun teu atuh punten nuhun nggih mboten "
    "sampun matur monggo siap baik dikirim dibayar dibantu ditunggu dibuat sampai sampe lihat liat cek "
    "bentar sebentar bagaimana kenapa kapan mana banyak sedikit tinggal masih sedang hanya cuma saja kami "
    "kita anda dia mereka terus trus lalu jangan jgn pembayaran kurir nomor sesuai maaf pelanggan tf oke "
    "rumah ingin pukul januari februari maret april mei juni juli agustus september oktober november "
    "desember senin selasa rabu kamis jumat sabtu"
).split()
# Short words that are also English words or names when capitalised ("Hello Dan", "Ada", "Mana"): in a
# gloss they count only in lower case. A line is Indonesian if it has any word above, in any case.
_AMBIGUOUS = {"dan", "di", "ke", "ya", "ada", "apa", "mana", "dia", "sama", "mau", "kita", "ka", "ga", "aku"}
_ANY = re.compile(r"\b(" + "|".join(_WORDS) + r")\b", re.IGNORECASE)
_STRICT = re.compile(r"\b(" + "|".join(w for w in _WORDS if w not in _AMBIGUOUS) + r")\b", re.IGNORECASE)
_LOWER = re.compile(r"\b(" + "|".join(sorted(_AMBIGUOUS)) + r")\b")
# warnanya, bahannya, pesanannya: the -nya forms the list cannot hold one by one (not Kenya, Tanya).
_NYA = re.compile(r"\b[a-z]{3,}nya\b", re.IGNORECASE)
# Product words ("kaos polos", "category": "celana") make a line Indonesian once the shop's product
# names are set aside. A gloss may still carry them inside a product name, which it keeps as written.
_PRODUCT_WORDS = re.compile(r"\b(kaos|polos|kemeja|celana|jaket|kanvas|kotak)\b", re.IGNORECASE)

# Place names a gloss may also give in their English form.
PLACES = {"Jakarta Selatan": ("Jakarta Selatan", "South Jakarta")}
# Order, item and transfer IDs (ORD-1002, KS-HTM-L, TRF-501) and codes with a digit (GAJIAN10).
ID_OR_CODE = re.compile(
    r"\b(?:[A-Z]{2,}-[A-Z0-9-]*\d[A-Z0-9-]*|[A-Z]{2,}-[A-Z]+-[A-Z]+|[A-Z]+\d+[A-Z0-9]*)\b"
)
# A number, with the unit that scales it: 227rb, 1,5jt, 227k, 1.5 million.
AMOUNT = re.compile(
    r"(?<![\d.,:])(\d+(?:[.,:]\d+)*)(?:\s?(rb|ribu|k|jt|juta|thousand|million)\b)?", re.IGNORECASE
)
SCALE = {"rb": 1_000, "ribu": 1_000, "k": 1_000, "thousand": 1_000}
SCALE |= {"jt": 10**6, "juta": 10**6, "million": 10**6}
# In chat Indonesian a 2 after a word repeats the word: tanya2 is tanya-tanya, not two. Not after p or x
# (Rp2.000, x2), and not when more digits follow.
REPEAT = re.compile(r"(?<=[a-oq-wyz])2(?![.,]?\d)\b")


def is_indonesian(text: str, keep: list[str] = ()) -> bool:
    plain = text
    for name in keep:
        plain = plain.replace(name, " ")
    return bool(_ANY.search(text) or _NYA.search(text) or _PRODUCT_WORDS.search(plain))


def _indonesian_left(gloss: str) -> str | None:
    found = _STRICT.search(gloss) or _LOWER.search(gloss) or _NYA.search(gloss)
    return found.group(0) if found else None


def amounts(text: str) -> list[str]:
    """Each number as the value it stands for: Rp133.570 and Rp133,570 are 133570, 227rb and 227k are
    227000, 1,5 and 1.5 are 1.5, and 10.00 and 10:00 are the time 10:00."""
    out = []
    for raw, unit in AMOUNT.findall(REPEAT.sub("", text)):
        time = re.fullmatch(r"(\d{1,2})[.:](\d{2})", raw)
        if time and not unit:
            out.append(f"{int(time.group(1))}:{time.group(2)}")
            continue
        groups = re.split(r"[.,:]", raw)
        if len(groups) == 1 or all(len(g) == 3 for g in groups[1:]):
            value = Decimal("".join(groups))
        elif len(groups) == 2:
            value = Decimal(f"{groups[0]}.{groups[1]}")
        else:  # 2026.10.15 and the like: each part as it stands
            out.extend(str(int(g)) for g in groups)
            continue
        value *= SCALE[unit.lower()] if unit else 1
        out.append(str(int(value)) if value == value.to_integral_value() else str(value.normalize()))
    return out


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


def _json_problem(line: str, gloss: str) -> str | None:
    if not line.lstrip().startswith("{"):
        return None
    try:
        said = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(said, dict):
        return None
    try:
        meant = json.loads(gloss)
    except json.JSONDecodeError:
        meant = None
    if not isinstance(meant, dict) or set(meant) != set(said):
        return "the line is a JSON object: the gloss must be the same object with its text in English"
    return None


def problems(line: str, gloss: str | None, keep: list[str]) -> list[str]:
    """Why a gloss does not stand for its line in English; empty when it does."""
    if gloss is None:
        return ["the line is Indonesian but has no gloss"] if is_indonesian(line, keep) else []
    if not is_indonesian(line, keep):
        return ["the line has no Indonesian in it: it needs no gloss"]
    if not gloss.strip() or gloss.strip() == line.strip():
        return ["the gloss is empty or repeats the line"]
    found = []
    # Codes and names are kept as written, so set them aside before looking for Indonesian words.
    plain = gloss
    for name in keep:
        plain = plain.replace(name, " ")
    left = _indonesian_left(ID_OR_CODE.sub(" ", plain))
    if left:
        found.append(f"the gloss still has the Indonesian word '{left}'")
    english, said = amounts(gloss), amounts(line)
    found += [f"the number {n} is missing" for n in said if n not in english]
    found += [f"the gloss adds the number {e}" for e in english if e not in said]
    if REPEAT.search(gloss):
        found.append("the gloss keeps a repeated word written with 2 (tanya2 means ask around)")
    for code in ID_OR_CODE.findall(line):
        if not re.search(rf"(?<!\w){re.escape(code)}(?!\w)", gloss):
            found.append(f"{code} is missing")
    for name in keep:
        if re.search(rf"(?<!\w){re.escape(name)}(?!\w)", line):
            if not any(form in gloss for form in PLACES.get(name, (name,))):
                found.append(f"{name} is missing")
    if not line.lstrip().startswith("{") and line.count('"') % 2 != gloss.count('"') % 2:
        found.append("the gloss has a stray quote mark")
    if (STOP in line) != (STOP in gloss):
        found.append(f"{STOP} must be kept exactly where the line has it")
    if line.count("\n") != gloss.count("\n"):
        found.append(f"the gloss has {gloss.count(chr(10))} line breaks, the line {line.count(chr(10))}")
    shape = _json_problem(line, gloss)
    if shape:
        found.append(shape)
    low, high = (0.65, 2.0) if len(line) >= 80 else (0.4, 2.5)
    if len(line) >= 40 and not low <= len(gloss) / len(line) <= high:
        found.append(f"the gloss is {len(gloss)} characters for a line of {len(line)}")
    return list(dict.fromkeys(found))


def _note(message: dict) -> str | None:
    return (((message.get("raw_data") or {}).get("toko_context") or {}).get("compaction") or {}).get("note")


def shown_lines(root: Path = ROOT) -> list[str]:
    """Every distinct line the replay shows a reader, in the order first seen: the earlier chats,
    the line drop leaves, what the customer and the agent said, the text arguments of tool calls and
    what the tools returned, the notes, the review's quotes."""
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
                add(message.get("content"))
                for call in message.get("tool_calls") or []:
                    for value in (call.get("arguments") or {}).values():
                        if isinstance(value, str):
                            add(value)
                add(_note(message))
    for item in json.loads((root / "review/2026-10-15.json").read_text(encoding="utf-8"))["items"]:
        add(item["quote"])
    return list(seen)


def load(root: Path = ROOT) -> dict[str, str | None]:
    return json.loads((root / "data" / "glosses-en.json").read_text(encoding="utf-8"))["glosses"]
