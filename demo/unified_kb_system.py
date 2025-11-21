"""
Unified KB System - Single Entry Point for All Interfaces
Combines Agent, Browser, Builder, and Audit interfaces
"""

import streamlit as st
import sys
from pathlib import Path

# Set page config ONCE for entire app
st.set_page_config(
    page_title="Intelligent KB System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #1f77b4;
    }
    .nav-section {
        padding: 1rem;
        background-color: #f0f2f6;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .stRadio > label {
        font-size: 1.1rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state"""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Agent Interface"


def render_sidebar():
    """Render sidebar navigation"""
    with st.sidebar:
        st.markdown("## 🧠 KB System")
        st.markdown("---")

        # Demo Mode Toggle (prominent placement)
        st.markdown("### 🎬 Presentation Mode")
        demo_mode = st.toggle(
            "Enable Demo Mode",
            value=st.session_state.get('demo_mode', False),
            help="Simplifies the interface for cleaner demos and presentations. Hides technical details and sentiment analysis.",
            key="demo_mode_toggle"
        )

        # Store in session state
        st.session_state.demo_mode = demo_mode

        if demo_mode:
            st.info("📊 Demo Mode Active - Simplified view enabled")

        st.markdown("---")

        # Navigation
        page = st.radio(
            "Navigate to:",
            [
                "🎯 Agent Interface",
                "📚 KB Browser",
                "✏️  KB Builder",
                "🔍 Audit Dashboard",
                "📊 Gap Analysis"
            ],
            key="page_selector"
        )

        st.markdown("---")

        # Quick Info
        st.markdown("### Quick Info")
        st.caption("**Agent Interface**: Resolve tickets with KB suggestions")
        st.caption("**KB Browser**: Search and explore KB articles")
        st.caption("**KB Builder**: Chat with AI to manage KB articles")
        st.caption("**Audit Dashboard**: Review and approve feedback")
        st.caption("**Gap Analysis**: Identify knowledge gaps and search patterns")

        return page


def run_agent_interface():
    """Run the Agent/Ticket Resolution interface"""
    import demo_app
    demo_app.main()


def run_kb_browser():
    """Run the KB Browser interface"""
    import kb_browser
    kb_browser.main()


def run_kb_builder():
    """Run the KB Agent Chat interface"""
    import kb_agent_chat
    kb_agent_chat.main()


def run_audit_dashboard():
    """Run the Audit Dashboard interface"""
    import kb_audit_dashboard
    kb_audit_dashboard.main()


def run_gap_analysis():
    """Run the Gap Analysis Dashboard"""
    import gap_analysis_dashboard
    gap_analysis_dashboard.main()


def main():
    """Main application entry point"""
    init_session_state()

    # Render sidebar navigation
    selected_page = render_sidebar()

    # Route to appropriate interface based on selection
    if "Agent" in selected_page:
        run_agent_interface()

    elif "Browser" in selected_page:
        run_kb_browser()

    elif "Builder" in selected_page:
        run_kb_builder()

    elif "Audit" in selected_page:
        run_audit_dashboard()
    
    elif "Gap Analysis" in selected_page or "Gap" in selected_page:
        run_gap_analysis()


if __name__ == "__main__":
    main()
