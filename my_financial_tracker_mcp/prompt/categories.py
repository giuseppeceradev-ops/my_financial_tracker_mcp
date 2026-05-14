def build_category_prompt(text: str) -> str:
    return f"""
    You must recognise a category associated to {text}

    ----------------------
    RULES
    ----------------------
    - Choose a very short and significant category, 
    - It must be composed by only one term
    - Use the italian language

    """