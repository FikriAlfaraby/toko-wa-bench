"""Each shop rule is enforced by its tool, and each refusal says why in words."""

import json
import math

import pytest

from toko_wa.seed import build
from toko_wa.tools import TokoTools, normalize_phone


@pytest.fixture
def shop() -> TokoTools:
    return TokoTools(build())


def order_of(shop: TokoTools, customer_id: str, status: str):
    found = [o for o in shop.db.orders.values() if o.customer_id == customer_id and o.status == status]
    assert len(found) == 1, (customer_id, status, found)
    return found[0]


def stock(shop: TokoTools, item_id: str) -> int:
    return shop._variant(item_id)[1].stock


def test_numbers_in_any_common_format_are_the_same():
    for raw in ("+62 812-3450-0001", "0812 3450 0001", "6281234500001"):
        assert normalize_phone(raw) == "6281234500001"


def test_the_chat_number_finds_the_customer(shop):
    shop.db.chat.phone = "6281234500010"
    assert shop.find_customer_by_phone(shop.get_chat_info().phone).name == "Asep Sunandar"
    with pytest.raises(ValueError, match="No customer"):
        shop.find_customer_by_phone("6289999999999")


def test_search_matches_every_word(shop):
    assert [p["product_id"] for p in json.loads(shop.search_products("kaos"))] == ["KS"]
    assert [p["product_id"] for p in json.loads(shop.search_products("hijab voal"))] == ["HJ"]
    assert json.loads(shop.search_products("sepatu")) == []


def test_ongkir_charges_every_started_kilogram(shop):
    assert shop.get_shipping_quote("Yogyakarta", "JNE", 300).shipping_cost == 15_000
    assert shop.get_shipping_quote("yogyakarta", "jne", 1001).shipping_cost == 30_000
    with pytest.raises(ValueError, match="does not deliver"):
        shop.get_shipping_quote("Garut", "SiCepat", 500)


def test_a_transfer_order_adds_ongkir_and_a_kode_unik_and_takes_stock(shop):
    before = stock(shop, "KS-HTM-L")
    order = shop.create_order("C001", [{"item_id": "KS-HTM-L", "qty": 2}], "C001-A1", "JNE", "transfer_bca")
    assert order.status == "menunggu_pembayaran"
    assert 100 <= order.unique_code <= 999
    assert order.total == 2 * 59_000 + 15_000 + order.unique_code
    assert stock(shop, "KS-HTM-L") == before - 2


def test_resellers_pay_the_reseller_price_and_cannot_add_a_promo(shop):
    order = shop.create_order("C013", [{"item_id": "HJ-NVY", "qty": 2}], "C013-A1", "JNE", "cod")
    assert order.items[0].unit_price == 38_000 and order.unique_code == 0 and order.status == "diproses"
    with pytest.raises(ValueError, match="reseller"):
        shop.create_order("C013", [{"item_id": "JK-HTM-L", "qty": 2}], "C013-A1", "JNE", "cod", "GAJIAN10")


def test_promos_need_a_valid_code_and_the_minimum(shop):
    order = shop.create_order(
        "C008", [{"item_id": "JK-HTM-L", "qty": 2}], "C008-A1", "JNE", "transfer_bca", "gajian10"
    )
    assert order.discount == 37_800 and order.promo_code == "GAJIAN10"
    with pytest.raises(ValueError, match="ended"):
        shop.create_order(
            "C008", [{"item_id": "JK-HTM-L", "qty": 2}], "C008-A1", "JNE", "transfer_bca", "OKTOBER5"
        )
    with pytest.raises(ValueError, match="at least"):
        shop.create_order(
            "C008", [{"item_id": "KS-HTM-L", "qty": 1}], "C008-A1", "JNE", "transfer_bca", "GAJIAN10"
        )


def test_cod_only_where_the_courier_offers_it_and_up_to_the_limit(shop):
    with pytest.raises(ValueError, match="COD is not available in Garut"):
        shop.create_order("C010", [{"item_id": "KS-HTM-L", "qty": 1}], "C010-A1", "JNE", "cod")
    with pytest.raises(ValueError, match="up to"):
        shop.create_order("C002", [{"item_id": "JK-HTM-L", "qty": 6}], "C002-A1", "JNE", "cod")
    assert (
        shop.create_order("C002", [{"item_id": "JK-HTM-L", "qty": 1}], "C002-A1", "JNE", "cod").total
        == 198_000
    )


def test_out_of_stock_and_unknown_items_are_refused(shop):
    with pytest.raises(ValueError, match="Only 0"):
        shop.create_order("C001", [{"item_id": "KS-NVY-XL", "qty": 1}], "C001-A1", "JNE", "transfer_bca")
    with pytest.raises(ValueError, match="not found"):
        shop.create_order("C001", [{"item_id": "KS-UNGU-L", "qty": 1}], "C001-A1", "JNE", "transfer_bca")
    with pytest.raises(ValueError, match="does not belong"):
        shop.create_order("C001", [{"item_id": "KS-HTM-L", "qty": 1}], "C002-A1", "JNE", "transfer_bca")


def test_payment_needs_the_exact_total_with_the_kode_unik(shop):
    unpaid = order_of(shop, "C009", "menunggu_pembayaran")
    round_amount = json.loads(shop.find_transfers("BRI", unpaid.total - unpaid.unique_code))
    assert [t["sender_name"] for t in round_amount] == ["NUR HIDAYAH"]
    assert json.loads(shop.find_transfers("BRI", unpaid.total)) == []
    with pytest.raises(ValueError, match="order total"):
        shop.confirm_payment(unpaid.order_id, round_amount[0]["transfer_id"])
    assert unpaid.status == "menunggu_pembayaran"


