"""
Simplified GPT-5 Classifier for Hackathon Demo
"""
import json
import os
from typing import Dict, Any, Tuple, Optional
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
from sentiment_analysis import SentimentAnalyzer
from cache_manager import CacheManager

load_dotenv()


class TicketClassifier:
    """Simplified ticket classifier using GPT-5."""

    def __init__(self):
        """Initialize the classifier."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.client = OpenAI(api_key=self.api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
        self.reasoning_effort = os.getenv("OPENAI_REASONING_EFFORT", "low")

        # Initialize cache manager (24 hour TTL for classifications)
        self.cache = CacheManager(cache_file="classification_cache.json", default_ttl_hours=24)

        # Load reference data
        self.syndicators = self._load_syndicators()
        self.import_providers = self._load_import_providers()
        self.dealer_mapping = self._load_dealer_mapping()

        # Initialize sentiment analyzer
        self.sentiment_analyzer = SentimentAnalyzer()

        # Valid categories
        self.valid_categories = [
            "Product Activation — New Client",
            "Product Activation — Existing Client",
            "Product Cancellation",
            "Problem / Bug",
            "General Question",
            "Analysis / Review",
            "Other"
        ]

        self.valid_subcategories = [
            "Import", "Export", "Sales Data Import",
            "Other Department", "Other"
        ]

        self.valid_inventory_types = [
            "New", "Used", "Demo", "New + Used", "In-Transit", "AS-IS", "CPO", "Unspecified"
        ]

        self.valid_tiers = [
            "Tier 1", "Tier 2", "Tier 3"
        ]

    def _load_syndicators(self):
        """Load syndicators list."""
        try:
            df = pd.read_csv("data/syndicators.csv", encoding="utf-8")
            return df["Syndicator"].dropna().tolist()
        except Exception as e:
            print(f"Warning: Could not load syndicators: {e}")
            return ["Syndicator_Export_1", "Syndicator_Export_2", "Syndicator_Export_3", "Syndicator_Export_4", "Syndicator_Export_5"]

    def _load_import_providers(self):
        """Load import providers list."""
        try:
            df = pd.read_csv("data/import_providers.csv", encoding="utf-8")
            return df["Provider"].dropna().tolist()
        except Exception as e:
            print(f"Warning: Could not load import providers: {e}")
            return ["Provider_Import_1", "Provider_Import_2"]

    def _load_dealer_mapping(self):
        """Load dealer mapping."""
        try:
            return pd.read_csv("data/rep_dealer_mapping.csv", encoding="utf-8")
        except Exception as e:
            print(f"Warning: Could not load dealer mapping: {e}")
            return pd.DataFrame(columns=["Rep Name", "Dealer Name", "Dealer ID"])

    def classify(self, ticket_text: str, ticket_subject: str = "") -> Dict[str, Any]:
        """
        Classify a ticket using Hybrid approach:
        - GPT-5 extracts entities/facts
        - Python decision tree determines classifications

        Args:
            ticket_text: The ticket content
            ticket_subject: Optional ticket subject

        Returns:
            Classification result dictionary
        """
        # Prepare input
        full_text = f"Subject: {ticket_subject}\n\n{ticket_text}" if ticket_subject else ticket_text

        try:
            # PHASE 1: GPT-5 Entity Extraction
            entities = self._extract_entities(full_text)

            # PHASE 2: Python Decision Tree Classification
            classification = self._classify_from_entities(entities)

            # PHASE 3: Enrich with dealer lookup from CSV
            classification = self._enrich_with_dealer_lookup(classification)

            # PHASE 4: Generate suggested response
            suggested_response = self._generate_response(classification, entities)

            # PHASE 5: Sentiment Analysis
            sentiment_data = self._analyze_sentiment(full_text, classification)

            return {
                "success": True,
                "classification": classification,
                "entities": entities,
                "suggested_response": suggested_response,
                "sentiment": sentiment_data
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "classification": self._empty_classification()
            }

    def _extract_entities(self, ticket_text: str) -> Dict[str, Any]:
        """
        PHASE 1: Use GPT-5 to extract raw entities and facts from the ticket.

        Args:
            ticket_text: Full ticket text including subject

        Returns:
            Dictionary of extracted entities
        """
        # Get syndicator and provider examples
        syndicator_examples = ", ".join(self.syndicators[:20]) if len(self.syndicators) > 20 else ", ".join(self.syndicators)
        provider_examples = ", ".join(self.import_providers)

        prompt = f"""You are an entity extraction assistant for automotive support tickets.

