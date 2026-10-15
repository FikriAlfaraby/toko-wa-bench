"""The database behind data/toko_wa/db.json: a small Bandung clothing shop that sells over WhatsApp.

Past orders are made with the same tools the agent uses (create_order, confirm_payment), with the
shop clock set back, so every total, kode unik and stock count follows the shop's rules.
Every name, number and address is made up.

Written by scripts/make_db.py; tests build it fresh.
"""

from toko_wa.data_model import (
    Address,
    BankTransfer,
    Chat,
    Customer,
    Product,
    Promo,
    ShippingRate,
    Shop,
    TokoDB,
    Variant,
)
from toko_wa.tools import TokoTools

NOW = "2026-10-15T10:00:00+07:00"  # Thursday

COLOURS = {
    "hitam": "HTM",
    "putih": "PTH",
    "navy": "NVY",
    "abu": "ABU",
    "cream": "CRM",
    "maroon": "MRN",
    "merah": "MRH",
    "hijau": "HJU",
    "biru": "BRU",
    "dusty pink": "DPK",
    "natural": "NTR",
}


def product(
    pid: str,
    name: str,
    category: str,
    price: int,
    reseller: int,
    grams: int,
    colours: list[str],
    sizes: list[str],
    stock: dict[str, int] | None = None,
) -> Product:
    variants = {}
    for colour in colours:
        for size in sizes:
            item_id = "-".join(x for x in (pid, COLOURS[colour], size) if x)
            options = {"warna": colour} | ({"ukuran": size} if size else {})
            variants[item_id] = Variant(
                item_id=item_id,
                options=options,
                price=price,
                reseller_price=reseller,
                stock=(stock or {}).get(item_id, 12),
                weight_grams=grams,
            )
    return Product(product_id=pid, name=name, category=category, variants=variants)


PRODUCTS = [
    product(
        "KS",
        "Kaos Polos Cotton Combed 30s",
        "kaos",
        59_000,
        49_000,
        200,
        ["hitam", "putih", "navy", "abu"],
        ["S", "M", "L", "XL"],
        {"KS-NVY-XL": 0, "KS-PTH-S": 2},
    ),
    product(
        "KM",
        "Kemeja Flanel Kotak",
        "kemeja",
        129_000,
        109_000,
        300,
        ["merah", "hijau", "biru"],
        ["M", "L", "XL"],
        {"KM-HJU-XL": 0},
    ),
    product(
        "HJ",
        "Hijab Segi Empat Voal",
        "hijab",
        45_000,
        38_000,
        100,
        ["hitam", "cream", "maroon", "navy", "dusty pink"],
        [""],
        {"HJ-MRN": 3},
    ),
    product(
        "CL",
        "Celana Chino Slim Fit",
        "celana",
        159_000,
        135_000,
        450,
        ["cream", "hitam", "navy"],
        ["28", "30", "32", "34"],
        {"CL-CRM-28": 0},
    ),
    product(
        "JK",
        "Jaket Hoodie Fleece",
        "jaket",
        189_000,
        159_000,
        600,
        ["hitam", "abu", "maroon"],
        ["M", "L", "XL"],
        {"JK-MRN-XL": 1},
    ),
    product("TB", "Totebag Kanvas", "tas", 35_000, 29_000, 150, ["natural", "hitam"], [""]),
]


def addr(
    cid: str,
    n: int,
    label: str,
    recipient: str,
    street: str,
    district: str,
    city: str,
    province: str,
    postal: str,
) -> Address:
    return Address(
        address_id=f"{cid}-A{n}",
        label=label,
        recipient=recipient,
        street=street,
        district=district,
        city=city,
        province=province,
        postal_code=postal,
    )


def customer(cid: str, name: str, phone: str, addresses: list[Address], reseller: bool = False) -> Customer:
    return Customer(
        customer_id=cid,
        name=name,
        phone=phone,
        addresses=addresses,
        default_address_id=addresses[0].address_id,
        is_reseller=reseller,
    )


