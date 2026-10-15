"""The meaning checks against Indonesian chat's own habits, and against the wrong English an independent
review wrote to slip past the first version of them (2026-10-15). Each wrong gloss below keeps every
number and name of its line; only its meaning changed."""

import pytest

from toko_wa.meaning import problems


@pytest.mark.parametrize(
    "line, gloss, problem",
    [
        # a not lost, added, hidden behind a later question, or said in Sundanese, Javanese or a contraction
        ("Maaf Kak, stoknya belum ada.", "Sorry, it's in stock.", "the line says not"),
        ("Sudah dibayar kak, tinggal kirim.", "It has not been paid, just ship it.", "the gloss says not"),
        ("Bisa COD kak, ke Bandung.", "COD isn't possible to Bandung.", "the gloss says not"),
        (
            "Saya belum membuat pesanan baru—Kakak setuju saya buat dengan rincian tersebut?",
            "I created the new order. Do you agree I make it with those details?",
            "the line says not",
        ),
        ("Punten Kak, duanana teu tiasa COD.", "Sorry, both support COD.", "the line says not"),
        ("Kak, hoodie hitam gaada", "The black hoodie is available.", "the line says not"),
        ("mboten kak, kula pesen sing M", "Yes, I order the M.", "the line says not"),
        (
            "Kode unik tilu angka can ditetepkeun.",
            "The three-digit unique code has been set.",
            "the line says not",
        ),
        # nots English says with another word
        ("gak jadi beli hoodie nya kak", "I will buy the hoodie.", "calls something off"),
        ("Tidak apa-apa Kak, kami kirim besok.", "It's a problem, we ship tomorrow.", "it's fine"),
        ("stok hitam M habis kak", "Black M is in stock.", "out of stock"),
        ("ukuran L kosong kak", "Size L is available.", "out of stock"),
        ("Pesanan ORD-1006 dibatalkan ya kak", "Order ORD-1006 is confirmed.", "cancelled"),
        ("promo GAJIAN10 sudah berakhir", "The GAJIAN10 promo has started.", "ended"),
        ("COD tanpa ongkir ya", "COD with shipping.", "without"),
        # inside a tool's JSON
        (
            '{"message": "Maaf Kak, promonya belum bisa saya verifikasi."}',
            '{"message": "Sorry, I have verified the promotion."}',
            "message: the line says not",
        ),
        # a statement made a question, a question made a statement
        (
            "Ongkir JNE ke Bandung Rp9.000 atau J&T Rp8.000.",
            "Is JNE shipping to Bandung Rp9.000 or J&T Rp8.000?",
            "asks a question the line does not",
        ),
        (
            "Tidak apa-apa Kak, kami kirim besok.",
            "Is that okay? We ship tomorrow.",
            "asks a question the line does not",
        ),
        ("Saya cek dulu ya.", "Shall I check first?", "asks a question the line does not"),
        ("Belum Kak.", "Not yet?", "asks a question the line does not"),
        (
            "Siap, hoodie nya dikirim besok ya",
            "Okay, will the hoodie be sent tomorrow?",
            "asks a question the line does not",
        ),
        (
            "Mohon konfirmasi alamatnya ya Kak. Mau dikirim pakai JNE atau J&T?",
            "Please confirm the address. We will ship by JNE or J&T.",
            "the line asks a question",
        ),
        (
            "Alamatnya sudah benar? Mau dikirim hari ini?",
            "Could you please confirm the address?",
            "the line asks a question",
        ),
        # the time of day, an hour, a 24-hour time, their order
        (
            "Siap Kak, pesanan dikirim besok pagi.",
            "Okay, the order ships tomorrow evening.",
            "another time of day",
        ),
        (
            "malem kak, mau tanya kemeja flanel masih ada?",
            "Good morning, is the flannel shirt still available?",
            "another time of day",
        ),
        ("Dikirim jam 7.30 malam ya kak", "It ships at 7:30 am.", "wrong half of the day"),
        ("Dikirim jam 12 siang ya kak", "It ships at 12 am.", "wrong half of the day"),
        ("Dikirim jam 11 siang ya kak", "It ships at 11 pm.", "wrong half of the day"),
        ("Status terakhir pukul 21:45 ya Kak.", "The latest status is at 9:45 AM.", "wrong half of the day"),
        ("Buka jam 9 pagi sampai jam 9 malam", "Open from 9 pm until 9 am", "another order"),
        (
            "Tokonya tutup sore, buka lagi besok pagi.",
            "The shop closes in the morning and opens again tomorrow evening.",
            "another order",
        ),
        # days, relative days, spans
        ("Dikirim hari Jum’at ya kak", "It ships on Monday, okay?", "Friday is missing"),
        ("Senin sampai Jumat buka", "Open Friday to Monday", "another order"),
        ("Dikirim hari Senin ya kak", "Shipped Monday and Friday.", "the gloss adds Friday"),
        ("Sabtu minggu libur ya kak", "Closed on Saturday, open next week.", "Sunday is missing"),
        ("Dikirim besok ya kak", "It was shipped yesterday.", "tomorrow"),
        ("Estimasi 2-3 hari kerja", "Estimate 2-3 weeks", "span"),
        # the second review (2026-10-16): a not said twice, slang and Sundanese nots, a not moved
        (
            "Transfer Rp227.000 sudah kami terima, tetapi belum sesuai total.",
            "We haven't received the Rp227.000 transfer, but it doesn't match the total.",
            "the gloss says not",
        ),
        (
            "Stok M belum ada dan ongkir tidak gratis.",
            "M is in stock. Shipping isn't free.",
            "the line says not",
        ),
        ("stoknya sudah tidak ada kak.", "It is in stock.", "the line says not"),
        ("udah transfer belum kak", "I have transferred.", "the line asks a question"),
        ("bisa COD ga kak", "COD is possible.", "the line asks a question"),
        ("kaga bisa COD", "COD is possible.", "the line says not"),
        ("stok M abis kak", "M is in stock.", "out of stock"),
        (
            "Hijau: M, L (ukuran XL sedang habis). COD tidak tersedia.",
            "Green: M, L (size XL is in stock). COD isn't available.",
            "out of stock",
        ),
        # opposites
        ("Promo GAJIAN10 berlaku sampai 31 Oktober", "The GAJIAN10 promo is valid from 31 October", "until"),
        ("Paket tertahan sejak 11 Oktober 2026", "The package has been held until 11 October 2026", "since"),
        ("Total Rp225.000 sebelum kode unik", "Total Rp225.000 after the unique code", "before"),
        ("Nominal kurang Rp459 dari total", "The amount is Rp459 more than the total", "less than"),
        ("Pembayaran sudah lunas", "Payment is still outstanding", "paid in full"),
        ("Ongkir gratis ke Bandung", "Shipping to Bandung costs extra", "free"),
        ("Harga naik jadi Rp199.000", "The price dropped to Rp199.000", "up"),
        ("hoodie nya lebih tebal dari kaos", "the hoodie is thinner than the T-shirt", "tebal"),
        ("dikirim dari gudang Bandung", "shipped to the Bandung warehouse", "from Bandung"),
        ("Kakak minta ukuran L, bukan M", "You asked for size M, not L", "not M"),
        ("Tiba dalam 3 hari", "Arrives 3 days ago.", "ago"),
        # when
        ("Dikirim hari Jumat depan", "It ships this Friday.", "the coming Friday"),
        ("Dikirim hari Jumat ya kak", "It ships next Friday.", "next Friday"),
        ("Kemarin dikirim, besok sampai", "Tomorrow it ships, yesterday it arrives", "another order"),
        ("Dikirim besok kak", "It ships the day after tomorrow.", "day after tomorrow"),
        ("Garansi 7 hari, retur 1 bulan", "Warranty 7 months, returns 1 day", "swapped"),
        ("Buka jam 8 pagi sampai 10 malam", "Open 8 am to 10 am", "wrong half of the day"),
        ("Buka jam 9 pagi sampai jam 9 malam", "Open from 9 am until 9 am", "wrong half of the day"),
        ("Promo berlaku minggu ini", "The promo ends last week", "this week"),
        # English that stops short
        (
            "Paketnya tertahan di gudang dan saya teruskan ke admin ya Kakak",
            "The package is held at the warehouse and I'll pass it to",
            "stops before the end",
        ),
        ("Saya teruskan ke admin ya Kak. 🙏", "I will pass it on to the admin, 🙏", "stops before the end"),
    ],
)
def test_wrong_english_is_caught(line, gloss, problem):
    found = problems(line, gloss)
    assert any(problem in f for f in found), found


