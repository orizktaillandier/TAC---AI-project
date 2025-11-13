"""
Generate Embeddings for KB Articles
Run this script once to generate embeddings for all existing KB articles
"""

from knowledge_base import KnowledgeBase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    print("=" * 60)
    print("  KB Embeddings Generator")
    print("=" * 60)
    print()

    kb = KnowledgeBase()

    print(f"Found {len(kb.articles)} KB articles")
    print()

    # Update all embeddings
    kb.update_all_embeddings()

    print()
    print("=" * 60)
    print("  [OK] All embeddings generated successfully!")
    print("  Semantic search is now enabled")
    print("=" * 60)


if __name__ == "__main__":
    main()