Extract ONLY the following information from the ticket and output as JSON:

{{
  "dealer_name": "Name of dealership mentioned (e.g., Dealership_1, Dealership_4)",
  "syndicators_mentioned": ["List of syndicators mentioned (e.g., Syndicator_Export_A, Syndicator_Export_B)"],
  "providers_mentioned": ["List of import providers mentioned (e.g., Provider_Import_1, Provider_Import_2)"],
  "inventory_type": "If explicitly stated: New, Used, Demo, New + Used, In-Transit, AS-IS, or CPO. Otherwise empty",
  "action_keywords": ["List of action words found: activate, cancel, setup, disable, problem, bug, question, urgent, review, etc."],
  "problem_indicators": ["ONLY mentions of technical issues, errors, malfunctions, or things not working properly. DO NOT include normal business requests like 'cancel', 'disable', or 'deactivate' here."],
  "urgency_indicators": ["Words indicating urgency: urgent, asap, threatening, frustrated, angry, critical, etc."],
  "multiple_dealers": true/false,
  "sentiment": "Overall emotional tone: Calm, Neutral, Concerned, Frustrated, Urgent, or Critical",
  "key_action_items": ["List of specific actions requested or needed (max 3 items)"],
  "additional_questions": ["Any questions asked (e.g., 'When will this be ready?', 'Can you confirm...?', 'Do we need...?', etc.)"],
  "special_requests": ["Any non-standard requests or special requirements mentioned (e.g., 'rush this', 'need custom settings', 'specific timing', etc.)"]
}}

**Available Syndicators:** {syndicator_examples}
**Available Providers:** {provider_examples}

**IMPORTANT DISTINCTIONS:**
- **Normal Business Requests** (NOT problems): activate, cancel, disable, deactivate, setup, remove feeds - these are routine operations
- **Actual Problems** (ARE problems): feed not working, data missing, errors, wrong data, delays, system issues, bugs, malfunctions

**Instructions:**
- Extract dealer names exactly as written
- If multiple dealers mentioned, list in syndicators_mentioned or providers_mentioned accordingly
- Only extract inventory_type if EXPLICITLY stated (not inferred)
- Look for action keywords that indicate what the user wants
- Flag urgency indicators ONLY for time-sensitive issues
- DO NOT classify cancellation/deactivation requests as problems - they are normal business operations
- DO NOT classify or categorize - just extract facts

Ticket to analyze:
{ticket_text}

