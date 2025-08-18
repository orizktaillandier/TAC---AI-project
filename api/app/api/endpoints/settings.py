"""
Zoho endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.api.deps import get_db, get_zoho_service
from app.services.zoho import ZohoService
from app.core.logging import get_logger

logger = get_logger()

router = APIRouter()


@router.get("/tickets/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    zoho_service: ZohoService = Depends(get_zoho_service),
):
    """
    Get a ticket from Zoho.
    
    Args:
        ticket_id: Ticket ID
        zoho_service: Zoho service
        
    Returns:
        Ticket data
    """
    ticket, error = await zoho_service.get_ticket(ticket_id)
    
    if error:
        logger.error(f"Error getting ticket {ticket_id}: {error}")
        raise HTTPException(status_code=404, detail=error)
    
    return ticket


@router.get("/tickets/{ticket_id}/threads")
async def get_ticket_threads(
    ticket_id: str,
    zoho_service: ZohoService = Depends(get_zoho_service),
):
    """
    Get threads for a ticket from Zoho.
    
    Args:
        ticket_id: Ticket ID
        zoho_service: Zoho service
        
    Returns:
        Threads data
    """
    threads, error = await zoho_service.get_ticket_threads(ticket_id)
    
    if error:
        logger.error(f"Error getting threads for ticket {ticket_id}: {error}")
        raise HTTPException(status_code=404, detail=error)
    
    return threads


@router.get("/departments")
async def get_departments(
    zoho_service: ZohoService = Depends(get_zoho_service),
):
    """
    Get departments from Zoho.
    
    Args:
        zoho_service: Zoho service
        
    Returns:
        Departments data
    """
    departments = await zoho_service.get_departments()
    
    return departments


@router.get("/agents")
async def get_agents(
    zoho_service: ZohoService = Depends(get_zoho_service),
):
    """
    Get agents from Zoho.
    
    Args:
        zoho_service: Zoho service
        
    Returns:
        Agents data
    """
    agents = await zoho_service.get_agents()
    
    return agents


@router.get("/views")
async def get_views(
    zoho_service: ZohoService = Depends(get_zoho_service),
):
    """
    Get views from Zoho.
    
    Args:
        zoho_service: Zoho service
        
    Returns:
        Views data
    """
    views = await zoho_service.get_views()
    
    return views


@router.get("/tickets")
async def get_tickets(
    view_id: str = None,
    department_id: str = None,
    status: str = None,
    priority: str = None,
    assignee: str = None,
    search_str: str = None,
    page: int = 1,
    limit: int = 50,
    zoho_service: ZohoService = Depends(get_zoho_service),
):
    """
    Get tickets from Zoho with filters.
    
    Args:
        view_id: View ID
        department_id: Department ID
        status: Status
        priority: Priority
        assignee: Assignee
        search_str: Search string
        page: Page number
        limit: Maximum number of tickets per page
        zoho_service: Zoho service
        
    Returns:
        Tickets data
    """
    filters = {}
    
    if view_id:
        filters["viewId"] = view_id
    
    if department_id:
        filters["departmentId"] = department_id
    
    if status:
        filters["status"] = status
    
    if priority:
        filters["priority"] = priority
    
    if assignee:
        if assignee.lower() == "null":
            filters["unassigned"] = True
        else:
            filters["assignee"] = assignee
    
    if search_str:
        filters["searchStr"] = search_str
    
    if view_id:
        tickets, error = await zoho_service.fetch_tickets_by_view(
            view_id=view_id, page=page, limit=limit
        )
    else:
        tickets, error = await zoho_service.fetch_tickets_with_filters(
            filters=filters, page=page, limit=limit
        )
    
    if error:
        logger.error(f"Error getting tickets: {error}")
        raise HTTPException(status_code=500, detail=error)
    
    return tickets


@router.post("/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    data: Dict[str, Any],
    zoho_service: ZohoService = Depends(get_zoho_service),
):
    """
    Update a ticket in Zoho.
    
    Args:
        ticket_id: Ticket ID
        data: Update data
        zoho_service: Zoho service
        
    Returns:
        Update result
    """
    success, errors = await zoho_service.update_ticket(ticket_id, data)
    
    if not success:
        logger.error(f"Error updating ticket {ticket_id}: {errors}")
        raise HTTPException(status_code=500, detail="\n".join(errors))
    
    return {"success": True, "ticket_id": ticket_id}