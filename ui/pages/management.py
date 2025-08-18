"""
Ticket management page for the Streamlit UI.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
import io


def render_management_page(api_client):
    """
    Render the ticket management page.
    
    Args:
        api_client: API client instance
    """
    st.title("📋 Ticket Management")
    st.markdown(
        """
        Manage and classify tickets in batch mode.
        """
    )
    
    # Create tabs for different management functions
    tab1, tab2, tab3 = st.tabs(["Batch Classification", "Ticket Search", "Export Data"])
    
    with tab1:
        _render_batch_classification(api_client)
    
    with tab2:
        _render_ticket_search(api_client)
    
    with tab3:
        _render_export_data(api_client)


def _render_batch_classification(api_client):
    """Render the batch classification section."""
    st.subheader("Batch Classification")
    st.markdown("Classify multiple tickets at once.")
    
    # Input methods
    input_method = st.radio(
        "Choose input method:",
        ["Manual Entry", "File Upload"],
        key="batch_input_method"
    )
    
    ticket_ids = []
    
    if input_method == "Manual Entry":
        batch_input = st.text_area(
            "Enter Ticket IDs (one per line)",
            height=150,
            key="batch_input",
            help="Enter one ticket ID per line",
        )
        ticket_ids = [tid.strip() for tid in batch_input.split("\n") if tid.strip()]
    
    elif input_method == "File Upload":
        uploaded_file = st.file_uploader(
            "Upload CSV file with ticket IDs",
            type=['csv'],
            key="batch_upload"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                # Try to find ticket ID column
                possible_columns = ['ticket_id', 'id', 'ticketId', 'Ticket ID', 'ID']
                ticket_column = None
                
                for col in possible_columns:
                    if col in df.columns:
                        ticket_column = col
                        break
                
                if ticket_column:
                    ticket_ids = df[ticket_column].dropna().astype(str).tolist()
                    st.success(f"Found {len(ticket_ids)} ticket IDs in column '{ticket_column}'")
                else:
                    st.error(f"Could not find ticket ID column. Available columns: {list(df.columns)}")
                    ticket_column = st.selectbox("Select ticket ID column:", df.columns)
                    if ticket_column:
                        ticket_ids = df[ticket_column].dropna().astype(str).tolist()
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    # Batch options
    col1, col2 = st.columns(2)
    with col1:
        auto_push_batch = st.checkbox("Auto-push to Zoho", value=False, key="auto_push_batch_checkbox")
    with col2:
        max_concurrent = st.slider("Max concurrent requests", 1, 10, 3, key="max_concurrent")
    
    # Display ticket count
    if ticket_ids:
        st.info(f"Ready to process {len(ticket_ids)} tickets")
        
        # Show sample of ticket IDs
        if len(ticket_ids) > 5:
            st.write("Sample ticket IDs:", ticket_ids[:5] + ["..."])
        else:
            st.write("Ticket IDs:", ticket_ids)
    
    # Process button
    col1, col2 = st.columns([1, 5])
    with col1:
        process_btn = st.button("Process Batch", key="batch_btn", type="primary", disabled=not ticket_ids)
    
    if process_btn and ticket_ids:
        _process_batch_classification(api_client, ticket_ids, auto_push_batch)


def _process_batch_classification(api_client, ticket_ids: List[str], auto_push: bool):
    """
    Process batch classification.
    
    Args:
        api_client: API client instance
        ticket_ids: List of ticket IDs
        auto_push: Whether to auto-push to Zoho
    """
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    with st.spinner(f"Processing {len(ticket_ids)} tickets..."):
        result, error = api_client.batch_classify(ticket_ids=ticket_ids, auto_push=auto_push)
    
    progress_bar.progress(1.0)
    
    if error:
        st.error(f"Batch processing failed: {error}")
        return
    
    if not result:
        st.error("No result received from batch processing")
        return
    
    # Display summary
    st.success(f"Batch processing completed: {result['ok']} successful, {result['err']} failed")
    
    # Convert results to DataFrame
    results_df = _convert_batch_results_to_dataframe(result["results"])
    
    if not results_df.empty:
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Processed", len(results_df))
        with col2:
            successful = len(results_df[results_df['Status'] == 'success'])
            st.metric("Successful", successful)
        with col3:
            failed = len(results_df[results_df['Status'] == 'error'])
            st.metric("Failed", failed)
        with col4:
            if auto_push:
                pushed = len(results_df[results_df['Pushed'] == True])
                st.metric("Pushed to Zoho", pushed)
        
        # Display results table
        st.subheader("Results")
        
        # Add filters
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox("Filter by status:", ["All", "success", "error"], key="status_filter")
        with col2:
            if auto_push:
                push_filter = st.selectbox("Filter by push status:", ["All", "Pushed", "Not Pushed"], key="push_filter")
        
        # Apply filters
        filtered_df = results_df.copy()
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df['Status'] == status_filter]
        if auto_push and 'push_filter' in locals() and push_filter != "All":
            if push_filter == "Pushed":
                filtered_df = filtered_df[filtered_df['Pushed'] == True]
            else:
                filtered_df = filtered_df[filtered_df['Pushed'] == False]
        
        # Display filtered results
        st.dataframe(filtered_df, use_container_width=True)
        
        # Export options
        _render_export_options(filtered_df, "batch_results")


def _convert_batch_results_to_dataframe(results: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert batch results to DataFrame.
    
    Args:
        results: List of result dictionaries
        
    Returns:
        DataFrame with results
    """
    rows = []
    for r in results:
        classification = r.get("classification") or {}
        row = {
            "Ticket ID": r["ticket_id"],
            "Status": r["status"],
            "Contact": classification.get("contact", ""),
            "Dealer Name": classification.get("dealer_name", ""),
            "Dealer ID": classification.get("dealer_id", ""),
            "Rep": classification.get("rep", ""),
            "Category": classification.get("category", ""),
            "Sub Category": classification.get("sub_category", ""),
            "Syndicator": classification.get("syndicator", ""),
            "Inventory Type": classification.get("inventory_type", ""),
            "Pushed": r.get("pushed", False),
            "Updated Fields": ", ".join(r.get("updated", [])),
            "Errors": ", ".join(r.get("errors", [])),
        }
        rows.append(row)
    
    return pd.DataFrame(rows)


