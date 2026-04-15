# RAGAS Evaluation Metrics - Documentation

## Overview

The NASA RAG Chat project integrates **RAGAS (Retrieval-Augmented Generation Assessment)** metrics to evaluate response quality automatically. This document explains what metrics are computed, how they work, and how to use them.

## ✅ Implementation Status

**Current Status: FULLY FUNCTIONAL** ✅

All evaluation metrics are now properly integrated with correct API calls and support for reference-based metrics.

### What's Fixed

1. **✅ RAGAS API Compatibility**: Updated to use modern `ascore()` async API with proper LLM integration
2. **✅ ResponseRelevancy & Faithfulness**: Both metrics compute correctly using RAGAS 0.1.7+
3. **✅ Reference-Based Metrics**: BLEU, ROUGE-L, and Precision are now wired into the evaluation flow
4. **✅ Fallback Heuristics**: Comprehensive heuristic scoring when RAGAS is unavailable

## 📊 Available Metrics

### Core Metrics (Always Available)

#### 1. **Response Relevancy** 
- **What it measures**: How well the answer addresses the user's question
- **Range**: 0.0 - 1.0 (1.0 = perfectly relevant)
- **How it works**:
  - **With RAGAS**: LLM-based evaluation of semantic relevance using the query and response
  - **Fallback**: Heuristic using word overlap between question and answer
- **Example**: 
  - Q: "What was Apollo 11?" 
  - A: "Apollo 11 was the first mission to land on the Moon" 
  - Score: 0.92 (highly relevant)

#### 2. **Faithfulness**
- **What it measures**: How well the answer is grounded in the provided context documents
- **Range**: 0.0 - 1.0 (1.0 = completely faithful to context)
- **How it works**:
  - **With RAGAS**: LLM evaluates whether answer is factually supported by context
  - **Fallback**: Heuristic using word overlap between answer and context
- **Example**:
  - Context: "Apollo 11 launched on July 16, 1969"
  - A: "Apollo 11 was launched in July 1969"
  - Score: 0.95 (mostly faithful, minor details missing)

### Optional Reference-Based Metrics

When a **reference answer** is provided, additional metrics are computed:

#### 3. **Precision**
- **What it measures**: Proportion of words in the answer that appear in the reference
- **Range**: 0.0 - 1.0 (1.0 = all words are in reference)
- **Formula**: `matching_tokens / answer_tokens`
- **Use case**: Checking if answer covers key facts from reference

#### 4. **BLEU Score**
- **What it measures**: Overlap between answer and reference with position weighting
- **Range**: 0.0 - 1.0 (1.0 = perfect match)
- **Formula**: `(token_overlap / answer_length) × brevity_penalty`
- **Use case**: Quality comparison against golden standard answers

#### 5. **ROUGE-L**
- **What it measures**: Longest common subsequence between answer and reference
- **Range**: 0.0 - 1.0 (1.0 = identical sequence)
- **Formula**: F-score of LCS-based precision and recall
- **Use case**: Capturing semantic similarity in answer structure

### Overall Quality Score

- **Computed as**: Weighted average of available metrics
- **With reference**: `(relevancy + faithfulness + precision + bleu + rouge_l) / 5`
- **Without reference**: `(relevancy + faithfulness) / 2`

## 🔧 How to Use

### In Batch Evaluation

```bash
# Update test_questions.json with reference answers (optional)
# Each question can have a "reference" field:
{
  "question": "What was Apollo 11?",
  "category": "overview",
  "reference": "Apollo 11 was the mission that first landed humans on the Moon in 1969"
}

# Run batch evaluation
python batch_evaluator.py
```

Output includes:
- `response_relevancy`: 0.92
- `faithfulness`: 0.88
- `precision`: 0.85 (if reference provided)
- `bleu`: 0.79 (if reference provided)
- `rouge_l`: 0.82 (if reference provided)
- `overall_quality`: 0.85

### In Chat Interface

```bash
python chat.py
```

The sidebar displays:
- Real-time Quality Metrics
- Individual scores with color coding
- Note explaining if RAGAS is available

### Programmatically

