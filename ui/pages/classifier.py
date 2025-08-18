"""
Classifier page for the Streamlit UI.
"""
import streamlit as st
import httpx
from typing import Dict, Any, Optional


def render_classifier_page(api_client):
    """
    Render the classifier page.
    
    Args:
        api_client: API client instance
    """
    st.title("🎯 Ticket Classifier")
    st.markdown(
        """
        Classify tickets by ID or by entering ticket text directly.
        """
    )
    
    # Input section
    st.subheader("Input")
    
    # Tabs for different input methods
    tab1, tab2 = st.tabs(["Classify by Ticket ID", "Classify by Text"])
    
    with tab1:
        _render_ticket_id_tab(api_client)
    
    with tab2:
        _render_text_tab(api_client)


def _render_ticket_id_tab(api_client):
    """Render the ticket ID classification tab."""
    ticket_id = st.text_input("Enter Ticket ID", key="ticket_id_input")
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


def _render_text_tab(api_client):
    """Render the text classification tab."""
    subject = st.text_input("Subject (optional)", key="subject_input")
    ticket_text = st.text_area("Ticket Text", height=300, key="ticket_text_input")
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


def _display_classification_result(result: Dict[str, Any], api_client, ticket_id: Optional[str], auto_push: bool):
    """
    Display the classification result.
    
    Args:
        result: Classification result
        api_client: API client instance
        ticket_id: Ticket ID (if available)
        auto_push: Whether auto-push was enabled
    """
    st.success("Classification successful!")
    
    # Display classification result
    st.subheader("Classification Result")
    
    # Format the display in a structured way
    classification = result.get('classification', {})
    
    # Contact and Dealer Information
    with st.expander("📞 Contact & Dealer Information", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Contact", classification.get('contact', ''))
            st.metric("Dealer ID", classification.get('dealer_id', ''))
        with col2:
            st.metric("Dealer Name", classification.get('dealer_name', ''))
            st.metric("Rep", classification.get('rep', ''))
    
    # Category Information
    with st.expander("📋 Category Information", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Category", classification.get('category', ''))
        with col2:
            st.metric("Sub Category", classification.get('sub_category', ''))
    
    # Syndication Information
    with st.expander("🔗 Syndication Information", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Syndicator", classification.get('syndicator', ''))
        with col2:
            st.metric("Inventory Type", classification.get('inventory_type', ''))
    
    # Push to Zoho section
    if not auto_push and ticket_id:
        st.subheader("Push to Zoho")
        
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
                    st.success("Push successful!")
                    if push_result.get('changes'):
                        st.json(push_result.get('changes', {}))
    elif auto_push:
        if result.get("pushed"):
            st.success("✅ Classification pushed to Zoho successfully!")
        else:
            st.warning("⚠️ Auto-push was enabled but push failed")
    
    # Raw classification data (collapsible)
    with st.expander("🔍 Raw Classification Data", expanded=False):
        st.json(result)


def _format_field_display(label: str, value: str) -> None:
    """
    Format and display a field with consistent styling.
    
    Args:
        label: Field label
        value: Field value
    """
    if value:
        st.markdown(f"**{label}:** {value}")
    else:
        st.markdown(f"**{label}:** *Not specified*")
