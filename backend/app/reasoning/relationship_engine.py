from typing import Dict, Any
import re

from app.reasoning.fact_matcher import facts_match
from app.reasoning.fact_normalizer import normalize_fact, normalize_number


# ============================================================
# UNIT ALIASES
# ============================================================

UNIT_ALIASES = {
    "%": "%",
    "percent": "%",
    "percentage": "%",
    "pct": "%",

    "k": "k",
    "thousand": "k",

    "m": "m",
    "mn": "m",
    "million": "m",

    "bn": "bn",
    "b": "bn",
    "billion": "bn",

    "tn": "tn",
    "t": "tn",
    "trillion": "tn",

    "lakh": "lakh",
    "lakhs": "lakh",

    "crore": "crore",
    "crores": "crore",

    "$": "$",
    "usd": "$",
    "us$": "$",

    "₹": "₹",
    "rs": "₹",
    "rs.": "₹",
    "inr": "₹",

    "€": "€",
    "eur": "€",

    "£": "£",
    "gbp": "£",

    "g": "g",
    "gram": "g",
    "grams": "g",

    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",

    "ton": "ton",
    "tons": "ton",
    "tonne": "ton",
    "tonnes": "ton",

    "km": "km",
    "kilometer": "km",
    "kilometers": "km",
    "kilometre": "km",
    "kilometres": "km",

    "mile": "mile",
    "miles": "mile",

    "second": "second",
    "seconds": "second",

    "minute": "minute",
    "minutes": "minute",

    "hour": "hour",
    "hours": "hour",

    "day": "day",
    "days": "day",

    "month": "month",
    "months": "month",

    "year": "year",
    "years": "year",

    "kw": "kw",
    "kilowatt": "kw",
    "kilowatts": "kw",

    "mw": "mw",
    "megawatt": "mw",
    "megawatts": "mw",

    "gw": "gw",
    "gigawatt": "gw",
    "gigawatts": "gw",

    "bps": "bps",
    "basis point": "bps",
    "basis points": "bps",
}


MAGNITUDE_UNITS = {
    "k",
    "m",
    "bn",
    "tn",
    "lakh",
    "crore",
}

CURRENCY_UNITS = {
    "$",
    "₹",
    "€",
    "£",
}

PERCENT_UNITS = {
    "%",
}

WEIGHT_UNITS = {
    "g",
    "kg",
    "ton",
}

DISTANCE_UNITS = {
    "km",
    "mile",
}

TIME_UNITS = {
    "second",
    "minute",
    "hour",
    "day",
    "month",
    "year",
}

POWER_UNITS = {
    "kw",
    "mw",
    "gw",
}

RATE_UNITS = {
    "bps",
}


# ============================================================
# UNIT NORMALIZATION
# ============================================================

def normalize_unit(unit: Any) -> str:
    """
    Convert common unit spellings into a canonical representation.
    """

    if unit is None:
        return ""

    value = str(unit).strip().lower()

    if not value:
        return ""

    if value in UNIT_ALIASES:
        return UNIT_ALIASES[value]

    value = " ".join(value.split())

    if value in UNIT_ALIASES:
        return UNIT_ALIASES[value]

    return value


# ============================================================
# UNIT DIMENSION
# ============================================================

def _unit_dimension(unit: Any) -> str:
    """
    Determine the semantic measurement dimension of a unit.

    Examples:
        "$"             -> currency
        "%"             -> percentage
        "million"       -> magnitude
        "tonnes"        -> weight
        "MW"            -> power
        "shipments/day" -> throughput
        "employees"     -> count
        ""              -> unknown
    """

    normalized = normalize_unit(unit)

    if not normalized:
        return "unknown"

    if normalized in CURRENCY_UNITS:
        return "currency"

    if normalized in PERCENT_UNITS:
        return "percentage"

    if normalized in MAGNITUDE_UNITS:
        return "magnitude"

    if normalized in WEIGHT_UNITS:
        return "weight"

    if normalized in DISTANCE_UNITS:
        return "distance"

    if normalized in TIME_UNITS:
        return "time"

    if normalized in POWER_UNITS:
        return "power"

    if normalized in RATE_UNITS:
        return "rate"

    lowered = normalized.lower()

    # Generic throughput / rate units.
    if "/" in lowered:
        if any(
            token in lowered
            for token in [
                "day",
                "month",
                "year",
                "hour",
                "second",
                "minute",
            ]
        ):
            return "throughput"

    # Generic count-like dimensions.
    if lowered in {
        "count",
        "counts",
        "employee",
        "employees",
        "customer",
        "customers",
        "user",
        "users",
        "vehicle",
        "vehicles",
        "store",
        "stores",
        "location",
        "locations",
        "facility",
        "facilities",
        "vendor",
        "vendors",
        "shipments",
        "orders",
        "accounts",
        "branches",
    }:
        return "count"

    return "other"


