"""The tools a shop assistant has on WhatsApp. Each write tool enforces the shop's rules itself and
fails with a sentence the agent can read; whether to call it at all is the agent's judgement."""

import json
import math
import re
from datetime import datetime, timedelta
from typing import Literal

from pydantic import BaseModel
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool

from toko_wa.data_model import Address, Customer, Order, OrderItem, Product, ReturnRequest, Shipment, TokoDB

COD_LIMIT = 1_000_000
RETURN_WINDOW = timedelta(hours=72)
EDITABLE = ("menunggu_pembayaran", "diproses")


class ItemQty(BaseModel):
    item_id: str
    qty: int


# Tools return models, not dicts: tau2 turns numbers and booleans inside a dict into strings.
class ChatInfo(BaseModel):
    phone: str
    now: str


class ShippingQuote(BaseModel):
    shipping_cost: int
    eta_days: str
    cod_available: bool


class Tracking(BaseModel):
    status: str
    courier: str
    tracking_number: str
    events: list[str]


def normalize_phone(phone: str) -> str:
    """'+62 812-3456-7890', '0812 3456 7890' and '6281234567890' are the same number."""
    digits = re.sub(r"\D", "", phone)
    return "62" + digits[1:] if digits.startswith("0") else digits


class TokoTools(ToolKitBase):
    """All the tools for the toko_wa domain."""

    db: TokoDB

    def __init__(self, db: TokoDB) -> None:
        super().__init__(db)

    # helpers -----------------------------------------------------------------------------------

    def _now(self) -> datetime:
        return datetime.fromisoformat(self.db.shop.now)

    def _customer(self, customer_id: str) -> Customer:
        if customer_id not in self.db.customers:
            raise ValueError(f"Customer {customer_id} not found")
        return self.db.customers[customer_id]

    def _order(self, order_id: str) -> Order:
        if order_id not in self.db.orders:
            raise ValueError(f"Order {order_id} not found")
        return self.db.orders[order_id]

    def _variant(self, item_id: str):
        for product in self.db.products.values():
            if item_id in product.variants:
                return product, product.variants[item_id]
        raise ValueError(f"Item {item_id} not found")

    def _address(self, customer: Customer, address_id: str) -> Address:
        for address in customer.addresses:
            if address.address_id == address_id:
                return address
        raise ValueError(f"Address {address_id} does not belong to customer {customer.customer_id}")

    def _rate(self, city: str, courier: str):
        for rate in self.db.shipping_rates:
            if rate.city.lower() == city.strip().lower() and rate.courier.lower() == courier.strip().lower():
                return rate
        raise ValueError(f"{courier} does not deliver to {city} from this shop")

    def _shipping_cost(self, city: str, courier: str, weight_grams: int) -> int:
        return self._rate(city, courier).price_per_kg * max(1, math.ceil(weight_grams / 1000))

    def _build_items(self, customer: Customer, items: list[ItemQty], restock: list[OrderItem] | None = None):
        """Check stock (counting units an edited order gives back) and price each line."""
        returned = {i.item_id: i.qty for i in restock or []}
        lines, weight = [], 0
        if not items:
            raise ValueError("An order needs at least one item")
        for entry in items:
            entry = ItemQty.model_validate(entry)
            if entry.qty < 1:
                raise ValueError(f"Quantity for {entry.item_id} must be at least 1")
            product, variant = self._variant(entry.item_id)
            if variant.stock + returned.get(entry.item_id, 0) < entry.qty:
                raise ValueError(f"Only {variant.stock} of {entry.item_id} in stock")
            price = variant.reseller_price if customer.is_reseller else variant.price
            lines.append(
                OrderItem(
                    item_id=entry.item_id,
                    product_id=product.product_id,
                    name=product.name,
                    options=variant.options,
                    qty=entry.qty,
                    unit_price=price,
                )
            )
            weight += variant.weight_grams * entry.qty
        return lines, weight

    def _discount(self, customer: Customer, promo_code: str | None, subtotal: int) -> int:
        if not promo_code:
            return 0
        promo = self.db.promos.get(promo_code.strip().upper())
        if promo is None:
            raise ValueError(f"Promo code {promo_code} does not exist")
        if customer.is_reseller:
            raise ValueError("Promo codes do not apply to reseller prices")
        if self._now().date().isoformat() > promo.valid_until:
            raise ValueError(f"Promo code {promo.code} ended on {promo.valid_until}")
        if subtotal < promo.min_purchase:
            raise ValueError(
                f"Promo code {promo.code} needs an item total of at least Rp{promo.min_purchase}"
            )
        return subtotal * promo.percent // 100 // 100 * 100

    def _stock(self, lines: list[OrderItem], sign: int) -> None:
        for line in lines:
            _, variant = self._variant(line.item_id)
            variant.stock += sign * line.qty

    def _check_cod(self, payment_method: str, city: str, courier: str, total: int) -> None:
        if payment_method != "cod":
            return
        if not self._rate(city, courier).cod:
            raise ValueError(f"COD is not available in {city} with {courier}")
        if total > COD_LIMIT:
            raise ValueError(f"COD is only for totals up to Rp{COD_LIMIT}")

    # read ----------------------------------------------------------------------------------------

    @is_tool(ToolType.READ)
    def get_chat_info(self) -> ChatInfo:
        """Get the WhatsApp number this chat is with and the current time. Call this first: the
        customer is identified by this number.

        Returns:
            ChatInfo: the customer's WhatsApp number, and the current time in WIB.
        """
        return ChatInfo(phone=self.db.chat.phone, now=self.db.shop.now)

    @is_tool(ToolType.READ)
    def find_customer_by_phone(self, phone: str) -> Customer:
        """Find a customer by WhatsApp number.

        Args:
            phone: The number, in any common format, e.g. '6281234567890' or '0812-3456-7890'.

        Returns:
            Customer: The customer's profile, saved addresses and reseller status.
        """
        wanted = normalize_phone(phone)
        for customer in self.db.customers.values():
            if normalize_phone(customer.phone) == wanted:
                return customer
        raise ValueError(f"No customer with number {phone}")

    @is_tool(ToolType.READ)
    def search_products(self, keyword: str) -> str:
        """Search products by a word in their name or category, e.g. 'kaos', 'hijab', 'kemeja'.

        Args:
            keyword: One or more words; every word must match the name or the category.

        Returns:
            str: JSON list of {'product_id', 'name', 'category'}.
        """
        words = keyword.lower().split()
        found = [
            {"product_id": p.product_id, "name": p.name, "category": p.category}
            for p in self.db.products.values()
            if words and all(w in f"{p.name} {p.category}".lower() for w in words)
        ]
        return json.dumps(found, ensure_ascii=False)

    @is_tool(ToolType.READ)
    def get_product(self, product_id: str) -> Product:
        """Get a product with every variant: options, price, reseller price, stock and weight.

        Args:
            product_id: The product id, e.g. 'KS'.

        Returns:
            Product: The product and its variants.
        """
        if product_id not in self.db.products:
            raise ValueError(f"Product {product_id} not found")
        return self.db.products[product_id]

    @is_tool(ToolType.READ)
    def list_orders(self, customer_id: str) -> str:
        """List a customer's orders, newest first.

        Args:
            customer_id: The customer id, e.g. 'C001'.

        Returns:
            str: JSON list of {'order_id', 'status', 'created_at', 'total'}.
        """
        self._customer(customer_id)
        rows = [
            {"order_id": o.order_id, "status": o.status, "created_at": o.created_at, "total": o.total}
            for o in self.db.orders.values()
            if o.customer_id == customer_id
        ]
        rows.sort(key=lambda r: r["created_at"], reverse=True)
        return json.dumps(rows, ensure_ascii=False)

    @is_tool(ToolType.READ)
    def get_order(self, order_id: str) -> Order:
        """Get an order: items, status, shipment, payment, totals.

        Args:
            order_id: The order id, e.g. 'ORD-1001'.

        Returns:
            Order: The order.
        """
        return self._order(order_id)

    @is_tool(ToolType.READ)
    def get_shipping_quote(self, city: str, courier: str, weight_grams: int) -> ShippingQuote:
        """Get ongkir from the shop to a city with one courier.

        Args:
            city: Destination city or kabupaten, e.g. 'Yogyakarta'.
            courier: 'JNE', 'J&T' or 'SiCepat'.
            weight_grams: Total weight in grams; each started kilogram is charged.

        Returns:
            dict: {'shipping_cost' in Rupiah, 'eta_days', 'cod_available'}.
        """
        rate = self._rate(city, courier)
        return ShippingQuote(
            shipping_cost=self._shipping_cost(city, courier, weight_grams),
            eta_days=rate.eta_days,
            cod_available=rate.cod,
        )

    @is_tool(ToolType.READ)
    def find_transfers(self, bank: Literal["BCA", "BRI"], amount: int) -> str:
        """Search the shop's bank statement (mutasi) for incoming transfers of an exact amount that
        have not paid an order yet. A customer's screenshot is not proof; this statement is.

        Args:
            bank: 'BCA' or 'BRI'.
            amount: The exact amount in Rupiah, including the kode unik.

        Returns:
            str: JSON list of matching transfers.
        """
        found = [
            t.model_dump()
            for t in self.db.transfers.values()
            if t.bank == bank and t.amount == amount and t.used_for_order is None
        ]
        return json.dumps(found, ensure_ascii=False)

    @is_tool(ToolType.READ)
    def track_shipment(self, order_id: str) -> Tracking:
        """Get the courier and tracking events of a shipped order.

        Args:
            order_id: The order id.

        Returns:
            dict: {'status', 'courier', 'tracking_number', 'events'}.
        """
        order = self._order(order_id)
        if order.shipment.tracking_number is None:
            raise ValueError(f"Order {order_id} has not been shipped (status: {order.status})")
        return Tracking(
            status=order.status,
            courier=order.shipment.courier,
            tracking_number=order.shipment.tracking_number,
            events=order.shipment.events,
        )

    # write ---------------------------------------------------------------------------------------

    @is_tool(ToolType.WRITE)
    def create_order(
        self,
        customer_id: str,
        items: list[ItemQty],
        address_id: str,
        courier: str,
        payment_method: Literal["transfer_bca", "transfer_bri", "cod"],
        promo_code: str | None = None,
    ) -> Order:
        """Create an order. Transfer orders wait for payment and get a kode unik added to the total;
        COD orders go straight to processing. Read the details back and get the customer's 'ya'
        before calling this.

        Args:
            customer_id: The customer id.
            items: List of {'item_id', 'qty'}.
            address_id: One of the customer's saved address ids.
            courier: 'JNE', 'J&T' or 'SiCepat'.
            payment_method: 'transfer_bca', 'transfer_bri' or 'cod'.
            promo_code: Optional promo code.

        Returns:
            Order: The new order with its total.
        """
        customer = self._customer(customer_id)
        address = self._address(customer, address_id)
        lines, weight = self._build_items(customer, items)
        subtotal = sum(line.unit_price * line.qty for line in lines)
        discount = self._discount(customer, promo_code, subtotal)
        shipping = self._shipping_cost(address.city, courier, weight)
        number = max(int(o.split("-")[1]) for o in self.db.orders) + 1 if self.db.orders else 1001
        unique = 0 if payment_method == "cod" else 100 + (number * 37) % 900
        total = subtotal - discount + shipping + unique
        self._check_cod(payment_method, address.city, courier, total)
        order = Order(
            order_id=f"ORD-{number}",
            customer_id=customer_id,
            status="diproses" if payment_method == "cod" else "menunggu_pembayaran",
            created_at=self.db.shop.now,
            items=lines,
            shipment=Shipment(
                courier=self._rate(address.city, courier).courier, address=address, shipping_cost=shipping
            ),
            payment_method=payment_method,
            promo_code=promo_code.strip().upper() if discount else None,
            discount=discount,
            unique_code=unique,
            total=total,
        )
        self._stock(lines, -1)
        self.db.orders[order.order_id] = order
        return order

    @is_tool(ToolType.WRITE)
    def confirm_payment(self, order_id: str, transfer_id: str) -> Order:
        """Mark a transfer order as paid with a transfer found in the bank statement. The amount must
        equal the order total exactly, kode unik included.

        Args:
            order_id: The order id.
            transfer_id: The transfer id from find_transfers.

        Returns:
            Order: The order, now being processed.
        """
        order = self._order(order_id)
        if order.status != "menunggu_pembayaran":
            raise ValueError(f"Order {order_id} is not waiting for payment (status: {order.status})")
        transfer = self.db.transfers.get(transfer_id)
        if transfer is None:
            raise ValueError(f"Transfer {transfer_id} not found in the bank statement")
        if transfer.used_for_order is not None:
            raise ValueError(f"Transfer {transfer_id} already paid order {transfer.used_for_order}")
        if order.payment_method != f"transfer_{transfer.bank.lower()}":
            raise ValueError(
                f"Order {order_id} is paid by {order.payment_method}, the transfer is to {transfer.bank}"
            )
        if transfer.amount != order.total:
            raise ValueError(f"Transfer is Rp{transfer.amount}, the order total is Rp{order.total}")
        if transfer.received_at < order.created_at:
            raise ValueError(f"Transfer {transfer_id} arrived before order {order_id} was made")
        transfer.used_for_order = order_id
        order.paid_transfer_id = transfer_id
        order.status = "diproses"
        return order

    @is_tool(ToolType.WRITE)
    def update_order_items(self, order_id: str, items: list[ItemQty]) -> Order:
        """Replace the items of an order that has not been paid yet. The kode unik stays; the total
        changes. Read the new items and total back and get a 'ya' first.

        Args:
            order_id: The order id.
            items: The full new list of {'item_id', 'qty'}.

        Returns:
            Order: The updated order.
        """
        order = self._order(order_id)
        if order.status != "menunggu_pembayaran":
            raise ValueError(f"Items can only change before payment (status: {order.status})")
        customer = self._customer(order.customer_id)
        lines, weight = self._build_items(customer, items, restock=order.items)
        subtotal = sum(line.unit_price * line.qty for line in lines)
        discount = self._discount(customer, order.promo_code, subtotal)
        shipping = self._shipping_cost(order.shipment.address.city, order.shipment.courier, weight)
        self._stock(order.items, +1)
        self._stock(lines, -1)
        order.items, order.discount, order.shipment.shipping_cost = lines, discount, shipping
        order.total = subtotal - discount + shipping + order.unique_code
        return order

    @is_tool(ToolType.WRITE)
    def update_order_address(self, order_id: str, address_id: str) -> Order:
        """Ship an order to another of the customer's saved addresses, before it is shipped. If the
        order is already paid by transfer, the ongkir must not change; otherwise hand it to the admin.

        Args:
            order_id: The order id.
            address_id: One of the customer's saved address ids (add a new one with add_address first).

        Returns:
            Order: The updated order.
        """
        order = self._order(order_id)
        if order.status not in EDITABLE:
            raise ValueError(f"The address can only change before shipping (status: {order.status})")
        address = self._address(self._customer(order.customer_id), address_id)
        weight = sum(self._variant(i.item_id)[1].weight_grams * i.qty for i in order.items)
        shipping = self._shipping_cost(address.city, order.shipment.courier, weight)
        paid = order.paid_transfer_id is not None
        if paid and shipping != order.shipment.shipping_cost:
            raise ValueError("The order is paid and the ongkir would change: hand it to the admin")
        total = order.total - order.shipment.shipping_cost + shipping
        self._check_cod(order.payment_method, address.city, order.shipment.courier, total)
        order.shipment.address, order.shipment.shipping_cost, order.total = address, shipping, total
        return order

    @is_tool(ToolType.WRITE)
    def add_address(
        self,
        customer_id: str,
        label: str,
        recipient: str,
        street: str,
        district: str,
        city: str,
        province: str,
        postal_code: str,
        make_default: bool = False,
    ) -> Customer:
        """Save a new address for the customer.

        Args:
            customer_id: The customer id.
            label: The customer's name for it, e.g. 'Rumah baru'.
            recipient: Who receives parcels there.
            street: Street, number, RT/RW.
            district: Kecamatan.
            city: Kota or kabupaten.
            province: Province.
            postal_code: Postal code.
            make_default: Whether this becomes the default ('alamat biasa').

        Returns:
            Customer: The customer with the new address.
        """
        customer = self._customer(customer_id)
        address = Address(
            address_id=f"{customer_id}-A{len(customer.addresses) + 1}",
            label=label,
            recipient=recipient,
            street=street,
            district=district,
            city=city,
            province=province,
            postal_code=postal_code,
        )
        customer.addresses.append(address)
        if make_default:
            customer.default_address_id = address.address_id
        return customer

    @is_tool(ToolType.WRITE)
    def cancel_order(self, order_id: str, reason: Literal["tidak jadi", "salah pesan"]) -> Order:
        """Cancel an order before it is shipped. A paid order's money is sent back by the admin
        within 1-3 working days. Get a 'ya' and the reason first.

        Args:
            order_id: The order id.
            reason: 'tidak jadi' or 'salah pesan'.

        Returns:
            Order: The cancelled order.
        """
        order = self._order(order_id)
        if order.status not in EDITABLE:
            raise ValueError(f"Only orders not yet shipped can be cancelled (status: {order.status})")
        if reason not in ("tidak jadi", "salah pesan"):
            raise ValueError("The reason must be 'tidak jadi' or 'salah pesan'")
        self._stock(order.items, +1)
        order.status, order.cancel_reason = "dibatalkan", reason
        order.refund_due = order.total if order.paid_transfer_id else 0
        return order

    @is_tool(ToolType.WRITE)
    def request_return(
        self,
        order_id: str,
        item_ids: list[str],
        reason: Literal["cacat", "salah kirim"],
        has_unboxing_video: bool,
    ) -> Order:
        """Request a return for items that arrived defective or wrong, within 72 hours of delivery,
        with an unboxing video. Wrong size or a change of mind is not a reason. Get a 'ya' first.

        Args:
            order_id: The order id.
            item_ids: The item ids to return.
            reason: 'cacat' (defective) or 'salah kirim' (wrong item sent).
            has_unboxing_video: Whether the customer has an unboxing video.

        Returns:
            Order: The order with the return request.
        """
        order = self._order(order_id)
        if order.status != "diterima" or order.delivered_at is None:
            raise ValueError(f"Only delivered orders can be returned (status: {order.status})")
        if self._now() - datetime.fromisoformat(order.delivered_at) > RETURN_WINDOW:
            raise ValueError("The 72-hour return window has passed")
        if not has_unboxing_video:
            raise ValueError("A return needs an unboxing video")
        ordered = {i.item_id for i in order.items}
        if not item_ids or not set(item_ids) <= ordered:
            raise ValueError(f"Items must be from order {order_id}: {sorted(ordered)}")
        request = ReturnRequest(item_ids=item_ids, reason=reason, requested_at=self.db.shop.now)
        order.status, order.return_request = "retur_diajukan", request
        return order

    # generic -------------------------------------------------------------------------------------

    @is_tool(ToolType.GENERIC)
    def calculate(self, expression: str) -> str:
        """Calculate an arithmetic expression, e.g. '2 * 89000 + 15000'.

        Args:
            expression: Numbers, + - * / ( ) and spaces only.

        Returns:
            str: The result.
        """
        if not re.fullmatch(r"[0-9+\-*/(). ]+", expression):
            raise ValueError("Only numbers and + - * / ( ) are allowed")
        return str(round(float(eval(expression, {"__builtins__": None}, {})), 2))

    @is_tool(ToolType.GENERIC)
    def transfer_to_admin(self, summary: str) -> str:
        """Hand the chat to a person, for what the tools cannot do: a lost parcel, a paid order whose
        ongkir would change, a refund question. Write a short summary for the admin. It changes no
        data: the summary is free text, so the database stays comparable with the expected one.

        Args:
            summary: What the customer needs and what was already done.

        Returns:
            str: Confirmation.
        """
        return "Transfer successful"
