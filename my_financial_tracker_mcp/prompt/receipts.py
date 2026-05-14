def build_receipt_prompt(text: str, description: str) -> str:
    return f"""
    You are an expert financial OCR parser.

    Extract structured receipt data into STRICT JSON.

    The OCR text may contain errors → be conservative.

    ----------------------
    RULES
    ----------------------

    1. NO INVENTED ITEMS
    - Extract ONLY items clearly present
    - If unreadable → SKIP

    2. CLEAN TEXT
    - Fix obvious OCR errors ONLY if very clear
    - Otherwise keep original

    3. VALID ITEMS ONLY
    - Must contain description + numeric price
    - Ignore lines without price
    - Ignore totals, taxes, payments

    4. DUPLICATES
    - Merge identical items

    5. CATEGORIES (MANDATORY)
    Choose ONLY:
    - food
    - beverages
    - shopping
    - transport
    - other

    6. TOTAL
    - Extract if clearly present
    - Else null

    7. VALIDATE TOTAL
    - Compare sum(items) with total
    - If mismatch > 5% → total = null

    8. COMPANY
    - Extract if clear, else null

    9. DESCRIPTION
    - Pass "{description}" to the description attribute

    10. DATE
    - Extract receipt date if clearly present (format: ISO 8601 YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
    - Else null

    ----------------------
    OUTPUT (STRICT JSON ONLY)
    ----------------------

    {{
    "company": string | null,
    "description": string,
    "date": string | null,
    "items": [
        {{
        "description": string,
        "amount": float,
        "category": string
        }}
    ],
    "total": float | null
    }}

    NO markdown.
    NO explanations.

    OCR TEXT:
    {text}
    """