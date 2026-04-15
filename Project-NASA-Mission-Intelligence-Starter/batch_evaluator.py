import json
import numpy as np
from rag_client import discover_chroma_backends, initialize_rag_system, retrieve_documents, format_context
from llm_client import generate_response
from ragas_evaluator import evaluate_response_quality


def load_questions(file_path):
    """Load test questions from JSON file"""
    with open(file_path, "r") as f:
        return json.load(f)


def run_batch_evaluation(openai_key, collection_name="nasa_space_missions_text", chroma_dir="./chroma_db_nasa", use_mock=False):
    """Run batch evaluation on test questions"""

    print("🚀 Starting Batch Evaluation")
    print("=" * 50)

    # Initialize RAG system (skip if using mock)
    if not use_mock:
        print("📊 Initializing RAG system...")
        collection, success, error = initialize_rag_system(chroma_dir, collection_name)

        if not success:
            print(f"❌ Failed to initialize RAG system: {error}")
            print("🔄 Switching to mock mode...")
            use_mock = True

    if use_mock:
        print("🎭 Using mock retrieval system for testing...")
        collection = None

    # Load test questions
    print("📋 Loading test questions...")
    try:
        questions = load_questions("test_questions.json")
        print(f"✅ Loaded {len(questions)} test questions")
    except FileNotFoundError:
        print("❌ test_questions.json not found!")
        return

    results = []

    for i, q in enumerate(questions, 1):
        question = q["question"]
        category = q.get("category", "general")

        print(f"\n🔍 Question {i}/{len(questions)}: {question}")
        print(f"📂 Category: {category}")

        try:
            # Retrieve documents
            if use_mock:
                # Mock retrieval for testing
                docs_result = {
                    'documents': [["Apollo 11 was the first manned mission to land on the Moon. The mission was launched on July 16, 1969, and successfully landed on the lunar surface on July 20, 1969. Astronauts Neil Armstrong and Buzz Aldrin became the first humans to walk on the Moon."]],
                    'metadatas': [[{"mission": "apollo11", "source": "mock_data"}]]
                }
                print("📄 Using mock documents for testing")
            else:
                docs_result = retrieve_documents(collection, question, n_results=3)

            if not docs_result or 'documents' not in docs_result:
                print("❌ No documents retrieved")
                continue

            # Format context
            context = format_context(
                docs_result['documents'][0] if docs_result['documents'] else [],
                docs_result['metadatas'][0] if docs_result['metadatas'] else []
            )

            # Generate answer
            answer = generate_response(
                user_message=question,
                context=context,
                conversation_history=[],
                openai_key=openai_key
            )

            # Extract contexts for evaluation
            contexts = docs_result['documents'][0] if docs_result['documents'] else []

            # Evaluate response quality
            scores = evaluate_response_quality(
                question=question,
                answer=answer,
                contexts=contexts
            )

            print("✨ Answer:", answer[:100] + "..." if len(answer) > 100 else answer)
            print("📊 Scores:", {k: f"{v:.3f}" if isinstance(v, (int, float)) else v for k, v in scores.items()})

            # Store results
            result_entry = {
                "question": question,
                "category": category,
                "answer": answer,
                "scores": scores,
                "context_length": len(context),
                "num_docs": len(contexts)
            }
            results.append(result_entry)

        except Exception as e:
            print(f"❌ Error processing question: {e}")
            continue

    # Aggregate and display final metrics
    if results:
        print("\n" + "=" * 60)
        print("📊 FINAL BATCH EVALUATION RESULTS")
        print("=" * 60)

        # Calculate averages for available metrics
        metric_sums = {}
        metric_counts = {}

        for result in results:
            for metric, value in result["scores"].items():
                if isinstance(value, (int, float)):
                    metric_sums[metric] = metric_sums.get(metric, 0) + value
                    metric_counts[metric] = metric_counts.get(metric, 0) + 1

        print(f"📋 Total Questions Evaluated: {len(results)}")
        print(f"📈 Average Scores:")

        for metric in sorted(metric_sums.keys()):
            avg_score = metric_sums[metric] / metric_counts[metric]
            print(f"  - {metric}: {avg_score:.3f}")

        # Category breakdown
        categories = {}
        for result in results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result["scores"].get("overall_quality", 0))

        print(f"\n📂 Performance by Category:")
        for cat, scores in categories.items():
            avg_cat_score = np.mean(scores) if scores else 0
            print(f"  - {cat}: {avg_cat_score:.3f}")

        # Save detailed results
        output_file = "batch_evaluation_results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Detailed results saved to: {output_file}")

    else:
        print("❌ No results to evaluate!")

    print("\n🎉 Batch evaluation completed!")


if __name__ == "__main__":
    import os
    openai_key = os.getenv("OPENAI_API_KEY")

    if not openai_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("Please set it with: $env:OPENAI_API_KEY='your-key-here'")
        exit(1)

    # Use mock mode by default to avoid ChromaDB issues
    run_batch_evaluation(openai_key, use_mock=True)
    run_batch_evaluation(openai_key)
