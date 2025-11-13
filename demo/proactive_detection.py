"""
Proactive Issue Detection System
Identifies system-wide patterns and potential outages before they escalate
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import json


class ProactiveIssueDetector:
    """Detects system-wide patterns and potential issues from ticket analysis"""

    def __init__(self):
        self.issue_threshold = 3  # Number of similar tickets to trigger alert
        self.time_window_hours = 24  # Time window for pattern detection

    def analyze_patterns(self, tickets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze tickets to identify system-wide patterns and potential issues

        Args:
            tickets: List of classified tickets with metadata

        Returns:
            Dictionary containing detected patterns and alerts
        """
        patterns = {
            "system_wide_issues": [],
            "syndicator_outages": [],
            "provider_issues": [],
            "feature_problems": [],
            "spike_alerts": [],
            "summary": {
                "total_patterns": 0,
                "critical_alerts": 0,
                "affected_dealers": 0
            }
        }

        if not tickets:
            return patterns

        # Detect syndicator-related issues
        syndicator_issues = self._detect_syndicator_issues(tickets)
        if syndicator_issues:
            patterns["syndicator_outages"].extend(syndicator_issues)
            patterns["summary"]["critical_alerts"] += len(syndicator_issues)

        # Detect provider/import issues
        provider_issues = self._detect_provider_issues(tickets)
        if provider_issues:
            patterns["provider_issues"].extend(provider_issues)
            patterns["summary"]["critical_alerts"] += len(provider_issues)

        # Detect feature-specific problems
        feature_issues = self._detect_feature_issues(tickets)
        if feature_issues:
            patterns["feature_problems"].extend(feature_issues)

        # Detect ticket volume spikes
        spike_alerts = self._detect_volume_spikes(tickets)
        if spike_alerts:
            patterns["spike_alerts"].extend(spike_alerts)

        # Calculate summary
        patterns["summary"]["total_patterns"] = (
            len(patterns["syndicator_outages"]) +
            len(patterns["provider_issues"]) +
            len(patterns["feature_problems"]) +
            len(patterns["spike_alerts"])
        )

        # Count unique affected dealers
        all_dealers = set()
        for issue_list in [patterns["syndicator_outages"], patterns["provider_issues"],
                          patterns["feature_problems"]]:
            for issue in issue_list:
                all_dealers.update(issue.get("affected_dealers", []))
        patterns["summary"]["affected_dealers"] = len(all_dealers)

        return patterns

    def _detect_syndicator_issues(self, tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect patterns indicating syndicator outages or problems"""
        syndicator_issues = defaultdict(list)

        for ticket in tickets:
            classification = ticket.get("classification", {})
            category = classification.get("category", "").lower()
            syndicator = classification.get("syndicator", "Unknown")

            # Look for syndicator-related issues
            if syndicator and syndicator != "Unknown" and syndicator != "N/A":
                if any(keyword in category for keyword in ["bug", "outage", "issue", "problem"]):
                    syndicator_issues[syndicator].append({
                        "dealer_id": classification.get("dealer_id", "Unknown"),
                        "dealer_name": classification.get("dealer_name", "Unknown"),
                        "ticket_subject": ticket.get("subject", ""),
                        "category": category
                    })

        # Identify syndicators with multiple issues
        alerts = []
        for syndicator, issue_list in syndicator_issues.items():
            if len(issue_list) >= self.issue_threshold:
                severity = "critical" if len(issue_list) >= 5 else "high"

                alerts.append({
                    "type": "syndicator_outage",
                    "syndicator": syndicator,
                    "severity": severity,
                    "ticket_count": len(issue_list),
                    "affected_dealers": [i["dealer_id"] for i in issue_list],
                    "affected_dealer_names": [i["dealer_name"] for i in issue_list],
                    "description": f"{syndicator} experiencing issues across {len(issue_list)} dealers",
                    "recommended_action": f"Contact {syndicator} support team immediately. Send mass communication to affected dealers.",
                    "revenue_at_risk": self._calculate_revenue_impact(issue_list),
                    "sample_tickets": [i["ticket_subject"] for i in issue_list[:3]]
                })

        return alerts

    def _detect_provider_issues(self, tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect patterns indicating import provider issues"""
        provider_issues = defaultdict(list)

        for ticket in tickets:
            classification = ticket.get("classification", {})
            category = classification.get("category", "").lower()
            provider = classification.get("provider", "Unknown")

            # Look for import/provider-related issues
            if provider and provider != "Unknown" and provider != "N/A":
                if "import" in category or "feed" in category or "provider" in category.lower():
                    provider_issues[provider].append({
                        "dealer_id": classification.get("dealer_id", "Unknown"),
                        "dealer_name": classification.get("dealer_name", "Unknown"),
                        "ticket_subject": ticket.get("subject", ""),
                        "category": category
                    })

        # Identify providers with multiple issues
        alerts = []
        for provider, issue_list in provider_issues.items():
            if len(issue_list) >= self.issue_threshold:
                severity = "critical" if len(issue_list) >= 5 else "high"

                alerts.append({
                    "type": "provider_issue",
                    "provider": provider,
                    "severity": severity,
                    "ticket_count": len(issue_list),
                    "affected_dealers": [i["dealer_id"] for i in issue_list],
                    "affected_dealer_names": [i["dealer_name"] for i in issue_list],
                    "description": f"{provider} import issues affecting {len(issue_list)} dealers",
                    "recommended_action": f"Investigate {provider} API connection. Check authentication and data feed status.",
                    "revenue_at_risk": self._calculate_revenue_impact(issue_list),
                    "sample_tickets": [i["ticket_subject"] for i in issue_list[:3]]
                })

        return alerts

    def _detect_feature_issues(self, tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect patterns indicating feature-specific problems"""
        category_counts = Counter()
        category_tickets = defaultdict(list)

        for ticket in tickets:
            classification = ticket.get("classification", {})
            category = classification.get("category", "Unknown")

            if category and category != "Unknown":
                category_counts[category] += 1
                category_tickets[category].append({
                    "dealer_id": classification.get("dealer_id", "Unknown"),
                    "dealer_name": classification.get("dealer_name", "Unknown"),
                    "ticket_subject": ticket.get("subject", "")
                })

        # Identify categories with unusual volume
        alerts = []
        for category, count in category_counts.items():
            if count >= self.issue_threshold:
                severity = "medium" if count < 5 else "high"
                issue_list = category_tickets[category]

                alerts.append({
                    "type": "feature_issue",
                    "feature_category": category,
                    "severity": severity,
                    "ticket_count": count,
                    "affected_dealers": [i["dealer_id"] for i in issue_list],
                    "description": f"Multiple tickets ({count}) related to {category}",
                    "recommended_action": f"Review {category} functionality. Check for recent deployments or changes.",
                    "sample_tickets": [i["ticket_subject"] for i in issue_list[:3]]
                })

        return alerts

    def _detect_volume_spikes(self, tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect unusual spikes in ticket volume"""
        if len(tickets) < 10:  # Need meaningful sample size
            return []

        alerts = []

        # Check for high Tier 3 volume (critical issues)
        tier3_count = sum(1 for t in tickets if t.get("classification", {}).get("tier") == "Tier 3")
        tier3_percentage = (tier3_count / len(tickets)) * 100

        if tier3_percentage > 30:  # More than 30% Tier 3 is concerning
            alerts.append({
                "type": "tier3_spike",
                "severity": "high",
                "tier3_count": tier3_count,
                "tier3_percentage": round(tier3_percentage, 1),
                "total_tickets": len(tickets),
                "description": f"High volume of Tier 3 (critical) tickets: {tier3_percentage:.1f}%",
                "recommended_action": "Review recent system changes. Consider all-hands support coverage."
            })

        # Check for negative sentiment spike
        negative_count = sum(1 for t in tickets
                           if t.get("classification", {}).get("sentiment", "").lower() in ["negative", "frustrated"])
        negative_percentage = (negative_count / len(tickets)) * 100

        if negative_percentage > 40:  # More than 40% negative is concerning
            alerts.append({
                "type": "sentiment_spike",
                "severity": "medium",
                "negative_count": negative_count,
                "negative_percentage": round(negative_percentage, 1),
                "total_tickets": len(tickets),
                "description": f"High volume of negative sentiment tickets: {negative_percentage:.1f}%",
                "recommended_action": "Increase support capacity. Consider proactive outreach to frustrated dealers."
            })

        return alerts

    def _calculate_revenue_impact(self, issue_list: List[Dict[str, Any]]) -> str:
        """Calculate potential revenue impact of an issue"""
        # Average ARR per dealer (from mock data)
        avg_arr_per_dealer = 20000

        affected_count = len(set(i["dealer_id"] for i in issue_list))

        # Assume 5% churn risk for dealers experiencing issues
        revenue_at_risk = affected_count * avg_arr_per_dealer * 0.05

        return f"${revenue_at_risk:,.0f}"

    def generate_alert_summary(self, patterns: Dict[str, Any]) -> str:
        """Generate a human-readable summary of detected patterns"""
        if patterns["summary"]["total_patterns"] == 0:
            return "✅ No system-wide issues detected. All systems operating normally."

        summary_parts = []

        if patterns["syndicator_outages"]:
            summary_parts.append(
                f"🚨 {len(patterns['syndicator_outages'])} syndicator outage(s) detected"
            )

        if patterns["provider_issues"]:
            summary_parts.append(
                f"⚠️ {len(patterns['provider_issues'])} provider issue(s) detected"
            )

        if patterns["feature_problems"]:
            summary_parts.append(
                f"🔧 {len(patterns['feature_problems'])} feature-related pattern(s) detected"
            )

        if patterns["spike_alerts"]:
            summary_parts.append(
                f"📈 {len(patterns['spike_alerts'])} volume spike alert(s)"
            )

        summary_parts.append(
            f"👥 {patterns['summary']['affected_dealers']} dealers affected"
        )

        return " | ".join(summary_parts)


def test_proactive_detection():
    """Test the proactive issue detector with sample data"""
    detector = ProactiveIssueDetector()

    # Sample tickets simulating a Kijiji outage
    sample_tickets = [
        {
            "subject": "Kijiji ads not showing",
            "classification": {
                "dealer_id": "D001",
                "dealer_name": "Dealership_1",
                "category": "Syndicator Bug",
                "syndicator": "Kijiji",
                "tier": "Tier 3",
                "sentiment": "Frustrated"
            }
        },
        {
            "subject": "Kijiji feed down",
            "classification": {
                "dealer_id": "D002",
                "dealer_name": "Dealership_2",
                "category": "Syndicator Outage",
                "syndicator": "Kijiji",
                "tier": "Tier 3",
                "sentiment": "Negative"
            }
        },
        {
            "subject": "Cars not appearing on Kijiji",
            "classification": {
                "dealer_id": "D003",
                "dealer_name": "Dealership_3",
                "category": "Syndicator Issue",
                "syndicator": "Kijiji",
                "tier": "Tier 3",
                "sentiment": "Frustrated"
            }
        },
        {
            "subject": "PBS import not working",
            "classification": {
                "dealer_id": "D004",
                "dealer_name": "Dealership_4",
                "category": "Import Issue",
                "provider": "PBS",
                "tier": "Tier 2",
                "sentiment": "Neutral"
            }
        }
    ]

    patterns = detector.analyze_patterns(sample_tickets)
    summary = detector.generate_alert_summary(patterns)

    print("=== Proactive Issue Detection Test ===")
    print(f"\nSummary: {summary}")
    print(f"\nDetected Patterns:")
    print(json.dumps(patterns, indent=2))


if __name__ == "__main__":
    test_proactive_detection()
