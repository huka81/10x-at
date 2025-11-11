def format_currency_human_readable(amount, currency: str = "PLN"):
    """
    Format a potentially large number as a human-readable currency value.

    Args:
        amount: The numeric amount to format (int, float, or string representation)
        currency: Currency symbol/code (default: "PLN")

    Returns:
        Formatted string like "1,23 mln PLN" or "500,00 tys. PLN"
        If input is not a valid number, returns the original input value

    Examples:
        >>> format_currency_human_readable(1230000)
        '1,23 mln PLN'
        >>> format_currency_human_readable(500000)
        '500,00 tys. PLN'
        >>> format_currency_human_readable("invalid")
        'invalid'
        >>> format_currency_human_readable(None)
        None
        >>> format_currency_human_readable("")
        ''
    """
    # Handle None or empty values
    if amount is None or amount == "":
        return amount

    # Try to convert to float
    try:
        numeric_amount = float(amount)
        # Check for NaN
        if numeric_amount != numeric_amount:  # NaN check
            return amount
    except (ValueError, TypeError):
        # If conversion fails, return original value
        return amount

    if numeric_amount == 0:
        return f"0,00 {currency}"

    # Handle negative numbers
    is_negative = numeric_amount < 0
    numeric_amount = abs(numeric_amount)

    # Define thresholds and suffixes
    if numeric_amount >= 1_000_000_000:
        # Billions
        formatted_amount = numeric_amount / 1_000_000_000
        suffix = "mld"
    elif numeric_amount >= 1_000_000:
        # Millions
        formatted_amount = numeric_amount / 1_000_000
        suffix = "mln"
    elif numeric_amount >= 1_000:
        # Thousands
        formatted_amount = numeric_amount / 1_000
        suffix = "tys."
    else:
        # Less than 1000 - no suffix needed
        formatted_amount = numeric_amount
        suffix = ""

    # Format the number with appropriate decimal places
    if suffix:
        # For abbreviated amounts, use 2 decimal places
        formatted_str = f"{formatted_amount:.2f}".replace(".", ",")
    else:
        # For regular amounts, use standard formatting with thousands separator
        formatted_str = f"{formatted_amount:,.2f}".replace(",", " ").replace(".", ",")

    # Add negative sign if needed
    if is_negative:
        formatted_str = f"-{formatted_str}"

    # Combine with suffix and currency
    if suffix:
        return f"{formatted_str} {suffix} {currency}"
    else:
        return f"{formatted_str} {currency}"


def format_currency_compact(amount, currency: str = "PLN"):
    """
    Format a number as a more compact currency value (shorter suffixes).

    Args:
        amount: The numeric amount to format (int, float, or string representation)
        currency: Currency symbol/code (default: "PLN")

    Returns:
        Formatted string like "1,23M PLN" or "500K PLN"
        If input is not a valid number, returns the original input value

    Examples:
        >>> format_currency_compact(1230000)
        '1,23M PLN'
        >>> format_currency_compact("invalid")
        'invalid'
        >>> format_currency_compact(None)
        None
    """
    # Handle None or empty values
    if amount is None or amount == "":
        return amount

    # Try to convert to float
    try:
        numeric_amount = float(amount)
        # Check for NaN
        if numeric_amount != numeric_amount:  # NaN check
            return amount
    except (ValueError, TypeError):
        # If conversion fails, return original value
        return amount

    if numeric_amount == 0:
        return f"0 {currency}"

    # Handle negative numbers
    is_negative = numeric_amount < 0
    numeric_amount = abs(numeric_amount)

    # Define thresholds and suffixes (English style)
    if numeric_amount >= 1_000_000_000:
        formatted_amount = numeric_amount / 1_000_000_000
        suffix = "B"
    elif numeric_amount >= 1_000_000:
        formatted_amount = numeric_amount / 1_000_000
        suffix = "M"
    elif numeric_amount >= 1_000:
        formatted_amount = numeric_amount / 1_000
        suffix = "K"
    else:
        formatted_amount = numeric_amount
        suffix = ""

    # Format the number
    if suffix:
        if formatted_amount == int(formatted_amount):
            formatted_str = f"{int(formatted_amount)}"
        else:
            formatted_str = f"{formatted_amount:.2f}".replace(".", ",")
    else:
        formatted_str = f"{formatted_amount:,.0f}".replace(",", " ")

    # Add negative sign if needed
    if is_negative:
        formatted_str = f"-{formatted_str}"

    # Combine with suffix and currency
    if suffix:
        return f"{formatted_str}{suffix} {currency}"
    else:
        return f"{formatted_str} {currency}"


if __name__ == "__main__":
    # Test the functions
    print(format_currency_human_readable(1230000))  # "1,23 mln PLN"
    print(format_currency_human_readable(500000))  # "500,00 tys. PLN"
    print(format_currency_human_readable(1500))  # "1 500,00 PLN"
    print(format_currency_human_readable(1234567890))  # "1,23 mld PLN"
    print(format_currency_human_readable(-750000))  # "-750,00 tys. PLN"
    print(format_currency_human_readable(0))  # "0,00 PLN"
    print(format_currency_human_readable("NaN"))  # "NaN"
    print(format_currency_human_readable(""))  # ""
    print(format_currency_human_readable(None))  # None
    print(format_currency_human_readable("invalid"))  # "invalid"
    print(format_currency_human_readable("123.45"))  # "123,45 PLN"

    # Using different currency
    print(format_currency_human_readable(1230000, "USD"))  # "1,23 mln USD"

    # Compact version
    print(format_currency_compact(1230000))  # "1,23M PLN"
    print(format_currency_compact(500000))  # "500K PLN"
    print(format_currency_compact(1500))  # "1 500 PLN"
    print(format_currency_compact("invalid"))  # "invalid"
    print(format_currency_compact(None))  # None
