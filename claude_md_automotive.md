# Automotive Ticket Classifier - Claude Code Context

## Project Overview
AI-powered ticket classification system for automotive dealership syndication support. Processes French/English support tickets from Zoho Desk using OpenAI GPT-4 to automatically categorize and route them.

## Critical Architecture Rules

### 1. STRICT FIELD STRUCTURE (NEVER MODIFY)
Every classification MUST return exactly these 8 fields:
```python
["contact", "dealer_name", "dealer_id", "rep", "category", "sub_category", "syndicator", "inventory_type"]
```

### 2. Valid Dropdown Values (from validation lists)
- **Category**: "Product Activation - New Client", "Product Activation - Existing Client", "Product Cancellation", "Problem / Bug", "General Question", "Analysis / Review", "Other"
- **Sub Category**: "Import", "Export", "Sales Data Import", "FB Setup", "Google Setup", "Other Department", "Other", "AccuTrade"
- **Inventory Type**: "New", "Used", "Demo", "New + Used"
- **Syndicator**: Values from data/syndicators.csv (Kijiji, AutoTrader, Cars.com, Trader, etc.)

### 3. Data Flow Pipeline
```
1. Zoho Ticket Fetch (enhanced_zoho_integration.py)
   ↓
2. Smart Dealer Extraction (complete_dealer_api.py)
   ↓  
3. LLM Classification (llm_classifier.py)
   ↓
4. Validation & Mapping (dealer_utils.py)
   ↓
5. Push Back to Zoho (auto_push=True)
   ↓
6. Streamlit UI Display (main.py + api_client_updated.py)
```

## Key Files & Responsibilities

### Backend (FastAPI)
- **complete_dealer_api.py**: Main API server with smart dealer extraction
- **llm_classifier.py**: OpenAI GPT-4 integration with system prompts
- **enhanced_zoho_integration.py**: Zoho Desk API client (fetch/push tickets)
- **dealer_utils.py**: CSV-based dealer/rep mapping utilities

### Frontend (Streamlit)  
- **main.py**: Main UI with navigation and status indicators
- **api_client_updated.py**: API client for UI communication
- **pages/**: Individual UI components (classifier, management, analytics)

### Data
- **data/rep_dealer_mapping.csv**: Dealer ID/Name/Rep mappings (2732 rows)
- **data/syndicators.csv**: Valid syndicator dropdown values

## Critical Business Rules

### Dealer Extraction Priority (HIGHEST TO LOWEST)
1. **Subject Line Patterns**: `/\s*([Brand Name])\s*$` (e.g., "Cancel Export / Joliette Dodge")
2. **Rep Name Matching**: Find people names in text, lookup in CSV
3. **Brand Pattern Matching**: "[Word] [Brand]" (e.g., "Fines Ford")
4. **Special Test Cases**: "Number 7 Honda" = dealer_id "2221"

### Import vs Export Detection
- **Import**: DMS issues, "ne fonctionne pas", "not updating", delivery problems
- **Export**: Feed destinations, syndication partners, cancellations

### French/English Support
- Bilingual prompts and validation
- French keywords: "désactivation", "véhicule", "livraison"
- English keywords: "cancel", "activate", "export"

## Common Debugging Patterns

### Zoho API Issues
```python
# Always log these for API debugging
if debug:
    print(f"API URL: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
```

### Classification Validation
```python
# Ensure all 8 fields present
required_fields = ["contact", "dealer_name", "dealer_id", "rep", 
                  "category", "sub_category", "syndicator", "inventory_type"]
for field in required_fields:
    if field not in result:
        result[field] = ""
```

## Environment Setup
- **API Server**: `python complete_dealer_api.py` (Port 8090)
- **UI Server**: `streamlit run main.py` (Port 8501)
- **Required ENV**: `OPENAI_API_KEY`, `ZOHO_CLIENT_ID`, `ZOHO_CLIENT_SECRET`, `ZOHO_REFRESH_TOKEN`, `ZOHO_ORG_ID`

## Testing Endpoints
- **Health**: `GET localhost:8090/health`
- **Test Classification**: `POST localhost:8090/api/v1/test-classify`
- **Zoho Ticket**: `POST localhost:8090/api/v1/classify`
- **Debug Ticket**: `GET localhost:8090/debug/ticket/{ticket_id}`

## Known Issues & Gotchas
1. **Zoho Custom Fields**: Use `cf_` prefix, not `customFields`
2. **Dealer ID Validation**: Only accept IDs from CSV or D2C sources
3. **Multi-Dealer Format**: "Multiple: [Name1], [Name2]" with blank dealer_id
4. **Subject Priority**: Subject line extraction takes precedence over text body
5. **Push Result Structure**: Detailed field tracking in `push_result` object

## Performance Notes
- **CSV Loading**: Dealer mapping loaded once at startup (2732 rows)
- **LLM Calls**: Single GPT-4 call per classification (~2-3 seconds)
- **Zoho Rate Limits**: Built-in retry with exponential backoff
- **Token Usage**: ~500-1000 tokens per classification

When modifying this system:
- ALWAYS preserve the 8-field structure
- Test with both French and English tickets  
- Verify dropdown values against validation lists
- Check dealer extraction prioritization logic
- Maintain Zoho API field format consistency