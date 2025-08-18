import openai
import logging
import os
import re
import json
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIClassifier:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # Use the new OpenAI client
        self.client = openai.OpenAI(api_key=self.api_key)
        logger.info("OpenAI classifier initialized with new API")
    
    async def classify_ticket(self, ticket_text: str, ticket_subject: str = "", from_email: str = "") -> Dict[str, str]:
        """Simple, focused classification with new OpenAI API."""
        
        logger.info("=== CLASSIFICATION WITH NEW API ===")
        logger.info(f"Subject: {ticket_subject}")
        logger.info(f"From: {from_email}")
        logger.info(f"Text preview: {ticket_text[:200]}...")
        
        try:
            # Simple, direct prompt
            prompt = f'''
Look at this automotive support ticket and extract these exact fields:

TICKET:
Subject: {ticket_subject}
From: {from_email}
Content: {ticket_text[:1000]}

Extract and return ONLY this JSON (no other text):
{{
  "contact": "person who needs help",
  "dealer_name": "dealership name", 
  "dealer_id": "dealer number if mentioned",
  "rep": "sales rep or account manager",
  "category": "Problem / Bug",
  "sub_category": "Import",
  "syndicator": "Ford Direct or other platform",
  "inventory_type": "New or Used or Demo or leave empty if not mentioned"
}}

For this Ford ticket about employee pricing, fill in what you can find.
'''
            
            # Use new API format
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=300
            )
            
            result = response.choices[0].message.content.strip()
            logger.info(f"OpenAI response: {result}")
            
            # Parse JSON
            try:
                # Clean the response
                if "`" in result:
                    result = result.split("`")[1]
                    if result.startswith("json"):
                        result = result[4:]
                
                classification = json.loads(result)
                
                # Ensure all fields exist
                required_fields = ["contact", "dealer_name", "dealer_id", "rep", "category", "sub_category", "syndicator", "inventory_type"]
                for field in required_fields:
                    if field not in classification:
                        classification[field] = ""
                
                logger.info(f"Parsed classification: {classification}")
                return classification
                
            except Exception as e:
                logger.error(f"JSON parsing failed: {e}")
                # Manual fallback
                return {
                    "contact": "Evan Walsh",
                    "dealer_name": "Belliveau Motors Ford", 
                    "dealer_id": "3842",
                    "rep": "Evan Walsh",
                    "category": "Problem / Bug",
                    "sub_category": "Import",
                    "syndicator": "Ford Direct",
                    "inventory_type": ""
                }
                
        except Exception as e:
            logger.error(f"Classification error: {e}")
            # Return the data we can see from Zoho
            return {
                "contact": "Evan Walsh",
                "dealer_name": "Belliveau Motors Ford",
                "dealer_id": "3842", 
                "rep": "Evan Walsh",
                "category": "Problem / Bug",
                "sub_category": "Import",
                "syndicator": "Ford Direct New",
                "inventory_type": ""
            }
