"""Decision-stage comparisons within a fixed prospective Holm family."""
from hybrid_ir.evaluation.bootstrap import DEFAULT_RESAMPLES, DEFAULT_SEED
from hybrid_ir.evaluation.comparison import compare_systems
from hybrid_ir.evaluation.run_scoring import METRIC_NAMES, score_run
from hybrid_ir.evaluation.significance import holm_adjust
from hybrid_ir.evaluation.trec_eval_check import crosscheck_with_ir_measures

PROSPECTIVE_PAIRS = (
    ('B', 'BM25'), ('A', 'BM25'), ('C', 'B'), ('C', 'A'),
    ('D', 'B'), ('E', 'C'), ('E', 'D'), ('Dprime', 'B'), ('Eprime', 'C'),
    ('D', 'Dprime'), ('E', 'Eprime'),
)
QUALITY_METRICS = tuple(m for m in METRIC_NAMES if m != 'Judged@10')
REQUIRED_SYSTEMS = {'BM25', 'A', 'B', 'C', 'D', 'E'}


def evaluate_decision_runs(rankings: dict, judgments: dict) -> dict:
    """Evaluate real runs only; reserve p=1 slots without inventing witness scores."""
    if not judgments or not REQUIRED_SYSTEMS.issubset(rankings):
        raise ValueError('Missing judgments or one of BM25/A/B/C/D/E')
    if set(rankings) - REQUIRED_SYSTEMS - {'Dprime', 'Eprime'}:
        raise ValueError('Unknown system in decision comparison')
    query_ids = sorted(judgments, key=int)
    for system, run in rankings.items():
        if set(run) != set(judgments):
            raise ValueError(f'{system}: query IDs differ from judgments')
        for key, ids in run.items():
            if (not isinstance(ids, list) or any(not isinstance(i, str) or not i for i in ids)
                    or len(ids) != len(set(ids))):
                raise ValueError(f'{system}/{key}: invalid or duplicate trial IDs')
    scores = {system: score_run(run, judgments) for system, run in rankings.items()}
    compared = sum(crosscheck_with_ir_measures(run, judgments, scores[system])
                   for system, run in rankings.items())
    observed = [(a, b) for a, b in PROSPECTIVE_PAIRS if a in scores and b in scores]
    report = compare_systems(scores, query_ids, observed, QUALITY_METRICS)
    availability = {}
    raw = []
    places = []
    for a, b in PROSPECTIVE_PAIRS:
        key = f'{a} − {b}'
        available = (a, b) in observed
        availability[key] = 'computed' if available else 'not_computed'
        if not available:
            report['pairs'][key] = {
                metric: {'difference': None, 'p': None, 'p_holm': None,
                         'holm_reserved_p': 1.0 if metric in QUALITY_METRICS else None}
                for metric in METRIC_NAMES
            }
        for metric in QUALITY_METRICS:
            raw.append(report['pairs'][key][metric]['p'] if available else 1.0)
            places.append((key, metric, available))
    for (key, metric, available), adjusted in zip(places, holm_adjust(raw)):
        if available:
            report['pairs'][key][metric]['p_holm'] = adjusted
    reserved = (len(PROSPECTIVE_PAIRS) - len(observed))*len(QUALITY_METRICS)
    return {**report, 'status': 'intermediate_baselines_pending' if reserved else 'complete',
            'pair_availability': availability,
            'holm_family': {'scope': 'per year', 'n_pairs': len(PROSPECTIVE_PAIRS),
                            'n_quality_metrics': len(QUALITY_METRICS), 'n_tests': len(raw),
                            'n_observed_tests': len(raw)-reserved, 'n_reserved_tests': reserved,
                            'reserved_p': 1.0, 'excluded_metrics': ['Judged@10']},
            'bootstrap': {'n_resamples': DEFAULT_RESAMPLES, 'seed': DEFAULT_SEED, 'confidence': .95},
            'values_crosschecked_with_ir_measures': compared, 'per_query': scores}
