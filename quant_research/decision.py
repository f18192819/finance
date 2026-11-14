from dataclasses import dataclass

WEIGHTS = dict(trend=25, structure=25, zone=20, volume=15, momentum=15)


@dataclass
class Decision:
    score: float
    category: str
    reasons: list
    rejected_conditions: list


def score_candidate(factors, hard_rejections=(), weights=None, disabled=()):
    weights = weights or WEIGHTS
    active = {k: v for k, v in weights.items() if k not in disabled}
    if not active or any(v < 0 for v in active.values()) or sum(active.values()) <= 0:
        raise ValueError("Scoring weights must have positive total")
    score = 100 * sum(v for k, v in active.items() if factors.get(k, False)) / sum(active.values())
    reasons = [f"{k}: {'confirmed' if factors.get(k) else 'not confirmed'} ({v})" for k, v in active.items()]
    category = "REJECTED" if hard_rejections else "HIGH_QUALITY" if score >= 80 else "WAIT_CONFIRMATION" if score >= 65 else "EXCLUDED"
    return Decision(score, category, reasons, list(hard_rejections))
