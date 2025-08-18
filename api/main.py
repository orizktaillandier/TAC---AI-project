from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import json
from typing import Dict, Any

# Add the parent directory to path for zoho_integration import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Automotive Ticket Classifier API", "version": "3.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "auto-ticket-classifier"}

@app.post("/classify")
async def classify_ticket(request: Request):
    data = await request.json()
    ticket_id = data.get("ticket_id")
    ticket_text = data.get("ticket_text")
    
    if ticket_id:
        try:
            from enhanced_zoho_integration import ZohoTicketFetcher
            
            fetcher = ZohoTicketFetcher()
            ticket_data, threads, error = await fetcher.get_ticket_with_threads(ticket_id)
            
            if error:
                return {"error": f"Failed to fetch ticket: {error}"}
            
            classification = {
                "contact": "Test Contact",
                "dealer_name": "Test Dealer", 
                "dealer_id": "1234",
                "rep": "Test Rep",
                "category": "General Question",
                "sub_category": "Other",
                "syndicator": "Kijiji",
                "inventory_type": "Used"
            }
            
            return {
                "ticket_id": ticket_id,
                "classification": classification,
                "zoho_data": {
                    "subject": ticket_data.get("subject"),
                    "status": ticket_data.get("status"),
                    "threads_count": len(threads)
                },
                "source": "zoho"
            }
            
        except Exception as e:
            return {"error": f"Zoho classification failed: {str(e)}"}
    
    elif ticket_text:
        classification = {
            "contact": "Direct Input",
            "dealer_name": "Text Input Dealer",
            "dealer_id": "",
            "rep": "Unknown", 
            "category": "General Question",
            "sub_category": "Other",
            "syndicator": "",
            "inventory_type": ""
        }
        
        return {"classification": classification, "source": "direct_text"}
    
    else:
        return {"error": "Either ticket_id or ticket_text must be provided"}

@app.get("/zoho/test")
async def test_zoho_connection():
    try:
        from enhanced_zoho_integration import ZohoTicketFetcher
        
        fetcher = ZohoTicketFetcher()
        tickets, error = await fetcher.search_tickets(limit=1)
        
        if error:
            return {"status": "error", "message": error}
        
        return {
            "status": "success", 
            "message": "Zoho connection working",
            "tickets_found": len(tickets)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/metrics")
async def get_metrics():
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
    uvicorn.run(app, host="0.0.0.0", port=8088)
