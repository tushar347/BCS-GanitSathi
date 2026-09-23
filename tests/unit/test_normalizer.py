from src.normalizer.bengali_normalizer import BengaliNormalizer


def test_digit_conversion():
    normalizer = BengaliNormalizer()
    raw = "একটি সংখ্যার ২৫% হলো ১২০"
    result = normalizer.normalize(raw)
    assert "25%" in result.normalized_text
    assert "120" in result.normalized_text
    assert result.original_text == raw


def test_decimal_and_mixed():
    normalizer = BengaliNormalizer()
    raw = "মূল্য ৩.৫ টাকা বা ৩,৫ টাকা"
    result = normalizer.normalize(raw)
    assert "3.5" in result.normalized_text


def test_reversible_digits():
    normalizer = BengaliNormalizer()
    bn_num = "১২৩৪৫৬৭৮৯০"
    result = normalizer.normalize(bn_num)
    assert result.normalized_text == "1234567890"
    back_to_bn = result.to_bengali()
    assert back_to_bn == bn_num


def test_operator_spacing_and_preservation():
    normalizer = BengaliNormalizer()
    raw = "ক+৫>=১০"
    result = normalizer.normalize(raw)
    assert ">=" in result.normalized_text
    assert "10" in result.normalized_text

