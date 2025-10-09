from src.utils import normalize_text
def test_normalize_nfkc():
    assert normalize_text("Ａ B\u200B C") == "A B C"
