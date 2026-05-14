def validate_receipt(data: dict):
    items = data.get("items", [])
    total = data.get("total")

    clean_items = []

    for i in items:
        desc = (i.get("description") or "").strip()
        amount = i.get("amount")

        # filtro base
        if not desc or len(desc) < 3:
            continue
        if not isinstance(amount, (int, float)):
            continue

        # rimuove righe non item
        if any(x in desc.lower() for x in ["totale", "conto", "resto"]):
            continue

        # evita stringhe senza senso
        if not any(c.isalpha() for c in desc):
            continue

        clean_items.append(i)

    data["items"] = clean_items

    # validazione totale
    if clean_items and total:
        computed = sum(i["amount"] for i in clean_items)
        diff = abs(computed - total) / max(total, 1)

        if diff > 0.05:
            data["total"] = None

    return data
