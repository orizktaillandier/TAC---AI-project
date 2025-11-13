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

        # Navigation
        page = st.radio(
            "Navigate to:",
            [
                "🎯 Agent Interface",
                "📚 KB Browser",
                "✏️  KB Builder",
                "🔍 Audit Dashboard"
            ],
            key="page_selector"
        )

        st.markdown("---")

        # Quick Info
        st.markdown("### Quick Info")
        st.caption("**Agent Interface**: Resolve tickets with KB suggestions")
        st.caption("**KB Browser**: Search and explore KB articles")
        st.caption("**KB Builder**: Create new KB articles manually")
        st.caption("**Audit Dashboard**: Review and approve feedback")

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
    """Run the KB Builder interface"""
    import kb_builder_app

    # kb_builder_app doesn't have a main() function, so we need to execute it differently
    # For now, let's import and let it run
    st.markdown('<div class="main-header">✏️ KB Builder</div>', unsafe_allow_html=True)
    st.info("KB Builder interface - Run `streamlit run kb_builder_app.py --server.port 8505` for the full builder interface.")

    # TODO: Extract kb_builder_app content into a callable function


def run_audit_dashboard():
    """Run the Audit Dashboard interface"""
    import kb_audit_dashboard
    kb_audit_dashboard.main()


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


if __name__ == "__main__":
    main()
