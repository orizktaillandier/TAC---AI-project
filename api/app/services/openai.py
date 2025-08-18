"""
OpenAI service for interacting with the OpenAI API.
"""
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI API."""
    
    def __init__(self):
        """Initialize the OpenAI service."""
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.temperature = settings.OPENAI_TEMPERATURE
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.client = AsyncOpenAI(api_key=self.api_key)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def generate_completion(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a completion from OpenAI.
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            
        Returns:
            Generated text
            
        Raises:
            Exception: If OpenAI API call fails
        """
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def classify_ticket(
        self,
        ticket_text: str,
        system_prompt: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], float]:
        """
        Classify a ticket using OpenAI.
        
        Args:
            ticket_text: Ticket text to classify
            system_prompt: Optional system prompt override
            
        Returns:
            Tuple of (classification_result, confidence_score)
            
        Raises:
            Exception: If OpenAI API call fails or response cannot be parsed
        """
        if not system_prompt:
            system_prompt = self._get_default_system_prompt()
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": ticket_text},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            # Parse the response
            response_text = response.choices[0].message.content
            classification = self._parse_classification_response(response_text)
            
            # Calculate confidence score based on response metadata
            confidence_score = 0.0
            if hasattr(response, "usage") and hasattr(response.usage, "completion_tokens"):
                # More tokens usually means more confident response
                # This is a simple heuristic and can be improved
                completion_tokens = response.usage.completion_tokens
                confidence_score = min(0.99, max(0.5, completion_tokens / 200))
            
            return classification, confidence_score
            
        except Exception as e:
            logger.error(f"Error classifying ticket: {str(e)}")
            raise
    
    def _parse_classification_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the classification response from OpenAI.
        
        Args:
            response_text: Response text from OpenAI
            
        Returns:
            Parsed classification result
            
        Raises:
            ValueError: If response cannot be parsed as JSON
        """
        try:
            # Find JSON object in the response text
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > 0:
                json_str = response_text[start:end]
                return json.loads(json_str)
            
            # If no JSON found, try to parse the whole response
            return json.loads(response_text)
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse OpenAI response as JSON: {response_text}")
            # Return empty dict with required fields
            return {
                "contact": "",
                "dealer_name": "",
                "dealer_id": "",
                "rep": "",
                "category": "",
                "sub_category": "",
                "syndicator": "",
                "inventory_type": "",
            }
    
    def _get_default_system_prompt(self) -> str:
        """
        Get the default system prompt for classification.
        
        Returns:
            Default system prompt
        """
        # Build valid categories/subcategories lists for the prompt
        categories = ", ".join(settings.VALID_CATEGORIES)
        subcategories = ", ".join(settings.VALID_SUBCATEGORIES)
        inventory_types = ", ".join(settings.VALID_INVENTORY_TYPES)
        
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
- Category: {categories}
- Sub Category: {subcategories}
- Inventory Type: {inventory_types}
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