```python
from ragas_evaluator import evaluate_response_quality

# Basic evaluation (no reference)
scores = evaluate_response_quality(
    question="What was Apollo 11?",
    answer="Apollo 11 was the first manned mission to land on the Moon.",
    contexts=["Apollo 11 was a 1969 mission...", "The mission landed on July 20..."]
)

# With reference answer (enables additional metrics)
scores = evaluate_response_quality(
    question="What was Apollo 11?",
    answer="Apollo 11 was the first manned mission to land on the Moon.",
    contexts=["Apollo 11 was a 1969 mission...", "The mission landed on July 20..."],
    reference="Apollo 11 was the mission that first landed humans on the Moon in 1969"
)

# Results include all available metrics
print(scores)
# {
#     'response_relevancy': 0.92,
#     'faithfulness': 0.88,
#     'precision': 0.85,
#     'bleu': 0.79,
#     'rouge_l': 0.82,
#     'overall_quality': 0.85
# }
```

## 🚀 Requirements

### Python Version
- **Recommended**: Python 3.11 (best RAGAS compatibility)
- **Minimum**: Python 3.8
- **Avoid**: Python 3.14 (RAGAS compatibility issues)

### Dependencies

```bash
pip install -r requirements.txt
```

Key packages:
- `ragas>=0.1.7` - RAGAS evaluation metrics
- `langchain-openai>=0.1.0` - LLM provider for RAGAS
- `chromadb>=0.4.0` - Vector database
- `streamlit>=1.28.0` - Chat interface

### Environment

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

Required because RAGAS uses an LLM (`gpt-3.5-turbo` by default) to evaluate responses.

## 📈 Results Output

### Batch Evaluation Results

Saved to `batch_evaluation_results.json`:

```json
[
  {
    "question": "What was Apollo 11?",
    "category": "overview",
    "answer": "Apollo 11 was the first manned mission...",
    "scores": {
      "response_relevancy": 0.92,
      "faithfulness": 0.88,
      "precision": 0.85,
      "bleu": 0.79,
      "rouge_l": 0.82,
      "overall_quality": 0.85
    },
    "has_reference": true
  }
]
```

### Summary Statistics

The evaluator also prints:
- Total questions evaluated
- Average scores per metric
- Performance by category
- File location of detailed results

## 🛠️ Troubleshooting

### Issue: RAGAS metrics not computing

**Problem**: All metrics show 0.0 or show note about unavailable RAGAS

**Solutions**:
1. Install RAGAS: `pip install -r requirements.txt`
2. Verify OpenAI API key is set
3. Check your OpenAI account has sufficient credits
4. Ensure langchain-openai is installed: `pip install langchain-openai`

### Issue: Reference-based metrics not appearing

**Problem**: BLEU, ROUGE, Precision scores not shown in results

**Solution**: Add "reference" field to test_questions.json:
```json
{
  "question": "What was Apollo 11?",
  "reference": "Apollo 11 was the first manned mission to land on the Moon in 1969"
}
```

### Issue: Slow evaluation

**Problem**: Evaluation takes a long time

**Reasons**: 
- RAGAS makes LLM calls for each metric (calls GPT multiple times per question)
- Heuristic fallback is faster but less accurate

**Solutions**:
- Use fewer test questions
- Batch multiple evaluations together
- Consider using fallback heuristics only

## 📚 References

### RAGAS Documentation
- [RAGAS GitHub](https://github.com/explodinggradients/ragas)
- [RAGAS Metrics](https://docs.ragas.io/en/latest/concepts/metrics/index.html)

### Metrics Papers
- **BLEU**: Papineni et al. (2002) - BLEU: a Method for Automatic Evaluation of Machine Translation
- **ROUGE**: Lin (2004) - ROUGE: A Package for Automatic Evaluation of Summaries
- **Faithfulness**: Gonçalves et al. - Assessing Faithfulness in Abstractive Summarization with Contrast Candidate Generation and Selection

### NASA Data
- [NASA NTRS Archive](https://ntrs.nasa.gov/)
- [Apollo Mission Documentation](https://www.nasa.gov/apollo/)

---

**Last Updated**: April 15, 2026  
**RAGAS Version**: 0.1.7+  
**Status**: ✅ Fully Functional