CUSTOMERS = [
    customer(
        "C001",
        "Rina Wulandari",
        "6281234500001",
        [
            addr(
                "C001",
                1,
                "Kos",
                "Rina Wulandari",
                "Jl. Kaliurang Km 5 No. 12",
                "Depok",
                "Yogyakarta",
                "DI Yogyakarta",
                "55281",
            )
        ],
    ),
    customer(
        "C002",
        "Dimas Pratama",
        "6281234500002",
        [
            addr(
                "C002",
                1,
                "Rumah",
                "Dimas Pratama",
                "Jl. Cigadung Raya No. 8",
                "Cibeunying Kaler",
                "Bandung",
                "Jawa Barat",
                "40191",
            )
        ],
    ),
    customer(
        "C003",
        "Sari Kusuma",
        "6281234500003",
        [
            addr(
                "C003",
                1,
                "Rumah",
                "Sari Kusuma",
                "Jl. Rungkut Asri No. 21",
                "Rungkut",
                "Surabaya",
                "Jawa Timur",
                "60293",
            ),
            addr(
                "C003",
                2,
                "Kantor",
                "Sari Kusuma",
                "Jl. Basuki Rahmat No. 129, Lt. 7",
                "Tegalsari",
                "Surabaya",
                "Jawa Timur",
                "60271",
            ),
        ],
    ),
    customer(
        "C004",
        "Bayu Saputra",
        "6281234500004",
        [
            addr(
                "C004",
                1,
                "Rumah",
                "Bayu Saputra",
                "Perum Harapan Indah Blok C2 No. 5",
                "Medan Satria",
                "Bekasi",
                "Jawa Barat",
                "17132",
            )
        ],
    ),
    customer(
        "C005",
        "Maya Anggraini",
        "6281234500005",
        [
            addr(
                "C005",
                1,
                "Apartemen",
                "Maya Anggraini",
                "Apartemen Kalibata City Tower B 12F",
                "Pancoran",
                "Jakarta Selatan",
                "DKI Jakarta",
                "12750",
            ),
            addr(
                "C005",
                2,
                "Rumah Mama",
                "Hj. Wartini",
                "Jl. Kemang Pratama Raya No. 18",
                "Rawalumbu",
                "Bekasi",
                "Jawa Barat",
                "17116",
            ),
        ],
    ),
    customer(
        "C006",
        "Fajar Nugroho",
        "6281234500006",
        [
            addr(
                "C006",
                1,
                "Rumah",
                "Fajar Nugroho",
                "Jl. Setia Budi No. 77",
                "Medan Selayang",
                "Medan",
                "Sumatera Utara",
                "20132",
            )
        ],
    ),
    customer(
        "C007",
        "Lestari Putri",
        "6281234500007",
        [
            addr(
                "C007",
                1,
                "Rumah",
                "Lestari Putri",
                "Jl. Hertasning Baru No. 30",
                "Rappocini",
                "Makassar",
                "Sulawesi Selatan",
                "90222",
            )
        ],
    ),
    customer(
        "C008",
        "Agus Setiawan",
        "6281234500008",
        [
            addr(
                "C008",
                1,
                "Rumah",
                "Agus Setiawan",
                "Jl. Antapani Lama No. 4",
                "Antapani",
                "Bandung",
                "Jawa Barat",
                "40291",
            )
        ],
    ),
    customer(
        "C009",
        "Nur Hidayah",
        "6281234500009",
        [
            addr(
                "C009",
                1,
                "Rumah",
                "Nur Hidayah",
                "Jl. Mitra Batik No. 15",
                "Tamansari",
                "Tasikmalaya",
                "Jawa Barat",
                "46196",
            )
        ],
    ),
    customer(
        "C010",
        "Asep Sunandar",
        "6281234500010",
        [
            addr(
                "C010",
                1,
                "Imah",
                "Asep Sunandar",
                "Kp. Cimanuk RT 02/05",
                "Tarogong Kidul",
                "Garut",
                "Jawa Barat",
                "44151",
            )
        ],
    ),
    customer(
        "C011",
        "Dewi Lestari",
        "6281234500011",
        [
            addr(
                "C011",
                1,
                "Rumah",
                "Dewi Lestari",
                "Jl. Soekarno Hatta No. 9",
                "Lowokwaru",
                "Malang",
                "Jawa Timur",
                "65141",
            )
        ],
    ),
    customer(
        "C012",
        "Rudi Hartono",
        "6281234500012",
        [
            addr(
                "C012",
                1,
                "Toko",
                "Rudi Hartono",
                "Jl. Pandanaran No. 50",
                "Semarang Tengah",
                "Semarang",
                "Jawa Tengah",
                "50241",
            )
        ],
    ),
    customer(
        "C013",
        "Hj. Siti Aminah",
        "6281234500013",
        [
            addr(
                "C013",
                1,
                "Toko Berkah",
                "Siti Aminah",
                "Pasar Baru Lt. 2 Blok F No. 8",
                "Sumur Bandung",
                "Bandung",
                "Jawa Barat",
                "40111",
            )
        ],
        reseller=True,
    ),
]

