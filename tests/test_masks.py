"""Liste d'essais gardés par le filtre, codée en un bit par essai dans l'ordre du corpus (envoi compact vers Colab)."""
import pytest
from hybrid_ir.retrieval.masks import pack_kept_mask, unpack_kept_mask

DOC_IDS = ["NCT1", "NCT2", "NCT3", "NCT4", "NCT5", "NCT6", "NCT7", "NCT8", "NCT9"]


def test_a_packed_mask_unpacks_to_the_same_trials_in_corpus_order():
    packed = pack_kept_mask({"NCT9", "NCT2", "NCT5"}, DOC_IDS)

    assert unpack_kept_mask(packed, len(DOC_IDS)) == [False, True, False, False, True, False, False, False, True]


def test_a_kept_trial_absent_from_the_corpus_is_an_error():
    with pytest.raises(ValueError, match="absent"):
        pack_kept_mask({"NCT404"}, DOC_IDS)
