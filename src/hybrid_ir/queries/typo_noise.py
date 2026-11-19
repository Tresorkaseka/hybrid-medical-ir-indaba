"""Bruit synthétique auditable : une modification par mot sélectionné, requêtes seules."""
import hashlib
import math
import random
import re
import string
from collections.abc import Mapping, Sequence

_WORDS = re.compile(r'[A-Za-z]{2,}')


def _edit(word: str, rng: random.Random) -> tuple[str, str]:
    swaps = [i for i in range(len(word) - 1) if word[i] != word[i + 1]]
    operations = ['delete', 'insert', 'substitute'] + (['swap'] if swaps else [])
    operation = rng.choice(operations)
    if operation == 'swap':
        i = rng.choice(swaps)
        return word[:i] + word[i + 1] + word[i] + word[i + 2:], operation
    if operation == 'delete':
        i = rng.randrange(len(word))
        return word[:i] + word[i + 1:], operation
    i = rng.randrange(len(word) + (operation == 'insert'))
    reference = word[min(i, len(word) - 1)]
    alphabet = string.ascii_uppercase if reference.isupper() else string.ascii_lowercase
    letter = rng.choice(alphabet.replace(reference, '') if operation == 'substitute' else alphabet)
    return word[:i] + letter + word[i + (operation == 'substitute'):], operation


def perturb_queries(queries: Mapping[str, str], *, rates: Sequence[float] = (0.05, 0.1),
                    seed: int = 20261117) -> dict[str, dict[str, dict]]:
    """Niveaux imbriqués, échantillonnage par requête indépendant de l'ordre des entrées.

    Mots = segments ASCII d'au moins deux lettres ; chiffres, ponctuation et espaces
    intacts. Nombre choisi = taux × mots, arrondi au plus proche (demi vers le haut),
    minimum un si du texte est éligible. Les taux réalisés sont donc discrets.
    """
    if (not rates or any(isinstance(r, bool) or not isinstance(r, (float, int))
                         or not math.isfinite(r) or not 0 < r <= 1 for r in rates)
            or len(set(rates)) != len(rates)):
        raise ValueError('Rates must be distinct finite numbers in (0, 1]')
    outputs = {str(float(rate)): {} for rate in rates}
    for key, text in queries.items():
        digest = hashlib.sha256(f'{seed}\0{key}'.encode()).digest()
        rng = random.Random(int.from_bytes(digest, 'big'))
        words = list(_WORDS.finditer(text))
        positions = list(range(len(words)))
        rng.shuffle(positions)
        # Toute mutation est fixée une seule fois avant le choix du niveau de bruit.
        edits = []
        for i in positions:
            match = words[i]
            after, operation = _edit(match[0], rng)
            edits.append(dict(start=match.start(), end=match.end(), before=match[0],
                              after=after, operation=operation))
        for rate in rates:
            count = min(len(words), max(1, math.floor(len(words) * rate + 0.5))) if words else 0
            selected = sorted(edits[:count], key=lambda e: e['start'])
            noisy = text
            for edit in reversed(selected):
                noisy = noisy[:edit['start']] + edit['after'] + noisy[edit['end']:]
            outputs[str(float(rate))][key] = dict(text=noisy, n_eligible_words=len(words),
                                                 edits=selected, realized_rate=count / len(words) if words else 0)
    return outputs
