"""Extended normalizer tests for LaTeX, commas, superscripts, and directional terms.

Tests Update 2 normalizer enhancements.
"""

import pytest
from src.normalizer.bengali_normalizer import BengaliNormalizer


@pytest.fixture
def normalizer():
    return BengaliNormalizer()


# ---------- Comma-separated number tests ----------

class TestCommaSeparatedNumbers:
    def test_bengali_comma_number(self, normalizer):
        """৬,০০০ -> 6000"""
        text = "৬,০০০ টাকায়"
        res = normalizer.normalize(text)
        assert "6000" in res.normalized_text
        assert "," not in res.normalized_text.split("টাকায়")[0]

    def test_bengali_lakh_format(self, normalizer):
        """১,০০,০০০ -> 100000 (Indian lakh grouping)"""
        text = "মোট ১,০০,০০০ টাকা"
        res = normalizer.normalize(text)
        assert "100000" in res.normalized_text

    def test_english_comma_number(self, normalizer):
        """6,000 -> 6000"""
        text = "Total is 6,000 taka"
        res = normalizer.normalize(text)
        assert "6000" in res.normalized_text

    def test_english_million_format(self, normalizer):
        """1,000,000 -> 1000000"""
        text = "Amount: 1,000,000"
        res = normalizer.normalize(text)
        assert "1000000" in res.normalized_text

    def test_comma_in_non_number_preserved(self, normalizer):
        """Commas in non-numeric contexts should be preserved."""
        text = "Hello, World"
        res = normalizer.normalize(text)
        assert "," in res.normalized_text


# ---------- Superscript tests ----------

class TestSuperscriptNormalization:
    def test_square_superscript(self, normalizer):
        """x² -> x**2"""
        text = "x² + y²"
        res = normalizer.normalize(text)
        assert "x**2" in res.normalized_text
        assert "y**2" in res.normalized_text

    def test_cube_superscript(self, normalizer):
        """a³ -> a**3"""
        text = "a³ = 27"
        res = normalizer.normalize(text)
        assert "a**3" in res.normalized_text

    def test_superscript_reversibility(self, normalizer):
        """Superscript -> power -> back to superscript."""
        text = "x²"
        res = normalizer.normalize(text)
        assert "x**2" in res.normalized_text
        reconstructed = res.to_bengali()
        assert "x²" in reconstructed


# ---------- Directional term tests ----------

class TestDirectionalTermDetection:
    def test_increase_detected(self, normalizer):
        text = "চালের মূল্য ২৫% বৃদ্ধি পেলে"
        res = normalizer.normalize(text)
        assert "বৃদ্ধি" in res.directional_terms_detected

    def test_decrease_detected(self, normalizer):
        text = "মূল্য ১২% কমে যাওয়ায়"
        res = normalizer.normalize(text)
        assert "কমে" in res.directional_terms_detected

    def test_profit_loss_detected(self, normalizer):
        text = "লাভ ২০% এবং ক্ষতি ১০%"
        res = normalizer.normalize(text)
        assert "লাভ" in res.directional_terms_detected
        assert "ক্ষতি" in res.directional_terms_detected


# ---------- LaTeX math span tests ----------

class TestLaTeXExtraction:
    def test_dollar_delimited_latex(self, normalizer):
        """Extract LaTeX from $...$ delimiters."""
        text = "The answer is $x = 720$ taka"
        spans = normalizer.extract_latex_spans(text)
        assert len(spans) == 1
        assert "x = 720" in spans[0]

    def test_paren_delimited_latex(self, normalizer):
        """Extract LaTeX from \\(...\\) delimiters."""
        text = "Perimeter \\(= 2(48 + 16) = 128\\) metres"
        spans = normalizer.extract_latex_spans(text)
        assert len(spans) == 1

    def test_multiple_latex_spans(self, normalizer):
        text = "We have $a = 5$ and $b = 10$"
        spans = normalizer.extract_latex_spans(text)
        assert len(spans) == 2

    def test_extract_expression_with_latex(self, normalizer):
        """extract_expression should pick relational LaTeX spans."""
        text = "Therefore $720/x = 1$, so $x = 720$ taka"
        expr = normalizer.extract_expression(text)
        assert "=" in expr
        # Should contain the numeric answer
        assert "720" in expr

    def test_latex_frac_conversion(self, normalizer):
        """\\frac{a}{b} should convert to (a)/(b)."""
        text = "$\\frac{6000}{x}$"
        expr = normalizer.extract_expression(text)
        assert "6000" in expr
        assert "/" in expr

    def test_latex_times_conversion(self, normalizer):
        """\\times should convert to *."""
        text = "$2 \\times 64 = 128$"
        expr = normalizer.extract_expression(text)
        assert "*" in expr
        assert "128" in expr

    def test_latex_div_conversion(self, normalizer):
        """\\div should convert to /."""
        text = "$6000 \\div 720 = 8.333$"
        expr = normalizer.extract_expression(text)
        assert "/" in expr

    def test_latex_power_conversion(self, normalizer):
        """x^{2} should convert to x**2."""
        text = "$x^{2} + y^{3} = 25$"
        expr = normalizer.extract_expression(text)
        assert "**2" in expr
        assert "**3" in expr


# ---------- Unit detection tests ----------

class TestExtendedUnitDetection:
    def test_quintal_unit(self, normalizer):
        text = "১ কুইন্টাল চাল"
        res = normalizer.normalize(text)
        assert "কুইন্টাল" in res.units_detected

    def test_square_meter(self, normalizer):
        text = "ক্ষেত্রফল ১০০ বর্গমিটার"
        res = normalizer.normalize(text)
        assert "বর্গমিটার" in res.units_detected


# ---------- Implicit multiplication tests ----------

class TestImplicitMultiplication:
    def test_digit_variable(self, normalizer):
        """3x -> 3*x."""
        text = "3x + 5"
        expr = normalizer.extract_expression(text)
        assert "3*x" in expr

    def test_digit_parenthesis(self, normalizer):
        """3(a+b) -> 3*(a+b)."""
        text = "3(a + b)"
        expr = normalizer.extract_expression(text)
        assert "3*" in expr

    def test_adjacent_parentheses(self, normalizer):
        """(x+1)(x-1) -> (x+1)*(x-1)."""
        text = "(x + 1)(x - 1)"
        expr = normalizer.extract_expression(text)
        assert ")*(" in expr or ")* (" in expr


# ---------- Operator normalization tests ----------

class TestExtendedOperatorNormalization:
    def test_en_dash_as_minus(self, normalizer):
        """– (en-dash) should be normalized to -."""
        text = "100 – 25"
        res = normalizer.normalize(text)
        assert "100 - 25" in res.normalized_text

    def test_em_dash_as_minus(self, normalizer):
        """— (em-dash) should be normalized to -."""
        text = "200 — 50"
        res = normalizer.normalize(text)
        assert "200 - 50" in res.normalized_text

    def test_bengali_visarga_as_colon(self, normalizer):
        """ঃ should be normalized to : (for ratios)."""
        text = "5ঃ18"
        res = normalizer.normalize(text)
        assert "5:18" in res.normalized_text
