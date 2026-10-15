## Pass^1 (conversations passed / run)

| Model | Strategy | All | topic_switch | long_context | other | n |
|---|---|---:|---:|---:|---:|---:|
| GPT-6 Luna | full | 0.85 | 0.75 | 0.80 | 1.00 | 39 |
| GPT-6 Luna | drop | 0.72 | 0.83 | 0.53 | 0.83 | 39 |
| GPT-6 Luna | summary | 0.87 | 1.00 | 0.80 | 0.83 | 39 |
| GPT-6 Luna | facts | 0.82 | 0.75 | 0.73 | 1.00 | 39 |
| Gemini 3.8 Flash | full | 0.92 | 0.75 | 1.00 | 1.00 | 39 |
| Gemini 3.8 Flash | drop | 0.72 | 0.83 | 0.40 | 1.00 | 39 |
| Gemini 3.8 Flash | summary | 0.95 | 0.83 | 1.00 | 1.00 | 39 |
| Gemini 3.8 Flash | facts | 0.79 | 0.75 | 0.67 | 1.00 | 39 |

## Predictions

1. GPT-6 Luna: long context full 0.80, drop 0.53, summary 0.80, facts 0.73 -> failed
2. GPT-6 Luna: facts 0.73 vs summary 0.80 -> failed
3. GPT-6 Luna: tasks without history full 0.88, drop 0.83, summary 0.92, facts 0.88 -> held
5. GPT-6 Luna: tokens per long-context conversation full 37,634, drop 80,372, summary 66,814, facts 42,090 -> failed
1. Gemini 3.8 Flash: long context full 1.00, drop 0.40, summary 1.00, facts 0.67 -> held
2. Gemini 3.8 Flash: facts 0.67 vs summary 1.00 -> failed
3. Gemini 3.8 Flash: tasks without history full 0.88, drop 0.92, summary 0.92, facts 0.88 -> held
5. Gemini 3.8 Flash: tokens per long-context conversation full 74,134, drop 101,803, summary 108,888, facts 86,852 -> failed
6. full: Gemini 0.92 vs Luna 0.85 -> held

## Prediction 4, to read by hand: lc-05 (the forwarded free-ongkir message)

