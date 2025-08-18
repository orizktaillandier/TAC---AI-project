"""
Complete Zoho integration for the ticket classifier.
"""
import asyncio
import json
import httpx
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class ZohoTicketFetcher:
    """Fetch and process tickets from Zoho Desk API."""
    
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
        # Check if we have a valid token
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
                    
                    # Set expiration (default 1 hour, subtract 5 minutes for buffer)
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
        # Ensure we have a valid token
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
        """
        Get a specific ticket by ID with all custom fields.
        
        Returns:
            Tuple of (ticket_data, error_message)
        """
        print(f"Fetching ticket {ticket_id}...")
        
        data, error = await self.make_request(f"/tickets/{ticket_id}")
        
        if error:
            return None, error
        
        if not data:
            return None, "No ticket data returned"
        
        # Process and clean the ticket data
        processed_ticket = self._process_ticket_data(data)
        
        return processed_ticket, None
    
    async def get_ticket_threads(self, ticket_id: str) -> Tuple[List[Dict], Optional[str]]:
        """
        Get all threads/conversations for a ticket.
        
        Returns:
            Tuple of (threads_list, error_message)
        """
        print(f"Fetching threads for ticket {ticket_id}...")
        
        data, error = await self.make_request(f"/tickets/{ticket_id}/threads")
        
        if error:
            return [], error
        
        if not data or "data" not in data:
            return [], "No thread data returned"
        
        threads = data["data"]
        
        # Process threads to extract useful content
        processed_threads = []
        for thread in threads:
            processed_thread = self._process_thread_data(thread)
            if processed_thread:  # Only include threads with content
                processed_threads.append(processed_thread)
        
        return processed_threads, None
    
    async def get_ticket_with_threads(self, ticket_id: str) -> Tuple[Optional[Dict], List[Dict], Optional[str]]:
        """
        Get ticket and its threads in one call.
        
        Returns:
            Tuple of (ticket_data, threads_list, error_message)
        """
        print(f"Fetching complete ticket data for {ticket_id}...")
        
        # Get ticket data
        ticket, ticket_error = await self.get_ticket_by_id(ticket_id)
        if ticket_error:
            return None, [], ticket_error
        
        # Get threads
        threads, threads_error = await self.get_ticket_threads(ticket_id)
        if threads_error:
            print(f"Warning: Could not fetch threads: {threads_error}")
            # Continue without threads rather than failing completely
        
        return ticket, threads, None
    
    async def search_tickets(self, 
                           status: Optional[str] = None,
                           department_id: Optional[str] = None,
                           created_since: Optional[datetime] = None,
                           limit: int = 50) -> Tuple[List[Dict], Optional[str]]:
        """
        Search for tickets with filters.
        
        Args:
            status: Ticket status filter
            department_id: Department filter
            created_since: Only tickets created after this date
            limit: Maximum number of tickets to return
        
        Returns:
            Tuple of (tickets_list, error_message)
        """
        print(f"Searching tickets with filters...")
        
        params = {"limit": min(limit, 100)}  # Zoho API limit
        
        if status:
            params["status"] = status
        if department_id:
            params["departmentId"] = department_id
        if created_since:
            # Format datetime for Zoho API
            params["createdTimeRange"] = created_since.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        data, error = await self.make_request("/tickets", params)
        
        if error:
            return [], error
        
        if not data or "data" not in data:
            return [], "No tickets returned"
        
        tickets = data["data"]
        
        # Process each ticket
        processed_tickets = []
        for ticket in tickets:
            processed_ticket = self._process_ticket_data(ticket)
            processed_tickets.append(processed_ticket)
        
        return processed_tickets, None
    
    async def update_ticket_fields(self, ticket_id: str, updates: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Update ticket fields including custom fields.
        
        Args:
            ticket_id: Ticket ID
            updates: Dictionary of fields to update
        
        Returns:
            Tuple of (success, error_message)
        """
        print(f"Updating ticket {ticket_id} with fields: {list(updates.keys())}")
        
        # Separate standard fields from custom fields
        standard_fields = {}
        cf_fields = {}
        
        for key, value in updates.items():
            if key.startswith("cf_"):
                cf_fields[key] = value
            else:
                standard_fields[key] = value
        
        # Build update payload
        update_payload = {}
        
        if standard_fields:
            update_payload.update(standard_fields)
        
        if cf_fields:
            update_payload["cf"] = cf_fields
        
        # Make the update request
        data, error = await self.make_request(f"/tickets/{ticket_id}", method="PATCH", data=update_payload)
        
        if error:
            return False, error
        
        print(f"Successfully updated ticket {ticket_id}")
        return True, None
    
    def _process_ticket_data(self, raw_ticket: Dict) -> Dict:
        """Process raw ticket data into a clean format."""
        
        # Extract key fields for classification
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
        
        # Extract custom fields (both formats)
        custom_fields = {}
        
        # Extract from cf object
        if "cf" in raw_ticket and raw_ticket["cf"]:
            for key, value in raw_ticket["cf"].items():
                if value is not None and value != "":
                    custom_fields[key] = value
        
        # Extract from customFields object 
        if "customFields" in raw_ticket and raw_ticket["customFields"]:
            for key, value in raw_ticket["customFields"].items():
                if value is not None and value != "":
                    # Convert display name to cf_ format for consistency
                    cf_key = f"cf_{key.lower().replace(' ', '_').replace('/', '_').replace('?', '').replace(':', '')}"
                    custom_fields[cf_key] = value
        
        processed["custom_fields"] = custom_fields
        
        # Extract specifically the fields we care about for classification
        processed["syndicator"] = custom_fields.get("cf_syndicators")
        processed["inventory_type"] = custom_fields.get("cf_inventory_type") or custom_fields.get("inventory_type")
        processed["oem"] = custom_fields.get("cf_oem")
        processed["product"] = custom_fields.get("cf_product")
        
        return processed
    
    def _process_thread_data(self, raw_thread: Dict) -> Optional[Dict]:
        """Process raw thread data into a clean format."""
        
        # Skip threads without useful content
        summary = raw_thread.get("summary", "").strip()
        if not summary or len(summary) < 10:
            return None
        
        # Extract author info
        author = raw_thread.get("author", {})
        author_name = author.get("name") or author.get("email", "Unknown")
        
        processed = {
            "id": raw_thread.get("id"),
            "summary": summary,
            "content": summary,  # Use summary as content
            "author_name": author_name,
            "author_email": author.get("email"),
            "author_type": author.get("type"),
            "created_time": raw_thread.get("createdTime"),
            "direction": raw_thread.get("direction"),
            "channel": raw_thread.get("channel"),
            "from_email": raw_thread.get("fromEmailAddress"),
        }
        
        return processed

# Example usage and testing
async def test_zoho_integration():
    """Test the Zoho integration."""
    print("Testing Zoho Integration")
    print("=" * 30)
    
    fetcher = ZohoTicketFetcher()
    
    # Test 1: Get a specific ticket
    ticket_id = "319204000303289257"  # Use the ticket we found earlier
    
    ticket, threads, error = await fetcher.get_ticket_with_threads(ticket_id)
    
    if error:
        print(f"Error: {error}")
        return
    
    print(f"\nTicket Data:")
    print(f"  ID: {ticket['id']}")
    print(f"  Subject: {ticket['subject']}")
    print(f"  Status: {ticket['status']}")
    print(f"  Custom Fields: {len(ticket['custom_fields'])} found")
    
    # Show relevant custom fields
    if ticket['custom_fields']:
        print(f"  Relevant Custom Fields:")
        for key, value in ticket['custom_fields'].items():
            if 'syndic' in key or 'inventory' in key or 'oem' in key:
                print(f"    {key}: {value}")
    
    print(f"\nThreads: {len(threads)} found")
    for i, thread in enumerate(threads[:2]):  # Show first 2 threads
        print(f"  Thread {i+1}: {thread['summary'][:100]}...")
    
    # Test 2: Search for recent tickets
    print(f"\nSearching for recent tickets...")
    
    recent_tickets, search_error = await fetcher.search_tickets(limit=5)
    
    if search_error:
        print(f"Search error: {search_error}")
    else:
        print(f"Found {len(recent_tickets)} recent tickets:")
        for ticket in recent_tickets:
            print(f"  - {ticket['id']}: {ticket['subject'][:50]}...")

if __name__ == "__main__":
    asyncio.run(test_zoho_integration())
