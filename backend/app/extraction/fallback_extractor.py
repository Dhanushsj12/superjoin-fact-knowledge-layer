"""
Generic rule-based fallback fact extractor.

Purpose:
- Extract numerical/semantic facts when an LLM is unavailable.
- Work across arbitrary PDFs without document-specific rules.
- Prefer metric/value relationships that are close together.
- Avoid obvious page numbers, note references, and headings.
- Handle common financial-table row patterns.
"""

import re
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Generic patterns
# ---------------------------------------------------------------------------

NUMBER_PATTERN = r"""
    (?<![\w.])
    -?
    (?:
        \d{1,3}(?:,\d{3})+(?:\.\d+)?
        |
        \d+(?:\.\d+)?
    )
    (?![\w.])
"""

NUMBER_RE = re.compile(NUMBER_PATTERN, re.VERBOSE)

PERCENT_RE = re.compile(
    rf"({NUMBER_PATTERN})\s*%",
    re.VERBOSE | re.IGNORECASE,
)

PERCENT_WORD_RE = re.compile(
    rf"({NUMBER_PATTERN})\s*(?:percent|percentage)",
    re.VERBOSE | re.IGNORECASE,
)

CURRENCY_RE = re.compile(
    rf"""
    (?P<prefix>
        ₹ | Rs\.? | INR | US\$ | USD | \$ | € | EUR | £ | GBP
    )
    \s*
    (?P<number>
        {NUMBER_PATTERN}
    )
    \s*
    (?P<magnitude>
        trillion | billion | million | thousand |
        crore | crores | lakh | lakhs |
        tn | bn | mn | k | t | b | m
    )?
    """,
    re.VERBOSE | re.IGNORECASE,
)



NUMBER_UNIT_RE = re.compile(
    rf"""
    ({NUMBER_PATTERN})
    \s*
    (
        million\s+shipments?/day
        |million\s+orders?/day
        |million\s+packages?/day
        |million\s+parcels?/day
        |million\s+bags?/day
        |million\s+units?/day
        |million\s+shipments?/month
        |million\s+orders?/month
        |million\s+packages?/month
        |million\s+units?/month

        |shipments?/day
        |orders?/day
        |packages?/day
        |parcels?/day
        |bags?/day
        |units?/day
        |shipments?/month
        |orders?/month
        |packages?/month
        |units?/month

        |trillion |billion |million |thousand
        |mn |bn |tn
        |crore |crores |lakh |lakhs
        |k |m |b |t

        |tonnes? |tons? |kg |kgs |g |grams?
        |kw |mw |gw
        |km |kms |miles?
        |hours? |days? |months? |years?

        |employees? |customers? |users? |vehicles?
        |locations? |stores? |facilities?
    )
    \b
    """,
    re.VERBOSE | re.IGNORECASE,
)




# ---------------------------------------------------------------------------
# Generic metric vocabulary
# ---------------------------------------------------------------------------

METRIC_KEYWORDS = {
    "revenue": [
        "revenue",
        "revenues",
        "income from operations",
        "revenue from contract with customers",
    ],
    "profit": [
        "profit",
        "profits",
        "net profit",
        "profit after tax",
        "profit before tax",
    ],
    "loss": [
        "loss",
        "losses",
        "net loss",
        "loss before tax",
        "loss after tax",
    ],
    "growth": [
        "growth rate",
        "growth of",
        "grew by",
        "grown by",
        "growth percentage",
        "growth %",
    ],
    "employees": [
        "employees",
        "employee count",
        "number of employees",
        "workforce",
        "headcount",
    ],
    "customers": [
        "customers",
        "customer base",
        "number of customers",
        "users",
        "user base",
    ],
    "production": [
        "production",
        "production volume",
        "output",
    ],
    "volume": [
        "volume",
        "shipment volume",
        "sales volume",
        "transaction volume",
    ],
    "market share": [
        "market share",
        "share of the market",
    ],
    "assets": [
        "assets",
        "total assets",
        "non-current assets",
        "current assets",
    ],
    "debt": [
        "debt",
        "total debt",
        "borrowings",
        "total borrowings",
        "indebtedness",
    ],
    "investment": [
        "investment",
        "investments",
        "capital investment",
        "investment in equity",
        "deemed investment",
    ],
    "capacity": [
        "capacity",
        "installed capacity",
        "production capacity",
    ],
    "gdp": [
        "gdp",
        "gross domestic product",
    ],
    "inflation": [
        "inflation rate",
        "inflation",
    ],
    "exports": [
        "exports",
        "export value",
        "export volume",
    ],
    "imports": [
        "imports",
        "import value",
        "import volume",
    ],
    "direct spend": [
        "direct spend",
        "direct spending",
        "spend",
        "spending",
    ],
}


