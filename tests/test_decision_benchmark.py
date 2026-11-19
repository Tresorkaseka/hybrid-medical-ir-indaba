import math
import json

import pytest

from hybrid_ir.decision.benchmark import decision_request, yes_probability, benchmark_pairs


def test_request_keeps_patient_and_trial_separate_without_labels():
    request = decision_request("patient text", "trial criteria")
    assert request["state"] == {"patient": "patient text", "clinical_trial": "trial criteria"}
    assert request["questions"]["eligible"]["type"] == "noul"
    assert set(request) == {"state", "questions"}


@pytest.mark.parametrize("value", [0.0, 0.27, 1.0])
def test_probability_is_read_from_official_noul_field(value):
    assert yes_probability({"answers": {"eligible": {"type": "noul", "noul": value}}}) == value


@pytest.mark.parametrize("answer", [
    {"type": "noul", "error": "max_length_exceeded"},
    {"type": "noul", "noul": math.nan},
    {"type": "noul", "noul": math.inf},
    {"type": "noul", "noul": -0.1},
    {"type": "noul", "noul": 1.1},
    {"type": "noul", "noul": True},
    {"type": "noul", "noul": "0.7"},
    {"type": "choice", "noul": 0.7},
])
def test_invalid_answers_fail_instead_of_becoming_ranking_scores(answer):
    with pytest.raises(ValueError):
        yes_probability({"answers": {"eligible": answer}})


def test_benchmark_preserves_raw_output_and_records_model_failures():
    payload = {"queries": {"2021/1": "patient"}, "trials": {"NCT1": "trial"},
               "benchmark_pairs": [{"query_key": "2021/1", "trial_id": "NCT1", "source": "B", "rank": 1}]}
    def scorer(**request):
        return {"answers": {"eligible": {"type": "noul", "noul": 0.8}},
                "usage": {"input_tokens": 52, "output_tokens": 0}}
    report = benchmark_pairs(payload, scorer)
    assert report["status"] == "complete"
    assert report["n_valid"] == 1
    assert report["records"][0]["probability"] == 0.8
    assert report["records"][0]["raw"]["usage"]["input_tokens"] == 52
    def failing_scorer(**request):
        raise RuntimeError("GPU unavailable")
    report = benchmark_pairs(payload, failing_scorer)
    assert report["status"] == "failed"
    assert report["n_valid"] == 0
    assert "GPU unavailable" in report["records"][0]["error"]


def test_benchmark_missing_trial_is_an_input_error():
    payload = {"queries": {"2021/1": "patient"}, "trials": {},
               "benchmark_pairs": [{"query_key": "2021/1", "trial_id": "NCT1"}]}
    with pytest.raises(ValueError, match="NCT1"):
        benchmark_pairs(payload, lambda **kw: None)


def test_nonfinite_model_response_can_be_saved_as_standard_json():
    payload = {"queries": {"2021/1": "patient"}, "trials": {"NCT1": "trial"},
               "benchmark_pairs": [{"query_key": "2021/1", "trial_id": "NCT1"}]}
    report = benchmark_pairs(payload, lambda **kw: {"answers": {
        "eligible": {"type": "noul", "noul": math.nan}}})
    assert report["status"] == "failed"
    json.dumps(report, allow_nan=False)
