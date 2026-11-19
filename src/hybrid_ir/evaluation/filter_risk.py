"""Risque du filtre SQL : parmi les essais jugés pour une requête, lesquels le filtre écarte-t-il ?

Niveaux de jugement TREC : 0 = non pertinent, 1 = exclu, 2 = éligible. Le dommage du filtre,
ce sont les essais éligibles écartés à tort ; son bénéfice, ce sont les non pertinents écartés.
"""
from collections.abc import Collection, Mapping
from dataclasses import dataclass

from hybrid_ir.evaluation.judgment_levels import ELIGIBLE, EXCLUDED, NOT_RELEVANT


@dataclass(frozen=True)
class FilterRisk:
    eligible_total: int
    eligible_removed: int
    excluded_total: int
    excluded_removed: int
    not_relevant_total: int
    not_relevant_removed: int


def measure_filter_risk(kept_ids: Collection[str], judgments: Mapping[str, int]) -> FilterRisk:
    totals = {NOT_RELEVANT: 0, EXCLUDED: 0, ELIGIBLE: 0}
    removed = {NOT_RELEVANT: 0, EXCLUDED: 0, ELIGIBLE: 0}
    kept = set(kept_ids)
    for trial_id, level in judgments.items():
        if level not in totals:
            raise ValueError(f"niveau de jugement inconnu : {level!r} pour {trial_id}")
        totals[level] += 1
        removed[level] += trial_id not in kept
    return FilterRisk(
        eligible_total=totals[ELIGIBLE], eligible_removed=removed[ELIGIBLE],
        excluded_total=totals[EXCLUDED], excluded_removed=removed[EXCLUDED],
        not_relevant_total=totals[NOT_RELEVANT], not_relevant_removed=removed[NOT_RELEVANT],
    )
