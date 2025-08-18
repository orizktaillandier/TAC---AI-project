from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import json
import logging
import pandas as pd
import re
from typing import Dict, Any, Tuple, Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fixed_openai_service import OpenAIClassifier

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    openai_classifier = OpenAIClassifier(api_key=openai_api_key)
else:
    openai_classifier = None

# Fix path - go up one level from api folder to find data folder
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
data_dir = os.path.join(project_root, 'data')

logger.info(f"Current directory: {current_dir}")
logger.info(f"Project root: {project_root}")
logger.info(f"Data directory: {data_dir}")

# Load dealer mapping once at startup
dealer_mapping_df = None
try:
    dealer_mapping_path = os.path.join(data_dir, 'rep_dealer_mapping.csv')
    logger.info(f"Looking for dealer mapping at: {dealer_mapping_path}")
    
    if os.path.exists(dealer_mapping_path):
        dealer_mapping_df = pd.read_csv(dealer_mapping_path)
        dealer_mapping_df.columns = dealer_mapping_df.columns.str.strip()
        logger.info(f"Loaded dealer mapping with {len(dealer_mapping_df)} rows")
        logger.info(f"Columns: {list(dealer_mapping_df.columns)}")
    else:
        logger.error(f"Dealer mapping file not found: {dealer_mapping_path}")
except Exception as e:
    logger.error(f"Error loading dealer mapping: {e}")

@app.get("/debug/ticket/{ticket_id}")
async def debug_ticket_text(ticket_id: str):
    """Debug endpoint to see ticket text content"""
    try:
        from enhanced_zoho_integration import ZohoTicketFetcher
        
        fetcher = ZohoTicketFetcher()
        ticket_data, threads, error = await fetcher.get_ticket_with_threads(ticket_id)
        
        if error:
            return {"error": error}
        
        subject = ticket_data.get('subject', '')
        full_text = f"Subject: {subject}\\n\\n"
        
        if ticket_data.get('description'):
            full_text += f"Description: {ticket_data.get('description')}\\n\\n"
        
        if threads:
            full_text += "Conversation:\\n"
            for thread in threads:
                author = thread.get('author_name', 'Unknown')
                content = thread.get('summary', thread.get('content', ''))
                if content:
                    full_text += f"From {author}: {content}\\n\\n"
        
        return {
            "ticket_id": ticket_id,
            "subject": subject,
            "full_text": full_text,
            "text_length": len(full_text),
            "custom_fields": ticket_data.get('custom_fields', {}),
            "threads_count": len(threads)
        }
    except Exception as e:
        return {"error": str(e)}

def normalize_text(text: str) -> str:
    """Normalize text for better matching"""
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation
    text = re.sub(r'[^\\w\\s]', ' ', text)
    
    # Normalize whitespace
    text = re.sub(r'\\s+', ' ', text)
    
    return text.strip()

def get_common_words() -> set:
    """Get set of common words to exclude from matching"""
    return {
        'motors', 'auto', 'group', 'sales', 'limited', 'inc', 'dealer',
        'dealership', 'automotive', 'center', 'car', 'cars', 'company', 
        'corporation', 'corp', 'llc', 'ltd', 'the', 'new', 'used', 'demo',
        'certified', 'pre-owned', 'preowned', 'vehicle', 'vehicles'
    }

