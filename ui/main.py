"""
Updated main Streamlit application with Zoho integration.
"""
import os
import sys
import time
from datetime import datetime
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Add pages directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'pages'))

# Import page modules and enhanced API client
from pages.management import render_management_page
from pages.analytics import render_analytics_page
from pages.settings import render_settings_page
from pages.advanced_features import render as render_advanced_features

# Import our enhanced API client
from api_client_updated import EnhancedAPIClient, render_classifier_page

# Load environment variables
load_dotenv()

# Configuration
from config import API_URL
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Page configuration
st.set_page_config(
    page_title="Automotive Ticket Classifier",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Enhanced CSS with Zoho integration styling
st.markdown(
    """
    <style>
        .main {
            max-width: 1200px;
            padding: 1rem;
        }
        .stButton>button {
            margin-top: 1rem;
        }
        .sidebar .sidebar-content {
            background-color: #f8f9fa;
        }
        .css-1d391kg {
            padding-top: 3.5rem;
        }
        .classification-success {
            background-color: #d4edda;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .classification-error {
            background-color: #f8d7da;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .push-success {
            background-color: #cce5ff;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .push-error {
            background-color: #f8d7da;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .dataframe-container {
            overflow-x: auto;
            margin-top: 1rem;
        }
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        .zoho-integration {
            border-left: 4px solid #1f77b4;
            padding-left: 1rem;
            margin: 1rem 0;
        }
        .ticket-preview {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Session state initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = ENVIRONMENT == "development"
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "api_health" not in st.session_state:
    st.session_state.api_health = False
if "last_health_check" not in st.session_state:
    st.session_state.last_health_check = 0
if "current_page" not in st.session_state:
    st.session_state.current_page = "Classifier"
if "zoho_status" not in st.session_state:
    st.session_state.zoho_status = "Unknown"

def check_api_health():
    """Check if the API is healthy."""
    now = time.time()
    # Only check every 30 seconds
    if now - st.session_state.last_health_check < 30:
        return st.session_state.api_health
    
    try:
        api_client = EnhancedAPIClient(API_URL)
        st.session_state.api_health = api_client.health_check()
        
        # Also check if we can get a sample ticket (indicates Zoho is working)
        if st.session_state.api_health:
            try:
                # Try to search for one ticket to test Zoho connectivity
                search_result, _ = api_client.search_tickets(limit=1)
                st.session_state.zoho_status = "Connected" if search_result else "API Only"
            except:
                st.session_state.zoho_status = "API Only"
        else:
            st.session_state.zoho_status = "Disconnected"
            
    except Exception:
        st.session_state.api_health = False
        st.session_state.zoho_status = "Disconnected"
    
    st.session_state.last_health_check = now
    return st.session_state.api_health

def render_sidebar():
    """Render the enhanced sidebar navigation."""
    st.sidebar.title("🎯 Ticket Classifier")
    
    # API and Zoho status indicators
    api_status = check_api_health()
    api_color = "green" if api_status else "red"
    api_text = "Connected" if api_status else "Disconnected"
    
    # Zoho status color
    zoho_color = {
        "Connected": "green",
        "API Only": "orange", 
        "Disconnected": "red",
        "Unknown": "gray"
    }.get(st.session_state.zoho_status, "gray")
    
    st.sidebar.markdown(
        f"""
        <div style='margin-bottom: 1rem;'>
            <div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
                <div style='width: 10px; height: 10px; border-radius: 50%; background-color: {api_color}; margin-right: 10px;'></div>
                <div style='font-size: 0.9rem;'>API {api_text}</div>
            </div>
            <div style='display: flex; align-items: center;'>
                <div style='width: 10px; height: 10px; border-radius: 50%; background-color: {zoho_color}; margin-right: 10px;'></div>
                <div style='font-size: 0.9rem;'>Zoho {st.session_state.zoho_status}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Feature highlights
    if st.session_state.zoho_status == "Connected":
        st.sidebar.success("🚀 Zoho Integration Active!")
    elif st.session_state.zoho_status == "API Only":
        st.sidebar.warning("⚠️ API Only (No Zoho)")
    else:
        st.sidebar.error("❌ Services Offline")
    
    # Navigation
    st.sidebar.markdown("## Navigation")
    
    pages = [
        ("Classifier", "🎯", "Classify tickets from Zoho or text"),
        ("Ticket Management", "📋", "Batch operations and search"),
        ("Advanced Features", "🚀", "Bulk processing and system tools"),
        ("Analytics", "📊", "Performance metrics and trends"),
        ("Settings", "⚙️", "Configuration and preferences")
    ]
    
    for page_name, icon, description in pages:
        is_current = st.session_state.current_page == page_name
        button_type = "primary" if is_current else "secondary"
        
        if st.sidebar.button(
            f"{icon} {page_name}",
            key=f"nav_{page_name}",
            use_container_width=True,
            help=description,
            type=button_type,
        ):
            st.session_state.current_page = page_name
            st.rerun()
    
    # Quick stats (if API is available)
    if api_status:
        st.sidebar.markdown("## Quick Stats")
        try:
            api_client = EnhancedAPIClient(API_URL)
            metrics, _ = api_client.get_metrics()
            if metrics:
                uptime_hours = metrics.get('uptime', 0) / 3600
                st.sidebar.metric("Uptime", f"{uptime_hours:.1f} hrs")
                st.sidebar.metric("Processed", metrics.get('processed', 0))
                st.sidebar.metric("Success Rate", f"{metrics.get('success_rate', 0):.1f}%")
        except:
            st.sidebar.metric("Uptime", "N/A")
            st.sidebar.metric("Processed", "N/A")
            st.sidebar.metric("Success Rate", "N/A")
    
    # Environment and debug info
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Environment:** {ENVIRONMENT.capitalize()}")
    
    if ENVIRONMENT != "production":
        st.sidebar.markdown(f"**Debug Mode:** {'On' if DEBUG else 'Off'}")
    
    # Zoho Integration info
    if st.session_state.zoho_status == "Connected":
        st.sidebar.markdown("### 🔗 Zoho Features")
        st.sidebar.markdown("""
        - ✅ Fetch tickets by ID
        - ✅ Auto-push classifications  
        - ✅ Search tickets
        - ✅ Batch processing
        """)
    
    # Authentication information
    if st.session_state.authenticated and st.session_state.user_info:
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**Logged in as:** {st.session_state.user_info.get('name', 'User')}")
        if st.sidebar.button("Logout", key="logout"):
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.rerun()

def main():
    """Main application function."""
    # Initialize enhanced API client
    api_client = EnhancedAPIClient(API_URL)
    
    # Render sidebar
    render_sidebar()
    
    # Render the current page
    try:
        if st.session_state.current_page == "Classifier":
            render_classifier_page(api_client)
        elif st.session_state.current_page == "Ticket Management":
            render_management_page(api_client)
        elif st.session_state.current_page == "Advanced Features":
            render_advanced_features()
        elif st.session_state.current_page == "Analytics":
            render_analytics_page(api_client)
        elif st.session_state.current_page == "Settings":
            render_settings_page(api_client)
        else:
            st.error(f"Unknown page: {st.session_state.current_page}")
            st.session_state.current_page = "Classifier"
            st.rerun()
    except Exception as e:
        st.error(f"Error rendering page: {str(e)}")
        if DEBUG:
            st.exception(e)

if __name__ == "__main__":
    main()