    """
    Simplified RAGAS Evaluator - Works without complex dependencies
    """

    from typing import Dict, List

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


    def evaluate_response_quality(question: str, answer: str, contexts: List[str]) -> Dict[str, float]:
        """
        Evaluate response quality using RAGAS metrics when available.
        Falls back to heuristic scoring if the RAGAS library is unavailable.
        """
        try:
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
                return {
                    "response_relevancy": response_relevancy,
                    "faithfulness": faithfulness,
                    "overall_quality": (response_relevancy + faithfulness) / 2.0
                }

            question_words = set(question.lower().split())
            answer_words = set(answer.lower().split())
            overlap = len(question_words.intersection(answer_words))
            relevance_score = min(overlap / max(len(question_words), 1), 1.0)

            contexts_text = " ".join(contexts) if contexts else ""
            context_words = set(contexts_text.lower().split())
            faithfulness_score = 0.0
            if context_words and answer_words:
                faithfulness_score = min(len(answer_words.intersection(context_words)) / max(len(answer_words), 1), 1.0)

            overall_quality = (relevance_score + faithfulness_score) / 2.0
            return {
                "response_relevancy": relevance_score,
                "faithfulness": faithfulness_score,
                "overall_quality": overall_quality,
                "note": "RAGAS library unavailable; using fallback heuristic evaluation"
            }

        except Exception as e:
            return {
                "error": f"Evaluation failed: {str(e)}",
                "response_relevancy": 0.0,
                "faithfulness": 0.0
            }
