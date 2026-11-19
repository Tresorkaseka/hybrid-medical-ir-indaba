"""Comparaison bruit/propre par système, sans modifier la famille des ablations."""
import math
from collections.abc import Mapping

from hybrid_ir.evaluation.bootstrap import bootstrap_ci, paired_bootstrap_ci


def compare_noisy_to_clean(clean: Mapping[str, float], noisy: Mapping[str, float]) -> dict:
    """Perte relative ponctuelle et IC de différence absolue, appariés par requête."""
    if (not clean or clean.keys() != noisy.keys()
            or any(isinstance(v, bool) or not isinstance(v, (int, float))
                   or not math.isfinite(v) or not 0 <= v <= 1
                   for scores in (clean, noisy) for v in scores.values())):
        raise ValueError('Expected aligned nonempty finite ranking scores in [0, 1]')
    keys = sorted(clean)
    original, changed = [clean[k] for k in keys], [noisy[k] for k in keys]
    clean_ci, noisy_ci = bootstrap_ci(original), bootstrap_ci(changed)
    return dict(n_queries=len(keys), clean_mean=clean_ci.mean, noisy_mean=noisy_ci.mean,
                clean_ci=vars(clean_ci), noisy_ci=vars(noisy_ci),
                relative_loss=(clean_ci.mean - noisy_ci.mean) / clean_ci.mean if clean_ci.mean else None,
                difference_noisy_minus_clean=vars(paired_bootstrap_ci(changed, original)))