Output only the JSON object with extracted entities:"""

        try:
            # Use cache for entity extraction (same ticket = same entities)
            def _call_api():
                response = self.client.responses.create(
                    model=self.model,
                    input=prompt,
                    reasoning={"effort": self.reasoning_effort}
                )
                return self._parse_json(response.output_text)
            
            # Cache based on prompt content
            entities = self.cache.cache_api_call(prompt, _call_api)

            # Ensure all expected keys exist
            default_entities = {
                "dealer_name": "",
                "syndicators_mentioned": [],
                "providers_mentioned": [],
                "inventory_type": "",
                "action_keywords": [],
                "problem_indicators": [],
                "urgency_indicators": [],
                "multiple_dealers": False,
                "sentiment": "Neutral",
                "key_action_items": [],
                "additional_questions": [],
                "special_requests": []
            }

            for key in default_entities:
                if key not in entities:
                    entities[key] = default_entities[key]

            return entities

        except Exception as e:
            print(f"Entity extraction error: {e}")
            return {
                "dealer_name": "",
                "syndicators_mentioned": [],
                "providers_mentioned": [],
                "inventory_type": "",
                "action_keywords": [],
                "problem_indicators": [],
                "urgency_indicators": [],
                "multiple_dealers": False,
                "sentiment": "Neutral",
                "key_action_items": [],
                "additional_questions": [],
                "special_requests": []
            }

    def _classify_from_entities(self, entities: Dict[str, Any]) -> Dict[str, str]:
        """
        PHASE 2: Use Python decision tree to classify based on extracted entities.

        Args:
            entities: Dictionary of entities from GPT extraction

        Returns:
            Complete classification dictionary
        """
        classification = self._empty_classification()

        # Extract action keywords, problem indicators, and urgency
        actions = [kw.lower() for kw in entities.get("action_keywords", [])]
        problems = entities.get("problem_indicators", [])
        urgency = entities.get("urgency_indicators", [])

        # Dealer name
        classification["dealer_name"] = entities.get("dealer_name", "")
        if entities.get("multiple_dealers"):
            # If multiple dealers, format appropriately
            synd = entities.get("syndicators_mentioned", [])
            prov = entities.get("providers_mentioned", [])
            if len(synd) > 1 or len(prov) > 1:
                classification["dealer_name"] = f"Multiple: {', '.join(synd + prov)}"

        # Inventory type
        inv_type = entities.get("inventory_type", "").strip()
        if inv_type and inv_type in self.valid_inventory_types:
            classification["inventory_type"] = inv_type
        else:
            classification["inventory_type"] = "Unspecified"

        # CATEGORY DECISION TREE
        # NOTE: Problem/Bug is checked FIRST per company policy - any problematic event = Problem/Bug
        if problems:
            # If ANY problem indicators found, classify as Problem/Bug
            classification["category"] = "Problem / Bug"
        elif any(word in actions for word in ["cancel", "deactivate", "disable", "stop", "remove"]):
            classification["category"] = "Product Cancellation"
        elif any(word in actions for word in ["activate", "setup", "enable", "start", "configure"]):
            # Determine if new or existing client based on context
            if any(word in actions for word in ["new", "onboard", "first"]):
                classification["category"] = "Product Activation — New Client"
            else:
                classification["category"] = "Product Activation — Existing Client"
        elif any(word in actions for word in ["question", "how", "can", "what", "why", "clarify"]):
            classification["category"] = "General Question"
        elif any(word in actions for word in ["review", "analyze", "check", "audit", "report"]):
            classification["category"] = "Analysis / Review"
        else:
            classification["category"] = "Other"

        # SUB-CATEGORY DECISION TREE
        syndicators = entities.get("syndicators_mentioned", [])
        providers = entities.get("providers_mentioned", [])

        if providers or any(word in actions for word in ["import", "importing", "feed in", "data in"]):
            classification["sub_category"] = "Import"
            # Assign provider - use first from list or default
            if providers:
                classification["provider"] = providers[0]
            else:
                # Default to first provider if import but no specific provider mentioned
                classification["provider"] = self.import_providers[0] if self.import_providers else "Provider_Import_1"
            classification["syndicator"] = ""
        elif syndicators or any(word in actions for word in ["export", "exporting", "feed out", "syndicate"]):
            classification["sub_category"] = "Export"
            # Assign syndicator - use first from list or default
            if syndicators:
                classification["syndicator"] = syndicators[0]
            else:
                # Default to first syndicator if export but no specific syndicator mentioned
                classification["syndicator"] = self.syndicators[0] if self.syndicators else "Syndicator_Export_1"
            classification["provider"] = ""
        else:
            # For "Other" sub-category, try to infer from syndicators/providers mentioned
            classification["sub_category"] = "Other"
            if syndicators:
                classification["syndicator"] = syndicators[0]
                classification["provider"] = ""
            elif providers:
                classification["provider"] = providers[0]
                classification["syndicator"] = ""
            else:
                # Default: assume export to first syndicator
                classification["syndicator"] = self.syndicators[0] if self.syndicators else "Syndicator_Export_1"
                classification["provider"] = ""

        # FINAL CHECK: Ensure at least one of syndicator/provider is filled
        if not classification["syndicator"] and not classification["provider"]:
            # If both still empty, default based on sub_category
            if classification["sub_category"] == "Import":
                classification["provider"] = self.import_providers[0] if self.import_providers else "Provider_Import_1"
            else:
                # Default to export
                classification["syndicator"] = self.syndicators[0] if self.syndicators else "Syndicator_Export_1"

        # TIER DECISION TREE
        # Extract additional complexity indicators
        additional_questions = entities.get("additional_questions", [])
        special_requests = entities.get("special_requests", [])
        has_complexity = bool(additional_questions) or bool(special_requests)

        if urgency or any(word in actions for word in ["urgent", "asap", "critical", "emergency", "threatening", "angry"]):
            # Urgent tickets always Tier 3
            classification["tier"] = "Tier 3"
        elif classification["category"] == "Problem / Bug":
            # All problems/bugs are Tier 2 or 3
            classification["tier"] = "Tier 2"
        elif classification["category"] in ["Product Activation — Existing Client"]:
            # SMART TIER LOGIC FOR PRODUCT ACTIVATION:
            # - If SIMPLE (just feed setup, no questions, no special requests) → Tier 1 (automatable)
            # - If COMPLEX (has questions or special requests) → Tier 2 (needs human)
            if has_complexity:
                classification["tier"] = "Tier 2"  # Needs human attention
            else:
                classification["tier"] = "Tier 1"  # Can be automated
        elif classification["category"] == "Product Activation — New Client":
            # New clients always need human touch
            classification["tier"] = "Tier 2"
        elif classification["category"] == "Product Cancellation":
            # SMART TIER LOGIC FOR PRODUCT CANCELLATION:
            # - If SIMPLE (just cancellation request, no questions) → Tier 1 (automatable)
            # - If COMPLEX (has questions or concerns) → Tier 2 (needs human)
            if has_complexity:
                classification["tier"] = "Tier 2"  # Needs human attention
            else:
                classification["tier"] = "Tier 1"  # Can be automated
        elif classification["category"] == "General Question":
            classification["tier"] = "Tier 1"
        else:
            classification["tier"] = "Tier 1"

        return classification

    def _build_system_prompt_old(self) -> str:
        """Build the classification system prompt."""
        categories = ", ".join(self.valid_categories)
        subcategories = ", ".join(self.valid_subcategories)
        inventory_types = ", ".join(self.valid_inventory_types)

        # Get top syndicators for the prompt (show first 20 as examples)
        syndicator_examples = ", ".join(self.syndicators[:20]) if len(self.syndicators) > 20 else ", ".join(self.syndicators)

        # Get import providers for the prompt
        provider_examples = ", ".join(self.import_providers)

        return f"""You are a Zoho Desk ticket classification assistant for an automotive syndication support team.

