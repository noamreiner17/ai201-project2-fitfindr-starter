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

def test_suggest_outfit_returns_tuple():
    suggestion = suggest_outfit(new_item, wardrobe)
    assert isinstance(suggestion, tuple)
    assert len(suggestion) == 2
    assert isinstance(suggestion[0], bool)
    assert isinstance(suggestion[1], str)

def test_suggest_outfit_full_wardrobe():
    suggestion = suggest_outfit(new_item, wardrobe)
    assert suggestion[0] is False      
    assert isinstance(suggestion[1], str)
    assert len(suggestion[1]) > 0

def test_suggest_outfit_no_wardrobe():
    suggestion = suggest_outfit(new_item, wardrobe_empty)
    assert suggestion[0] is True
    assert isinstance(suggestion[1], str)
    assert len(suggestion[1]) > 0

def test_suggest_outfit_varies_by_item():
    other_item = {
        "id": "test999",
        "title": "Black leather biker jacket",
        "description": "Edgy black leather jacket with silver hardware.",
        "category": "outerwear",
        "style_tags": ["edgy", "punk", "streetwear"],
        "size": "M",
        "condition": "good",
        "price": 80.00,
        "colors": ["black"],
        "brand": "RiderCo",
        "platform": "depop",
    }
    _, text_a = suggest_outfit(new_item, wardrobe)
    _, text_b = suggest_outfit(other_item, wardrobe)
    assert text_a != text_b