COUNT_METRICS = {
    "employees",
    "customers",
}

MONETARY_METRICS = {
    "revenue",
    "profit",
    "loss",
    "debt",
    "investment",
    "assets",
    "direct spend",
}

PERCENT_METRICS = {
    "growth",
    "inflation",
    "market share",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_number(value: str) -> float:
    """Convert common formatted numbers to float."""
    value = value.replace(",", "").strip()

    try:
        return float(value)
    except ValueError:
        return 0.0


def _format_value(value: float):
    """Return int when the number is mathematically integral."""
    if value.is_integer():
        return int(value)

    return value


def _is_year(value: float) -> bool:
    """Identify likely year values."""
    return 1900 <= value <= 2100 and value.is_integer()


def _looks_like_page_number(text: str, match: re.Match) -> bool:
    """
    Detect numbers that are probably page numbers.

    Examples:
        '92 RESTATED SUMMARY...'
        '510 FINANCIAL INDEBTEDNESS...'
    """
    before = text[:match.start()].rstrip()
    after = text[match.end():].lstrip()

    number = _clean_number(match.group(0))

    if not _is_year(number) and number > 0:
        first_words = after[:80]

        # Page-number-like pattern:
        # 92 RESTATED SUMMARY...
        # 510 FINANCIAL...
        if (
            len(before) < 20
            and re.match(r"^[A-Z][A-Z\s\-/&]{4,}", first_words)
        ):
            return True

    return False


def _looks_like_note_reference(text: str, match: re.Match) -> bool:
    """Reject numbers used as note references."""
    before = text[max(0, match.start() - 20):match.start()].lower()

    return bool(
        re.search(
            r"(note|notes|page|pages|refer|reference|item)\s*$",
            before,
        )
    )


def _looks_like_date_component(text: str, match: re.Match) -> bool:
    """Reject numbers that are clearly part of a written date."""
    before = text[max(0, match.start() - 30):match.start()]
    after = text[match.end():match.end() + 30]

    month_pattern = (
        r"(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December|Jan|Feb|Mar|Apr|May|"
        r"Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
    )

    number = re.escape(match.group(0))
    context = before + match.group(0) + after

    return bool(
        re.search(
            rf"\b{month_pattern}\s+{number}\s*,?\s*20\d{{2}}\b",
            context,
            re.IGNORECASE,
        )
        or re.search(
            rf"\b{number}\s*,?\s*20\d{{2}}\b",
            context,
            re.IGNORECASE,
        )
        or re.search(
            rf"\b(?:as of|as at|ended|year ended|period ended)\s+"
            rf"{month_pattern}\s+{number}\b",
            before + match.group(0),
            re.IGNORECASE,
        )
    )


def _looks_like_footnote_marker(text: str, match: re.Match) -> bool:
    """Reject numbers used as parenthesized footnote markers such as (1)."""
    before = text[max(0, match.start() - 3):match.start()]
    after = text[match.end():match.end() + 3]

    return bool(
        re.search(r"\(\s*$", before)
        and re.match(r"^\s*\)", after)
    )


def _looks_like_heading(text: str) -> bool:
    """Detect likely section headings."""
    stripped = text.strip()

    if not stripped:
        return True

    # Very short text is usually not a useful fact sentence.
    if len(stripped) < 25:
        alpha = re.sub(r"[^A-Za-z]", "", stripped)

        if alpha and alpha.isupper():
            return True

    # Heading-like uppercase text.
    alpha_chars = [c for c in stripped if c.isalpha()]

    if alpha_chars:
        uppercase_ratio = sum(
            1 for c in alpha_chars if c.isupper()
        ) / len(alpha_chars)

        if uppercase_ratio > 0.90 and len(stripped) < 180:
            return True

    return False


def _split_sentences(text: str) -> List[str]:
    """
    Split text into reasonably useful sentence/table fragments.
    """
    parts = re.split(
        r"(?<=[.!?])\s+|\n+",
        text,
    )

    return [
        part.strip()
        for part in parts
        if part.strip()
    ]


def _looks_like_section_reference(text: str, match_position: int) -> bool:
    """Reject legal/accounting section numbers such as section 135(5)."""
    before = text[max(0, match_position - 25):match_position].lower()
    after = text[match_position:match_position + 12].lower()

    if re.search(r"\bsection\s*$|\bsections\s*$|\bsec\.\s*$", before):
        if re.match(r"\d+\s*\(", after):
            return True

    return False


def _looks_like_accounting_standard_reference(text: str, match_position: int) -> bool:
    """Reject accounting-standard references such as Ind AS 109."""
    before = text[max(0, match_position - 20):match_position].lower()

    return bool(
        re.search(
            r"\bind\s+as\s*$|\bindian\s+accounting\s+standard\s*$",
            before,
        )
    )


def _looks_like_level_reference(text: str, match_position: int) -> bool:
    """Reject values that are merely accounting hierarchy levels (Level 1/2/3)."""
    before = text[max(0, match_position - 12):match_position].lower()

    return bool(re.search(r"\blevel\s*$", before))


def _looks_like_footnote_or_url_reference(text: str, match_position: int) -> bool:
    """Reject numeric fragments that are clearly citation/URL references."""
    before = text[max(0, match_position - 45):match_position].lower()
    after = text[match_position:match_position + 45].lower()

    if re.search(r"https?://|www\.", before):
        return True

    if re.search(r"\bdoi\s*$|\bref(?:erence)?\s*$|\bfootnote\s*$", before):
        return True

    if re.search(r"\.com/\w*|\.\w{2,6}/\w*", after):
        return True

    return False


def _metric_is_negated_or_contextual(metric: str, sentence: str, position: int) -> bool:
    """
    Reject generic keyword matches when the keyword is being used
    as part of a different concept.

    This remains document-independent.
    """
    lowered = sentence.lower()

    if metric == "customers":
        # "revenue from contract(s) with customers" describes revenue,
        # not a customer count.
        if re.search(
            r"\brevenue\s+from\s+(?:contract|contracts)\s+with\s+customers\b",
            lowered,
        ):
            return True

        # "customers" inside phrases describing revenue/value should not
        # automatically create a customer-count fact.
        left = lowered[max(0, position - 80):position]
        if re.search(
            r"\b(?:revenue|income|sales|amount|value)\b.{0,45}\bcustomers?\b",
            left,
        ):
            return True

    if metric == "investment":
        # "investments in scope of Ind AS 109" is a standard/reference,
        # not an investment amount.
        if re.search(
            r"\bind\s+as\s+\d+",
            lowered,
        ):
            return True

        # Maturity/tenure references such as "more than 3 months" are
        # time information, not investment values.
        if re.search(
            r"\b(?:maturity|matures|tenure|period)\b.{0,35}\b\d+\s*"
            r"(?:days?|months?|years?)\b",
            lowered,
        ):
            return True

    if metric == "assets":
        # "Level 1/2/3" is an accounting classification, not asset value.
        if re.search(r"\blevel\s+[123]\b", lowered):
            return True

    if metric in {"profit", "loss"}:
        # EPS / loss-per-share text should not become a profit/loss amount.
        if re.search(
            r"\b(?:profit|loss)\s+per\s+(?:equity\s+)?share\b",
            lowered,
        ):
            return True

    if metric == "gdp":
        # GDP references embedded in citations/URLs are not GDP values.
        if re.search(r"https?://|www\.|imf\.", lowered):
            return True

    if metric == "direct spend":
        # The generic word "spends" is too broad when it refers to a
        # percentage of spending rather than a monetary spend amount.
        if re.search(
            r"\b\d+(?:\.\d+)?\s*%\s+of\s+the\s+(?:company'?s\s+)?spend",
            lowered,
        ):
            return True

    return False


def _find_metric(sentence: str) -> Optional[Tuple[str, int, int]]:
    """
    Find the best metric in a sentence.

    Selection is generic:
    - specific multi-word phrases are preferred;
    - contextual false positives are rejected;
    - among remaining candidates, prefer the strongest phrase;
    - if several candidates have the same strength, prefer the earliest one.
    """
    lowered = sentence.lower()

    candidates = []

    for metric, keywords in METRIC_KEYWORDS.items():
        for keyword in keywords:
            keyword_lower = keyword.lower()
            position = lowered.find(keyword_lower)

            if position < 0:
                continue

            # Avoid matching a keyword in the middle of a larger word.
            before = lowered[position - 1] if position > 0 else " "
            after_pos = position + len(keyword_lower)
            after = lowered[after_pos] if after_pos < len(lowered) else " "

            if before.isalnum() or after.isalnum():
                continue

            if _metric_is_negated_or_contextual(
                metric,
                sentence,
                position,
            ):
                continue

            candidates.append(
                (
                    len(keyword),
                    position,
                    metric,
                    keyword,
                )
            )

    if not candidates:
        return None

    # Prefer longer/more-specific keywords, then earlier occurrence.
    candidates.sort(
        key=lambda item: (-item[0], item[1])
    )

    _, position, metric, keyword = candidates[0]

    return (
        metric,
        position,
        position + len(keyword),
    )


def _find_metric_position(
    sentence: str,
    metric: str,
) -> int:
    lowered = sentence.lower()

    positions = [
        lowered.find(keyword.lower())
        for keyword in METRIC_KEYWORDS.get(metric, [metric])
    ]

    positions = [
        position
        for position in positions
        if position >= 0
    ]

    return min(positions) if positions else -1


def _find_period(
    text: str,
    metric_position: int = 0,
) -> Optional[str]:
    """
    Extract a nearby year/date/period.
    """
    patterns = [
        r"\b(?:fiscal year|financial year|FY)\s*(\d{4})\b",
        r"\b(?:year ended|year ending)\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})\b",
        r"\b(?:year ended|year ending)\s+([A-Za-z]+\s+\d{4})\b",
        r"\b(?:as at|as of|ended)\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})\b",
        r"\b(20\d{2})\b",
    ]

    nearby_start = max(0, metric_position - 180)
    nearby_end = min(len(text), metric_position + 220)

    nearby = text[nearby_start:nearby_end]

    for pattern in patterns:
        match = re.search(
            pattern,
            nearby,
            re.IGNORECASE,
        )

        if match:
            return match.group(1)

    return None


def _find_scope(text: str) -> Optional[str]:
    lowered = text.lower()

    if "consolidated" in lowered:
        return "consolidated"

    if "standalone" in lowered:
        return "standalone"

    if "domestic" in lowered:
        return "domestic"

    if "international" in lowered:
        return "international"

    return None


def _extract_entity(text: str) -> Optional[str]:
    """
    Conservative generic entity extraction.

    Prefer legal/company-style names rather than arbitrary capitalized
    phrases from tables.
    """
    patterns = [
        r"\b([A-Z][A-Za-z0-9&.,' -]{2,80}\b(?:Limited|Ltd\.?|LLC|Inc\.?|Corp\.?|Corporation|Private Limited|Pte\. Ltd\.?|PLC))\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            entity = " ".join(match.group(1).split())

            if len(entity) <= 100:
                return entity

    return None


# ---------------------------------------------------------------------------
# Numeric extraction
# ---------------------------------------------------------------------------

def _extract_percentage(
    text: str,
    metric_position: int = 0,
) -> Optional[Tuple[float, str]]:
    candidates = []

    for regex in (PERCENT_RE, PERCENT_WORD_RE):
        for match in regex.finditer(text):
            number = _clean_number(match.group(1))

            distance = abs(
                match.start() - metric_position
            )

            candidates.append(
                (
                    distance,
                    number,
                    "%",
                )
            )

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0])

    _, value, unit = candidates[0]

    return _format_value(value), unit


