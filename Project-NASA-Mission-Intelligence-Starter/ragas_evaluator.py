"""
Simplified RAGAS Evaluator - Works without complex dependencies
"""

def evaluate_response_quality(question: str, answer: str, contexts: List[str]) -> Dict[str, float]:
    """
    Simplified evaluation that doesn't require RAGAS dependencies.
    Provides basic quality metrics for RAG responses.
    """
    try:
        # Basic metrics that don't require external libraries
        metrics = {}

        # Response length score (normalized)
        answer_length = len(answer.split())
        metrics['response_length'] = min(answer_length / 100.0, 1.0)  # Max score at 100 words

        # Context utilization score
        if contexts:
            total_context_length = sum(len(ctx.split()) for ctx in contexts)
            context_usage_ratio = min(answer_length / max(total_context_length, 1), 1.0)
            metrics['context_utilization'] = context_usage_ratio
        else:
            metrics['context_utilization'] = 0.0

        # Question-answer relevance (simple keyword matching)
        question_words = set(question.lower().split())
        answer_words = set(answer.lower().split())
        overlap = len(question_words.intersection(answer_words))
        relevance_score = min(overlap / max(len(question_words), 1), 1.0)
        metrics['relevance'] = relevance_score

        # Answer completeness (checks for common question indicators)
        completeness_indicators = ['because', 'due to', 'since', 'as', 'when', 'where', 'how', 'why']
        completeness_score = sum(1 for indicator in completeness_indicators if indicator in answer.lower())
        metrics['completeness'] = min(completeness_score / 3.0, 1.0)

        # Overall quality score (weighted average)
        weights = {
            'response_length': 0.2,
            'context_utilization': 0.3,
            'relevance': 0.3,
            'completeness': 0.2
        }

        overall_score = sum(metrics[metric] * weight for metric, weight in weights.items())
        metrics['overall_quality'] = overall_score

        return metrics

    except Exception as e:
        return {
            "error": f"Evaluation failed: {str(e)}",
            "response_length": 0.5,
            "context_utilization": 0.5,
            "relevance": 0.5,
            "completeness": 0.5,
            "overall_quality": 0.5
        }
