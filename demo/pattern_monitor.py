"""
Pattern Monitoring System
Detects patterns across tickets and caches results for performance
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List
from proactive_detection import ProactiveDetection
from feedback_manager import FeedbackManager
from knowledge_base import KnowledgeBase


class PatternMonitor:
    """Monitors and caches pattern detection results"""

    def __init__(self, cache_file: str = "pattern_cache.json", cache_duration_minutes: int = 15):
        self.cache_file = Path("mock_data") / cache_file
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
        self.detector = ProactiveDetection()
        self.feedback_manager = FeedbackManager()
        self.kb = KnowledgeBase()
        self.cached_patterns = None
        self.cache_timestamp = None

    def get_patterns(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get pattern analysis, using cache if available and fresh

        Args:
            force_refresh: Force re-analysis even if cache is valid

        Returns:
            Pattern analysis results
        """
        # Check if cache is valid
        if not force_refresh and self._is_cache_valid():
            return self.cached_patterns

        # Run fresh analysis
        patterns = self._analyze_patterns()

        # Update cache
        self.cached_patterns = patterns
        self.cache_timestamp = datetime.now()
        self._save_cache()

        return patterns

    def _is_cache_valid(self) -> bool:
        """Check if cached patterns are still valid"""
        if self.cached_patterns is None or self.cache_timestamp is None:
            # Try loading from file
            if not self._load_cache():
                return False

        # Check if cache is expired
        age = datetime.now() - self.cache_timestamp
        return age < self.cache_duration

    def _analyze_patterns(self) -> Dict[str, Any]:
        """Run pattern analysis on recent tickets"""
        # Gather tickets from multiple sources
        tickets = []

        # 1. Get feedback tickets (these have failed KB resolutions)
        feedback_items = self.feedback_manager.get_pending()
        for item in feedback_items:
            ticket_data = item.get("ticket_data", {})
            tickets.append({
                "ticket_id": ticket_data.get("ticket_id", f"feedback_{item.get('id')}"),
                "text": ticket_data.get("text", ""),
                "classification": {
                    "category": ticket_data.get("category"),
                    "sub_category": ticket_data.get("sub_category"),
                    "syndicator": ticket_data.get("syndicator"),
                    "provider": ticket_data.get("provider"),
                    "dealer_name": ticket_data.get("dealer_name"),
                    "tier": "Tier 3"  # Feedback tickets are high priority
                },
                "timestamp": item.get("timestamp"),
                "resolution_status": "failed"
            })

        # 2. Get resolved tickets
        resolved_file = Path("mock_data") / "resolved_tickets.json"
        if resolved_file.exists():
            with open(resolved_file, 'r', encoding='utf-8') as f:
                resolved_tickets = json.load(f)
                for rt in resolved_tickets:
                    ticket = rt.get("ticket", {})
                    tickets.append({
                        "ticket_id": ticket.get("ticket_id", ""),
                        "text": ticket.get("text", ""),
                        "classification": ticket.get("classification", {}),
                        "timestamp": ticket.get("timestamp", datetime.now().isoformat()),
                        "resolution_status": "resolved"
                    })

        # 3. Analyze KB coverage gaps (low confidence matches)
        kb_gaps = self._detect_kb_gaps()

        # Run pattern detection
        pattern_analysis = self.detector.analyze_patterns(tickets)

        # Add KB gap analysis
        pattern_analysis["kb_gaps"] = kb_gaps

        # Add summary statistics
        pattern_analysis["summary"] = {
            "total_tickets_analyzed": len(tickets),
            "total_patterns_detected": len(pattern_analysis.get("patterns", [])),
            "kb_gaps_found": len(kb_gaps),
            "analysis_timestamp": datetime.now().isoformat()
        }

        return pattern_analysis

    def _detect_kb_gaps(self) -> List[Dict[str, Any]]:
        """Detect areas where KB coverage is weak"""
        gaps = []

        # Check KB article success rates
        for article in self.kb.articles:
            success_rate = article.get("success_rate", 1.0)
            usage_count = article.get("usage_count", 0)

            # Flag articles with low success rates and decent usage
            if success_rate < 0.5 and usage_count >= 3:
                gaps.append({
                    "type": "low_success_rate",
                    "article_id": article.get("id"),
                    "article_title": article.get("title"),
                    "success_rate": success_rate,
                    "usage_count": usage_count,
                    "category": article.get("category"),
                    "recommendation": f"Article '{article.get('title')}' has only {success_rate:.0%} success rate. Consider updating or replacing."
                })

        # Check for categories with no articles
        feedback_categories = {}
        for item in self.feedback_manager.get_pending():
            cat = item["ticket_data"].get("category", "Unknown")
            sub_cat = item["ticket_data"].get("sub_category", "Unknown")
            key = f"{cat} → {sub_cat}"
            feedback_categories[key] = feedback_categories.get(key, 0) + 1

        # Check if KB has articles for these categories
        kb_categories = set()
        for article in self.kb.articles:
            cat = article.get("category", "Unknown")
            sub_cat = article.get("sub_category", "Unknown")
            kb_categories.add(f"{cat} → {sub_cat}")

        for category_key, count in feedback_categories.items():
            if category_key not in kb_categories and count >= 2:
                gaps.append({
                    "type": "missing_coverage",
                    "category": category_key,
                    "ticket_count": count,
                    "recommendation": f"No KB articles found for '{category_key}' but {count} tickets need help. Consider creating new article."
                })

        return gaps

    def _save_cache(self):
        """Save pattern cache to file"""
        try:
            cache_data = {
                "patterns": self.cached_patterns,
                "timestamp": self.cache_timestamp.isoformat() if self.cache_timestamp else None
            }
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving pattern cache: {e}")

    def _load_cache(self) -> bool:
        """Load pattern cache from file"""
        try:
            if not self.cache_file.exists():
                return False

            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            self.cached_patterns = cache_data.get("patterns")
            timestamp_str = cache_data.get("timestamp")
            if timestamp_str:
                self.cache_timestamp = datetime.fromisoformat(timestamp_str)
                return True

            return False
        except Exception as e:
            print(f"Error loading pattern cache: {e}")
            return False

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active high-priority pattern alerts"""
        patterns = self.get_patterns()
        alerts = []

        # Extract critical patterns
        for pattern in patterns.get("patterns", []):
            severity = pattern.get("severity", "Low")
            if severity in ["High", "Critical"]:
                alerts.append({
                    "type": pattern.get("pattern_type"),
                    "severity": severity,
                    "message": pattern.get("description"),
                    "ticket_count": pattern.get("affected_tickets_count", 0),
                    "recommendation": pattern.get("recommendation")
                })

        # Add KB gap alerts
        for gap in patterns.get("kb_gaps", []):
            if gap.get("type") == "missing_coverage":
                alerts.append({
                    "type": "kb_gap",
                    "severity": "Medium",
                    "message": f"KB gap detected: {gap.get('category')}",
                    "ticket_count": gap.get("ticket_count", 0),
                    "recommendation": gap.get("recommendation")
                })

        return alerts


# Singleton instance
_pattern_monitor = None


def get_pattern_monitor() -> PatternMonitor:
    """Get the singleton pattern monitor instance"""
    global _pattern_monitor
    if _pattern_monitor is None:
        _pattern_monitor = PatternMonitor()
    return _pattern_monitor
