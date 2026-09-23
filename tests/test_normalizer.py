"""Unit tests for Task 2.1 BengaliNormalizer."""

from src.normalizer.bengali_normalizer import BengaliNormalizer


def test_bengali_numeral_conversion():
    normalizer = BengaliNormalizer()
    text = "১২৫ টাকা দিয়ে ২৫টি আম ক্রয় করা হলো"
    res = normalizer.normalize(text)
    assert "125" in res.normalized_text
    assert "25" in res.normalized_text
    # Check reversible alignment
    idx_125 = res.normalized_text.find("125")
    assert res.char_map[idx_125] == text.find("১")


def test_superscript_exponent_normalization():
    normalizer = BengaliNormalizer()
    text = "x² + y³ = z⁴"
    res = normalizer.normalize(text)
    assert res.normalized_text == "x**2 + y**3 = z**4"


def test_unicode_operator_standardization():
    normalizer = BengaliNormalizer()
    text = "১০ × ৫ ÷ ২ − ১ = ২৪"
    res = normalizer.normalize(text)
    assert res.normalized_text == "10 * 5 / 2 - 1 = 24"


def test_unicode_minus_variants():
    normalizer = BengaliNormalizer()
    text = "a − b – c — d"
    res = normalizer.normalize(text)
    assert res.normalized_text == "a - b - c - d"


def test_bilingual_math_tokens_and_units():
    normalizer = BengaliNormalizer()
    text = "চালের মূল্য ১২% কমে যাওয়ায় ৬,০০০ টাকায় পূর্বাপেক্ষা ১ কুইন্টাল চাল বেশি পাওয়া যায়"
    res = normalizer.normalize(text)
    assert "টাকা" in res.units_detected
    assert "%" in res.units_detected
    assert "কুইন্টাল" in res.units_detected
    assert "কমে" in res.directional_terms_detected
    assert "বেশি" in res.directional_terms_detected
    assert "12%" in res.normalized_text
    assert "6000" in res.normalized_text or "6,000" in res.normalized_text


def test_ratio_colon_standardization():
    normalizer = BengaliNormalizer()
    text = "দুধ ও পানির অনুপাত ৫ ঃ ২"
    res = normalizer.normalize(text)
    assert "5 : 2" in res.normalized_text


def test_expression_extraction():
    normalizer = BengaliNormalizer()
    text = "বর্তমান মূল্য প্রতি কুইন্টাল = 720 টাকা"
    expr = normalizer.extract_expression(text, variable_aliases={"price": ["বর্তমান মূল্য প্রতি কুইন্টাল"]})
    assert expr == "price = 720"


def test_implicit_algebraic_multiplication():
    normalizer = BengaliNormalizer()
    text = "4x² − px + 9 = 0"
    res = normalizer.normalize(text)
    expr = normalizer.extract_expression(res.normalized_text)
    assert expr == "4*x**2 - px + 9 = 0"


def test_latex_math_extraction():
    normalizer = BengaliNormalizer()
    text = "Use the identity $a^{3} - b^{3} = (a - b)(a^{2} + ab + b^{2})$."
    expr = normalizer.extract_expression(text)
    assert "a**3 - b**3" in expr
    assert "(a - b)*(a**2 + ab + b**2)" in expr or "(a - b)(a**2 + ab + b**2)" in expr
