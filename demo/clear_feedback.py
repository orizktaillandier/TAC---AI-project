"""
Clear all pending feedback to start fresh
"""

import json
from pathlib import Path

def clear_feedback():
    """Clear all pending feedback"""
    feedback_file = Path("mock_data") / "pending_feedback.json"

    # Create empty feedback list
    empty_feedback = []

    # Save it
    with open(feedback_file, 'w', encoding='utf-8') as f:
        json.dump(empty_feedback, f, indent=2, ensure_ascii=False)

    print(f"[SUCCESS] Cleared all feedback from {feedback_file}")
    print("You can now submit new feedback and it will track the correct article IDs")

if __name__ == "__main__":
    clear_feedback()