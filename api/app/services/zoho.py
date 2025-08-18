"""
Zoho Desk API integration service.
"""
import json
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
import httpx
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import ZohoToken

logger = logging.getLogger(__name__)


class ZohoService:
    """Service for interacting with Zoho Desk API."""
    
    def __init__(self, db: Session):
        """
        Initialize the Zoho service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.base_url = settings.ZOHO_BASE_URL.rstrip("/")
        self.client = httpx.AsyncClient(timeout=settings.ZOHO_TIMEOUT)
    
    async def get_access_token(self, force_refresh: bool = False) -> str:
        """
        Get a valid Zoho access token, refreshing if necessary.
        
        Args:
            force_refresh: If True, force refresh the token even if not expired
            
        Returns:
            Access token string
            
        Raises:
            Exception: If token refresh fails
        """
        # Check if we have a valid token in the database
        if not force_refresh:
            token = self.db.query(ZohoToken).order_by(ZohoToken.created_at.desc()).first()
            if token and token.expires_at > datetime.utcnow() + timedelta(minutes=5):
                return token.access_token
        
        # Refresh token
        logger.info("Refreshing Zoho access token")
        token_url = settings.ZOHO_AUTH_URL
        
        params = {
            "refresh_token": settings.ZOHO_REFRESH_TOKEN,
            "client_id": settings.ZOHO_CLIENT_ID,
            "client_secret": settings.ZOHO_CLIENT_SECRET,
            "grant_type": "refresh_token",
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_url,
                    data=params,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=settings.ZOHO_TIMEOUT
                )
                
                if response.status_code != 200:
                    raise Exception(f"Token refresh failed: {response.status_code} {response.text}")
                
                data = response.json()
                access_token = data.get("access_token")
                
                if not access_token:
                    raise Exception("No access token in response")
                
                # Store the new token
                expires_in = int(data.get("expires_in", 3600))
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)  # 1 minute buffer
                
                # Create new token record
                new_token = ZohoToken(
                    access_token=access_token,
                    expires_at=expires_at
                )
                self.db.add(new_token)
                self.db.commit()
                
                # Update base URL if api_domain is provided
                api_domain = data.get("api_domain")
                if api_domain and "desk.zoho." in api_domain:
                    self.base_url = f"{api_domain.rstrip('/')}/api/v1"
                
                return access_token
                
        except Exception as e:
            logger.error(f"Error refreshing Zoho token: {str(e)}")
            raise
    
    def _get_headers(self, access_token: str) -> Dict[str, str]:
        """
        Get headers for Zoho API requests.
        
        Args:
            access_token: Zoho access token
            
        Returns:
            Headers dictionary
        """
        return {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "orgId": settings.ZOHO_ORG_ID,
            "Accept": "application/json",
        }
    
    async def make_request(
        self,
        method: str,
        endpoint: str,
        access_token: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        max_retries: int = 3
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Make a request to the Zoho API.
        
        Args:
            method: HTTP method (GET, POST, PATCH, PUT)
            endpoint: API endpoint (without base URL)
            access_token: Access token (will be fetched if not provided)
            params: Query parameters
            data: Request body data
            headers: Additional headers
            max_retries: Maximum number of retries
            
        Returns:
            Tuple of (response_data, error_message)
        """
        # Get access token if not provided
        if not access_token:
            try:
                access_token = await self.get_access_token()
            except Exception as e:
                return None, f"Failed to get access token: {str(e)}"
        
        # Build request
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        req_headers = self._get_headers(access_token)
        if headers:
            req_headers.update(headers)
        
        if data:
            req_headers["Content-Type"] = "application/json"
        
        # Logging
        if settings.DEBUG:
            logger.debug(f"Zoho API request: {method} {url}")
            logger.debug(f"Headers: {json.dumps({k: '***' if k == 'Authorization' else v for k, v in req_headers.items()})}")
            if params:
                logger.debug(f"Params: {json.dumps(params)}")
            if data:
                logger.debug(f"Data: {json.dumps(data)}")
        
        # Make request with retries
        retries = 0
        backoff = 1.0
        
        while retries < max_retries:
            try:
                method = method.upper()
                
                if method == "GET":
                    response = await self.client.get(url, headers=req_headers, params=params)
                elif method == "POST":
                    response = await self.client.post(url, headers=req_headers, params=params, json=data)
                elif method == "PATCH":
                    response = await self.client.patch(url, headers=req_headers, params=params, json=data)
                elif method == "PUT":
                    response = await self.client.put(url, headers=req_headers, params=params, json=data)
                elif method == "DELETE":
                    response = await self.client.delete(url, headers=req_headers, params=params)
                else:
                    return None, f"Unsupported HTTP method: {method}"
                
                # Handle successful responses
                if response.status_code in (200, 201):
                    try:
                        return response.json(), None
                    except json.JSONDecodeError:
                        return {"status": "success"}, None
                
                if response.status_code == 204:
                    return {}, None
                
                # Handle authentication errors
                if response.status_code == 401 and retries < max_retries - 1:
                    logger.warning("Authentication failed, refreshing token")
                    access_token = await self.get_access_token(force_refresh=True)
                    req_headers = self._get_headers(access_token)
                    if headers:
                        req_headers.update(headers)
                    retries += 1
                    continue
                
                # Handle rate limiting
                if response.status_code == 429:
                    retries += 1
                    wait_time = backoff * (2 ** retries)
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry {retries}/{max_retries}")
                    await asyncio.sleep(wait_time)
                    continue
                
                # Handle server errors
                if 500 <= response.status_code < 600 and retries < max_retries - 1:
                    retries += 1
                    wait_time = backoff * (2 ** retries)
                    logger.warning(f"Server error {response.status_code}, waiting {wait_time}s before retry {retries}/{max_retries}")
                    await asyncio.sleep(wait_time)
                    continue
                
                # Other errors
                error_message = f"API error {response.status_code}"
                try:
                    error_detail = response.text[:500]
                    error_message += f": {error_detail}"
                except Exception:
                    pass
                
                return None, error_message
                
            except httpx.RequestError as e:
                retries += 1
                if retries >= max_retries:
                    return None, f"Request failed after {max_retries} retries: {str(e)}"
                
                wait_time = backoff * (2 ** retries)
                logger.warning(f"Request error, waiting {wait_time}s before retry {retries}/{max_retries}: {str(e)}")
                await asyncio.sleep(wait_time)
    
    async def get_ticket(self, ticket_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Get a ticket by ID.
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Tuple of (ticket_data, error_message)
        """
        access_token = await self.get_access_token()
        return await self.make_request("GET", f"/tickets/{ticket_id}", access_token)
    
    async def get_ticket_threads(self, ticket_id: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Get threads for a ticket.
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Tuple of (threads_list, error_message)
        """
        access_token = await self.get_access_token()
        response, error = await self.make_request("GET", f"/tickets/{ticket_id}/threads", access_token)
        
        if error:
            return [], error
            
        if response and "data" in response and isinstance(response["data"], list):
            return response["data"], None
            
        return [], "No threads found"
    
    async def get_ticket_with_threads(self, ticket_id: str) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Get a ticket and its threads.
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Tuple of (ticket_data, threads_list)
        """
        ticket, _ = await self.get_ticket(ticket_id)
        threads, _ = await self.get_ticket_threads(ticket_id)
        return ticket, threads
    
    async def update_ticket(
        self, 
        ticket_id: str, 
        update_data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Update a ticket.
        
        Args:
            ticket_id: Ticket ID
            update_data: Data to update
            
        Returns:
            Tuple of (success, errors)
        """
        if not update_data:
            return True, []
        
        access_token = await self.get_access_token()
        
        # Split the update into core fields and custom fields
        core_fields = {}
        custom_fields = {}
        cf_fields = {}
        
        for key, value in update_data.items():
            if key == "cf" and isinstance(value, dict):
                cf_fields = value
            elif key == "customFields" and isinstance(value, dict):
                custom_fields = value
            else:
                core_fields[key] = value
        
        errors = []
        success = True
        
        # Update core fields
        if core_fields:
            response, error = await self.make_request(
                "PATCH", 
                f"/tickets/{ticket_id}", 
                access_token, 
                data=core_fields
            )
            
            if error:
                errors.append(f"Failed to update core fields: {error}")
                success = False
        
        # Update custom fields
        if custom_fields:
            response, error = await self.make_request(
                "PATCH", 
                f"/tickets/{ticket_id}", 
                access_token, 
                data={"customFields": custom_fields}
            )
            
            if error:
                errors.append(f"Failed to update custom fields: {error}")
                success = False
        
        # Update cf fields one by one
        for key, value in cf_fields.items():
            response, error = await self.make_request(
                "PATCH", 
                f"/tickets/{ticket_id}", 
                access_token, 
                data={"cf": {key: value}}
            )
            
            if error:
                errors.append(f"Failed to update cf.{key}: {error}")
                success = False
        
        return success, errors
    
    async def preview_ticket_update(
        self, 
        ticket_id: str, 
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Preview the changes that would be made by an update.
        
        Args:
            ticket_id: Ticket ID
            update_data: Data to update
            
        Returns:
            Dictionary of changes
        """
        # Get the current ticket
        current, error = await self.get_ticket(ticket_id)
        if error or not current:
            return {"error": error or "Failed to fetch current ticket"}
        
        # Build a flat representation of the current ticket
        current_flat = self._flatten_dict(current)
        
        # Build a flat representation of the update
        update_flat = self._flatten_dict(update_data)
        
        # Find differences
        changes = {}
        for key, new_value in update_flat.items():
            if key in current_flat:
                old_value = current_flat[key]
                if old_value != new_value:
                    changes[key] = {"old": old_value, "new": new_value}
            else:
                changes[key] = {"old": None, "new": new_value}
        
        return changes
    
    def _flatten_dict(self, d: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """
        Flatten a nested dictionary.
        
        Args:
            d: Dictionary to flatten
            prefix: Prefix for keys
            
        Returns:
            Flattened dictionary
        """
        result = {}
        
        for key, value in d.items():
            new_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                result.update(self._flatten_dict(value, new_key))
            else:
                result[new_key] = value
        
        return result
    
    async def get_departments(self) -> List[Dict[str, Any]]:
        """
        Get all departments.
        
        Returns:
            List of department objects
        """
        access_token = await self.get_access_token()
        params = {"from": 1, "limit": 100}
        response, error = await self.make_request("GET", "/departments", access_token, params=params)
        
        if error or not response:
            return []
            
        if "data" in response and isinstance(response["data"], list):
            return response["data"]
            
        return []
    
    async def get_agents(self, limit: int = 200) -> List[Dict[str, Any]]:
        """
        Get all agents.
        
        Args:
            limit: Maximum number of agents to return
            
        Returns:
            List of agent objects
        """
        access_token = await self.get_access_token()
        params = {
            "from": 1,
            "limit": min(limit, 100),
            "include": "profile,role"
        }
        
        response, error = await self.make_request("GET", "/agents", access_token, params=params)
        
        if error or not response:
            return []
            
        if "data" in response and isinstance(response["data"], list):
            return response["data"]
            
        return []
    
    async def get_views(self) -> List[Dict[str, Any]]:
        """
        Get all views.
        
        Returns:
            List of view objects
        """
        access_token = await self.get_access_token()
        params = {"module": "tickets", "from": 1, "limit": 100}
        response, error = await self.make_request("GET", "/views", access_token, params=params)
        
        if error or not response:
            return []
            
        if "data" in response and isinstance(response["data"], list):
            return response["data"]
            
        return []
    
    async def fetch_tickets_by_view(
        self, 
        view_id: str, 
        page: int = 1, 
        limit: int = 50
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Fetch tickets by view.
        
        Args:
            view_id: View ID
            page: Page number (1-based)
            limit: Maximum number of tickets per page
            
        Returns:
            Tuple of (tickets_list, error_message)
        """
        access_token = await self.get_access_token()
        start = max(1, (page - 1) * limit + 1)
        params = {
            "viewId": view_id,
            "from": start,
            "limit": min(limit, 100),
            "sortBy": "createdTime"
        }
        
        response, error = await self.make_request("GET", "/tickets", access_token, params=params)
        
        if error:
            return [], error
            
        if response and "data" in response and isinstance(response["data"], list):
            return response["data"], None
            
        return [], "No tickets found"
    
    async def fetch_tickets_with_filters(
        self,
        filters: Dict[str, Any] = None,
        page: int = 1,
        limit: int = 50
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Fetch tickets with filters.
        
        Args:
            filters: Filter parameters
            page: Page number (1-based)
            limit: Maximum number of tickets per page
            
        Returns:
            Tuple of (tickets_list, error_message)
        """
        access_token = await self.get_access_token()
        start = max(1, (page - 1) * limit + 1)
        params = {"from": start, "limit": min(limit, 100), "sortBy": "createdTime"}
        
        if filters:
            # Valid filter keys for Zoho API
            valid_keys = [
                "status", "priority", "category", "subCategory", "departmentId",
                "viewId", "searchStr", "createdTimeRange", "modifiedTimeRange"
            ]
            
            for key in valid_keys:
                if key in filters and filters[key]:
                    params[key] = filters[key]
            
            # Handle special cases
            if filters.get("unassigned"):
                params["assignee"] = "null"
                
            assignee = filters.get("assignee") or filters.get("assigneeId")
            if assignee:
                params["assignee"] = assignee
        
        response, error = await self.make_request("GET", "/tickets", access_token, params=params)
        
        if error:
            return [], error
            
        if response and "data" in response and isinstance(response["data"], list):
            return response["data"], None
            
        return [], "No tickets found"