def extract_dealer_from_text(text: str, subject: str = "", oem: str = "", from_email: str = "") -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract dealer information using multiple strategies.
    
    Returns:
        Tuple of (dealer_name, dealer_id, rep_name) or (None, None, None)
    """
    if dealer_mapping_df is None:
        logger.warning("No dealer mapping available")
        return None, None, None
    
    # Combine text sources and normalize
    full_text = normalize_text(f"{subject} {text}")
    logger.info(f"Extracting dealer from text (length: {len(full_text)} chars)")
    logger.info(f"Text preview: {full_text[:200]}...")
    logger.info(f"OEM context: {oem}")
    logger.info(f"From email: {from_email}")
    
    # Get common words to exclude
    common_words = get_common_words()
    
    # Extract all potential rep names
    # This regex looks for Name Surname pattern
    name_pattern = r'\\b[A-Z][a-z]+ [A-Z][a-z]+\\b'
    potential_names = re.findall(name_pattern, text)
    logger.info(f"Potential names found in text: {potential_names}")
    
    # Extract all 4-digit numbers (potential dealer IDs)
    id_pattern = r'\\b\\d{4}\\b'
    potential_ids = re.findall(id_pattern, full_text)
    logger.info(f"Potential dealer IDs found in text: {potential_ids}")
    
    # STRATEGY 1: Check if the sender email is associated with a rep
    if from_email:
        # Extract domain and username from email
        email_parts = from_email.split('@')
        if len(email_parts) == 2:
            username = email_parts[0].lower()
            domain = email_parts[1].lower()
            
            # Check for rep name matches based on email
            for _, row in dealer_mapping_df.iterrows():
                rep_name = str(row['Rep Name']).strip()
                if not rep_name:
                    continue
                
                # Normalize rep name for comparison
                rep_normalized = normalize_text(rep_name)
                rep_parts = rep_normalized.split()
                
                # Check if username contains rep name parts
                if len(rep_parts) >= 2:
                    first_name = rep_parts[0]
                    last_name = rep_parts[-1]
                    
                    # Check if email contains parts of the rep name
                    if (first_name in username or last_name in username or 
                        (len(first_name) > 1 and first_name[0] + last_name in username)):
                        logger.info(f"Found rep '{rep_name}' by email match: {from_email}")
                        return row['Dealer Name'], str(row['Dealer ID']), row['Rep Name']
    
    # STRATEGY 2: Direct dealer ID lookup
    for dealer_id in potential_ids:
        matches = dealer_mapping_df[dealer_mapping_df['Dealer ID'].astype(str) == dealer_id]
        if not matches.empty:
            row = matches.iloc[0]
            logger.info(f"Found dealer by ID {dealer_id}: {row['Dealer Name']}")
            return row['Dealer Name'], str(row['Dealer ID']), row['Rep Name']
    
    # STRATEGY 3: Find rep name in text and match dealer
    for name in potential_names:
        # Check if this is a rep name in our mapping
        rep_matches = dealer_mapping_df[dealer_mapping_df['Rep Name'] == name]
        if not rep_matches.empty:
            logger.info(f"Found rep '{name}' in text")
            
            # If only one dealer for this rep, use it
            if len(rep_matches) == 1:
                row = rep_matches.iloc[0]
                logger.info(f"Single dealer for rep {name}: {row['Dealer Name']}")
                return row['Dealer Name'], str(row['Dealer ID']), row['Rep Name']
            
            # Multiple dealers - need to narrow down
            logger.info(f"Rep '{name}' has {len(rep_matches)} dealers")
            
            # If OEM is specified, filter by OEM
            if oem:
                oem_dealers = rep_matches[rep_matches['Dealer Name'].str.lower().str.contains(oem.lower(), na=False)]
                if not oem_dealers.empty:
                    logger.info(f"Found {len(oem_dealers)} {oem} dealers for rep {name}")
                    
                    # Search for dealer name words in text
                    best_match = None
                    max_matches = 0
                    
                    for _, dealer_row in oem_dealers.iterrows():
                        dealer_name = dealer_row['Dealer Name'].lower()
                        
                        # Split dealer name into words
                        dealer_words = set(dealer_name.split())
                        dealer_words = {word for word in dealer_words if len(word) > 3 and word not in common_words}
                        
                        # Count how many dealer words appear in text
                        matches = sum(1 for word in dealer_words if word in full_text)
                        
                        if matches > max_matches:
                            max_matches = matches
                            best_match = dealer_row
                    
                    if best_match is not None and max_matches > 0:
                        logger.info(f"Best dealer match: {best_match['Dealer Name']} ({max_matches} word matches)")
                        return best_match['Dealer Name'], str(best_match['Dealer ID']), best_match['Rep Name']
                    
                    # If no specific match, just use first OEM dealer for this rep
                    first_match = oem_dealers.iloc[0]
                    logger.info(f"Using first OEM dealer for rep: {first_match['Dealer Name']}")
                    return first_match['Dealer Name'], str(first_match['Dealer ID']), first_match['Rep Name']
            
            # Try matching by dealer words in the text
            for _, dealer_row in rep_matches.iterrows():
                dealer_name = dealer_row['Dealer Name'].lower()
                dealer_words = set(dealer_name.split())
                dealer_words = {word for word in dealer_words if len(word) > 3 and word not in common_words}
                
                # Check if any significant dealer words appear in text
                matches = [word for word in dealer_words if word in full_text]
                if matches:
                    logger.info(f"Dealer match by words {matches}: {dealer_row['Dealer Name']}")
                    return dealer_row['Dealer Name'], str(dealer_row['Dealer ID']), dealer_row['Rep Name']
            
            # If we found a rep but couldn't determine dealer, just return the rep
            logger.info(f"Found rep {name} but couldn't determine dealer")
            return None, None, name
    
    # STRATEGY 4: Direct dealer name matching in text
    # Score all dealers by word matches in text
    best_score = 0
    best_match = None
    
    # If OEM specified, only check those dealers
    if oem:
        dealer_subset = dealer_mapping_df[dealer_mapping_df['Dealer Name'].str.lower().str.contains(oem.lower(), na=False)]
    else:
        dealer_subset = dealer_mapping_df
    
    for _, row in dealer_subset.iterrows():
        dealer_name = normalize_text(row['Dealer Name'])
        if not dealer_name:
            continue
        
        # Split into words, remove common words
        dealer_words = set(dealer_name.split())
        dealer_words = {word for word in dealer_words if len(word) > 3 and word not in common_words}
        
        # Count matches
        score = sum(1 for word in dealer_words if word in full_text)
        
        # Bonus points for multiple matching words
        if score > 1:
            score *= 1.5
        
        if score > best_score:
            best_score = score
            best_match = row
    
    # If good match found
    if best_match is not None and best_score >= 2:
        logger.info(f"Direct dealer match: {best_match['Dealer Name']} (score: {best_score})")
        return best_match['Dealer Name'], str(best_match['Dealer ID']), best_match['Rep Name']
    
    # If we have potential rep names but couldn't match them, check if any appear in mapping
    for name in potential_names:
        for _, row in dealer_mapping_df.iterrows():
            if name == row['Rep Name']:
                logger.info(f"Found rep name only: {name}")
                return None, None, name
    
    logger.info("No dealer or rep found in text")
    return None, None, None

@app.get("/")
def root():
    return {"message": "Versatile Dealer Lookup API", "version": "9.0.0"}

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "versatile-dealer-api"}

@app.post("/api/v1/classify")
async def classify_ticket(request: Request):
    logger.info("=== CLASSIFICATION WITH VERSATILE DEALER LOOKUP ===")
    try:
        data = await request.json()
        ticket_id = data.get("ticket_id")
        auto_push = data.get("auto_push", False)
        
        if ticket_id:
            try:
                from enhanced_zoho_integration import ZohoTicketFetcher
                
                fetcher = ZohoTicketFetcher()
                ticket_data, threads, error = await fetcher.get_ticket_with_threads(ticket_id)
                
                if error:
                    return {"error": f"Failed to fetch ticket: {error}"}
                
                custom_fields = ticket_data.get('custom_fields', {})
                subject = ticket_data.get('subject', '')
                from_email = ticket_data.get('email', '')
                oem = custom_fields.get('cf_oem', '')
                
                logger.info(f"Processing ticket {ticket_id} - Subject: {subject}, OEM: {oem}")
                
                # Build ticket text
                full_text = f"Subject: {subject}\\n\\n"
                
                if ticket_data.get('description'):
                    full_text += f"Description: {ticket_data.get('description')}\\n\\n"
                
                if threads:
                    full_text += "Conversation:\\n"
                    for thread in threads[:3]:
                        author = thread.get('author_name', 'Unknown')
                        content = thread.get('summary', thread.get('content', ''))
                        if content:
                            full_text += f"From {author}: {content}\\n\\n"
                
                # Apply versatile dealer lookup
                dealer_name, dealer_id, rep_name = extract_dealer_from_text(
                    full_text, subject, oem, from_email
                )
                
                # Start classification with discovered dealer info
                classification = {
                    "contact": rep_name or "",
                    "dealer_name": dealer_name or "",
                    "dealer_id": dealer_id or "",
                    "rep": rep_name or "",
                    "category": "", 
                    "sub_category": "", 
                    "syndicator": custom_fields.get('cf_syndicators', ''),
                    "inventory_type": custom_fields.get('cf_inventory_type', '')
                }
                
                logger.info(f"Dealer lookup result: dealer='{dealer_name}', id='{dealer_id}', rep='{rep_name}'")
                
                # Use AI to fill remaining fields only
                if openai_classifier:
                    try:
                        ai_classification = await openai_classifier.classify_ticket(
                            ticket_text=full_text,
                            ticket_subject=subject,
                            from_email=from_email
                        )
                        
                        # Only use AI for specific fields and only if empty
                        ai_fields = ["category", "sub_category", "syndicator", "inventory_type"]
                        for field in ai_fields:
                            if field in ai_classification and ai_classification[field] and not classification[field]:
                                classification[field] = ai_classification[field]
                        
                        # If AI found dealer info that we didn't, use it as fallback
                        if not classification["dealer_name"] and ai_classification.get("dealer_name"):
                            logger.info(f"Using AI-provided dealer name: {ai_classification['dealer_name']}")
                            classification["dealer_name"] = ai_classification["dealer_name"]
                            
                        if not classification["dealer_id"] and ai_classification.get("dealer_id"):
                            logger.info(f"Using AI-provided dealer ID: {ai_classification['dealer_id']}")
                            classification["dealer_id"] = ai_classification["dealer_id"]
                            
                        if not classification["rep"] and ai_classification.get("rep"):
                            logger.info(f"Using AI-provided rep: {ai_classification['rep']}")
                            classification["rep"] = ai_classification["rep"]
                            
                        if not classification["contact"] and ai_classification.get("contact"):
                            logger.info(f"Using AI-provided contact: {ai_classification['contact']}")
                            classification["contact"] = ai_classification["contact"]
                        
                    except Exception as e:
                        logger.error(f"AI classification failed: {e}")
                
                logger.info(f"Final classification: {classification}")
                
                # Auto-push
                pushed = False
                push_result = {}
                
                if auto_push:
                    logger.info("Auto-push enabled")
                    
                    update_payload = {}
                    
                    # Add cf fields
                    cf_updates = {}
                    if classification["syndicator"]:
                        cf_updates["cf_syndicators"] = classification["syndicator"]
                    
                    # Add customFields
                    custom_field_updates = {}
                    if classification["inventory_type"]:
                        custom_field_updates["Inventory Type"] = classification["inventory_type"]
                    if classification["contact"]:
                        custom_field_updates["Sales Representative"] = classification["contact"]
                    
                    # Include updates
                    if cf_updates:
                        update_payload["cf"] = cf_updates
                    if custom_field_updates:
                        update_payload["customFields"] = custom_field_updates
                    
                    # Category/subcategory updates
                    if classification["category"]:
                        update_payload["category"] = classification["category"]
                    if classification["sub_category"]:
                        update_payload["subCategory"] = classification["sub_category"]
                    
                    if update_payload:
                        logger.info(f"Update payload: {update_payload}")
                        
                        try:
                            success, error, result = await fetcher.update_ticket_custom_fields(
                                ticket_id, update_payload, dry_run=False
                            )
                            
                            if success:
                                pushed = True
                                push_result = {"status": "success", "updated_fields": list(update_payload.keys()), "result": result}
                            else:
                                push_result = {"status": "error", "error": error}
                                
                        except Exception as e:
                            logger.error(f"Update error: {str(e)}")
                            push_result = {"status": "error", "error": str(e)}
                    else:
                        logger.info("No fields to update")
                        push_result = {"status": "warning", "message": "No fields to update"}
                
                return {
                    "ticket_id": ticket_id,
                    "classification": classification,
                    "zoho_data": {
                        "subject": subject,
                        "status": ticket_data.get("status"),
                        "ticket_number": ticket_data.get("ticket_number"),
                        "threads_count": len(threads),
                        "from_email": from_email,
                        "web_url": ticket_data.get("web_url"),
                        "existing_syndicator": custom_fields.get('cf_syndicators', ''),
                        "existing_inventory_type": custom_fields.get('cf_inventory_type', '')
                    },
                    "pushed": pushed,
                    "push_result": push_result,
                    "source": "versatile_dealer_api_v9"
                }
                
            except Exception as e:
                logger.error(f"Error: {str(e)}", exc_info=True)
                return {"error": f"Classification failed: {str(e)}"}
        
        else:
            return {"error": "ticket_id is required"}
    
    except Exception as e:
        logger.error(f"Request error: {str(e)}", exc_info=True)
        return {"error": f"Request processing error: {str(e)}"}

@app.get("/api/v1/zoho/test")
async def test_zoho_connection():
    try:
        from enhanced_zoho_integration import ZohoTicketFetcher
        fetcher = ZohoTicketFetcher()
        tickets, error = await fetcher.search_tickets(limit=1)
        
        if error:
            return {"status": "error", "message": error}
        
        return {"status": "success", "message": "Zoho connection working", "tickets_found": len(tickets)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/v1/metrics")
def get_metrics():
    return {
        "uptime": 3600,
        "processed": 100,
        "success_rate": 95.5,
        "avg_processing_time": 2.3,
        "active_workers": 1,
        "queue_size": 0,
        "last_minute": {"classifications": 5},
        "last_hour": {"classifications": 45},
        "last_day": {"classifications": 200}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
