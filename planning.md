# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.


### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
This tool parses the user query into structured parameters and searches `listings.json` for items that match. It returns a ranked list of matching listing dictionaries sorted by relevance (closeness of description match, then ascending price).

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): A plain-language description of the item the user wants (e.g. `"vintage graphic tee"`). Used to match against the `title`, `description`, and `style_tags` fields in the listings data.

- `size` (str): The clothing size the user needs (e.g. `"M"`, `"Oversized"`, `"US 7"`).

- `max_price` (float): The maximum price the user is willing to pay. Only listings with `price <= max_price` are returned.


**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
A tuple `(results, message)`:
- `results` (`list[dict]`): the matching listing dictionaries, sorted by relevance (best match first). Each dictionary contains all fields from `listings.json` for that item: `id` (str), `title` (str), `description` (str), `category` (str), `style_tags` (list[str]), `size` (str), `condition` (str), `price` (float), `colors` (list[str]), `brand` (str), and `platform` (str). Empty list `[]` if no listings match.
- `message` (`str`): empty string `""` on success; on no match, a short informative message (e.g. `"No listings found for your search criteria."`).

The planning loop unpacks the tuple, uses `results` to decide whether to proceed, and stores `message` in `session["error"]` when `results` is empty.


**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
The tool itself returns a short no-match message (it never raises an exception and never returns nothing — it returns `([], message)`). When `results` is empty, the planning loop copies that `message` into `session["error"]`, returns early, and does not call `suggest_outfit` or `create_fit_card`.
---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->

This tool takes the selected thrifted item and the user's existing wardrobe and uses an LLM to suggest one or more outfit combinations. It reasons about style, color compatibility, and aesthetic to pair the new item with pieces the user already owns.


**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): The listing dictionary selected from `search_listings` results (same schema as above: `id`, `title`, `price`, `size`, `colors`, `style_tags`, etc.).

- `wardrobe` (dict): The user's wardrobe loaded from `wardrobe_schema.json`. Contains a key `"items"` (list[dict]), where each wardrobe item has: `id` (str), `name` (str), `category` (str, one of: tops/bottoms/outerwear/shoes/accessories), `colors` (list[str]), `style_tags` (list[str]), and `notes` (str | None).


**What it returns:**
<!-- Describe the return value -->

A tuple `(is_fallback, text)`:
- `is_fallback` (`bool`): `True` when the wardrobe was empty and `text` is general styling advice; `False` when `text` references the user's actual wardrobe pieces. Mainly used for testing. 
- `text` (`str`): a non-empty string describing one or more complete outfit combinations. Example: `"Pair the Harley Davidson tee with your wide-leg black jeans and chunky white sneakers for a 90s grunge look. Tuck the front corner of the tee slightly for shape."` If the wardrobe is empty, `text` is general styling advice for the new item based on its style tags alone.

The planning loop unpacks the tuple and passes only `text` forward (to `session["outfit_suggestion"]` and to `create_fit_card`), while `is_fallback` can be used to flag in the UI that the suggestion is generic rather than wardrobe-specific.


**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->

If `wardrobe["items"]` is empty, the tool does not crash — it falls back to LLM-generated general styling advice for the item (e.g. "This tee pairs well with wide-leg jeans and chunky sneakers based on its vintage style tags."). The loop stores this fallback string in `session["outfit_suggestion"]` and continues to `create_fit_card`. If the LLM call itself fails, `session["error"]` is set to an informative message and the loop returns early.

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->

This tool takes an outfit suggestion and the selected new item, and uses an LLM to generate a short, shareable social media caption — the kind of thing someone would post with an outfit photo on Instagram or TikTok.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): The outfit suggestion string returned by `suggest_outfit`.

- `new_item` (dict): The selected listing dictionary (same schema as Tool 1), used to pull in specific details like price, platform, and item title for the caption. 


**What it returns:**
<!-- Describe the return value -->
A short string (`str`) of 1–3 sentences formatted as a casual social media caption. Example: `"thrifted this faded harley tee off depop for $22 and it was made for my wide-legs 🖤 full look in my stories"`. The output should vary meaningfully for different inputs — if two calls return identical text, the LLM temperature should be increased.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->

If `outfit` is an empty string or `None`, the tool returns a descriptive error string (e.g. `"Could not generate a fit card: outfit suggestion was missing."`) rather than raising an exception. The planning loop stores this message in `session["fit_card"]` so the UI can display it informatively.

