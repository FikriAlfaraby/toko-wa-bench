"""The English glosses: one for every Indonesian line the replay shows, each saying the same thing,
and none of them anywhere an agent could read it."""

import json
import re
from pathlib import Path

import pytest

from toko_wa.glosses import GLOSSES_PATH, is_indonesian, names, problems, shown_lines
from toko_wa.paths import DB_PATH

ROOT = Path(__file__).resolve().parents[1]
GLOSSES = json.loads(GLOSSES_PATH.read_text(encoding="utf-8"))["glosses"]
KEEP = names(json.loads(DB_PATH.read_text(encoding="utf-8")))


def test_every_line_the_replay_shows_has_an_entry_in_order_and_nothing_else_does():
    assert list(GLOSSES) == shown_lines()


def test_every_gloss_passes_the_checks():
    failing = {line[:80]: found for line, gloss in GLOSSES.items() if (found := problems(line, gloss, KEEP))}
    assert not failing


def test_a_line_has_a_gloss_exactly_when_it_has_indonesian_in_it():
    for line, gloss in GLOSSES.items():
        assert (gloss is None) == (not is_indonesian(line, KEEP)), line


@pytest.mark.parametrize(
    "line, gloss, problem",
    [
        ("Totalnya Rp133.570 ya Kak.", "The total is the amount.", "the number 133570 is missing"),
        ("Totalnya Rp133.570 ya Kak.", "The total is Rp133.570, 2 items.", "the gloss adds the number 2"),
        ("kak mau tanya2 dulu", "I want to ask 2 things first.", "the gloss adds the number 2"),
        ("aku pikir2 dulu ya", "I'll think it over2 first.", "a repeated word written with 2"),
        ("Siap Kak, dikirim besok.", "Siap, it ships tomorrow.", "the Indonesian word 'Siap'"),
        ("Sudah dikirim ya Kak.", "Sudah shipped.", "the Indonesian word 'Sudah'"),
        ("Pesanan ORD-1002 sudah dibayar.", "Your order has been paid.", "ORD-1002 is missing"),
        ("Pakai kode GAJIAN10 ya.", "Use the promo code.", "GAJIAN10 is missing"),
        ("Dikirim ke Bekasi ya Kak.", "It will be sent to your mum's.", "Bekasi is missing"),
        ("Transfer ke BCA ya.", "Transfer to the bank.", "BCA is missing"),
        ("Halo Kak Rina, ada yang bisa dibantu?", "Hi, how can I help?", "Rina is missing"),
        ("ok makasih kak###STOP###", "ok thanks", "###STOP### must be kept"),
        ('{"message": "Halo Kak, ada yang bisa dibantu?"}', "Hi, how can I help?", "a JSON object"),
        ("Pesanan sudah dibuat dan besok pagi dikirim lewat JNE ke alamat Kakak.", "Done.", "is 5 chara"),
        ("Halo Kak, ada yang bisa dibantu?", None, "the line is Indonesian but has no gloss"),
        ('{"phone":"6281234500002"}', '{"phone":"6281234500002"}', "it needs no gloss"),
        # a wrong amount must not pass because its digits start the same
        ("dapat potongan 10% ya", "you get 100% off", "the gloss adds the number 100"),
        ("mau 2 hoodie ya kak", "I want 20 hoodies.", "the gloss adds the number 20"),
        ("Ongkir ke Bandung Rp18.000 ya", "Shipping to Bandung is Rp180.000.", "the number 18000 is missing"),
        ("udh tf 227rb ya", "I've transferred 227 million.", "the number 227000 is missing"),
        ("transfer 1,5jt ya", "transfer 15 million", "the number 1500000 is missing"),
        ("Pesanan ORD-1010 sudah dibayar.", "Order ORD-10100 is paid.", "ORD-1010 is missing"),
        ("Pesanan:\n- 2 kaos\n- 1 hoodie", "Order: 2 T-shirts, 1 hoodie", "line breaks"),
        (
            "Baik Kak, pesanan ORD-1003 sudah saya cek, paketnya tertahan di gudang J&T Bandung "
            "sejak tanggal 11.",
            "Okay, I checked ORD-1003 at J&T Bandung on the 11th.",
            "characters for a line of",
        ),
    ],
)
def test_each_kind_of_wrong_gloss_is_caught(line, gloss, problem):
    found = problems(line, gloss, KEEP)
    assert any(problem in f for f in found), found


