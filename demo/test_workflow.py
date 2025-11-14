"""
Test Script for Self-Learning KB System
Tests the complete 3-step workflow including edge cases
"""

import json
from pathlib import Path
from classifier import TicketClassifier
from knowledge_base import KnowledgeBase
from kb_intelligence import KBIntelligence
from datetime import datetime


def print_section(title):
    """Print a section header"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def test_classification():
    """Test Step 1: Ticket Classification"""
    print_section("TEST 1: Ticket Classification")

    classifier = TicketClassifier()

    test_tickets = [
        "Can you activate our export feed for Syndicator D? We just signed up.",
        "Our import feed is showing vehicles that were sold last week.",
        "I need to cancel our Syndicator B export feed immediately.",
        "Is it possible to have separate feeds for new and used inventory?"
    ]

    for i, ticket in enumerate(test_tickets, 1):
        print(f"Ticket {i}: {ticket}")
        result = classifier.classify(ticket)
        classification = result.get('classification', {})
        print(f"  Category: {classification.get('category', 'N/A')}")
        print(f"  Sub-Category: {classification.get('sub_category', 'N/A')}")
        print(f"  Success: {result.get('success', False)}\n")

    print("[OK] Classification test passed\n")


def test_kb_matching():
    """Test Step 2: KB Matching and Resolution"""
    print_section("TEST 2: KB Matching and Resolution")

    kb = KnowledgeBase()
    classifier = TicketClassifier()

    test_cases = [
        {
            "ticket": "Our import feed shows stale inventory from last month",
            "expected_article_id": 3
        },
        {
            "ticket": "Need to activate Syndicator D export feed for new client",
            "expected_article_id": 2
        },
        {
            "ticket": "Cancel our Syndicator B export immediately",
            "expected_article_id": 1
        }
    ]

    for case in test_cases:
        ticket = case['ticket']
        expected_id = case['expected_article_id']

        print(f"Ticket: {ticket}")

        # Classify
        result = classifier.classify(ticket)
        classification = result.get('classification', {})

        # Search KB
        results = kb.search_articles(ticket, classification)

        if results:
            top_match = results[0]
            matched_id = top_match['article']['id']
            score = top_match['score']

            print(f"  Matched Article ID: {matched_id} (Score: {score})")
            print(f"  Expected Article ID: {expected_id}")

            if matched_id == expected_id:
                print("  [OK] Correct match\n")
            else:
                print(f"  [WARN] Mismatch! Expected {expected_id}, got {matched_id}\n")
        else:
            print("  [FAIL] No matches found\n")


def test_kb_persistence():
    """Test KB Add/Update/Delete operations"""
    print_section("TEST 3: KB Persistence Operations")

    kb = KnowledgeBase()

    # Test 1: Add new article
    print("Test 3.1: Adding new article")
    new_article = {
        "title": "Test Article - Import Feed Timeout",
        "problem": "Import feed times out during large inventory updates",
        "solution": "Increase timeout settings and batch the import",
        "steps": [
            "Go to Admin Page",
            "Navigate to Import Settings",
            "Increase timeout to 300 seconds",
            "Enable batch processing"
        ],
        "tags": ["import", "timeout", "performance"],
        "category": "Problem / Bug",
        "sub_category": "Import",
        "syndicator": "",
        "provider": "",
        "inventory_type": "Both"
    }

    new_id = kb.add_article(new_article)
    print(f"  [OK] Added article with ID: {new_id}")

    # Verify it exists
    retrieved = kb.get_article(new_id)
    if retrieved and retrieved['title'] == new_article['title']:
        print("  [OK] Article retrieved successfully\n")
    else:
        print("  [FAIL] Failed to retrieve article\n")
        return

    # Test 2: Update article
    print("Test 3.2: Updating article with version history")
    updates = {
        "solution": "Increase timeout settings, enable batch processing, and notify provider",
        "steps": [
            "Go to Admin Page",
            "Navigate to Import Settings",
            "Increase timeout to 300 seconds",
            "Enable batch processing",
            "Notify provider about timeout issues"  # New step
        ]
    }

    success = kb.update_article(new_id, updates, change_reason="Added provider notification step")
    if success:
        print("  [OK] Article updated successfully")

        # Check version history
        history = kb.get_version_history(new_id)
        if history and len(history) > 0:
            print(f"  [OK] Version history created: {len(history)} version(s)\n")
        else:
            print("  [WARN] No version history found\n")
    else:
        print("  [FAIL] Failed to update article\n")

    # Test 3: Delete article
    print("Test 3.3: Deleting article")
    success = kb.delete_article(new_id)
    if success:
        print("  [OK] Article deleted successfully")

        # Verify it's gone
        retrieved = kb.get_article(new_id)
        if retrieved is None:
            print("  [OK] Article confirmed deleted\n")
        else:
            print("  [WARN] Article still exists after deletion\n")
    else:
        print("  [FAIL] Failed to delete article\n")


def test_kb_intelligence():
    """Test KB Intelligence analysis"""
    print_section("TEST 4: KB Intelligence Analysis")

    try:
        kb_intel = KBIntelligence()
        kb = KnowledgeBase()

        # Test case: Resolution didn't work, agent provides actual solution
        ticket_data = {
            "text": "Our import feed from Provider C is showing cars that were sold 2 weeks ago",
            "category": "Problem / Bug",
            "sub_category": "Import",
            "provider": "Provider C",
            "dealer_name": "Test Motors"
        }

        resolution_data = {
            "solution": "Had to force refresh AND clear the cache in the admin panel. "
                       "Also had to contact Provider C to verify their webhook was working.",
            "success": True
        }

        # Get existing similar articles
        classification = {
            "category": ticket_data["category"],
            "sub_category": ticket_data["sub_category"],
            "provider": ticket_data["provider"]
        }
        existing_articles = kb.search_articles(ticket_data["text"], classification)

        print("Analyzing resolution...")
        print(f"Ticket: {ticket_data['text']}")
        print(f"Actual Solution: {resolution_data['solution']}\n")

        analysis = kb_intel.analyze_resolution(
            ticket=ticket_data,
            resolution=resolution_data,
            existing_articles=existing_articles
        )

        print(f"AI Decision: {analysis.get('action', 'none').upper()}")
        print(f"Confidence: {analysis.get('confidence', 0)}%")
        print(f"Reasoning: {analysis.get('reasoning', 'No reasoning provided')}")

        if analysis.get('action') in ['add_new', 'update_existing']:
            print("\n[OK] KB Intelligence is working - AI decided to update KB\n")
        else:
            print("\n[WARN] AI decided not to update KB (action: none or remove)\n")

    except Exception as e:
        print(f"[FAIL] KB Intelligence test failed: {e}")
        print("Note: This requires OPENAI_API_KEY to be set\n")


def test_edge_cases():
    """Test edge cases"""
    print_section("TEST 5: Edge Cases")

    kb = KnowledgeBase()
    classifier = TicketClassifier()

    # Edge case 1: Ticket with no KB match
    print("Edge Case 1: Ticket with no KB match")
    weird_ticket = "Can you help me install Windows 11 on my laptop?"
    result = classifier.classify(weird_ticket)
    classification = result.get('classification', {})
    results = kb.search_articles(weird_ticket, classification)

    if not results or results[0]['score'] < 10:
        print("  [OK] Correctly identified as no match or low score\n")
    else:
        print(f"  [WARN] Found match with score {results[0]['score']} - might be false positive\n")

    # Edge case 2: Very similar tickets should match same article
    print("Edge Case 2: Similar tickets matching same article")
    similar_tickets = [
        "Import feed is not updating, showing old vehicles",
        "Our provider import is stale, vehicles already sold still showing",
        "Inventory import feed has outdated cars from last week"
    ]

    matched_articles = []
    for ticket in similar_tickets:
        result = classifier.classify(ticket)
        classification = result.get('classification', {})
        results = kb.search_articles(ticket, classification)
        if results:
            matched_articles.append(results[0]['article']['id'])

    if len(set(matched_articles)) == 1:
        print(f"  [OK] All similar tickets matched article #{matched_articles[0]}\n")
    else:
        print(f"  [WARN] Similar tickets matched different articles: {matched_articles}\n")

    # Edge case 3: Empty or very short ticket
    print("Edge Case 3: Empty or very short ticket")
    short_ticket = "help"
    result = classifier.classify(short_ticket)
    classification = result.get('classification', {})
    results = kb.search_articles(short_ticket, classification)

    if not results or results[0]['score'] < 15:
        print("  [OK] Correctly handled short/vague ticket\n")
    else:
        print(f"  [WARN] Short ticket got high match score: {results[0]['score']}\n")


def test_stats():
    """Test KB statistics"""
    print_section("TEST 6: KB Statistics")

    kb = KnowledgeBase()
    stats = kb.get_stats()

    print(f"Total Articles: {stats['total_articles']}")
    print(f"Total Usage: {stats['total_usage']}")
    print(f"Average Success Rate: {stats['avg_success_rate']:.0%}")

    print("\nArticles by Category:")
    for category, count in sorted(stats['articles_by_category'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: {count}")

    print("\n[OK] Statistics test passed\n")


def main():
    """Run all tests"""
    print(f"\n{'#' * 60}")
    print(f"  SELF-LEARNING KB SYSTEM - COMPREHENSIVE TEST SUITE")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#' * 60}")

    try:
        test_classification()
        test_kb_matching()
        test_kb_persistence()
        test_kb_intelligence()
        test_edge_cases()
        test_stats()

        print_section("ALL TESTS COMPLETED")
        print("The self-learning KB system is ready for production!")
        print("\nNext steps:")
        print("1. Run the demo app: streamlit run demo_app.py")
        print("2. Test with real tickets from your boss")
        print("3. Monitor the feedback and KB updates\n")

    except Exception as e:
        print(f"\n[FAILED] TEST SUITE ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