Your job: extract ONLY the following fields from incoming ticket/email messages and output a single JSON dictionary with these **exact keys** (no extras, no markdown, no explanations):

  - contact
  - dealer_name
  - dealer_id
  - rep
  - category
  - sub_category
  - syndicator
  - provider
  - inventory_type
  - tier

**CRITICAL RULE - ALL FIELDS MUST BE FILLED:**
- ALL fields must ALWAYS be classified (no empty strings allowed)
- ONLY EXCEPTION: provider and syndicator are mutually exclusive (either/or, never both)

**RULES FOR EVERY OUTPUT:**
- Category: REQUIRED - must be one of: {categories}
- Sub Category: REQUIRED - must be one of: {subcategories}
- Inventory Type: REQUIRED - must be one of: {inventory_types}
  - If explicitly mentioned (New, Used, Demo, New + Used), use that value
  - If NOT explicitly mentioned, use "Unspecified"
  - Do NOT try to infer inventory type if not stated
- Tier: REQUIRED - must be exactly "Tier 1", "Tier 2", or "Tier 3"
- Dealer Name: REQUIRED - extract from ANY mention of a dealership in the ticket

**SYNDICATOR vs PROVIDER (Mutually Exclusive):**
- If sub_category is "Export" → fill 'syndicator', leave 'provider' empty
- If sub_category is "Import" → fill 'provider', leave 'syndicator' empty
- Common syndicators (Export): {syndicator_examples}
- Import providers: {provider_examples}

