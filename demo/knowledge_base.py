"""
Knowledge Base Storage and Retrieval System
Handles storing, searching, and managing KB articles
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from gap_analysis import GapAnalyzer
from cache_manager import CacheManager

load_dotenv()

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """Manages the knowledge base - storage, search, and retrieval"""

    def __init__(self, kb_file: str = "knowledge_base.json"):
        """Initialize KB with persistent storage"""
        self.kb_file = Path(__file__).parent / "mock_data" / kb_file
        self.articles: List[Dict[str, Any]] = []

        # Initialize OpenAI for query understanding
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            self.model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
        else:
            self.client = None

        # Initialize cache manager for query understanding (12 hour TTL)
        self.cache = CacheManager(cache_file="kb_query_cache.json", default_ttl_hours=12)
        
        # Initialize gap analyzer for search tracking
        self.gap_analyzer = GapAnalyzer()

        self.load()

    def load(self):
        """Load KB from file"""
        try:
            if self.kb_file.exists():
                with open(self.kb_file, 'r', encoding='utf-8') as f:
                    self.articles = json.load(f)
            else:
                # Ensure directory exists
                self.kb_file.parent.mkdir(parents=True, exist_ok=True)
                self.articles = []
                self.save()
        except FileNotFoundError:
            logger.warning(f"KB file not found: {self.kb_file}, initializing empty KB")
            self.articles = []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing KB JSON file {self.kb_file}: {e}")
            self.articles = []
        except Exception as e:
            logger.error(f"Unexpected error loading KB from {self.kb_file}: {e}")
            self.articles = []

    def save(self):
        """Save KB to file"""
        try:
            self.kb_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.kb_file, 'w', encoding='utf-8') as f:
                json.dump(self.articles, f, indent=2, ensure_ascii=False)
        except (IOError, OSError) as e:
            logger.error(f"Error writing KB file {self.kb_file}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving KB to {self.kb_file}: {e}")

    def add_article(self, article: Dict[str, Any]) -> int:
        """Add a new article to KB"""
        # Generate ID if not present
        if 'id' not in article:
            article['id'] = max([a.get('id', 0) for a in self.articles], default=0) + 1

        # Add timestamps
        article['created_at'] = datetime.now().isoformat()
        article['updated_at'] = datetime.now().isoformat()

        # Initialize tracking fields
        if 'usage_count' not in article:
            article['usage_count'] = 0
        if 'success_count' not in article:
            article['success_count'] = 0
        if 'success_rate' not in article:
            article['success_rate'] = 1.0

        # Initialize edge cases and example tickets
        if 'edge_cases' not in article:
            article['edge_cases'] = []
        if 'example_tickets' not in article:
            article['example_tickets'] = []

        # Initialize voting
        if 'upvotes' not in article:
            article['upvotes'] = 0
        if 'downvotes' not in article:
            article['downvotes'] = 0
        if 'vote_score' not in article:
            article['vote_score'] = 0

        # Initialize embedding (for semantic search)
        if 'embedding' not in article:
            article['embedding'] = None

        self.articles.append(article)
        self.save()
        return article['id']

    def update_article(self, article_id: int, updates: Dict[str, Any], change_reason: str = "Manual update"):
        """Update an existing article with version history tracking"""
        for article in self.articles:
            if article.get('id') == article_id:
                # Initialize version history if not present
                if 'version_history' not in article:
                    article['version_history'] = []

                # Save current state to history
                version_snapshot = {
                    'version': len(article['version_history']) + 1,
                    'timestamp': article.get('updated_at', datetime.now().isoformat()),
                    'change_reason': change_reason,
                    'previous_state': {
                        'title': article.get('title'),
                        'problem': article.get('problem'),
                        'solution': article.get('solution'),
                        'steps': article.get('steps', []).copy(),
                        'tags': article.get('tags', []).copy(),
                        'success_rate': article.get('success_rate'),
                        'usage_count': article.get('usage_count')
                    }
                }
                article['version_history'].append(version_snapshot)

                # Apply updates
                article.update(updates)
                article['updated_at'] = datetime.now().isoformat()
                article['version'] = len(article['version_history']) + 1

                self.save()
                return True
        return False

    def delete_article(self, article_id: int) -> bool:
        """Delete an article"""
        original_len = len(self.articles)
        self.articles = [a for a in self.articles if a.get('id') != article_id]
        if len(self.articles) < original_len:
            self.save()
            return True
        return False

    def get_article(self, article_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific article by ID"""
        for article in self.articles:
            if article.get('id') == article_id:
                return article
        return None

    def understand_query(self, query: str, classification: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Use AI to understand query intent and expand search terms

        Args:
            query: Original search query
            classification: Optional classification context

        Returns:
            Dictionary with expanded search terms and intent
        """
        if not self.client:
            # Return original query if no AI available
            return {
                "original_query": query,
                "expanded_queries": [query],
                "keywords": [query],
                "intent": "unknown"
            }

        context = ""
        if classification:
            context = f"""
Context:
- Category: {classification.get('category', 'N/A')}
- Sub-Category: {classification.get('sub_category', 'N/A')}
- Syndicator: {classification.get('syndicator', 'N/A')}
- Provider: {classification.get('provider', 'N/A')}
"""

        prompt = f"""Analyze this support ticket query and generate search terms for knowledge base lookup.

Query: "{query}"
{context}

Generate:
1. Expanded queries: Rephrase the query in 2-3 different ways
2. Keywords: Extract 3-5 key searchable terms
3. Intent: What is the user trying to do? (e.g., "troubleshoot", "activate", "cancel", "configure")

Rules:
- Expand acronyms if present
- Include synonyms (e.g., "broken" → "failed", "not working", "error")
- Include technical variations (e.g., "feed" → "export feed", "syndication", "data feed")
- Keep syndicator/provider names intact

Return JSON:
{{
  "expanded_queries": ["variation 1", "variation 2", "variation 3"],
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "intent": "action_verb"
}}
"""

        try:
            # Use cache for query understanding (same query = same expansion)
            def _call_api():
                response = self.client.responses.create(
                    model=self.model,
                    input=prompt,
                    reasoning={"effort": "low"}
                )
                return json.loads(response.output_text)
            
            # Cache based on prompt content
            result = self.cache.cache_api_call(prompt, _call_api)
            result["original_query"] = query
            return result

        except Exception as e:
            logger.error(f"Query understanding failed: {e}")
            # Fallback to original query
            return {
                "original_query": query,
                "expanded_queries": [query],
                "keywords": [query],
                "intent": "unknown"
            }

    def search_articles(self, query: str, classification: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search articles by query string and classification
        Uses semantic search if embeddings available, otherwise falls back to keyword search
        Returns list of matching articles with relevance scores
        """
        if not query and not classification:
            return self.articles

        # Track search for gap analysis
        results_found = False
        result_count = 0
        article_id = None

        # Try semantic search first if embeddings are available
        if query:
            has_embeddings = any(article.get('embedding') for article in self.articles)
            if has_embeddings:
                try:
                    semantic_results = self.semantic_search(query, top_k=10)
                    if semantic_results:
                        # Boost scores based on classification if provided
                        if classification:
                            for result in semantic_results:
                                article = result['article']
                                boost = 0
                                # Classification matching
                                if article.get('category') == classification.get('category'):
                                    boost += 15
                                if article.get('sub_category') == classification.get('sub_category'):
                                    boost += 10
                                if classification.get('syndicator') and article.get('syndicator') == classification.get('syndicator'):
                                    boost += 10
                                if classification.get('provider') and article.get('provider') == classification.get('provider'):
                                    boost += 10

                                # Enhanced: Success rate boost (up to +15 points)
                                success_rate = article.get('success_rate', 0.5)
                                usage_count = article.get('usage_count', 0)
                                if usage_count >= 3:  # Only boost if article has been used
                                    if success_rate >= 0.9:
                                        boost += 15  # Excellent success rate
                                    elif success_rate >= 0.7:
                                        boost += 10  # Good success rate
                                    elif success_rate >= 0.5:
                                        boost += 5   # OK success rate
                                    elif success_rate < 0.3:
                                        boost -= 10  # Penalize low success rate

                                # Enhanced: Usage-based ranking (up to +5 points for popular articles)
                                if usage_count > 0:
                                    # Normalize usage count to 0-5 boost
                                    usage_boost = min(usage_count / 2, 5)
                                    boost += usage_boost

                                # Enhanced: Recency boost (up to +3 points for recently updated)
                                if article.get('updated_at'):
                                    try:
                                        from datetime import datetime, timedelta
                                        updated = datetime.fromisoformat(article['updated_at'])
                                        age_days = (datetime.now() - updated).days
                                        if age_days <= 7:
                                            boost += 3  # Very recent
                                        elif age_days <= 30:
                                            boost += 1  # Recent
                                    except:
                                        pass  # Skip if parsing fails

                                result['score'] = min(result['score'] + boost, 100)
                                result['confidence'] = result['score']

                        semantic_results.sort(key=lambda x: x['score'], reverse=True)
                        
                        # Track search for gap analysis
                        results_found = len(semantic_results) > 0
                        result_count = len(semantic_results)
                        article_id = semantic_results[0]['article']['id'] if semantic_results else None
                        
                        # Log search to gap analyzer
                        self.gap_analyzer.log_search(
                            query=query,
                            results_found=results_found,
                            article_id=article_id,
                            result_count=result_count,
                            classification=classification
                        )
                        
                        return semantic_results
                except Exception as e:
                    print(f"Semantic search failed, falling back to keyword search: {e}")

        # Fallback to keyword search
        results = []
        query_lower = query.lower() if query else ""

        for article in self.articles:
            score = 0

            # Text matching
            if query_lower:
                if query_lower in article.get('title', '').lower():
                    score += 10
                if query_lower in article.get('problem', '').lower():
                    score += 5
                if query_lower in article.get('solution', '').lower():
                    score += 3
                if any(query_lower in tag.lower() for tag in article.get('tags', [])):
                    score += 3

            # Classification matching
            if classification:
                if article.get('category') == classification.get('category'):
                    score += 15
                if article.get('sub_category') == classification.get('sub_category'):
                    score += 10

                # Syndicator/Provider matching
                if classification.get('syndicator') and article.get('syndicator') == classification.get('syndicator'):
                    score += 10
                if classification.get('provider') and article.get('provider') == classification.get('provider'):
                    score += 10

            if score > 0:
                results.append({
                    'article': article,
                    'score': score,
                    'confidence': min(score * 5, 100)  # Convert to percentage
                })

        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Track search for gap analysis (keyword search fallback)
        if query:
            results_found = len(results) > 0
            result_count = len(results)
            article_id = results[0]['article']['id'] if results else None
            
            # Log search to gap analyzer
            self.gap_analyzer.log_search(
                query=query,
                results_found=results_found,
                article_id=article_id,
                result_count=result_count,
                classification=classification
            )
        
        return results

    def record_usage(self, article_id: int, success: bool):
        """Record usage of an article and whether it was successful"""
        article = self.get_article(article_id)
        if article:
            article['usage_count'] = article.get('usage_count', 0) + 1
            if success:
                article['success_count'] = article.get('success_count', 0) + 1

            # Calculate success rate
            if article['usage_count'] > 0:
                article['success_rate'] = article['success_count'] / article['usage_count']

            article['last_used'] = datetime.now().isoformat()
            self.save()

    def get_stats(self) -> Dict[str, Any]:
        """Get KB statistics"""
        total = len(self.articles)
        if total == 0:
            return {
                'total_articles': 0,
                'avg_success_rate': 0,
                'total_usage': 0
            }

        total_usage = sum(a.get('usage_count', 0) for a in self.articles)
        avg_success = sum(a.get('success_rate', 1.0) for a in self.articles) / total

        return {
            'total_articles': total,
            'avg_success_rate': avg_success,
            'total_usage': total_usage,
            'articles_by_category': self._count_by_field('category'),
            'articles_by_subcategory': self._count_by_field('sub_category')
        }

    def _count_by_field(self, field: str) -> Dict[str, int]:
        """Count articles by a specific field"""
        counts = {}
        for article in self.articles:
            value = article.get(field, 'Unknown')
            counts[value] = counts.get(value, 0) + 1
        return counts

    def get_version_history(self, article_id: int) -> List[Dict[str, Any]]:
        """Get version history for an article"""
        article = self.get_article(article_id)
        if article:
            return article.get('version_history', [])
        return []

    def rollback_article(self, article_id: int, version_number: int) -> bool:
        """Rollback an article to a specific version"""
        article = self.get_article(article_id)
        if not article or 'version_history' not in article:
            return False

        # Find the version
        target_version = None
        for version in article['version_history']:
            if version.get('version') == version_number:
                target_version = version
                break

        if not target_version:
            return False

        # Restore the previous state
        previous_state = target_version.get('previous_state', {})

        # Update article with previous state (keeping history intact)
        article['title'] = previous_state.get('title', article.get('title'))
        article['problem'] = previous_state.get('problem', article.get('problem'))
        article['solution'] = previous_state.get('solution', article.get('solution'))
        article['steps'] = previous_state.get('steps', article.get('steps', []))
        article['tags'] = previous_state.get('tags', article.get('tags', []))
        article['updated_at'] = datetime.now().isoformat()

        # Add a history entry for the rollback
        rollback_entry = {
            'version': len(article['version_history']) + 1,
            'timestamp': datetime.now().isoformat(),
            'change_reason': f"Rolled back to version {version_number}",
            'previous_state': {
                'title': article.get('title'),
                'problem': article.get('problem'),
                'solution': article.get('solution'),
                'steps': article.get('steps', []).copy(),
                'tags': article.get('tags', []).copy(),
                'success_rate': article.get('success_rate'),
                'usage_count': article.get('usage_count')
            }
        }
        article['version_history'].append(rollback_entry)
        article['version'] = len(article['version_history']) + 1

        self.save()
        return True

    def add_edge_case(self, article_id: int, edge_case: Dict[str, Any]) -> bool:
        """
        Add an edge case to an article

        Args:
            article_id: ID of the article
            edge_case: Dict with 'scenario', 'note', 'reported_by', 'date'
        """
        article = self.get_article(article_id)
        if article:
            if 'edge_cases' not in article:
                article['edge_cases'] = []

            edge_case_entry = {
                'scenario': edge_case.get('scenario', ''),
                'note': edge_case.get('note', ''),
                'reported_by': edge_case.get('reported_by', 'Unknown'),
                'date': edge_case.get('date', datetime.now().isoformat())
            }
            article['edge_cases'].append(edge_case_entry)
            article['updated_at'] = datetime.now().isoformat()
            self.save()
            return True
        return False

    def add_example_ticket(self, article_id: int, example: Dict[str, Any]) -> bool:
        """
        Add an example ticket to an article

        Args:
            article_id: ID of the article
            example: Dict with 'summary', 'resolution_worked', 'actual_resolution', 'date'
        """
        article = self.get_article(article_id)
        if article:
            if 'example_tickets' not in article:
                article['example_tickets'] = []

            example_entry = {
                'summary': example.get('summary', ''),
                'resolution_worked': example.get('resolution_worked', False),
                'actual_resolution': example.get('actual_resolution', ''),
                'date': example.get('date', datetime.now().isoformat()),
                'ticket_id': example.get('ticket_id', '')
            }
            article['example_tickets'].append(example_entry)
            article['updated_at'] = datetime.now().isoformat()
            self.save()
            return True
        return False

    def get_edge_cases(self, article_id: int) -> List[Dict[str, Any]]:
        """Get all edge cases for an article"""
        article = self.get_article(article_id)
        if article:
            return article.get('edge_cases', [])
        return []

    def get_example_tickets(self, article_id: int) -> List[Dict[str, Any]]:
        """Get all example tickets for an article"""
        article = self.get_article(article_id)
        if article:
            return article.get('example_tickets', [])
        return []

    def vote_article(self, article_id: int, vote_type: str) -> bool:
        """
        Vote on an article

        Args:
            article_id: ID of the article
            vote_type: 'up' or 'down'
        """
        article = self.get_article(article_id)
        if article:
            if vote_type == 'up':
                article['upvotes'] = article.get('upvotes', 0) + 1
            elif vote_type == 'down':
                article['downvotes'] = article.get('downvotes', 0) + 1

            # Calculate vote score (upvotes - downvotes)
            upvotes = article.get('upvotes', 0)
            downvotes = article.get('downvotes', 0)
            article['vote_score'] = upvotes - downvotes

            self.save()
            return True
        return False

    def generate_embedding(self, article: Dict[str, Any]) -> Optional[List[float]]:
        """
        Generate embedding for an article using OpenAI

        Args:
            article: Article dictionary

        Returns:
            List of floats representing the embedding, or None if failed
        """
        try:
            from openai import OpenAI
            import os

            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            # Combine article text for embedding
            text = f"{article.get('title', '')} {article.get('problem', '')} {article.get('solution', '')} {' '.join(article.get('tags', []))}"

            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )

            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    def update_article_embedding(self, article_id: int) -> bool:
        """Update the embedding for a specific article"""
        article = self.get_article(article_id)
        if article:
            embedding = self.generate_embedding(article)
            if embedding:
                article['embedding'] = embedding
                self.save()
                return True
        return False

    def update_all_embeddings(self):
        """Generate/update embeddings for all articles"""
        print("Generating embeddings for all articles...")
        for article in self.articles:
            print(f"  Processing article #{article.get('id')}...")
            embedding = self.generate_embedding(article)
            if embedding:
                article['embedding'] = embedding
        self.save()
        print(f"[OK] Updated {len(self.articles)} article embeddings")

    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search articles using semantic similarity

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of matching articles with similarity scores
        """
        try:
            from openai import OpenAI
            import os
            import numpy as np

            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            # Generate query embedding
            query_response = client.embeddings.create(
                model="text-embedding-3-small",
                input=query
            )
            query_embedding = np.array(query_response.data[0].embedding)

            # Calculate similarity with all articles
            results = []
            for article in self.articles:
                if article.get('embedding'):
                    article_embedding = np.array(article['embedding'])

                    # Cosine similarity
                    similarity = np.dot(query_embedding, article_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(article_embedding)
                    )

                    # Convert to percentage (0-100)
                    score = int(similarity * 100)

                    results.append({
                        'article': article,
                        'score': score,
                        'confidence': score
                    })

            # Sort by similarity
            results.sort(key=lambda x: x['score'], reverse=True)

            return results[:top_k]

        except Exception as e:
            print(f"Error in semantic search: {e}")
            # Fallback to keyword search
            return []
