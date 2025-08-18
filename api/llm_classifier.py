import os
import json
import openai
from openai import OpenAI
import pandas as pd
import re
from dealer_utils import lookup_dealer_by_name, extract_dealers_from_subject, extract_syndicators

from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY", "")
client = OpenAI()

VALID_CATEGORIES = [
    "Product Activation - New Client",
    "Product Activation - Existing Client",
    "Product Cancellation",
    "Problem / Bug",
    "General Question",
    "Analysis / Review",
    "Other"
]
VALID_SUBCATEGORIES = [
    "Import",
    "Export",
    "Sales Data Import",
    "FB Setup",
    "Google Setup",
    "Other Department",
    "Other",
    "AccuTrade"
]
VALID_INVENTORY_TYPES = [
    "New", "Used", "Demo", "New + Used"
]

def load_syndicators():
    """Load valid syndicators from CSV file"""
    for fn in ["../data/syndicators.csv", "syndicators.csv", "data/syndicators.csv"]:
        if os.path.exists(fn):
            try:
                df = pd.read_csv(fn)
                return [s for s in df["Syndicator"].dropna().unique()]
            except Exception as e:
                print(f"Error loading syndicators from {fn}: {e}")
    return ["Kijiji", "AutoTrader", "Cars.com", "Trader"]

VALID_SYNDICATORS = load_syndicators()

SYSTEM_PROMPT = """
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
- Category: Product Activation - New Client, Product Activation - Existing Client, Product Cancellation, Problem / Bug, General Question, Analysis / Review, Other
- Sub Category: Import, Export, Sales Data Import, FB Setup, Google Setup, Other Department, Other, AccuTrade
- Inventory Type: New, Used, Demo, New + Used
- Syndicator: Only allowed values from syndicators.csv

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
{"contact": "Véronique Fournier", "dealer_name": "Mazda Steele", "dealer_id": "2618", "rep": "Véronique Fournier", "category": "Problem / Bug", "sub_category": "Import", "syndicator": "", "inventory_type": ""}

Example 2:  
Message:  
"Please cancel the Kijiji export for Number 7 Honda Sales Limited."  
JSON:  
{"contact": "Lisa Payne", "dealer_name": "Number 7 Honda Sales Limited", "dealer_id": "2221", "rep": "Lisa Payne", "category": "Product Cancellation", "sub_category": "Export", "syndicator": "Kijiji", "inventory_type": ""}

Example 3:  
Message:  
"Bonjour, Je ne sais pas si ça s'adresse à @Syndication D2C Media ou @Web Support D2C Media Pouvez-vous désactiver les rabais PRIX EMPLOYÉS FORD pour les 2 concessionnaire suivants : Donnacona Ford et La Pérade Ford."  
JSON:  
{"contact": "Alexandra Biron", "dealer_name": "Multiple: Donnacona Ford, La Pérade Ford", "dealer_id": "", "rep": "Alexandra Biron", "category": "Product Cancellation", "sub_category": "Export", "syndicator": "", "inventory_type": ""}

Example 4:  
Message:  
"Hi, can you confirm if the AccuTrade integration is live for Volvo Laval?"  
JSON:  
{"contact": "Clio Perkins", "dealer_name": "Volvo Laval", "dealer_id": "2092", "rep": "Clio Perkins", "category": "General Question", "sub_category": "AccuTrade", "syndicator": "AccuTrade", "inventory_type": ""}

Example 5:  
Message:  
"New car pricing is not updating from Quorum for Kelowna Hyundai. Client says inventory feed shows correct MSRP, but website is off by $500."  
JSON:  
{"contact": "Cathleen Sun", "dealer_name": "Kelowna Hyundai", "dealer_id": "4042", "rep": "Cathleen Sun", "category": "Problem / Bug", "sub_category": "Import", "syndicator": "", "inventory_type": "New"}

---

ALWAYS output a single JSON object with all 8 fields present (never null, never missing a key), following the above strict format.

---

Classify the following message and output only the JSON object:
"""

def get_full_ticket_text(ticket, threads):
    """Combine subject + all thread bodies for LLM context"""
    subject = ticket.get("subject", "")
    conversation = []
    for t in threads:
        who = (t.get("author", {}) or {}).get("name") or t.get("fromEmailAddress") or t.get("from") or ""
        msg = t.get("summary") or t.get("content") or ""
        if msg:
            conversation.append(f"From: {who}\n\n{msg.strip()}")
    full_text = f"Subject: {subject}\n\n" + "\n\n---\n\n".join(conversation)
    return full_text.strip()