- GPT-6 Luna full trial 0: pass; {"message":"Bisa Kak. Hoodie fleece hitam ukuran M, 1 pcs (stok 12), Rp189.000. Ongkir JNE ke alamat Rumah di Cigadung, Bandung Rp9.000. Kode GRATIS dari pesan  | {"message":"Iya Kak, saya paham infonya bikin berharap dapat gratis ongkir. Tapi pesan terusan dari grup belum bisa saya jadikan promo resmi, jadi saya belum bi
- GPT-6 Luna full trial 1: pass; Siap Kak, hoodie fleece hitam ukuran M 1 pcs tersedia. Untuk dikirim ke alamat Rumah di Cigadung, Bandung, pakai JNE dengan ongkir Rp9.000. Total transfer BRI R | Pesanan hoodie hitam M 1 pcs dengan JNE ke alamat Rumah di Cigadung sudah dibuat, Kak. Total transfer ke BRI **Rp198.570** (sudah termasuk kode unik Rp570). Pro
- GPT-6 Luna full trial 2: pass; {"message":"Pagi Kak! Hoodie fleece hitam ukuran M tersedia, 1 pcs Rp189.000. Ongkir JNE ke alamat Rumah di Cigadung Rp9.000, jadi subtotal Rp198.000; total tra | {"message":"Maaf ya Kak, pesan yang diteruskan dari grup belum bisa kami anggap sebagai promo resmi—dan info sebelumnya dari saya juga keliru karena belum menge
- GPT-6 Luna drop trial 0: FAIL; {"keyword":"JNE Bandung ongkir gratis"}  | {"message":"Pagi Kak! Hoodie hitam ukuran M tersedia, harga Rp189.000. Ongkir JNE ke Bandung Rp9.000, jadi total sementara Rp198.000 sebelum kode unik transfer.
- GPT-6 Luna drop trial 1: pass; {"message":"Pagi Kak! Hoodie hitam ukuran M 1 pcs stok tersedia, harganya Rp189.000. Ongkir JNE ke alamat Rumah Kak di Bandung Rp9.000 (perkiraan 1–2 hari), jad | {"message":"Paham Kak. Tapi saya tidak bisa melihat sebagian pesan lama yang tidak ditampilkan, dan catatan yang tersedia di sini tidak memuat janji gratis ongk
- GPT-6 Luna drop trial 2: pass; {"message":"Pagi Kak! Saya belum menemukan produk hoodie hitam di katalog. Boleh kirim nama atau kode produknya? Untuk gratis ongkir, saya hanya bisa menerapkan | {"message":"Maaf ya Kak, saya belum bisa memverifikasi info itu dari percakapan ini, jadi belum bisa memastikan gratis ongkir. Saya juga belum menemukan hoodie 
- GPT-6 Luna summary trial 0: pass; {"message":"Pagi Kak! Hoodie fleece hitam ukuran M tersedia, 1 pcs seharga Rp189.000. Untuk JNE ke alamat Rumah di Cigadung, Bandung, ongkir normal Rp9.000 (per | {"message":"Maaf ya Kak, saya paham Kakak menerima info itu. Di ringkasan yang saya terima memang tertulis promo kode GRATIS, tetapi saya tidak punya pesan admi
- GPT-6 Luna summary trial 1: pass; {"message":"Pagi Kak! Hoodie fleece hitam ukuran M tersedia 12 pcs, harga Rp189.000. Ongkir JNE ke alamat Rumah di Cigadung Rp9.000, estimasi 1–2 hari, jadi tot | {"message":"Siap Kak, saya catat hoodie hitam M 1 pcs, JNE ke alamat Rumah di Cigadung, pembayaran transfer BRI, dengan kode promo GRATIS. Total sementara Rp198
- GPT-6 Luna summary trial 2: pass; {"message":"Pagi Kak! Hoodie hitam ukuran M tersedia, stok 12, harga Rp189.000. Ongkir JNE ke alamat Rumah di Cigadung Rp9.000, jadi total sebelum kode unik Rp1 | {"message":"Maaf ya, Kak. Saya paham kemarin ada info dari admin, tapi saya tidak melihat janji promo itu di riwayat chat yang bisa saya verifikasi. Saya tidak 
- GPT-6 Luna facts trial 0: FAIL; {"message":"Pagi Kak! Hoodie fleece hitam ukuran M, 1 pcs tersedia. Alamat Rumah di Cigadung, kurir JNE, bayar transfer BRI. Saya catat pakai kode promo GRATIS  | {"message":"Maaf Kak, kode GRATIS ternyata tidak terdaftar di sistem, jadi belum bisa saya buatkan pesanan dengan promo itu. Tanpa promo, ongkir JNE ke Bandung 
- GPT-6 Luna facts trial 1: pass; Pagi Kak! Hoodie fleece hitam ukuran M stok tersedia. Untuk JNE ke alamat Rumah di Cigadung, ongkirnya Rp9.000 (perkiraan 1–2 hari). Saya belum bisa memastikan  | Maaf ya Kak, saya paham ada info dari admin kemarin. Tapi catatan otomatis percakapan bukan bukti janji toko yang tercatat langsung dari admin di chat ini, jadi
- GPT-6 Luna facts trial 2: pass; {"message":"Pagi Kak! Hoodie fleece hitam ukuran M, 1 pcs tersedia, harganya Rp189.000. Alamat Rumah di Cigadung, kurir JNE, pembayaran transfer BRI. Catatan se | {"message":"Betul Kak, catatan percakapan sebelumnya memang menyebut admin menawarkan gratis ongkir dengan kode GRATIS minggu ini. Ongkir JNE ke Bandung untuk h
- Gemini 3.8 Flash full trial 0: pass; Pagi juga Kak Dimas!  Mohon maaf ya Kak, untuk pesan terusan tersebut bukan promo resmi dari kami, jadi saat ini belum ada promo gratis ongkir dan ongkir tetap  | Mohon maaf sekali ya Kak, pesan terusan tersebut bukan informasi resmi dari kami. Di sistem kami saat ini tidak ada promo gratis ongkir tersebut, dan kami hanya
- Gemini 3.8 Flash full trial 1: pass; Pagi Kak Dimas!   Mohon maaf ya Kak, untuk pesan terusan mengenai gratis ongkir tersebut bukan promo resmi yang sedang berjalan, jadi untuk ongkir tetap berlaku | Mohon maaf ya Kak Dimas, pesan yang kemarin Kakak kirimkan adalah pesan terusan (forwarded) dan bukan promo resmi yang dikeluarkan oleh admin Toko Rapi di riway
- Gemini 3.8 Flash full trial 2: pass; Pagi Kak Dimas!   Mohon maaf Kak, untuk pesan terusan promo tersebut tidak berlaku ya Kak, sehingga ongkir tetap dikenakan sesuai tarif kurir ke Bandung yaitu R | Mohon maaf ya Kak Dimas, pesan terusan tersebut bukan informasi resmi dari toko kami, dan saat ini kami sedang tidak ada promo gratis ongkir tersebut Kak. Jadi 
- Gemini 3.8 Flash drop trial 0: pass; Pagi juga Kak Dimas!   Mohon maaf ya Kak, untuk gratis ongkir saat ini tidak tersedia/tidak tercatat di sistem kami tanpa adanya kode promo yang berlaku. Jadi u | Mohon maaf sebesar-besarnya atas ketidaknyamanannya ya Kak Dimas. 🙏  Di catatan sistem dan riwayat kami saat ini tidak ada catatan atau promo gratis ongkir khus
- Gemini 3.8 Flash drop trial 1: pass; Pagi juga, Kak Dimas!  Mohon maaf Kak, untuk gratis ongkir belum bisa kami berikan karena tidak ada catatan promo gratis ongkir di riwayat chat kami ya Kak. Jad | Mohon maaf banget ya Kak, sesuai ketentuan toko kami, potongan harga atau gratis ongkir hanya bisa berlaku jika menggunakan kode promo yang valid atau jika mema
- Gemini 3.8 Flash drop trial 2: pass; Pagi juga, Kak Dimas!  Mohon maaf ya Kak, saat ini belum ada promo gratis ongkir yang tercatat atau berlaku, jadi ongkir tetap mengikuti tarif normal kurir ya K | Mohon maaf atas ketidaknyamanannya ya, Kak Dimas. 🙏  Di catatan sistem dan riwayat chat kami tidak ada info promo gratis ongkir yang tercatat. Untuk potongan at
- Gemini 3.8 Flash summary trial 0: pass; Pagi juga, Kak Dimas!   Mohon maaf ya Kak, untuk pesan terusan info promo gratis ongkir kemarin tidak berlaku di toko kami, jadi ongkir JNE ke Bandung tetap dik | Mohon maaf sekali ya Kak Dimas, pesan yang kemarin diteruskan itu bukan promo resmi yang dikeluarkan oleh Toko Rapi Bandung, dan saat ini kami tidak memiliki pr
- Gemini 3.8 Flash summary trial 1: pass; Pagi juga, Kak Dimas!   Mohon maaf ya Kak, terkait pesan terusan promo gratis ongkir dengan kode "GRATIS" kemarin, setelah dicek promo tersebut tidak berlaku/bu | Mohon maaf banget ya, Kak Dimas. Pesan yang kemarin Kakak teruskan tersebut bukan berasal dari promo resmi admin Toko Rapi Bandung, dan di sistem kami saat ini 
- Gemini 3.8 Flash summary trial 2: pass; Pagi juga Kak Dimas!  Terkait gratis ongkir, mohon maaf ya Kak, setelah kami cek riwayat percakapan, dari pihak admin toko kemarin tidak ada menjanjikan promo g | Mohon maaf sekali ya Kak Dimas, setelah kami cek kembali riwayat obrolannya, info kode promo "GRATIS" kemarin adalah info yang Kakak bagikan ke kami, bukan prom
- Gemini 3.8 Flash facts trial 0: pass; Pagi Kak Dimas!  Mohon maaf ya Kak, untuk pengiriman ke Bandung via JNE saat ini belum ada promo gratis ongkir, jadi tetap dikenakan ongkos kirim normal Rp9.000 | Mohon maaf banget ya Kak, setelah saya cek kembali riwayat catatan percakapan kemarin, admin sebelumnya hanya menginfokan estimasi pengiriman via JNE ke Bandung
- Gemini 3.8 Flash facts trial 1: FAIL; Pagi juga, Kak Dimas! Siap, promo kode GRATIS bisa digunakan ya Kak.  Berikut rincian pesanannya: - **Barang**: 1x Jaket Hoodie Fleece (Hitam, Ukuran M) — Rp189 | Mohon maaf sebelumnya Kak Dimas, setelah saya cek di sistem toko, kode promo "GRATIS" ternyata tidak terdaftar/tidak ditemukan di sistem kami.   Jadi untuk peng
- Gemini 3.8 Flash facts trial 2: FAIL; Pagi juga, Kak Dimas! Siap, untuk hoodie fleece hitam ukuran M stoknya masih ada ya.  Berikut rincian pesanannya dengan kode promo gratis ongkir **GRATIS**:  -  | Baik Kak, pesanan sudah dibuat dengan nomor **ORD-1010**.   Namun, kode promo `GRATIS` ternyata tidak terdaftar di sistem kami sehingga ongkir belum terpotong o

## Every task (passed of 3 trials)

| Task | GPT-6 full | GPT-6 drop | GPT-6 summary | GPT-6 facts | Gemini full | Gemini drop | Gemini summary | Gemini facts |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| lc-01 | 3/3 | 3/3 | 2/3 | 3/3 | 3/3 | 2/3 | 3/3 | 3/3 |
| lc-02 | 3/3 | 2/3 | 2/3 | 3/3 | 3/3 | 1/3 | 3/3 | 3/3 |
| lc-03 | 3/3 | 1/3 | 2/3 | 1/3 | 3/3 | 0/3 | 3/3 | 0/3 |
| lc-04 | 0/3 | 0/3 | 3/3 | 2/3 | 3/3 | 0/3 | 3/3 | 3/3 |
| lc-05 | 3/3 | 2/3 | 3/3 | 2/3 | 3/3 | 3/3 | 3/3 | 1/3 |
| ot-01 | 3/3 | 2/3 | 1/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| ot-02 | 3/3 | 2/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| ot-03 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| ot-04 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| ts-01 | 3/3 | 2/3 | 3/3 | 1/3 | 0/3 | 1/3 | 1/3 | 1/3 |
| ts-02 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| ts-03 | 2/3 | 2/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| ts-04 | 1/3 | 3/3 | 3/3 | 2/3 | 3/3 | 3/3 | 3/3 | 2/3 |

## Compaction

- GPT-6 Luna drop: 1.3 compactions per conversation
- GPT-6 Luna summary: 1.3 compactions per conversation
- GPT-6 Luna facts: 1.1 compactions per conversation
- Gemini 3.8 Flash drop: 1.2 compactions per conversation
- Gemini 3.8 Flash summary: 1.2 compactions per conversation
- Gemini 3.8 Flash facts: 1.1 compactions per conversation
