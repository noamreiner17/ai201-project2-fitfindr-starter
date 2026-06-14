# FitFindr 🛍️

FitFindr is an agentic assistant for secondhand shopping. You describe a piece you want in plain language ("vintage graphic tee under $30, size M") and the agent finds a matching listing, suggests an outfit built from your existing wardrobe, and writes a shareable social-media "fit card" to caption the find.

The point of the project is the **planning loop**: the agent doesn't blindly run three tools in a row. It parses your query, decides whether each next step is worth taking based on what the previous step returned, and bails out early with a useful message when it can't help.

---

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file in the project root (get a free key at [console.groq.com](https://console.groq.com)):

```
GROQ_API_KEY=your_key_here
```

## Running the app

```bash
python app.py
```

Then open the URL printed in your terminal. It is usually `http://localhost:7860`, but Gradio will pick a different port if 7860 is taken — read the terminal output rather than assuming the default.

The UI has a query box, a wardrobe selector (example wardrobe vs. empty/new-user wardrobe), and three output panels: the top listing found, the outfit idea, and the fit card. A set of example queries (including one deliberate no-results query) is wired in under the box.

You can also run the agent headless:

```bash
python agent.py      # runs a happy-path query and a no-results query
```

---

## Tool Inventory

The agent has three tools, all in [tools.py](tools.py). Each is a standalone function that can be tested (and tested in  [test_tools.py](test_tools.py))in isolation with hardcoded inputs.

### 1. `search_listings`

| **Purpose** | Find listings in the mock dataset that match the user's description, within an optional size and price ceiling, ranked by relevance. |
| **Inputs** | `description: str` — keywords describing the wanted item.<br>`size: str \| None` — size filter (case-insensitive substring match against each listing's `size`); `None` skips size filtering.<br>`max_price: float \| None` — inclusive price ceiling; `None` skips price filtering. |
| **Output** | `tuple[list[dict], str]` — `(results, message)`. `results` is the matching listing dicts (each with `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`), sorted by keyword-overlap score (desc) then price (asc). `message` is `""` on success, or an informative no-match message when `results` is `[]`. |

It scores each listing by how many query keywords appear in the combined `title` + `description` + `style_tags` text, drops zero-score listings, and sorts by score then price. It **never raises** on a no-match, instead it returns `([], message)`.

### 2. `suggest_outfit`

| | |
| **Purpose** | Use an LLM to pair the selected thrifted item with pieces from the user's wardrobe (or give general styling advice if the wardrobe is empty). |
| **Inputs** | `new_item: dict` — the selected listing dict.<br>`wardrobe: dict` — wardrobe with an `"items"` list (each item has `id`, `name`, `category`, `colors`, `style_tags`, `notes`). |
| **Output** | `tuple[bool, str]` — `(is_fallback, text)`. `is_fallback` is `True` when the wardrobe was empty and `text` is generic advice; `False` when `text` references the user's actual pieces by name. `text` is always a non-empty styling string. |

Model: Groq `llama-3.3-70b-versatile`, `temperature=0.7`. When `wardrobe["items"]` is empty it prompts for general styling ideas instead of crashing; otherwise it formats the named wardrobe pieces into the prompt and asks for 1–2 specific combinations.

### 3. `create_fit_card`

| | |
|---|---|
| **Purpose** | Use an LLM to turn the outfit suggestion + item details into a short, casual, shareable social-media caption. |
| **Inputs** | `outfit: str` — the suggestion text from `suggest_outfit`.<br>`new_item: dict` — the selected listing dict (for title, price, platform).<br>`is_general: bool = False` — when `True`, the caption must not claim the user owns/wore other pieces; it hypes the find and frames styling as future ideas. The loop passes `is_general=is_fallback`. |
| **Output** | `str` — a 1–3 sentence caption. If `outfit` is empty/whitespace, returns a descriptive error string instead of raising. |

Model: Groq `llama-3.3-70b-versatile`, `temperature=1.0` (high, so repeated calls vary).

There is also a non-tool helper, `_parse_query` in [agent.py](agent.py), which the loop uses before any tool — see below.

---

## The Planning Loop

The loop lives in `run_agent()` in [agent.py](agent.py). It is **sequential with early exits** — not an unconditional pipeline. Here's what it decides at each point and *why*, not just what it calls.

**Step 0 — Parse the query (`_parse_query`).** Before any tool runs, the loop converts the free-text query into structured parameters using the LLM in JSON mode (`temperature=0.0`). The model returns `{description, size, max_price}` with size/price wording stripped out of the description. Types are normalized (`size → str | None`, `max_price → float | None`). **Decision made here:** if the LLM call or JSON parse fails, the loop doesn't abort — it falls back to using the raw query as the description with no size/price filters, so search can still run. The parsed dict is stored in `session["parsed"]`.

**Step 1 — Search (`search_listings`).** Calls the tool with the parsed parameters. **Decision:** look at whether `results` is empty.
- Empty → copy the tool's own no-match `message` into `session["error"]` and **return immediately**. The agent does *not* call `suggest_outfit` or `create_fit_card`, because there's nothing to style. This is the key non-happy-path branch.
- Non-empty → select `results[0]` (highest-scoring, cheapest tie-break) as `session["selected_item"]` and continue.

**Step 2 — Suggest outfit (`suggest_outfit`).** Called with the selected item and the wardrobe. **Decision:** the tool itself decides between two paths based on whether the wardrobe has items — a real wardrobe-specific suggestion, or a generic fallback. Either way it returns `(is_fallback, text)`. The empty-wardrobe case is **not** treated as an error; the loop stores `text` and carries `is_fallback` forward so the next step can adjust its tone.

**Step 3 — Create fit card (`create_fit_card`).** Called with the outfit text, the selected item, and `is_general=is_fallback`. Passing `is_fallback` through is a deliberate decision: it prevents the caption from hallucinating a wardrobe the user doesn't have. The result is stored in `session["fit_card"]`.

**Termination.** The loop is strictly forward-only. Each tool runs **at most once** per session; the loop never retries, never re-prompts, and never loops back to an earlier tool. It is "done" when it has either returned early with an error or populated all three output fields.

```
User query
   │
   ▼
_parse_query (LLM, JSON, temp=0)  ──fail──► fall back to raw query, no filters
   │
   ▼
search_listings(description, size, max_price)
   │
   ├── results == []  ──► session["error"] = no-match message  ──► RETURN (skip remaining tools)
   │
   └── results != []  ──► session["selected_item"] = results[0]
                              │
                              ▼
                      suggest_outfit(selected_item, wardrobe)  ──► (is_fallback, text)
                              │   (empty wardrobe → generic advice, NOT an error)
                              ▼
                      session["outfit_suggestion"] = text
                              │
                              ▼
                      create_fit_card(outfit=text, new_item, is_general=is_fallback)
                              │
                              ▼
                      session["fit_card"] = caption
                              │
                              ▼
                          RETURN session
```

---

## State Management

All state for one interaction lives in a single `session` dict created by `_new_session()` and threaded through the loop. Tools never read from the session directly — the loop reads from it and passes explicit function arguments in, which keeps every tool independently testable with hardcoded inputs.

| Key | Type | Set when | Read by |
|-----|------|----------|---------|
| `query` | `str` | At init | reference |
| `parsed` | `dict` | After `_parse_query` | `search_listings` arguments |
| `search_results` | `list[dict]` | After `search_listings` | branch decision / `selected_item` |
| `selected_item` | `dict \| None` | After a successful search | `suggest_outfit`, `create_fit_card` |
| `wardrobe` | `dict` | At init | `suggest_outfit` |
| `outfit_suggestion` | `str \| None` | After `suggest_outfit` | `create_fit_card`, UI |
| `fit_card` | `str \| None` | After `create_fit_card` | UI |
| `error` | `str \| None` | On any early exit | UI (checked first) |

The UI ([app.py](app.py)) consumes the returned session by checking `session["error"]` first: if set, it shows the error in the first panel and leaves the others blank; otherwise it formats `selected_item` into the listing panel and shows `outfit_suggestion` and `fit_card` in the other two.

---

## Error Handling (per tool)

| Tool | Failure mode handled | What the agent does |
|------|---------------------|---------------------|
| `_parse_query` | LLM call errors or returns non-JSON | Falls back to raw query as `description`, `size=None`, `max_price=None`, so search still runs. |
| `search_listings` | No listing matches the filters | Returns `([], message)` (never raises). The loop puts `message` in `session["error"]` and returns early, skipping the other two tools. |
| `suggest_outfit` | Wardrobe is empty | Not fatal — returns `(True, general_advice)`. The loop continues and the fit card is told to stay generic via `is_general=True`. |
| `create_fit_card` | `outfit` is empty / whitespace | Returns `"Could not generate a fit card: outfit suggestion was missing."` instead of raising; the UI displays it. |

### Concrete example from testing

Query: **`designer ballgown size XXS under $5`** (the deliberate no-results example in the UI).

`_parse_query` returns `{description: "designer ballgown", size: "XXS", max_price: 5.0}`. `search_listings` filters out everything — no listing is both under $5 and size XXS matching those keywords — and returns:

```
([], "No listings found for 'designer ballgown' in size XXS under $5.0. Try increasing your budget or removing the size filter.")
```

The loop sets `session["error"]` to that message and returns immediately. `suggest_outfit` and `create_fit_card` are **never called**, and the UI shows the message in the listing panel with the other two panels blank. This confirms the early-exit branch works end to end rather than the agent pushing an empty item into the LLM tools.

---

## Spec Reflection

A few places where the implementation matched the plan, and a few where building it sharpened the spec:

- **The `(results, message)` tuple was the right call.** Putting the no-match message inside `search_listings` (rather than having the loop invent one) kept the loop's branch logic trivial — `if not results: session["error"] = message` — and meant the message could name the exact filters applied. The plan called for this and it held up.
- **`is_fallback` had to be plumbed all the way to the fit card.** The plan originally treated the empty-wardrobe case as just a `suggest_outfit` concern. In practice the *fit card* was the part that hallucinated — it would write "paired it with my black jeans" for a user who owns nothing. Threading `is_general=is_fallback` into `create_fit_card` was the fix, and the spec was updated to make that the explicit contract.
- **Query parsing needed a fallback path.** The plan assumed the LLM JSON parse would succeed. Wrapping it in a try/except that degrades to "search the raw query with no filters" means a flaky parse downgrades result quality instead of breaking the whole run — a more honest failure mode than crashing.
- **What I'd add next:** `search_listings` selects only `results[0]`. The richer behavior would be to surface the top few and let the user pick before styling — the session already stores the full `search_results` list, so the state model supports it without changes.

---

## AI Usage

I used Claude to help implement parts of this project. Two specific instances:

**1. Implementing `search_listings`.** I gave Claude the Tool 1 spec block from [planning.md](planning.md) (the input parameters, the `(results, message)` return contract, and the no-match failure mode) plus the `load_listings()` signature from the data loader. It produced a working keyword-overlap scorer. **What I changed:** its first version did a strict equality size match (`listing["size"] == size`), which missed listings stored as `"S/M"` when the user asked for `"M"`. I overrode it to a case-insensitive substring match (`size.lower() in listing["size"].lower()`) so combined-size listings still match. I also tightened the tie-break to sort by price ascending after score, which the spec required but the draft omitted.

**2. Implementing the planning loop in `run_agent`.** I gave Claude the Architecture diagram and the Planning Loop + State Management sections from planning.md and asked it to fill in `run_agent()`. It produced the sequential structure correctly. **What I changed:** the draft called all three tools and only checked for an empty result at the very end, which defeats the point of the early exit (it still sent an empty item into the LLM tools). I rewrote it to branch immediately after `search_listings` and `return session` before any LLM call, matching the diagram's early-exit arrow. I also had it stop returning a bare suggestion string from `suggest_outfit` and instead unpack the `(is_fallback, text)` tuple so the fallback flag could reach the fit card.
