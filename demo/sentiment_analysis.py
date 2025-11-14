"""
Enhanced Sentiment Analysis System
Provides nuanced sentiment tracking with escalation alerts and trend analysis
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json


class SentimentAnalyzer:
    """Enhanced sentiment analysis with escalation detection and trend tracking"""

    def __init__(self):
        # Sentiment scoring thresholds
        self.escalation_keywords = [
            "furious", "angry", "unacceptable", "terrible", "worst",
            "cancel", "lawyer", "sue", "incompetent", "useless",
            "frustrated", "disappointed", "fed up", "enough"
        ]

        self.urgency_keywords = [
            "urgent", "asap", "immediately", "critical", "emergency",
            "down", "not working", "broken", "outage"
        ]

    def analyze_sentiment(self, ticket_text: str, classification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform enhanced sentiment analysis on a ticket

        Args:
            ticket_text: Full ticket content
            classification: Existing classification data

        Returns:
            Enhanced sentiment analysis with scores and flags
        """
        text_lower = ticket_text.lower()

        # Get base sentiment from classification (if exists)
        base_sentiment = classification.get("sentiment", "Neutral")

        # Calculate sentiment score (-100 to +100)
        sentiment_score = self._calculate_sentiment_score(text_lower, base_sentiment)

        # Detect escalation risk
        escalation_risk = self._detect_escalation_risk(text_lower, classification)

        # Detect urgency level
        urgency_level = self._detect_urgency(text_lower, classification)

        # Generate recommended actions
        recommended_actions = self._generate_recommendations(
            sentiment_score, escalation_risk, urgency_level, classification
        )

        return {
            "base_sentiment": base_sentiment,
            "sentiment_score": sentiment_score,
            "sentiment_label": self._score_to_label(sentiment_score),
            "escalation_risk": escalation_risk,
            "urgency_level": urgency_level,
            "requires_immediate_attention": self._requires_immediate_attention(
                sentiment_score, escalation_risk, urgency_level
            ),
            "recommended_actions": recommended_actions,
            "flags": self._generate_flags(sentiment_score, escalation_risk, urgency_level)
        }

    def _calculate_sentiment_score(self, text: str, base_sentiment: str) -> int:
        """
        Calculate numerical sentiment score

        Returns:
            Score from -100 (very negative) to +100 (very positive)
        """
        # Start with base score from classification
        score_map = {
            "Positive": 50,
            "Neutral": 0,
            "Negative": -50,
            "Frustrated": -70
        }
        score = score_map.get(base_sentiment, 0)

        # Adjust based on escalation keywords
        escalation_count = sum(1 for keyword in self.escalation_keywords if keyword in text)
        score -= escalation_count * 15  # Each escalation keyword reduces score by 15

        # Adjust based on urgency keywords
        urgency_count = sum(1 for keyword in self.urgency_keywords if keyword in text)
        score -= urgency_count * 5  # Each urgency keyword reduces score by 5

        # Positive indicators
        positive_keywords = ["thank", "appreciate", "great", "excellent", "happy", "good"]
        positive_count = sum(1 for keyword in positive_keywords if keyword in text)
        score += positive_count * 10

        # Clamp score to -100 to +100
        return max(-100, min(100, score))

    def _score_to_label(self, score: int) -> str:
        """Convert sentiment score to label"""
        if score >= 50:
            return "Very Positive"
        elif score >= 20:
            return "Positive"
        elif score >= -20:
            return "Neutral"
        elif score >= -50:
            return "Negative"
        elif score >= -75:
            return "Very Negative"
        else:
            return "Highly Negative (Critical)"

    def _detect_escalation_risk(self, text: str, classification: Dict[str, Any]) -> str:
        """
        Detect risk of customer escalation

        Returns:
            "High", "Medium", "Low", or "None"
        """
        escalation_count = sum(1 for keyword in self.escalation_keywords if keyword in text)

        # Check for cancellation threats
        cancellation_keywords = ["cancel", "discontinue", "switch", "leave", "competitor"]
        has_cancellation_threat = any(keyword in text for keyword in cancellation_keywords)

        # Check tier (Tier 3 issues are more likely to escalate)
        tier = classification.get("tier", "")
        is_tier3 = "tier 3" in tier.lower()

        if escalation_count >= 3 or has_cancellation_threat:
            return "High"
        elif escalation_count >= 2 or is_tier3:
            return "Medium"
        elif escalation_count >= 1:
            return "Low"
        else:
            return "None"

    def _detect_urgency(self, text: str, classification: Dict[str, Any]) -> str:
        """
        Detect urgency level of ticket

        Returns:
            "Critical", "High", "Medium", or "Low"
        """
        urgency_count = sum(1 for keyword in self.urgency_keywords if keyword in text)

        # Check for business impact keywords
        business_impact = ["losing money", "revenue", "sales", "customers leaving", "business down"]
        has_business_impact = any(keyword in text for keyword in business_impact)

        # Check tier
        tier = classification.get("tier", "")
        is_tier3 = "tier 3" in tier.lower()

        if has_business_impact or (urgency_count >= 3 and is_tier3):
            return "Critical"
        elif urgency_count >= 2 or is_tier3:
            return "High"
        elif urgency_count >= 1:
            return "Medium"
        else:
            return "Low"

    def _requires_immediate_attention(self, sentiment_score: int,
                                     escalation_risk: str, urgency_level: str) -> bool:
        """Determine if ticket requires immediate attention"""
        return (
            sentiment_score <= -60 or
            escalation_risk == "High" or
            urgency_level == "Critical"
        )

    def _generate_recommendations(self, sentiment_score: int, escalation_risk: str,
                                 urgency_level: str, classification: Dict[str, Any]) -> List[str]:
        """Generate recommended actions based on sentiment analysis"""
        recommendations = []

        # Sentiment-based recommendations
        if sentiment_score <= -75:
            recommendations.append("🚨 URGENT: Executive escalation recommended")
            recommendations.append("📞 Call dealer immediately (do not email)")

        elif sentiment_score <= -50:
            recommendations.append("⚠️ Priority response required within 1 hour")
            recommendations.append("📞 Consider phone call over email")

        # Escalation risk recommendations
        if escalation_risk == "High":
            recommendations.append("🎯 Assign to senior support specialist")
            recommendations.append("💰 Review dealer ARR - high churn risk")
            recommendations.append("📋 Prepare detailed action plan")

        elif escalation_risk == "Medium":
            recommendations.append("👀 Manager review recommended")
            recommendations.append("⏱️ Set follow-up reminder in 24 hours")

        # Urgency recommendations
        if urgency_level == "Critical":
            recommendations.append("🔥 All-hands alert - potential outage")
            recommendations.append("📊 Check for similar tickets from other dealers")

        elif urgency_level == "High":
            recommendations.append("⚡ Fast-track to appropriate team")

        # Tier-based recommendations
        tier = classification.get("tier", "")
        if "tier 3" in tier.lower():
            recommendations.append("🔧 Technical team involvement required")

        # If no major concerns
        if not recommendations:
            recommendations.append("✅ Standard response protocol")
            recommendations.append("⏱️ Respond within SLA timeframe (4 hours)")

        return recommendations

    def _generate_flags(self, sentiment_score: int, escalation_risk: str,
                       urgency_level: str) -> List[str]:
        """Generate warning flags for the ticket"""
        flags = []

        if sentiment_score <= -75:
            flags.append("CRITICAL_SENTIMENT")

        if escalation_risk == "High":
            flags.append("HIGH_CHURN_RISK")

        if urgency_level == "Critical":
            flags.append("BUSINESS_IMPACT")

        if sentiment_score <= -60 and escalation_risk in ["High", "Medium"]:
            flags.append("EXECUTIVE_ALERT")

        return flags

    def analyze_sentiment_trends(self, ticket_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze sentiment trends for a specific dealer over time

        Args:
            ticket_history: List of tickets from the same dealer

        Returns:
            Trend analysis with alerts
        """
        if not ticket_history:
            return {"status": "no_data"}

        sentiment_scores = []
        escalation_count = 0
        negative_streak = 0

        for ticket in ticket_history:
            sentiment_data = ticket.get("sentiment_analysis", {})
            score = sentiment_data.get("sentiment_score", 0)
            sentiment_scores.append(score)

            if sentiment_data.get("escalation_risk") in ["High", "Medium"]:
                escalation_count += 1

            if score < -20:
                negative_streak += 1
            else:
                negative_streak = 0

        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        trend = "improving" if sentiment_scores[-1] > avg_sentiment else "declining"

        # Detect concerning patterns
        alerts = []
        if negative_streak >= 3:
            alerts.append({
                "type": "negative_streak",
                "severity": "high",
                "message": f"{negative_streak} consecutive negative tickets",
                "action": "Proactive outreach recommended"
            })

        if escalation_count >= 2:
            alerts.append({
                "type": "multiple_escalations",
                "severity": "high",
                "message": f"{escalation_count} escalation-risk tickets",
                "action": "Account manager involvement recommended"
            })

        if avg_sentiment < -40:
            alerts.append({
                "type": "poor_average_sentiment",
                "severity": "medium",
                "message": f"Low average sentiment: {avg_sentiment:.0f}",
                "action": "Review overall dealer satisfaction"
            })

        return {
            "status": "analyzed",
            "average_sentiment": round(avg_sentiment, 1),
            "trend": trend,
            "ticket_count": len(ticket_history),
            "escalation_count": escalation_count,
            "negative_streak": negative_streak,
            "alerts": alerts,
            "health_score_impact": self._calculate_health_impact(avg_sentiment, escalation_count)
        }

    def _calculate_health_impact(self, avg_sentiment: float, escalation_count: int) -> str:
        """Calculate impact on dealer health score"""
        impact = 0

        if avg_sentiment < -50:
            impact -= 20
        elif avg_sentiment < -20:
            impact -= 10

        impact -= escalation_count * 5

        if impact <= -20:
            return "Severe negative impact (-20 or more)"
        elif impact <= -10:
            return "Moderate negative impact (-10 to -20)"
        elif impact < 0:
            return "Minor negative impact"
        else:
            return "No negative impact"


def test_sentiment_analysis():
    """Test the sentiment analyzer with sample tickets"""
    analyzer = SentimentAnalyzer()

    # Test cases
    test_tickets = [
        {
            "text": "This is absolutely unacceptable! Our cars have been down on Syndicator A for 3 days now. We're losing thousands in sales. I need this fixed immediately or we're cancelling our contract!",
            "classification": {"tier": "Tier 3", "sentiment": "Frustrated"}
        },
        {
            "text": "Hi, I noticed our Syndicator B feed isn't updating. Can you take a look when you get a chance? Thanks!",
            "classification": {"tier": "Tier 2", "sentiment": "Neutral"}
        },
        {
            "text": "Thank you so much for the quick resolution! Your support team has been excellent.",
            "classification": {"tier": "Tier 1", "sentiment": "Positive"}
        }
    ]

    print("=== Enhanced Sentiment Analysis Test ===\n")

    for i, ticket in enumerate(test_tickets, 1):
        print(f"Ticket {i}:")
        print(f"Text: {ticket['text'][:80]}...")
        analysis = analyzer.analyze_sentiment(ticket["text"], ticket["classification"])
        print(json.dumps(analysis, indent=2))
        print()


if __name__ == "__main__":
    test_sentiment_analysis()
