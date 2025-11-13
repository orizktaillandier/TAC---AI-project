"""
KB Audit Log System
Tracks all changes to the knowledge base with timestamps and user info
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class KBAuditLog:
    """Manages audit logging for all KB changes"""

    def __init__(self, log_file: str = "kb_audit_log.json"):
        self.log_file = Path("mock_data") / log_file
        self.log_entries = []
        self.load()

    def load(self):
        """Load audit log from file"""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    self.log_entries = json.load(f)
            else:
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
                self.log_entries = []
                self.save()
        except Exception as e:
            print(f"Error loading audit log: {e}")
            self.log_entries = []

    def save(self):
        """Save audit log to file"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.log_entries, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving audit log: {e}")

    def log_action(
        self,
        action: str,
        article_id: Optional[int],
        user: str,
        details: Dict[str, Any],
        feedback_id: Optional[int] = None
    ):
        """
        Log a KB action

        Args:
            action: Type of action (create, update, delete, rollback, etc.)
            article_id: ID of article affected (None for new articles)
            user: User who performed the action
            details: Additional details about the change
            feedback_id: Associated feedback item ID if applicable
        """
        log_entry = {
            'id': len(self.log_entries) + 1,
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'article_id': article_id,
            'user': user,
            'feedback_id': feedback_id,
            'details': details
        }

        self.log_entries.append(log_entry)
        self.save()
        return log_entry['id']

    def get_recent_actions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent audit log entries"""
        return list(reversed(self.log_entries[-limit:]))

    def get_article_history(self, article_id: int) -> List[Dict[str, Any]]:
        """Get all actions for a specific article"""
        return [
            entry for entry in self.log_entries
            if entry.get('article_id') == article_id
        ]

    def get_user_actions(self, user: str) -> List[Dict[str, Any]]:
        """Get all actions by a specific user"""
        return [
            entry for entry in self.log_entries
            if entry.get('user') == user
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get audit log statistics"""
        if not self.log_entries:
            return {
                'total_actions': 0,
                'actions_by_type': {},
                'most_active_user': None,
                'most_modified_article': None
            }

        # Count actions by type
        actions_by_type = {}
        users = {}
        articles = {}

        for entry in self.log_entries:
            # Count by action type
            action = entry.get('action', 'unknown')
            actions_by_type[action] = actions_by_type.get(action, 0) + 1

            # Count by user
            user = entry.get('user', 'unknown')
            users[user] = users.get(user, 0) + 1

            # Count by article
            article_id = entry.get('article_id')
            if article_id:
                articles[article_id] = articles.get(article_id, 0) + 1

        # Find most active user
        most_active_user = max(users.items(), key=lambda x: x[1])[0] if users else None

        # Find most modified article
        most_modified_article = max(articles.items(), key=lambda x: x[1])[0] if articles else None

        return {
            'total_actions': len(self.log_entries),
            'actions_by_type': actions_by_type,
            'most_active_user': most_active_user,
            'most_modified_article': most_modified_article,
            'unique_users': len(users),
            'unique_articles': len(articles)
        }

    def export_to_csv(self, filename: str = "kb_audit_log.csv"):
        """Export audit log to CSV for reporting"""
        import csv

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            if self.log_entries:
                writer = csv.DictWriter(f, fieldnames=self.log_entries[0].keys())
                writer.writeheader()
                writer.writerows(self.log_entries)
        return filename


# Singleton instance
_audit_log = None


def get_audit_log() -> KBAuditLog:
    """Get the singleton audit log instance"""
    global _audit_log
    if _audit_log is None:
        _audit_log = KBAuditLog()
    return _audit_log