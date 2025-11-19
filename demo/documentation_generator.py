"""
AI-Powered Documentation Generator
Automatically generates knowledge base articles from resolved tickets
"""

import logging
from typing import Dict, Any, List, Optional
import os
from dotenv import load_dotenv
from openai import OpenAI
import json
from pathlib import Path

# Load .env file from the current directory
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

logger = logging.getLogger(__name__)


class DocumentationGenerator:
    """Generates KB documentation from resolved tickets using AI"""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "sk-your-openai-api-key-here":
            raise ValueError("OPENAI_API_KEY not set or using placeholder value")

        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def generate_kb_article(self, ticket_data: Dict[str, Any],
                           resolution_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a complete KB article from ticket and resolution

        Args:
            ticket_data: Original ticket information
            resolution_data: How the ticket was resolved

        Returns:
            Generated KB article
        """
        prompt = self._build_generation_prompt(ticket_data, resolution_data)

        try:
            # Use Responses API for GPT-5
            full_input = f"""You are an expert technical writer who creates clear, concise knowledge base articles for support teams.

{prompt}

IMPORTANT: Return ONLY valid JSON, no other text."""

            response = self.client.responses.create(
                model=self.model,
                input=full_input,
                reasoning={"effort": "medium"}  # Medium reasoning for quality documentation
            )

            result = json.loads(response.output_text)

            # Enhance with metadata from ticket
            classification = ticket_data.get("classification", {})
            result["category"] = classification.get("category", "General")
            result["syndicator"] = classification.get("syndicator", "N/A")
            result["provider"] = classification.get("provider", "N/A")
            result["source_ticket_id"] = ticket_data.get("ticket_id", None)
            result["resolution_time"] = resolution_data.get("time_to_resolve", "Unknown")

            return result

        except Exception as e:
            logger.error(f"Error generating KB article from ticket {ticket_data.get('ticket_id', 'unknown')}: {e}")
            return self._generate_fallback_article(ticket_data, resolution_data)

    def _build_generation_prompt(self, ticket_data: Dict[str, Any],
                                 resolution_data: Dict[str, Any]) -> str:
        """Build the prompt for AI article generation"""
        ticket_text = ticket_data.get("text", ticket_data.get("description", ""))
        ticket_subject = ticket_data.get("subject", "")
        resolution_text = resolution_data.get("resolution", resolution_data.get("solution", ""))
        steps_taken = resolution_data.get("steps", [])

        prompt = f"""Create a knowledge base article from this resolved support ticket.

**Original Ticket:**
Subject: {ticket_subject}
Description: {ticket_text}

**Resolution:**
{resolution_text}

**Steps Taken:**
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(steps_taken)) if steps_taken else 'N/A'}

Generate a complete KB article in JSON format with these fields:
- title: Clear, searchable title (50 chars max)
- problem: Description of the issue (2-3 sentences)
- solution: High-level solution summary (2-3 sentences)
- steps: Array of step-by-step instructions to resolve
- tags: Array of relevant keywords for searching
- related_issues: Array of related problems that might have same solution

Make it clear, actionable, and searchable. Focus on what support agents need to know.

