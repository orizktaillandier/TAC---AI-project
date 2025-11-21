"""
AI-Powered Ticket Classifier
Simple classification demo - no extra features
"""
import streamlit as st
import json
import os
import time
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from classifier import TicketClassifier, load_mock_tickets
from knowledge_base import KnowledgeBase
from kb_intelligence import KBIntelligence
from feedback_manager import FeedbackManager
from step_automation import StepAutomation

load_dotenv()


def render_automated_step(step_data: dict, step_num: int):
    """Render a step with action buttons if applicable - Clean simple design"""
    step_text = step_data.get("step_text", "")
    automation = step_data.get("automation", {})
    
    # Only show action buttons, not data displays
    if automation.get("can_automate") and automation.get("automation_type") == "action":
        action_type = automation.get("action_type")
        action_params = automation.get("action_params", {})
        display_format = automation.get("display_format")
        
        if display_format == "action_button":
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**{step_num}.** {step_text}")
                
                with col2:
                    # Execute action button
                    button_key = f"action_{step_num}_{action_type}_{action_params.get('feed_name', '')}"
                    
                    if action_type == "enable_feed":
                        if st.button("✅ Enable Feed", key=button_key, use_container_width=True, type="primary"):
                            execute_action(action_type, action_params, step_num)
                    
                    elif action_type == "disable_feed":
                        if st.button("❌ Disable Feed", key=button_key, use_container_width=True, type="primary"):
                            execute_action(action_type, action_params, step_num)
                    
                    elif action_type in ["add_new_export", "add_new_import"]:
                        if st.button("➕ Add New Feed", key=button_key, use_container_width=True, type="primary"):
                            execute_action(action_type, action_params, step_num)
                    
                    elif action_type == "copy_feed_id":
                        if st.button("📋 Copy Feed ID", key=button_key, use_container_width=True, type="primary"):
                            execute_action(action_type, action_params, step_num)
                    
                    elif action_type == "force_refresh":
                        if st.button("🔄 Force Refresh", key=button_key, use_container_width=True, type="primary"):
                            execute_action(action_type, action_params, step_num)
                    
                    elif action_type == "download_feed_file":
                        if st.button("📥 Download Feed File", key=button_key, use_container_width=True, type="primary"):
                            execute_action(action_type, action_params, step_num)
                    
                    elif action_type == "save_settings":
                        if st.button("💾 Save Settings", key=button_key, use_container_width=True, type="primary"):
                            execute_action(action_type, action_params, step_num)
                    
                    elif action_type == "add_new_client":
                        if st.button("➕ Add New Client", key=button_key, use_container_width=True, type="primary"):
                            execute_action(action_type, action_params, step_num)
                    
                    elif action_type == "select_syndicator":
                        if st.button("📋 Select Syndicator", key=button_key, use_container_width=True, type="primary"):
                            execute_action(action_type, action_params, step_num)
                    
                    elif action_type == "confirm_action":
                        if st.button("✅ Confirm Action", key=button_key, use_container_width=True, type="primary"):
                            execute_action(action_type, action_params, step_num)
            return
    
    # Regular step without action button
    st.markdown(f"**{step_num}.** {step_text}")


def execute_action(action_type: str, action_params: dict, step_num: int):
    """Execute an action via Admin Dashboard"""
    from step_automation import StepAutomation
    dashboard = StepAutomation().dashboard
    
    dealer_name = action_params.get("dealer_name", "")
    feed_name = action_params.get("feed_name", "")
    feed_type = action_params.get("feed_type", "export")
    
    result = None
    
    if action_type == "enable_feed":
        result = dashboard.enable_feed(dealer_name, feed_name, feed_type)
    elif action_type == "disable_feed":
        result = dashboard.disable_feed(dealer_name, feed_name, feed_type)
    elif action_type == "add_new_export":
        result = dashboard.add_new_export(dealer_name, feed_name)
    elif action_type == "add_new_import":
        result = dashboard.add_new_export(dealer_name, feed_name)  # Same method for now
    elif action_type == "copy_feed_id":
        feed_id = dashboard.get_feed_id(dealer_name, feed_name, feed_type)
        if feed_id:
            # Display Feed ID prominently for copying
            st.success(f"✅ Feed ID: **{feed_id}**")
            st.code(feed_id, language=None)  # Display in code block for easy copying
            st.info("💡 Click the code block above to select and copy the Feed ID")
        else:
            st.warning("⚠️ Feed ID not found. Feed may not exist yet.")
        return
    elif action_type == "force_refresh":
        result = dashboard.force_refresh_feed(dealer_name, feed_name, feed_type)
    elif action_type == "download_feed_file":
        result = dashboard.download_feed_file(dealer_name, feed_name, feed_type)
    elif action_type == "save_settings":
        result = dashboard.save_settings(dealer_name, feed_name, feed_type)
    elif action_type == "add_new_client":
        result = dashboard.add_new_client(dealer_name)
    elif action_type == "select_syndicator":
        feed_name = action_params.get("feed_name", "")
        result = dashboard.select_syndicator(dealer_name, feed_name)
    elif action_type == "confirm_action":
        result = dashboard.confirm_action(dealer_name)
    
    if result:
        if result.get("success"):
            st.success(f"✅ {result.get('message', 'Action completed successfully')}")
            
            # Show Feed ID if available
            if result.get("feed_id"):
                st.info(f"📋 Feed ID: **{result['feed_id']}**")
            
            # Show download file info
            if result.get("file_name"):
                file_name = result.get("file_name")
                file_size = result.get("file_size", 0)
                file_size_kb = file_size / 1024
                
                st.info(f"📥 **File:** {file_name} ({file_size_kb:.1f} KB)")
                st.code(result.get("content_preview", ""), language="xml")
                st.caption("💡 File is ready for download/review")
            
            st.rerun()  # Refresh to show updated data
        else:
            st.error(f"❌ {result.get('message', 'Action failed')}")


