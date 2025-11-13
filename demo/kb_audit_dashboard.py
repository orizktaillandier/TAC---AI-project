"""
KB Audit Dashboard
Allows supervisors to review pending feedback and intelligently update the KB
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Import modules
from feedback_manager import FeedbackManager
from knowledge_base import KnowledgeBase
from kb_intelligence import KBIntelligence
from kb_audit_log import get_audit_log

# Page config (with safe handling for unified app import)
try:
    st.set_page_config(
        page_title="KB Audit Dashboard",
        page_icon="🔍",
        layout="wide"
    )
except:
    # Already configured by unified app
    pass

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 1rem;
    }
    .feedback-card {
        padding: 1rem;
        border: 1px solid #ddd;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def get_managers():
    """Get manager instances - FeedbackManager NOT cached to get fresh data"""
    # Don't cache FeedbackManager so it reloads the file each time
    return {
        'feedback': FeedbackManager(),  # Always fresh to get new feedback
        'kb': KnowledgeBase(),
        'kb_intel': KBIntelligence()
    }


def init_session_state():
    """Initialize session state"""
    if 'selected_feedback_ids' not in st.session_state:
        st.session_state.selected_feedback_ids = []
    if 'ai_recommendations' not in st.session_state:
        st.session_state.ai_recommendations = {}
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = "By Article"


def run_ai_analysis(feedback_items: List[Dict[str, Any]], kb: KnowledgeBase, kb_intel: KBIntelligence, feedback_mgr: FeedbackManager):
    """Run AI analysis on feedback items and persist recommendations"""
    recommendations = {}

    for item in feedback_items:
        feedback_id = item['id']

        # Get matched article if exists
        matched_article_id = item.get('matched_article_id')
        existing_articles = []

        if matched_article_id:
            article = kb.get_article(matched_article_id)
            if article:
                existing_articles = [{'article': article, 'score': 100}]

        # Prepare data for AI
        ticket_data = item['ticket_data']
        resolution_data = {
            'solution': item['agent_feedback']['actual_solution'],
            'edge_case': item['agent_feedback'].get('edge_case', ''),
            'success': not item['resolution_worked']
        }

        # Run AI analysis
        try:
            analysis = kb_intel.analyze_resolution(
                ticket=ticket_data,
                resolution=resolution_data,
                existing_articles=existing_articles
            )
            recommendations[feedback_id] = analysis
            # PERSIST to disk immediately
            feedback_mgr.update_ai_recommendation(feedback_id, analysis)
        except Exception as e:
            error_recommendation = {
                'action': 'none',
                'confidence': 0,
                'reasoning': f'Error: {str(e)}'
            }
            recommendations[feedback_id] = error_recommendation
            # PERSIST error state too
            feedback_mgr.update_ai_recommendation(feedback_id, error_recommendation)

    return recommendations


def render_feedback_card(item: Dict[str, Any], kb: KnowledgeBase, recommendation: Dict[str, Any] = None):
    """Render a single feedback item card"""
    feedback_id = item['id']

    with st.container():
        # Header
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.markdown(f"### 📋 Feedback #{feedback_id}")
            st.caption(f"Submitted: {item.get('timestamp', 'N/A')}")

        with col2:
            st.metric("Status", item.get('status', 'pending').upper())

        with col3:
            if item.get('matched_article_id'):
                st.metric("Original KB", f"#{item['matched_article_id']}")
            else:
                st.caption("No KB match")

        st.markdown("---")

        # Ticket info
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🎫 Original Ticket")
            st.markdown(f"**Subject:** {item['ticket_data'].get('subject', 'N/A')}")
            st.markdown(f"**Text:** {item['ticket_data'].get('text', 'N/A')}")
            st.markdown(f"**Category:** {item['ticket_data'].get('category')} → {item['ticket_data'].get('sub_category')}")

        with col2:
            st.markdown("#### 💬 Agent Feedback")
            st.markdown(f"**Agent:** {item['agent_feedback'].get('agent_name', 'Unknown')}")
            st.markdown(f"**Resolution Worked:** {'❌ No' if not item['resolution_worked'] else '✅ Yes'}")
            st.markdown(f"**Actual Solution:**")
            st.info(item['agent_feedback'].get('actual_solution', 'N/A'))

            if item['agent_feedback'].get('edge_case'):
                st.markdown(f"**Edge Case:**")
                st.warning(item['agent_feedback'].get('edge_case'))

        # Show matched article if exists
        if item.get('matched_article_id'):
            matched_article = kb.get_article(item['matched_article_id'])
            if matched_article:
                with st.expander(f"📄 Originally Used Article #{item['matched_article_id']} (Agent tried this)", expanded=False):
                    st.markdown(f"**Title:** {matched_article.get('title')}")
                    st.markdown(f"**Solution:** {matched_article.get('solution')}")
                    st.markdown(f"**Steps:** {len(matched_article.get('steps', []))} step(s)")
                    st.caption("⚠️ This solution did not work for the ticket")

        # Show AI recommendation if available
        if recommendation:
            st.markdown("---")
            st.markdown("#### 🤖 AI Recommendation")

            action = recommendation.get('action', 'none')
            confidence = recommendation.get('confidence', 0)
            reasoning = recommendation.get('reasoning', '')

            col1, col2, col3 = st.columns(3)
            with col1:
                action_display = action.upper().replace('_', ' ')
                if action == 'add_new':
                    st.metric("Action", "➕ " + action_display)
                elif action == 'update_existing':
                    target_id = recommendation.get('target_id')
                    if target_id:
                        st.metric("Action", f"🔄 UPDATE ARTICLE #{target_id}")
                    else:
                        st.metric("Action", "🔄 " + action_display)
                elif action == 'none':
                    st.metric("Action", "⏸️ " + action_display)
                else:
                    st.metric("Action", action_display)
            with col2:
                # Color-coded confidence
                if confidence >= 80:
                    st.metric("Confidence", f"{confidence}%", delta="High", delta_color="normal")
                elif confidence >= 60:
                    st.metric("Confidence", f"{confidence}%", delta="Medium", delta_color="normal")
                else:
                    st.metric("Confidence", f"{confidence}%", delta="Low", delta_color="inverse")
            with col3:
                # Confidence indicator with progress bar
                if confidence >= 80:
                    st.success("✅ High Confidence - Safe to apply")
                elif confidence >= 60:
                    st.warning("⚠️ Medium Confidence - Review carefully")
                else:
                    st.error("❌ Low Confidence - Manual review needed")

            # Progress bar for confidence
            st.progress(confidence / 100.0)
            st.markdown(f"**Reasoning:** {reasoning}")

            # Show new/updated article preview
            if action in ['add_new', 'update_existing'] and recommendation.get('new_article'):
                with st.expander("✏️ Article to " + ("Create" if action == 'add_new' else "Update"), expanded=True):
                    article = recommendation['new_article']
                    st.markdown(f"**Title:** {article.get('title', 'N/A')}")
                    st.markdown(f"**Problem:** {article.get('problem', 'N/A')}")
                    st.markdown(f"**Solution:** {article.get('solution', 'N/A')}")

                    if article.get('steps'):
                        st.markdown("**Steps:**")
                        for i, step in enumerate(article['steps'], 1):
                            st.markdown(f"{i}. {step}")

                    if article.get('tags'):
                        st.markdown(f"**Tags:** {', '.join(article['tags'])}")

        return feedback_id


def render_action_buttons(feedback_id: int, recommendation: Dict[str, Any], feedback_mgr: FeedbackManager, kb: KnowledgeBase):
    """Render action buttons for a feedback item"""
    action = recommendation.get('action', 'none')

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if action == 'add_new':
            if st.button(f"✅ Create New Article", key=f"add_{feedback_id}"):
                new_article = recommendation.get('new_article', {})
                new_id = kb.add_article(new_article)
                feedback_mgr.update_feedback_status(feedback_id, 'applied', f'Created new KB article #{new_id}')

                # Log to audit trail
                audit_log = get_audit_log()
                audit_log.log_action(
                    action='create',
                    article_id=new_id,
                    user='Supervisor',
                    details={
                        'title': new_article.get('title'),
                        'reason': recommendation.get('reasoning'),
                        'confidence': recommendation.get('confidence')
                    },
                    feedback_id=feedback_id
                )

                st.success(f"Created new KB article #{new_id}")
                st.rerun()

    with col2:
        if action == 'update_existing':
            if st.button(f"🔄 Update Article", key=f"update_{feedback_id}"):
                target_id = recommendation.get('target_id')
                updates = recommendation.get('new_article', {})
                kb.update_article(target_id, updates, change_reason=recommendation.get('reasoning', ''))
                feedback_mgr.update_feedback_status(feedback_id, 'applied', f'Updated KB article #{target_id}')

                # Log to audit trail
                audit_log = get_audit_log()
                audit_log.log_action(
                    action='update',
                    article_id=target_id,
                    user='Supervisor',
                    details={
                        'changes': updates,
                        'reason': recommendation.get('reasoning'),
                        'confidence': recommendation.get('confidence')
                    },
                    feedback_id=feedback_id
                )

                st.success(f"Updated KB article #{target_id}")
                st.rerun()

        elif action == 'add_new':
            pass  # Already handled in col1

    with col3:
        if st.button(f"➕ Add as Edge Case", key=f"edge_{feedback_id}"):
            # Get feedback item
            item = feedback_mgr.get_feedback(feedback_id)
            if item and item.get('matched_article_id'):
                edge_case = {
                    'scenario': item['ticket_data'].get('text', ''),
                    'note': item['agent_feedback'].get('actual_solution', ''),
                    'reported_by': item['agent_feedback'].get('agent_name', 'Unknown'),
                    'date': datetime.now().isoformat()
                }
                kb.add_edge_case(item['matched_article_id'], edge_case)
                feedback_mgr.update_feedback_status(feedback_id, 'applied', 'Added as edge case')
                st.success(f"Added edge case to article #{item['matched_article_id']}")
                st.rerun()

    with col4:
        if st.button(f"❌ Dismiss", key=f"dismiss_{feedback_id}"):
            feedback_mgr.update_feedback_status(feedback_id, 'dismissed', 'Dismissed by supervisor')
            st.info("Feedback dismissed")
            st.rerun()

    with col5:
        if st.button(f"🗑️ Delete", key=f"delete_{feedback_id}"):
            if feedback_mgr.delete_feedback(feedback_id):
                st.success("Feedback deleted permanently")
                st.rerun()
            else:
                st.error("Failed to delete feedback")


def render_feedback_list():
    """Render the main feedback list view"""
    managers = get_managers()
    feedback_mgr = managers['feedback']
    kb = managers['kb']
    kb_intel = managers['kb_intel']

    # Get pending feedback
    pending = feedback_mgr.get_pending_feedback()

    if not pending:
        st.info("🎉 No pending feedback! All caught up.")
        return

    # Load existing AI recommendations from feedback items (PERSISTENCE!)
    for item in pending:
        feedback_id = item['id']
        if item.get('ai_recommendation') and feedback_id not in st.session_state.ai_recommendations:
            # Load persisted recommendation into session state cache
            st.session_state.ai_recommendations[feedback_id] = item['ai_recommendation']

    st.markdown(f"### 📋 {len(pending)} Pending Feedback Items")
    st.caption(f"DEBUG: Loaded {len(pending)} items from file: {[item['id'] for item in pending]}")

    # View mode selector
    view_mode = st.radio(
        "View by:",
        ["By Article", "By Date", "All"],
        horizontal=True,
        index=["By Article", "By Date", "All"].index(st.session_state.view_mode)
    )
    st.session_state.view_mode = view_mode

    st.markdown("---")

    # Run AI Analysis button
    if st.button("🤖 Run AI Analysis on All", type="primary"):
        with st.spinner("Running AI analysis on all pending feedback..."):
            st.session_state.ai_recommendations = run_ai_analysis(pending, kb, kb_intel, feedback_mgr)
        st.success(f"✅ Analyzed {len(pending)} feedback items and saved recommendations!")
        st.rerun()

    st.markdown("---")

    # Group feedback based on view mode
    if view_mode == "By Article":
        grouped = feedback_mgr.group_by_article()

        for article_id, items in grouped.items():
            article = kb.get_article(article_id)
            article_title = article.get('title', 'Unknown') if article else 'No Article Match'

            with st.expander(f"📄 Article #{article_id}: {article_title} ({len(items)} feedback items)", expanded=True):
                for item in items:
                    feedback_id = item['id']
                    recommendation = st.session_state.ai_recommendations.get(feedback_id)

                    render_feedback_card(item, kb, recommendation)

                    # Always show delete button
                    col1, col2 = st.columns([5, 1])
                    with col2:
                        if st.button(f"🗑️ Delete", key=f"delete_{feedback_id}_standalone"):
                            if feedback_mgr.delete_feedback(feedback_id):
                                st.success("Feedback deleted")
                                st.rerun()

                    if recommendation:
                        render_action_buttons(feedback_id, recommendation, feedback_mgr, kb)

                    st.markdown("---")

    elif view_mode == "By Date":
        # Sort by timestamp
        sorted_items = sorted(pending, key=lambda x: x.get('timestamp', ''), reverse=True)

        for item in sorted_items:
            feedback_id = item['id']
            recommendation = st.session_state.ai_recommendations.get(feedback_id)

            render_feedback_card(item, kb, recommendation)

            if recommendation:
                render_action_buttons(feedback_id, recommendation, feedback_mgr, kb)

            st.markdown("---")

    else:  # All
        for item in pending:
            feedback_id = item['id']
            recommendation = st.session_state.ai_recommendations.get(feedback_id)

            render_feedback_card(item, kb, recommendation)

            if recommendation:
                render_action_buttons(feedback_id, recommendation, feedback_mgr, kb)

            st.markdown("---")


def render_stats():
    """Render statistics sidebar"""
    managers = get_managers()
    feedback_mgr = managers['feedback']
    kb = managers['kb']

    st.sidebar.title("📊 Feedback Statistics")

    stats = feedback_mgr.get_stats()

    st.sidebar.metric("Total Feedback", stats['total_feedback'])
    st.sidebar.metric("Pending", stats['pending'])
    st.sidebar.metric("Applied", stats['applied'])
    st.sidebar.metric("Dismissed", stats['dismissed'])

    st.sidebar.markdown("---")

    st.sidebar.markdown("### 🔥 Most Reported Articles")
    for article_id, count in stats['most_reported_articles']:
        article = kb.get_article(article_id)
        title = article.get('title', 'Unknown') if article else 'No Match'
        st.sidebar.caption(f"#{article_id}: {title[:30]}... ({count} reports)")

    st.sidebar.markdown("---")

    # Quick actions
    st.sidebar.markdown("### ⚡ Quick Actions")

    if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

    if st.sidebar.button("🧹 Clear Processed (30+ days)", use_container_width=True):
        feedback_mgr.clear_processed_feedback(older_than_days=30)
        st.sidebar.success("Cleared old processed feedback")
        st.rerun()

    # Audit Log
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📜 Recent KB Changes")

    audit_log = get_audit_log()
    recent_actions = audit_log.get_recent_actions(limit=5)

    if recent_actions:
        for action in recent_actions:
            action_type = action.get('action', 'unknown')
            article_id = action.get('article_id', 'N/A')
            user = action.get('user', 'Unknown')

            # Format timestamp
            try:
                ts = datetime.fromisoformat(action['timestamp'])
                time_str = ts.strftime('%m/%d %H:%M')
            except:
                time_str = 'Unknown'

            # Icons for different actions
            icon = {'create': '➕', 'update': '🔄', 'delete': '🗑️',
                   'rollback': '↩️', 'edge_case': '📌'}.get(action_type, '•')

            st.sidebar.caption(f"{icon} {time_str} - {action_type.upper()}")
            st.sidebar.caption(f"   Article #{article_id} by {user}")
    else:
        st.sidebar.caption("No recent changes")


def main():
    """Main application"""
    init_session_state()

    # Title
    st.title("🔍 KB Audit Dashboard")
    st.markdown("Review and approve pending feedback to improve the Knowledge Base")

    # Render sidebar stats
    render_stats()

    # Render main content
    render_feedback_list()


if __name__ == "__main__":
    main()
