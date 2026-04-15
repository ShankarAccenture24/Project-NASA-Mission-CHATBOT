"""
Simplified RAGAS Evaluator - Works without complex dependencies
"""

from collections import Counter
from typing import Dict, List, Optional

RAGAS_AVAILABLE = False

try:
    from ragas import SingleTurnSample
    try:
        from ragas.scorers import ResponseRelevancy, Faithfulness
    except ImportError:
        try:
            from ragas.metrics import ResponseRelevancy, Faithfulness
        except ImportError:
            from ragas import ResponseRelevancy, Faithfulness
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False
except Exception:
    RAGAS_AVAILABLE = False


def _safe_extract_score(score_obj):
    if isinstance(score_obj, dict):
        if "score" in score_obj:
            return float(score_obj["score"])
        if "scores" in score_obj and isinstance(score_obj["scores"], dict):
            return float(score_obj["scores"].get("score", 0.0))
    if isinstance(score_obj, (int, float)):
        return float(score_obj)
    raise ValueError(f"Unsupported score object: {score_obj}")


def _tokenize(text: str) -> List[str]:
    return [token for token in text.lower().split() if token]


def _compute_precision(candidate_tokens: List[str], reference_tokens: List[str]) -> float:
    if not candidate_tokens or not reference_tokens:
        return 0.0
    reference_counts = Counter(reference_tokens)
    match_count = 0
    for token in candidate_tokens:
        if reference_counts[token] > 0:
            match_count += 1
            reference_counts[token] -= 1
    return min(match_count / len(candidate_tokens), 1.0)


def _compute_bleu(candidate_tokens: List[str], reference_tokens: List[str]) -> float:
    if not candidate_tokens or not reference_tokens:
        return 0.0
    candidate_counts = Counter(candidate_tokens)
    reference_counts = Counter(reference_tokens)
    overlap = sum(min(candidate_counts[token], reference_counts[token]) for token in candidate_counts)
    precision = overlap / len(candidate_tokens)
    brevity = min(1.0, len(candidate_tokens) / max(len(reference_tokens), 1))
    return round(precision * brevity, 4)


def _lcs_length(a: List[str], b: List[str]) -> int:
    if not a or not b:
        return 0
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[-1][-1]


def _compute_rouge_l(candidate_tokens: List[str], reference_tokens: List[str]) -> float:
    if not candidate_tokens or not reference_tokens:
        return 0.0
    lcs = _lcs_length(candidate_tokens, reference_tokens)
    if lcs == 0:
        return 0.0
    precision = lcs / len(candidate_tokens)
    recall = lcs / len(reference_tokens)
    if precision + recall == 0:
        return 0.0
    return round(2 * precision * recall / (precision + recall), 4)


def evaluate_response_quality(question: str, answer: str, contexts: List[str], reference: Optional[str] = None) -> Dict[str, float]:
    """
    Evaluate response quality using RAGAS metrics when available.
    Falls back to heuristic scoring if the RAGAS library is unavailable.
    Supports optional deterministic metrics when a reference answer is provided.
    """
    try:
        question_words = set(question.lower().split())
        answer_words = set(answer.lower().split())
        overlap = len(question_words.intersection(answer_words))
        relevance_score = min(overlap / max(len(question_words), 1), 1.0)

        contexts_text = " ".join(contexts) if contexts else ""
        context_words = set(contexts_text.lower().split())
        faithfulness_score = 0.0
        if context_words and answer_words:
            faithfulness_score = min(len(answer_words.intersection(context_words)) / max(len(answer_words), 1), 1.0)

        scores = {
            "response_relevancy": relevance_score,
            "faithfulness": faithfulness_score,
        }

        if reference:
            reference_tokens = _tokenize(reference)
            candidate_tokens = _tokenize(answer)
            scores["precision"] = _compute_precision(candidate_tokens, reference_tokens)
            scores["bleu"] = _compute_bleu(candidate_tokens, reference_tokens)
            scores["rouge_l"] = _compute_rouge_l(candidate_tokens, reference_tokens)

        if RAGAS_AVAILABLE:
            sample = SingleTurnSample(
                query=question,
                response=answer,
                sources=[{"text": c} if isinstance(c, str) else c for c in (contexts or [])]
            )

            relevance_result = ResponseRelevancy().score(sample)
            faithfulness_result = Faithfulness().score(sample)

            response_relevancy = min(max(_safe_extract_score(relevance_result), 0.0), 1.0)
            faithfulness = min(max(_safe_extract_score(faithfulness_result), 0.0), 1.0)
            scores["response_relevancy"] = response_relevancy
            scores["faithfulness"] = faithfulness

        if reference:
            scores["overall_quality"] = (
                scores["response_relevancy"] +
                scores["faithfulness"] +
                scores["precision"] +
                scores["bleu"] +
                scores["rouge_l"]
            ) / 5.0
        else:
            scores["overall_quality"] = (scores["response_relevancy"] + scores["faithfulness"]) / 2.0

        if not RAGAS_AVAILABLE:
            scores["note"] = "RAGAS library unavailable; using fallback heuristic evaluation"

        return scores

    except Exception as e:
        return {
            "error": f"Evaluation failed: {str(e)}",
            "response_relevancy": 0.0,
            "faithfulness": 0.0
        }