def display_client_configuration(dealer_name: str):
    """Display client configuration summary"""
    if not dealer_name:
        st.info("No dealer name available")
        return
    
    from step_automation import StepAutomation
    dashboard = StepAutomation().dashboard
    config = dashboard.get_client_configuration(dealer_name)
    
    if not config.get("dealer_found"):
        st.warning(f"⚠️ Configuration not found for {dealer_name}")
        return
    
    # Display in a clean card format
    st.markdown('<div class="zoho-card-compact">', unsafe_allow_html=True)
    
    st.markdown(f"**{config.get('dealer_name', dealer_name)}**")
    st.caption(f"ID: {config.get('dealer_id', 'N/A')} | Status: {config.get('account_status', 'N/A')}")
    
    st.markdown("---")
    
    # Active Exports
    active_exports = config.get("active_exports", [])
    if active_exports:
        st.markdown("**📤 Active Exports:**")
        for export in active_exports:
            st.markdown(f"• {export}")
    else:
        st.markdown("**📤 Active Exports:**")
        st.caption("None")
    
    st.markdown("")
    
    # Active Imports
    active_imports = config.get("active_imports", [])
    if active_imports:
        st.markdown("**📥 Active Imports:**")
        for import_feed in active_imports:
            st.markdown(f"• {import_feed}")
    else:
        st.markdown("**📥 Active Imports:**")
        st.caption("None")
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_resolution_steps_with_automation(steps: list, ticket_context: dict):
    """Render resolution steps with action buttons where applicable - Clean simple layout"""
    step_automation = StepAutomation()
    processed_steps = step_automation.process_steps(steps, ticket_context)
    
    # Count actionable steps (with buttons)
    actionable_count = sum(1 for s in processed_steps if s["automation"].get("automation_type") == "action")
    
    # Show brief info if there are actionable steps
    if actionable_count > 0:
        st.caption(f"💡 {actionable_count} step(s) can be executed directly via buttons")
    
    # Render steps in a clean container with reduced spacing
    with st.container():
        for i, step_data in enumerate(processed_steps, 1):
            render_automated_step(step_data, i)
            # Reduced spacing - only small gap between steps
            if i < len(processed_steps):
                st.markdown("<br>", unsafe_allow_html=True)  # Minimal spacing


# Page config (with safe handling for unified app import)
try:
    st.set_page_config(
        page_title="AI Ticket Classifier",
        page_icon="🎯",
        layout="wide"
    )
except:
    # Already configured by unified app
    pass


