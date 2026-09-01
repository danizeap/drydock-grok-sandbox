"""A single pure function used as the choreography smoke target."""


def seaworthy_greeting(name: str) -> str:
    """Return a fixed greeting for ``name``.

    The name is stripped of surrounding whitespace. An empty or
    whitespace-only name is rejected so the function has one real rule
    worth testing.
    """
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("name must not be empty")
    return f"Ahoy, {cleaned}! The deck is seaworthy."
