def validate_invoice(data: dict):
    items = data.get("items", [])

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
        if any(x in desc.lower() for x in ["totale"]):
            continue

        # evita stringhe senza senso
        if not any(c.isalpha() for c in desc):
            continue

        clean_items.append(i)

    data["items"] = clean_items

    return data