#!/usr/bin/env python3
"""
Specifically test for custom fields in Zoho API.
"""
import asyncio
import json
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

class ZohoCustomFieldsExplorer:
    """Explore custom fields specifically."""
    
    def __init__(self):
        self.client_id = os.getenv("ZOHO_CLIENT_ID")
        self.client_secret = os.getenv("ZOHO_CLIENT_SECRET") 
        self.refresh_token = os.getenv("ZOHO_REFRESH_TOKEN")
        self.org_id = os.getenv("ZOHO_ORG_ID")
        self.base_url = os.getenv("ZOHO_BASE_URL", "https://desk.zoho.com/api/v1")
        self.access_token = None
    
    async def get_access_token(self):
        """Get access token."""
        token_url = "https://accounts.zoho.com/oauth/v2/token"
        
        data = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data, timeout=30)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                return True
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
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params, timeout=30)
            if response.status_code == 200:
                return response.json(), None
            else:
                return None, f"Error {response.status_code}: {response.text}"
    
    async def test_layout_fields(self):
        """Check what fields are defined in layouts."""
        print("=== Testing Layout Fields ===")
        
        # Get layouts
        data, error = await self.make_request("/layouts", {"module": "tickets"})
        
        if error:
            print(f"Failed to get layouts: {error}")
            return
        
        if not data or "data" not in data:
            print("No layout data returned")
            return
        
        layouts = data["data"]
        print(f"Found {len(layouts)} layouts")
        
        for layout in layouts[:2]:  # Check first 2 layouts
            layout_id = layout.get("id")
            layout_name = layout.get("name")
            print(f"\nLayout: {layout_name} (ID: {layout_id})")
            
            # Get fields for this layout
            fields_data, fields_error = await self.make_request(f"/layouts/{layout_id}")
            
            if fields_error:
                print(f"  Failed to get fields: {fields_error}")
                continue
            
            if fields_data and "sections" in fields_data:
                print(f"  Found sections with fields:")
                
                custom_fields_found = []
                
                for section in fields_data["sections"]:
                    section_name = section.get("name", "Unnamed")
                    fields = section.get("fields", [])
                    
                    for field in fields:
                        field_name = field.get("fieldName", "")
                        field_label = field.get("displayLabel", "")
                        field_type = field.get("type", "")
                        is_custom = field.get("isCustomField", False)
                        
                        if is_custom or field_name.startswith("cf_"):
                            custom_fields_found.append({
                                "name": field_name,
                                "label": field_label,
                                "type": field_type,
                                "section": section_name
                            })
                
                if custom_fields_found:
                    print(f"  CUSTOM FIELDS FOUND:")
                    for cf in custom_fields_found:
                        print(f"    - {cf['name']} ({cf['label']}) - Type: {cf['type']}")
                else:
                    print(f"    No custom fields found in this layout")
        
        # Save layout data
        with open("layout_fields.json", "w", encoding='utf-8') as f:
            json.dump(layouts, f, indent=2, default=str)
        print(f"\nSaved layout data to: layout_fields.json")
    
    async def test_tickets_with_include(self):
        """Test getting tickets with include parameters."""
        print("\n=== Testing Tickets with Include Parameters ===")
        
        # Try different include parameters
        include_options = [
            "customFields",
            "cf", 
            "customFields,cf",
            "all"
        ]
        
        for include_param in include_options:
            print(f"\nTrying include={include_param}")
            
            params = {
                "limit": 1,
                "include": include_param
            }
            
            data, error = await self.make_request("/tickets", params)
            
            if error:
                print(f"  Error: {error}")
                continue
            
            if data and "data" in data and data["data"]:
                ticket = data["data"][0]
                ticket_id = ticket.get("id")
                
                print(f"  Ticket {ticket_id} fields:")
                
                # Check for custom field objects
                has_custom_fields = "customFields" in ticket and ticket["customFields"]
                has_cf = "cf" in ticket and ticket["cf"]
                
                print(f"    Has customFields: {has_custom_fields}")
                print(f"    Has cf: {has_cf}")
                
                if has_custom_fields:
                    print(f"    customFields content:")
                    for key, value in ticket["customFields"].items():
                        print(f"      {key}: {value}")
                
                if has_cf:
                    print(f"    cf content:")
                    for key, value in ticket["cf"].items():
                        print(f"      {key}: {value}")
                
                # Save this version
                filename = f"ticket_include_{include_param.replace(',', '_')}.json"
                with open(filename, "w", encoding='utf-8') as f:
                    json.dump(ticket, f, indent=2, default=str)
                print(f"    Saved to: {filename}")
    
    async def test_specific_ticket_details(self, ticket_id):
        """Get detailed info for a specific ticket."""
        print(f"\n=== Testing Specific Ticket Details: {ticket_id} ===")
        
        # Try getting ticket with different parameters
        test_params = [
            {},
            {"include": "customFields"},
            {"include": "cf"},
            {"include": "customFields,cf"},
            {"include": "all"}
        ]
        
        for i, params in enumerate(test_params):
            print(f"\nTest {i+1}: params={params}")
            
            data, error = await self.make_request(f"/tickets/{ticket_id}", params)
            
            if error:
                print(f"  Error: {error}")
                continue
            
            if data:
                # Check what we got
                has_custom_fields = "customFields" in data and data["customFields"]
                has_cf = "cf" in data and data["cf"]
                
                print(f"  Has customFields: {has_custom_fields}")
                print(f"  Has cf: {has_cf}")
                
                if has_custom_fields:
                    print(f"  customFields:")
                    for key, value in data["customFields"].items():
                        print(f"    {key}: {value}")
                
                if has_cf:
                    print(f"  cf:")
                    for key, value in data["cf"].items():
                        print(f"    {key}: {value}")
                
                # Show all top-level keys
                print(f"  All keys: {list(data.keys())}")

async def main():
    """Main function."""
    print("Testing Custom Fields in Zoho API")
    print("=" * 40)
    
    explorer = ZohoCustomFieldsExplorer()
    
    if not await explorer.get_access_token():
        print("Failed to get access token")
        return
    
    # Test 1: Check layout fields (this shows what custom fields are defined)
    await explorer.test_layout_fields()
    
    # Test 2: Try different include parameters
    await explorer.test_tickets_with_include()
    
    # Test 3: Test specific ticket (use the one we found earlier)
    await explorer.test_specific_ticket_details("319204000303289257")
    
    print(f"\n" + "=" * 40)
    print("Custom Fields Testing Complete!")

if __name__ == "__main__":
    asyncio.run(main())
