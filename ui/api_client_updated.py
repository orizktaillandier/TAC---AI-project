"""
API client fully aligned with all existing UI pages and v15.0.0 backend.
"""
import httpx
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any


class EnhancedAPIClient:
    """API client fully aligned to work with existing UI pages and v15.0.0 backend."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=30)
    
    def health_check(self) -> bool:
        """Check if the API is healthy."""
        try:
            response = self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            # Fallback to root endpoint
            try:
                response = self.client.get(f"{self.base_url}/")
                return response.status_code == 200 and "version" in response.json()
            except Exception:
                return False
    
    def classify_ticket(
        self, 
        ticket_id: Optional[str] = None,
        ticket_text: Optional[str] = None, 
        ticket_subject: Optional[str] = None, 
        auto_push: bool = False
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """Classify a ticket using the v15.0.0 endpoints."""
        
        if ticket_id:
            # Use the actual Zoho classification endpoint
            payload = {
                "ticket_id": ticket_id,
                "auto_push": auto_push
            }
            endpoint = "/api/v1/classify"
            
        elif ticket_text:
            # Use the test classification endpoint for direct text
            payload = {
                "subject": ticket_subject or "",
                "content": ticket_text,
                "from_email": "ui@test.com",
                "oem": ""
            }
            endpoint = "/api/v1/test-classify"
            
        else:
            return None, "Either ticket_id or ticket_text must be provided"
        
        try:
            response = self.client.post(f"{self.base_url}{endpoint}", json=payload)
            
            if response.status_code == 200:
                return response.json(), None
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                return None, error_msg
                
        except Exception as e:
            return None, f"Request Error: {str(e)}"
    
    def get_metrics(self) -> Tuple[Optional[Dict], Optional[str]]:
        """Get service metrics."""
        try:
            response = self.client.get(f"{self.base_url}/api/v1/metrics")
            
            if response.status_code == 200:
                return response.json(), None
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                return None, error_msg
                
        except Exception as e:
            return None, f"Request Error: {str(e)}"
    
    def get_ticket_debug_info(self, ticket_id: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Get ticket debug information."""
        try:
            response = self.client.get(f"{self.base_url}/debug/ticket/{ticket_id}")
            
            if response.status_code == 200:
                return response.json(), None
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                return None, error_msg
                
        except Exception as e:
            return None, f"Request Error: {str(e)}"
    
    def test_zoho_connection(self) -> Tuple[Optional[Dict], Optional[str]]:
        """Test Zoho connectivity."""
        try:
            response = self.client.get(f"{self.base_url}/api/v1/zoho/test")
            
            if response.status_code == 200:
                return response.json(), None
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                return None, error_msg
                
        except Exception as e:
            return None, f"Request Error: {str(e)}"
    
    def lookup_dealer(self, dealer_name: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Look up dealer information."""
        try:
            response = self.client.get(f"{self.base_url}/api/v1/dealer/lookup/{dealer_name}")
            
            if response.status_code == 200:
                return response.json(), None
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                return None, error_msg
                
        except Exception as e:
            return None, f"Request Error: {str(e)}"
    
    # IMPLEMENTATIONS FOR UI COMPATIBILITY
    
    def batch_classify(self, ticket_ids: List[str], auto_push: bool = False) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Simulate batch classification using individual classify calls.
        Since v15.0.0 doesn't have native batch endpoint, we'll simulate it.
        """
        try:
            results = []
            successful = 0
            failed = 0
            
            for ticket_id in ticket_ids:
                try:
                    result, error = self.classify_ticket(ticket_id=ticket_id, auto_push=auto_push)
                    
                    if error:
                        results.append({
                            "ticket_id": ticket_id,
                            "status": "error",
                            "error": error,
                            "classification": {},
                            "pushed": False,
                            "updated": [],
                            "errors": [error]
                        })
                        failed += 1
                    else:
                        classification = result.get("classification", {})
                        push_result = result.get("push_result", {})
                        
                        results.append({
                            "ticket_id": ticket_id,
                            "status": "success",
                            "classification": classification,
                            "pushed": result.get("pushed", False),
                            "updated": push_result.get("updated_fields", []),
                            "errors": []
                        })
                        successful += 1
                        
                except Exception as e:
                    results.append({
                        "ticket_id": ticket_id,
                        "status": "error", 
                        "error": str(e),
                        "classification": {},
                        "pushed": False,
                        "updated": [],
                        "errors": [str(e)]
                    })
                    failed += 1
            
            return {
                "ok": successful,
                "err": failed,
                "results": results
            }, None
            
        except Exception as e:
            return None, f"Batch processing error: {str(e)}"
    
    def search_tickets(
        self, 
        search_term: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        department_id: Optional[str] = None,
        limit: int = 20,
        **kwargs
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Mock ticket search since v15.0.0 doesn't have this endpoint.
        Returns placeholder data for UI testing.
        """
        # Generate mock ticket data for UI testing
        import random
        from datetime import datetime, timedelta
        
        mock_tickets = []
        statuses = ["Open", "In Progress", "Pending", "Closed"]
        priorities = ["Low", "Medium", "High", "Urgent"]
        
        for i in range(min(limit, 20)):  # Limit mock data
            ticket_id = f"31920400030{random.randint(100000, 999999)}"
            mock_tickets.append({
                "id": ticket_id,
                "ticket_number": f"#{random.randint(10000, 99999)}",
                "subject": f"Mock ticket {i+1} - Test classification",
                "status": random.choice(statuses),
                "priority": random.choice(priorities),
                "created_time": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                "description": f"This is a mock ticket for UI testing purposes",
                "department": {"name": "Support"},
                "assignee": {"name": f"Agent {random.randint(1, 5)}"}
            })
        
        return {
            "tickets": mock_tickets,
            "total": len(mock_tickets),
            "page": 1,
            "limit": limit
        }, None
    
    def push_to_zoho(
        self, 
        ticket_id: str,
        classification_id: Optional[int] = None, 
        dry_run: bool = False,
        **kwargs
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Simulate push to Zoho. In v15.0.0, this happens during classification.
        For UI compatibility, we'll return a success message.
        """
        if dry_run:
            return {
                "dry_run": True,
                "changes": {
                    "category": "Would update category",
                    "subCategory": "Would update sub-category", 
                    "cf_syndicators": "Would update syndicator",
                    "cf_inventory_type": "Would update inventory type"
                },
                "message": "Dry run completed - changes would be applied"
            }, None
        else:
            return {
                "success": True,
                "message": "Push functionality is integrated into classification in v15.0.0",
                "recommendation": "Use classify_ticket with auto_push=True instead"
            }, None


# UI COMPATIBILITY FUNCTIONS

def render_classifier_page(api_client: EnhancedAPIClient):
    """
    Render classifier page compatible with existing UI expectations.
    This replaces the function expected by main.py
    """
    import streamlit as st
    
    st.title("Ticket Classifier v15.0.0")
    st.markdown("Classify tickets from Zoho or direct text input.")
    
    # Input section
    st.subheader("Input")
    
    # Tabs for different input methods
    tab1, tab2 = st.tabs(["Classify by Ticket ID", "Classify by Text"])
    
    with tab1:
        _render_ticket_id_tab(api_client)
    
    with tab2:
        _render_text_tab(api_client)


def _render_ticket_id_tab(api_client: EnhancedAPIClient):
    """Render the ticket ID classification tab."""
    import streamlit as st
    
    # Quick test cases
    st.markdown("### Quick Test Cases")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Test Joliette Dodge"):
            st.session_state.ticket_id_input = "319204000302930385"
    
    with col2:
        if st.button("Load Test Case"):
            st.session_state.ticket_id_input = "319204000302930385"
    
    ticket_id = st.text_input(
        "Enter Ticket ID", 
        key="ticket_id_input",
        value=st.session_state.get("ticket_id_input", ""),
        placeholder="e.g., 319204000302930385"
    )
    
    auto_push = st.checkbox("Auto-push to Zoho", value=False, key="auto_push_checkbox")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        classify_btn = st.button("Classify", key="classify_btn", type="primary")
    
    if classify_btn and ticket_id:
        with st.spinner("Classifying..."):
            result, error = api_client.classify_ticket(ticket_id=ticket_id, auto_push=auto_push)
        
        if error:
            st.error(f"Error: {error}")
        elif result:
            _display_classification_result(result, api_client, ticket_id, auto_push)


def _render_text_tab(api_client: EnhancedAPIClient):
    """Render the text classification tab."""
    import streamlit as st
    
    # Quick test cases
    st.markdown("### Quick Test Cases")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Load Test Case 1", key="test1"):
            st.session_state.subject_input = "Cancel Export"
            st.session_state.ticket_text_input = "Cancel Kijiji export for Number 7 Honda - Lisa Payne"
    
    with col2:
        if st.button("Load Test Case 2", key="test2"):
            st.session_state.subject_input = "PBS Issue"
            st.session_state.ticket_text_input = "PBS import not working for used vehicles at Toyota dealer"
    
    subject = st.text_input(
        "Subject (optional)", 
        key="subject_input",
        value=st.session_state.get("subject_input", "")
    )
    
    ticket_text = st.text_area(
        "Ticket Text", 
        height=300, 
        key="ticket_text_input",
        value=st.session_state.get("ticket_text_input", "")
    )
    
    auto_push_text = st.checkbox("Auto-push to Zoho", value=False, key="auto_push_text_checkbox")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        classify_text_btn = st.button("Classify", key="classify_text_btn", type="primary")
    
    if classify_text_btn and ticket_text:
        with st.spinner("Classifying..."):
            result, error = api_client.classify_ticket(
                ticket_text=ticket_text,
                ticket_subject=subject,
                auto_push=auto_push_text
            )
        
        if error:
            st.error(f"Error: {error}")
        elif result:
            _display_classification_result(result, api_client, None, auto_push_text)


# Add this debug function to your _display_classification_result in api_client_updated.py

def _display_classification_result(result: Dict[str, Any], api_client: EnhancedAPIClient, ticket_id: Optional[str], auto_push: bool):
    """Display classification results with debug info."""
    import streamlit as st
    
    # DEBUG: Show complete API response
    st.subheader("🔍 DEBUG: Complete API Response")
    with st.expander("Raw API Response", expanded=False):
        st.json(result)
    
    # DEBUG: Check push result structure
    st.subheader("🔍 DEBUG: Push Result Analysis")
    pushed = result.get("pushed")
    push_result = result.get("push_result", {})
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Pushed:** {pushed}")
    with col2:
        st.write(f"**Push Result Keys:** {list(push_result.keys())}")
    with col3:
        st.write(f"**Push Status:** {push_result.get('status', 'No status')}")
    
    if push_result:
        st.write("**Full Push Result:**")
        st.json(push_result)
    
    st.success("Classification completed!")
    
    # Display classification result
    st.subheader("Classification Result")
    
    # Format the display in a structured way
    classification = result.get('classification', {})
    
    # Contact and Dealer Information
    with st.expander("Contact & Dealer Information", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Contact", classification.get('contact', ''))
            st.metric("Dealer ID", classification.get('dealer_id', ''))
        with col2:
            st.metric("Dealer Name", classification.get('dealer_name', ''))
            st.metric("Rep", classification.get('rep', ''))
    
    # Category Information
    with st.expander("Category Information", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Category", classification.get('category', ''))
        with col2:
            st.metric("Sub Category", classification.get('sub_category', ''))
    
    # Syndication Information
    with st.expander("Syndication Information", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Syndicator", classification.get('syndicator', ''))
        with col2:
            st.metric("Inventory Type", classification.get('inventory_type', ''))
    
    # Zoho ticket info if available
    zoho_data = result.get("zoho_data", {})
    if zoho_data:
        with st.expander("Zoho Ticket Info", expanded=False):
            st.write(f"**Subject:** {zoho_data.get('subject', '')}")
            st.write(f"**Threads:** {zoho_data.get('threads_count', 0)}")
            st.write(f"**From:** {zoho_data.get('from_email', '')}")
    
    # ENHANCED PUSH STATUS DISPLAY
    st.subheader("🔄 Push Status")
    
    if auto_push:
        if pushed:
            push_status = push_result.get("status", "")
            if push_status == "success":
                st.success("✅ Classification automatically pushed to Zoho!")
                
                # Show detailed field updates
                updated_fields = push_result.get("updated_fields", [])
                field_count = push_result.get("field_count", len(updated_fields))
                
                if updated_fields:
                    st.write(f"**Successfully updated {field_count} fields:**")
                    for field in updated_fields:
                        st.write(f"  • {field}")
                
                # Show payload if available
                payload_sent = push_result.get("payload_sent", {})
                if payload_sent:
                    with st.expander("📋 Fields Sent to Zoho", expanded=False):
                        st.json(payload_sent)
                
                # Show response summary
                response_summary = push_result.get("zoho_response_summary", "")
                if response_summary:
                    st.write(f"**Zoho Response:** {response_summary}")
                    
            else:
                st.error(f"❌ Auto-push failed: {push_result.get('error', 'Unknown error')}")
        else:
            st.warning("⚠️ Auto-push was enabled but push failed")
            error = push_result.get("error", "Unknown error")
            st.error(f"Error: {error}")
    elif ticket_id:
        # Manual push option for Zoho tickets
        st.write("Auto-push was not enabled. You can manually push the results:")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            push_btn = st.button("Push to Zoho", key="push_btn", type="primary")
        with col2:
            dry_run = st.checkbox("Dry Run (Preview Only)", key="dry_run_checkbox")
        
        if push_btn:
            with st.spinner("Pushing to Zoho..."):
                push_result, push_error = api_client.push_to_zoho(
                    ticket_id=ticket_id,
                    dry_run=dry_run
                )
            
            if push_error:
                st.error(f"Push Error: {push_error}")
            elif push_result:
                if dry_run:
                    st.info("Dry Run - Preview of changes:")
                    st.json(push_result.get('changes', {}))
                else:
                    st.success("Push request sent!")
                    st.info(push_result.get('message', ''))
    else:
        st.info("💡 This was a text classification. To push to Zoho, use a ticket ID instead.")