# (city, courier, price per kg, eta, cod)
RATES = [
    ("Bandung", "JNE", 9_000, "1-2", True),
    ("Bandung", "J&T", 8_000, "1-2", True),
    ("Bandung", "SiCepat", 8_000, "1-2", False),
    ("Jakarta Selatan", "JNE", 11_000, "2-3", True),
    ("Jakarta Selatan", "J&T", 10_000, "2-3", True),
    ("Jakarta Selatan", "SiCepat", 10_000, "2-3", False),
    ("Bekasi", "JNE", 11_000, "2-3", True),
    ("Bekasi", "J&T", 10_000, "2-3", True),
    ("Bekasi", "SiCepat", 10_000, "2-3", False),
    ("Surabaya", "JNE", 18_000, "2-4", True),
    ("Surabaya", "J&T", 17_000, "2-4", False),
    ("Surabaya", "SiCepat", 16_000, "3-4", False),
    ("Yogyakarta", "JNE", 15_000, "2-3", True),
    ("Yogyakarta", "J&T", 14_000, "2-3", False),
    ("Yogyakarta", "SiCepat", 13_000, "2-4", False),
    ("Garut", "JNE", 12_000, "2-3", False),
    ("Garut", "J&T", 11_000, "2-3", False),
    ("Tasikmalaya", "JNE", 12_000, "2-3", True),
    ("Tasikmalaya", "J&T", 11_000, "2-3", True),
    ("Malang", "JNE", 19_000, "3-4", True),
    ("Malang", "J&T", 18_000, "3-4", False),
    ("Medan", "JNE", 38_000, "4-6", False),
    ("Medan", "J&T", 36_000, "4-6", False),
    ("Makassar", "JNE", 45_000, "4-7", False),
    ("Makassar", "J&T", 43_000, "5-7", False),
    ("Semarang", "JNE", 14_000, "2-3", True),
    ("Semarang", "J&T", 13_000, "2-3", False),
]

PROMOS = [
    Promo(code="GAJIAN10", percent=10, min_purchase=200_000, valid_until="2026-10-31"),
    Promo(code="OKTOBER5", percent=5, min_purchase=100_000, valid_until="2026-10-10"),
]


def at(day: int, hour: int, minute: int = 0) -> str:
    return f"2026-10-{day:02d}T{hour:02d}:{minute:02d}:00+07:00"