---
### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->
---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
---
The planning loop runs sequentially through three tool calls. At each step it checks the result before proceeding. Here is the exact conditional logic:

**Step 1 — `search_listings`:**
Call `search_listings(description, size, max_price)` with parameters parsed from the user query; it returns a tuple `(results, message)`. Check if `results` is an empty list. If yes: set `session["error"] = message` (the tool's own informative no-match message) and return the session early — do not call `suggest_outfit` or `create_fit_card`. If no: set `session["selected_item"] = results[0]` (the top-ranked match) and proceed to Step 2.

**Step 2 — `suggest_outfit`:**
Call `suggest_outfit(new_item=session["selected_item"], wardrobe=wardrobe)`, which returns a tuple `(is_fallback, text)`. If the LLM call raises an exception: set `session["error"]` with an informative message and return early. If the call succeeds (including the empty-wardrobe fallback path): unpack the tuple, set `session["outfit_suggestion"] = text` (and optionally store `is_fallback` for the UI), then proceed to Step 3.

**Step 3 — `create_fit_card`:**
Call `create_fit_card(outfit=session["outfit_suggestion"], new_item=session["selected_item"])`. If `outfit` is empty or `None`: set `session["fit_card"]` to the error string returned by the tool and return the session. If the call succeeds: set `session["fit_card"] = result` and return the completed session.

The loop does not re-prompt the user or retry automatically. Each tool is called at most once per session. The agent only moves forward — it never loops back to an earlier tool.


## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->


All state is stored in a single `session` dictionary that is created at the start of `run_agent()` and passed through each step. The following keys are written during execution:

| Key | Type | Set when | Used by |
|-----|------|----------|---------|
| `session["selected_item"]` | `dict` | After `search_listings` succeeds | `suggest_outfit`, `create_fit_card` |
| `session["outfit_suggestion"]` | `str` | After `suggest_outfit` succeeds | `create_fit_card` |
| `session["fit_card"]` | `str` | After `create_fit_card` completes | Returned to UI |
| `session["error"]` | `str` | When any tool triggers an early exit | Returned to UI |

No tool reads from the session directly — each tool receives its inputs as explicit function arguments. The planning loop is responsible for reading from the session and passing values forward. This keeps tools independently testable with hardcoded inputs.

---
## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | No listings match the query parameters | Sets `session["error"]` to the tool's no-match message: `"No listings found for your search criteria."` Returns the session early without calling the remaining tools. |
| `suggest_outfit` | `wardrobe["items"]` is empty | Falls back to LLM-generated general styling advice based on the new item's `style_tags` alone. Stores the fallback string in `session["outfit_suggestion"]` and continues to `create_fit_card` — this is not a fatal error. |
| `create_fit_card` | `outfit` argument is an empty string or `None` | Returns a descriptive error string: `"Could not generate a fit card: outfit suggestion was missing."` The planning loop stores this in `session["fit_card"]` so the UI panel shows the message rather than crashing. |


---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

---

```
User query
    │
    ▼
Planning Loop
    │
    ├─► search_listings(description, size, max_price)
    │       │
    │       ├── results == [] ──► session["error"] = "No listings found..." ──► return session (early)
    │       │
    │       └── results != []
    │               │
    │           session["selected_item"] = results[0]
    │               │
    ├─► suggest_outfit(new_item=selected_item, wardrobe=wardrobe)
    │       │
    │       ├── wardrobe["items"] == [] ──► fallback: general styling advice (not a fatal error)
    │       │                                   │
    │       │                               session["outfit_suggestion"] = fallback_string
    │       │                                   │
    │       ├── LLM call fails ──► session["error"] = "Outfit suggestion failed..." ──► return session (early)
    │       │
    │       └── success
    │               │
    │           session["outfit_suggestion"] = result
    │               │
    └─► create_fit_card(outfit=outfit_suggestion, new_item=selected_item)
            │
            ├── outfit is empty/None ──► session["fit_card"] = "Could not generate fit card..."
            │
            └── success
                    │
                session["fit_card"] = result
                    │
                    ▼
              Return session
              (selected_item + outfit_suggestion + fit_card all populated)
```

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**

For `search_listings`: I'll give Claude the Tool 1 spec block from this file (input parameters, return value, failure mode) and ask it to implement the function using `load_listings()` from `utils/data_loader.py`. Before running the generated code, I'll verify it filters by all three parameters (`description`, `size`, `max_price`) and returns `[]` rather than raising an exception when nothing matches. I'll test it with three queries: one that should return results, one with an impossible size + price combo that should return `[]`, and one with `size=None` to confirm size filtering is skipped correctly.

For `suggest_outfit`: I'll give Claude the Tool 2 spec block and the `wardrobe_schema.json` structure, and ask it to implement the function using the Groq API (`llama-3.3-70b-versatile`). Before running, I'll check that the generated code handles the empty-wardrobe case without crashing. I'll test it with `get_example_wardrobe()` (should return styled advice) and `get_empty_wardrobe()` (should return fallback general advice, not an exception or empty string).

For `create_fit_card`: I'll give Claude the Tool 3 spec block and ask it to implement the function using the Groq API. Before running, I'll check that it guards against an empty `outfit` string. I'll run it three times on the same input and confirm the outputs differ — if they're identical, I'll ask Claude to increase the `temperature` parameter.

**Milestone 4 — Planning loop and state management:**

I'll give Claude the full ## Architecture diagram and both the ## Planning Loop and ## State Management sections from this file, and ask it to implement `run_agent()` in `agent.py`. Before running, I'll review the generated code and check three things: (1) it branches on `search_listings` returning an empty list; (2) it stores values in the `session` dict between steps rather than passing them as local variables; (3) it does not call all three tools unconditionally regardless of earlier results. I'll then run a happy-path query and print `session["selected_item"]` to confirm it matches what `suggest_outfit` received. I'll also run an impossible query to confirm `session["error"]` is set and `session["fit_card"]` is `None`.

---

## A Complete Interaction (Step by Step)

Initially, the user requests an item description. FitFindr finds a piece that fits this description and triggers a recommendation engine to suggest an outfit with that piece. After a combination is chosen, it generates a shareable social media fit card. If it can't find an item in `search_listings()`, it handles the error by terminating the loop early (preventing subsequent tool calls later) and providing an informative message.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
The agent parses the user's request and identifies constraints for the item the user wants (`description="vintage graphic tee"`, `size=None`, `max_price=30.0`). It calls the first tool: `search_listings(description="vintage graphic tee", size=None, max_price=30.0)`. 

Note: If this tool returns an empty list, the loop terminates here (early), sets `session["error"] = "No listings found for your search criteria."` in the session state, and prevents subsequent tool calls from running.

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
Assuming Step 1 successfully finds items, it returns a list of matching listing dictionaries. The top result might be: `{"id": "listing_042", "title": "90s Vintage Harley Davidson Tee", "price": 25.0, "size": "L", "colors": ["black", "orange"], "style_tags": ["vintage", "graphic", "band tee"], "platform": "Depop", "condition": "Good"}`. The agent saves `results[0]` to `session["selected_item"]` and calls `suggest_outfit(new_item=session["selected_item"], wardrobe=get_example_wardrobe())`. The wardrobe passed in contains items like `{"id": "w_001", "name": "Baggy straight-leg jeans, dark wash", "category": "bottoms", "colors": ["dark blue", "indigo"], "style_tags": ["denim", "streetwear", "baggy"], "notes": "High-waisted, sits above the hip"}` and `{"id": "w_007", "name": "Chunky white sneakers", "category": "shoes", "colors": ["white"], "style_tags": ["sneakers", "chunky", "streetwear"], "notes": null}` — the LLM reasons over all 10 items to pick the best combination with the new tee.

**Step 3:**
<!-- Continue until the full interaction is complete -->
The `suggest_outfit` tool returns a string such as: `"Pair this tee with your wide-leg black jeans and chunky white sneakers for a classic 90s grunge look. Roll the sleeves once and tuck the front corner slightly for shape."`. The agent saves this to `session["outfit_suggestion"]` and calls `create_fit_card(outfit=session["outfit_suggestion"], new_item=session["selected_item"])`.


**Final output to user:**
<!-- What does the user actually see at the end? -->
The user sees the final formatted results in the UI panels, containing:
1. The matching secondhand item details found within their budget (title, price, platform, condition, size).
2. The recommended styling advice incorporating their existing wardrobe items.
3. A formatted, shareable social media "fit card" text summary ready to post.