def _extract_currency(
    text: str,
    metric_position: int = 0,
) -> Optional[Tuple[float, str]]:
    """
    Extract a monetary value while preserving an optional magnitude.

    Examples:
        $1 billion              -> (1, "$ billion")
        US$3.9 trillion         -> (3.9, "$ trillion")
        ₹16,538.97 million      -> (16538.97, "₹ million")
        Rs 46 Cr                -> (46, "₹ crore")
        $500                    -> (500, "$")
    """

    candidates = []

    for match in CURRENCY_RE.finditer(text):
        raw_number = match.group("number")
        if raw_number is None:
            continue

        value = _clean_number(raw_number)
        if _is_year(value):
            continue

        prefix = match.group("prefix").strip().lower()
        magnitude = match.group("magnitude")

        if prefix.startswith(("₹", "rs", "inr")):
            currency = "₹"
        elif prefix.startswith(("us$", "$", "usd")):
            currency = "$"
        elif prefix.startswith(("€", "eur")):
            currency = "€"
        elif prefix.startswith(("£", "gbp")):
            currency = "£"
        else:
            currency = prefix

        unit = (
            f"{currency} {magnitude.lower()}"
            if magnitude
            else currency
        )

        distance = abs(match.start() - metric_position)
        candidates.append((distance, value, unit))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0])
    _, value, unit = candidates[0]

    return _format_value(value), unit



