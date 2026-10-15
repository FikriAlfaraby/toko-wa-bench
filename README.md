# toko-wa-bench

**An Indonesian WhatsApp-shop domain for [tau-bench](https://github.com/sierra-research/tau2-bench),
and a measurement of what an agent forgets when a long chat is compacted.**

Status: designed and pre-registered. No result below yet; the predictions were written before any
model ran the experiment.

## Why

A shop on WhatsApp has one endless thread per customer. Customers switch topics mid-order, write
"yg item L 2 ya" (item means black), come back the next day with "kirim ke alamat yang kemarin aku
bilang", and say "udh tf ya kak" before the money arrives. An agent serving them has to decide
what to keep of that thread when it grows: everything, the recent messages only, a summary, or a
note of facts. This repo measures what each choice costs in tasks done wrong, and what it saves.

[tau-bench](https://github.com/sierra-research/tau2-bench) (Sierra) is the standard benchmark for
customer-service agents: a simulated customer, a written policy, tools that change a database, and
a check of the database at the end. [SEATauBench](https://github.com/SEACrowd/SEATauBench) (Findings
of EMNLP 2026) translated its airline, retail and telecom tasks into Indonesian and four other
Southeast Asian languages. This domain is not a translation: it is a small Bandung clothing shop
with Rupiah prices, transfers with a kode unik, COD by city, ongkir per started kilogram, and
chats written the way people write on WhatsApp. None of tau-bench's 2,449 retail, airline and
telecom tasks starts with an earlier chat history; five of these do.

## The domain

- `data/toko_wa/policy.md`: the shop's rules in Indonesian, written like an admin's SOP.
- `src/toko_wa/tools.py`: 16 tools: the chat's WhatsApp number, customers, products, ongkir,
  orders, the bank statement (mutasi), tracking, returns, and a hand-off to a person. Each write
  tool enforces the rules itself and refuses with a sentence the agent can read.
- `src/toko_wa/seed.py`: 13 customers, 6 products, past orders made with the same tools, the bank
  statement and the courier price list. Every name, number and address is made up.
- `data/toko_wa/task_specs.yaml`: the 13 chats, by hand. `scripts/make_tasks.py` replays each
  task's reference actions on a fresh shop and fills in every Rupiah amount an assertion quotes,
  so no total is computed by hand.
- It plugs into tau-bench through its registry; tau-bench itself is not changed.

## The tasks

| Group | Task | The trap |
|---|---|---|
| Topic switch | ts-01 | ongkir question, then "paket aku yg kemarin kok blm sampe", then "jd yg tadi 2 ya" |
| | ts-02 | asks about a shirt, then a parcel stuck for 3 days; orders nothing; must be handed to a person |
| | ts-03 | an address change for yesterday's unpaid order and a new order, interleaved |
| | ts-04 | asks to change an unpaid order, then cancels it and asks for a return instead |
| Long context | lc-01 | "kirim ke alamat yg kemarin aku bilang": Mama's house, said early in yesterday's chat |
| | lc-02 | "checkout yg tadi": the hoodie was changed from M to L later in the morning's chat |
| | lc-03 | "yg nomer 2 dr list hijab kmrn": yesterday's list was in a different order from the catalogue |
| | lc-04 | "sesuai janji kemarin": the admin promised GAJIAN10 and refused free ongkir |
| | lc-05 | yesterday the customer forwarded a fake "admin" free-ongkir message; nobody answered it |
| Other | ot-01 | "udh tf ya kak, 227rb, ini buktinya [gambar]": the transfer lacks the kode unik |
| | ot-02 | Sundanese: "tiasa COD ka Garut?" (COD does not reach Garut) |
| | ot-03 | "2 ya", then "eh 1 aja deh" |
| | ot-04 | a forwarded "admin" message promising reseller prices and free ongkir |

The database is checked at the end, as in tau-bench. Where a task also depends on what the agent
says (the exact amount to transfer, that COD is unavailable), a language model judges the
conversation; it judges only words, because tau-bench's judge does not reliably see tool calls.
Hand-offs are recorded in the database so that they are checked like any other action.

## The four strategies (`src/toko_wa/context.py`)

| Strategy | What the agent sees of the earlier conversation |
|---|---|
| full | everything (tau-bench's own agent) |
| drop | nothing, and a line saying older messages are hidden |
| summary | a summary the same model writes |
| facts | a note of facts the same model keeps up to date ("koreksi: L, mengganti M") |

When a chat resumes after an earlier session (the task's starting history), drop, summary and
facts compact that whole session before their first reply, the way an agent reloads a thread the
next day. Within a session, the conversation may hold about 2,000 tokens (characters / 4), what is
left of an 8k context after the policy and tool schemas; past that, all but the last ~800 tokens
are compacted, cutting at a customer message so no tool result loses its call. The note opens the
conversation, marked as an automatic note from the shop's system. Every compaction, its note and
the tokens it cost are recorded in the run.

## Predictions, written before any model ran the experiment

Setup: 13 tasks x 4 strategies x 2 agent models (GPT-6 Luna, Gemini 3.8 Flash) x 3 trials = 312
conversations. The simulated customer and the judge are GPT-6 Luna for every run.

1. On the five long-context tasks, drop scores lowest of the four strategies for both models, at
   least 0.30 below full (pass^1).
2. On the long-context tasks, facts scores at least as well as summary, for both models.
3. On the eight tasks without an earlier session, every strategy is within 0.15 of full, for each
   model.
4. lc-05: under summary or facts, at least one of the 12 runs fails because the agent treats the
   forwarded free-ongkir message as the shop's offer (read by hand); under full, none does.
5. On the long-context tasks, summary and facts use at least 25% fewer agent prompt tokens than
   full, counting the compaction calls.
6. Under full, Gemini scores at least as well as Luna over all 13 tasks.

### What was tried before the predictions, and changed

- An answer-key agent (tau-bench's `llm_agent_gt`, which is told the reference actions) ran every
  task to find broken ones. Two failed at first: ts-02's reference skipped the lookups and its
  judge sentence asked about a tool call; lc-04 failed once and passed four times after. The
  reference and the policy line on hand-offs were fixed; lc-05 was added and checked the same way.
- A probe task outside the 13 (smoke-02) ran each strategy. With the note as a second system
  message, the agent ignored it ("kurir yang Kakak maksud belum terlihat di chat ini") although the
  note said "kurir: JNE"; the note now opens the conversation instead. Compaction at the resume
  point was added after the first probe showed the in-session budget alone cut too late to matter.

### Changed after the tag

- History messages now carry fixed times. tau2 stamps a history message with the time it is loaded,
  so a task with a history hashed differently on every load and `--auto-resume` refused to continue
  a run interrupted by a usage limit ("Tasks were modified"). The model and the simulated customer
  receive only role and content, never the time; apart from the times, `tasks.json` is identical to
  the tagged version (checked by a script). Runs started before this change (Luna, full and drop)
  are kept; the others restarted.

## Run it

```bash
uv sync
uv run python scripts/make_db.py      # writes data/toko_wa/db.json
uv run python scripts/make_tasks.py   # writes tasks.json from task_specs.yaml
uv run pytest
# tau2 installed from git has no data folder: point TAU2_DATA_DIR at a clone of tau2-bench at 5ade54e
TAU2_DATA_DIR=../tau2-bench/data LLM_BASE_URL=... LLM_API_KEY=... \
  uv run python scripts/run.py --judge <model> -- run --domain toko_wa --agent ctx_summary \
  --agent-llm openai/<model> --user-llm openai/<model> --num-trials 3
```

MIT licence. Fikri Alfaraby, [fikrialfaraby.com](https://fikrialfaraby.com).