def build() -> TokoDB:
    # deep copies: the tools change stock and addresses, and every build starts from the same shop
    db = TokoDB(
        shop=Shop(name="Toko Rapi Bandung", now=NOW),
        chat=Chat(phone="0"),
        customers={c.customer_id: c.model_copy(deep=True) for c in CUSTOMERS},
        products={p.product_id: p.model_copy(deep=True) for p in PRODUCTS},
        orders={},
        transfers={},
        promos={p.code: p.model_copy(deep=True) for p in PROMOS},
        shipping_rates=[
            ShippingRate(city=c, courier=k, price_per_kg=p, eta_days=e, cod=cod) for c, k, p, e, cod in RATES
        ],
    )
    tools = TokoTools(db)
    transfers = iter(range(501, 600))

    def order(
        when: str,
        cid: str,
        items: list[tuple[str, int]],
        courier: str,
        pay: str,
        address: int = 1,
        promo: str | None = None,
        paid_at: str | None = None,
    ):
        db.shop.now = when
        made = tools.create_order(
            cid, [{"item_id": i, "qty": q} for i, q in items], f"{cid}-A{address}", courier, pay, promo
        )
        if paid_at:
            transfer = BankTransfer(
                transfer_id=f"TRF-{next(transfers)}",
                bank="BCA" if pay == "transfer_bca" else "BRI",
                amount=made.total,
                sender_name=db.customers[cid].name.upper(),
                received_at=paid_at,
            )
            db.transfers[transfer.transfer_id] = transfer
            db.shop.now = paid_at
            tools.confirm_payment(made.order_id, transfer.transfer_id)
        return made

    def ship(o, when: str, resi: str, events: list[str]):
        o.status, o.shipment.tracking_number, o.shipment.events = "dikirim", resi, events

    def deliver(o, when: str):
        o.status, o.delivered_at = "diterima", when
        o.shipment.events.append(f"{when[:16].replace('T', ' ')} Diterima oleh yang bersangkutan")

    # C001 Rina: one old delivered order, one shipped yesterday (in transit)
    o = order(at(1, 9), "C001", [("KS-HTM-M", 2)], "JNE", "transfer_bca", paid_at=at(1, 11))
    ship(o, at(2, 15), "JNE0100000101", ["2026-10-02 15:10 Paket diterima di agen JNE Bandung"])
    deliver(o, at(4, 13, 20))
    o = order(
        at(13, 20), "C001", [("HJ-CRM", 2), ("TB-NTR", 1)], "JNE", "transfer_bca", paid_at=at(13, 21, 5)
    )
    ship(
        o,
        at(14, 16),
        "JNE0100000102",
        [
            "2026-10-14 16:02 Paket diterima di agen JNE Bandung",
            "2026-10-14 22:40 Berangkat dari Bandung menuju Yogyakarta",
            "2026-10-15 06:15 Tiba di gudang JNE Yogyakarta",
        ],
    )
    # C002 Dimas: shipped on the 11th, stuck in transit since the evening of the 11th
    o = order(at(10, 19), "C002", [("JK-HTM-L", 1)], "J&T", "transfer_bri", paid_at=at(10, 19, 40))
    ship(
        o,
        at(11, 14),
        "JT0200000201",
        [
            "2026-10-11 14:30 Paket diterima di drop point J&T Bandung",
            "2026-10-11 18:10 Transit di gateway Bandung",
            "2026-10-11 21:45 Paket tertahan di gateway, menunggu jadwal berikutnya",
        ],
    )
    # C003 Sari: unpaid order to her home in Surabaya
    order(at(14, 21), "C003", [("KM-BRU-L", 1), ("KS-PTH-L", 1)], "JNE", "transfer_bca")
    # C004 Bayu: a hoodie delivered yesterday morning (inside the 72-hour return window), and an unpaid order
    o = order(at(10, 8), "C004", [("JK-ABU-XL", 1)], "JNE", "transfer_bri", paid_at=at(10, 9))
    ship(o, at(11, 10), "JNE0400000401", ["2026-10-11 10:00 Paket diterima di agen JNE Bandung"])
    deliver(o, at(14, 8, 30))
    order(at(15, 9, 30), "C004", [("KS-ABU-L", 2)], "J&T", "transfer_bri")
    # C009 Nur: unpaid order; she transferred the round amount, without the kode unik
    o = order(at(14, 19), "C009", [("HJ-NVY", 2), ("HJ-HTM", 2), ("TB-HTM", 1)], "JNE", "transfer_bri")
    db.transfers["TRF-590"] = BankTransfer(
        transfer_id="TRF-590",
        bank="BRI",
        amount=o.total - o.unique_code,
        sender_name="NUR HIDAYAH",
        received_at=at(15, 8, 10),
    )
    # C011 Dewi: delivered six days ago (outside the return window)
    o = order(at(5, 10), "C011", [("CL-NVY-30", 1)], "JNE", "transfer_bca", paid_at=at(5, 12))
    ship(o, at(6, 9), "JNE1100001101", ["2026-10-06 09:00 Paket diterima di agen JNE Bandung"])
    deliver(o, at(9, 11))
    # C013 the reseller: a paid order being packed
    order(at(15, 8), "C013", [("HJ-HTM", 6), ("HJ-CRM", 6)], "JNE", "cod")
    # other people's transfers in the statement
    for amount, sender, day in (
        (178_000, "ANDI WIJAYA", at(15, 7, 2)),
        (250_000, "BUDI SANTOSO", at(14, 22, 30)),
    ):
        tid = f"TRF-{next(transfers)}"
        db.transfers[tid] = BankTransfer(
            transfer_id=tid, bank="BRI", amount=amount, sender_name=sender, received_at=day
        )
    db.shop.now = NOW
    return db
