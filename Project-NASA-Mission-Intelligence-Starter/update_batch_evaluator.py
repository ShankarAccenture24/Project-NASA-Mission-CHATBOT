#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Update batch_evaluator.py to support reference answers"""

# Read the file
with open('batch_evaluator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the loop to add reference support
old_loop = '''    for i, q in enumerate(questions, 1):
        question = q["question"]
        category = q.get("category", "general")

        print(f"\\n🔍 Question {i}/{len(questions)}: {question}")
        print(f"📂 Category: {category}")'''

new_loop = '''    for i, q in enumerate(questions, 1):
        question = q["question"]
        category = q.get("category", "general")
        reference = q.get("reference", None)  # Optional reference answer for additional metrics

        print(f"\\n🔍 Question {i}/{len(questions)}: {question}")
        print(f"📂 Category: {category}")
        if reference:
            print(f"📋 Reference answer available for enhanced metrics")'''

content = content.replace(old_loop, new_loop)

# Replace the evaluate_response_quality call
old_eval = '''            # Evaluate response quality
            scores = evaluate_response_quality(
                question=question,
                answer=answer,
                contexts=contexts
            )'''

new_eval = '''            # Evaluate response quality (with optional reference answer)
            scores = evaluate_response_quality(
                question=question,
                answer=answer,
                contexts=contexts,
                reference=reference  # Pass reference for BLEU/ROUGE/Precision metrics
            )'''

content = content.replace(old_eval, new_eval)

# Replace result_entry dict
old_entry = '''            result_entry = {
                "question": question,
                "category": category,
                "answer": answer,
                "scores": scores,
                "context_length": len(context),
                "num_docs": len(contexts)
            }'''

new_entry = '''            result_entry = {
                "question": question,
                "category": category,
                "answer": answer,
                "scores": scores,
                "context_length": len(context),
                "num_docs": len(contexts),
                "has_reference": reference is not None
            }'''

content = content.replace(old_entry, new_entry)

# Write back
with open('batch_evaluator.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ Updated batch_evaluator.py to support reference answers')
