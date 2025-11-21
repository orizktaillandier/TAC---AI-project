"""
Gap Analysis System for Knowledge Base
Tracks search patterns and identifies knowledge gaps
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)


class GapAnalyzer:
    """Analyzes KB searches to identify knowledge gaps and patterns"""
    
    def __init__(self, analytics_file: str = "search_analytics.json"):
        """Initialize gap analyzer"""
        self.analytics_file = Path(__file__).parent / "mock_data" / analytics_file
        self.search_logs: List[Dict[str, Any]] = []
        self.load()
    
    def load(self):
        """Load search analytics from file"""
        try:
            if self.analytics_file.exists():
                with open(self.analytics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.search_logs = data.get('searches', [])
                logger.debug(f"Loaded {len(self.search_logs)} search logs")
            else:
                self.search_logs = []
                self.save()
        except Exception as e:
            logger.error(f"Error loading search analytics: {e}")
            self.search_logs = []
    
    def save(self):
        """Save search analytics to file"""
        try:
            self.analytics_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                'searches': self.search_logs,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.analytics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving search analytics: {e}")
    
    def log_search(self, query: str, results_found: bool, 
                   article_id: Optional[int] = None, 
                   result_count: int = 0,
                   classification: Optional[Dict[str, Any]] = None):
        """
        Log a search query
        
        Args:
            query: Search query text
            results_found: Whether results were found
            article_id: ID of article used (if any)
            result_count: Number of results found
            classification: Ticket classification context (if available)
        """
        log_entry = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'results_found': results_found,
            'article_id': article_id,
            'result_count': result_count,
            'classification': classification or {},
            'success': None  # Will be updated after resolution
        }
        
        self.search_logs.append(log_entry)
        
        # Keep only last 1000 entries to prevent file from growing too large
        if len(self.search_logs) > 1000:
            self.search_logs = self.search_logs[-1000:]
        
        self.save()
        logger.debug(f"Logged search: query='{query[:50]}...', found={results_found}")
    
    def update_search_success(self, query: str, success: bool):
        """Update success status for recent searches matching query"""
        # Update most recent matching search
        for log in reversed(self.search_logs):
            if log['query'] == query and log['success'] is None:
                log['success'] = success
                self.save()
                break
    
    def get_failed_searches(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get searches that found no results (knowledge gaps)
        
        Args:
            days: Number of days to look back
        
        Returns:
            List of failed search entries
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        failed = []
        for log in self.search_logs:
            log_date = datetime.fromisoformat(log['timestamp'])
            if log_date >= cutoff_date and not log['results_found']:
                failed.append(log)
        
        return failed
    
    def get_most_searched_topics(self, days: int = 30, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get most frequently searched topics
        
        Args:
            days: Number of days to look back
            limit: Maximum number of topics to return
        
        Returns:
            List of topics with search counts
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query_counts = Counter()
        for log in self.search_logs:
            log_date = datetime.fromisoformat(log['timestamp'])
            if log_date >= cutoff_date:
                query_counts[log['query'].lower().strip()] += 1
        
        return [
            {'query': query, 'count': count}
            for query, count in query_counts.most_common(limit)
        ]
    
    def get_knowledge_gaps(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Identify knowledge gaps (failed searches with frequency)
        
        Args:
            days: Number of days to analyze
        
        Returns:
            List of knowledge gaps sorted by frequency
        """
        failed_searches = self.get_failed_searches(days)
        
        # Count frequency of each failed query
        gap_counts = Counter()
        gap_details = defaultdict(list)
        
        for search in failed_searches:
            query = search['query'].lower().strip()
            gap_counts[query] += 1
            gap_details[query].append({
                'timestamp': search['timestamp'],
                'classification': search.get('classification', {})
            })
        
        # Build gap analysis
        gaps = []
        for query, count in gap_counts.most_common():
            gaps.append({
                'query': query,
                'frequency': count,
                'first_seen': min([d['timestamp'] for d in gap_details[query]]),
                'last_seen': max([d['timestamp'] for d in gap_details[query]]),
                'classifications': [
                    d['classification'].get('category', 'Unknown')
                    for d in gap_details[query]
                    if d.get('classification')
                ],
                'priority': 'high' if count >= 3 else 'medium' if count >= 2 else 'low'
            })
        
        return gaps
    
    def get_search_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive search analytics
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with analytics data
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_logs = [
            log for log in self.search_logs
            if datetime.fromisoformat(log['timestamp']) >= cutoff_date
        ]
        
        if not recent_logs:
            return {
                'total_searches': 0,
                'successful_searches': 0,
                'failed_searches': 0,
                'success_rate': 0,
                'avg_results_per_search': 0,
                'knowledge_gaps': []
            }
        
        total = len(recent_logs)
        successful = sum(1 for log in recent_logs if log['results_found'])
        failed = total - successful
        success_rate = (successful / total * 100) if total > 0 else 0
        
        # Calculate average results
        results_with_count = [log for log in recent_logs if log.get('result_count', 0) > 0]
        avg_results = (
            sum(log['result_count'] for log in results_with_count) / len(results_with_count)
            if results_with_count else 0
        )
        
        # Get knowledge gaps
        gaps = self.get_knowledge_gaps(days)
        
        return {
            'total_searches': total,
            'successful_searches': successful,
            'failed_searches': failed,
            'success_rate': round(success_rate, 2),
            'avg_results_per_search': round(avg_results, 2),
            'knowledge_gaps': gaps[:10],  # Top 10 gaps
            'most_searched': self.get_most_searched_topics(days, limit=10)
        }
    
    def get_trends(self, days: int = 7) -> Dict[str, Any]:
        """
        Get search trends over time
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with daily trends
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        daily_stats = defaultdict(lambda: {'total': 0, 'successful': 0, 'failed': 0})
        
        for log in self.search_logs:
            log_date = datetime.fromisoformat(log['timestamp'])
            if log_date >= cutoff_date:
                date_key = log_date.strftime('%Y-%m-%d')
                daily_stats[date_key]['total'] += 1
                if log['results_found']:
                    daily_stats[date_key]['successful'] += 1
                else:
                    daily_stats[date_key]['failed'] += 1
        
        # Convert to list sorted by date
        trends = []
        for date in sorted(daily_stats.keys()):
            stats = daily_stats[date]
            trends.append({
                'date': date,
                'total': stats['total'],
                'successful': stats['successful'],
                'failed': stats['failed'],
                'success_rate': round((stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0, 2)
            })
        
        return {
            'period_days': days,
            'daily_trends': trends,
            'avg_daily_searches': round(sum(s['total'] for s in trends) / len(trends) if trends else 0, 2)
        }

