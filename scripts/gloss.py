"""Write data/glosses-en.json: an English line for every Indonesian line the replay shows.

    LLM_BASE_URL=... LLM_API_KEY=... uv run python scripts/gloss.py [--model cx/gpt-6-luna]

Glosses already in the file and passing the checks are kept; only the rest are sent, in batches.
A gloss that fails a check (toko_wa.glosses.problems) is asked for again with the reasons, twice at
most; what still fails is listed at the end and left out of the file.
"""

import argparse
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from toko_wa.glosses import GLOSSES_PATH, names, problems, shown_lines
from toko_wa.paths import DB_PATH

SYSTEM = """You translate lines from WhatsApp chats between customers and Toko Rapi Bandung, a small
clothing shop in Bandung, Indonesia, into English for readers who do not speak Indonesian. The lines
were written by customers, by the shop's admin and by AI agents serving the shop, and include the
agents' own notes, the text the agents passed to the shop's tools, and what the tools returned.
Many are informal WhatsApp Indonesian with abbreviations (yg = yang, udh/sdh =
sudah, blm = belum, tf = transfer, kmrn = kemarin, dr = dari, jd = jadi, gk/ga/gak = tidak,
rb = ribu, jt = juta, pcs = pieces); some are Sundanese or Javanese.

Translate each line into natural English that says exactly what the line says: the same facts,
requests and tone (casual stays casual). Do not add, explain or leave out anything: a short
confirmation inside a line ("detailnya sesuai", the details are right) stays in the English.

Words of this shop:
- "item" next to a colour or a product means black (slang for hitam); "abu" or "abu-abu" is grey.
- ongkir = shipping cost; resi = tracking number; rekening = bank account; mutasi = bank statement;
  kode unik = unique code (the three digits, 100 to 999 rupiah, added to a transfer total so the
  shop can match it);
  COD = cash on delivery; admin = the shop's admin.
- kak, ka, kakak, mas, mbak, bu, pak are polite forms of address: leave them out, but keep a name
  that follows them.
- [gambar] means the customer sent a picture: write [image].
- A 2 written after a word repeats the word, it is not the number two: tanya2 = tanya-tanya (ask a
  few things), liat2 = look around, pikir2 = think it over, kotak2 = checked (the pattern).
- abu-abu medium or abu medium is a shade, medium grey; it is not a size.
- teruskan ke admin means pass it on to the admin (a hand-off), not check with the admin.
- kira-kira at the start of a request softens it (could you perhaps ...); there it does not mean
  approximately.
- A month or a day keeps its English name: Oktober = October, Sabtu = Saturday; pukul = at.
- wkwk is laughter (lol); hehe stays hehe.
- The agents' fact notes use fixed labels; always translate them the same way: pesanan = order;
  alamat atau tujuan = address or destination; kurir = courier; pembayaran = payment; koreksi =
  correction; janji atau penolakan toko = shop's promise or refusal; nomor pesanan = order number;
  masih terbuka = still open.

Keep exactly as written: every number (Rp133.570 stays Rp133.570, 10.00 stays 10.00; only amounts
with rb or jt may become k or million, 227rb -> 227k), order and item IDs (ORD-1002, KS-HTM-L),
promo codes (GAJIAN10, GRATIS), sizes (S, M, L, XL), product names (Kaos Polos Cotton Combed 30s,
Kemeja Flanel Kotak, Hijab Segi Empat Voal, Celana Chino Slim Fit, Jaket Hoodie Fleece, Totebag
Kanvas), names of people, street addresses, cities and districts, banks (BCA, BRI, Mandiri, BNI),
couriers (JNE, J&T, SiCepat), phone and account numbers, links, emoji, Markdown (**bold**, lists,
line breaks) and the marker ###STOP###.

If a line is a JSON object such as {"message": "..."}, return the same JSON object, with the same
keys, as a string, translating only the human-readable text inside it.

If a line is already entirely in English, return null for it.

You receive a JSON object that maps ids to lines. Answer with one JSON object that maps every id to
its English line (or null), and nothing else."""

BATCH_CHARS = 5_000
BATCH_LINES = 20
lock = threading.Lock()


def call(model: str, messages: list[dict]) -> str:
    """One chat completion through the OpenAI-compatible gateway; waits out rate and usage limits."""
    body = json.dumps({"model": model, "messages": messages, "temperature": 0}).encode()
    request = urllib.request.Request(
        os.environ["LLM_BASE_URL"].rstrip("/") + "/chat/completions",
        data=body,
        method="POST",
        headers={"Authorization": "Bearer " + os.environ["LLM_API_KEY"], "Content-Type": "application/json"},
    )
    for attempt in range(8):
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                raw = response.read().decode()
            break
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as error:
            wait = 60 * (attempt + 1)
            print(f"  gateway: {error}; waiting {wait}s", file=sys.stderr)
            time.sleep(wait)
    else:
        raise SystemExit("the gateway kept failing")
    if raw.startswith("data:"):  # some models answer as server-sent events even without stream
        events = [line[5:] for line in raw.splitlines() if line.startswith("data:") and "[DONE]" not in line]
        parts = [json.loads(event) for event in events]
        return "".join((p["choices"][0].get("delta") or {}).get("content") or "" for p in parts)
    return json.loads(raw)["choices"][0]["message"]["content"]