Return ONLY valid JSON, no other text."""

        return prompt

    def _generate_fallback_article(self, ticket_data: Dict[str, Any],
                                   resolution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a basic article if AI fails"""
        classification = ticket_data.get("classification", {})

        return {
            "title": ticket_data.get("subject", "Support Issue Resolution"),
            "problem": ticket_data.get("text", "Issue reported by dealer"),
            "solution": resolution_data.get("resolution", "Issue resolved"),
            "steps": resolution_data.get("steps", ["Contact support for assistance"]),
            "tags": [classification.get("category", "general")],
            "related_issues": [],
            "category": classification.get("category", "General"),
            "syndicator": classification.get("syndicator", "N/A"),
            "provider": classification.get("provider", "N/A")
        }

    def generate_batch_articles(self, resolved_tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate KB articles for multiple resolved tickets

        Args:
            resolved_tickets: List of tickets with resolution data

        Returns:
            List of generated articles
        """
        articles = []

        for ticket in resolved_tickets:
            try:
                article = self.generate_kb_article(
                    ticket_data=ticket.get("ticket", {}),
                    resolution_data=ticket.get("resolution", {})
                )
                articles.append(article)
            except Exception as e:
                logger.error(f"Error processing ticket {ticket.get('ticket_id', 'unknown')}: {e}")
                continue

        return articles

    def suggest_improvements(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest improvements for an existing KB article

        Args:
            article: Existing KB article

        Returns:
            Suggestions for improvement
        """
        prompt = f"""Review this knowledge base article and suggest improvements.

**Current Article:**
Title: {article.get('title', '')}
Problem: {article.get('problem', '')}
Solution: {article.get('solution', '')}
Steps: {json.dumps(article.get('steps', []), indent=2)}

Suggest improvements in JSON format:
- clarity_score: 1-10 rating of how clear the article is
- completeness_score: 1-10 rating of completeness
- suggested_title: Better title if needed (or null)
- missing_information: Array of things that should be added
- improvement_notes: Array of specific suggestions

Return ONLY valid JSON."""

        try:
            # Use Responses API for GPT-5
            full_input = f"""You are a technical writing expert who reviews documentation quality.

{prompt}

IMPORTANT: Return ONLY valid JSON, no other text."""

            response = self.client.responses.create(
                model=self.model,
                input=full_input,
                reasoning={"effort": "low"}  # Low reasoning for simple review task
            )

            return json.loads(response.output_text)

        except Exception as e:
            logger.error(f"Error suggesting improvements for article: {e}")
            return {
                "clarity_score": 7,
                "completeness_score": 7,
                "suggested_title": None,
                "missing_information": [],
                "improvement_notes": []
            }

    def extract_article_from_text(self, resolution_text: str,
                                  category: str = "General") -> Dict[str, Any]:
        """
        Extract KB article structure from plain text resolution

        Args:
            resolution_text: Plain text describing the resolution
            category: Category to assign

        Returns:
            Structured KB article
        """
        prompt = f"""Convert this resolution text into a structured KB article.

**Resolution Text:**
{resolution_text}

**Category:** {category}

Generate a structured article in JSON format with:
- title: Clear, concise title
- problem: What issue this resolves
- solution: How to fix it
- steps: Step-by-step instructions
- tags: Relevant keywords

Return ONLY valid JSON."""

        try:
            # Use Responses API for GPT-5
            full_input = f"""You are a technical writer who structures support resolutions into clear KB articles.

{prompt}

IMPORTANT: Return ONLY valid JSON, no other text."""

            response = self.client.responses.create(
                model=self.model,
                input=full_input,
                reasoning={"effort": "low"}  # Low reasoning for extraction task
            )

            result = json.loads(response.output_text)
            result["category"] = category
            return result

        except Exception as e:
            logger.error(f"Error extracting article from text: {e}")
            return {
                "title": "Resolution",
                "problem": "Support issue",
                "solution": resolution_text,
                "steps": [],
                "tags": [category.lower()],
                "category": category
            }


def test_documentation_generator():
    """Test the documentation generator"""
    print("=== Documentation Generator Test ===\n")

    try:
        generator = DocumentationGenerator()

        # Sample resolved ticket
        ticket_data = {
            "ticket_id": "T12345",
            "subject": "Syndicator A ads not showing",
            "text": "Our vehicles haven't appeared on Syndicator A for the past 2 days. Please help!",
            "classification": {
                "category": "Syndicator Bug",
                "syndicator": "Syndicator A",
                "tier": "Tier 2"
            }
        }

        resolution_data = {
            "resolution": "Syndicator A API credentials had expired. Re-authenticated and triggered manual sync.",
            "steps": [
                "Checked Syndicator A API status - all systems operational",
                "Verified dealer's Syndicator A account was active",
                "Found expired API credentials in our system",
                "Re-authenticated Syndicator A connection",
                "Triggered manual sync of all vehicles",
                "Confirmed vehicles appeared on Syndicator A within 5 minutes"
            ],
            "time_to_resolve": "20 minutes"
        }

        print("Generating KB article...")
        article = generator.generate_kb_article(ticket_data, resolution_data)
        print("\nGenerated Article:")
        print(json.dumps(article, indent=2))

        print("\n\nSuggesting improvements...")
        improvements = generator.suggest_improvements(article)
        print(json.dumps(improvements, indent=2))

    except ValueError as e:
        print(f"Setup error: {e}")
        print("Make sure OPENAI_API_KEY is set in your .env file")
    except Exception as e:
        print(f"Test error: {e}")


if __name__ == "__main__":
    test_documentation_generator()
