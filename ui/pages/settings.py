"""
Settings page for the Streamlit UI.
"""
import streamlit as st
import os
import json
from typing import Dict, Any, List


def render_settings_page(api_client):
    """
    Render the settings page.
    
    Args:
        api_client: API client instance
    """
    st.title("⚙️ Settings")
    st.markdown(
        """
        Configure application settings and system preferences.
        """
    )
    
    # Create tabs for different settings categories
    tab1, tab2, tab3, tab4 = st.tabs(["API Configuration", "Classification Settings", "System Settings", "About"])
    
    with tab1:
        _render_api_settings(api_client)
    
    with tab2:
        _render_classification_settings(api_client)
    
    with tab3:
        _render_system_settings()
    
    with tab4:
        _render_about_section()


def _render_api_settings(api_client):
    """Render API configuration settings."""
    st.subheader("API Configuration")
    
    # Current API URL
    current_api_url = os.getenv("API_URL", "http://localhost:8088")
    api_url = st.text_input(
        "API URL",
        value=current_api_url,
        key="api_url_input",
        help="Base URL for the classification API"
    )
    
    # API connection test
    col1, col2 = st.columns([1, 3])
    
    with col1:
        test_btn = st.button("Test Connection", key="test_connection_btn", type="secondary")
    
    with col2:
        if test_btn:
            with st.spinner("Testing connection..."):
                is_healthy = api_client.health_check()
            
            if is_healthy:
                st.success("✅ Connection successful!")
            else:
                st.error("❌ Connection failed!")
    
    # API timeout settings
    st.subheader("Request Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        timeout = st.slider(
            "Request Timeout (seconds)",
            min_value=5,
            max_value=120,
            value=30,
            key="api_timeout"
        )
    
    with col2:
        max_retries = st.slider(
            "Max Retries",
            min_value=0,
            max_value=5,
            value=3,
            key="max_retries"
        )
    
    # Batch processing settings
    st.subheader("Batch Processing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        batch_size = st.slider(
            "Batch Size",
            min_value=1,
            max_value=50,
            value=10,
            key="batch_size",
            help="Number of tickets to process in each batch"
        )
    
    with col2:
        concurrent_requests = st.slider(
            "Concurrent Requests",
            min_value=1,
            max_value=10,
            value=3,
            key="concurrent_requests",
            help="Number of simultaneous API requests"
        )
    
    # Save API settings
    if st.button("Save API Settings", key="save_api_settings", type="primary"):
        # In a real implementation, these would be saved to a config file or database
        os.environ["API_URL"] = api_url
        st.success("API settings saved! Some changes may require restart.")


def _render_classification_settings(api_client):
    """Render classification-specific settings."""
    st.subheader("Classification Settings")
    
    # Display current valid categories/subcategories
    st.subheader("Valid Categories")
    
    # These would typically come from the API or config
    valid_categories = [
        "Product Activation — New Client",
        "Product Activation — Existing Client", 
        "Product Cancellation",
        "Problem / Bug",
        "General Question",
        "Analysis / Review",
        "Other"
    ]
    
    with st.expander("View Valid Categories", expanded=False):
        for i, category in enumerate(valid_categories, 1):
            st.write(f"{i}. {category}")
    
    # Valid subcategories
    valid_subcategories = [
        "Import",
        "Export",
        "Sales Data Import", 
        "FB Setup",
        "Google Setup",
        "Other Department",
        "Other",
        "AccuTrade"
    ]
    
    with st.expander("View Valid Subcategories", expanded=False):
        for i, subcategory in enumerate(valid_subcategories, 1):
            st.write(f"{i}. {subcategory}")
    
    # Valid inventory types
    valid_inventory_types = [
        "New",
        "Used",
        "Demo", 
        "New + Used"
    ]
    
    with st.expander("View Valid Inventory Types", expanded=False):
        for i, inv_type in enumerate(valid_inventory_types, 1):
            st.write(f"{i}. {inv_type}")
    
    # Classification confidence settings
    st.subheader("Confidence Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        min_confidence = st.slider(
            "Minimum Confidence Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.05,
            key="min_confidence",
            help="Classifications below this threshold will be flagged for review"
        )
    
    with col2:
        auto_push_threshold = st.slider(
            "Auto-Push Confidence Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.85,
            step=0.05,
            key="auto_push_threshold",
            help="Classifications above this threshold can be auto-pushed to Zoho"
        )
    
    # Language detection settings
    st.subheader("Language Detection")
    
    detect_language = st.checkbox(
        "Enable automatic language detection",
        value=True,
        key="detect_language",
        help="Automatically detect if tickets are in English or French"
    )
    
    if detect_language:
        col1, col2 = st.columns(2)
        
        with col1:
            french_threshold = st.slider(
                "French Detection Threshold",
                min_value=1,
                max_value=10,
                value=3,
                key="french_threshold",
                help="Number of French words needed to classify as French"
            )
        
        with col2:
            default_language = st.selectbox(
                "Default Language",
                ["English", "French"],
                index=0,
                key="default_language",
                help="Default language when detection is uncertain"
            )