@pytest.mark.parametrize(
    "line, gloss",
    [
        # nots English says another way
        ("stok hitam M tidak ada kak", "Black M is out of stock."),
        ("jangan lupa transfer ya kak", "Remember to transfer, okay?"),
        ("warnanya tidak sama kak sama di foto", "The color is different from the photo."),
        ("belum dikirim kak", "It is still pending shipment."),
        ("tidak ada masalah kak", "It's fine."),
        ("promonya sudah tidak berlaku kak", "The promo has expired."),
        ("Total Rp225.000 belum termasuk kode unik", "Rp225.000 before the unique code"),
        (
            "Jika ada pertanyaan lain, jangan sungkan hubungi kami ya.",
            "If you have any other questions, feel free to contact us.",
        ),
        ("Tidak sampai 1 jam sudah selesai.", "It will be done in under 1 hour."),
        ("gak usah kak", "That's okay."),
        ("Kode unik tilu angka can ditetepkeun.", "The three-digit unique code hasn't been set yet."),
        ("Tidak tersedia/tidak tercatat di sistem kami.", "It isn't available or listed in our system."),
        # nots that only ask
        ("bisa gak dikirim hari ini kak", "Can it be shipped today?"),
        ("udah transfer belum kak", "Have you transferred yet?"),
        ("udah sampe belum paketnya", "Has the package arrived yet?"),
        ("udah bayar belum Rp227.459 itu kak?", "Have you paid that Rp227.459 yet?"),
        # questions with no "?", tags English renders "…, okay?", one question said in two
        ("siap kak, aku tf sekarang ya###STOP###", "Okay, I'll transfer now, okay?###STOP###"),
        (
            "iya kak, nomor 2 dari list hijab kemarin ya 🙏",
            "Yes, number 2 from yesterday's hijab list, okay? 🙏",
        ),
        ("Kalau sudah sesuai, balas “ya” ya, Kak.", "If everything looks right, reply “yes,” okay?"),
        ("kenapa belum dikirim kak", "Why hasn't it been shipped?"),
        ("kak bahan hoodie nya tebel ga", "Is the hoodie material thick?"),
        ("kaos polos warnanya apa aja", "What colors are the plain T-shirts available in?"),
        (
            "eh btw paket aku yg kemarin kok blm sampe ya kak. bisa dicek?",
            "Oh, why hasn't my package from yesterday arrived yet? Can you check?",
        ),
        ("kok blm nyampe??", "Why hasn't it arrived yet?"),
        ("halo?? ada orang??", "Hello? Anyone there?"),
        ("Kakak mau pakai kurir JNE atau J&T?", "Which courier? JNE or J&T?"),
        (
            "Bagaimana Kak, apakah mau tetap dilanjutkan?",
            "What do you think? Would you still like to proceed?",
        ),
        ("Boleh minta alamatnya kak?", "Please send me your address."),
        ("alamatnya ganti ke kantor aja ya kak", "Could you change the address to my office?"),
        ("sabaraha ongkirna ka Garut kak", "How much is shipping to Garut?"),
        # times of day, hours, days
        (
            "Selamat malam Kak, pesanan dikirim besok pagi ya.",
            "Good evening! Your order ships tomorrow morning.",
        ),
        ("Pesanan di atas jam 12 malam diproses besok.", "Orders after 12 am are processed tomorrow."),
        ("Tokonya tutup jam 1 malam ya.", "The shop closes at 1 am."),
        (
            "Pelanggan pamit tidur dan memesan besok pagi.",
            "The customer said good night and will order tomorrow morning.",
        ),
        ("Sabtu Minggu libur kak", "We are closed on weekends."),
        ("Senin-Jumat buka jam 9", "Open on weekdays at 9."),
        ("Minggu kemarin aku beli di toko lain", "Last week I bought one at another store."),
        ("Libur hari Kamis", "Off on Thurs."),
        ("biasanya akan diantar dalam 1-2 hari ini", "it's usually delivered within the next 1–2 days"),
        ("Berikut daftar warnanya.", "Here is the list of colors:"),
        # from the second review: English that says it another way
        ("ukuran apa aja ya kak", "What sizes are there?"),
        (
            "Total Rp225.000 belum termasuk kode unik",
            "The total is Rp225.000, with the unique code still to be added.",
        ),
        ("Stok hijau habis", "Green is out."),
        ("Sama-sama kak", "Don't mention it."),
        ("Buka jam 9 pagi sampai jam 9 malam", "Open 9AM-9PM"),
        ("Minggu yang lalu aku beli di toko lain", "Last week I bought one at another store."),
        ("Ini yang kakak maksud, bukan?", "This is what you meant, right?"),
        ("paketnya belum sampai kak", "The package is still in transit."),
        ("Mohon tunggu sebentar ya kak", "Mind waiting a moment?"),
        ("Silakan pilih kurirnya", "Which courier would you like?"),
        (
            "Iya Kak, betul dana Rp227.000 sudah masuk di mutasi kami.",
            "Yes, the Rp227,000 has come through on our bank statement.",
        ),
        (
            "Agar tidak salah, mohon kirim ulang rinciannya.",
            "To avoid any mistakes, please send the details again.",
        ),
        (
            "Nanging kanggo ka Garut, punten teu acan tiasa COD.",
            "However, COD isn't available for delivery to Garut.",
        ),
        ("tidak tersedia atau tidak tercatat di sistem kami", "It isn't available or listed in our system"),
        ("totalnya jadi berapa kak", "So what's the total"),
        ("ini punya siapa", "Whose is this"),
        ("Pelanggan Bandung ke Bandung.", "The customer is from Bandung to Bandung."),
    ],
)
def test_right_english_passes(line, gloss):
    assert problems(line, gloss) == []
