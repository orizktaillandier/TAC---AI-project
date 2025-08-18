import asyncio
import json
import httpx
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class ZohoTicketFetcher:
    def __init__(self):
        self.client_id = os.getenv("ZOHO_CLIENT_ID")
        self.client_secret = os.getenv("ZOHO_CLIENT_SECRET") 
        self.refresh_token = os.getenv("ZOHO_REFRESH_TOKEN")
        self.org_id = os.getenv("ZOHO_ORG_ID")
        self.base_url = os.getenv("ZOHO_BASE_URL", "https://desk.zoho.com/api/v1")
        
        self.access_token = None
        self.token_expires_at = None
    
    async def get_access_token(self, force_refresh=False):
        """Get or refresh access token."""
        if (not force_refresh and self.access_token and 
            self.token_expires_at and datetime.now() < self.token_expires_at):
            return self.access_token
        
        print("Refreshing Zoho access token...")
        
        token_url = "https://accounts.zoho.com/oauth/v2/token"
        
        data = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    token_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.access_token = token_data.get("access_token")
                    
                    expires_in = token_data.get("expires_in", 3600)
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
                    
                    print(f"Token refreshed successfully, expires at {self.token_expires_at}")
                    return self.access_token
                else:
                    error_msg = f"Token refresh failed: {response.status_code} - {response.text}"
                    print(error_msg)
                    raise Exception(error_msg)
                    
            except Exception as e:
                print(f"Error refreshing token: {e}")
                raise
    
    def get_headers(self):
        """Get API request headers."""
        return {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "orgId": self.org_id,
            "Accept": "application/json",
        }
    
    async def make_request(self, endpoint, params=None, method="GET", data=None):
        """Make authenticated request to Zoho API."""
        await self.get_access_token()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self.get_headers()
        
        if data and method in ["POST", "PATCH", "PUT"]:
            headers["Content-Type"] = "application/json"
        
        async with httpx.AsyncClient() as client:
            try:
                if method == "GET":
                    response = await client.get(url, headers=headers, params=params, timeout=30)
                elif method == "POST":
                    response = await client.post(url, headers=headers, params=params, json=data, timeout=30)
                elif method == "PATCH":
                    response = await client.patch(url, headers=headers, params=params, json=data, timeout=30)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                if response.status_code in [200, 201]:
                    return response.json(), None
                elif response.status_code == 401:
                    # Token expired, try once more with fresh token
                    await self.get_access_token(force_refresh=True)
                    headers = self.get_headers()
                    
                    if method == "GET":
                        response = await client.get(url, headers=headers, params=params, timeout=30)
                    elif method == "POST":
                        response = await client.post(url, headers=headers, params=params, json=data, timeout=30)
                    elif method == "PATCH":
                        response = await client.patch(url, headers=headers, params=params, json=data, timeout=30)
                    
                    if response.status_code in [200, 201]:
                        return response.json(), None
                
                error_msg = f"API Error {response.status_code}: {response.text}"
                return None, error_msg
                
            except Exception as e:
                error_msg = f"Request Exception: {str(e)}"
                return None, error_msg
    
    async def get_ticket_by_id(self, ticket_id: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Get a specific ticket by ID with all custom fields."""
        print(f"Fetching ticket {ticket_id}...")
        
        data, error = await self.make_request(f"/tickets/{ticket_id}")
        
        if error:
            return None, error
        
        if not data:
            return None, "No ticket data returned"
        
        processed_ticket = self._process_ticket_data(data)
        return processed_ticket, None
    
    async def get_ticket_threads(self, ticket_id: str) -> Tuple[List[Dict], Optional[str]]:
        """Get all threads/conversations for a ticket."""
        print(f"Fetching threads for ticket {ticket_id}...")
        
        data, error = await self.make_request(f"/tickets/{ticket_id}/threads")
        
        if error:
            return [], error
        
        if not data or "data" not in data:
            return [], "No thread data returned"
        
        threads = data["data"]
        processed_threads = []
        for thread in threads:
            processed_thread = self._process_thread_data(thread)
            if processed_thread:
                processed_threads.append(processed_thread)
        
        return processed_threads, None
    
    async def get_ticket_with_threads(self, ticket_id: str) -> Tuple[Optional[Dict], List[Dict], Optional[str]]:
        """Get ticket and its threads in one call."""
        print(f"Fetching complete ticket data for {ticket_id}...")
        
        ticket, ticket_error = await self.get_ticket_by_id(ticket_id)
        if ticket_error:
            return None, [], ticket_error
        
        threads, threads_error = await self.get_ticket_threads(ticket_id)
        if threads_error:
            print(f"Warning: Could not fetch threads: {threads_error}")
        
        return ticket, threads, None
    
    async def update_ticket_custom_fields(self, ticket_id: str, update_data: Dict[str, Any], dry_run: bool = False) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Update custom fields for a ticket.
        
        Args:
            ticket_id: Zoho ticket ID
            update_data: Dictionary of fields to update (can contain cf, customFields, and regular fields)
            dry_run: If True, return what would be updated without making changes
            
        Returns:
            Tuple of (success, error_message, changes_made)
        """
        print(f"{'[DRY RUN] ' if dry_run else ''}Updating ticket {ticket_id}...")
        print(f"Update data: {update_data}")
        
        if dry_run:
            # Get current ticket to show what would change
            current_ticket, error = await self.get_ticket_by_id(ticket_id)
            if error:
                return False, f"Could not fetch current ticket: {error}", {}
            
            current_cf = current_ticket.get('custom_fields', {})
            changes = {}
            
            # Check cf changes
            if 'cf' in update_data:
                for field, new_value in update_data['cf'].items():
                    old_value = current_cf.get(field, '')
                    if old_value != new_value:
                        changes[f"cf.{field}"] = {"old": old_value, "new": new_value}
            
            # Check customFields changes
            if 'customFields' in update_data:
                for field, new_value in update_data['customFields'].items():
                    # Map customFields to cf_* format for comparison
                    cf_field = f"cf_{field.lower().replace(' ', '_').replace('/', '_').replace('?', '').replace(':', '')}"
                    old_value = current_cf.get(cf_field, '')
                    if old_value != new_value:
                        changes[f"customFields.{field}"] = {"old": old_value, "new": new_value}
            
            # Check regular field changes
            for field, new_value in update_data.items():
                if field not in ['cf', 'customFields']:
                    old_value = current_ticket.get(field, '')
                    if old_value != new_value:
                        changes[field] = {"old": old_value, "new": new_value}
            
            return True, None, {"would_change": changes, "dry_run": True}
        
        # Make the update request
        print(f"Update payload: {json.dumps(update_data, indent=2)}")
        
        data, error = await self.make_request(f"/tickets/{ticket_id}", method="PATCH", data=update_data)
        
        if error:
            return False, error, {}
        
        print(f"Successfully updated ticket {ticket_id}")
        
        # Compile list of updated fields
        updated_fields = []
        if 'cf' in update_data:
            updated_fields.extend([f"cf.{f}" for f in update_data['cf'].keys()])
        if 'customFields' in update_data:
            updated_fields.extend([f"customFields.{f}" for f in update_data['customFields'].keys()])
        for field in update_data:
            if field not in ['cf', 'customFields']:
                updated_fields.append(field)
        
        return True, None, {"updated_fields": updated_fields}
    
    async def search_tickets(self, 
                           status: Optional[str] = None,
                           department_id: Optional[str] = None,
                           created_since: Optional[datetime] = None,
                           limit: int = 50) -> Tuple[List[Dict], Optional[str]]:
        """Search for tickets with filters."""
        print(f"Searching tickets with filters...")
        
        params = {"limit": min(limit, 100)}
        
        if status:
            params["status"] = status
        if department_id:
            params["departmentId"] = department_id
        if created_since:
            params["createdTimeRange"] = created_since.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        data, error = await self.make_request("/tickets", params)
        
        if error:
            return [], error
        
        if not data or "data" not in data:
            return [], "No tickets returned"
        
        tickets = data["data"]
        processed_tickets = []
        for ticket in tickets:
            processed_ticket = self._process_ticket_data(ticket)
            processed_tickets.append(processed_ticket)
        
        return processed_tickets, None
    
    def _process_ticket_data(self, raw_ticket: Dict) -> Dict:
        """Process raw ticket data into a clean format."""
        processed = {
            "id": raw_ticket.get("id"),
            "ticket_number": raw_ticket.get("ticketNumber"),
            "subject": raw_ticket.get("subject"),
            "description": raw_ticket.get("description"),
            "status": raw_ticket.get("status"),
            "category": raw_ticket.get("category"),
            "sub_category": raw_ticket.get("subCategory"),
            "priority": raw_ticket.get("priority"),
            "created_time": raw_ticket.get("createdTime"),
            "email": raw_ticket.get("email"),
            "contact_id": raw_ticket.get("contactId"),
            "department_id": raw_ticket.get("departmentId"),
            "assignee_id": raw_ticket.get("assigneeId"),
            "web_url": raw_ticket.get("webUrl"),
        }
        
        # Extract custom fields
        custom_fields = {}
        
        if "cf" in raw_ticket and raw_ticket["cf"]:
            for key, value in raw_ticket["cf"].items():
                if value is not None and value != "":
                    custom_fields[key] = value
        
        if "customFields" in raw_ticket and raw_ticket["customFields"]:
            for key, value in raw_ticket["customFields"].items():
                if value is not None and value != "":
                    cf_key = f"cf_{key.lower().replace(' ', '_').replace('/', '_').replace('?', '').replace(':', '')}"
                    custom_fields[cf_key] = value
        
        processed["custom_fields"] = custom_fields
        
        return processed
    
    def _process_thread_data(self, raw_thread: Dict) -> Optional[Dict]:
        print(f"RAW THREAD DEBUG: {json.dumps(raw_thread, indent=2)}")  # ADD THIS LINE
        """Process raw thread data into a clean format."""
        """Process raw thread data into a clean format."""
        summary = raw_thread.get("summary", "").strip()
        if not summary or len(summary) < 10:
            return None
        
        author = raw_thread.get("author", {})
        author_name = author.get("name") or author.get("email", "Unknown")
        
        processed = {
            "id": raw_thread.get("id"),
            "summary": summary,
            "content": summary,
            "author_name": author_name,
            "author_email": author.get("email"),
            "author_type": author.get("type"),
            "created_time": raw_thread.get("createdTime"),
            "direction": raw_thread.get("direction"),
            "channel": raw_thread.get("channel"),
            "from_email": raw_thread.get("fromEmailAddress"),
        }
        
        return processed
