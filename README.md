# toko-wa-bench

**An Indonesian WhatsApp-shop domain for [tau-bench](https://github.com/sierra-research/tau2-bench),
and a measurement of what context compaction makes a customer-service agent forget.**

Work in progress. Nothing below is a result yet.

## Why

A shop on WhatsApp has one endless thread per customer. Customers switch topics, write
"yg item L 2 ya" (item = black), come back days later with "kirim ke alamat yang kemarin", and say
"udh tf ya kak" before the money has arrived. An agent that serves them has to decide what to keep
of that thread when it grows too long: keep everything, drop old messages, summarise, or keep a note
of facts. This repo measures what each choice costs in tasks done wrong, and what it saves.

tau-bench (Sierra) is the standard benchmark for customer-service agents: a simulated customer, a
written policy, tools that change a database, and a check of the database at the end. SEATauBench
(EMNLP 2026) translated its airline, retail and telecom tasks into Indonesian and four other
Southeast Asian languages. This domain is not a translation: it is a small Bandung clothing shop
with Rupiah prices, transfer with a kode unik, COD by city, ongkir per kilogram, and the way people
actually write on WhatsApp.

## The domain

- `data/toko_wa/policy.md`: the shop's rules, in Indonesian, written like an admin's SOP.
- `src/toko_wa/tools.py`: 16 tools (find a customer by WhatsApp number, products, ongkir, orders,
  the bank statement, tracking, returns, hand-off to a person). Each write tool enforces the rules
  itself and refuses with a sentence the agent can read.
- `src/toko_wa/seed.py`: 13 customers, 6 products, past orders made with the same tools, the bank
  statement, the courier price list. Every name, number and address is made up.
- It plugs into tau-bench through its registry; tau-bench itself is not changed.

## Run it

```bash
uv sync
uv run python scripts/make_db.py   # writes data/toko_wa/db.json
uv run pytest
```

MIT licence. Fikri Alfaraby, [fikrialfaraby.com](https://fikrialfaraby.com).