def _extract_number_with_unit(
    text: str,
    metric_position: int = 0,
) -> Optional[Tuple[float, str]]:
    """
    Extract a number followed by a semantic unit.

    Compound units such as "million shipments/day" are preserved.
    """

    candidates = []

    for match in NUMBER_UNIT_RE.finditer(text):
        raw_number = match.group(1)
        raw_unit = match.group(2)

        value = _clean_number(raw_number)
        unit = " ".join(raw_unit.lower().split())

        distance = abs(match.start() - metric_position)

        candidates.append(
            (
                distance,
                value,
                unit,
            )
        )

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0])
    _, value, unit = candidates[0]

    return _format_value(value), unit



def _extract_plain_number(
    text: str,
    metric_position: int = 0,
) -> Optional[Tuple[float, None]]:
    candidates = []

    for match in NUMBER_RE.finditer(text):
        number = _clean_number(match.group(0))

        if _is_year(number):
            continue

        if _looks_like_page_number(text, match):
            continue

        if _looks_like_note_reference(text, match):
            continue

        if _looks_like_date_component(text, match):
            continue

        if _looks_like_footnote_marker(text, match):
            continue

        if _looks_like_section_reference(text, match.start()):
            continue

        if _looks_like_accounting_standard_reference(
            text,
            match.start(),
        ):
            continue

        if _looks_like_level_reference(text, match.start()):
            continue

        if _looks_like_footnote_or_url_reference(
            text,
            match.start(),
        ):
            continue

        distance = abs(
            match.start() - metric_position
        )

        candidates.append(
            (
                distance,
                number,
            )
        )

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0])

    _, value = candidates[0]

    return _format_value(value), None