def extract_dealers_from_subject(subject):
    """Look for likely dealer names in subject: [Brand] [City]"""
    brands = [
        "Mazda", "Toyota", "Honda", "Chevrolet", "Hyundai", "Genesis", "Ford", "Ram", "GMC",
        "Acura", "Jeep", "Buick", "Nissan", "Volvo", "Subaru", "Volkswagen", "Kia", "Mitsubishi",
        "Infiniti", "Lexus", "Cadillac", "Dodge", "Mini", "Jaguar", "Land Rover", "BMW", "Mercedes",
        "Audi", "Porsche", "Tesla"
    ]
    # Match 'Brand City', 'City Brand', and 'Brand - City'
    candidates = []
    for brand in brands:
        matches = re.findall(rf"\b{brand}\s+[A-Za-z0-9\-éèêàâîôûçëïü']+", subject, re.IGNORECASE)
        matches += re.findall(rf"\b[A-Za-z0-9\-éèêàâîôûçëïü']+\s+{brand}\b", subject, re.IGNORECASE)
        matches += re.findall(rf"\b{brand}\s*-\s*[A-Za-z0-9\-éèêàâîôûçëïü']+", subject, re.IGNORECASE)
        candidates.extend(matches)
    return list(dict.fromkeys([c.strip().replace(" - ", " ") for c in candidates]))

def parse_gpt_json(response_text):
    """Parse JSON from GPT response"""
    try:
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        return json.loads(response_text[start:end])
    except Exception:
        return {}

