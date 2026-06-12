# tests/test_tools.py
from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

#run using this comand in terminal: python -m pytest test/test_tools.py
"""
Tests for search_listings
"""

def test_search_returns_results():
    results, message = search_listings("denim jeans", size=None, max_price=60)
    assert isinstance(results, list)
    assert len(results) >= 1
    assert message == ""   # no error message on success

def test_search_empty_results():
    results, message = search_listings("sequined astronaut gown", size="XXS", max_price=2)
    assert results == []# empty list, no exception
    assert isinstance(message, str) and len(message) > 0
    assert message == "No listings found for your search criteria."

def test_search_price_filter():
    results, message = search_listings("shirt", size=None, max_price=20)
    assert all(item["price"] <= 20 for item in results)


"""
Tests for suggest_outfit
"""

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


"""
Tests for create_fit_card
"""

outfit_text = (
    "Pair the vintage floral dress with white sneakers and a denim jacket "
    "for an easy spring day look."
)

def test_create_fit_card_returns_caption():
    caption = create_fit_card(outfit_text, new_item)
    assert isinstance(caption, str)
    assert len(caption) > 0

def test_create_fit_card_empty_outfit():
    # Empty or whitespace-only outfit -> descriptive error string, no exception.
    error_msg = "Could not generate a fit card: outfit suggestion was missing."
    assert create_fit_card("", new_item) == error_msg
    assert create_fit_card("   ", new_item) == error_msg
    assert create_fit_card(None, new_item) == error_msg

def test_create_fit_card_varies_by_input():
    # Higher temperature: different outfits should give different captions.
    other_outfit = "Style the dress with chunky boots and a leather jacket for an edgy twist."
    caption_a = create_fit_card(outfit_text, new_item)
    caption_b = create_fit_card(other_outfit, new_item)
    assert caption_a != caption_b