def _extract_value_and_unit(
    text: str,
    metric_position: int,
) -> Optional[Tuple[float, Optional[str]]]:
    """
    Extract the numeric value closest to the metric.

    Priority:
        1. percentage
        2. currency + optional magnitude
        3. number + semantic unit
        4. plain number
    """

    percentage = _extract_percentage(text, metric_position)
    if percentage:
        return percentage

    currency = _extract_currency(text, metric_position)
    if currency:
        return currency

    number_unit = _extract_number_with_unit(text, metric_position)
    if number_unit:
        return number_unit

    return _extract_plain_number(text, metric_position)




# ---------------------------------------------------------------------------
# Metric/value validation
# ---------------------------------------------------------------------------

def _is_metric_value_compatible(
    metric: str,
    value: float,
    unit: Optional[str],
    text: str,
) -> bool:
    """
    Generic semantic compatibility checks.

    The fallback prefers rejecting an ambiguous candidate over
    manufacturing a misleading fact.
    """

    lowered = text.lower()

    unit_normalized = (
        unit.strip().lower()
        if isinstance(unit, str)
        else ""
    )

    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return False

    if _is_year(numeric_value):
        return False

    currency_units = {"₹", "$", "€", "£", "inr", "usd", "eur", "gbp"}
    percentage_units = {"%", "percent", "percentage", "pct"}

    physical_units = {
        "tonne", "tonnes", "ton", "tons",
        "kg", "kgs", "g", "grams",
        "km", "kms", "mile", "miles",
        "kw", "mw", "gw",
    }

    time_units = {
        "second", "seconds",
        "minute", "minutes",
        "hour", "hours",
        "day", "days",
        "month", "months",
        "year", "years",
    }

    rate_units = {"bps", "basis points"}

    magnitude_units = {
        "k", "thousand",
        "m", "mn", "million",
        "b", "bn", "billion",
        "t", "tn", "trillion",
        "lakh", "lakhs",
        "crore", "crores",
    }

    throughput_unit = (
        "/" in unit_normalized
        and any(
            token in unit_normalized
            for token in ["day", "month", "year", "hour", "minute"]
        )
    )

    # ---------------------------------------------------------------
    # Count metrics
    # ---------------------------------------------------------------

    if metric in COUNT_METRICS:
        if unit_normalized in percentage_units:
            return False

        if unit_normalized in currency_units:
            return False

        if unit_normalized in physical_units:
            return False

        if unit_normalized in time_units:
            return False

        if unit_normalized in rate_units:
            return False

        if throughput_unit:
            return False

        monetary_words = [
            "revenue", "salary", "remuneration",
            "payment", "expense", "spend", "spending",
        ]

        count_words = [
            "employees", "employee count",
            "workforce", "headcount",
            "customers", "customer base",
            "users", "user base",
            "number of customers",
            "number of employees",
        ]

        if any(word in lowered for word in monetary_words):
            if not any(word in lowered for word in count_words):
                return False

    # ---------------------------------------------------------------
    # Percentage metrics
    # ---------------------------------------------------------------

    if metric in PERCENT_METRICS:
        if unit_normalized not in percentage_units:
            if unit_normalized in rate_units:
                if not re.search(
                    r"\b(?:rate|margin|growth|change|increase|decrease)\b",
                    lowered,
                ):
                    return False
            elif not re.search(
                r"\b(?:percent|percentage|rate|margin)\b|%",
                lowered,
            ):
                return False

    # ---------------------------------------------------------------
    # Monetary metrics
    # ---------------------------------------------------------------

    if metric in MONETARY_METRICS:
        if unit_normalized in percentage_units:
            return False

        if unit_normalized in rate_units:
            return False

        if unit_normalized in physical_units:
            return False

        if unit_normalized in time_units:
            return False

        if throughput_unit:
            return False

        # Explicit currency, including "$ billion"/"₹ million".
        if unit_normalized in currency_units:
            return True

        if any(
            unit_normalized.endswith(f" {magnitude}")
            for magnitude in magnitude_units
        ):
            if any(
                currency in unit_normalized
                for currency in currency_units
            ):
                return True

        if unit_normalized in magnitude_units:
            monetary_words = [
                "revenue", "income", "profit", "loss",
                "debt", "borrowings", "investment",
                "spend", "spending", "assets",
                "cost", "value", "amount",
                "usd", "inr", "rs.", "rupees",
            ]

            if not any(word in lowered for word in monetary_words):
                return False

        if not unit_normalized:
            monetary_words = [
                "revenue", "income", "profit", "loss",
                "debt", "borrowings", "investment",
                "spend", "spending", "assets",
                "cost", "amount", "value",
            ]

            if not any(word in lowered for word in monetary_words):
                return False

    # ---------------------------------------------------------------
    # Capacity
    # ---------------------------------------------------------------

    if metric == "capacity":
        explicit_count_units = {
            "employees", "employee",
            "customers", "customer",
            "users", "user",
            "vehicles", "vehicle",
            "locations", "location",
            "stores", "store",
            "facilities", "facility",
            "vendors", "vendor",
            "partners", "partner",
        }

        if unit_normalized in explicit_count_units:
            return False

        if throughput_unit:
            return True

        if unit_normalized in {
            "kw", "mw", "gw",
            "kg", "kgs", "g", "grams",
            "tonne", "tonnes", "ton", "tons",
        }:
            return True

        if unit_normalized in magnitude_units:
            if not re.search(
                r"\b(?:capacity|installed capacity|production capacity|"
                r"processing capacity|sort capacity|rated capacity|"
                r"sanctioned capacity)\b",
                lowered,
            ):
                return False

        if re.search(
            r"\b(?:locations?|stores?|facilities|centres?|centers?|"
            r"vehicles?|vendors?|partners?)\b",
            lowered,
        ):
            if re.search(
                r"\b\d[\d,.]*\s+(?:additional\s+)?"
                r"(?:locations?|stores?|facilities|centres?|centers?|"
                r"vehicles?|vendors?|partners?)\b",
                lowered,
            ):
                return False

        if not unit_normalized:
            if not re.search(r"\b(?:capacity|capacities)\b", lowered):
                return False

        return True

    # ---------------------------------------------------------------
    # GDP
    # ---------------------------------------------------------------

    if metric == "gdp":
        if re.search(
            r"https?://|www\.|\bdoi\b|\bref(?:erence)?\b",
            lowered,
        ):
            return False

        if re.search(
            r"\b(?:section|note|page|figure|table)\s+\d+",
            lowered,
        ):
            return False

    # ---------------------------------------------------------------
    # Basis points sanity
    # ---------------------------------------------------------------

    if unit_normalized in rate_units:
        if metric not in {"growth", "inflation"}:
            if not re.search(
                r"\b(?:rate|margin|growth|change|increase|decrease)\b",
                lowered,
            ):
                return False

    return True




