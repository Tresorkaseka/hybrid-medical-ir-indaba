from collections.abc import Hashable, Mapping
from dataclasses import dataclass, field

from hybrid_ir.queries.demographics import PatientDemographics

_AGE_TOLERANCE_YEARS = 1e-6


@dataclass(frozen=True)
class GoldLabel:
    age_years: float
    sex: str


@dataclass
class FieldScore:
    """Compte, pour un champ, les valeurs justes, fausses et non trouvées (abstentions)."""

    correct: int = 0
    wrong: int = 0
    abstained: int = 0

    @property
    def found_rate(self) -> float:
        return (self.correct + self.wrong) / self._total

    @property
    def precision(self) -> float:
        found = self.correct + self.wrong
        return self.correct / found if found else 0.0

    @property
    def _total(self) -> int:
        return self.correct + self.wrong + self.abstained


@dataclass(frozen=True)
class ExtractionError:
    query_key: Hashable
    field: str
    expected: object
    predicted: object


@dataclass
class ExtractionScore:
    n_queries: int = 0
    age: FieldScore = field(default_factory=FieldScore)
    sex: FieldScore = field(default_factory=FieldScore)
    errors: list[ExtractionError] = field(default_factory=list)


def score_extraction(
    predictions: Mapping[Hashable, PatientDemographics],
    gold: Mapping[Hashable, GoldLabel],
) -> ExtractionScore:
    score = ExtractionScore(n_queries=len(gold))
    for query_key, label in gold.items():
        predicted = predictions[query_key]
        _record(score, query_key, "age", score.age, label.age_years, predicted.age_years, _same_age)
        _record(score, query_key, "sex", score.sex, label.sex, predicted.sex, lambda a, b: a == b)
    return score


def _same_age(expected: float, predicted: float) -> bool:
    return abs(expected - predicted) < _AGE_TOLERANCE_YEARS


def _record(score, query_key, field_name, field_score, expected, predicted, same) -> None:
    if predicted is None:
        field_score.abstained += 1
    elif same(expected, predicted):
        field_score.correct += 1
    else:
        field_score.wrong += 1
        score.errors.append(ExtractionError(query_key, field_name, expected, predicted))
