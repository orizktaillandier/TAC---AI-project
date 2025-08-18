"""
Core classification service using OpenAI GPT models.
"""
import json
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import unicodedata
import nltk
from openai import AsyncOpenAI
from sqlalchemy.orm import Session
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from zoho_integration import ZohoTicketFetcher

from app.core.config import settings
from app.db.models import Classification, AuditLog
from app.services.cache import CacheService
from app.services.zoho import ZohoService
from app.utils.dealer import extract_dealers, lookup_dealer_by_name, normalize_dealer_name
from app.utils.text import clean_text, detect_language

# Download NLTK data if needed
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

logger = logging.getLogger(__name__)


class ClassifierService:
    """Service for classifying tickets using OpenAI API."""
    
    def __init__(
        self, 
        db: Session,
        zoho_service: Optional[ZohoService] = None,
        cache_service: Optional[CacheService] = None
    ):
        """
        Initialize the classifier service.
        
        Args:
            db: Database session
            zoho_service: Zoho API service
            cache_service: Cache service
        """
        self.db = db
        self.zoho_service = zoho_service
        self.cache_service = cache_service
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Load syndicators and dealer mappings
        self._load_reference_data()
    
    def _load_reference_data(self):
        """Load reference data from CSV files."""
        # Load syndicators
        try:
            self.syndicators = pd.read_csv(settings.SYNDICATORS_CSV)["Syndicator"].dropna().tolist()
            self.approved_syndicators = set(s.lower() for s in self.syndicators)
            logger.info(f"Loaded {len(self.syndicators)} syndicators")
        except Exception as e:
            logger.error(f"Error loading syndicators: {e}")
            self.syndicators = []
            self.approved_syndicators = set()
        
        # Load dealer mappings
        try:
            self.dealer_mapping = pd.read_csv(settings.DEALER_MAPPING_CSV)
            logger.info(f"Loaded {len(self.dealer_mapping)} dealer mappings")
        except Exception as e:
            logger.error(f"Error loading dealer mappings: {e}")
            self.dealer_mapping = pd.DataFrame(columns=["Rep Name", "Dealer Name", "Dealer ID"])
    
    async def classify_ticket(
        self, 
        ticket_id: str, 
        ticket_text: Optional[str] = None,
        ticket_subject: Optional[str] = None,
        threads: Optional[List[Dict[str, Any]]] = None,
        use_cache: bool = True
    ) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """
        Classify a ticket.
        
        Args:
            ticket_id: The ticket ID
            ticket_text: The ticket text (optional)
            ticket_subject: The ticket subject (optional)
            threads: List of ticket threads (optional)
            use_cache: Whether to use cache
            
        Returns:
            Tuple of (classification_fields, raw_classification)
        """
        # Check cache first if enabled
        if use_cache and self.cache_service:
            cache_key = f"classification:{ticket_id}"
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for ticket {ticket_id}")
                return cached_result
        
        # If no ticket text/subject/threads provided, fetch from Zoho
        if not any([ticket_text, ticket_subject, threads]) and self.zoho_service:
            ticket_data, threads = await self.zoho_service.get_ticket_with_threads(ticket_id)
            if ticket_data:
                ticket_subject = ticket_data.get("subject", "")
                ticket_text = ticket_data.get("description", "")
        
        # Prepare full text for classification
        full_text = self._prepare_text_for_classification(ticket_subject, ticket_text, threads)
        
        # Call OpenAI for classification
        raw_classification = await self._call_openai_classifier(full_text)
        
        # Process and validate the classification
        fields = self._validate_classification(raw_classification, full_text)
        
        # Store in cache if enabled
        if self.cache_service:
            cache_key = f"classification:{ticket_id}"
            await self.cache_service.set(cache_key, (fields, raw_classification), 
                                        ttl=settings.CACHE_TTL)
        
        return fields, raw_classification
    
    def _prepare_text_for_classification(
        self,
        subject: Optional[str] = None,
        description: Optional[str] = None,
        threads: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Prepare text for classification.
        
        Args:
            subject: Ticket subject
            description: Ticket description
            threads: Ticket threads
            
        Returns:
            Prepared text for classification
        """
        parts = []
        
        if subject:
            parts.append(f"Subject: {subject}")
        
        if description:
            parts.append(description.strip())
        
        if threads:
            # Add up to 5 most recent threads
            for th in threads[:5]:
                body = th.get("summary") or th.get("content") or ""
                if isinstance(body, str) and body.strip():
                    # Add sender information if available
                    sender = ""
                    if th.get("author") and th.get("author").get("name"):
                        sender = f"From: {th.get('author').get('name')}\n"
                    elif th.get("fromEmailAddress"):
                        sender = f"From: {th.get('fromEmailAddress')}\n"
                    
                    parts.append(f"{sender}{body.strip()}")
        
        return "\n\n".join([p for p in parts if p.strip()])
        
    async def _call_openai_classifier(self, text: str) -> Dict[str, Any]:
        """
        Call OpenAI API to classify the ticket.
        
        Args:
            text: The text to classify
            
        Returns:
            Raw classification from OpenAI
        """
        system_prompt = self._get_system_prompt()
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text.strip()}
                ],
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=settings.OPENAI_MAX_TOKENS,
            )
            
            # Parse the response text as JSON
            response_text = response.choices[0].message.content
            return self._parse_gpt_json(response_text)
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            return {}
    
    def _parse_gpt_json(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON from OpenAI response.
        
        Args:
            response_text: Response text from OpenAI
            
        Returns:
            Parsed JSON or empty dict if parsing fails
        """
        try:
            # Find JSON object in the response text
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > 0:
                json_str = response_text[start:end]
                return json.loads(json_str)
            return {}
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse GPT response as JSON: {response_text}")
            return {}
        except Exception as e:
            logger.error(f"Error parsing GPT response: {str(e)}")
            return {}
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the classifier.
        
        Returns:
            System prompt string
        """
        return f"""
You are a Zoho Desk ticket classification assistant for an automotive syndication support team.

Your job: extract ONLY the following fields from incoming ticket/email messages and output a single JSON dictionary with these **exact keys** (no extras, no markdown, no explanations):

  - contact
  - dealer_name
  - dealer_id
  - rep
  - category
  - sub_category
  - syndicator
  - inventory_type

**RULES FOR EVERY OUTPUT:**
- Only use these dropdowns. If not found, leave blank.
- Category: {', '.join(settings.VALID_CATEGORIES)}
- Sub Category: {', '.join(settings.VALID_SUBCATEGORIES)}
- Inventory Type: {', '.join(settings.VALID_INVENTORY_TYPES)}
- Syndicator: Only allowed values loaded from syndicators.csv

**STRICT FIELD LOGIC:**
- 'dealer_name' must be the dealership/rooftop, not a group name (use 'Sunrise Ford', NOT 'Kot Auto Group')
- If multiple dealers mentioned, format as: 'Multiple: [Name1], [Name2]' and leave dealer_id blank
- Only set 'rep' if sender is actually that rep. Never default to analyst or staff unless they sent the ticket.
- The 'contact' is always the rep, **unless the ticket/email is from the client domain** (e.g., @auto, @cars, @[OEM]). If unsure, leave blank.
- The 'syndicator' is always the export/feed destination, not the import/source
- Never guess any field. If not 100% sure, output an empty string
- No invented or auto-corrected dropdown values—**only valid values**
- If info is missing or ambiguous, always output "" (empty string), never null or omit
- Use address blocks and signatures to extract dealership if not explicit in the body
- If a Dealer ID is not in our mapping CSV or from a trusted D2C sender, leave it blank

**NO HALLUCINATIONS. NO EXTRAS. NO EXPLANATIONS.**

---

### Examples (Use for grounding and format reference):

Example 1:  
Message:  
"Hi Véronique, Mazda Steele is still showing vehicles that were sold last week. Request to check the PBS import."  
JSON:  
{{"contact": "Véronique Fournier", "dealer_name": "Mazda Steele", "dealer_id": "2618", "rep": "Véronique Fournier", "category": "Problem / Bug", "sub_category": "Import", "syndicator": "", "inventory_type": ""}}

Example 2:  
Message:  
"Please cancel the Kijiji export for Number 7 Honda Sales Limited."  
JSON:  
{{"contact": "Lisa Payne", "dealer_name": "Number 7 Honda Sales Limited", "dealer_id": "2221", "rep": "Lisa Payne", "category": "Product Cancellation", "sub_category": "Export", "syndicator": "Kijiji", "inventory_type": ""}}

Example 3:  
Message:  
"Bonjour, Je ne sais pas si ça s'adresse à @Syndication D2C Media ou @Web Support D2C Media Pouvez-vous désactiver les rabais PRIX EMPLOYÉS FORD pour les 2 concessionnaire suivants : Donnacona Ford et La Pérade Ford."  
JSON:  
{{"contact": "Alexandra Biron", "dealer_name": "Multiple: Donnacona Ford, La Pérade Ford", "dealer_id": "", "rep": "Alexandra Biron", "category": "Product Cancellation", "sub_category": "Export", "syndicator": "", "inventory_type": ""}}

Example 4:  
Message:  
"Hi, can you confirm if the AccuTrade integration is live for Volvo Laval?"  
JSON:  
{{"contact": "Clio Perkins", "dealer_name": "Volvo Laval", "dealer_id": "2092", "rep": "Clio Perkins", "category": "General Question", "sub_category": "AccuTrade", "syndicator": "AccuTrade", "inventory_type": ""}}

Example 5:  
Message:  
"New car pricing is not updating from Quorum for Kelowna Hyundai. Client says inventory feed shows correct MSRP, but website is off by $500."  
JSON:  
{{"contact": "Cathleen Sun", "dealer_name": "Kelowna Hyundai", "dealer_id": "4042", "rep": "Cathleen Sun", "category": "Problem / Bug", "sub_category": "Import", "syndicator": "", "inventory_type": "New"}}

---

ALWAYS output a single JSON object with all 8 fields present (never null, never missing a key), following the above strict format.

---

Classify the following message and output only the JSON object:
"""
    
    def _validate_classification(self, raw_classification: Dict[str, Any], text: str) -> Dict[str, str]:
        """
        Validate and process the classification from OpenAI.
        
        Args:
            raw_classification: Raw classification from OpenAI
            text: Original text for fallback extraction
            
        Returns:
            Validated classification fields
        """
        # Initialize result with empty strings for all required fields
        result = {
            "contact": "",
            "dealer_name": "",
            "dealer_id": "",
            "rep": "",
            "category": "",
            "sub_category": "",
            "syndicator": "",
            "inventory_type": ""
        }
        
        # Update with values from raw classification
        for field in result.keys():
            if field in raw_classification and raw_classification[field]:
                result[field] = str(raw_classification[field]).strip()
        
        # Validate category
        if result["category"] not in settings.VALID_CATEGORIES:
            result["category"] = ""
            
        # Validate sub_category
        if result["sub_category"] not in settings.VALID_SUBCATEGORIES:
            result["sub_category"] = ""
            
        # Validate inventory_type
        if result["inventory_type"] not in settings.VALID_INVENTORY_TYPES:
            result["inventory_type"] = ""
            
        # Validate syndicator against approved list
        syndicator = result["syndicator"].lower()
        if syndicator and syndicator not in self.approved_syndicators:
            # Try to find a close match
            for s in self.approved_syndicators:
                if syndicator in s or s in syndicator:
                    result["syndicator"] = s.title()
                    break
            else:
                result["syndicator"] = ""
        
        # Verify dealer info using mapping
        if result["dealer_name"] and not result["dealer_name"].lower().startswith("multiple"):
            dealer_info = self._lookup_dealer(result["dealer_name"])
            if dealer_info:
                result["dealer_name"] = dealer_info.get("dealer_name", result["dealer_name"])
                result["dealer_id"] = dealer_info.get("dealer_id", result["dealer_id"])
                # Only set rep if empty and available from mapping
                if not result["rep"] and dealer_info.get("rep"):
                    result["rep"] = dealer_info.get("rep")
        
        # If fields are still empty, try fallback extraction
        if not result["dealer_name"] or not result["category"] or not result["sub_category"]:
            self._apply_fallback_extraction(result, text)
            
        return result
    
    def _lookup_dealer(self, dealer_name: str) -> Dict[str, str]:
        """
        Look up dealer information from the mapping.
        
        Args:
            dealer_name: Dealer name to look up
            
        Returns:
            Dictionary with dealer_name, dealer_id, rep
        """
        if not dealer_name or not isinstance(dealer_name, str):
            return {}
            
        # Normalize the dealer name
        normalized_name = normalize_dealer_name(dealer_name)
        
        try:
            # Convert all dealer names in the mapping to normalized form
            self.dealer_mapping["Normalized Name"] = self.dealer_mapping["Dealer Name"].apply(normalize_dealer_name)
            
            # 1. Try exact match
            exact_match = self.dealer_mapping[self.dealer_mapping["Normalized Name"] == normalized_name]
            if not exact_match.empty:
                row = exact_match.iloc[0]
                return {
                    "dealer_name": row["Dealer Name"],
                    "dealer_id": str(row["Dealer ID"]),
                    "rep": row["Rep Name"]
                }
                
            # 2. Try substring match
            for idx, row in self.dealer_mapping.iterrows():
                if normalized_name in row["Normalized Name"] or row["Normalized Name"] in normalized_name:
                    return {
                        "dealer_name": row["Dealer Name"],
                        "dealer_id": str(row["Dealer ID"]),
                        "rep": row["Rep Name"]
                    }
                    
            return {"dealer_name": dealer_name.title()}
            
        except Exception as e:
            logger.error(f"Error looking up dealer: {str(e)}")
            return {"dealer_name": dealer_name.title()}
    
    def _apply_fallback_extraction(self, result: Dict[str, str], text: str) -> None:
        """
        Apply fallback extraction logic for missing fields.
        
        Args:
            result: Current classification result to update
            text: Original text
        """
        # Lowercase text for case-insensitive matching
        text_lower = text.lower()
        
        # Try to extract dealer names if missing
        if not result["dealer_name"]:
            dealers = extract_dealers(text)
            if dealers:
                # Check if multiple dealers
                if len(dealers) > 1:
                    result["dealer_name"] = f"Multiple: {', '.join(d.title() for d in dealers)}"
                    result["dealer_id"] = ""  # Clear dealer_id for multiple dealers
                else:
                    # Look up single dealer
                    dealer_info = self._lookup_dealer(dealers[0])
                    result["dealer_name"] = dealer_info.get("dealer_name", dealers[0].title())
                    result["dealer_id"] = dealer_info.get("dealer_id", "")
                    if not result["rep"] and dealer_info.get("rep"):
                        result["rep"] = dealer_info.get("rep")
        
        # Try to extract syndicator if missing
        if not result["syndicator"]:
            for syndicator in self.syndicators:
                if syndicator.lower() in text_lower:
                    result["syndicator"] = syndicator
                    break
        
        # Try to infer category/subcategory from keywords
        if not result["category"] or not result["sub_category"]:
            # Cancellation patterns
            if any(w in text_lower for w in ["désactivation", "disable", "cancel", "terminate", "desactiver", "désactiver"]):
                result["category"] = "Product Cancellation"
                if "export" in text_lower:
                    result["sub_category"] = "Export"
                elif "import" in text_lower:
                    result["sub_category"] = "Import"
            
            # Activation patterns
            elif any(w in text_lower for w in ["activate", "enable", "setup", "set up"]):
                result["category"] = "Product Activation — Existing Client"
                if "export" in text_lower:
                    result["sub_category"] = "Export"
                elif "import" in text_lower:
                    result["sub_category"] = "Import"
            
            # Problem/Bug patterns
            elif any(w in text_lower for w in ["bug", "issue", "problem", "not working", "error", "fix"]):
                result["category"] = "Problem / Bug"
                if "export" in text_lower:
                    result["sub_category"] = "Export"
                elif "import" in text_lower:
                    result["sub_category"] = "Import"
            
            # AccuTrade specific
            elif "accutrade" in text_lower:
                result["category"] = "General Question" if not result["category"] else result["category"]
                result["sub_category"] = "AccuTrade"
            
            # Set defaults if still empty
            if not result["category"]:
                result["category"] = "Other"
            if not result["sub_category"]:
                result["sub_category"] = "Other"
        
        # Try to infer inventory type from keywords
        if not result["inventory_type"]:
            if "new" in text_lower and "used" in text_lower:
                result["inventory_type"] = "New + Used"
            elif "new" in text_lower:
                result["inventory_type"] = "New"
            elif "used" in text_lower:
                result["inventory_type"] = "Used"
            elif "demo" in text_lower:
                result["inventory_type"] = "Demo"
    
    async def classify_ticket_from_zoho(self, ticket_id: str, auto_push: bool = False):
        """
        Classify a ticket fetched from Zoho.
        
        Args:
            ticket_id: Zoho ticket ID
            auto_push: Whether to automatically push results back to Zoho
            
        Returns:
            Classification result with Zoho data
        """
        logger.info(f"Starting Zoho classification for ticket {ticket_id}")
        
        try:
            # Initialize Zoho fetcher
            zoho_fetcher = ZohoTicketFetcher()
            
            # Fetch ticket and threads from Zoho
            ticket_data, threads, error = await zoho_fetcher.get_ticket_with_threads(ticket_id)
            
            if error:
                logger.error(f"Failed to fetch ticket {ticket_id}: {error}")
                raise Exception(f"Failed to fetch ticket: {error}")
            
            if not ticket_data:
                raise Exception("No ticket data returned")
            
            # Prepare text for classification
            parts = []
            
            # Add subject
            if ticket_data.get("subject"):
                parts.append(f"Subject: {ticket_data['subject']}")
            
            # Add description if available
            if ticket_data.get("description"):
                parts.append(f"Description: {ticket_data['description']}")
            
            # Add thread content (limit to most recent 3 threads)
            if threads:
                parts.append("--- Conversation ---")
                for thread in threads[:3]:
                    author = thread.get("author_name", "Unknown")
                    content = thread.get("summary", thread.get("content", ""))
                    
                    if content and len(content.strip()) > 10:
                        parts.append(f"From {author}: {content}")
            
            full_text = "\n\n".join(parts)
            
            logger.info(f"Prepared {len(full_text)} characters for classification")
            
            # Classify using existing method
            fields, raw = await self.classify_ticket(
                ticket_id=ticket_id,
                ticket_text=full_text,
                ticket_subject=ticket_data.get("subject"),
                use_cache=True
            )
            
            # Store classification in database
            db_classification = await self.store_classification(
                ticket_id=ticket_id,
                classification=fields,
                raw_classification=raw,
                ticket_subject=ticket_data.get("subject"),
                ticket_content=full_text,
                ticket_metadata={
                    "zoho_data": {
                        "ticket_number": ticket_data.get("ticket_number"),
                        "status": ticket_data.get("status"),
                        "created_time": ticket_data.get("created_time"),
                        "web_url": ticket_data.get("web_url"),
                        "custom_fields_count": len(ticket_data.get("custom_fields", {}))
                    }
                }
            )
            
            # Auto-push if requested
            push_result = {"pushed": False}
            if auto_push:
                logger.info(f"Auto-pushing classification for ticket {ticket_id}")
                
                try:
                    # Prepare updates for custom fields
                    updates = {}
                    
                    if fields.get("syndicator"):
                        updates["cf_syndicators"] = fields["syndicator"]
                    
                    if fields.get("inventory_type"):
                        updates["cf_inventory_type"] = fields["inventory_type"]
                    
                    if fields.get("category"):
                        updates["category"] = fields["category"]
                    
                    if fields.get("sub_category"):
                        updates["subCategory"] = fields["sub_category"]
                    
                    if updates:
                        success, push_error = await zoho_fetcher.update_ticket_fields(ticket_id, updates)
                        if success:
                            logger.info(f"Successfully pushed classification to Zoho for ticket {ticket_id}")
                            push_result = {"pushed": True, "fields_updated": list(updates.keys())}
                        else:
                            logger.error(f"Failed to push to Zoho: {push_error}")
                            push_result = {"pushed": False, "error": push_error}
                    
                except Exception as push_ex:
                    logger.error(f"Auto-push failed: {str(push_ex)}")
                    push_result = {"pushed": False, "error": str(push_ex)}
            
            # Build response
            result = {
                "ticket_id": ticket_id,
                "classification": fields,
                "raw_classification": raw,
                "confidence_score": getattr(db_classification, 'confidence_score', None),
                "zoho_data": {
                    "subject": ticket_data.get("subject"),
                    "status": ticket_data.get("status"),
                    "ticket_number": ticket_data.get("ticket_number"),
                    "web_url": ticket_data.get("web_url"),
                    "threads_count": len(threads),
                    "existing_syndicator": ticket_data.get("syndicator"),
                    "existing_inventory_type": ticket_data.get("inventory_type")
                },
                "push_result": push_result
            }
            
            logger.info(f"Classification completed for ticket {ticket_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in Zoho classification for ticket {ticket_id}: {str(e)}")
            raise
        
    async def store_classification(
        self, 
        ticket_id: str,
        classification: Dict[str, str],
        raw_classification: Dict[str, Any],
        ticket_subject: Optional[str] = None,
        ticket_content: Optional[str] = None,
        ticket_metadata: Optional[Dict[str, Any]] = None,
        confidence_score: Optional[float] = None,
        user_id: Optional[int] = None
    ) -> Classification:
        """
        Store classification in the database.
        
        Args:
            ticket_id: Ticket ID
            classification: Classification fields
            raw_classification: Raw classification from OpenAI
            ticket_subject: Ticket subject
            ticket_content: Ticket content
            ticket_metadata: Additional ticket metadata
            confidence_score: Classification confidence score
            user_id: User ID who initiated the classification
            
        Returns:
            Classification object
        """
        # Check if classification already exists
        existing = self.db.query(Classification).filter(
            Classification.ticket_id == ticket_id
        ).first()
        
        if existing:
            # Update existing classification
            for key, value in classification.items():
                setattr(existing, key, value)
                
            existing.raw_classification = raw_classification
            
            if confidence_score is not None:
                existing.confidence_score = confidence_score
                
            if ticket_subject:
                existing.ticket_subject = ticket_subject
                
            if ticket_content:
                existing.ticket_content = ticket_content
                
            if ticket_metadata:
                existing.ticket_metadata = ticket_metadata
                
            if user_id:
                existing.user_id = user_id
                
            self.db.commit()
            self.db.refresh(existing)
            
            # Log the update
            audit_log = AuditLog(
                action="update",
                entity_type="classification",
                entity_id=str(existing.id),
                details={"changes": classification},
                status="success",
                user_id=user_id,
                classification_id=existing.id
            )
            self.db.add(audit_log)
            self.db.commit()
            
            return existing
        else:
            # Create new classification
            db_classification = Classification(
                ticket_id=ticket_id,
                **classification,
                raw_classification=raw_classification,
                confidence_score=confidence_score,
                ticket_subject=ticket_subject,
                ticket_content=ticket_content,
                ticket_metadata=ticket_metadata,
                user_id=user_id
            )
            
            self.db.add(db_classification)
            self.db.commit()
            self.db.refresh(db_classification)
            
            # Log the creation
            audit_log = AuditLog(
                action="create",
                entity_type="classification",
                entity_id=str(db_classification.id),
                details={"classification": classification},
                status="success",
                user_id=user_id,
                classification_id=db_classification.id
            )
            self.db.add(audit_log)
            self.db.commit()
            
            return db_classification
    
    async def push_to_zoho(
        self,
        ticket_id: str,
        classification_id: Optional[int] = None,
        dry_run: bool = False,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Push classification to Zoho.
        
        Args:
            ticket_id: Ticket ID
            classification_id: Classification ID (optional)
            dry_run: If True, only preview changes without applying
            user_id: User ID who initiated the push
            
        Returns:
            Dictionary with push results
        """
        if not self.zoho_service:
            return {
                "ticket_id": ticket_id,
                "status": "error",
                "errors": ["Zoho service not available"],
                "dry_run": dry_run
            }
        
        # Get classification
        if classification_id:
            db_classification = self.db.query(Classification).filter(
                Classification.id == classification_id
            ).first()
        else:
            db_classification = self.db.query(Classification).filter(
                Classification.ticket_id == ticket_id
            ).order_by(Classification.created_at.desc()).first()
        
        if not db_classification:
            return {
                "ticket_id": ticket_id,
                "status": "error",
                "errors": ["Classification not found"],
                "dry_run": dry_run
            }
        
        # Build Zoho update payload
        update_data = self._build_zoho_payload(db_classification)
        
        # Preview changes
        changes = await self.zoho_service.preview_ticket_update(ticket_id, update_data)
        
        if dry_run:
            # Log the dry run
            audit_log = AuditLog(
                action="push_dry_run",
                entity_type="classification",
                entity_id=str(db_classification.id),
                details={"changes": changes, "payload": update_data},
                status="success",
                user_id=user_id,
                classification_id=db_classification.id
            )
            self.db.add(audit_log)
            self.db.commit()
            
            return {
                "ticket_id": ticket_id,
                "status": "preview",
                "fields": list(update_data.keys()),
                "changes": changes,
                "dry_run": True
            }
        
        # Actually push changes to Zoho
        success, errors = await self.zoho_service.update_ticket(ticket_id, update_data)
        
        if success:
            # Update classification status
            db_classification.is_pushed = True
            db_classification.pushed_at = pd.Timestamp.now().tz_localize("UTC")
            self.db.commit()
            
            # Log the push
            audit_log = AuditLog(
                action="push",
                entity_type="classification",
                entity_id=str(db_classification.id),
                details={"payload": update_data, "changes": changes},
                status="success",
                user_id=user_id,
                classification_id=db_classification.id
            )
            self.db.add(audit_log)
            self.db.commit()
            
            return {
                "ticket_id": ticket_id,
                "status": "success",
                "fields": list(update_data.keys()),
                "changes": changes,
                "dry_run": False
            }
        else:
            # Log the failed push
            audit_log = AuditLog(
                action="push",
                entity_type="classification",
                entity_id=str(db_classification.id),
                details={"payload": update_data, "errors": errors},
                status="error",
                user_id=user_id,
                classification_id=db_classification.id
            )
            self.db.add(audit_log)
            self.db.commit()
            
            return {
                "ticket_id": ticket_id,
                "status": "error",
                "errors": errors,
                "fields": list(update_data.keys()),
                "changes": changes,
                "dry_run": False
            }
    
    def _build_zoho_payload(self, classification: Classification) -> Dict[str, Any]:
        """
        Build Zoho API update payload from classification.
        
        Args:
            classification: Classification object
            
        Returns:
            Zoho API update payload
        """
        payload = {}
        
        # Category and subcategory
        if classification.category:
            payload["category"] = classification.category
        if classification.sub_category:
            payload["subCategory"] = classification.sub_category
        
        # Custom fields for syndicator and inventory type
        custom_fields = {}
        if classification.syndicator:
            custom_fields["cf_syndicators"] = classification.syndicator
        if classification.inventory_type:
            custom_fields["cf_inventory_type"] = classification.inventory_type
        
        if custom_fields:
            payload["cf"] = custom_fields
        
        return payload
    
    async def process_batch(
        self, 
        ticket_ids: List[str],
        auto_push: bool = False,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Process a batch of tickets.
        
        Args:
            ticket_ids: List of ticket IDs
            auto_push: If True, automatically push classifications to Zoho
            user_id: User ID who initiated the batch
            
        Returns:
            List of result dictionaries
        """
        results = []
        
        for ticket_id in ticket_ids:
            try:
                # Classify the ticket
                fields, raw = await self.classify_ticket(ticket_id)
                
                # Store the classification
                db_classification = await self.store_classification(
                    ticket_id=ticket_id,
                    classification=fields,
                    raw_classification=raw,
                    user_id=user_id
                )
                
                result = {
                    "ticket_id": ticket_id,
                    "status": "success",
                    "classification": fields,
                    "pushed": False
                }
                
                # Push to Zoho if auto_push is enabled
                if auto_push:
                    push_result = await self.push_to_zoho(
                        ticket_id=ticket_id,
                        classification_id=db_classification.id,
                        user_id=user_id
                    )
                    
                    result["pushed"] = push_result["status"] == "success"
                    result["updated"] = push_result.get("fields", [])
                    
                    if push_result["status"] == "error":
                        result["errors"] = push_result.get("errors", [])
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing ticket {ticket_id}: {str(e)}")
                results.append({
                    "ticket_id": ticket_id,
                    "status": "error",
                    "errors": [str(e)]
                })
        
        return results
, AuditLog
from app.services.cache import CacheService
from app.services.zoho import ZohoService
from app.utils.dealer import extract_dealers, lookup_dealer_by_name, normalize_dealer_name
from app.utils.text import clean_text, detect_language

# Download NLTK data if needed
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

logger = logging.getLogger(__name__)


class ClassifierService:
    """Service for classifying tickets using OpenAI API."""
    
    def __init__(
        self, 
        db: Session,
        zoho_service: Optional[ZohoService] = None,
        cache_service: Optional[CacheService] = None
    ):
        """
        Initialize the classifier service.
        
        Args:
            db: Database session
            zoho_service: Zoho API service
            cache_service: Cache service
        """
        self.db = db
        self.zoho_service = zoho_service
        self.cache_service = cache_service
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Load syndicators and dealer mappings
        self._load_reference_data()
    
    def _load_reference_data(self):
        """Load reference data from CSV files."""
        # Load syndicators
        try:
            self.syndicators = pd.read_csv(settings.SYNDICATORS_CSV)["Syndicator"].dropna().tolist()
            self.approved_syndicators = set(s.lower() for s in self.syndicators)
            logger.info(f"Loaded {len(self.syndicators)} syndicators")
        except Exception as e:
            logger.error(f"Error loading syndicators: {e}")
            self.syndicators = []
            self.approved_syndicators = set()
        
        # Load dealer mappings
        try:
            self.dealer_mapping = pd.read_csv(settings.DEALER_MAPPING_CSV)
            logger.info(f"Loaded {len(self.dealer_mapping)} dealer mappings")
        except Exception as e:
            logger.error(f"Error loading dealer mappings: {e}")
            self.dealer_mapping = pd.DataFrame(columns=["Rep Name", "Dealer Name", "Dealer ID"])
    
    async def classify_ticket(
        self, 
        ticket_id: str, 
        ticket_text: Optional[str] = None,
        ticket_subject: Optional[str] = None,
        threads: Optional[List[Dict[str, Any]]] = None,
        use_cache: bool = True
    ) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """
        Classify a ticket.
        
        Args:
            ticket_id: The ticket ID
            ticket_text: The ticket text (optional)
            ticket_subject: The ticket subject (optional)
            threads: List of ticket threads (optional)
            use_cache: Whether to use cache
            
        Returns:
            Tuple of (classification_fields, raw_classification)
        """
        # Check cache first if enabled
        if use_cache and self.cache_service:
            cache_key = f"classification:{ticket_id}"
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for ticket {ticket_id}")
                return cached_result
        
        # If no ticket text/subject/threads provided, fetch from Zoho
        if not any([ticket_text, ticket_subject, threads]) and self.zoho_service:
            ticket_data, threads = await self.zoho_service.get_ticket_with_threads(ticket_id)
            if ticket_data:
                ticket_subject = ticket_data.get("subject", "")
                ticket_text = ticket_data.get("description", "")
        
        # Prepare full text for classification
        full_text = self._prepare_text_for_classification(ticket_subject, ticket_text, threads)
        
        # Call OpenAI for classification
        raw_classification = await self._call_openai_classifier(full_text)
        
        # Process and validate the classification
        fields = self._validate_classification(raw_classification, full_text)
        
        # Store in cache if enabled
        if self.cache_service:
            cache_key = f"classification:{ticket_id}"
            await self.cache_service.set(cache_key, (fields, raw_classification), 
                                        ttl=settings.CACHE_TTL)
        
        return fields, raw_classification
    
    def _prepare_text_for_classification(
        self,
        subject: Optional[str] = None,
        description: Optional[str] = None,
        threads: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Prepare text for classification.
        
        Args:
            subject: Ticket subject
            description: Ticket description
            threads: Ticket threads
            
        Returns:
            Prepared text for classification
        """
        parts = []
        
        if subject:
            parts.append(f"Subject: {subject}")
        
        if description:
            parts.append(description.strip())
        
        if threads:
            # Add up to 5 most recent threads
            for th in threads[:5]:
                body = th.get("summary") or th.get("content") or ""
                if isinstance(body, str) and body.strip():
                    # Add sender information if available
                    sender = ""
                    if th.get("author") and th.get("author").get("name"):
                        sender = f"From: {th.get('author').get('name')}\n"
                    elif th.get("fromEmailAddress"):
                        sender = f"From: {th.get('fromEmailAddress')}\n"
                    
                    parts.append(f"{sender}{body.strip()}")
        
        return "\n\n".join([p for p in parts if p.strip()])
        
    async def _call_openai_classifier(self, text: str) -> Dict[str, Any]:
        """
        Call OpenAI API to classify the ticket.
        
        Args:
            text: The text to classify
            
        Returns:
            Raw classification from OpenAI
        """
        system_prompt = self._get_system_prompt()
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text.strip()}
                ],
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=settings.OPENAI_MAX_TOKENS,
            )
            
            # Parse the response text as JSON
            response_text = response.choices[0].message.content
            return self._parse_gpt_json(response_text)
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            return {}
    
    def _parse_gpt_json(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON from OpenAI response.
        
        Args:
            response_text: Response text from OpenAI
            
        Returns:
            Parsed JSON or empty dict if parsing fails
        """
        try:
            # Find JSON object in the response text
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > 0:
                json_str = response_text[start:end]
                return json.loads(json_str)
            return {}
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse GPT response as JSON: {response_text}")
            return {}
        except Exception as e:
            logger.error(f"Error parsing GPT response: {str(e)}")
            return {}
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the classifier.
        
        Returns:
            System prompt string
        """
        return f"""
You are a Zoho Desk ticket classification assistant for an automotive syndication support team.

Your job: extract ONLY the following fields from incoming ticket/email messages and output a single JSON dictionary with these **exact keys** (no extras, no markdown, no explanations):

  - contact
  - dealer_name
  - dealer_id
  - rep
  - category
  - sub_category
  - syndicator
  - inventory_type

**RULES FOR EVERY OUTPUT:**
- Only use these dropdowns. If not found, leave blank.
- Category: {', '.join(settings.VALID_CATEGORIES)}
- Sub Category: {', '.join(settings.VALID_SUBCATEGORIES)}
- Inventory Type: {', '.join(settings.VALID_INVENTORY_TYPES)}
- Syndicator: Only allowed values loaded from syndicators.csv

**STRICT FIELD LOGIC:**
- 'dealer_name' must be the dealership/rooftop, not a group name (use 'Sunrise Ford', NOT 'Kot Auto Group')
- If multiple dealers mentioned, format as: 'Multiple: [Name1], [Name2]' and leave dealer_id blank
- Only set 'rep' if sender is actually that rep. Never default to analyst or staff unless they sent the ticket.
- The 'contact' is always the rep, **unless the ticket/email is from the client domain** (e.g., @auto, @cars, @[OEM]). If unsure, leave blank.
- The 'syndicator' is always the export/feed destination, not the import/source
- Never guess any field. If not 100% sure, output an empty string
- No invented or auto-corrected dropdown values—**only valid values**
- If info is missing or ambiguous, always output "" (empty string), never null or omit
- Use address blocks and signatures to extract dealership if not explicit in the body
- If a Dealer ID is not in our mapping CSV or from a trusted D2C sender, leave it blank

**NO HALLUCINATIONS. NO EXTRAS. NO EXPLANATIONS.**

---

### Examples (Use for grounding and format reference):

Example 1:  
Message:  
"Hi Véronique, Mazda Steele is still showing vehicles that were sold last week. Request to check the PBS import."  
JSON:  
{{"contact": "Véronique Fournier", "dealer_name": "Mazda Steele", "dealer_id": "2618", "rep": "Véronique Fournier", "category": "Problem / Bug", "sub_category": "Import", "syndicator": "", "inventory_type": ""}}

Example 2:  
Message:  
"Please cancel the Kijiji export for Number 7 Honda Sales Limited."  
JSON:  
{{"contact": "Lisa Payne", "dealer_name": "Number 7 Honda Sales Limited", "dealer_id": "2221", "rep": "Lisa Payne", "category": "Product Cancellation", "sub_category": "Export", "syndicator": "Kijiji", "inventory_type": ""}}

Example 3:  
Message:  
"Bonjour, Je ne sais pas si ça s'adresse à @Syndication D2C Media ou @Web Support D2C Media Pouvez-vous désactiver les rabais PRIX EMPLOYÉS FORD pour les 2 concessionnaire suivants : Donnacona Ford et La Pérade Ford."  
JSON:  
{{"contact": "Alexandra Biron", "dealer_name": "Multiple: Donnacona Ford, La Pérade Ford", "dealer_id": "", "rep": "Alexandra Biron", "category": "Product Cancellation", "sub_category": "Export", "syndicator": "", "inventory_type": ""}}

Example 4:  
Message:  
"Hi, can you confirm if the AccuTrade integration is live for Volvo Laval?"  
JSON:  
{{"contact": "Clio Perkins", "dealer_name": "Volvo Laval", "dealer_id": "2092", "rep": "Clio Perkins", "category": "General Question", "sub_category": "AccuTrade", "syndicator": "AccuTrade", "inventory_type": ""}}

Example 5:  
Message:  
"New car pricing is not updating from Quorum for Kelowna Hyundai. Client says inventory feed shows correct MSRP, but website is off by $500."  
JSON:  
{{"contact": "Cathleen Sun", "dealer_name": "Kelowna Hyundai", "dealer_id": "4042", "rep": "Cathleen Sun", "category": "Problem / Bug", "sub_category": "Import", "syndicator": "", "inventory_type": "New"}}

---

ALWAYS output a single JSON object with all 8 fields present (never null, never missing a key), following the above strict format.

---

Classify the following message and output only the JSON object:
"""
    
    def _validate_classification(self, raw_classification: Dict[str, Any], text: str) -> Dict[str, str]:
        """
        Validate and process the classification from OpenAI.
        
        Args:
            raw_classification: Raw classification from OpenAI
            text: Original text for fallback extraction
            
        Returns:
            Validated classification fields
        """
        # Initialize result with empty strings for all required fields
        result = {
            "contact": "",
            "dealer_name": "",
            "dealer_id": "",
            "rep": "",
            "category": "",
            "sub_category": "",
            "syndicator": "",
            "inventory_type": ""
        }
        
        # Update with values from raw classification
        for field in result.keys():
            if field in raw_classification and raw_classification[field]:
                result[field] = str(raw_classification[field]).strip()
        
        # Validate category
        if result["category"] not in settings.VALID_CATEGORIES:
            result["category"] = ""
            
        # Validate sub_category
        if result["sub_category"] not in settings.VALID_SUBCATEGORIES:
            result["sub_category"] = ""
            
        # Validate inventory_type
        if result["inventory_type"] not in settings.VALID_INVENTORY_TYPES:
            result["inventory_type"] = ""
            
        # Validate syndicator against approved list
        syndicator = result["syndicator"].lower()
        if syndicator and syndicator not in self.approved_syndicators:
            # Try to find a close match
            for s in self.approved_syndicators:
                if syndicator in s or s in syndicator:
                    result["syndicator"] = s.title()
                    break
            else:
                result["syndicator"] = ""
        
        # Verify dealer info using mapping
        if result["dealer_name"] and not result["dealer_name"].lower().startswith("multiple"):
            dealer_info = self._lookup_dealer(result["dealer_name"])
            if dealer_info:
                result["dealer_name"] = dealer_info.get("dealer_name", result["dealer_name"])
                result["dealer_id"] = dealer_info.get("dealer_id", result["dealer_id"])
                # Only set rep if empty and available from mapping
                if not result["rep"] and dealer_info.get("rep"):
                    result["rep"] = dealer_info.get("rep")
        
        # If fields are still empty, try fallback extraction
        if not result["dealer_name"] or not result["category"] or not result["sub_category"]:
            self._apply_fallback_extraction(result, text)
            
        return result
    
    def _lookup_dealer(self, dealer_name: str) -> Dict[str, str]:
        """
        Look up dealer information from the mapping.
        
        Args:
            dealer_name: Dealer name to look up
            
        Returns:
            Dictionary with dealer_name, dealer_id, rep
        """
        if not dealer_name or not isinstance(dealer_name, str):
            return {}
            
        # Normalize the dealer name
        normalized_name = normalize_dealer_name(dealer_name)
        
        try:
            # Convert all dealer names in the mapping to normalized form
            self.dealer_mapping["Normalized Name"] = self.dealer_mapping["Dealer Name"].apply(normalize_dealer_name)
            
            # 1. Try exact match
            exact_match = self.dealer_mapping[self.dealer_mapping["Normalized Name"] == normalized_name]
            if not exact_match.empty:
                row = exact_match.iloc[0]
                return {
                    "dealer_name": row["Dealer Name"],
                    "dealer_id": str(row["Dealer ID"]),
                    "rep": row["Rep Name"]
                }
                
            # 2. Try substring match
            for idx, row in self.dealer_mapping.iterrows():
                if normalized_name in row["Normalized Name"] or row["Normalized Name"] in normalized_name:
                    return {
                        "dealer_name": row["Dealer Name"],
                        "dealer_id": str(row["Dealer ID"]),
                        "rep": row["Rep Name"]
                    }
                    
            return {"dealer_name": dealer_name.title()}
            
        except Exception as e:
            logger.error(f"Error looking up dealer: {str(e)}")
            return {"dealer_name": dealer_name.title()}
    
    def _apply_fallback_extraction(self, result: Dict[str, str], text: str) -> None:
        """
        Apply fallback extraction logic for missing fields.
        
        Args:
            result: Current classification result to update
            text: Original text
        """
        # Lowercase text for case-insensitive matching
        text_lower = text.lower()
        
        # Try to extract dealer names if missing
        if not result["dealer_name"]:
            dealers = extract_dealers(text)
            if dealers:
                # Check if multiple dealers
                if len(dealers) > 1:
                    result["dealer_name"] = f"Multiple: {', '.join(d.title() for d in dealers)}"
                    result["dealer_id"] = ""  # Clear dealer_id for multiple dealers
                else:
                    # Look up single dealer
                    dealer_info = self._lookup_dealer(dealers[0])
                    result["dealer_name"] = dealer_info.get("dealer_name", dealers[0].title())
                    result["dealer_id"] = dealer_info.get("dealer_id", "")
                    if not result["rep"] and dealer_info.get("rep"):
                        result["rep"] = dealer_info.get("rep")
        
        # Try to extract syndicator if missing
        if not result["syndicator"]:
            for syndicator in self.syndicators:
                if syndicator.lower() in text_lower:
                    result["syndicator"] = syndicator
                    break
        
        # Try to infer category/subcategory from keywords
        if not result["category"] or not result["sub_category"]:
            # Cancellation patterns
            if any(w in text_lower for w in ["désactivation", "disable", "cancel", "terminate", "desactiver", "désactiver"]):
                result["category"] = "Product Cancellation"
                if "export" in text_lower:
                    result["sub_category"] = "Export"
                elif "import" in text_lower:
                    result["sub_category"] = "Import"
            
            # Activation patterns
            elif any(w in text_lower for w in ["activate", "enable", "setup", "set up"]):
                result["category"] = "Product Activation — Existing Client"
                if "export" in text_lower:
                    result["sub_category"] = "Export"
                elif "import" in text_lower:
                    result["sub_category"] = "Import"
            
            # Problem/Bug patterns
            elif any(w in text_lower for w in ["bug", "issue", "problem", "not working", "error", "fix"]):
                result["category"] = "Problem / Bug"
                if "export" in text_lower:
                    result["sub_category"] = "Export"
                elif "import" in text_lower:
                    result["sub_category"] = "Import"
            
            # AccuTrade specific
            elif "accutrade" in text_lower:
                result["category"] = "General Question" if not result["category"] else result["category"]
                result["sub_category"] = "AccuTrade"
            
            # Set defaults if still empty
            if not result["category"]:
                result["category"] = "Other"
            if not result["sub_category"]:
                result["sub_category"] = "Other"
        
        # Try to infer inventory type from keywords
        if not result["inventory_type"]:
            if "new" in text_lower and "used" in text_lower:
                result["inventory_type"] = "New + Used"
            elif "new" in text_lower:
                result["inventory_type"] = "New"
            elif "used" in text_lower:
                result["inventory_type"] = "Used"
            elif "demo" in text_lower:
                result["inventory_type"] = "Demo"
    
    async def store_classification(
        self, 
        ticket_id: str,
        classification: Dict[str, str],
        raw_classification: Dict[str, Any],
        ticket_subject: Optional[str] = None,
        ticket_content: Optional[str] = None,
        ticket_metadata: Optional[Dict[str, Any]] = None,
        confidence_score: Optional[float] = None,
        user_id: Optional[int] = None
    ) -> Classification:
        """
        Store classification in the database.
        
        Args:
            ticket_id: Ticket ID
            classification: Classification fields
            raw_classification: Raw classification from OpenAI
            ticket_subject: Ticket subject
            ticket_content: Ticket content
            ticket_metadata: Additional ticket metadata
            confidence_score: Classification confidence score
            user_id: User ID who initiated the classification
            
        Returns:
            Classification object
        """
        # Check if classification already exists
        existing = self.db.query(Classification).filter(
            Classification.ticket_id == ticket_id
        ).first()
        
        if existing:
            # Update existing classification
            for key, value in classification.items():
                setattr(existing, key, value)
                
            existing.raw_classification = raw_classification
            
            if confidence_score is not None:
                existing.confidence_score = confidence_score
                
            if ticket_subject:
                existing.ticket_subject = ticket_subject
                
            if ticket_content:
                existing.ticket_content = ticket_content
                
            if ticket_metadata:
                existing.ticket_metadata = ticket_metadata
                
            if user_id:
                existing.user_id = user_id
                
            self.db.commit()
            self.db.refresh(existing)
            
            # Log the update
            audit_log = AuditLog(
                action="update",
                entity_type="classification",
                entity_id=str(existing.id),
                details={"changes": classification},
                status="success",
                user_id=user_id,
                classification_id=existing.id
            )
            self.db.add(audit_log)
            self.db.commit()
            
            return existing
        else:
            # Create new classification
            db_classification = Classification(
                ticket_id=ticket_id,
                **classification,
                raw_classification=raw_classification,
                confidence_score=confidence_score,
                ticket_subject=ticket_subject,
                ticket_content=ticket_content,
                ticket_metadata=ticket_metadata,
                user_id=user_id
            )
            
            self.db.add(db_classification)
            self.db.commit()
            self.db.refresh(db_classification)
            
            # Log the creation
            audit_log = AuditLog(
                action="create",
                entity_type="classification",
                entity_id=str(db_classification.id),
                details={"classification": classification},
                status="success",
                user_id=user_id,
                classification_id=db_classification.id
            )
            self.db.add(audit_log)
            self.db.commit()
            
            return db_classification
    
    async def push_to_zoho(
        self,
        ticket_id: str,
        classification_id: Optional[int] = None,
        dry_run: bool = False,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Push classification to Zoho.
        
        Args:
            ticket_id: Ticket ID
            classification_id: Classification ID (optional)
            dry_run: If True, only preview changes without applying
            user_id: User ID who initiated the push
            
        Returns:
            Dictionary with push results
        """
        if not self.zoho_service:
            return {
                "ticket_id": ticket_id,
                "status": "error",
                "errors": ["Zoho service not available"],
                "dry_run": dry_run
            }
        
        # Get classification
        if classification_id:
            db_classification = self.db.query(Classification).filter(
                Classification.id == classification_id
            ).first()
        else:
            db_classification = self.db.query(Classification).filter(
                Classification.ticket_id == ticket_id
            ).order_by(Classification.created_at.