# ---------------------------------------------------------------------------
# Financial table extraction
# ---------------------------------------------------------------------------

FINANCIAL_ROW_PATTERNS = [
    "revenue",
    "total revenue",
    "income",
    "total income",
    "profit",
    "net profit",
    "loss",
    "net loss",
    "total assets",
    "assets",
    "borrowings",
    "total borrowings",
    "debt",
    "investments",
    "investment",
    "market share",
    "employees",
    "employee count",
    "customers",
    "capacity",
]


def _extract_table_row_fact(
    fragment: str,
    source_document: str,
    page_number: int,
    chunk_id: int,
) -> Optional[Dict]:
    """
    Extract a fact when the fragment resembles:

        Revenue 48,105.30 ...

    or:

        Total borrowings 3,707.81 ...
    """
    lowered = fragment.lower()

    for row_label in sorted(
        FINANCIAL_ROW_PATTERNS,
        key=len,
        reverse=True,
    ):
        pattern = re.compile(
            rf"\b{re.escape(row_label)}\b"
            rf"\s*[:\-]?\s*"
            rf"({NUMBER_PATTERN})"
            rf"(?:\s*(million|billion|mn|bn|crore|lakh|k|m|b))?",
            re.IGNORECASE | re.VERBOSE,
        )

        match = pattern.search(fragment)

        if not match:
            continue

        raw_value = match.group(1)
        raw_unit = match.group(2)

        value = _clean_number(raw_value)

        if _is_year(value):
            continue

        unit = raw_unit.lower() if raw_unit else None

        metric = None

        if "revenue" in row_label:
            metric = "revenue"

        elif "income" in row_label:
            metric = "revenue"

        elif "profit" in row_label:
            metric = "profit"

        elif "loss" in row_label:
            metric = "loss"

        elif "borrow" in row_label or "debt" in row_label:
            metric = "debt"

        elif "asset" in row_label:
            metric = "assets"

        elif "investment" in row_label:
            metric = "investment"

        elif "employee" in row_label:
            metric = "employees"

        elif "customer" in row_label:
            metric = "customers"

        elif "market share" in row_label:
            metric = "market share"

        if metric is None:
            continue

        if not _is_metric_value_compatible(
            metric,
            value,
            unit,
            fragment,
        ):
            continue

        period = _find_period(
            fragment,
            match.start(),
        )

        scope = _find_scope(fragment)

        return {
            "chunk_id": chunk_id,
            "entity": _extract_entity(fragment),
            "metric": metric,
            "value": _format_value(value),
            "unit": unit,
            "period": period,
            "scope": scope,
            "evidence": fragment,
            "page_number": page_number,
            "source_document": source_document,
        }

    return None