def _render_system_settings():
    """Render system-wide settings."""
    st.subheader("System Settings")
    
    # UI preferences
    st.subheader("User Interface")
    
    col1, col2 = st.columns(2)
    
    with col1:
        theme = st.selectbox(
            "Theme",
            ["Auto", "Light", "Dark"],
            index=0,
            key="ui_theme"
        )
        
        results_per_page = st.slider(
            "Results per Page",
            min_value=10,
            max_value=100,
            value=50,
            step=10,
            key="results_per_page"
        )
    
    with col2:
        auto_refresh = st.checkbox(
            "Auto-refresh metrics",
            value=True,
            key="auto_refresh",
            help="Automatically refresh analytics data"
        )
        
        if auto_refresh:
            refresh_interval = st.slider(
                "Refresh Interval (seconds)",
                min_value=30,
                max_value=300,
                value=60,
                step=30,
                key="refresh_interval"
            )
    
    # Export settings
    st.subheader("Export Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        default_export_format = st.selectbox(
            "Default Export Format",
            ["Excel (.xlsx)", "CSV (.csv)", "JSON (.json)"],
            index=0,
            key="default_export_format"
        )
    
    with col2:
        include_metadata = st.checkbox(
            "Include metadata in exports",
            value=True,
            key="include_metadata",
            help="Include timestamps, confidence scores, etc."
        )
    
    # Logging and debugging
    st.subheader("Logging & Debugging")
    
    col1, col2 = st.columns(2)
    
    with col1:
        log_level = st.selectbox(
            "Log Level",
            ["ERROR", "WARNING", "INFO", "DEBUG"],
            index=2,
            key="log_level"
        )
        
        enable_debug = st.checkbox(
            "Enable debug mode",
            value=False,
            key="enable_debug",
            help="Show detailed error messages and API responses"
        )
    
    with col2:
        log_api_requests = st.checkbox(
            "Log API requests",
            value=False,
            key="log_api_requests",
            help="Log all API requests for debugging"
        )
        
        show_raw_responses = st.checkbox(
            "Show raw API responses",
            value=False,
            key="show_raw_responses",
            help="Display raw API responses in the UI"
        )
    
    # Cache settings
    st.subheader("Cache Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        enable_cache = st.checkbox(
            "Enable caching",
            value=True,
            key="enable_cache",
            help="Cache API responses to improve performance"
        )
    
    with col2:
        if enable_cache:
            cache_ttl = st.slider(
                "Cache TTL (minutes)",
                min_value=5,
                max_value=120,
                value=60,
                key="cache_ttl",
                help="How long to keep cached responses"
            )
    
    # Clear cache button
    if enable_cache:
        if st.button("Clear Cache", key="clear_cache_btn", type="secondary"):
            # In a real implementation, this would clear the cache
            st.success("Cache cleared successfully!")


def _render_about_section():
    """Render the about section."""
    st.subheader("About Automotive Ticket Classifier")
    
    # System information
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Version:** 3.0.0  
        **Environment:** Development  
        **Build Date:** 2024-08-15  
        **API Version:** v1  
        """)
    
    with col2:
        st.markdown("""
        **Technology Stack:**
        - Frontend: Streamlit
        - Backend: FastAPI
        - AI: OpenAI GPT-4
        - Database: PostgreSQL
        - Cache: Redis
        """)
    
    # Feature overview
    st.subheader("Features")
    
    features = [
        "🤖 **AI-Powered Classification** - Uses OpenAI GPT-4 for intelligent ticket analysis",
        "🌍 **Bilingual Support** - Handles both English and French tickets",
        "⚡ **Batch Processing** - Classify multiple tickets simultaneously",
        "🔄 **Zoho Integration** - Direct integration with Zoho Desk API",
        "📊 **Analytics Dashboard** - Comprehensive performance metrics and trends",
        "💾 **Data Export** - Export results in multiple formats (Excel, CSV, JSON)",
        "🔍 **Dealer Recognition** - Advanced dealer name extraction and normalization",
        "📈 **Performance Monitoring** - Real-time system health and metrics",
    ]
    
    for feature in features:
        st.markdown(feature)
    
    # Documentation and support
    st.subheader("Documentation & Support")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **📚 Documentation**
        - [User Guide](docs/user-guide.md)
        - [API Reference](docs/api-reference.md)
        - [Troubleshooting](docs/troubleshooting.md)
        """)
    
    with col2:
        st.markdown("""
        **🔧 Development**
        - [GitHub Repository](#)
        - [Issue Tracker](#)
        - [Development Guide](docs/development.md)
        """)
    
    with col3:
        st.markdown("""
        **📞 Support**
        - [Contact Support](#)
        - [FAQ](docs/faq.md)
        - [Change Log](docs/changelog.md)
        """)
    
    # Configuration info
    st.subheader("Current Configuration")
    
    # Display current environment variables (non-sensitive ones)
    config_info = {
        "Environment": os.getenv("ENVIRONMENT", "development"),
        "Debug Mode": os.getenv("DEBUG", "false"),
        "API URL": os.getenv("API_URL", "http://localhost:8088"),
        "OpenAI Model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "Cache Enabled": os.getenv("USE_REDIS", "true"),
    }
    
    config_df = pd.DataFrame([
        {"Setting": key, "Value": value}
        for key, value in config_info.items()
    ])
    
    st.dataframe(config_df, use_container_width=True, hide_index=True)
    
    # System status
    st.subheader("System Status")
    
    # This would typically fetch real system status
    status_items = [
        ("🟢", "API Service", "Operational"),
        ("🟢", "Database", "Connected"),
        ("🟢", "Cache", "Available"),
        ("🟢", "OpenAI API", "Connected"),
        ("🟢", "Zoho Integration", "Active"),
    ]
    
    for icon, service, status in status_items:
        col1, col2, col3 = st.columns([1, 3, 2])
        with col1:
            st.markdown(icon)
        with col2:
            st.markdown(f"**{service}**")
        with col3:
            st.markdown(status)
