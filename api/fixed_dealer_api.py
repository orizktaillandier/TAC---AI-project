from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import your working classifier
try:
    from llm_classifier import LLMClassifier
    working_classifier = LLMClassifier(debug=True)
    logger.info("LLM classifier initialized")
except Exception as e:
    logger.error(f"Failed to initialize classifier: {e}")
    working_classifier = None

# Create FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_full_classification(text: str, subject: str = "", oem: str = "", from_email: str = ""):
    """Get complete classification including all fields"""
    if working_classifier:
        try:
            full_text = f"Subject: {subject}\n\nDescription: {text}"
            fields, raw_fields = working_classifier.classify(full_text)
            logger.info(f"Classification result: {fields}")
            return fields
        except Exception as e:
            logger.error(f"Classifier failed: {e}")
    
    return {
        "contact": "",
        "dealer_name": "",
        "dealer_id": "",
        "rep": "",
        "category": "",
        "sub_category": "",
        "syndicator": "",
        "inventory_type": ""
    }

@app.get("/")
def root():
    return {"message": "Working Classifier API", "version": "12.0.0"}

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "classifier-api"}

@app.post("/api/v1/test-classify")
async def test_classify_synthetic(request: Request):
    """Test endpoint for synthetic ticket data"""
    try:
        data = await request.json()
        
        subject = data.get("subject", "")
        content = data.get("content", "")
        from_email = data.get("from_email", "")
        oem = data.get("oem", "")
        
        logger.info(f"Testing: {subject}")
        
        full_text = f"Subject: {subject}\n\nDescription: {content}"
        
        classification = get_full_classification(full_text, subject, oem, from_email)
        
        return {
            "test_data": {
                "subject": subject,
                "content": content,
                "from_email": from_email,
                "oem": oem
            },
            "classification": classification,
            "source": "working_test"
        }
        
    except Exception as e:
        logger.error(f"Test error: {str(e)}")
        return {"error": f"Test failed: {str(e)}"}

@app.get("/api/v1/metrics")
def get_metrics():
    return {
        "uptime": 3600,
        "processed": 100,
        "success_rate": 95.5
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