def _render_ticket_search(api_client):
    """Render the ticket search section."""
    st.subheader("Ticket Search")
    st.markdown("Search and view tickets from Zoho Desk.")
    
    # Search filters
    col1, col2 = st.columns(2)
    with col1:
        search_term = st.text_input("Search term", key="search_term")
        status = st.selectbox("Status", ["All", "Open", "Pending", "Resolved", "Closed"], key="ticket_status")
    
    with col2:
        priority = st.selectbox("Priority", ["All", "Low", "Medium", "High", "Urgent"], key="ticket_priority")
        limit = st.slider("Max results", 10, 100, 50, key="search_limit")
    
    search_btn = st.button("Search Tickets", key="search_btn")
    
    if search_btn:
        with st.spinner("Searching tickets..."):
            # Note: This would need to be implemented in the API client
            st.info("Ticket search functionality would be implemented here")
            # tickets, error = api_client.search_tickets(
            #     search_term=search_term,
            #     status=status if status != "All" else None,
            #     priority=priority if priority != "All" else None,
            #     limit=limit
            # )


def _render_export_data(api_client):
    """Render the export data section."""
    st.subheader("Export Data")
    st.markdown("Export classification data and reports.")
    
    # Export options
    export_type = st.selectbox(
        "What would you like to export?",
        ["Recent Classifications", "All Classifications", "Custom Date Range"],
        key="export_type"
    )
    
    if export_type == "Custom Date Range":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", key="export_start_date")
        with col2:
            end_date = st.date_input("End Date", key="export_end_date")
    
    # Export format
    export_format = st.selectbox(
        "Export format",
        ["Excel (.xlsx)", "CSV (.csv)", "JSON (.json)"],
        key="export_format"
    )
    
    export_btn = st.button("Export Data", key="export_btn")
    
    if export_btn:
        with st.spinner("Preparing export..."):
            st.info("Export functionality would be implemented here")
            # This would integrate with the API to get classification data


def _render_export_options(df: pd.DataFrame, filename_prefix: str):
    """
    Render export options for a DataFrame.
    
    Args:
        df: DataFrame to export
        filename_prefix: Prefix for the filename
    """
    if df.empty:
        return
    
    st.subheader("Export Results")
    
    col1, col2, col3 = st.columns(3)
    
    # Excel export
    with col1:
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.xlsx"
        
        st.download_button(
            "📊 Download Excel",
            data=excel_buffer.getvalue(),
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    
    # CSV export
    with col2:
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.csv"
        
        st.download_button(
            "📄 Download CSV",
            data=csv_buffer.getvalue(),
            file_name=filename,
            mime="text/csv",
        )
    
    # JSON export
    with col3:
        json_data = df.to_json(orient='records', indent=2)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.json"
        
        st.download_button(
            "🔗 Download JSON",
            data=json_data,
            file_name=filename,
            mime="application/json",
        )