**CRITICAL FIELD EXTRACTION:**
- **dealer_name** is THE MOST IMPORTANT field - extract it from ANY mention of a dealership in the ticket
- dealer_name must be the dealership/rooftop mentioned in the ticket (e.g., "Dealership_1", "Dealership_4")
- If multiple dealers mentioned, format as: 'Multiple: [Name1], [Name2]'
- Look for dealer names in: subject line, body text, signature, anywhere in the ticket

**OTHER FIELD LOGIC:**
- DO NOT extract 'contact', 'dealer_id', or 'rep' - these will be filled automatically from the dealer database
- Make intelligent inferences if information is not explicit
- If truly ambiguous, choose the most likely option based on context - DO NOT leave fields empty

**TIER CLASSIFICATION RULES:**
- **Tier 1 (Simple/Automated)**: General questions, status inquiries, information requests that can be answered automatically
- **Tier 2 (Human Required)**: Product activations/cancellations, configuration changes, setups requiring human verification
- **Tier 3 (Urgent/Critical)**: System outages, feeds not updating for days, angry/frustrated clients, revenue-impacting issues, threats to cancel service

**NO HALLUCINATIONS. NO EXTRAS. NO EXPLANATIONS.**

### Examples:

Example 1:
Message: "Hi Support Team, Dealership_4 is still showing vehicles that were sold last week. Request to check the Provider_Import_1 import."
JSON: {{"contact": "", "dealer_name": "Dealership_4", "dealer_id": "", "rep": "", "category": "Problem / Bug", "sub_category": "Import", "syndicator": "", "provider": "Provider_Import_1", "inventory_type": "Unspecified", "tier": "Tier 2"}}

Example 2:
Message: "Please cancel the Syndicator_Export_1 export for Dealership_3."
JSON: {{"contact": "", "dealer_name": "Dealership_3", "dealer_id": "", "rep": "", "category": "Product Cancellation", "sub_category": "Export", "syndicator": "Syndicator_Export_1", "provider": "", "inventory_type": "Unspecified", "tier": "Tier 2"}}

Example 3:
Message: "Quick question - can a dealer have separate feeds for new and used inventory?"
JSON: {{"contact": "", "dealer_name": "", "dealer_id": "", "rep": "", "category": "General Question", "sub_category": "Other", "syndicator": "", "provider": "", "inventory_type": "Unspecified", "tier": "Tier 1"}}

Example 4:
Message: "URGENT: Syndicator_Export_4 feed for Dealership_1 hasn't updated in 3 days. Client is calling constantly and threatening to cancel!"
JSON: {{"contact": "", "dealer_name": "Dealership_1", "dealer_id": "", "rep": "", "category": "Problem / Bug", "sub_category": "Export", "syndicator": "Syndicator_Export_4", "provider": "", "inventory_type": "Unspecified", "tier": "Tier 3"}}

Example 5:
Message: "New car pricing is not updating from Provider_Import_2 for Dealership_5. Website is off by $500."
JSON: {{"contact": "", "dealer_name": "Dealership_5", "dealer_id": "", "rep": "", "category": "Problem / Bug", "sub_category": "Import", "syndicator": "", "provider": "Provider_Import_2", "inventory_type": "New", "tier": "Tier 3"}}

