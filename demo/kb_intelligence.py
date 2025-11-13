"""
KB Intelligence - Learning System
Analyzes ticket resolutions and decides how to update KB
"""

import json
import os
from typing import Dict, Any, List
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)


class KBIntelligence:
    """
    Intelligent KB manager that decides:
    - Add new knowledge (truly new issue)
    - Update existing knowledge (better solution)
    - Remove outdated knowledge (no longer relevant)
    """

    def __init__(self):
        """Initialize with GPT-5-mini"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")

        self.client = OpenAI(api_key=self.api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
        self.reasoning_effort = os.getenv("OPENAI_REASONING_EFFORT", "low")

    def analyze_resolution(self,
                          ticket: Dict[str, Any],
                          resolution: Dict[str, Any],
                          existing_articles: list = None) -> Dict[str, Any]:
        """
        Analyze a ticket resolution and decide what KB action to take

        Returns:
        {
            "action": "add_new" | "update_existing" | "remove" | "none",
            "target_id": article_id if updating/removing,
            "reasoning": explanation,
            "confidence": 0-100,
            "new_article": article data if adding new
        }
        """

        # Build context
        ticket_info = f"""
Ticket Classification:
- Category: {ticket.get('category', 'Unknown')}
- Sub-Category: {ticket.get('sub_category', 'Unknown')}
- Syndicator: {ticket.get('syndicator', 'N/A')}
- Provider: {ticket.get('provider', 'N/A')}
- Dealer: {ticket.get('dealer_name', 'Unknown')}

Ticket Content: {ticket.get('text', '')}

Resolution Provided:
{resolution.get('solution', '')}

Resolution Worked: {resolution.get('success', True)}
"""

        existing_context = ""
        if existing_articles:
            existing_context = "\n\nExisting KB Articles (Top 3 similar):\n"
            for i, art_data in enumerate(existing_articles[:3], 1):
                art = art_data['article']
                existing_context += f"""
Article {i} (ID: {art.get('id')}):
- Title: {art.get('title', '')}
- Problem: {art.get('problem', '')}
- Solution: {art.get('solution', '')}
- Success Rate: {art.get('success_rate', 1.0):.0%} ({art.get('usage_count', 0)} uses)
"""

        prompt = f"""{ticket_info}{existing_context}

Based on this ticket and resolution, decide the best KB action:

1. **add_new**: This is a completely NEW type of issue not covered by existing articles
2. **update_existing**: An existing article covers this but the resolution is BETTER or more complete
3. **remove**: An existing article is outdated and should be removed
4. **none**: Resolution didn't work OR duplicate of existing knowledge

Return JSON:
{{
  "action": "add_new|update_existing|remove|none",
  "target_id": <article_id if update/remove, else null>,
  "reasoning": "Clear explanation of why this action",
  "confidence": 0-100,
  "new_article": {{
    "title": "Clear descriptive title",
    "problem": "What the problem is",
    "solution": "How to solve it",
    "steps": ["Step 1", "Step 2", ...],
    "tags": ["relevant", "tags"],
    "category": "{ticket.get('category', '')}",
    "sub_category": "{ticket.get('sub_category', '')}",
    "syndicator": "{ticket.get('syndicator', '')}",
    "provider": "{ticket.get('provider', '')}"
  }}
}}

