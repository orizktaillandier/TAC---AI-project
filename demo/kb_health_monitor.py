"""
KB Health Monitoring System
Tracks KB performance and detects declining success rates
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List
from knowledge_base import KnowledgeBase
from feedback_manager import FeedbackManager


class KBHealthMonitor:
    """Monitors KB health metrics and detects performance issues"""

    def __init__(self):
        self.kb = KnowledgeBase()
        self.feedback_manager = FeedbackManager()

    def get_health_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive KB health report

        Returns:
            Health report with metrics and warnings
        """
        report = {
            "overall_health": "Good",
            "total_articles": len(self.kb.articles),
            "metrics": self._calculate_metrics(),
            "warnings": [],
            "recommendations": [],
            "timestamp": datetime.now().isoformat()
        }

        # Detect issues
        warnings = self._detect_issues(report["metrics"])
        report["warnings"] = warnings

        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(warnings, report["metrics"])

        # Determine overall health
        if any(w.get("severity") == "Critical" for w in warnings):
            report["overall_health"] = "Critical"
        elif any(w.get("severity") == "High" for w in warnings):
            report["overall_health"] = "Poor"
        elif any(w.get("severity") == "Medium" for w in warnings):
            report["overall_health"] = "Fair"

        return report

    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate current KB metrics"""
        metrics = {
            "overall_success_rate": 0.0,
            "total_usage": 0,
            "articles_by_category": {},
            "success_by_category": {},
            "low_performing_articles": [],
            "unused_articles": [],
            "high_performing_articles": []
        }

        if not self.kb.articles:
            return metrics

        # Calculate overall metrics
        total_success = 0
        total_usage = 0

        for article in self.kb.articles:
            usage = article.get("usage_count", 0)
            success_count = article.get("success_count", 0)
            success_rate = article.get("success_rate", 0.0)
            category = article.get("category", "Unknown")

            total_usage += usage
            total_success += success_count

            # Track by category
            if category not in metrics["articles_by_category"]:
                metrics["articles_by_category"][category] = {
                    "count": 0,
                    "total_usage": 0,
                    "total_success": 0
                }

            metrics["articles_by_category"][category]["count"] += 1
            metrics["articles_by_category"][category]["total_usage"] += usage
            metrics["articles_by_category"][category]["total_success"] += success_count

            # Identify problem articles
            if usage >= 3 and success_rate < 0.5:
                metrics["low_performing_articles"].append({
                    "id": article.get("id"),
                    "title": article.get("title"),
                    "success_rate": success_rate,
                    "usage_count": usage,
                    "category": category
                })

            # Identify unused articles
            if usage == 0:
                age_days = self._get_article_age_days(article)
                if age_days > 30:  # Unused for more than 30 days
                    metrics["unused_articles"].append({
                        "id": article.get("id"),
                        "title": article.get("title"),
                        "age_days": age_days,
                        "category": category
                    })

            # Identify high performers
            if usage >= 5 and success_rate >= 0.8:
                metrics["high_performing_articles"].append({
                    "id": article.get("id"),
                    "title": article.get("title"),
                    "success_rate": success_rate,
                    "usage_count": usage,
                    "category": category
                })

        # Calculate overall success rate
        if total_usage > 0:
            metrics["overall_success_rate"] = total_success / total_usage
        metrics["total_usage"] = total_usage

        # Calculate success rate by category
        for category, data in metrics["articles_by_category"].items():
            if data["total_usage"] > 0:
                metrics["success_by_category"][category] = {
                    "success_rate": data["total_success"] / data["total_usage"],
                    "usage_count": data["total_usage"]
                }

        return metrics

    def _detect_issues(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect KB health issues"""
        warnings = []

        # Check overall success rate
        overall_sr = metrics.get("overall_success_rate", 0)
        if overall_sr < 0.5 and metrics.get("total_usage", 0) >= 10:
            warnings.append({
                "severity": "Critical",
                "type": "low_overall_success",
                "message": f"Overall KB success rate is critically low: {overall_sr:.0%}",
                "metric": overall_sr,
                "threshold": 0.5
            })
        elif overall_sr < 0.7 and metrics.get("total_usage", 0) >= 10:
            warnings.append({
                "severity": "High",
                "type": "declining_success",
                "message": f"Overall KB success rate needs improvement: {overall_sr:.0%}",
                "metric": overall_sr,
                "threshold": 0.7
            })

        # Check for categories with low success rates
        for category, data in metrics.get("success_by_category", {}).items():
            sr = data.get("success_rate", 0)
            usage = data.get("usage_count", 0)

            if usage >= 5 and sr < 0.5:
                warnings.append({
                    "severity": "High",
                    "type": "category_low_success",
                    "message": f"Category '{category}' has low success rate: {sr:.0%} ({usage} uses)",
                    "category": category,
                    "metric": sr,
                    "threshold": 0.5
                })

        # Check for too many low-performing articles
        low_perf_count = len(metrics.get("low_performing_articles", []))
        total_articles = metrics.get("total_articles", 1)
        if low_perf_count / total_articles > 0.3:  # More than 30% are low performing
            warnings.append({
                "severity": "Medium",
                "type": "many_low_performers",
                "message": f"{low_perf_count} articles ({low_perf_count/total_articles:.0%}) have low success rates",
                "metric": low_perf_count
            })

        # Check for unused articles
        unused_count = len(metrics.get("unused_articles", []))
        if unused_count / total_articles > 0.2:  # More than 20% unused
            warnings.append({
                "severity": "Low",
                "type": "many_unused",
                "message": f"{unused_count} articles ({unused_count/total_articles:.0%}) haven't been used in 30+ days",
                "metric": unused_count
            })

        return warnings

    def _generate_recommendations(self, warnings: List[Dict[str, Any]], metrics: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on warnings"""
        recommendations = []

        for warning in warnings:
            warning_type = warning.get("type")

            if warning_type == "low_overall_success":
                recommendations.append("🔴 URGENT: Review and update KB articles. Over 50% of resolutions are failing.")
                recommendations.append("Consider running an audit of all articles to identify outdated information.")

            elif warning_type == "declining_success":
                recommendations.append("⚠️ KB effectiveness declining. Schedule a review of top-used articles.")
                recommendations.append("Check if recent product changes made existing articles obsolete.")

            elif warning_type == "category_low_success":
                category = warning.get("category", "Unknown")
                recommendations.append(f"Review all '{category}' articles - this category is underperforming.")

            elif warning_type == "many_low_performers":
                recommendations.append("Multiple articles need updates. Prioritize by usage count.")
                recommendations.append("Consider using agent feedback to improve these articles.")

            elif warning_type == "many_unused":
                recommendations.append("Archive or update unused articles to keep KB focused and current.")

        # Add positive recommendations for high performers
        high_perf = metrics.get("high_performing_articles", [])
        if high_perf:
            top_article = max(high_perf, key=lambda x: x.get("usage_count", 0))
            recommendations.append(f"✅ Best performing article: '{top_article.get('title')}' - use as template for others.")

        return recommendations

    def _get_article_age_days(self, article: Dict[str, Any]) -> int:
        """Calculate how many days since article was created"""
        created_at = article.get("created_at")
        if not created_at:
            return 0

        try:
            created = datetime.fromisoformat(created_at)
            age = datetime.now() - created
            return age.days
        except:
            return 0

    def get_critical_alerts(self) -> List[Dict[str, Any]]:
        """Get only critical/high severity warnings"""
        report = self.get_health_report()
        return [w for w in report.get("warnings", []) if w.get("severity") in ["Critical", "High"]]


# Singleton instance
_health_monitor = None


def get_health_monitor() -> KBHealthMonitor:
    """Get the singleton health monitor instance"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = KBHealthMonitor()
    return _health_monitor