ALWAYS output a single JSON object with all 10 fields present (including tier and provider), following the above strict format.

Classify the following message and output only the JSON object:"""

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Parse JSON from GPT response."""
        try:
            # Find JSON object in text
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > 0:
                json_str = text[start:end]
                return json.loads(json_str)
            return json.loads(text)
        except:
            return self._empty_classification()

    def _validate_classification(self, classification: Dict[str, Any]) -> Dict[str, str]:
        """Validate and clean up classification."""
        result = self._empty_classification()

        # Copy over valid fields
        for field in result.keys():
            if field in classification and classification[field]:
                result[field] = str(classification[field]).strip()

        # Validate dropdowns
        if result["category"] not in self.valid_categories:
            result["category"] = ""
        if result["sub_category"] not in self.valid_subcategories:
            result["sub_category"] = ""
        if result["inventory_type"] not in self.valid_inventory_types:
            result["inventory_type"] = "Unspecified"  # Default to Unspecified if invalid or missing
        if result["tier"] not in self.valid_tiers:
            result["tier"] = ""

        return result

    def _enrich_with_dealer_lookup(self, classification: Dict[str, str]) -> Dict[str, str]:
        """
        Enrich classification with dealer ID and rep from CSV lookup.

        Args:
            classification: Classification dict from GPT

        Returns:
            Enriched classification with dealer_id and rep filled in
        """
        dealer_name = classification.get("dealer_name", "").strip()

        if not dealer_name or dealer_name.startswith("Multiple:"):
            # Can't lookup multiple dealers or empty
            # But still set contact = rep if rep exists
            if classification.get("rep"):
                classification["contact"] = classification["rep"]
            return classification

        # Normalize dealer name for lookup (lowercase, strip)
        dealer_name_normalized = dealer_name.lower().strip()

        # Search in dealer mapping CSV
        if not self.dealer_mapping.empty:
            # Try exact match first
            match = self.dealer_mapping[
                self.dealer_mapping["Dealer Name"].str.lower().str.strip() == dealer_name_normalized
            ]

            if not match.empty:
                # Found exact match
                row = match.iloc[0]
                classification["dealer_id"] = str(row["Dealer ID"])
                classification["rep"] = str(row["Rep Name"])
                # Contact always equals rep
                classification["contact"] = str(row["Rep Name"])
            else:
                # Try partial match (contains)
                match = self.dealer_mapping[
                    self.dealer_mapping["Dealer Name"].str.lower().str.contains(dealer_name_normalized, na=False)
                ]

                if not match.empty:
                    # Found partial match, use first one
                    row = match.iloc[0]
                    classification["dealer_id"] = str(row["Dealer ID"])
                    classification["rep"] = str(row["Rep Name"])
                    classification["contact"] = str(row["Rep Name"])

        # If we still have rep but no contact, set contact = rep
        if classification.get("rep") and not classification.get("contact"):
            classification["contact"] = classification["rep"]

        return classification

    def _empty_classification(self) -> Dict[str, str]:
        """Return empty classification structure."""
        return {
            "contact": "",
            "dealer_name": "",
            "dealer_id": "",
            "rep": "",
            "category": "",
            "sub_category": "",
            "syndicator": "",
            "provider": "",
            "inventory_type": "Unspecified",
            "tier": ""
        }

    def _generate_response(self, classification: Dict[str, str], entities: Dict[str, Any]) -> str:
        """
        PHASE 4: Generate a suggested response based on classification and entities.
        Uses templates for speed and consistency.

        Args:
            classification: The classification result
            entities: The extracted entities

        Returns:
            Suggested response text
        """
        category = classification.get("category", "")
        sub_category = classification.get("sub_category", "")
        tier = classification.get("tier", "")
        dealer_name = classification.get("dealer_name", "")
        syndicator = classification.get("syndicator", "")
        provider = classification.get("provider", "")
        sentiment = entities.get("sentiment", "Neutral")

        # Template-based response generation for different categories
        response_templates = {
            "Problem / Bug": f"""Hi there,

Thank you for reporting this issue. I've escalated this ticket to our technical team for investigation.

**Issue Summary:**
- Dealer: {dealer_name if dealer_name else 'Multiple dealers'}
- {f'Syndicator: {syndicator}' if syndicator else f'Provider: {provider}'}
- Priority: {tier}

Our team will investigate and provide an update within 24 hours. We understand the urgency and appreciate your patience.

Best regards,
Support Team""",

            "Product Activation — Existing Client": f"""Hi there,

Thank you for your request. I'll process this activation for you right away.

**Activation Details:**
- Dealer: {dealer_name}
- {f'Syndicator: {syndicator}' if syndicator else f'Provider: {provider}'}
- Type: {classification.get('inventory_type', 'Unspecified')}

I'll send you a confirmation once the setup is complete, typically within 1-2 business days.

Best regards,
Support Team""",

            "Product Activation — New Client": f"""Hi there,

Welcome aboard! I'm excited to help you get started.

**Onboarding Details:**
- Dealer: {dealer_name}
- {f'Syndicator: {syndicator}' if syndicator else f'Provider: {provider}'}

Our onboarding team will reach out within 24 hours to guide you through the setup process.

Best regards,
Support Team""",

            "Product Cancellation": f"""Hi there,

I've received your cancellation request and will process it accordingly.

**Cancellation Details:**
- Dealer: {dealer_name if dealer_name else 'Multiple dealers'}
- {f'Syndicator: {syndicator}' if syndicator else f'Provider: {provider}'}

I'll send you a confirmation once the cancellation is complete.

Best regards,
Support Team""",

            "General Question": f"""Hi there,

Thank you for reaching out! I'd be happy to help answer your question.

Based on your inquiry, {' '.join(entities.get('key_action_items', [])[:2]) if entities.get('key_action_items') else 'I will provide you with the information you need'}.

Feel free to let me know if you need any clarification!

Best regards,
Support Team""",

            "Analysis / Review": f"""Hi there,

Thank you for your request. I've forwarded this to the appropriate team for review.

**Review Details:**
- Dealer: {dealer_name}
- Status: Under review

You'll receive an update once the analysis is complete.

Best regards,
Support Team"""
        }

        # Add sentiment-based tone adjustments
        if sentiment in ["Frustrated", "Critical", "Urgent"]:
            # For urgent/frustrated tickets, add empathy
            response = response_templates.get(category, "Thank you for contacting us. We'll review your request and get back to you shortly.")
            if category == "Problem / Bug":
                response = response.replace("Thank you for reporting this issue.",
                                          "Thank you for reporting this issue. I understand how frustrating this must be, and I sincerely apologize for the inconvenience.")
        else:
            response = response_templates.get(category, "Thank you for contacting us. We'll review your request and get back to you shortly.")

        return response

    def _analyze_sentiment(self, ticket_text: str, classification: Dict[str, str]) -> Dict[str, Any]:
        """
        PHASE 5: Analyze sentiment and urgency of the ticket.

        Args:
            ticket_text: The ticket content
            classification: The classification result

        Returns:
            Sentiment analysis result
        """
        try:
            sentiment_data = self.sentiment_analyzer.analyze_sentiment(ticket_text, classification)
            return sentiment_data
        except Exception as e:
            # Return default sentiment if analysis fails
            return {
                "score": 0,
                "label": "Neutral",
                "urgency_level": "Medium",
                "escalation_risk": "Low",
                "flags": [],
                "recommendations": []
            }


def load_mock_tickets():
    """Load mock ticket data."""
    try:
        with open("mock_data/sample_tickets.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading mock tickets: {e}")
        return []
