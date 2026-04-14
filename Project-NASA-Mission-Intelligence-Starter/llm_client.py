import os
from typing import Dict, List
from openai import OpenAI

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system environment variables


def generate_response(
    user_message: str,
    context: str,
    conversation_history: List[Dict],
    openai_key: str = None,
    model: str = "gpt-3.5-turbo"
) -> str:
    """
    Generate response using OpenAI with context
    
    Args:
        user_message: The user's query
        context: The context to use for answering
        conversation_history: Previous conversation messages
        openai_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        model: Model to use (default: gpt-3.5-turbo)
    """
    
    # Get API key from parameter or environment variable
    if not openai_key:
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("OPENAI_API_KEY not provided. Set it as an environment variable or pass it as a parameter.")

    #  Create OpenAI Client
    client = OpenAI(api_key=openai_key)

    #  Define system prompt (NASA expert assistant)
    system_prompt = """
    You are a NASA mission intelligence assistant.

    Instructions:
    - Answer ONLY using the provided context
    - If the answer is not in the context, say "I don't know"
    - Be precise, factual, and concise
    - Do not hallucinate or assume information
    """

    #  Prepare context + user query
    context_block = f"""
    Context:
    {context}

    Question:
    {user_message}
    """

    #  Build messages list
    messages = [
        {"role": "system", "content": system_prompt}
    ]

    #  Add conversation history (if exists)
    if conversation_history:
        messages.extend(conversation_history)

    #  Add current user query with context
    messages.append({
        "role": "user",
        "content": context_block
    })

    try:
        #  Send request to OpenAI
        response = client.chat.completions.create(
            model=model,  # You can change to "gpt-4o-mini" later
            messages=messages,
            temperature=0.2,
            max_tokens=500
        )

        #  Extract response text
        answer = response.choices[0].message.content.strip()
        return answer

    except Exception as e:
        #  Basic error handling
        return f"Error generating response: {str(e)}"


if __name__ == "__main__":
    OPENAI_API_KEY="voc-570145424126677498479269d73ba36de0c3.00974578"

    try:
        response = generate_response(
            user_message="What is Apollo 11?",
            context="Apollo 11 was the first mission to land humans on the Moon in 1969.",
            conversation_history=[]
        )
        print("Response:", response)
    except ValueError as e:
        print(f"Error: {e}")
        print("\nPlease set your OpenAI API key:")
        print('$env:OPENAI_API_KEY="your-api-key"')