def test_a_paid_transfer_cannot_pay_twice(shop):
    paid = order_of(shop, "C002", "dikirim")
    with pytest.raises(ValueError, match="already paid"):
        unpaid = order_of(shop, "C003", "menunggu_pembayaran")
        shop.confirm_payment(unpaid.order_id, paid.paid_transfer_id)


def test_items_change_only_before_payment_and_stock_follows(shop):
    unpaid = order_of(shop, "C004", "menunggu_pembayaran")
    before = stock(shop, "KS-ABU-L"), stock(shop, "KS-HTM-L")
    shop.update_order_items(unpaid.order_id, [{"item_id": "KS-HTM-L", "qty": 1}])
    assert (stock(shop, "KS-ABU-L"), stock(shop, "KS-HTM-L")) == (before[0] + 2, before[1] - 1)
    assert unpaid.total == 59_000 + 10_000 + unpaid.unique_code
    shipped = order_of(shop, "C001", "dikirim")
    with pytest.raises(ValueError, match="before payment"):
        shop.update_order_items(shipped.order_id, [{"item_id": "KS-HTM-L", "qty": 1}])


def test_address_changes_before_shipping_and_never_change_a_paid_ongkir(shop):
    unpaid = order_of(shop, "C003", "menunggu_pembayaran")
    old_total = unpaid.total
    assert shop.update_order_address(unpaid.order_id, "C003-A2").shipment.address.label == "Kantor"
    assert unpaid.total == old_total
    paid = shop.create_order("C008", [{"item_id": "KS-HTM-L", "qty": 1}], "C008-A1", "JNE", "transfer_bca")
    shop.db.transfers["TRF-T1"] = shop.db.transfers["TRF-590"].model_copy(
        update={"transfer_id": "TRF-T1", "bank": "BCA", "amount": paid.total, "received_at": shop.db.shop.now}
    )
    shop.confirm_payment(paid.order_id, "TRF-T1")
    shop.add_address(
        "C008", "Kos", "Agus", "Jl. Kaliurang 1", "Depok", "Yogyakarta", "DI Yogyakarta", "55281"
    )
    with pytest.raises(ValueError, match="hand it to the admin"):
        shop.update_order_address(paid.order_id, "C008-A2")
    with pytest.raises(ValueError, match="before shipping"):
        shop.update_order_address(order_of(shop, "C001", "dikirim").order_id, "C001-A1")


def test_cancelling_gives_stock_back_and_owes_a_paid_order_its_money(shop):
    unpaid = order_of(shop, "C004", "menunggu_pembayaran")
    before = stock(shop, "KS-ABU-L")
    assert shop.cancel_order(unpaid.order_id, "tidak jadi").refund_due == 0
    assert stock(shop, "KS-ABU-L") == before + 2
    with pytest.raises(ValueError, match="'tidak jadi' or 'salah pesan'"):
        shop.cancel_order(order_of(shop, "C003", "menunggu_pembayaran").order_id, "kemahalan")
    cod = order_of(shop, "C013", "diproses")
    assert shop.cancel_order(cod.order_id, "salah pesan").refund_due == 0


def test_returns_need_the_window_the_video_and_a_real_reason(shop):
    recent = order_of(shop, "C004", "diterima")
    with pytest.raises(ValueError, match="unboxing video"):
        shop.request_return(recent.order_id, ["JK-ABU-XL"], "cacat", False)
    with pytest.raises(Exception, match="cacat"):
        shop.request_return(recent.order_id, ["JK-ABU-XL"], "kekecilan", True)
    assert recent.status == "diterima"
    assert shop.request_return(recent.order_id, ["JK-ABU-XL"], "cacat", True).status == "retur_diajukan"
    with pytest.raises(ValueError, match="72-hour"):
        shop.request_return(order_of(shop, "C011", "diterima").order_id, ["CL-NVY-30"], "cacat", True)


def test_tracking_only_for_shipped_orders(shop):
    shipped = order_of(shop, "C002", "dikirim")
    assert "tertahan" in shop.track_shipment(shipped.order_id).events[-1]
    with pytest.raises(ValueError, match="has not been shipped"):
        shop.track_shipment(order_of(shop, "C003", "menunggu_pembayaran").order_id)


def test_calculate_takes_arithmetic_only(shop):
    assert shop.calculate("2 * 59000 + 15000") == "133000.0"
    with pytest.raises(ValueError):
        shop.calculate("__import__('os')")


def test_the_seeded_orders_follow_the_rules(shop):
    for order in shop.db.orders.values():
        subtotal = sum(i.unit_price * i.qty for i in order.items)
        weight = sum(shop._variant(i.item_id)[1].weight_grams * i.qty for i in order.items)
        rate = shop._rate(order.shipment.address.city, order.shipment.courier)
        assert order.shipment.shipping_cost == rate.price_per_kg * max(1, math.ceil(weight / 1000))
        assert order.total == subtotal - order.discount + order.shipment.shipping_cost + order.unique_code
        if order.paid_transfer_id:
            assert shop.db.transfers[order.paid_transfer_id].amount == order.total


def test_a_hand_off_is_recorded_with_its_order_and_reason_only(shop):
    shop.transfer_to_admin("paket bermasalah", "tertahan di gateway sejak 11 Okt", "ORD-1003")
    assert [h.model_dump() for h in shop.db.handoffs] == [
        {"order_id": "ORD-1003", "reason": "paket bermasalah"}
    ]
    with pytest.raises(ValueError, match="not found"):
        shop.transfer_to_admin("lainnya", "x", "ORD-9999")