@pytest.mark.parametrize(
    "line, gloss",
    [
        ("udh tf 227rb ya kak", "I've transferred 227k."),
        ("udh tf 227rb ya kak", "I've transferred Rp227,000."),
        ("Ongkir ke Jakarta Selatan Rp18.000 ya Kak.", "Shipping to South Jakarta is Rp18.000."),
        ("jam 10.00 ya kak", "At 10:00, please."),
        ('{"message": "Halo Kak, ada yang bisa dibantu?"}', '{"message": "Hi, how can I help?"}'),
        ('{"phone":"6281234500002"}', None),
        ("Ongkir Rp2.000 ya kak", "Shipping is Rp2.000."),
        ("hoodie x2 ya kak", "Hoodie x2, please."),
        ("Pesanan ORD-1003 dikirim ke alamat C007-A1 ya.", "Order ORD-1003 will be sent to address C007-A1."),
        # a capitalised English name is not an Indonesian word
        ("Kirim ke Dan ya kak", "Send it to Dan, please."),
    ],
)
def test_a_right_gloss_passes(line, gloss):
    assert problems(line, gloss, KEEP) == []


def test_the_lines_the_findings_rest_on_say_in_english_what_they_say_in_indonesian():
    # lc-04: with the whole chat, Luna called the shop's own promise its mistake.
    assert "wrong" in GLOSSES["saya keliru menjanjikannya"].lower()
    # The line drop leaves in place of the earlier chat.
    hidden = GLOSSES["[Sebagian pesan lama dalam percakapan ini tidak ditampilkan.]"].lower()
    assert "not shown" in hidden or "hidden" in hidden
    # lc-05: the fact notes that filed the forwarded fake promo as the shop's own promise.
    laundered = [line for line in GLOSSES if "janji atau penolakan toko" in line and "GRATIS" in line]
    assert laundered
    for line in laundered:
        assert "GRATIS" in GLOSSES[line] and "free shipping" in GLOSSES[line].lower(), line
    # "item" is slang for black: every line that uses it says black in English.
    black = [line for line in GLOSSES if re.search(r"\bitem\b", line) and not line.lstrip().startswith("{")]
    assert len(black) >= 3
    for line in black:
        assert "black" in GLOSSES[line].lower(), line
    # The notes' labels read the same everywhere, so the page can quote "shop's promise or refusal".
    for line, gloss in GLOSSES.items():
        if "janji atau penolakan toko:" in line:
            assert "shop's promise or refusal" in gloss.replace("’", "'"), gloss


def test_the_phrases_the_first_translation_misread_now_read_right():
    for line, gloss in GLOSSES.items():
        low = (gloss or "").lower()
        if re.search(r"abu(-abu)? medium", line, re.I):
            assert re.search(r"medium[- ]gr[ae]y", low), gloss
        if re.search(r"teruskan .{0,12}ke admin", line, re.I):
            assert "check with" not in low and re.search(r"\b(pass|forward|hand|refer|escalat)", low), gloss
        if "detailnya sesuai" in line:
            assert "detail" in low, gloss
        if re.search(r"\bkira-kira bisa", line, re.I):
            assert "approximately" not in low, gloss


def test_every_gloss_edited_by_hand_says_why_and_still_passes():
    data = json.loads(GLOSSES_PATH.read_text(encoding="utf-8"))
    for line, why in data["corrected_by_hand"].items():
        assert why.strip() and line in GLOSSES and not problems(line, GLOSSES[line], KEEP), line
    # The agent searched for the customer's own words; the gloss keeps them, so the reader sees why it failed.
    assert any("“kaos polos item”" in (gloss or "") for gloss in GLOSSES.values())


def test_the_glosses_and_the_policy_translation_never_reach_an_agent():
    for path in sorted((ROOT / "src" / "toko_wa").glob("*.py")) + [ROOT / "scripts" / "run.py"]:
        if path.name == "glosses.py":
            continue
        text = path.read_text(encoding="utf-8")
        assert "glosses" not in text and "policy.en" not in text, path.name
