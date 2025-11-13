"""
Feedback Manager - Handles pending feedback storage and retrieval
Collects agent feedback for later audit instead of immediate KB updates
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class FeedbackManager:
    """Manages pending feedback from agents about KB article performance"""

    def __init__(self, feedback_file: str = "pending_feedback.json"):
        """Initialize feedback manager with persistent storage"""
        self.feedback_file = Path(__file__).parent / "mock_data" / feedback_file
        self.feedback_items: List[Dict[str, Any]] = []
        self.load()

    def load(self):
        """Load pending feedback from file"""
        try:
            if self.feedback_file.exists():
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    self.feedback_items = json.load(f)
            else:
                # Ensure directory exists
                self.feedback_file.parent.mkdir(parents=True, exist_ok=True)
                self.feedback_items = []
                self.save()
        except Exception as e:
            print(f"Error loading feedback: {e}")
            self.feedback_items = []

    def save(self):
        """Save pending feedback to file"""
        try:
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_items, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving feedback: {e}")

    def add_feedback(
        self,
        ticket_data: Dict[str, Any],
        matched_article_id: Optional[int],
        agent_feedback: Dict[str, Any],
        resolution_worked: bool
    ) -> int:
        """
        Add new feedback item

        Args:
            ticket_data: Original ticket information
            matched_article_id: ID of KB article that was suggested (or None if no match)
            agent_feedback: Dict with 'actual_solution', 'edge_case', 'agent_name'
            resolution_worked: Whether the suggested resolution worked

        Returns:
            ID of the new feedback item
        """
        # Generate ID
        feedback_id = max([f.get('id', 0) for f in self.feedback_items], default=0) + 1

        feedback_item = {
            'id': feedback_id,
            'timestamp': datetime.now().isoformat(),
            'ticket_data': {
                'ticket_id': ticket_data.get('ticket_id'),
                'subject': ticket_data.get('subject', ''),
                'text': ticket_data.get('text', ''),
                'category': ticket_data.get('category'),
                'sub_category': ticket_data.get('sub_category'),
                'syndicator': ticket_data.get('syndicator', ''),
                'provider': ticket_data.get('provider', ''),
                'dealer_name': ticket_data.get('dealer_name', '')
            },
            'matched_article_id': matched_article_id,
            'resolution_worked': resolution_worked,
            'agent_feedback': {
                'actual_solution': agent_feedback.get('actual_solution', ''),
                'edge_case': agent_feedback.get('edge_case', ''),
                'agent_name': agent_feedback.get('agent_name', 'Unknown')
            },
            'status': 'pending',  # pending, reviewed, applied, dismissed
            'audit_notes': '',
            'ai_recommendation': None  # Will be filled during audit
        }

        self.feedback_items.append(feedback_item)
        self.save()
        return feedback_id

    def get_feedback(self, feedback_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific feedback item by ID"""
        for item in self.feedback_items:
            if item.get('id') == feedback_id:
                return item
        return None

    def get_pending_feedback(self) -> List[Dict[str, Any]]:
        """Get all pending feedback items"""
        return [f for f in self.feedback_items if f.get('status') == 'pending']

    def get_feedback_by_article(self, article_id: int) -> List[Dict[str, Any]]:
        """Get all feedback for a specific KB article"""
        return [
            f for f in self.feedback_items
            if f.get('matched_article_id') == article_id
        ]

    def get_feedback_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get feedback items by status (pending, reviewed, applied, dismissed)"""
        return [f for f in self.feedback_items if f.get('status') == status]

    def update_feedback_status(
        self,
        feedback_id: int,
        status: str,
        audit_notes: str = '',
        ai_recommendation: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update the status of a feedback item"""
        for item in self.feedback_items:
            if item.get('id') == feedback_id:
                item['status'] = status
                item['audit_notes'] = audit_notes
                if ai_recommendation:
                    item['ai_recommendation'] = ai_recommendation
                item['reviewed_at'] = datetime.now().isoformat()
                self.save()
                return True
        return False

    def update_ai_recommendation(self, feedback_id: int, recommendation: Dict[str, Any]) -> bool:
        """
        Update the AI recommendation for a feedback item

        Args:
            feedback_id: ID of the feedback item
            recommendation: AI recommendation dictionary with action, confidence, reasoning, etc.

        Returns:
            True if updated successfully, False otherwise
        """
        for item in self.feedback_items:
            if item.get('id') == feedback_id:
                item['ai_recommendation'] = recommendation
                item['recommendation_generated_at'] = datetime.now().isoformat()
                self.save()
                return True
        return False

    def delete_feedback(self, feedback_id: int) -> bool:
        """Delete a feedback item"""
        original_len = len(self.feedback_items)
        self.feedback_items = [f for f in self.feedback_items if f.get('id') != feedback_id]
        if len(self.feedback_items) < original_len:
            self.save()
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get feedback statistics"""
        total = len(self.feedback_items)
        if total == 0:
            return {
                'total_feedback': 0,
                'pending': 0,
                'reviewed': 0,
                'applied': 0,
                'dismissed': 0,
                'by_status': {},
                'most_reported_articles': [],
                'resolution_success_rate': 0
            }

        status_counts = {}
        for item in self.feedback_items:
            status = item.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1

        # Count by article
        article_feedback_counts = {}
        for item in self.feedback_items:
            article_id = item.get('matched_article_id')
            if article_id:
                article_feedback_counts[article_id] = article_feedback_counts.get(article_id, 0) + 1

        # Find most reported articles
        most_reported = sorted(
            article_feedback_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            'total_feedback': total,
            'pending': status_counts.get('pending', 0),
            'reviewed': status_counts.get('reviewed', 0),
            'applied': status_counts.get('applied', 0),
            'dismissed': status_counts.get('dismissed', 0),
            'by_status': status_counts,
            'most_reported_articles': most_reported,
            'resolution_success_rate': sum(1 for f in self.feedback_items if f.get('resolution_worked')) / total if total > 0 else 0
        }

    def group_by_article(self) -> Dict[int, List[Dict[str, Any]]]:
        """Group feedback items by article ID"""
        grouped = {}
        for item in self.feedback_items:
            article_id = item.get('matched_article_id')
            if article_id:
                if article_id not in grouped:
                    grouped[article_id] = []
                grouped[article_id].append(item)
        return grouped

    def clear_processed_feedback(self, older_than_days: int = 30):
        """Clear feedback that has been processed and is older than X days"""
        cutoff_date = datetime.now().timestamp() - (older_than_days * 24 * 60 * 60)

        self.feedback_items = [
            f for f in self.feedback_items
            if f.get('status') == 'pending' or
            datetime.fromisoformat(f.get('timestamp', datetime.now().isoformat())).timestamp() > cutoff_date
        ]
        self.save()
