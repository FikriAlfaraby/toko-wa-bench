"""The shop's database: customers known by their WhatsApp number, products in Rupiah, orders, the
bank statement the shop checks transfers against, and the courier price list."""

from typing import Literal

from pydantic import BaseModel, Field
from tau2.environment.db import DB

OrderStatus = Literal[
    "menunggu_pembayaran", "diproses", "dikirim", "diterima", "dibatalkan", "retur_diajukan"
]
PaymentMethod = Literal["transfer_bca", "transfer_bri", "cod"]
Bank = Literal["BCA", "BRI"]


class Shop(BaseModel):
    name: str = Field(description="Shop name")
    now: str = Field(description="The current time, ISO 8601 with the +07:00 (WIB) offset")


class Chat(BaseModel):
    phone: str = Field(description="The WhatsApp number this chat is with, e.g. '6281234567890'")


class Address(BaseModel):
    address_id: str = Field(description="Unique address id, e.g. 'C001-A1'")
    label: str = Field(description="The customer's name for it, e.g. 'Rumah' or 'Kantor'")
    recipient: str = Field(description="Who receives the parcel")
    street: str = Field(description="Street, number, RT/RW")
    district: str = Field(description="Kecamatan")
    city: str = Field(description="Kota or kabupaten, e.g. 'Bandung' or 'Garut'")
    province: str = Field(description="Province")
    postal_code: str = Field(description="Postal code")


class Customer(BaseModel):
    customer_id: str = Field(description="Unique customer id, e.g. 'C001'")
    name: str = Field(description="Customer name")
    phone: str = Field(description="WhatsApp number, e.g. '6281234567890'")
    addresses: list[Address] = Field(description="Saved addresses")
    default_address_id: str = Field(description="The address used when the customer says 'alamat biasa'")
    is_reseller: bool = Field(description="Registered resellers pay the reseller price")


class Variant(BaseModel):
    item_id: str = Field(description="Unique variant id, e.g. 'KS-HTM-L'")
    options: dict[str, str] = Field(description="e.g. {'warna': 'hitam', 'ukuran': 'L'}")
    price: int = Field(description="Price in Rupiah")
    reseller_price: int = Field(description="Price in Rupiah for registered resellers")
    stock: int = Field(description="Units in stock")
    weight_grams: int = Field(description="Shipping weight of one unit in grams")


class Product(BaseModel):
    product_id: str = Field(description="Unique product id, e.g. 'KS'")
    name: str = Field(description="Product name")
    category: str = Field(description="e.g. 'kaos', 'kemeja', 'hijab'")
    variants: dict[str, Variant] = Field(description="Variants by item id")


class OrderItem(BaseModel):
    item_id: str
    product_id: str
    name: str
    options: dict[str, str]
    qty: int
    unit_price: int


class Shipment(BaseModel):
    courier: str = Field(description="'JNE', 'J&T' or 'SiCepat'")
    address: Address
    shipping_cost: int = Field(description="Ongkir in Rupiah")
    tracking_number: str | None = Field(default=None, description="Resi, once shipped")
    events: list[str] = Field(default_factory=list, description="Courier tracking events, oldest first")


class ReturnRequest(BaseModel):
    item_ids: list[str]
    reason: Literal["cacat", "salah kirim"]
    requested_at: str


class Order(BaseModel):
    order_id: str = Field(description="Unique order id, e.g. 'ORD-1001'")
    customer_id: str
    status: OrderStatus
    created_at: str
    items: list[OrderItem]
    shipment: Shipment
    payment_method: PaymentMethod
    promo_code: str | None = None
    discount: int = Field(default=0, description="Promo discount in Rupiah")
    unique_code: int = Field(default=0, description="Kode unik added to a transfer total; 0 for COD")
    total: int = Field(description="Items - discount + ongkir + kode unik, in Rupiah")
    paid_transfer_id: str | None = None
    delivered_at: str | None = None
    cancel_reason: Literal["tidak jadi", "salah pesan"] | None = None
    refund_due: int = Field(default=0, description="Rupiah the admin must send back after a cancel")
    return_request: ReturnRequest | None = None


class BankTransfer(BaseModel):
    transfer_id: str = Field(description="Unique id of the incoming transfer, e.g. 'TRF-501'")
    bank: Bank
    amount: int = Field(description="Amount received in Rupiah")
    sender_name: str
    received_at: str
    used_for_order: str | None = Field(default=None, description="Order this transfer already paid")


class ShippingRate(BaseModel):
    city: str
    courier: str
    price_per_kg: int = Field(description="Rupiah per started kilogram")
    eta_days: str = Field(description="Courier's estimate, e.g. '2-3'")
    cod: bool = Field(description="Whether COD is available for this city with this courier")


class Promo(BaseModel):
    code: str
    percent: int = Field(description="Discount on the items, in percent")
    min_purchase: int = Field(description="Minimum item total in Rupiah")
    valid_until: str = Field(description="Last valid day, YYYY-MM-DD (WIB)")


class Handoff(BaseModel):
    order_id: str | None = Field(default=None, description="The order it is about, if any")
    reason: Literal["paket bermasalah", "ongkir berubah", "pengembalian uang", "lainnya"]


class TokoDB(DB):
    """The shop's whole state. `chat` is set per task: the number the current chat is with."""

    shop: Shop
    chat: Chat
    customers: dict[str, Customer]
    products: dict[str, Product]
    orders: dict[str, Order]
    transfers: dict[str, BankTransfer]
    shipping_rates: list[ShippingRate]
    promos: dict[str, Promo]
    handoffs: list[Handoff] = Field(default_factory=list, description="Chats handed to a person")
