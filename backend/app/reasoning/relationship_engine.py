from typing import Dict, Any

from app.reasoning.fact_matcher import facts_match
from app.reasoning.fact_normalizer import normalize_fact, normalize_number


# ============================================================
# UNIT ALIASES
# ============================================================

UNIT_ALIASES = {
    # Percentage
    "%": "%",
    "percent": "%",
    "percentage": "%",
    "pct": "%",

    # Magnitude-only units
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

    # Indian magnitude units
    "lakh": "lakh",
    "lakhs": "lakh",

    "crore": "crore",
    "crores": "crore",

    # Currency
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

    # Weight
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

    # Distance
    "km": "km",
    "kilometer": "km",
    "kilometers": "km",
    "kilometre": "km",
    "kilometres": "km",

    "mile": "mile",
    "miles": "mile",

    # Time
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

    # Power
    "kw": "kw",
    "kilowatt": "kw",
    "kilowatts": "kw",

    "mw": "mw",
    "megawatt": "mw",
    "megawatts": "mw",

    "gw": "gw",
    "gigawatt": "gw",
    "gigawatts": "gw",

    # Basis points
    "bps": "bps",
    "basis points": "bps",
}


# Magnitude units are scales rather than measurement dimensions.
MAGNITUDE_UNITS = {
    "k",
    "m",
    "bn",
    "tn",
    "lakh",
    "crore",
}


# Currency dimensions.
CURRENCY_UNITS = {
    "$",
    "₹",
    "€",
    "£",
}


# Percentage dimensions.
PERCENT_UNITS = {
    "%",
}