# ---------------------------------------------------------------------------
# Main fallback extractor
# ---------------------------------------------------------------------------

def extract_facts_fallback(
    chunks: List[Dict],
) -> List[Dict]:
    """
    Extract generic facts from candidate chunks.

    Expected chunk structure:

        {
            "chunk_id": int,
            "page_number": int,
            "chunk_text": str,
            "source_document": str
        }
    """

    facts: List[Dict] = []

    for index, chunk in enumerate(chunks):
        text = chunk.get("chunk_text", "").strip()

        if not text:
            continue

        page_number = int(
            chunk.get("page_number", 0)
        )

        source_document = chunk.get(
            "source_document",
            "",
        )

        chunk_id = chunk.get(
            "chunk_id",
            index + 1,
        )

        # ---------------------------------------------------------------
        # First try sentence/table fragments.
        # ---------------------------------------------------------------

        fragments = _split_sentences(text)

        for fragment in fragments:
            if len(fragment) < 20:
                continue

            if _looks_like_heading(fragment):
                continue

            # -----------------------------------------------------------
            # Financial/table row extraction gets first priority.
            # -----------------------------------------------------------

            table_fact = _extract_table_row_fact(
                fragment,
                source_document,
                page_number,
                chunk_id,
            )

            if table_fact:
                facts.append(table_fact)
                continue

            # -----------------------------------------------------------
            # General semantic extraction.
            # -----------------------------------------------------------

            metric_result = _find_metric(fragment)

            if not metric_result:
                continue

            metric, metric_position, _ = metric_result

            value_result = _extract_value_and_unit(
                fragment,
                metric_position,
            )

            if not value_result:
                continue

            value, unit = value_result

            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                continue

            if not _is_metric_value_compatible(
                metric,
                numeric_value,
                unit,
                fragment,
            ):
                continue

            period = _find_period(
                fragment,
                metric_position,
            )

            scope = _find_scope(fragment)

            facts.append(
                {
                    "chunk_id": chunk_id,
                    "entity": _extract_entity(fragment),
                    "metric": metric,
                    "value": value,
                    "unit": unit,
                    "period": period,
                    "scope": scope,
                    "evidence": fragment,
                    "page_number": page_number,
                    "source_document": source_document,
                }
            )

    return facts