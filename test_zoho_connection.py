#!/usr/bin/env python3
"""
Test script to explore Zoho API fields and structure - PowerShell friendly.
"""
import asyncio
import json
import httpx
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ZohoExplorer:
    """Explore Zoho API to understand available fields."""
    
    def __init__(self):
        self.client_id = os.getenv("ZOHO_CLIENT_ID")
        self.client_secret = os.getenv("ZOHO_CLIENT_SECRET") 
        self.refresh_token = os.getenv("ZOHO_REFRESH_TOKEN")
        self.org_id = os.getenv("ZOHO_ORG_ID")
        self.base_url = os.getenv("ZOHO_BASE_URL", "https://desk.zoho.com/api/v1")
        
        self.access_token = None
        
        print("=== Zoho Configuration ===")
        print(f"Base URL: {self.base_url}")
        print(f"Org ID: {self.org_id}")
        print(f"Client ID: {self.client_id[:10] if self.client_id else 'None'}...")
        print(f"Has Refresh Token: {'Yes' if self.refresh_token else 'No'}")
        print()
    
    async def get_access_token(self):
        """Get access token from refresh token."""
        print("Getting access token...")
        
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
                    print(f"SUCCESS: Got access token: {self.access_token[:20] if self.access_token else 'None'}...")
                    return True
                else:
                    print(f"ERROR: Token request failed: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
            except Exception as e:
                print(f"ERROR: Exception during token request: {e}")
                return False
    
    def get_headers(self):
        """Get API headers."""
        return {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "orgId": self.org_id,
            "Accept": "application/json",
        }
    
    async def make_request(self, endpoint, params=None):
        """Make API request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self.get_headers()
        
        print(f"Making request to: {endpoint}")
        print(f"URL: {url}")
        if params:
            print(f"Params: {params}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, params=params, timeout=30)
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    return response.json(), None
                else:
                    error = f"Error {response.status_code}: {response.text[:200]}"
                    print(f"Error: {error}")
                    return None, error
            except Exception as e:
                error = f"Exception: {str(e)}"
                print(f"Error: {error}")
                return None, error
    
    async def test_basic_connection(self):
        """Test basic API connection."""
        print("\n=== Testing Basic Connection ===")
        
        # Try to get departments (simple endpoint)
        data, error = await self.make_request("/departments")
        
        if error:
            print(f"FAILED: {error}")
            return False
        
        if data and "data" in data:
            departments = data["data"]
            print(f"SUCCESS: Connected! Found {len(departments)} departments")
            for dept in departments[:3]:
                print(f"  - {dept.get('name')} (ID: {dept.get('id')})")
            return True
        else:
            print("FAILED: No data returned")
            return False
    
    async def get_sample_ticket(self):
        """Get one sample ticket to examine structure."""
        print("\n=== Getting Sample Ticket ===")
        
        # Get one ticket
        data, error = await self.make_request("/tickets", {"limit": 1})
        
        if error:
            print(f"FAILED: {error}")
            return None
        
        if not data or "data" not in data or not data["data"]:
            print("FAILED: No tickets returned")
            return None
        
        ticket = data["data"][0]
        ticket_id = ticket.get("id")
        
        print(f"SUCCESS: Got ticket {ticket_id}")
        print(f"Subject: {ticket.get('subject', 'No subject')}")
        
        # Show all available fields
        print(f"\nAll fields in ticket:")
        for key in sorted(ticket.keys()):
            value = ticket[key]
            if isinstance(value, dict):
                print(f"  {key}: [dict with {len(value)} keys]")
            elif isinstance(value, list):
                print(f"  {key}: [list with {len(value)} items]")
            elif value is None:
                print(f"  {key}: None")
            else:
                print(f"  {key}: {str(value)[:60]}...")
        
        # Check for custom fields
        if "customFields" in ticket and ticket["customFields"]:
            print(f"\nCustom Fields found:")
            for key, value in ticket["customFields"].items():
                print(f"  {key}: {value}")
        else:
            print(f"\nNo customFields found")
        
        if "cf" in ticket and ticket["cf"]:
            print(f"\nCF Fields found:")
            for key, value in ticket["cf"].items():
                print(f"  {key}: {value}")
        else:
            print(f"\nNo cf fields found")
        
        # Save to file for detailed inspection
        with open("sample_ticket.json", "w", encoding='utf-8') as f:
            json.dump(ticket, f, indent=2, default=str)
        print(f"\nSaved full ticket to: sample_ticket.json")
        
        return ticket
    
    async def get_ticket_threads(self, ticket_id):
        """Get threads for a specific ticket."""
        print(f"\n=== Getting Threads for Ticket {ticket_id} ===")
        
        data, error = await self.make_request(f"/tickets/{ticket_id}/threads")
        
        if error:
            print(f"FAILED: {error}")
            return None
        
        if not data or "data" not in data:
            print("FAILED: No thread data")
            return None
        
        threads = data["data"]
        print(f"SUCCESS: Got {len(threads)} threads")
        
        if threads:
            first_thread = threads[0]
            print(f"\nFirst thread fields:")
            for key in sorted(first_thread.keys()):
                value = first_thread[key]
                if isinstance(value, dict):
                    print(f"  {key}: [dict with {len(value)} keys]")
                elif isinstance(value, list):
                    print(f"  {key}: [list with {len(value)} items]")
                elif value is None:
                    print(f"  {key}: None")
                else:
                    print(f"  {key}: {str(value)[:60]}...")
            
            # Save threads to file
            with open("sample_threads.json", "w", encoding='utf-8') as f:
                json.dump(threads, f, indent=2, default=str)
            print(f"\nSaved threads to: sample_threads.json")
        
        return threads

async def main():
    """Main exploration function."""
    print("Starting Zoho API Exploration...")
    print("=" * 50)
    
    explorer = ZohoExplorer()
    
    # Step 1: Get access token
    if not await explorer.get_access_token():
        print("\nFAILED: Could not get access token")
        print("Check your .env file has:")
        print("  ZOHO_CLIENT_ID=...")
        print("  ZOHO_CLIENT_SECRET=...")
        print("  ZOHO_REFRESH_TOKEN=...")
        print("  ZOHO_ORG_ID=...")
        return
    
    # Step 2: Test basic connection
    if not await explorer.test_basic_connection():
        print("\nFAILED: Basic connection test failed")
        return
    
    # Step 3: Get sample ticket
    ticket = await explorer.get_sample_ticket()
    
    # Step 4: Get threads for the sample ticket
    if ticket:
        ticket_id = ticket.get("id")
        await explorer.get_ticket_threads(ticket_id)
    
    print(f"\n" + "=" * 50)
    print("Exploration Complete!")
    print("Check these files for detailed structure:")
    print("  - sample_ticket.json")
    print("  - sample_threads.json")

if __name__ == "__main__":
    asyncio.run(main())