Only include "new_article" if action is "add_new".
"""

        try:
            response = self.client.responses.create(
                model=self.model,
                input=prompt,
                reasoning={"effort": self.reasoning_effort}
            )

            result = json.loads(response.output_text)
            return result

        except Exception as e:
            print(f"Error analyzing resolution: {e}")
            return {
                "action": "none",
                "reasoning": f"Analysis failed: {str(e)}",
                "confidence": 0
            }

    def generate_article(self, ticket: Dict[str, Any], resolution: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a KB article from a ticket and resolution"""

        prompt = f"""Create a knowledge base article from this ticket resolution.

Ticket:
- Category: {ticket.get('category', 'Unknown')}
- Sub-Category: {ticket.get('sub_category', 'Unknown')}
- Syndicator: {ticket.get('syndicator', 'N/A')}
- Provider: {ticket.get('provider', 'N/A')}
- Issue: {ticket.get('text', '')}

Resolution:
{resolution.get('solution', '')}

Create a structured KB article with:
- Clear title
- Problem description (what the issue is)
- Solution summary (how to fix it)
- Step-by-step instructions
- Relevant tags

Return JSON:
{{
  "title": "Clear descriptive title",
  "problem": "Detailed problem description",
  "solution": "Solution summary",
  "steps": ["Step 1", "Step 2", "Step 3", ...],
  "tags": ["Extract 5-10 specific, searchable tags including: technical terms, product names, action verbs, problem keywords, and syndicator/provider names"],
  "category": "{ticket.get('category', '')}",
  "sub_category": "{ticket.get('sub_category', '')}",
  "syndicator": "{ticket.get('syndicator', '')}",
  "provider": "{ticket.get('provider', '')}"
}}

Tag generation guidelines:
- Include syndicator/provider name
- Include action verbs (e.g., "cancel", "activate", "configure")
- Include technical terms from the issue
- Include problem keywords (e.g., "error", "missing", "failed")
- Make tags lowercase and hyphenated
- Aim for 5-10 tags total
"""

        try:
            response = self.client.responses.create(
                model=self.model,
                input=prompt,
                reasoning={"effort": self.reasoning_effort}
            )

            article = json.loads(response.output_text)
            return article

        except Exception as e:
            print(f"Error generating article: {e}")
            # Fallback to basic article
            return {
                "title": ticket.get('text', 'Support Issue')[:100],
                "problem": ticket.get('text', ''),
                "solution": resolution.get('solution', ''),
                "steps": [],
                "tags": [ticket.get('category', 'general')],
                "category": ticket.get('category', ''),
                "sub_category": ticket.get('sub_category', ''),
                "syndicator": ticket.get('syndicator', ''),
                "provider": ticket.get('provider', '')
            }

    def auto_generate_tags(self, article: Dict[str, Any]) -> List[str]:
        """
        Automatically generate tags for an existing KB article

        Args:
            article: KB article dictionary

        Returns:
            List of generated tags
        """
        prompt = f"""Generate 5-10 specific, searchable tags for this KB article.

Article:
Title: {article.get('title', '')}
Problem: {article.get('problem', '')}
Solution: {article.get('solution', '')}
Steps: {' '.join(article.get('steps', [])[:3])}
Category: {article.get('category', '')}
Sub-Category: {article.get('sub_category', '')}
Syndicator: {article.get('syndicator', 'N/A')}
Provider: {article.get('provider', 'N/A')}

Tag generation guidelines:
- Include syndicator/provider name if applicable
- Include action verbs (e.g., "cancel", "activate", "configure", "troubleshoot")
- Include technical terms and product names from the content
- Include problem keywords (e.g., "error", "missing", "failed", "not-working")
- Include category/sub-category related terms
- Make tags lowercase and hyphenated (e.g., "export-feed", "syndicator-activation")
- Avoid generic tags like "support" or "help"
- Aim for 5-10 specific, searchable tags

Return ONLY a JSON array of tags: ["tag1", "tag2", "tag3", ...]
"""

        try:
            response = self.client.responses.create(
                model=self.model,
                input=prompt,
                reasoning={"effort": "low"}  # Use low effort for tag generation
            )

            tags = json.loads(response.output_text)
            if isinstance(tags, list):
                return tags
            else:
                # Fallback if response isn't a list
                return self._extract_basic_tags(article)

        except Exception as e:
            print(f"Error generating tags: {e}")
            return self._extract_basic_tags(article)

    def _extract_basic_tags(self, article: Dict[str, Any]) -> List[str]:
        """Fallback method to extract basic tags from article"""
        tags = []

        # Add category/sub-category
        if article.get('category'):
            tags.append(article['category'].lower().replace(' ', '-'))
        if article.get('sub_category'):
            tags.append(article['sub_category'].lower().replace(' ', '-'))

        # Add syndicator/provider
        if article.get('syndicator'):
            tags.append(article['syndicator'].lower())
        if article.get('provider'):
            tags.append(article['provider'].lower())

        # Extract common action words from title/problem
        action_words = ['cancel', 'activate', 'configure', 'setup', 'fix', 'troubleshoot', 'enable', 'disable']
        title_lower = article.get('title', '').lower()
        problem_lower = article.get('problem', '').lower()

        for word in action_words:
            if word in title_lower or word in problem_lower:
                tags.append(word)

        return tags[:10]  # Limit to 10 tags
