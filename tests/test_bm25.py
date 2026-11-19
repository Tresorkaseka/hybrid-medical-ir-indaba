"""Tests de BM25 (formule de Lucene : idf = ln(1 + (N - n + 0,5) / (n + 0,5))).

Trois protections indépendantes : des scores calculés à la main, une version naïve de la formule
écrite mot par mot, et des cas limites. Corpus de base :
  d0 « cough fever » (2 mots), d1 « cough » (1 mot), d2 « rash itch rash » (3 mots) ; longueur moyenne = 2.
"""
import math
import random

import pytest

from hybrid_ir.retrieval.bm25 import Bm25Index
from hybrid_ir.retrieval.tokenizer import tokenize

K1, B = 0.9, 0.4
DOCS = [("d0", "cough fever"), ("d1", "cough"), ("d2", "rash itch rash")]


@pytest.fixture
def index():
    return Bm25Index.build(DOCS, k1=K1, b=B)


def naive_scores(documents, query, k1, b):
    """Formule appliquée telle quelle, document par document : référence lente et indépendante."""
    tokenized = [tokenize(text) for _, text in documents]
    n_docs = len(tokenized)
    average_length = sum(len(t) for t in tokenized) / n_docs
    scores = []
    for words in tokenized:
        score = 0.0
        for term in tokenize(query):
            doc_freq = sum(term in other for other in tokenized)
            if doc_freq == 0:
                continue
            idf = math.log(1 + (n_docs - doc_freq + 0.5) / (doc_freq + 0.5))
            tf = words.count(term)
            score += idf * tf / (tf + k1 * (1 - b + b * len(words) / average_length))
        scores.append(score)
    return scores


def test_scores_match_a_hand_computation_for_a_word_in_two_documents(index):
    idf = math.log(1 + (3 - 2 + 0.5) / (2 + 0.5))            # cough : 2 documents sur 3 -> ln(1,6)
    d0 = idf * 1 / (1 + 0.9 * (1 - 0.4 + 0.4 * 2 / 2))      # tf=1, longueur 2 = moyenne -> 1/1,9
    d1 = idf * 1 / (1 + 0.9 * (1 - 0.4 + 0.4 * 1 / 2))      # tf=1, longueur 1 -> 1/1,72

    assert list(index.scores("cough")) == pytest.approx([d0, d1, 0.0])


def test_scores_match_a_hand_computation_for_a_repeated_word(index):
    idf = math.log(1 + (3 - 1 + 0.5) / (1 + 0.5))            # rash : 1 document sur 3
    d2 = idf * 2 / (2 + 0.9 * (1 - 0.4 + 0.4 * 3 / 2))       # tf=2, longueur 3

    assert list(index.scores("rash")) == pytest.approx([0.0, 0.0, d2])


def test_a_shorter_document_scores_higher_for_the_same_word(index):
    scores = index.scores("cough")

    assert scores[1] > scores[0] > scores[2]


def test_scores_agree_with_the_naive_formula_on_a_random_corpus():
    rng = random.Random(7)
    vocabulary = [f"w{i}" for i in range(40)]
    documents = [(f"doc{i}", " ".join(rng.choices(vocabulary, k=rng.randint(1, 30)))) for i in range(60)]
    query = " ".join(rng.choices(vocabulary, k=8))

    fast = Bm25Index.build(documents, k1=K1, b=B).scores(query)

    assert list(fast) == pytest.approx(naive_scores(documents, query, K1, B), rel=1e-5)


def test_a_word_repeated_in_the_query_counts_each_time(index):
    assert list(index.scores("cough cough")) == pytest.approx([2 * s for s in index.scores("cough")])


def test_unknown_or_empty_queries_give_zero_everywhere(index):
    assert list(index.scores("zzz")) == [0.0, 0.0, 0.0]
    assert list(index.scores("")) == [0.0, 0.0, 0.0]


def test_search_returns_best_documents_first_and_omits_zero_scores(index):
    hits = index.search("cough", top_k=10)

    assert [hit.doc_id for hit in hits] == ["d1", "d0"]
    assert hits[0].score > hits[1].score > 0


def test_search_keeps_only_top_k(index):
    assert [hit.doc_id for hit in index.search("cough", top_k=1)] == ["d1"]


def test_search_breaks_ties_by_insertion_order():
    index = Bm25Index.build([("a", "fever"), ("b", "fever"), ("c", "fever")], k1=K1, b=B)

    assert [hit.doc_id for hit in index.search("fever", top_k=3)] == ["a", "b", "c"]


def test_search_can_be_restricted_to_allowed_documents(index):
    hits = index.search("cough", top_k=10, allowed_doc_ids={"d0", "d2"})

    assert [hit.doc_id for hit in hits] == ["d0"]


def test_restricting_documents_keeps_corpus_wide_scores(index):
    full = {hit.doc_id: hit.score for hit in index.search("cough", top_k=10)}
    restricted = {hit.doc_id: hit.score for hit in index.search("cough", top_k=10, allowed_doc_ids={"d0"})}

    assert restricted["d0"] == pytest.approx(full["d0"])


def test_an_index_saved_then_loaded_gives_identical_results(index, tmp_path):
    index.save(tmp_path / "bm25")

    reloaded = Bm25Index.load(tmp_path / "bm25")

    assert reloaded.doc_ids == index.doc_ids
    assert (reloaded.k1, reloaded.b) == (K1, B)
    assert list(reloaded.scores("cough rash")) == list(index.scores("cough rash"))