def parse(answer: str) -> dict:
    answer = re.sub(r"^```(?:json)?\s*|\s*```$", "", answer.strip())
    return json.loads(answer)


def translate(model: str, lines: list[str], keep: list[str]) -> dict[str, str | None]:
    """Glosses for a batch; failures are asked again one by one with their problems."""
    ids = {str(i + 1): line for i, line in enumerate(lines)}
    try:
        answer = parse(
            call(
                model,
                [
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": json.dumps(ids, ensure_ascii=False)},
                ],
            )
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        answer = {}
    out = {}
    for key, line in ids.items():
        gloss = answer.get(key) if isinstance(answer, dict) else None
        if isinstance(gloss, dict):  # a JSON line answered as an object instead of a string
            gloss = json.dumps(gloss, ensure_ascii=False)
        for _ in range(2):
            readable = gloss is None or isinstance(gloss, str)
            found = problems(line, gloss, keep) if readable else ["not a string"]
            if not found:
                break
            retry = (
                f"Line: {json.dumps(line, ensure_ascii=False)}\nYour English: "
                f"{json.dumps(gloss, ensure_ascii=False)}\nProblems: {'; '.join(found)}.\n"
                'Translate the line again. Answer with {"1": "..."} only.'
            )
            try:
                gloss = parse(
                    call(model, [{"role": "system", "content": SYSTEM}, {"role": "user", "content": retry}])
                ).get("1")
                if isinstance(gloss, dict):
                    gloss = json.dumps(gloss, ensure_ascii=False)
            except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
                gloss = None
        out[line] = gloss
    return out


def batches(lines: list[str]) -> list[list[str]]:
    out, current, size = [], [], 0
    for line in lines:
        if current and (size + len(line) > BATCH_CHARS or len(current) >= BATCH_LINES):
            out.append(current)
            current, size = [], 0
        current.append(line)
        size += len(line)
    return out + ([current] if current else [])


def save(glosses: dict[str, str | None], model: str, order: list[str]) -> None:
    old = json.loads(GLOSSES_PATH.read_text(encoding="utf-8")) if GLOSSES_PATH.exists() else {}
    by_hand = old.get("corrected_by_hand", {})
    data = {
        "about": "English glosses for readers of the replay. The agents saw only the original lines. "
        "Written by scripts/gloss.py with the model below and checked by tests/test_glosses.py: "
        "no Indonesian left, every number, ID, code and name kept. "
        "null: the line is English already.",
        "model": model,
        "glosses": {line: glosses[line] for line in order if line in glosses},
        # glosses edited by hand after the model wrote them, with the reason; kept on every run
        "corrected_by_hand": by_hand,
    }
    tmp = GLOSSES_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(GLOSSES_PATH)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="cx/gpt-6-luna")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--limit", type=int, help="gloss only the first N lines still to do (a trial)")
    args = parser.parse_args()
    for var in ("LLM_BASE_URL", "LLM_API_KEY"):
        if not os.environ.get(var):
            raise SystemExit(f"set {var}")

    keep = names(json.loads(DB_PATH.read_text(encoding="utf-8")))
    order = shown_lines()
    glosses = json.loads(GLOSSES_PATH.read_text(encoding="utf-8"))["glosses"] if GLOSSES_PATH.exists() else {}
    todo = [line for line in order if line not in glosses or problems(line, glosses[line], keep)]
    todo = todo[: args.limit] if args.limit else todo
    print(f"{len(order)} lines shown, {len(order) - len(todo)} glossed already, {len(todo)} to do")

    done = 0
    chunks = batches(todo)

    def work(chunk: list[str]) -> None:
        nonlocal done
        result = translate(args.model, chunk, keep)
        with lock:
            for line, gloss in result.items():
                if not problems(line, gloss, keep):
                    glosses[line] = gloss
                elif not problems(line, None, keep):
                    # not Indonesian: the model echoed it or edited it, and no gloss is needed
                    glosses[line] = None
            save(glosses, args.model, order)
            done += 1
            print(f"  batch {done}/{len(chunks)}", flush=True)

    with ThreadPoolExecutor(args.workers) as pool:
        list(pool.map(work, chunks))

    failing = [line for line in order if line not in glosses]
    print(f"{len(order) - len(failing)} of {len(order)} lines glossed; {len(failing)} still failing")
    for line in failing[:40]:
        print("  -", line[:160].replace("\n", " "), "|", "; ".join(problems(line, None, keep)))


if __name__ == "__main__":
    main()
