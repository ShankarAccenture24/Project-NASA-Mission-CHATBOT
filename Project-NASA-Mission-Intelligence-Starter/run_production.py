#!/usr/bin/env python3
"""
NASA RAG Chat Production Runner

This script provides an easy way to run the complete NASA RAG Chat pipeline
from data processing to interactive chat interface.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_modules = [
        'streamlit', 'chromadb', 'openai', 'pandas'
    ]

    missing = []
    for module in required_modules:
        try:
            __import__(module.replace('_', '-'))
        except ImportError:
            missing.append(module)

    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False

    print("✅ All dependencies installed")
    return True

def setup_environment():
    """Set up the environment variables"""
    if not os.getenv("OPENAI_API_KEY"):
        api_key = input("Enter your OpenAI API key: ").strip()
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            print("✅ API key set")
        else:
            print("❌ No API key provided")
            return False
    else:
        print("✅ API key already set")

    return True

def run_embedding_pipeline(data_path: str, openai_key: str):
    """Run the embedding pipeline to process NASA data"""
    print("\n🚀 Running Embedding Pipeline...")

    cmd = [
        sys.executable, "embedding_pipeline.py",
        "--openai-key", openai_key,
        "--data-path", data_path,
        "--chroma-dir", "./chroma_db_nasa",
        "--collection-name", "nasa_space_missions_text"
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Embedding pipeline completed successfully")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Embedding pipeline failed: {e}")
        print(e.stdout)
        print(e.stderr)
        return False

def run_chat_interface():
    """Run the Streamlit chat interface"""
    print("\n💬 Starting Chat Interface...")

    cmd = [sys.executable, "-m", "streamlit", "run", "chat.py"]

    try:
        print("🌐 Chat interface will open in your browser")
        print("Press Ctrl+C to stop the server")
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Chat interface stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Chat interface failed: {e}")
        return False

    return True

def main():
    parser = argparse.ArgumentParser(description="NASA RAG Chat Production Runner")
    parser.add_argument("--data-path", default="./data_text",
                       help="Path to NASA data directory")
    parser.add_argument("--skip-embedding", action="store_true",
                       help="Skip embedding pipeline (use existing database)")
    parser.add_argument("--only-embedding", action="store_true",
                       help="Only run embedding pipeline, don't start chat")

    args = parser.parse_args()

    print("🚀 NASA RAG Chat Production Runner")
    print("=" * 50)

    # Check dependencies
    if not check_dependencies():
        return 1

    # Setup environment
    if not setup_environment():
        return 1

    openai_key = os.getenv("OPENAI_API_KEY")

    # Check if data directory exists
    data_path = Path(args.data_path)
    if not data_path.exists() and not args.skip_embedding:
        print(f"❌ Data directory not found: {data_path}")
        print("Please ensure NASA data is available in the data_text directory")
        return 1

    # Run embedding pipeline
    if not args.skip_embedding:
        if not run_embedding_pipeline(str(data_path), openai_key):
            return 1
    else:
        print("⏭️  Skipping embedding pipeline (using existing database)")

    # Run chat interface
    if not args.only_embedding:
        if not run_chat_interface():
            return 1

    print("\n🎉 Production setup complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())