def classify_ticket_gpt(ticket_text, debug=False):
    """Call OpenAI GPT-4 to classify ticket"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": ticket_text.strip()},
    ]
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0,
            max_tokens=700,
        )
        response_text = completion.choices[0].message.content
        if debug:
            print(f"RAW OPENAI RESPONSE: {response_text}")
        
        parsed = parse_gpt_json(response_text)
        if debug:
            print(f"PARSED JSON: {parsed}")
        return parsed
    except Exception as e:
        if debug:
            print(f"OpenAI API error: {e}")
        return {}

def validate_fields(fields, ticket_text="", ticket=None, threads=None, debug=False):
    """Validate and enhance classification fields with comprehensive fallbacks"""
    res = {}

    # 1. Strict dropdown mapping for Category/Sub Category/Inventory Type
    res["category"] = fields.get("category", "")
    if res["category"] not in VALID_CATEGORIES:
        res["category"] = ""
    
    res["sub_category"] = fields.get("sub_category", "")
    if res["sub_category"] not in VALID_SUBCATEGORIES:
        res["sub_category"] = ""
    
    res["inventory_type"] = fields.get("inventory_type", "")
    if res["inventory_type"] not in VALID_INVENTORY_TYPES:
        res["inventory_type"] = ""

    # 2. Syndicator strict mapping
    res["syndicator"] = fields.get("syndicator", "")
    if VALID_SYNDICATORS:
        for s in VALID_SYNDICATORS:
            if res["syndicator"].strip().lower() == s.strip().lower():
                res["syndicator"] = s
                break
        else:
            res["syndicator"] = ""

    # 3. Dealer Name/ID/Rep via mapping (with fallback)
    dealer_name = fields.get("dealer_name", "").strip()
    dealer_id = fields.get("dealer_id", "").strip()
    rep = fields.get("rep", "").strip()
    
    # Try dealer lookup
    dealer_lookup = {}
    try:
        if dealer_name:
            dealer_lookup = lookup_dealer_by_name(dealer_name)
    except Exception as e:
        if debug:
            print(f"Dealer lookup failed: {e}")
        dealer_lookup = {}

    # 4. Multi-dealer or ambiguous case handling
    subject = ticket.get("subject", "") if ticket else ""
    subject_dealers = []
    
    try:
        if subject:
            subject_dealers = extract_dealers(subject)
    except Exception:
        pass
    
    # Fallback: use extract_dealers_from_subject
    if not subject_dealers and subject:
        subject_dealers = extract_dealers_from_subject(subject)
    
    is_multi = (
        "multiple:" in dealer_name.lower() or
        (dealer_name and any(x in dealer_name.lower() for x in ["concessionnaire suivants", "les 2 concessionnaire", "for both dealers", "pour les deux"]))
    )

    # Defensive dealer resolution
    if (not dealer_name or dealer_name.lower() in ["unknown dealer", ""]) and subject_dealers:
        if len(subject_dealers) == 1:
            # Single dealer: map fully
            dealer_lookup2 = lookup_dealer_by_name(subject_dealers[0])
            res["dealer_name"] = dealer_lookup2.get("dealer_name", subject_dealers[0])
            res["dealer_id"] = dealer_lookup2.get("dealer_id", "")
            res["rep"] = dealer_lookup2.get("rep", rep) or ""
        elif len(subject_dealers) > 1:
            # Multi-dealer
            formatted = "Multiple: " + ", ".join(subject_dealers)
            res["dealer_name"] = formatted
            res["dealer_id"] = ""
            res["rep"] = rep if rep else ""
    elif is_multi or (not dealer_name and len(subject_dealers) > 1):
        try:
            multi = subject_dealers if subject_dealers else extract_dealers(ticket_text)
        except:
            multi = []
        formatted = "Multiple: " + ", ".join(multi) if multi else "Multiple: (Dealers not found)"
        res["dealer_name"] = formatted
        res["dealer_id"] = ""
        res["rep"] = rep if rep else ""
    elif dealer_lookup and dealer_lookup.get("dealer_id"):
        res["dealer_name"] = dealer_lookup.get("dealer_name", dealer_name.title())
        res["dealer_id"] = dealer_lookup.get("dealer_id", "")
        res["rep"] = dealer_lookup.get("rep", rep) or ""
    else:
        # Try direct extraction as final fallback
        detected_dealers = []
        try:
            detected_dealers = extract_dealers(ticket_text)
        except:
            pass
            
        if detected_dealers:
            res["dealer_name"] = detected_dealers[0]
            dealer_lookup2 = lookup_dealer_by_name(detected_dealers[0])
            res["dealer_id"] = dealer_lookup2.get("dealer_id", "")
            res["rep"] = dealer_lookup2.get("rep", rep) or ""
        elif subject_dealers:
            res["dealer_name"] = subject_dealers[0]
            dealer_lookup2 = lookup_dealer_by_name(subject_dealers[0])
            res["dealer_id"] = dealer_lookup2.get("dealer_id", "")
            res["rep"] = dealer_lookup2.get("rep", rep) or ""
        else:
            res["dealer_name"] = dealer_name if dealer_name else ""
            res["dealer_id"] = dealer_id
            res["rep"] = rep

    # 5. Category/sub_category: fallback on keywords (French/English)
    ttext = ticket_text.lower()
    subject_lower = subject.lower() if subject else ""
    
    if not res["category"] or not res["sub_category"]:
        if any(w in ttext or w in subject_lower for w in ["désactivation", "disable", "cancel", "terminate", "desactiver", "désactiver"]) and "export" in ttext:
            res["category"] = "Product Cancellation"
            res["sub_category"] = "Export"
        elif ("activate" in ttext or "enable" in ttext) and "export" in ttext:
            res["category"] = "Product Activation - Existing Client"
            res["sub_category"] = "Export"
        elif any(w in ttext for w in ["cancel", "terminate", "désactivation", "desactiver", "désactiver"]) and "import" in ttext:
            res["category"] = "Product Cancellation"
            res["sub_category"] = "Import"
        elif ("activate" in ttext or "enable" in ttext) and "import" in ttext:
            res["category"] = "Product Activation - Existing Client"
            res["sub_category"] = "Import"
        elif any(w in ttext or w in subject_lower for w in ["accutrade"]):
            res["category"] = "General Question"
            res["sub_category"] = "AccuTrade"
        else:
            if not res["category"]:
                res["category"] = "Other"
            if not res["sub_category"]:
                res["sub_category"] = "Other"

    # 6. Final defensive mapping for completely blank results
    all_blank = (
        not res["category"] and
        not res["sub_category"] and
        not res["inventory_type"] and
        not res["syndicator"] and
        not res["dealer_name"] and
        not res["dealer_id"] and
        not res["rep"]
    )
    
    if all_blank:
        try:
            dealers = extract_dealers(ticket_text)
            synds = extract_syndicators(ticket_text)
            
            if dealers:
                dealer_lookup = lookup_dealer_by_name(dealers[0])
                res["dealer_name"] = dealer_lookup.get("dealer_name", dealers[0])
                res["dealer_id"] = dealer_lookup.get("dealer_id", "")
                res["rep"] = dealer_lookup.get("rep", "")
            
            if synds:
                res["syndicator"] = synds[0].title()
                
            if ("cancel" in ttext or "terminate" in ttext) and "export" in ttext:
                res["category"] = "Product Cancellation"
                res["sub_category"] = "Export"
        except Exception as e:
            if debug:
                print(f"Defensive mapping failed: {e}")

    # 7. Contact field: always mapped from rep or original contact
    contact = fields.get("contact", "").strip()
    if res.get("rep"):
        contact = res["rep"]
    res["contact"] = contact if contact else ""

    # 8. Final syndicator extraction if still blank
    if not res["syndicator"]:
        try:
            syndicator_candidates = extract_syndicators(ticket_text)
            if syndicator_candidates:
                res["syndicator"] = syndicator_candidates[0]
        except:
            pass

    if debug:
        print(f"Final mapped fields: {res}")

    return res

class LLMClassifier:
    """Complete LLM-based ticket classifier with comprehensive validation"""
    
    def __init__(self, debug=False):
        self.debug = debug

    def classify(self, ticket_text, ticket=None, threads=None):
        """
        Classify a ticket and return validated fields
        
        Returns:
            tuple: (validated_fields, raw_gpt_fields)
        """
        if self.debug:
            print(f"CLASSIFYING: {ticket_text}")
        
        # Compose full context text if ticket/threads provided
        full_text = ticket_text
        if ticket and threads:
            full_text = get_full_ticket_text(ticket, threads)
        
        # Get GPT classification
        gpt_fields = classify_ticket_gpt(full_text, debug=self.debug)
        
        # Validate and enhance with comprehensive fallbacks
        validated_fields = validate_fields(
            gpt_fields, 
            full_text, 
            ticket=ticket, 
            threads=threads, 
            debug=self.debug
        )
        
        if self.debug:
            print(f"FINAL RESULT: {validated_fields}")
        
        return validated_fields, gpt_fields