# ============================================================
# UNIT COMPATIBILITY
# ============================================================

def units_are_compatible(
    unit_a: Any,
    unit_b: Any,
) -> bool:
    """
    Determine whether two units represent comparable dimensions.

    Missing units are intentionally conservative.
    """

    normalized_a = normalize_unit(unit_a)
    normalized_b = normalize_unit(unit_b)

    # Both units missing.
    if not normalized_a and not normalized_b:
        return True

    # One known and one missing cannot safely be compared.
    if not normalized_a or not normalized_b:
        return False

    # Exact match.
    if normalized_a == normalized_b:
        return True

    dimension_a = _unit_dimension(normalized_a)
    dimension_b = _unit_dimension(normalized_b)

    # Magnitude scales are compatible because values are normalized.
    if (
        dimension_a == "magnitude"
        and dimension_b == "magnitude"
    ):
        return True

    # Magnitude + untyped numeric value.
    if (
        dimension_a == "magnitude"
        and dimension_b == "unknown"
    ):
        return True

    if (
        dimension_b == "magnitude"
        and dimension_a == "unknown"
    ):
        return True

    # Same semantic dimension.
    if (
        dimension_a != "unknown"
        and dimension_a == dimension_b
    ):
        return True

    return False


# ============================================================
# VALUE NORMALIZATION
# ============================================================

def normalize_value(value: Any) -> Any:
    """
    Normalize a numerical value using the shared fact normalizer.
    """

    if value is None:
        return None

    return normalize_number(value)


# ============================================================
# FACT PREPARATION
# ============================================================

