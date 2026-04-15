"""
RAGAS Evaluator with proper async handling for modern RAGAS versions
Supports ResponseRelevancy, Faithfulness, and optional reference-based metrics
"""

import asyncio
from collections import Counter
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

RAGAS_AVAILABLE = False
RAGAS_LLM = None

try:
    from ragas import SingleTurnSample
    try:
        from ragas.metrics import ResponseRelevancy, Faithfulness
    except ImportError:
        try:
            from ragas.scorers import ResponseRelevancy, Faithfulness
        except ImportError:
            from ragas import ResponseRelevancy, Faithfulness
    
    # Try to import LLM provider for RAGAS
    try:
        from langchain_openai import ChatOpenAI
        RAGAS_LLM = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    except ImportError:
        RAGAS_LLM = None
    
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False
except Exception as e:
    logger.warning(f"RAGAS import error: {e}")
    RAGAS_AVAILABLE = False


def _safe_extract_score(score_obj):
    """Extract numeric score from various RAGAS response formats"""
    try:
        if isinstance(score_obj, dict):
            if "score" in score_obj:
                return float(score_obj["score"])
            if "scores" in score_obj and isinstance(score_obj["scores"], dict):
                return float(score_obj["scores"].get("score", 0.0))
        if isinstance(score_obj, (int, float)):
            return float(score_obj)
        # Handle numeric-like objects with __float__
        return float(score_obj)
    except (ValueError, TypeError, AttributeError):
        logger.warning(f"Could not extract score from: {score_obj}")
        return 0.0


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


async def _compute_ragas_scores(question: str, answer: str, contexts: List[str]) -> Dict[str, float]:
    """
    Compute RAGAS metrics asynchronously.
    Returns empty dict if RAGAS is unavailable or fails.
    """
    if not RAGAS_AVAILABLE or not RAGAS_LLM:
        return {}
    
    try:
        # Prepare sample for RAGAS
        sample = SingleTurnSample(
            query=question,
            response=answer,
            sources=[{"text": c} if isinstance(c, str) else c for c in (contexts or [])]
        )
        
        ragas_scores = {}
        
        # Score ResponseRelevancy
        try:
            relevance_metric = ResponseRelevancy(llm=RAGAS_LLM)
            relevance_result = await relevance_metric.ascore(sample)
            response_relevancy = _safe_extract_score(relevance_result)
            ragas_scores["response_relevancy"] = min(max(response_relevancy, 0.0), 1.0)
        except Exception as e:
            logger.warning(f"ResponseRelevancy scoring failed: {e}")
            ragas_scores["response_relevancy"] = 0.0
        
        # Score Faithfulness
        try:
            faithfulness_metric = Faithfulness(llm=RAGAS_LLM)
            faithfulness_result = await faithfulness_metric.ascore(sample)
            faithfulness = _safe_extract_score(faithfulness_result)
            ragas_scores["faithfulness"] = min(max(faithfulness, 0.0), 1.0)
        except Exception as e:
            logger.warning(f"Faithfulness scoring failed: {e}")
            ragas_scores["faithfulness"] = 0.0
        
        return ragas_scores
    except Exception as e:
        logger.error(f"RAGAS scoring error: {e}")
        return {}


def evaluate_response_quality(question: str, answer: str, contexts: List[str], reference: Optional[str] = None) -> Dict[str, float]:
    """
    Evaluate response quality using RAGAS metrics when available.
    
    Computes:
    - response_relevancy: How well the answer addresses the question (RAGAS metric if available)
    - faithfulness: How well the answer is grounded in the provided context (RAGAS metric if available)
    - precision/bleu/rouge_l: Optional metrics computed only when a reference answer is provided
    - overall_quality: Weighted average of available metrics
    
    Falls back to heuristic scoring if RAGAS library is unavailable.
    
    Args:
        question: The user's question
        answer: The system-generated answer
        contexts: List of retrieved context documents
        reference: Optional reference/ground-truth answer for additional metrics
        
    Returns:
        Dictionary with metric scores (0.0-1.0 range) and a note if fallback is used
    """
    try:
        # Compute heuristic baseline scores
        question_words = set(question.lower().split())
        answer_words = set(answer.lower().split())
        overlap = len(question_words.intersection(answer_words))
        heuristic_relevance = min(overlap / max(len(question_words), 1), 1.0)

        contexts_text = " ".join(contexts) if contexts else ""
        context_words = set(contexts_text.lower().split())
        heuristic_faithfulness = 0.0
        if context_words and answer_words:
            heuristic_faithfulness = min(len(answer_words.intersection(context_words)) / max(len(answer_words), 1), 1.0)

        scores = {
            "response_relevancy": heuristic_relevance,
            "faithfulness": heuristic_faithfulness,
        }

        # Try RAGAS scoring (async wrapper)
        if RAGAS_AVAILABLE:
            try:
                ragas_scores = asyncio.run(_compute_ragas_scores(question, answer, contexts))
                scores.update(ragas_scores)
            except Exception as e:
                logger.warning(f"RAGAS async scoring failed, using heuristic: {e}")

        # Compute reference-based metrics if provided
        if reference:
            reference_tokens = _tokenize(reference)
            candidate_tokens = _tokenize(answer)
            scores["precision"] = _compute_precision(candidate_tokens, reference_tokens)
            scores["bleu"] = _compute_bleu(candidate_tokens, reference_tokens)
            scores["rouge_l"] = _compute_rouge_l(candidate_tokens, reference_tokens)

        # Compute overall quality score
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

        # Add note if RAGAS is unavailable
        if not RAGAS_AVAILABLE:
            scores["note"] = "RAGAS unavailable: using heuristic scoring"
        elif not (RAGAS_LLM):
            scores["note"] = "RAGAS LLM provider unavailable: using heuristic scoring"

        return scores

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return {
            "error": f"Evaluation failed: {str(e)}",
            "response_relevancy": 0.0,
            "faithfulness": 0.0,
            "overall_quality": 0.0
        }
