"""BM25 à matrice creuse, avec la formule de Lucene.

Pourquoi un programme maison plutôt qu'une bibliothèque (détail : docs/pourquoi_bm25_maison.md) :
- il faut les MÊMES réglages et le MÊME découpage en mots dans toutes les configurations, y compris
  le test de fautes d'orthographe ; une bibliothèque tierce les cache ;
- `rank-bm25` est trop lent (≈ 18 s par requête sur 375 580 essais), `bm25s` et `bm25-turbo`
  saturent la mémoire d'un portable de 15 Go, `bm25-turbo` est sous licence AGPL ;
- le Rust est plus rapide pour indexer, mais l'écart n'a pas d'effet à notre échelle.

Formule (Lucene 9.12, BM25Similarity.java), pour un document d et une requête q :

    score(d, q) = somme, sur chaque mot t de q (répétitions comptées),
                  de  idf(t) * tf / (tf + k1 * (1 - b + b * longueur(d) / longueur_moyenne))
    idf(t)      = ln(1 + (N - n + 0,5) / (n + 0,5))     N documents, n contenant t

Différences connues avec Lucene : la longueur d'un document est exacte (Lucene la compresse sur
un octet, avec perte) ; le découpage en mots est celui de `tokenizer.py`.
"""
import json
from array import array
from collections.abc import Collection, Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import scipy.sparse as sp

from hybrid_ir.retrieval.tokenizer import tokenize

DEFAULT_K1 = 0.9  # défauts de Pyserini, fixés avant de voir les résultats : jamais réglés sur l'évaluation
DEFAULT_B = 0.4


@dataclass(frozen=True)
class Hit:
    doc_id: str
    score: float


class Bm25Index:
    def __init__(self, doc_ids: list[str], vocabulary: dict[str, int], weights: sp.csc_matrix, k1: float, b: float):
        self.doc_ids = doc_ids
        self.k1 = k1
        self.b = b
        self._vocabulary = vocabulary
        self._weights = weights

    @classmethod
    def build(cls, documents: Iterable[tuple[str, str]], k1: float = DEFAULT_K1, b: float = DEFAULT_B) -> "Bm25Index":
        """Construit l'index en lisant les documents un par un (mémoire maîtrisée sur 375 580 essais)."""
        doc_ids: list[str] = []
        vocabulary: dict[str, int] = {}
        row_starts, term_ids, term_counts, lengths = array("q", [0]), array("i"), array("d"), array("i")
        for doc_id, text in documents:
            words = tokenize(text)
            counts: dict[int, int] = {}
            for word in words:
                term_id = vocabulary.setdefault(word, len(vocabulary))
                counts[term_id] = counts.get(term_id, 0) + 1
            doc_ids.append(doc_id)
            lengths.append(len(words))
            term_ids.extend(counts.keys())
            term_counts.extend(counts.values())
            row_starts.append(len(term_ids))
        shape = (len(doc_ids), len(vocabulary))
        frequencies = sp.csr_matrix(
            (np.frombuffer(term_counts, dtype=np.float64), np.frombuffer(term_ids, dtype=np.int32), np.frombuffer(row_starts, dtype=np.int64)),
            shape=shape,
        )
        weights = _bm25_weights(frequencies, np.frombuffer(lengths, dtype=np.int32), k1, b)
        return cls(doc_ids, vocabulary, weights.tocsc(), k1, b)

    def scores(self, query: str) -> np.ndarray:
        """Score BM25 de chaque document, dans l'ordre d'insertion. Un mot répété compte autant de fois."""
        columns = [self._vocabulary[word] for word in tokenize(query) if word in self._vocabulary]
        if not columns:
            return np.zeros(len(self.doc_ids))
        return np.asarray(self._weights[:, columns].sum(axis=1)).ravel()

    def search(self, query: str, top_k: int, allowed_doc_ids: Collection[str] | None = None) -> list[Hit]:
        """Les `top_k` meilleurs documents, scores nuls exclus. Égalités : ordre d'insertion.

        `allowed_doc_ids` restreint la recherche (filtre SQL) sans changer les scores : l'idf et la
        longueur moyenne restent ceux du corpus entier, pour que le filtre ne modifie pas le classement.
        """
        scores = self.scores(query)
        if allowed_doc_ids is not None:
            allowed = set(allowed_doc_ids)
            scores = np.where([doc_id in allowed for doc_id in self.doc_ids], scores, 0.0)
        candidates = np.flatnonzero(scores > 0)
        ranked = candidates[np.lexsort((candidates, -scores[candidates]))][:top_k]
        return [Hit(self.doc_ids[i], float(scores[i])) for i in ranked]

    def save(self, directory: Path) -> None:
        """Écrit l'index dans `directory` : matrice (.npz) et métadonnées lisibles (.json), sans pickle."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        sp.save_npz(directory / "weights.npz", self._weights)
        metadata = {"k1": self.k1, "b": self.b, "doc_ids": self.doc_ids, "vocabulary": self._vocabulary}
        (directory / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    @classmethod
    def load(cls, directory: Path) -> "Bm25Index":
        directory = Path(directory)
        metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
        weights = sp.load_npz(directory / "weights.npz").tocsc()
        return cls(metadata["doc_ids"], metadata["vocabulary"], weights, metadata["k1"], metadata["b"])


def _bm25_weights(frequencies: sp.csr_matrix, lengths: np.ndarray, k1: float, b: float) -> sp.csr_matrix:
    n_docs = frequencies.shape[0]
    doc_freq = np.bincount(frequencies.indices, minlength=frequencies.shape[1])
    idf = np.log1p((n_docs - doc_freq + 0.5) / (doc_freq + 0.5))
    entry_lengths = np.repeat(lengths, np.diff(frequencies.indptr))
    length_norm = k1 * (1 - b + b * entry_lengths / lengths.mean())
    tf = frequencies.data
    weighted = frequencies.copy()
    weighted.data = idf[frequencies.indices] * tf / (tf + length_norm)
    return weighted