def _prepare_fact(fact: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure the fact is normalized.
    """

    if not isinstance(fact, dict):
        return {}

    has_normalized_fields = (
        "entity_key" in fact
        or "metric_key" in fact
        or "unit_key" in fact
        or "period_key" in fact
        or "scope_key" in fact
    )

    if has_normalized_fields:
        return fact

    return normalize_fact(fact)


# ============================================================
# BASIC FIELD HELPERS
# ============================================================

def _get_period(fact: Dict[str, Any]) -> str:
    return (
        fact.get("period_key")
        or fact.get("period")
        or ""
    )


def _get_scope(fact: Dict[str, Any]) -> str:
    return (
        fact.get("scope_key")
        or fact.get("scope")
        or ""
    )


def _get_unit(fact: Dict[str, Any]) -> str:
    return (
        fact.get("unit_key")
        or fact.get("unit")
        or ""
    )


def _get_evidence(fact: Dict[str, Any]) -> str:
    return str(
        fact.get("evidence")
        or ""
    ).strip()


def _get_metric(fact: Dict[str, Any]) -> str:
    return str(
        fact.get("metric_key")
        or fact.get("metric")
        or ""
    ).strip().lower()


def _get_entity(fact: Dict[str, Any]) -> str:
    return str(
        fact.get("entity_key")
        or fact.get("entity")
        or ""
    ).strip().lower()


# ============================================================
# CONTEXT EXTRACTION
# ============================================================

def _normalize_text(text: Any) -> str:
    """
    Normalize free text for lightweight semantic context checks.
    """

    text = str(text or "").lower()

    text = re.sub(
        r"[^a-z0-9%₹$€£/\-\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text


def _context_markers(fact: Dict[str, Any]) -> set:
    """
    Extract generic contextual qualifiers from the fact evidence.

    This is deliberately domain-agnostic. It does not contain
    document-specific rules or hard-coded document facts.

    Examples of qualifiers:
        female
        male
        permanent
        contract
        domestic
        international
        quarterly
        annual
        per day
        per month
        consolidated
        standalone
        segment
        subsidiary
        ESOP
    """

    evidence = _normalize_text(_get_evidence(fact))

    markers = set()

    marker_groups = {
        "female": [
            "female",
            "women",
            "woman",
        ],
        "male": [
            "male",
            "men",
            "man",
        ],
        "permanent": [
            "permanent employee",
            "permanent employees",
            "permanent workforce",
        ],
        "contract": [
            "contract employee",
            "contract employees",
            "contract worker",
            "contract workers",
            "contractual",
        ],
        "temporary": [
            "temporary employee",
            "temporary employees",
            "temporary worker",
            "temporary workers",
        ],
        "esop": [
            "esop",
            "employee stock option",
            "employee stock options",
        ],
        "domestic": [
            "domestic",
        ],
        "international": [
            "international",
            "overseas",
        ],
        "export": [
            "export",
            "exports",
        ],
        "import": [
            "import",
            "imports",
        ],
        "consolidated": [
            "consolidated",
        ],
        "standalone": [
            "standalone",
        ],
        "segment": [
            "segment",
            "business segment",
            "reportable segment",
        ],
        "subsidiary": [
            "subsidiary",
            "subsidiaries",
        ],
        "quarterly": [
            "quarter",
            "quarterly",
            "q1",
            "q2",
            "q3",
            "q4",
        ],
        "annual": [
            "annual",
            "financial year",
            "fiscal year",
            "fy ",
        ],
        "ytd": [
            "year to date",
            "ytd",
        ],
    }

    for marker, phrases in marker_groups.items():
        if any(phrase in evidence for phrase in phrases):
            markers.add(marker)

    # Detect generic "per X" measurement context.
    if re.search(r"\bper\s+day\b", evidence):
        markers.add("per_day")

    if re.search(r"\bper\s+month\b", evidence):
        markers.add("per_month")

    if re.search(r"\bper\s+year\b", evidence):
        markers.add("per_year")

    if re.search(r"\bper\s+employee\b", evidence):
        markers.add("per_employee")

    if re.search(r"\bper\s+customer\b", evidence):
        markers.add("per_customer")

    return markers


def _contexts_are_conflicting(
    fact_a: Dict[str, Any],
    fact_b: Dict[str, Any],
) -> bool:
    """
    Detect clearly different semantic populations or contexts.

    This prevents comparisons such as:

        total employees vs female employees
        permanent employees vs contract employees
        ESOP holders vs total employees
        domestic revenue vs international revenue

    from being classified as contradictions.
    """

    markers_a = _context_markers(fact_a)
    markers_b = _context_markers(fact_b)

    if not markers_a or not markers_b:
        return False

    mutually_exclusive_groups = [
        {"female", "male"},
        {"permanent", "contract"},
        {"permanent", "temporary"},
        {"contract", "temporary"},
        {"domestic", "international"},
        {"export", "import"},
        {"consolidated", "standalone"},
        {"annual", "quarterly"},
    ]

    for group in mutually_exclusive_groups:
        if len(markers_a.intersection(group)) == 1:
            if len(markers_b.intersection(group)) == 1:
                if (
                    markers_a.intersection(group)
                    != markers_b.intersection(group)
                ):
                    return True

    # A specialized subset should not be compared directly with
    # the overall population.
    subset_markers = {
        "female",
        "male",
        "permanent",
        "contract",
        "temporary",
        "esop",
        "domestic",
        "international",
        "segment",
        "subsidiary",
        "per_employee",
        "per_customer",
    }

    subset_a = markers_a.intersection(subset_markers)
    subset_b = markers_b.intersection(subset_markers)

    if subset_a != subset_b:
        # If one fact has contextual qualifiers and the other
        # does not, the contexts are not safely comparable.
        if subset_a or subset_b:
            return True

    return False


# ============================================================
# VALUE COMPARISON
# ============================================================

def _values_are_equal(
    value_a: Any,
    value_b: Any,
) -> bool:
    """
    Compare normalized numerical values safely.
    """

    if value_a is None or value_b is None:
        return False

    try:
        a = float(value_a)
        b = float(value_b)
    except (TypeError, ValueError):
        return False

    if a == b:
        return True

    difference = abs(a - b)
    scale = max(abs(a), abs(b), 1.0)

    return difference <= max(
        1e-9 * scale,
        1e-6,
    )


# ============================================================
# RELATIONSHIP RESULT HELPERS
# ============================================================

def _result(
    relationship: str,
    reason: str,
    value_a: Any = None,
    value_b: Any = None,
    **extra: Any,
) -> Dict[str, Any]:
    """
    Build a consistent relationship result.
    """

    result = {
        "relationship": relationship,
        "reason": reason,
    }

    if value_a is not None:
        result["normalized_value_a"] = value_a

    if value_b is not None:
        result["normalized_value_b"] = value_b

    result.update(extra)

    return result


# ============================================================
# RELATIONSHIP CLASSIFICATION
# ============================================================

def classify_relationship(
    fact_a: Dict[str, Any],
    fact_b: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Classify the relationship between two facts.

    Possible relationships:

        corroboration
        contradiction
        contextual_difference
        incomparable
        uncertain

    Conservative decision process:

        1. Validate facts.
        2. Verify same underlying concept.
        3. Verify measurement compatibility.
        4. Verify numerical values.
        5. Check explicit semantic context.
        6. Check reporting period.
        7. Check scope.
        8. Compare values only when the context is genuinely comparable.

    The key principle is:

        Different values alone are NOT sufficient evidence
        of contradiction.

    Contradiction requires comparable metric, entity,
    measurement dimension, period, scope, and semantic population.
    """

    # ---------------------------------------------------------
    # 1. Normalize facts.
    # ---------------------------------------------------------

    prepared_a = _prepare_fact(fact_a)
    prepared_b = _prepare_fact(fact_b)

    if not prepared_a or not prepared_b:
        return _result(
            "uncertain",
            "One or both facts are invalid or empty.",
        )

    # ---------------------------------------------------------
    # 2. Same underlying concept?
    # ---------------------------------------------------------

    if not facts_match(
        prepared_a,
        prepared_b,
    ):
        return _result(
            "incomparable",
            (
                "The facts do not refer to the same "
                "underlying entity and metric."
            ),
        )

    # ---------------------------------------------------------
    # 3. Measurement compatibility.
    # ---------------------------------------------------------

    unit_a = _get_unit(prepared_a)
    unit_b = _get_unit(prepared_b)

    if not units_are_compatible(
        unit_a,
        unit_b,
    ):
        dimension_a = _unit_dimension(unit_a)
        dimension_b = _unit_dimension(unit_b)

        return _result(
            "incomparable",
            (
                "The facts use incompatible measurement "
                "dimensions and cannot be directly compared."
            ),
            unit_a=normalize_unit(unit_a),
            unit_b=normalize_unit(unit_b),
            dimension_a=dimension_a,
            dimension_b=dimension_b,
        )

    # ---------------------------------------------------------
    # 4. Values are required.
    # ---------------------------------------------------------

    value_a = prepared_a.get("value")
    value_b = prepared_b.get("value")

    if value_a is None or value_b is None:
        return _result(
            "uncertain",
            (
                "The facts appear conceptually comparable, "
                "but one or both facts do not contain a "
                "comparable numerical value."
            ),
        )

    # ---------------------------------------------------------
    # 5. Normalize values.
    # ---------------------------------------------------------

    normalized_value_a = normalize_value(value_a)
    normalized_value_b = normalize_value(value_b)

    if not isinstance(
        normalized_value_a,
        (int, float),
    ):
        return _result(
            "uncertain",
            (
                "The first fact contains a value that "
                "could not be normalized numerically."
            ),
        )

    if not isinstance(
        normalized_value_b,
        (int, float),
    ):
        return _result(
            "uncertain",
            (
                "The second fact contains a value that "
                "could not be normalized numerically."
            ),
        )

    # ---------------------------------------------------------
    # 6. Semantic population/context.
    # ---------------------------------------------------------

    if _contexts_are_conflicting(
        prepared_a,
        prepared_b,
    ):
        return _result(
            "contextual_difference",
            (
                "The facts use the same metric but describe "
                "different semantic populations, segments, "
                "or measurement contexts."
            ),
            normalized_value_a,
            normalized_value_b,
        )

    # ---------------------------------------------------------
    # 7. Reporting periods.
    # ---------------------------------------------------------

    period_a = _get_period(prepared_a)
    period_b = _get_period(prepared_b)

    if period_a and period_b:
        if period_a != period_b:
            return _result(
                "contextual_difference",
                (
                    "The facts describe the same metric but "
                    "refer to different reporting periods."
                ),
                normalized_value_a,
                normalized_value_b,
            )

    elif period_a or period_b:
        # One known period and one unknown period.
        # We cannot safely call different values a contradiction.
        return _result(
            "contextual_difference",
            (
                "The facts have incomplete period information; "
                "one fact specifies a reporting period while "
                "the other does not."
            ),
            normalized_value_a,
            normalized_value_b,
        )

    # ---------------------------------------------------------
    # 8. Reporting scopes.
    # ---------------------------------------------------------

    scope_a = _get_scope(prepared_a)
    scope_b = _get_scope(prepared_b)

    if scope_a and scope_b:
        if scope_a != scope_b:
            return _result(
                "contextual_difference",
                (
                    "The facts describe the same metric but "
                    "refer to different reporting scopes."
                ),
                normalized_value_a,
                normalized_value_b,
            )

    elif scope_a or scope_b:
        # One known scope and one unknown scope.
        return _result(
            "contextual_difference",
            (
                "The facts have incomplete scope information; "
                "one fact specifies a scope while the other does not."
            ),
            normalized_value_a,
            normalized_value_b,
        )

    # ---------------------------------------------------------
    # 9. Entity context.
    # ---------------------------------------------------------

    entity_a = _get_entity(prepared_a)
    entity_b = _get_entity(prepared_b)

    if entity_a and entity_b and entity_a != entity_b:
        return _result(
            "incomparable",
            (
                "The facts refer to different entities and "
                "therefore cannot be treated as a direct "
                "corroboration or contradiction."
            ),
            normalized_value_a,
            normalized_value_b,
        )

    # ---------------------------------------------------------
    # 10. Missing measurement units.
    # ---------------------------------------------------------

    # If both units are absent, we can compare only when the
    # rest of the context is sufficiently strong.
    #
    # This deliberately avoids aggressive contradiction claims
    # based solely on metric names.

    if not unit_a and not unit_b:
        evidence_a = _get_evidence(prepared_a)
        evidence_b = _get_evidence(prepared_b)

        # If neither evidence contains meaningful measurement
        # context, identical values are still safe to corroborate,
        # but differing values are uncertain rather than contradiction.
        if _values_are_equal(
            normalized_value_a,
            normalized_value_b,
        ):
            return _result(
                "corroboration",
                (
                    "Both facts report the same normalized value "
                    "and no conflicting measurement context was found."
                ),
                normalized_value_a,
                normalized_value_b,
            )

        if not evidence_a or not evidence_b:
            return _result(
                "uncertain",
                (
                    "The facts have no explicit measurement units "
                    "or sufficient evidence context to safely "
                    "classify the differing values as a contradiction."
                ),
                normalized_value_a,
                normalized_value_b,
            )

        # Evidence exists, but without explicit units the engine
        # remains conservative.
        return _result(
            "uncertain",
            (
                "The facts share a metric but lack explicit units; "
                "different values are not sufficient evidence of "
                "a genuine contradiction."
            ),
            normalized_value_a,
            normalized_value_b,
        )

    # ---------------------------------------------------------
    # 11. Compare normalized values.
    # ---------------------------------------------------------

    if _values_are_equal(
        normalized_value_a,
        normalized_value_b,
    ):
        return _result(
            "corroboration",
            (
                "Both facts report the same normalized value "
                "for the same comparable context."
            ),
            normalized_value_a,
            normalized_value_b,
        )

    # ---------------------------------------------------------
    # 12. Genuine contradiction.
    # ---------------------------------------------------------

    return _result(
        "contradiction",
        (
            "The facts refer to the same metric, compatible "
            "measurement dimension, and comparable reporting "
            "context, but report materially different "
            "normalized values."
        ),
        normalized_value_a,
        normalized_value_b,
    )