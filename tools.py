"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> tuple[list[dict], str]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A tuple (results, message):
        - results (list[dict]): matching listing dicts, sorted by relevance
          (best match first). Empty list if nothing matches.
        - message (str): empty string on success; on no match, a specific,
          informative message naming the filters applied and what to adjust.
        Never raises an exception for a no-match case.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()

    # Break the description into lowercase keywords for matching.
    keywords = [w for w in description.lower().split() if w]

    results = []
    for listing in listings:
        # Filter by price ceiling (inclusive).
        if max_price is not None and listing["price"] > max_price:
            continue

        # Filter by size (case-insensitive substring match).
        if size is not None:
            if size.lower() not in listing["size"].lower():
                continue

        # Score by keyword overlap against title, description, and style_tags.
        haystack = " ".join([
            listing["title"],
            listing["description"],
            " ".join(listing["style_tags"]),
        ]).lower()

        score = sum(1 for kw in keywords if kw in haystack)

        # Drop listings with no keyword matches.
        if score == 0:
            continue

        results.append((score, listing))

    # Sort by score (highest first), then by price (lowest first) to break ties.
    results.sort(key=lambda r: (-r[0], r[1]["price"]))
    matches = [listing for score, listing in results]

    if not matches:
        # Build a specific, informative no-match message naming the filters used.
        message = ("No listings found for your search criteria.")
        return ([], message)
    
    return (matches, "")


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> tuple[bool, str]:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A tuple (is_fallback, text):
        - is_fallback (bool): True if the wardrobe was empty and `text` is
          general styling advice; False if `text` references the user's
          actual wardrobe pieces.
        - text (str): a non-empty string with outfit suggestions. If the
          wardrobe is empty, this is general styling advice rather than an
          exception or an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    client = _get_groq_client()

    # Compact summary of the thrifted item for the prompt.
    item_summary = (
        f"{new_item['title']} "
        f"(colors: {', '.join(new_item.get('colors', []))}; "
        f"style: {', '.join(new_item.get('style_tags', []))})"
    )

    items = wardrobe.get("items", [])
    empty_wardrobe = True

    if not items:
        # Empty wardrobe -> general styling advice based on the item alone.
        prompt = (
            f"A user is considering buying this secondhand item: {item_summary}.\n"
            "They have not listed any wardrobe items yet. Suggest general styling "
            "ideas for this one piece: what kinds of items pair well with it, what vibe "
            "it suits, and how to wear it. Keep it to 2-3 sentences."
        )
    else:
        # Format the wardrobe so the LLM can reference pieces by name.
        wardrobe_lines = []
        for w in items:
            wardrobe_lines.append(
                f"- {w['name']} ({w['category']}; "
                f"colors: {', '.join(w.get('colors', []))}; "
                f"style: {', '.join(w.get('style_tags', []))})"
            )
        wardrobe_text = "\n".join(wardrobe_lines)

        prompt = (
            f"A user is adding this secondhand item to their wardrobe: {item_summary}.\n\n"
            f"Their existing wardrobe:\n{wardrobe_text}\n\n"
            "Suggest 1-2 complete outfit combinations pairing the new item with "
            "specific pieces from their wardrobe (refer to pieces by name). "
            "Reason about color compatibility and overall aesthetic. "
            "Keep it to 2-4 sentences."
        )
        empty_wardrobe = False

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a personal stylist who gives concise, practical outfit advice.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    return (empty_wardrobe, response.choices[0].message.content.strip())


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict, is_general: bool = False) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:     The outfit suggestion string from suggest_outfit().
        new_item:   The listing dict for the thrifted item.
        is_general: True when `outfit` is generic styling advice (the user has
                    no wardrobe yet) rather than a real outfit built from owned
                    pieces. When True, the caption must NOT claim the user wore
                    or owns specific items — it hypes the thrifted find itself
                    and frames any styling as ideas ("can't wait to style it
                    with…"), so it doesn't hallucinate a wardrobe.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # Guard against a missing or whitespace-only outfit suggestion.
    if not outfit or not outfit.strip():
        return "Could not generate a fit card: outfit suggestion was missing."

    client = _get_groq_client()

    item_block = (
        f"Item: {new_item.get('title', 'this piece')}\n"
        f"Price: ${new_item.get('price', '?')}\n"
        f"Platform: {new_item.get('platform', 'a resale app')}\n"
        f"Styling notes: {outfit}\n\n"
    )

    if is_general:
        # No real wardrobe -> don't claim the user wore/owns specific pieces.
        prompt = (
            "Write a casual, authentic Instagram/TikTok-style caption for a "
            "thrifted find the user just bought.\n\n"
            + item_block
            + "Guidelines:\n"
            "- 1-3 sentences, sounds like a real post (not a product description).\n"
            "- Mention the item name, price, and platform naturally, once each.\n"
            "- Hype the piece itself. Do NOT claim the user wore or owns any other "
            "specific clothing — they have no wardrobe yet. Frame any styling as "
            "future ideas (e.g. \"can't wait to style it with…\"), not as an outfit "
            "they put together.\n"
            "Return only the caption text."
        )
    else:
        prompt = (
            "Write a casual, authentic Instagram/TikTok-style caption for an outfit "
            "post about a thrifted find.\n\n"
            + item_block
            + "Guidelines:\n"
            "- 1-3 sentences, sounds like a real OOTD post (not a product description).\n"
            "- Mention the item name, price, and platform naturally, once each.\n"
            "- Capture the outfit vibe in specific terms.\n"
            "Return only the caption text."
        )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You write fun, authentic social media outfit captions.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=1.0,
    )

    return response.choices[0].message.content.strip()