def main():
    """Main function for the demo app"""
    # Custom CSS - Clean professional styling
    st.markdown("""
    <style>
        /* Professional color palette */
        :root {
            --primary-orange: #FF6B35;
            --primary-blue: #4A90E2;
            --accent-green: #2ECC71;
            --dark-bg: #1E293B;
            --card-bg: #334155;
            --border-color: #475569;
        }

        /* Main layout - dark background */
        .main {
            background-color: #1E293B;
            padding: 1rem;
        }

        /* Light text on dark background */
        .main p, .main span, .main div, .main label {
            color: #E2E8F0 !important;
        }

        .main h1, .main h2, .main h3, .main h4, .main h5, .main h6 {
            color: #F1F5F9 !important;
        }

        /* Clean header */
        .app-header {
            background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
            color: white;
            padding: 1.2rem 2rem;
            margin: -1rem -1rem 1.5rem -1rem;
            border-bottom: 2px solid #2E5F8E;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .app-header h1 {
            margin: 0;
            font-size: 1.6rem;
            font-weight: 600;
        }

        .app-header p {
            margin: 0.4rem 0 0 0;
            opacity: 0.95;
            font-size: 0.9rem;
        }

        /* Professional cards - dark theme */
        .zoho-card {
            background: #334155;
            border: 1px solid #475569;
            border-radius: 6px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }

        .zoho-card-compact {
            background: #334155;
            border: 1px solid #475569;
            border-radius: 6px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }

        .zoho-card-header {
            font-size: 1.1rem;
            font-weight: 600;
            color: #F1F5F9;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid #4A90E2;
        }

        .info-group {
            background: #475569;
            padding: 0.75rem;
            border-radius: 4px;
            margin-bottom: 0.75rem;
        }

        .info-group-title {
            font-size: 0.75rem;
            font-weight: 600;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }

        .info-value {
            font-size: 0.95rem;
            color: #E2E8F0;
            font-weight: 500;
        }

        /* Ticket status badges */
        .ticket-badge {
            display: inline-block;
            padding: 0.35rem 0.9rem;
            border-radius: 16px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-right: 0.5rem;
        }

        .badge-open {
            background-color: #E3F2FD;
            color: #1976D2;
            border: 1px solid #90CAF9;
        }

        .badge-pending {
            background-color: #FFF9E6;
            color: #F57F17;
            border: 1px solid #FFD54F;
        }

        .badge-urgent {
            background-color: #FFEBEE;
            color: #C62828;
            border: 1px solid #EF5350;
        }

        .badge-resolved {
            background-color: #E8F5E9;
            color: #2E7D32;
            border: 1px solid #66BB6A;
        }

        /* Professional buttons */
        .stButton>button {
            background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
            color: white;
            border: none;
            border-radius: 6px;
            padding: 0.7rem 1.5rem;
            font-weight: 600;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(74, 144, 226, 0.3);
        }

        .stButton>button:hover {
            background: linear-gradient(135deg, #357ABD 0%, #2E5F8E 100%);
            box-shadow: 0 3px 6px rgba(74, 144, 226, 0.4);
            transform: translateY(-1px);
        }

        /* Ticket card buttons - special styling */
        button[kind="secondary"] {
            background: #334155 !important;
            color: #E2E8F0 !important;
            border: 1px solid #475569 !important;
            border-left: 3px solid #4A90E2 !important;
            text-align: left !important;
            padding: 0.75rem 1rem !important;
            font-weight: 500 !important;
        }

        button[kind="secondary"]:hover {
            background: #3B4A5F !important;
            border-left: 3px solid #60A5FA !important;
            transform: translateX(2px);
        }

        /* Metrics styling - dark theme, compact */
        div[data-testid="stMetricValue"] {
            color: #60A5FA;
            font-weight: 600;
            font-size: 1.1rem !important;
        }

        div[data-testid="stMetricLabel"] {
            color: #94A3B8 !important;
            font-size: 0.75rem !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        div[data-testid="stMetric"] {
            background: #475569;
            padding: 0.75rem;
            border-radius: 4px;
            border-left: 3px solid #4A90E2;
        }

        /* Field labels */
        .zoho-field-label {
            color: #94A3B8;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }

        /* Professional sidebar - dark theme */
        section[data-testid="stSidebar"] {
            background-color: #0F172A;
            border-right: 1px solid #475569;
        }

        section[data-testid="stSidebar"] > div {
            background-color: #0F172A;
        }

        /* Sidebar text visibility */
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] div,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: #E2E8F0 !important;
        }

        /* Success/warning/error styling */
        .stSuccess {
            background-color: #E8F5E9;
            border-left: 4px solid #2ECC71;
        }

        .stWarning {
            background-color: #FFF9E6;
            border-left: 4px solid #F59E0B;
        }

        .stError {
            background-color: #FFEBEE;
            border-left: 4px solid #EF4444;
        }

        /* Ticket info grid */
        .ticket-info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }

        .ticket-info-item {
            background: #475569;
            padding: 1rem;
            border-radius: 6px;
            border-left: 3px solid #4A90E2;
            color: #E2E8F0;
        }

        /* Streamlit specific text fixes - dark theme */
        .stMarkdown, .stText {
            color: #E2E8F0 !important;
        }

        /* Input fields - dark theme */
        input, textarea, select {
            background-color: #334155 !important;
            color: #E2E8F0 !important;
            border: 1px solid #475569 !important;
        }

        /* Expander content */
        .streamlit-expanderContent {
            color: #E2E8F0 !important;
            background-color: #334155 !important;
        }

        /* Radio and checkbox labels */
        .stRadio label, .stCheckbox label {
            color: #E2E8F0 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Initialize session state
    if "classifier" not in st.session_state:
        try:
            st.session_state.classifier = TicketClassifier()
            st.session_state.classifier_ready = True
        except Exception as e:
            st.session_state.classifier_ready = False
            st.session_state.classifier_error = str(e)

    if "kb" not in st.session_state:
        try:
            st.session_state.kb = KnowledgeBase()
            st.session_state.kb_ready = True
        except Exception as e:
            st.session_state.kb_ready = False
            st.session_state.kb_error = str(e)

    if "kb_intelligence" not in st.session_state:
        try:
            st.session_state.kb_intelligence = KBIntelligence()
            st.session_state.kb_intelligence_ready = True
        except Exception as e:
            st.session_state.kb_intelligence_ready = False
            st.session_state.kb_intelligence_error = str(e)

    if "feedback_manager" not in st.session_state:
        try:
            st.session_state.feedback_manager = FeedbackManager()
            st.session_state.feedback_manager_ready = True
        except Exception as e:
            st.session_state.feedback_manager_ready = False
            st.session_state.feedback_manager_error = str(e)

    if "mock_tickets" not in st.session_state:
        st.session_state.mock_tickets = load_mock_tickets()

    # Initialize feedback state
    if "show_feedback" not in st.session_state:
        st.session_state.show_feedback = False
    if "current_resolution" not in st.session_state:
        st.session_state.current_resolution = None
    if "current_ticket_data" not in st.session_state:
        st.session_state.current_ticket_data = None
    if "kb_results_cache" not in st.session_state:
        st.session_state.kb_results_cache = None

    # Professional Header
    demo_mode = st.session_state.get('demo_mode', False)
    header_subtitle = "🎬 DEMO MODE - Simplified View" if demo_mode else "Intelligent ticket classification and resolution powered by GPT-5"

    st.markdown(f"""
    <div class="app-header">
        <h1>🎯 Support Desk - AI Assistant</h1>
        <p>{header_subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

    # Check if classifier is ready
    if not st.session_state.classifier_ready:
        st.error(f"⚠️ Classifier not ready: {st.session_state.get('classifier_error', 'Unknown error')}")
        st.info("💡 Make sure your `.env` file has `OPENAI_API_KEY` set")
        st.stop()

    # Sidebar
    with st.sidebar:
        st.header("📊 Info")

        st.markdown("### What gets extracted:")
        st.markdown("""
        1. **Contact Name**
        2. **Dealer Name**
        3. **Dealer ID**
        4. **Rep Name**
        5. **Category**
        6. **Sub-Category**
        7. **Syndicator/Provider**
        8. **Inventory Type**
        9. **Tier** (1-3)
        """)

        st.markdown("---")
        st.markdown("### Sample Tickets")
        st.markdown(f"{len(st.session_state.mock_tickets)} available")

        # KB Health Monitoring
        st.markdown("---")
        st.markdown("### 📈 KB Health")
        try:
            from kb_health_monitor import get_health_monitor
            health_monitor = get_health_monitor()
            critical_alerts = health_monitor.get_critical_alerts()

            if critical_alerts:
                st.error(f"⚠️ {len(critical_alerts)} Critical Issues")
                for alert in critical_alerts:
                    severity = alert.get("severity", "Unknown")
                    message = alert.get("message", "")
                    if severity == "Critical":
                        st.error(f"🔴 {message}")
                    elif severity == "High":
                        st.warning(f"🟠 {message}")
            else:
                # Get overall health
                health_report = health_monitor.get_health_report()
                overall_health = health_report.get("overall_health", "Unknown")
                success_rate = health_report["metrics"].get("overall_success_rate", 0)

                if overall_health == "Good":
                    st.success(f"✅ {overall_health}")
                elif overall_health == "Fair":
                    st.info(f"ℹ️ {overall_health}")
                else:
                    st.warning(f"⚠️ {overall_health}")

                st.metric("Success Rate", f"{success_rate:.0%}")

                # Show health details in expander
                with st.expander("View Details"):
                    metrics = health_report.get("metrics", {})
                    st.caption(f"Total Usage: {metrics.get('total_usage', 0)}")
                    st.caption(f"Low Performers: {len(metrics.get('low_performing_articles', []))}")
                    st.caption(f"High Performers: {len(metrics.get('high_performing_articles', []))}")

                    if health_report.get("recommendations"):
                        st.markdown("**Recommendations:**")
                        for rec in health_report["recommendations"][:3]:
                            st.caption(f"• {rec}")
        except Exception as e:
            # Silently fail if health monitoring has issues
            pass

    # Main content - Clean header
    st.markdown("---")

    # Proactive Pattern Detection Alerts
    try:
        from pattern_monitor import get_pattern_monitor
        pattern_monitor = get_pattern_monitor()
        active_alerts = pattern_monitor.get_active_alerts()

        if active_alerts:
            # Show critical alerts as banners
            for alert in active_alerts[:3]:  # Show top 3 alerts
                severity = alert.get("severity", "Low")
                message = alert.get("message", "")
                ticket_count = alert.get("ticket_count", 0)

                if severity == "Critical":
                    st.error(f"🚨 **CRITICAL PATTERN DETECTED:** {message} ({ticket_count} tickets affected)")
                elif severity == "High":
                    st.warning(f"⚠️ **HIGH PRIORITY:** {message} ({ticket_count} tickets affected)")
                elif severity == "Medium":
                    st.info(f"ℹ️ **Pattern Detected:** {message} ({ticket_count} tickets)")

            # Show detailed pattern info in expander
            if len(active_alerts) > 0:
                with st.expander(f"🔍 View All Pattern Details ({len(active_alerts)} patterns detected)"):
                    for alert in active_alerts:
                        st.markdown(f"**Type:** {alert.get('type', 'Unknown')}")
                        st.markdown(f"**Severity:** {alert.get('severity', 'Unknown')}")
                        st.markdown(f"**Affected Tickets:** {alert.get('ticket_count', 0)}")
                        st.markdown(f"**Recommendation:** {alert.get('recommendation', 'No recommendation')}")
                        st.markdown("---")

            st.markdown("---")
    except Exception as e:
        # Silently fail if pattern detection has issues
        pass

    # ========== TOP ROW: Ticket Selection (1/3) + Classification Fields (2/3) ==========
    col_tickets, col_classification = st.columns([1, 2])
    
    with col_tickets:
        st.markdown("### 📋 Sample Tickets")
        if st.session_state.mock_tickets:
            # Create dropdown options
            ticket_options = [
                f"#{ticket['ticket_id']}: {ticket['subject'][:60]}{'...' if len(ticket['subject']) > 60 else ''}"
                for ticket in st.session_state.mock_tickets
            ]
            
            # Get current selection index
            current_idx = st.session_state.get('selected_ticket_idx', 0)
            if current_idx >= len(ticket_options):
                current_idx = 0
            
            # Dropdown selector
            selected_option = st.selectbox(
                "Select a ticket",
                options=range(len(ticket_options)),
                format_func=lambda x: ticket_options[x],
                index=current_idx,
                key="ticket_selector"
            )
            
            # Update session state if selection changed
            if selected_option != current_idx:
                st.session_state.selected_ticket_idx = selected_option
                st.rerun()
        else:
            st.warning("No sample tickets available")
    
    with col_classification:
        # Show selected ticket details and classification
        if 'selected_ticket_idx' in st.session_state and st.session_state.selected_ticket_idx is not None:
            ticket = st.session_state.mock_tickets[st.session_state.selected_ticket_idx]
            ticket_subject = ticket["subject"]
            ticket_text = ticket["description"]
            
            st.markdown("### 📄 Selected Ticket")
            st.markdown('<div class="zoho-card-compact">', unsafe_allow_html=True)
            st.markdown(f'<span class="ticket-badge badge-open">#{ticket["ticket_id"]}</span>', unsafe_allow_html=True)
            st.markdown(f"**Subject:** {ticket_subject}")
            st.markdown(f"**Description:** {ticket_text[:200]}{'...' if len(ticket_text) > 200 else ''}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            classify_button = st.button("🚀 Analyze Ticket", type="primary", use_container_width=True)
        else:
            st.info("👈 Select a ticket from the left to begin")
            ticket_subject = ""
            ticket_text = ""
            classify_button = False

    # Classification logic
    if classify_button:
        if not ticket_text.strip():
            st.error("Please enter ticket content")
        else:
            with st.spinner("Classifying ticket..."):
                result = st.session_state.classifier.classify(ticket_text, ticket_subject)

                if result.get("success"):
                    classification = result["classification"]
                    entities = result.get("entities", {})
                    suggested_response = result.get("suggested_response", "")

                    # Store classification in session state
                    st.session_state.current_classification = classification
                    st.session_state.current_ticket_text = ticket_text
                    st.session_state.current_ticket_subject = ticket_subject
                    
                    # Display classification results in the right column
                    st.markdown("### 🎯 Classification Results")
                    st.markdown('<div class="zoho-card-compact">', unsafe_allow_html=True)
                    
                    # Main Classification Fields
                    st.markdown("**📋 Classification**")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Category", classification.get("category", "N/A") or "N/A")
                        st.metric("Sub-Category", classification.get("sub_category", "N/A") or "N/A")
                    with col2:
                        st.metric("Tier", classification.get("tier", "N/A") or "N/A")
                        st.metric("Inventory Type", classification.get("inventory_type", "N/A") or "N/A")
                    
                    st.markdown("---")
                    
                    # Contact & Dealer Information - More Visible
                    st.markdown("### 👤 Contact & Dealer")
                    col1, col2 = st.columns(2)
                    with col1:
                        dealer_name = classification.get('dealer_name', '') or 'N/A'
                        dealer_id = classification.get('dealer_id', '') or 'N/A'
                        st.markdown(f"**Dealer Name:** {dealer_name}")
                        st.markdown(f"**Dealer ID:** {dealer_id}")
                    with col2:
                        contact = classification.get('contact', '') or classification.get('contact_name', '') or 'N/A'
                        rep = classification.get('rep', '') or classification.get('rep_name', '') or 'N/A'
                        st.markdown(f"**Contact:** {contact}")
                        st.markdown(f"**Rep:** {rep}")
                    
                    st.markdown("---")
                    
                    # Integrations - More Visible
                    st.markdown("### 🔗 Integrations")
                    syndicator = classification.get('syndicator', '') or 'N/A'
                    provider = classification.get('provider', '') or 'N/A'
                    if syndicator != 'N/A' and syndicator:
                        st.markdown(f"**Syndicator:** {syndicator}")
                    if provider != 'N/A' and provider:
                        st.markdown(f"**Provider:** {provider}")
                    if (not syndicator or syndicator == 'N/A') and (not provider or provider == 'N/A'):
                        st.markdown("*No integrations specified*")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Trigger KB search automatically after classification
                    st.session_state.auto_search_kb = True
                    st.session_state.current_classification = classification
                    st.session_state.current_ticket_text = ticket_text
                    st.session_state.current_ticket_subject = ticket_subject
                    st.rerun()

    # Auto-trigger KB search after classification
    if st.session_state.get('auto_search_kb') and st.session_state.get('current_classification'):
        classification = st.session_state.current_classification
        ticket_text = st.session_state.current_ticket_text
        ticket_subject = st.session_state.current_ticket_subject
        st.session_state.auto_search_kb = False  # Reset flag
        
        # Display classification results above resolution steps
        st.markdown("---")
        st.markdown("### 🎯 Classification Results")
        st.markdown('<div class="zoho-card-compact">', unsafe_allow_html=True)
        
        # Main Classification Fields
        st.markdown("**📋 Classification**")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Category", classification.get("category", "N/A") or "N/A")
            st.metric("Sub-Category", classification.get("sub_category", "N/A") or "N/A")
        with col2:
            st.metric("Tier", classification.get("tier", "N/A") or "N/A")
            st.metric("Inventory Type", classification.get("inventory_type", "N/A") or "N/A")
        
        st.markdown("---")
        
        # Contact & Dealer Information - More Visible
        st.markdown("### 👤 Contact & Dealer")
        col1, col2 = st.columns(2)
        with col1:
            dealer_name = classification.get('dealer_name', '') or 'N/A'
            dealer_id = classification.get('dealer_id', '') or 'N/A'
            st.markdown(f"**Dealer Name:** {dealer_name}")
            st.markdown(f"**Dealer ID:** {dealer_id}")
        with col2:
            contact = classification.get('contact', '') or classification.get('contact_name', '') or 'N/A'
            rep = classification.get('rep', '') or classification.get('rep_name', '') or 'N/A'
            st.markdown(f"**Contact:** {contact}")
            st.markdown(f"**Rep:** {rep}")
        
        st.markdown("---")
        
        # Integrations - More Visible
        st.markdown("### 🔗 Integrations")
        syndicator = classification.get('syndicator', '') or 'N/A'
        provider = classification.get('provider', '') or 'N/A'
        if syndicator != 'N/A' and syndicator:
            st.markdown(f"**Syndicator:** {syndicator}")
        if provider != 'N/A' and provider:
            st.markdown(f"**Provider:** {provider}")
        if (not syndicator or syndicator == 'N/A') and (not provider or provider == 'N/A'):
            st.markdown("*No integrations specified*")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ========== BOTTOM ROW: Resolution Steps (1/2) + Dealership Config (1/2) ==========
        st.markdown("---")
        st.markdown("### 📚 Knowledge Base Resolution")
        
        if st.session_state.kb_ready:
            with st.spinner("Searching Knowledge Base for relevant solutions..."):
                # Search KB using classification
                kb_results = st.session_state.kb.search_articles(
                    query=ticket_text,
                    classification=classification
                )

                if kb_results:
                    # Use AI to analyze and select best article
                    with st.spinner("AI is analyzing the best solution..."):
                        try:
                            # Prepare context for AI
                            top_articles = kb_results[:3]
                            articles_context = "\n\n".join([
                                f"Article {i+1} (Confidence: {art['confidence']}%):\n"
                                f"Title: {art['article'].get('title')}\n"
                                f"Problem: {art['article'].get('problem')}\n"
                                f"Solution: {art['article'].get('solution')}\n"
                                f"Steps: {json.dumps(art['article'].get('steps', []))}"
                                for i, art in enumerate(top_articles)
                            ])

                            # AI prompt to select and adapt solution
                            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                            ai_prompt = f"""You are a support agent AI assistant. Select the KB article and adapt its steps to this specific ticket.

Ticket:
- Category: {classification.get('category')}
- Dealer: {classification.get('dealer_name')}
- Syndicator: {classification.get('syndicator')}
- Provider: {classification.get('provider')}

Content: {ticket_text}

KB Articles:
{articles_context}

CRITICAL INSTRUCTIONS:
1. Select the best matching KB article
2. USE THE KB ARTICLE'S STEPS AS-IS, only replace placeholders with actual values from the ticket
3. DO NOT add edge cases unless the ticket explicitly mentions a complication
4. DO NOT add warnings about credentials, access, or obvious things
5. Keep it simple - trust the KB steps

Return JSON:
{{
  "selected_article_id": <1-3>,
  "confidence": <80-100 for clear matches>,
  "edge_cases_detected": [],
  "resolution_steps": ["KB step adapted to this ticket", ...],
  "additional_notes": "",
  "reasoning": "Matches the ticket type"
}}
"""

                            response = client.responses.create(
                                model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
                                input=ai_prompt,
                                reasoning={"effort": os.getenv("OPENAI_REASONING_EFFORT", "low")}
                            )

                            ai_analysis = json.loads(response.output_text)
                            
                            # Get selected article info
                            selected_idx = ai_analysis.get("selected_article_id", 1) - 1
                            selected_article = None
                            if selected_idx >= 0 and selected_idx < len(top_articles):
                                selected_article = top_articles[selected_idx]['article']
                            
                            confidence = ai_analysis.get("confidence", 0)
                            resolution_steps = ai_analysis.get("resolution_steps", [])
                            
                            # Prepare ticket context for automation
                            ticket_context = {
                                "dealer_name": classification.get("dealer_name", ""),
                                "syndicator": classification.get("syndicator", ""),
                                "provider": classification.get("provider", ""),
                                "category": classification.get("category", "")
                            }
                            
                            # Show selected article and confidence
                            if selected_article:
                                st.success(f"✅ **Selected Solution:** {selected_article.get('title')}")
                                confidence_color = "🟢" if confidence >= 80 else "🟡" if confidence >= 60 else "🔴"
                                st.caption(f"Confidence: {confidence_color} {confidence}%")
                            
                            st.markdown("---")
                            
                            # Layout: Resolution Steps (left 1/2) + Dealership Config (right 1/2)
                            col_steps, col_config = st.columns([1, 1])
                            
                            with col_steps:
                                st.markdown("### 📋 Resolution Steps")
                                render_resolution_steps_with_automation(resolution_steps, ticket_context)
                            
                            with col_config:
                                st.markdown("### ⚙️ Client Configuration")
                                display_client_configuration(ticket_context.get("dealer_name", ""))
                            
                            # Cache for feedback
                            if selected_idx >= 0 and selected_idx < len(top_articles):
                                selected_article_id = top_articles[selected_idx]['article'].get('id')
                                st.session_state.current_resolution = {
                                    "steps": resolution_steps,
                                    "selected_article_id": selected_article_id,
                                    "confidence": confidence
                                }
                                st.session_state.current_ticket_data = {
                                    "text": ticket_text,
                                    "subject": ticket_subject,
                                    "classification": classification
                                }
                                st.session_state.kb_results_cache = kb_results

                        except Exception as e:
                            st.error(f"❌ AI analysis failed: {str(e)}")
                            # Fallback: show first article's steps
                            st.warning("Showing fallback solution from top KB article:")
                            best_article = kb_results[0]['article']
                            st.markdown(f"**{best_article.get('title')}**")
                            
                            # Prepare ticket context for automation
                            ticket_context = {
                                "dealer_name": classification.get("dealer_name", ""),
                                "syndicator": classification.get("syndicator", ""),
                                "provider": classification.get("provider", ""),
                                "category": classification.get("category", "")
                            }
                            
                            # Layout: Resolution Steps (left 1/2) + Dealership Config (right 1/2)
                            col_steps, col_config = st.columns([1, 1])
                            
                            with col_steps:
                                st.markdown("### 📋 Resolution Steps")
                                render_resolution_steps_with_automation(best_article.get('steps', []), ticket_context)
                            
                            with col_config:
                                st.markdown("### ⚙️ Client Configuration")
                                display_client_configuration(ticket_context.get("dealer_name", ""))
                else:
                    st.warning("⚠️ No matching KB articles found. This may require manual handling.")
                    st.info("💡 This ticket might be a new type of issue that should be added to the KB after resolution.")
        else:
            st.error(f"⚠️ Knowledge Base not ready: {st.session_state.get('kb_error', 'Unknown error')}")

    # ========== STEP 3: FEEDBACK & KB LEARNING ==========
    # This is OUTSIDE the classify_button block so form submissions work
    st.markdown("---")
    demo_mode = st.session_state.get('demo_mode', False)
    step3_title = "🎓 STEP 3: KB Learning & Feedback" if demo_mode else "🎓 Step 3: KB Learning & Feedback"
    st.subheader(step3_title)

    if st.session_state.current_ticket_data:
        # Use a form to prevent reruns
        with st.form(key="feedback_form", clear_on_submit=False):
            st.markdown("**Did the suggested resolution work?**")
            resolution_failed = st.checkbox("❌ Resolution did not work")

            st.markdown("---")
            st.markdown("**Provide Feedback (Optional)**")
            st.caption("If the resolution didn't work, please tell us what actually worked:")

            actual_solution = st.text_area(
                "What was the actual solution?",
                placeholder="e.g., Had to also restart the service after disabling the feed...",
                height=100,
                key="actual_solution_input"
            )

            edge_case_desc = st.text_area(
                "Any edge cases or special circumstances?",
                placeholder="e.g., Client had custom integration that required additional steps...",
                height=80,
                key="edge_case_input"
            )

            submit_feedback = st.form_submit_button("📤 Submit Feedback", type="primary")

        # Process form submission
        if submit_feedback:
            if not resolution_failed:
                # Resolution worked - record success
                st.success("🎉 Great! This resolution is marked as successful.")
                # Track success
                if st.session_state.current_resolution and st.session_state.current_resolution.get("selected_article_id"):
                    article_id = st.session_state.current_resolution["selected_article_id"]
                    st.session_state.kb.record_usage(article_id, success=True)
                    st.success(f"✅ Success recorded for KB article #{article_id}")

                # Reset for next ticket
                st.session_state.current_ticket_data = None
                st.session_state.current_resolution = None
                time.sleep(1)
                st.rerun()

            elif actual_solution.strip():
                # Resolution failed - save feedback for audit
                if st.session_state.feedback_manager_ready:
                    # Prepare feedback data
                    ticket_data = {
                        "ticket_id": st.session_state.current_ticket_data.get("ticket_id", ""),
                        "subject": st.session_state.current_ticket_data.get("subject", ""),
                        "text": st.session_state.current_ticket_data["text"],
                        "category": st.session_state.current_ticket_data["classification"].get("category"),
                        "sub_category": st.session_state.current_ticket_data["classification"].get("sub_category"),
                        "syndicator": st.session_state.current_ticket_data["classification"].get("syndicator"),
                        "provider": st.session_state.current_ticket_data["classification"].get("provider"),
                        "dealer_name": st.session_state.current_ticket_data["classification"].get("dealer_name")
                    }

                    matched_article_id = None
                    if st.session_state.current_resolution and st.session_state.current_resolution.get("selected_article_id"):
                        matched_article_id = st.session_state.current_resolution["selected_article_id"]

                    agent_feedback = {
                        "actual_solution": actual_solution,
                        "edge_case": edge_case_desc,
                        "agent_name": "Demo Agent"  # In production, get from auth
                    }

                    # Save to pending feedback
                    feedback_id = st.session_state.feedback_manager.add_feedback(
                        ticket_data=ticket_data,
                        matched_article_id=matched_article_id,
                        agent_feedback=agent_feedback,
                        resolution_worked=False
                    )

                    st.success(f"📝 Feedback submitted! (ID: {feedback_id})")
                    st.info("💡 Your feedback has been queued for KB audit. A supervisor will review and update the KB accordingly.")

                    # Also record the failed usage if there was a matched article
                    if matched_article_id:
                        st.session_state.kb.record_usage(matched_article_id, success=False)

                    # Reset session state for next ticket
                    st.session_state.current_ticket_data = None
                    st.session_state.current_resolution = None
                    st.balloons()  # Visual celebration!
                    time.sleep(2)  # Give user time to see success message
                    st.rerun()  # Refresh to clear form
                else:
                    st.error(f"❌ Feedback system not available: {st.session_state.get('feedback_manager_error', 'Unknown error')}")
                    st.info("Your feedback could not be saved. Please contact support.")

            else:
                st.warning("⚠️ Please describe the actual solution before submitting.")

    # Footer
    st.markdown("---")
    st.caption("Powered by GPT-5-mini | Anthropic Claude Code")


if __name__ == '__main__':
    main()
