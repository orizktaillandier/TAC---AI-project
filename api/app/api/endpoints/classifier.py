"""
Updated classifier endpoints with Zoho integration.
"""
import sys
import os
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
import asyncio
import httpx
import os
from datetime import datetime

from app.api.deps import get_db, get_classifier_service, get_zoho_service
from app.services.classifier import ClassifierService
from app.services.zoho import ZohoService
from app.core.logging import get_logger

logger = get_logger()

router = APIRouter()

# Import our new Zoho integration
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from zoho_integration import ZohoTicketFetcher

class IntegratedClassifierService:
    """Enhanced classifier with Zoho integration."""
    
    def __init__(self, classifier_service: ClassifierService):
        self.classifier_service = classifier_service
        self.zoho_fetcher = ZohoTicketFetcher()
    
    async def classify_ticket_from_zoho(self, ticket_id: str, auto_push: bool = False) -> Dict[str, Any]:
        """
        Fetch ticket from Zoho and classify it.
        
        Args:
            ticket_id: Zoho ticket ID
            auto_push: Whether to automatically push results back to Zoho
            
        Returns:
            Classification result with Zoho data
        """
        logger.info(f"Starting classification for Zoho ticket {ticket_id}")
        
        try:
            # Step 1: Fetch ticket and threads from Zoho
            ticket_data, threads, fetch_error = await self.zoho_fetcher.get_ticket_with_threads(ticket_id)
            
            if fetch_error:
                logger.error(f"Failed to fetch ticket {ticket_id}: {fetch_error}")
                raise HTTPException(status_code=404, detail=f"Could not fetch ticket: {fetch_error}")
            
            if not ticket_data:
                logger.error(f"No ticket data for {ticket_id}")
                raise HTTPException(status_code=404, detail="Ticket not found")
            
            # Step 2: Prepare text for classification
            classification_text = self._prepare_classification_text(ticket_data, threads)
            
            logger.info(f"Prepared {len(classification_text)} characters for classification")
            
            # Step 3: Classify using existing classifier service
            fields, raw_classification = await self.classifier_service.classify_ticket(
                ticket_id=ticket_id,
                ticket_text=classification_text,
                ticket_subject=ticket_data.get("subject"),
                threads=threads,
                use_cache=True
            )
            
            # Step 4: Store classification in database
            db_classification = await self.classifier_service.store_classification(
                ticket_id=ticket_id,
                classification=fields,
                raw_classification=raw_classification,
                ticket_subject=ticket_data.get("subject"),
                ticket_content=classification_text,
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
            
            # Step 5: Auto-push to Zoho if requested
            push_result = None
            if auto_push:
                logger.info(f"Auto-pushing classification for ticket {ticket_id}")
                
                push_success, push_error = await self._push_classification_to_zoho(
                    ticket_id, fields
                )
                
                if push_success:
                    logger.info(f"Successfully pushed classification to Zoho for ticket {ticket_id}")
                    push_result = {"status": "success", "pushed": True}
                else:
                    logger.error(f"Failed to push to Zoho: {push_error}")
                    push_result = {"status": "error", "error": push_error, "pushed": False}
            
            # Step 6: Build response
            result = {
                "ticket_id": ticket_id,
                "classification": fields,
                "raw_classification": raw_classification,
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
                "pushed": push_result.get("pushed", False) if push_result else False,
                "push_result": push_result
            }
            
            logger.info(f"Classification completed for ticket {ticket_id}")
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error classifying ticket {ticket_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")
    
    def _prepare_classification_text(self, ticket_data: Dict, threads: List[Dict]) -> str:
        """
        Prepare text for classification from Zoho ticket data.
        
        Args:
            ticket_data: Ticket data from Zoho
            threads: Thread data from Zoho
            
        Returns:
            Formatted text for classification
        """
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
        
        # Add relevant custom field values if they exist
        custom_fields = ticket_data.get("custom_fields", {})
        if custom_fields:
            relevant_fields = []
            for key, value in custom_fields.items():
                if value and any(keyword in key.lower() for keyword in [
                    'syndic', 'inventory', 'product', 'oem', 'dealer', 'brand'
                ]):
                    relevant_fields.append(f"{key}: {value}")
            
            if relevant_fields:
                parts.append("--- Existing Data ---")
                parts.extend(relevant_fields)
        
        return "\n\n".join(parts)
    
    async def _push_classification_to_zoho(self, ticket_id: str, classification: Dict[str, str]) -> tuple[bool, Optional[str]]:
        """
        Push classification results back to Zoho custom fields.
        
        Args:
            ticket_id: Zoho ticket ID
            classification: Classification result
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Prepare updates for custom fields
            updates = {}
            
            # Map our classification fields to Zoho custom fields
            if classification.get("syndicator"):
                updates["cf_syndicators"] = classification["syndicator"]
            
            if classification.get("inventory_type"):
                updates["cf_inventory_type"] = classification["inventory_type"]
            
            if classification.get("category"):
                updates["category"] = classification["category"]
            
            if classification.get("sub_category"):
                updates["subCategory"] = classification["sub_category"]
            
            # Add classification metadata
            classification_summary = f"Auto-classified: {classification.get('category', 'Unknown')}"
            if classification.get("dealer_name"):
                classification_summary += f" | Dealer: {classification['dealer_name']}"
            if classification.get("syndicator"):
                classification_summary += f" | Syndicator: {classification['syndicator']}"
            
            # You might want to add this to a notes field
            # updates["cf_notes"] = classification_summary
            
            if not updates:
                return True, "No fields to update"
            
            # Push to Zoho
            success, error = await self.zoho_fetcher.update_ticket_fields(ticket_id, updates)
            
            if success:
                logger.info(f"Updated Zoho ticket {ticket_id} with fields: {list(updates.keys())}")
                return True, None
            else:
                logger.error(f"Failed to update Zoho ticket {ticket_id}: {error}")
                return False, error
            
        except Exception as e:
            error_msg = f"Error pushing to Zoho: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

# Updated endpoints
@router.post("/classify")
async def classify_ticket(
    request: Dict[str, Any],
    classifier_service: ClassifierService = Depends(get_classifier_service)
):
    """
    Classify a ticket - supports both Zoho ID and direct text input.
    
    Request body can contain:
    - ticket_id: Zoho ticket ID (will fetch from Zoho)
    - ticket_text: Direct text input
    - ticket_subject: Subject line
    - auto_push: Whether to push results back to Zoho
    """
    ticket_id = request.get("ticket_id")
    ticket_text = request.get("ticket_text")
    ticket_subject = request.get("ticket_subject")
    auto_push = request.get("auto_push", False)
    
    # If ticket_id is provided, fetch from Zoho
    if ticket_id:
        try:
            result = await classifier_service.classify_ticket_from_zoho(ticket_id, auto_push)
            return result
        except Exception as e:
            logger.error(f"Zoho classification failed: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    
    # Otherwise, use direct text classification (existing functionality)
    elif ticket_text:
        fields, raw_classification = await classifier_service.classify_ticket(
            ticket_id=None,
            ticket_text=ticket_text,
            ticket_subject=ticket_subject,
            use_cache=False
        )
        
        return {
            "classification": fields,
            "raw_classification": raw_classification,
            "source": "direct_text"
        }
    
    else:
        raise HTTPException(status_code=400, detail="Either ticket_id or ticket_text must be provided")

@router.get("/zoho/test")
async def test_zoho_connection():
    """Test Zoho connectivity."""
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        from zoho_integration import ZohoTicketFetcher
        
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
        
@router.post("/classify-batch")
async def classify_batch_tickets(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    classifier_service: ClassifierService = Depends(get_classifier_service)
):
    """
    Classify multiple tickets by Zoho IDs.
    
    Request body:
    - ticket_ids: List of Zoho ticket IDs
    - auto_push: Whether to push results back to Zoho
    """
    ticket_ids = request.get("ticket_ids", [])
    auto_push = request.get("auto_push", False)
    
    if not ticket_ids:
        raise HTTPException(status_code=400, detail="ticket_ids list is required")
    
    if len(ticket_ids) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 tickets per batch")
    
    # Create integrated service
    integrated_service = IntegratedClassifierService(classifier_service)
    
    # Process tickets
    results = []
    successful = 0
    failed = 0
    
    for ticket_id in ticket_ids:
        try:
            result = await integrated_service.classify_ticket_from_zoho(ticket_id, auto_push)
            results.append({
                "ticket_id": ticket_id,
                "status": "success",
                "classification": result["classification"],
                "pushed": result.get("pushed", False)
            })
            successful += 1
            
        except Exception as e:
            results.append({
                "ticket_id": ticket_id,
                "status": "error",
                "error": str(e),
                "pushed": False
            })
            failed += 1
    
    return {
        "ok": successful,
        "err": failed,
        "results": results,
        "total_processed": len(ticket_ids)
    }


@router.post("/push-classification")
async def push_classification_to_zoho(
    request: Dict[str, Any],
    classifier_service: ClassifierService = Depends(get_classifier_service)
):
    """
    Push an existing classification back to Zoho.
    
    Request body:
    - ticket_id: Zoho ticket ID
    - classification_id: Optional classification ID from database
    - dry_run: Preview changes without applying them
    """
    ticket_id = request.get("ticket_id")
    classification_id = request.get("classification_id")
    dry_run = request.get("dry_run", False)
    
    if not ticket_id:
        raise HTTPException(status_code=400, detail="ticket_id is required")
    
    # Use existing push functionality from classifier service
    return await classifier_service.push_to_zoho(
        ticket_id=ticket_id,
        classification_id=classification_id,
        dry_run=dry_run
    )


@router.get("/tickets/{ticket_id}")
async def get_ticket_info(ticket_id: str):
    """Get ticket information from Zoho."""
    zoho_fetcher = ZohoTicketFetcher()
    
    ticket_data, threads, error = await zoho_fetcher.get_ticket_with_threads(ticket_id)
    
    if error:
        raise HTTPException(status_code=404, detail=error)
    
    return {
        "ticket": ticket_data,
        "threads": threads,
        "threads_count": len(threads)
    }


@router.get("/tickets")
async def search_tickets(
    status: Optional[str] = None,
    department_id: Optional[str] = None,
    limit: int = 20
):
    """Search tickets in Zoho."""
    zoho_fetcher = ZohoTicketFetcher()
    
    tickets, error = await zoho_fetcher.search_tickets(
        status=status,
        department_id=department_id,
        limit=limit
    )
    
    if error:
        raise HTTPException(status_code=500, detail=error)
    
    return {
        "tickets": tickets,
        "count": len(tickets)
    }