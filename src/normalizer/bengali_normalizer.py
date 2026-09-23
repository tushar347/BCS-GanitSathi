"""Bilingual Bengali-English mathematical text normalizer.

Conforms to Section 5.2 of GonitSathi Guideline:
- Reversible numeral conversion (Bengali ০-৯ to ASCII 0-9).
- Unicode mathematical operator standardization (× -> *, ÷ -> /, − -> -, etc.).
- Superscript exponent normalization (x² -> x**2, a³ -> a**3).
- Comma-separated Bengali/English number handling (৬,০০০ -> 6000).
- LaTeX math span extraction ($...$, \\(...\\)).
- Directional indicator and unit preservation (টাকা, কেজি, %, বৃদ্ধি, হ্রাস).
- Explicit alignment map (char_map) between normalized text and original text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


BN_TO_EN_DIGITS = {
    "০": "0", "১": "1", "২": "2", "৩": "3", "৪": "4",
    "৫": "5", "৬": "6", "৭": "7", "৮": "8", "৯": "9",
}

EN_TO_BN_DIGITS = {v: k for k, v in BN_TO_EN_DIGITS.items()}

SUPERSCRIPT_TO_POW = {
    "⁰": "**0", "¹": "**1", "²": "**2", "³": "**3", "⁴": "**4",
    "⁵": "**5", "⁶": "**6", "⁷": "**7", "⁸": "**8", "⁹": "**9",
}

KNOWN_UNITS = [
    "টাকা", "পয়সা", "কেজি", "গ্রাম", "কিলোগ্রাম", "লিটার", "মিলি",
    "মিটার", "কিলোমিটার", "কিমি", "সেমি", "মিনিট", "ঘণ্টা", "ঘন্টা", "সেকেন্ড",
    "দিন", "মাস", "বছর", "%", "শতাংশ", "পার্সেন্ট", "পারসেন্ট", "কুইন্টাল",
    "বর্গমিটার", "বর্গফুট", "বর্গসেমি",
]

DIRECTIONAL_TERMS = [
    "বৃদ্ধি", "বেড়ে", "বাড়লে", "হ্রাস", "কমে", "কমলে", "লাভ", "ক্ষতি",
    "লাভবান", "ক্ষতিগ্রস্ত", "বেশি", "কম",
]

OPERATOR_REPLACEMENTS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"[×✕✖]"), "*"),
    (re.compile(r"[÷]"), "/"),
    (re.compile(r"[−–—]"), "-"),
    (re.compile(r"==|সমান"), "="),
    (re.compile(r"[≤⩽]"), "<="),
    (re.compile(r"[≥⩾]"), ">="),
    (re.compile(r"[ঃ]"), ":"),  # Bengali visarga used as ratio colon
    (re.compile(r"।"), "."),    # Bengali danda
]

# Pattern for comma-separated Bengali numbers: ৬,০০০ or ১,০০,০০০
_BN_COMMA_NUM_PATTERN = re.compile(
    r"[০-৯]{1,3}(?:,[০-৯]{2,3})+"
)

# Pattern for comma-separated ASCII numbers: 6,000 or 1,00,000
_EN_COMMA_NUM_PATTERN = re.compile(
    r"\d{1,3}(?:,\d{2,3})+"
)


@dataclass
class NormalizedTextResult:
    original_text: str
    normalized_text: str
    char_map: List[int]  # For each char in normalized_text, maps index in original_text
    units_detected: List[str] = field(default_factory=list)
    directional_terms_detected: List[str] = field(default_factory=list)
    has_bengali_numerals: bool = False

    def to_bengali(self) -> str:
        """Reconstructs text with Bengali numerals where digits occur."""
        # Reverse digits back to Bengali
        text = self.normalized_text
        # If power notation was introduced, convert back to superscripts if single digit
        reverse_sup = {v: k for k, v in SUPERSCRIPT_TO_POW.items()}
        for pow_str, sup_char in reverse_sup.items():
            text = text.replace(pow_str, sup_char)
        return "".join(EN_TO_BN_DIGITS.get(ch, ch) for ch in text)


class BengaliNormalizer:
    """Normalizes Bengali math expressions reversibly into standard ASCII math representation."""

    def __init__(self) -> None:
        self.bn_digits = BN_TO_EN_DIGITS
        self.known_units = KNOWN_UNITS
        self.directional_terms = DIRECTIONAL_TERMS
        self.superscripts = SUPERSCRIPT_TO_POW

    def _strip_commas_from_number(self, text: str) -> str:
        """Remove commas from comma-separated numbers (Bengali and ASCII).

        Handles both Indian-style grouping (1,00,000) and Western-style (100,000).
        """
        # Bengali comma-separated numbers first
        def _replace_bn_comma(match: re.Match) -> str:
            return match.group(0).replace(",", "")

        text = _BN_COMMA_NUM_PATTERN.sub(_replace_bn_comma, text)

        # ASCII comma-separated numbers
        def _replace_en_comma(match: re.Match) -> str:
            return match.group(0).replace(",", "")

        text = _EN_COMMA_NUM_PATTERN.sub(_replace_en_comma, text)
        return text

    def normalize(self, text: str) -> NormalizedTextResult:
        if not text:
            return NormalizedTextResult(
                original_text="",
                normalized_text="",
                char_map=[],
            )

        original = text

        # 0. Pre-pass: strip commas from comma-separated numbers
        text = self._strip_commas_from_number(text)

        char_map: List[int] = []
        normalized_chars: List[str] = []
        has_bn_digits = False

        # 1. Pass 1: character-level normalization for digits and superscripts
        for idx, ch in enumerate(text):
            if ch in self.bn_digits:
                normalized_chars.append(self.bn_digits[ch])
                char_map.append(idx)
                has_bn_digits = True
            elif ch in self.superscripts:
                pow_replacement = self.superscripts[ch]
                normalized_chars.append(pow_replacement)
                char_map.extend([idx] * len(pow_replacement))
            else:
                normalized_chars.append(ch)
                char_map.append(idx)

        intermediate_text = "".join(normalized_chars)

        # 2. Extract detected units and directional tokens
        detected_units = [u for u in self.known_units if u in original]
        detected_directions = [d for d in self.directional_terms if d in original]

        # 3. Replace mathematical operators while keeping char_map aligned
        result_text = intermediate_text
        for pattern, replacement in OPERATOR_REPLACEMENTS:
            new_text = ""
            new_map: List[int] = []
            last_end = 0
            for match in pattern.finditer(result_text):
                start, end = match.span()
                new_text += result_text[last_end:start]
                new_map.extend(char_map[last_end:start])

                new_text += replacement
                orig_target_idx = char_map[start] if start < len(char_map) else len(original) - 1
                new_map.extend([orig_target_idx] * len(replacement))
                last_end = end

            new_text += result_text[last_end:]
            new_map.extend(char_map[last_end:])
            result_text = new_text
            char_map = new_map

        # 4. Standardize spacing around operators while preserving alignment
        # Strip trailing/leading spaces while slicing char_map
        stripped_text = result_text.strip()
        leading_ws = len(result_text) - len(result_text.lstrip())
        aligned_map = char_map[leading_ws : leading_ws + len(stripped_text)]

        final_result = NormalizedTextResult(
            original_text=original,
            normalized_text=stripped_text,
            char_map=aligned_map,
            units_detected=detected_units,
            directional_terms_detected=detected_directions,
            has_bengali_numerals=has_bn_digits,
        )
        return final_result

    def extract_latex_spans(self, text: str) -> List[str]:
        """Extract LaTeX math spans from text enclosed in $...$ or \\(...\\)."""
        spans = []
        # $...$ delimiters
        spans.extend(re.findall(r"\$(.+?)\$", text))
        # \(...\) delimiters
        spans.extend(re.findall(r"\\\((.+?)\\\)", text))
        return spans

    def extract_expression(
        self,
        text: str,
        variable_aliases: Optional[Dict[str, List[str]]] = None,
    ) -> str:
        """Extracts purely mathematical relation/equation from mixed natural language."""
        normalized = self.normalize(text).normalized_text

        # Replace variable aliases if supplied (e.g., 'বর্তমান মূল্য' -> 'current_price')
        if variable_aliases:
            for canonical, aliases in variable_aliases.items():
                for alias in aliases:
                    if alias in normalized:
                        normalized = normalized.replace(alias, canonical)

        # Extract LaTeX math expressions if enclosed in $...$ or \(...\)
        matches = self.extract_latex_spans(normalized)
        if matches:
            # Prefer a span that has an equality or inequality
            rel_spans = [m for m in matches if any(op in m for op in ["<=", ">=", "==", "=", "<", ">"])]
            if rel_spans:
                normalized = rel_spans[-1]
            else:
                normalized = matches[-1]

        # Standardize LaTeX operators and symbols
        normalized = re.sub(r"\\(?:times|cdot)", "*", normalized)
        normalized = re.sub(r"\\div", "/", normalized)
        normalized = re.sub(r"\\le(?:q)?", "<=", normalized)
        normalized = re.sub(r"\\ge(?:q)?", ">=", normalized)
        normalized = re.sub(r"\\neq", "!=", normalized)
        # \frac{a}{b} -> (a)/(b)
        normalized = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"(\1)/(\2)", normalized)
        # \sqrt{x} -> sqrt(x)
        normalized = re.sub(r"\\sqrt\{([^}]+)\}", r"sqrt(\1)", normalized)
        # \text{...} -> strip
        normalized = re.sub(r"\\text\{([^}]*)\}", r"\1", normalized)

        # Convert LaTeX powers: x^{2} -> x**2, a^3 -> a**3
        normalized = re.sub(r"\^\{?([a-zA-Z0-9_\-\+]+)\}?", r"**\1", normalized)

        # Remove formatting braces
        normalized = re.sub(r"[\{\}]", "", normalized)

        # Standardize colon as equality if used as an equation assignment
        if ":" in normalized and "=" not in normalized:
            # Only replace if not preceded or followed by numbers (i.e. not a ratio like 5:18)
            normalized = re.sub(r"(?<!\d)\s*:\s*(?!\d)", " = ", normalized)

        # Remove known Bengali units for mathematical parsing
        expr = normalized
        for unit in self.known_units:
            expr = expr.replace(unit, " ")

        # Insert multiplication for implicit algebraic multiplication:
        # e.g. 3ab -> 3*a*b, 4x -> 4*x
        expr = re.sub(r"(\d)([a-zA-Z])", r"\1*\2", expr)
        # e.g. 3(a+b) -> 3*(a+b)
        expr = re.sub(r"(\d)(\s*\()", r"\1*\2", expr)
        # e.g. (x+3)(x-3) -> (x+3)*(x-3)
        expr = re.sub(r"\)(\s*\()", r")*\1", expr)
        # e.g. (a-b)a -> (a-b)*a or a(b+c) -> a*(b+c)
        expr = re.sub(r"([a-zA-Z])(\s*\()", r"\1*\2", expr)
        expr = re.sub(r"\)(\s*[a-zA-Z])", r")*\1", expr)

        # Remove trailing periods, commas, or semicolons resulting from Bengali sentence punctuation
        expr = re.sub(r"[\.,;।\s]+$", "", expr).strip()

        # If there is a relational sign, format cleanly
        for rel in ["<=", ">=", "==", "<", ">", "="]:
            if rel in expr:
                parts = expr.split(rel, 1)
                lhs, rhs = parts[0].strip(), parts[1].strip()
                # If LHS has no math operators and has spaces (e.g. 'বর্তমান মূল্য'), convert to identifier
                if not re.search(r"[\+\-\*/\^<>=]", lhs):
                    lhs = re.sub(r"\s+", "_", lhs)
                norm_rel = "=" if rel == "==" else rel
                expr = f"{lhs} {norm_rel} {rhs}"
                break

        return expr.strip()
