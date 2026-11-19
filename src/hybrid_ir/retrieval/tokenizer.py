import re

_WORD = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Découpe un texte en mots : minuscules, lettres et chiffres.

    Volontairement simple et identique pour toutes les configurations : ni racinisation,
    ni mots vides, ni accents. Limite connue : un texte français accentué serait coupé aux
    accents (« Zürich » donne « z » et « rich »).
    """
    return _WORD.findall(text.lower())
