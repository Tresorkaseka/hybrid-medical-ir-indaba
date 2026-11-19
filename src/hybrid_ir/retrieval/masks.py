"""Masque des essais gardés par le filtre SQL : un bit par essai, dans l'ordre du corpus, encodé en base64.

Sert à envoyer vers Colab, pour la configuration C, les essais admis pour chaque requête sans transférer
des centaines de milliers d'identifiants.
"""
import base64
from collections.abc import Collection, Sequence

import numpy as np


def pack_kept_mask(kept_ids: Collection[str], doc_ids: Sequence[str]) -> str:
    unknown = set(kept_ids) - set(doc_ids)
    if unknown:
        raise ValueError(f"{len(unknown)} essai(s) gardé(s) absent(s) du corpus, par ex. {sorted(unknown)[0]}")
    kept = set(kept_ids)
    bits = np.fromiter((doc_id in kept for doc_id in doc_ids), dtype=bool, count=len(doc_ids))
    return base64.b64encode(np.packbits(bits).tobytes()).decode("ascii")


def unpack_kept_mask(packed: str, n_docs: int) -> list[bool]:
    bits = np.unpackbits(np.frombuffer(base64.b64decode(packed), dtype=np.uint8), count=n_docs)
    return bits.astype(bool).tolist()
