#!/usr/bin/env python3
"""
Minimal NASA RAG Chat - No complex dependencies
"""

import os
import sys
from pathlib import Path

def main():
    print("🚀 Minimal NASA RAG Chat System")
    print("=" * 40)

    # Check basic imports
    try:
        import streamlit
        import chromadb
        import openai
        print("✅ Core dependencies available")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install streamlit chromadb openai")
        return 1

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        print("Run: $env:OPENAI_API_KEY='your-key-here'")
        return 1

    print("✅ API key configured")

    # Check data directory
    data_dir = Path("./data_text")
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        print("Make sure NASA data files are in ./data_text/")
        return 1

    print("✅ Data directory found")

    # Try to run embedding pipeline (skip if it fails)
    print("\n📊 Checking embedding pipeline...")
    try:
        # Simple test without importing the full pipeline
        import chromadb
        client = chromadb.PersistentClient(path="./chroma_db_minimal")
        collection = client.get_or_create_collection("nasa_missions_minimal")
        doc_count = collection.count()
        print(f"✅ Database ready (existing: {doc_count} documents)")

        if doc_count == 0:
            print("⚠️  No documents found. Run embedding pipeline manually:")
            print("python embedding_pipeline.py --openai-key YOUR_KEY --data-path ./data_text")

    except Exception as e:
        print(f"⚠️  Database check failed: {e}")
        print("Run embedding pipeline manually if needed")

    # Try to run chat interface
    print("\n💬 Starting chat interface...")
    try:
        import subprocess
        print("🌐 Open http://localhost:8501 in your browser")
        print("Press Ctrl+C to stop")

        # Run streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", "chat.py"],
                      check=True)

    except KeyboardInterrupt:
        print("\n👋 Chat interface stopped")
    except Exception as e:
        print(f"❌ Chat interface failed: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())