"""
Updated API client with Zoho integration support.
"""
import httpx
import streamlit as st
from typing import Dict, List, Optional, Tuple, Any


class EnhancedAPIClient:
    """Enhanced API client with Zoho integration."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=30)
    
    def health_check(self) -> bool:
        """Check if the API is healthy."""
        try:
            response = self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False
    
    def classify_ticket(
        self, 
        ticket_id: Optional[str] = None,
        ticket_text: Optional[str] = None, 
        ticket_subject: Optional[str] = None, 
        auto_push: bool = False
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Classify a ticket - supports both Zoho ID and direct text.
        
        Args:
            ticket_id: Zoho ticket ID (will fetch from Zoho automatically)
            ticket_text: Direct text input 
            ticket_subject: Subject line
            auto_push: Whether to push results back to Zoho
            
        Returns:
            Tuple of (result_data, error_message)
        """
        payload = {
            "auto_push": auto_push
        }
        
        if ticket_id:
            payload["ticket_id"] = ticket_id
        elif ticket_text:
            payload["ticket_text"] = ticket_text
            if ticket_subject:
                payload["ticket_subject"] = ticket_subject
        else:
            return None, "Either ticket_id or ticket_text must be provided"
        
        try:
            response = self.client.post(f"{self.base_url}/api/v1/classify", json=payload)
            
            if response.status_code == 200:
                return response.json(), None
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                return None, error_msg
                
        except Exception as e:
            return None, f"Request Error: {str(e)}"
    
    def get_ticket_info(self, ticket_id: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Get ticket information from Zoho.
        
        Args:
            ticket_id: Zoho ticket ID
            
        Returns:
            Tuple of (ticket_data, error_message)
        """
        try:
            response = self.client.get(f"{self.base_url}/api/v1/tickets/{ticket_id}")
            
            if response.status_code == 200:
                return response.json(), None
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                return None, error_msg
                
        except Exception as e:
            return None, f"Request Error: {str(e)}"
    
    def search_tickets(
        self, 
        status: Optional[str] = None,
        department_id: Optional[str] = None,
        limit: int = 20
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Search tickets in Zoho.
        
        Args:
            status: Filter by status
            department_id: Filter by department
            limit: Maximum number of tickets
            
        Returns:
            Tuple of (search_results, error_message)
        """
        params = {"limit": limit}
        if status:
            params["status"] = status
        if department_id:
            params["department_id"] = department_id
        
        try:
            response = self.client.get(f"{self.base_url}/api/v1/tickets", params=params)
            
            if response.status_code == 200:
                return response.json(), None
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                return None, error_msg
                
        except Exception as e:
            return None, f"Request Error: {str(e)}"
    
    def batch_classify(
        self, 
        ticket_ids: List[str], 
        auto_push: bool = False
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Classify multiple tickets by Zoho IDs.
        
        Args:
            ticket_ids: List of Zoho ticket IDs
            auto_push: Whether to push results back to Zoho
            
        Returns:
            Tuple of (batch_results, error_message)
        """
        payload = {
            "ticket_ids": ticket_ids,
            "auto_push": auto_push
        }
        
        try:
            response = self.client.post(f"{self.base_url}/api/v1/classify-batch", json=payload)
            
            if response.status_code == 200:
                return response.json(), None
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                return None, error_msg
                
        except Exception as e:
            return None, f"Request Error: {str(e)}"
    
    def push_to_zoho(
        self, 
        ticket_id: str,
        classification_id: Optional[int] = None, 
        dry_run: bool = False
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Push classification results to Zoho.
        
        Args:
            ticket_id: Zoho ticket ID
            classification_id: Optional classification ID from database
            dry_run: Preview changes without applying them
            
        Returns:
            Tuple of (push_result, error_message)
        """
        payload = {
            "ticket_id": ticket_id,
            "dry_run": dry_run
        }
        
        if classification_id:
            payload["classification_id"] = classification_id
        
        try:
            response = self.client.post(f"{self.base_url}/api/v1/push-classification", json=payload)
            
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


# Enhanced Classifier Page with Zoho Integration
def render_enhanced_classifier_page(api_client: EnhancedAPIClient):
    """Enhanced classifier page with Zoho integration."""
    st.title("🎯 Enhanced Ticket Classifier")
    st.markdown("Classify tickets from Zoho Desk or direct text input with auto-push capability.")
    
    # Create tabs for different input methods
    tab1, tab2, tab3 = st.tabs(["Zoho Ticket ID", "Direct Text", "Ticket Search"])
    
    with tab1:
        render_zoho_ticket_tab(api_client)
    
    with tab2:
        render_direct_text_tab(api_client)
    
    with tab3:
        render_ticket_search_tab(api_client)


def render_zoho_ticket_tab(api_client: EnhancedAPIClient):
    """Render the Zoho ticket ID classification tab."""
    st.subheader("Classify by Zoho Ticket ID")
    st.markdown("Enter a Zoho ticket ID to automatically fetch and classify the ticket.")
    
    # Input fields
    ticket_id = st.text_input(
        "Zoho Ticket ID", 
        key="zoho_ticket_id_input",
        placeholder="e.g., 319204000303289257",
        help="Enter the Zoho Desk ticket ID"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        auto_push = st.checkbox(
            "Auto-push to Zoho", 
            value=False, 
            key="zoho_auto_push_checkbox",
            help="Automatically update custom fields in Zoho after classification"
        )
    
    with col2:
        preview_ticket = st.checkbox(
            "Preview ticket first",
            value=False,
            key="preview_ticket_checkbox",
            help="Show ticket details before classification"
        )
    
    # Preview ticket if requested
    if preview_ticket and ticket_id:
        if st.button("Preview Ticket", key="preview_ticket_btn"):
            with st.spinner("Fetching ticket..."):
                ticket_info, error = api_client.get_ticket_info(ticket_id)
            
            if error:
                st.error(f"Error fetching ticket: {error}")
            elif ticket_info:
                ticket_data = ticket_info.get("ticket", {})
                threads = ticket_info.get("threads", [])
                
                st.subheader("Ticket Preview")
                
                # Show ticket details
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**ID:** {ticket_data.get('id')}")
                    st.write(f"**Status:** {ticket_data.get('status')}")
                    st.write(f"**Category:** {ticket_data.get('category')}")
                
                with col2:
                    st.write(f"**Ticket #:** {ticket_data.get('ticket_number')}")
                    st.write(f"**Priority:** {ticket_data.get('priority')}")
                    st.write(f"**Threads:** {len(threads)}")
                
                st.write(f"**Subject:** {ticket_data.get('subject')}")
                
                if ticket_data.get('description'):
                    st.write(f"**Description:** {ticket_data.get('description')[:200]}...")
                
                # Show existing custom fields
                custom_fields = ticket_data.get('custom_fields', {})
                if custom_fields:
                    relevant_fields = {k: v for k, v in custom_fields.items() 
                                     if v and any(word in k.lower() for word in ['syndic', 'inventory', 'oem'])}
                    if relevant_fields:
                        st.write("**Existing Custom Fields:**")
                        for key, value in relevant_fields.items():
                            st.write(f"  - {key}: {value}")
                
                # Show recent threads
                if threads:
                    st.write("**Recent Conversation:**")
                    for i, thread in enumerate(threads[:2]):
                        st.write(f"**Thread {i+1}** ({thread.get('author_name')}):")
                        st.write(f"  {thread.get('summary', '')[:150]}...")
    
    # Classify button
    col1, col2 = st.columns([1, 5])
    with col1:
        classify_btn = st.button("Classify Ticket", key="classify_zoho_btn", type="primary")
    
    if classify_btn and ticket_id:
        with st.spinner("Fetching and classifying ticket..."):
            result, error = api_client.classify_ticket(ticket_id=ticket_id, auto_push=auto_push)
        
        if error:
            st.error(f"Error: {error}")
        elif result:
            display_zoho_classification_result(result, api_client, auto_push)


def render_direct_text_tab(api_client: EnhancedAPIClient):
    """Render the direct text classification tab."""
    st.subheader("Classify Direct Text")
    st.markdown("Enter ticket text directly for classification.")
    
    # Input fields
    subject = st.text_input("Subject (optional)", key="direct_subject_input")
    ticket_text = st.text_area(
        "Ticket Text", 
        height=300, 
        key="direct_ticket_text_input",
        placeholder="Enter the ticket content here..."
    )
    
    # Classify button
    col1, col2 = st.columns([1, 5])
    with col1:
        classify_text_btn = st.button("Classify Text", key="classify_direct_btn", type="primary")
    
    if classify_text_btn and ticket_text:
        with st.spinner("Classifying..."):
            result, error = api_client.classify_ticket(
                ticket_text=ticket_text,
                ticket_subject=subject,
                auto_push=False  # Can't auto-push direct text
            )
        
        if error:
            st.error(f"Error: {error}")
        elif result:
            display_direct_classification_result(result)


def render_ticket_search_tab(api_client: EnhancedAPIClient):
    """Render the ticket search tab."""
    st.subheader("Search and Classify Tickets")
    st.markdown("Search for tickets in Zoho and classify them.")
    
    # Search filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Status",
            ["All", "Open", "In Progress", "Closed"],
            key="search_status_filter"
        )
    
    with col2:
        limit = st.slider("Max Results", 5, 50, 20, key="search_limit")
    
    with col3:
        search_btn = st.button("Search Tickets", key="search_tickets_btn", type="secondary")
    
    if search_btn:
        status = None if status_filter == "All" else status_filter
        
        with st.spinner("Searching tickets..."):
            search_result, error = api_client.search_tickets(status=status, limit=limit)
        
        if error:
            st.error(f"Search error: {error}")
        elif search_result:
            tickets = search_result.get("tickets", [])
            
            if tickets:
                st.success(f"Found {len(tickets)} tickets")
                
                # Display tickets in a table format
                ticket_data = []
                for ticket in tickets:
                    ticket_data.append({
                        "ID": ticket.get("id"),
                        "Subject": ticket.get("subject", "")[:50] + "...",
                        "Status": ticket.get("status"),
                        "Created": ticket.get("created_time", "")[:10] if ticket.get("created_time") else "",
                        "Select": False
                    })
                
                # Create editable dataframe for selection
                df = st.data_editor(
                    ticket_data,
                    column_config={
                        "Select": st.column_config.CheckboxColumn("Select"),
                        "ID": st.column_config.TextColumn("Ticket ID", width=150),
                        "Subject": st.column_config.TextColumn("Subject", width=300),
                        "Status": st.column_config.TextColumn("Status", width=100),
                        "Created": st.column_config.TextColumn("Created", width=100)
                    },
                    use_container_width=True,
                    key="tickets_selection"
                )
                
                # Get selected tickets
                selected_tickets = [row["ID"] for row in df.to_dict("records") if row["Select"]]
                
                if selected_tickets:
                    st.write(f"Selected {len(selected_tickets)} tickets")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        auto_push_batch = st.checkbox(
                            "Auto-push to Zoho",
                            value=False,
                            key="search_auto_push_checkbox"
                        )
                    
                    with col2:
                        classify_selected_btn = st.button(
                            f"Classify Selected ({len(selected_tickets)})",
                            key="classify_selected_btn",
                            type="primary"
                        )
                    
                    if classify_selected_btn:
                        with st.spinner(f"Classifying {len(selected_tickets)} tickets..."):
                            batch_result, batch_error = api_client.batch_classify(
                                ticket_ids=selected_tickets,
                                auto_push=auto_push_batch
                            )
                        
                        if batch_error:
                            st.error(f"Batch classification error: {batch_error}")
                        elif batch_result:
                            display_batch_classification_result(batch_result)
            else:
                st.info("No tickets found matching the search criteria")


def display_zoho_classification_result(result: Dict, api_client: EnhancedAPIClient, auto_push: bool):
    """Display classification result from Zoho ticket."""
    classification = result.get("classification", {})
    zoho_data = result.get("zoho_data", {})
    
    st.success("Classification completed!")
    
    # Show Zoho ticket info
    with st.expander("📋 Zoho Ticket Information", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Ticket ID", result.get("ticket_id"))
            st.metric("Status", zoho_data.get("status"))
            st.metric("Threads", zoho_data.get("threads_count"))
        
        with col2:
            st.metric("Ticket #", zoho_data.get("ticket_number"))
            if zoho_data.get("web_url"):
                st.markdown(f"[View in Zoho]({zoho_data['web_url']})")
        
        st.write(f"**Subject:** {zoho_data.get('subject')}")
    
    # Show classification results
    with st.expander("🎯 Classification Results", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Contact", classification.get("contact", ""))
            st.metric("Dealer Name", classification.get("dealer_name", ""))
            st.metric("Dealer ID", classification.get("dealer_id", ""))
            st.metric("Rep", classification.get("rep", ""))
        
        with col2:
            st.metric("Category", classification.get("category", ""))
            st.metric("Sub Category", classification.get("sub_category", ""))
            st.metric("Syndicator", classification.get("syndicator", ""))
            st.metric("Inventory Type", classification.get("inventory_type", ""))
    
    # Show existing vs new values comparison
    existing_syndicator = zoho_data.get("existing_syndicator")
    existing_inventory = zoho_data.get("existing_inventory_type")
    
    if existing_syndicator or existing_inventory:
        with st.expander("🔄 Comparison with Existing Data", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Field**")
                st.write("Syndicator")
                st.write("Inventory Type")
            
            with col2:
                st.write("**Existing**")
                st.write(existing_syndicator or "None")
                st.write(existing_inventory or "None")
            
            with col3:
                st.write("**New**")
                st.write(classification.get("syndicator", "") or "None")
                st.write(classification.get("inventory_type", "") or "None")
    
    # Push status
    if auto_push:
        if result.get("pushed"):
            st.success("✅ Classification automatically pushed to Zoho!")
        else:
            st.error("❌ Auto-push failed")
            if result.get("push_result", {}).get("error"):
                st.error(f"Error: {result['push_result']['error']}")
    else:
        # Manual push option
        col1, col2 = st.columns([1, 3])
        with col1:
            push_btn = st.button("Push to Zoho", key="manual_push_btn", type="primary")
        with col2:
            dry_run = st.checkbox("Dry Run (Preview Only)", key="manual_dry_run")
        
        if push_btn:
            with st.spinner("Pushing to Zoho..."):
                push_result, push_error = api_client.push_to_zoho(
                    ticket_id=result["ticket_id"],
                    dry_run=dry_run
                )
            
            if push_error:
                st.error(f"Push failed: {push_error}")
            elif push_result:
                if dry_run:
                    st.info("Dry run completed - preview of changes:")
                    st.json(push_result)
                else:
                    st.success("Successfully pushed to Zoho!")


def display_direct_classification_result(result: Dict):
    """Display classification result from direct text."""
    classification = result.get("classification", {})
    
    st.success("Classification completed!")
    
    # Show classification results
    with st.expander("🎯 Classification Results", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Contact", classification.get("contact", ""))
            st.metric("Dealer Name", classification.get("dealer_name", ""))
            st.metric("Dealer ID", classification.get("dealer_id", ""))
            st.metric("Rep", classification.get("rep", ""))
        
        with col2:
            st.metric("Category", classification.get("category", ""))
            st.metric("Sub Category", classification.get("sub_category", ""))
            st.metric("Syndicator", classification.get("syndicator", ""))
            st.metric("Inventory Type", classification.get("inventory_type", ""))
    
    st.info("💡 To push this classification to Zoho, use the Zoho Ticket ID method instead.")


def display_batch_classification_result(result: Dict):
    """Display batch classification results."""
    successful = result.get("ok", 0)
    failed = result.get("err", 0)
    results = result.get("results", [])
    
    st.success(f"Batch classification completed: {successful} successful, {failed} failed")
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Processed", successful + failed)
    with col2:
        st.metric("Successful", successful)
    with col3:
        st.metric("Failed", failed)
    
    # Detailed results
    if results:
        st.subheader("Detailed Results")
        
        # Convert to DataFrame for display
        results_data = []
        for r in results:
            classification = r.get("classification", {})
            results_data.append({
                "Ticket ID": r.get("ticket_id"),
                "Status": r.get("status"),
                "Dealer Name": classification.get("dealer_name", ""),
                "Category": classification.get("category", ""),
                "Syndicator": classification.get("syndicator", ""),
                "Pushed": "✅" if r.get("pushed") else "❌",
                "Error": r.get("error", "")
            })
        
        df = pd.DataFrame(results_data)
        st.dataframe(df, use_container_width=True)
        
        # Download option
        csv = df.to_csv(index=False)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            "📥 Download Results",
            data=csv,
            file_name=f"batch_classification_{timestamp}.csv",
            mime="text/csv"
        )


# Example usage in main.py
def get_enhanced_api_client():
    """Get enhanced API client with Zoho integration."""
    api_url = os.getenv("API_URL", "http://localhost:8088")
    return EnhancedAPIClient(api_url)


# Usage in main.py:
# Replace the existing APIClient with EnhancedAPIClient
# Replace render_classifier_page with render_enhanced_classifier_page