# Physical dimensions.
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

    Examples
    --------
    million -> m
    billion -> bn
    percentage -> %
    USD -> $
    INR -> ₹
    tonnes -> ton
    megawatts -> mw
    """

    if unit is None:
        return ""

    value = str(unit).strip().lower()

    if not value:
        return ""

    # Exact alias first.
    if value in UNIT_ALIASES:
        return UNIT_ALIASES[value]

    # Normalize spaces.
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

    This is intentionally generic.

    Examples
    --------
    "$"               -> currency
    "₹"               -> currency
    "%"               -> percentage
    "million"         -> magnitude
    "bn"              -> magnitude
    "tonnes"          -> weight
    "MW"              -> power
    "shipments/day"   -> throughput
    "bags/day"        -> throughput
    "vehicles"        -> count
    ""                -> unknown

    The function does NOT attempt currency conversion or physical
    unit conversion.
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

    # Generic throughput/rate units.
    lowered = normalized.lower()

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

    # Common count-like dimensions.
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

    Important distinction:

        million vs billion
            -> compatible

        % vs percentage
            -> compatible

        $ vs $
            -> compatible

        ₹ vs $
            -> NOT compatible

        % vs employees
            -> NOT compatible

        MW vs shipments/day
            -> NOT compatible

        tonnes vs customers
            -> NOT compatible

    Missing units are handled conservatively.
    """

    normalized_a = normalize_unit(unit_a)
    normalized_b = normalize_unit(unit_b)

    # Both units missing.
    if not normalized_a and not normalized_b:
        return True

    # One unit is known and the other is missing.
    #
    # We cannot safely prove comparability, so return False.
    #
    # This prevents false contradictions such as:
    #
    #   revenue = $1 billion
    #   revenue = 1000
    #
    # from automatically being treated as equivalent.
    if not normalized_a or not normalized_b:
        return False

    # Exactly equal units.
    if normalized_a == normalized_b:
        return True

    dimension_a = _unit_dimension(normalized_a)
    dimension_b = _unit_dimension(normalized_b)

    # Magnitude units are interchangeable because the numerical
    # value is normalized to its base representation elsewhere.
    if (
        dimension_a == "magnitude"
        and dimension_b == "magnitude"
    ):
        return True

    # Magnitude + untyped number can be comparable.
    #
    # Example:
    #   1 billion
    #   1000000000
    #
    # The normalizer will convert the first to the base number.
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
    Normalize a numeric value using the shared fact normalizer.

    Examples
    --------
    1000 million -> 1,000,000,000
    1 billion    -> 1,000,000,000
    12.68%       -> 12.68
    """

    if value is None:
        return None

    return normalize_number(value)


# ============================================================
# FACT PREPARATION
# ============================================================

def _prepare_fact(fact: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure the fact is in normalized form.

    The pipeline normally passes normalized facts.

    However, tests and other callers may pass raw facts such as:

        {
            "entity": "company a",
            "metric": "revenue",
            "value": 1,
            "unit": "billion"
        }

    In that situation, normalize_fact() is applied here.

    If the fact already contains the normalized keys, it is reused.
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
# PERIOD / SCOPE HELPERS
# ============================================================

def _get_period(fact: Dict[str, Any]) -> str:
    """
    Get normalized period from either raw or normalized fact.
    """

    return (
        fact.get("period_key")
        or fact.get("period")
        or ""
    )


def _get_scope(fact: Dict[str, Any]) -> str:
    """
    Get normalized scope from either raw or normalized fact.
    """

    return (
        fact.get("scope_key")
        or fact.get("scope")
        or ""
    )


def _get_unit(fact: Dict[str, Any]) -> str:
    """
    Get normalized unit from either raw or normalized fact.
    """

    return (
        fact.get("unit_key")
        or fact.get("unit")
        or ""
    )


# ============================================================
# VALUE COMPARISON
# ============================================================

def _values_are_equal(
    value_a: Any,
    value_b: Any,
) -> bool:
    """
    Compare normalized numerical values safely.

    A small relative tolerance is used because values may originate
    from decimal arithmetic or floating-point parsing.
    """

    if value_a is None or value_b is None:
        return False

    try:
        a = float(value_a)
        b = float(value_b)
    except (TypeError, ValueError):
        return False

    # Exact comparison first.
    if a == b:
        return True

    # Relative tolerance for large values.
    difference = abs(a - b)
    scale = max(abs(a), abs(b), 1.0)

    return difference <= max(
        1e-9 * scale,
        1e-6,
    )


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

        - corroboration
        - contradiction
        - contextual_difference
        - incomparable
        - uncertain

    Decision order
    --------------

    1. Same underlying concept?
    2. Are measurement dimensions compatible?
    3. Are values present?
    4. Are periods different?
    5. Are scopes different?
    6. Do normalized values agree?

    Important:

    Different units/dimensions are classified as
    ``incomparable``, NOT ``contextual_difference``.

    Contextual difference is reserved for cases such as:

        FY2022 revenue = $500M
        FY2024 revenue = $900M

    These facts can be meaningfully compared, but they describe
    different reporting contexts.
    """

    # ---------------------------------------------------------
    # 1. Normalize raw facts if necessary.
    # ---------------------------------------------------------

    prepared_a = _prepare_fact(fact_a)
    prepared_b = _prepare_fact(fact_b)

    if not prepared_a or not prepared_b:
        return {
            "relationship": "uncertain",
            "reason": "One or both facts are invalid or empty.",
        }

    # ---------------------------------------------------------
    # 2. Determine whether the facts describe the same concept.
    # ---------------------------------------------------------

    if not facts_match(
        prepared_a,
        prepared_b,
    ):
        return {
            "relationship": "incomparable",
            "reason": (
                "The facts do not refer to the same underlying "
                "entity and metric."
            ),
        }

    # ---------------------------------------------------------
    # 3. Check measurement dimensions BEFORE comparing values.
    # ---------------------------------------------------------

    unit_a = _get_unit(prepared_a)
    unit_b = _get_unit(prepared_b)

    if not units_are_compatible(
        unit_a,
        unit_b,
    ):
        dimension_a = _unit_dimension(unit_a)
        dimension_b = _unit_dimension(unit_b)

        return {
            "relationship": "incomparable",
            "reason": (
                "The facts use incompatible measurement "
                "dimensions and cannot be directly compared."
            ),
            "unit_a": normalize_unit(unit_a),
            "unit_b": normalize_unit(unit_b),
            "dimension_a": dimension_a,
            "dimension_b": dimension_b,
        }

    # ---------------------------------------------------------
    # 4. Values are required for numerical comparison.
    # ---------------------------------------------------------

    value_a = prepared_a.get("value")
    value_b = prepared_b.get("value")

    if value_a is None or value_b is None:
        return {
            "relationship": "uncertain",
            "reason": (
                "The facts appear conceptually comparable, "
                "but one or both facts do not contain a "
                "comparable numerical value."
            ),
        }

    # ---------------------------------------------------------
    # 5. Normalize values.
    # ---------------------------------------------------------

    normalized_value_a = normalize_value(value_a)
    normalized_value_b = normalize_value(value_b)

    # If normalization still leaves non-numeric values,
    # numerical relationship classification is unsafe.
    if not isinstance(
        normalized_value_a,
        (int, float),
    ):
        return {
            "relationship": "uncertain",
            "reason": (
                "The first fact contains a value that could "
                "not be normalized numerically."
            ),
        }

    if not isinstance(
        normalized_value_b,
        (int, float),
    ):
        return {
            "relationship": "uncertain",
            "reason": (
                "The second fact contains a value that could "
                "not be normalized numerically."
            ),
        }

    # ---------------------------------------------------------
    # 6. Compare reporting periods.
    # ---------------------------------------------------------

    period_a = _get_period(prepared_a)
    period_b = _get_period(prepared_b)

    if (
        period_a
        and period_b
        and period_a != period_b
    ):
        return {
            "relationship": "contextual_difference",
            "reason": (
                "The facts describe the same metric but "
                "refer to different reporting periods."
            ),
            "normalized_value_a": normalized_value_a,
            "normalized_value_b": normalized_value_b,
        }

    # ---------------------------------------------------------
    # 7. Compare scopes.
    # ---------------------------------------------------------

    scope_a = _get_scope(prepared_a)
    scope_b = _get_scope(prepared_b)

    if (
        scope_a
        and scope_b
        and scope_a != scope_b
    ):
        return {
            "relationship": "contextual_difference",
            "reason": (
                "The facts describe the same metric but "
                "refer to different reporting scopes."
            ),
            "normalized_value_a": normalized_value_a,
            "normalized_value_b": normalized_value_b,
        }

    # ---------------------------------------------------------
    # 8. Compare normalized values.
    # ---------------------------------------------------------

    if _values_are_equal(
        normalized_value_a,
        normalized_value_b,
    ):
        return {
            "relationship": "corroboration",
            "reason": (
                "Both facts report the same normalized value "
                "for the same comparable context."
            ),
            "normalized_value_a": normalized_value_a,
            "normalized_value_b": normalized_value_b,
        }

    # ---------------------------------------------------------
    # 9. Same concept, same comparable context, different value.
    # ---------------------------------------------------------

    return {
        "relationship": "contradiction",
        "reason": (
            "The facts refer to the same metric and comparable "
            "measurement context, but report different "
            "normalized values."
        ),
        "normalized_value_a": normalized_value_a,
        "normalized_value_b": normalized_value_b,
    }