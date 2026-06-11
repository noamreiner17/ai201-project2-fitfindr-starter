# tests/test_tools.py
from tools import search_listings, suggest_outfit
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

#run using this comand in terminal: python -m pytest test/test_tools.py
"""
Tests for search_listings
"""

def test_search_returns_results():
    results = search_listings("denim jeans", size=None, max_price=60)
    assert isinstance(results, list)
    assert len(results) >= 1

def test_search_empty_results():
    results = search_listings("sequined astronaut gown", size="XXS", max_price=2)
    assert results == []   # empty list, no exception

def test_search_price_filter():
    results = search_listings("shirt", size=None, max_price=20)
    assert all(item["price"] <= 20 for item in results)


"""
Tests for suggest_outfit
"""

#def suggest_outfit(new_item: dict, wardrobe: dict) -> str:

new_item = {
    "id": "test123",
    "title": "Vintage floral dress",
    "description": "A lovely vintage floral dress perfect for spring.",
    "category": "dresses",
    "style_tags": ["vintage", "floral", "spring"],
    "size": "M",
    "condition": "good",
    "price": 45.00,
    "colors": ["pink", "green"],
    "brand": "RetroStyle",
    "platform": "depop"
}

wardrobe = get_example_wardrobe()
wardrobe_empty = get_empty_wardrobe()

def test_suggest_outfit_returns_string():
    suggestion = suggest_outfit(new_item, wardrobe)
    assert isinstance(suggestion, str)
    assert len(suggestion) > 0

def test_suggest_outfit_no_wardrobe():
    suggestion = suggest_outfit(new_item, wardrobe_empty)
    assert isinstance(suggestion, str)
    assert len(suggestion) > 0


"""
Right — you want to test the empty-wardrobe branch vs the full-wardrobe branch and actually see what each returns. Here's how.

The test

from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

def test_suggest_outfit_empty_wardrobe():
    empty = get_empty_wardrobe()
    result = suggest_outfit(new_item, empty)
    # Should NOT crash and should NOT be empty, even with no wardrobe items
    assert isinstance(result, str)
    assert len(result) > 0
    print("\n[EMPTY WARDROBE]\n", result)

def test_suggest_outfit_full_wardrobe():
    full = get_example_wardrobe()
    result = suggest_outfit(new_item, full)
    assert isinstance(result, str)
    assert len(result) > 0
    print("\n[FULL WARDROBE]\n", result)
How to actually SEE the responses
By default pytest hides print() output for passing tests. Add the -s flag to see it:


python -m pytest test/test_tools.py -v -s
That prints both responses so you can eyeball that:

the empty one gives general advice (no named wardrobe pieces — it can't reference items it doesn't have)
the full one names specific pieces from the example wardrobe
Optional: assert the difference automatically
If you want the test itself to prove the two branches behave differently (not just print them):


def test_empty_vs_full_differ():
    general = suggest_outfit(new_item, get_empty_wardrobe())
    specific = suggest_outfit(new_item, get_example_wardrobe())

    # The two branches should produce different advice
    assert general != specific

    # The full-wardrobe response should mention at least one real wardrobe item
    wardrobe_names = [w["name"] for w in get_example_wardrobe()["items"]]
    # check a distinctive word from any wardrobe item appears in the specific output
    assert any(name.split()[0].lower() in specific.lower() for name in wardrobe_names)
That last assertion is a bit strict (the LLM might paraphrase a name), so if it flakes, drop it and rely on general != specific plus the printed output for your own review.

My suggestion: start with the two print-based tests + -s so you can read the responses yourself — that's the "test it and review the output" discipline your milestone is asking for. Want me to add these to your file?"""