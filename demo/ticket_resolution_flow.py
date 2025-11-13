"""
Ticket Resolution Flow - Main Application
Complete workflow: Input → Classify → Suggest → Resolve → Learn
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Import our modules
from classifier import TicketClassifier
from knowledge_base import KnowledgeBase
from kb_intelligence import KBIntelligence

# Page config (with safe handling for unified app import)
try:
    st.set_page_config(
        page_title="Ticket Resolution Flow",
        page_icon="🎫",
        layout="wide"
    )
except:
    # Already configured by unified app
    pass

# Initialize components
@st.cache_resource
def get_classifier():
    """Get cached classifier instance"""
    return TicketClassifier()

@st.cache_resource
def get_kb():
    """Get cached KB instance"""
    return KnowledgeBase()

@st.cache_resource
def get_kb_intelligence():
    """Get cached KB Intelligence instance"""
    return KBIntelligence()


def init_session_state():
    """Initialize session state variables"""
    if 'phase' not in st.session_state:
        st.session_state.phase = 'input'  # input, classified, suggested, resolved, learned

    if 'ticket_text' not in st.session_state:
        st.session_state.ticket_text = ""

    if 'ticket_subject' not in st.session_state:
        st.session_state.ticket_subject = ""

    if 'classification' not in st.session_state:
        st.session_state.classification = None

    if 'entities' not in st.session_state:
        st.session_state.entities = None

    if 'suggested_articles' not in st.session_state:
        st.session_state.suggested_articles = []

    if 'selected_article' not in st.session_state:
        st.session_state.selected_article = None

    if 'resolution_feedback' not in st.session_state:
        st.session_state.resolution_feedback = {
            'success': None,
            'notes': ''
        }

    if 'kb_action' not in st.session_state:
        st.session_state.kb_action = None


def load_sample_tickets():
    """Load sample tickets for quick templates"""
    try:
        with open("mock_data/sample_tickets.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading sample tickets: {e}")
        return []


def display_classification_info():
    """Display classification information in sidebar"""
    if st.session_state.classification:
        st.sidebar.markdown("### 📋 Classification")
        cls = st.session_state.classification

        st.sidebar.markdown(f"**Category:** {cls.get('category', 'Unknown')}")
        st.sidebar.markdown(f"**Sub-Category:** {cls.get('sub_category', 'Unknown')}")
        st.sidebar.markdown(f"**Tier:** {cls.get('tier', 'Unknown')}")
        st.sidebar.markdown(f"**Dealer:** {cls.get('dealer_name', 'Unknown')}")

        if cls.get('syndicator'):
            st.sidebar.markdown(f"**Syndicator:** {cls.get('syndicator')}")
        if cls.get('provider'):
            st.sidebar.markdown(f"**Provider:** {cls.get('provider')}")

        if cls.get('inventory_type'):
            st.sidebar.markdown(f"**Inventory Type:** {cls.get('inventory_type')}")


def phase_input():
    """Phase 1: Ticket Input"""
    st.title("🎫 Ticket Resolution System")
    st.markdown("### Phase 1: Ticket Input")

    # Load sample tickets for templates
    sample_tickets = load_sample_tickets()

    # Quick Templates
    if sample_tickets:
        st.markdown("#### Quick Templates - Choose a Sample Ticket")

        # Display all tickets in rows of 4
        for row_start in range(0, len(sample_tickets), 4):
            cols = st.columns(4)
            row_tickets = sample_tickets[row_start:row_start + 4]

            for col_idx, ticket in enumerate(row_tickets):
                idx = row_start + col_idx
                with cols[col_idx]:
                    if st.button(
                        f"📄 Sample {idx+1}\n{ticket.get('subject', '')[:30]}...",
                        key=f"template_{idx}",
                        use_container_width=True
                    ):
                        st.session_state.ticket_subject = ticket.get('subject', '')
                        st.session_state.ticket_text = ticket.get('description', '')
                        st.rerun()

    st.markdown("---")

    # Ticket input form
    subject = st.text_input(
        "Ticket Subject",
        value=st.session_state.ticket_subject,
        key="input_subject"
    )

    text = st.text_area(
        "Ticket Content",
        value=st.session_state.ticket_text,
        height=200,
        key="input_text"
    )

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("🔍 Classify Ticket", type="primary", use_container_width=True):
            if not text.strip():
                st.error("Please enter ticket content")
            else:
                # Update session state
                st.session_state.ticket_subject = subject
                st.session_state.ticket_text = text

                # Classify the ticket
                with st.spinner("Classifying ticket..."):
                    classifier = get_classifier()
                    result = classifier.classify(text, subject)

                    if result['success']:
                        st.session_state.classification = result['classification']
                        st.session_state.entities = result['entities']
                        st.session_state.phase = 'classified'
                        st.rerun()
                    else:
                        st.error(f"Classification failed: {result.get('error', 'Unknown error')}")

    with col2:
        if st.button("🔄 Clear", use_container_width=True):
            st.session_state.ticket_subject = ""
            st.session_state.ticket_text = ""
            st.rerun()


def phase_classified():
    """Phase 2: Classification Results & KB Suggestions"""
    st.title("🎫 Ticket Resolution System")
    st.markdown("### Phase 2: Classification & KB Suggestions")

    # Show ticket info
    with st.expander("📄 Ticket Details", expanded=False):
        st.markdown(f"**Subject:** {st.session_state.ticket_subject}")
        st.markdown(f"**Content:** {st.session_state.ticket_text}")

    # Show classification
    st.markdown("#### 📋 Classification Results")
    cls = st.session_state.classification

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Category", cls.get('category', 'Unknown'))
        st.metric("Sub-Category", cls.get('sub_category', 'Unknown'))
    with col2:
        st.metric("Tier", cls.get('tier', 'Unknown'))
        st.metric("Dealer", cls.get('dealer_name', 'Unknown'))
    with col3:
        if cls.get('syndicator'):
            st.metric("Syndicator", cls.get('syndicator'))
        if cls.get('provider'):
            st.metric("Provider", cls.get('provider'))
        if cls.get('inventory_type'):
            st.metric("Inventory Type", cls.get('inventory_type'))

    st.markdown("---")

    # Search KB for relevant articles
    st.markdown("#### 📚 Knowledge Base Suggestions")

    if not st.session_state.suggested_articles:
        with st.spinner("Searching knowledge base..."):
            kb = get_kb()
            # Search using both text and classification
            query = st.session_state.ticket_text[:100]  # First 100 chars as query
            results = kb.search_articles(query, cls)
            st.session_state.suggested_articles = results

    if st.session_state.suggested_articles:
        st.success(f"Found {len(st.session_state.suggested_articles)} relevant articles")

        # Display top 3 suggestions
        for idx, result in enumerate(st.session_state.suggested_articles[:3]):
            article = result['article']
            score = result['score']
            confidence = result['confidence']

            with st.expander(f"📄 {article.get('title', 'Untitled')} (Confidence: {confidence}%)", expanded=(idx == 0)):
                st.markdown(f"**Problem:** {article.get('problem', 'N/A')}")
                st.markdown(f"**Solution:** {article.get('solution', 'N/A')}")

                if article.get('steps'):
                    st.markdown("**Steps:**")
                    for step_idx, step in enumerate(article['steps'], 1):
                        st.markdown(f"{step_idx}. {step}")

                # Stats
                usage = article.get('usage_count', 0)
                success_rate = article.get('success_rate', 1.0)
                st.caption(f"Used {usage} times | Success rate: {success_rate:.0%}")

                if st.button(f"✅ Use This Solution", key=f"use_article_{article.get('id')}", use_container_width=True):
                    st.session_state.selected_article = article
                    st.session_state.phase = 'suggested'
                    st.rerun()
    else:
        st.info("No existing KB articles found for this type of issue")

        if st.button("➡️ Continue Without KB Article", type="secondary", use_container_width=True):
            st.session_state.selected_article = None
            st.session_state.phase = 'suggested'
            st.rerun()

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to Input", use_container_width=True):
            st.session_state.phase = 'input'
            st.rerun()
    with col2:
        if st.button("⏭️ Skip to Resolution", use_container_width=True):
            st.session_state.phase = 'suggested'
            st.rerun()


def phase_suggested():
    """Phase 3: Apply Solution & Get Feedback"""
    st.title("🎫 Ticket Resolution System")
    st.markdown("### Phase 3: Resolution Feedback")

    # Show ticket info
    with st.expander("📄 Ticket Details", expanded=False):
        st.markdown(f"**Subject:** {st.session_state.ticket_subject}")
        st.markdown(f"**Content:** {st.session_state.ticket_text}")

    # Show selected article if any
    if st.session_state.selected_article:
        st.markdown("#### 📄 Applied Solution")
        article = st.session_state.selected_article

        with st.container():
            st.markdown(f"**{article.get('title', 'Untitled')}**")
            st.markdown(f"**Problem:** {article.get('problem', 'N/A')}")
            st.markdown(f"**Solution:** {article.get('solution', 'N/A')}")

            if article.get('steps'):
                st.markdown("**Steps:**")
                for step_idx, step in enumerate(article['steps'], 1):
                    st.markdown(f"{step_idx}. {step}")
    else:
        st.info("No KB article was used for this resolution")

    st.markdown("---")

    # Feedback form
    st.markdown("#### 📝 Agent Feedback")
    st.markdown("Please provide feedback on the resolution:")

    success = st.radio(
        "Did the resolution work?",
        options=[True, False],
        format_func=lambda x: "✅ Yes - Issue Resolved" if x else "❌ No - Issue Not Resolved",
        key="resolution_success"
    )

    notes = st.text_area(
        "Resolution Notes",
        placeholder="Describe what was done to resolve the ticket, any challenges faced, or additional context...",
        height=150,
        key="resolution_notes"
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("⬅️ Back to Classification", use_container_width=True):
            st.session_state.phase = 'classified'
            st.rerun()

    with col2:
        if st.button("✅ Submit Feedback & Learn", type="primary", use_container_width=True):
            if not notes.strip():
                st.error("Please provide resolution notes")
            else:
                # Store feedback
                st.session_state.resolution_feedback = {
                    'success': success,
                    'notes': notes
                }

                # Move to learning phase
                st.session_state.phase = 'resolved'
                st.rerun()


def phase_resolved():
    """Phase 4: Learning & KB Update"""
    st.title("🎫 Ticket Resolution System")
    st.markdown("### Phase 4: Learning & Knowledge Base Update")

    # Show ticket info
    with st.expander("📄 Ticket Details", expanded=False):
        st.markdown(f"**Subject:** {st.session_state.ticket_subject}")
        st.markdown(f"**Content:** {st.session_state.ticket_text}")

    # Show resolution feedback
    with st.expander("📝 Resolution Feedback", expanded=False):
        feedback = st.session_state.resolution_feedback
        status = "✅ Resolved" if feedback['success'] else "❌ Not Resolved"
        st.markdown(f"**Status:** {status}")
        st.markdown(f"**Notes:** {feedback['notes']}")

    st.markdown("---")

    # KB Intelligence Analysis
    st.markdown("#### 🧠 KB Intelligence Analysis")

    if not st.session_state.kb_action:
        with st.spinner("Analyzing resolution and determining KB action..."):
            kb_intel = get_kb_intelligence()
            kb = get_kb()

            # Prepare ticket and resolution data
            ticket_data = {
                'category': st.session_state.classification.get('category'),
                'sub_category': st.session_state.classification.get('sub_category'),
                'syndicator': st.session_state.classification.get('syndicator'),
                'provider': st.session_state.classification.get('provider'),
                'dealer_name': st.session_state.classification.get('dealer_name'),
                'text': st.session_state.ticket_text
            }

            resolution_data = {
                'solution': st.session_state.resolution_feedback['notes'],
                'success': st.session_state.resolution_feedback['success']
            }

            # Get existing articles from KB search
            existing_articles = st.session_state.suggested_articles[:3] if st.session_state.suggested_articles else None

            # Analyze
            kb_action = kb_intel.analyze_resolution(ticket_data, resolution_data, existing_articles)
            st.session_state.kb_action = kb_action

    # Display KB action
    action = st.session_state.kb_action
    action_type = action.get('action', 'none')

    # Action icon and title
    action_icons = {
        'add_new': '➕',
        'update_existing': '✏️',
        'remove': '🗑️',
        'none': '⏭️'
    }

    action_titles = {
        'add_new': 'Add New KB Article',
        'update_existing': 'Update Existing Article',
        'remove': 'Remove Outdated Article',
        'none': 'No KB Action Needed'
    }

    st.markdown(f"### {action_icons.get(action_type, '❓')} {action_titles.get(action_type, 'Unknown Action')}")

    # Show reasoning
    with st.container():
        st.markdown(f"**Reasoning:** {action.get('reasoning', 'N/A')}")
        st.markdown(f"**Confidence:** {action.get('confidence', 0)}%")

    st.markdown("---")

    # Execute KB action
    if action_type == 'add_new':
        st.markdown("#### ➕ New Article to Add")
        new_article = action.get('new_article', {})

        if new_article:
            with st.container():
                st.markdown(f"**Title:** {new_article.get('title', 'N/A')}")
                st.markdown(f"**Problem:** {new_article.get('problem', 'N/A')}")
                st.markdown(f"**Solution:** {new_article.get('solution', 'N/A')}")

                if new_article.get('steps'):
                    st.markdown("**Steps:**")
                    for idx, step in enumerate(new_article['steps'], 1):
                        st.markdown(f"{idx}. {step}")

                if new_article.get('tags'):
                    st.markdown(f"**Tags:** {', '.join(new_article['tags'])}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Add to KB", type="primary", use_container_width=True):
                    kb = get_kb()
                    article_id = kb.add_article(new_article)
                    st.success(f"✅ Article added to KB (ID: {article_id})")
                    st.session_state.phase = 'learned'
                    st.rerun()
            with col2:
                if st.button("⏭️ Skip", use_container_width=True):
                    st.session_state.phase = 'learned'
                    st.rerun()

    elif action_type == 'update_existing':
        st.markdown("#### ✏️ Article to Update")
        target_id = action.get('target_id')

        if target_id:
            kb = get_kb()
            existing = kb.get_article(target_id)
            new_article = action.get('new_article', {})

            if existing and new_article:
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Current Version:**")
                    st.markdown(f"Title: {existing.get('title', 'N/A')}")
                    st.markdown(f"Solution: {existing.get('solution', 'N/A')}")

                with col2:
                    st.markdown("**Updated Version:**")
                    st.markdown(f"Title: {new_article.get('title', 'N/A')}")
                    st.markdown(f"Solution: {new_article.get('solution', 'N/A')}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Update KB", type="primary", use_container_width=True):
                        kb.update_article(target_id, new_article)
                        st.success(f"✅ Article {target_id} updated in KB")
                        st.session_state.phase = 'learned'
                        st.rerun()
                with col2:
                    if st.button("⏭️ Skip", use_container_width=True):
                        st.session_state.phase = 'learned'
                        st.rerun()

    elif action_type == 'remove':
        st.markdown("#### 🗑️ Article to Remove")
        target_id = action.get('target_id')

        if target_id:
            kb = get_kb()
            existing = kb.get_article(target_id)

            if existing:
                with st.container():
                    st.markdown(f"**Title:** {existing.get('title', 'N/A')}")
                    st.markdown(f"**Problem:** {existing.get('problem', 'N/A')}")
                    st.markdown(f"**Reason for removal:** {action.get('reasoning', 'N/A')}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ Remove from KB", type="primary", use_container_width=True):
                        kb.delete_article(target_id)
                        st.success(f"✅ Article {target_id} removed from KB")
                        st.session_state.phase = 'learned'
                        st.rerun()
                with col2:
                    if st.button("⏭️ Skip", use_container_width=True):
                        st.session_state.phase = 'learned'
                        st.rerun()

    else:  # none
        st.info("No KB action needed for this resolution")

        # Update usage stats if an article was used
        if st.session_state.selected_article:
            kb = get_kb()
            article_id = st.session_state.selected_article.get('id')
            success = st.session_state.resolution_feedback['success']
            kb.record_usage(article_id, success)
            st.success(f"✅ Usage stats updated for article {article_id}")

        if st.button("✅ Complete", type="primary", use_container_width=True):
            st.session_state.phase = 'learned'
            st.rerun()


def phase_learned():
    """Phase 5: Complete"""
    st.title("🎫 Ticket Resolution System")
    st.markdown("### ✅ Process Complete!")

    st.success("Ticket has been processed and the knowledge base has been updated!")

    # Show summary
    st.markdown("#### 📊 Summary")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Classification:**")
        cls = st.session_state.classification
        st.markdown(f"- Category: {cls.get('category')}")
        st.markdown(f"- Sub-Category: {cls.get('sub_category')}")
        st.markdown(f"- Tier: {cls.get('tier')}")

    with col2:
        st.markdown("**Resolution:**")
        feedback = st.session_state.resolution_feedback
        status = "✅ Resolved" if feedback['success'] else "❌ Not Resolved"
        st.markdown(f"- Status: {status}")

        if st.session_state.kb_action:
            action_type = st.session_state.kb_action.get('action')
            st.markdown(f"- KB Action: {action_type}")

    st.markdown("---")

    # KB Stats
    st.markdown("#### 📈 Knowledge Base Stats")
    kb = get_kb()
    stats = kb.get_stats()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Articles", stats['total_articles'])
    with col2:
        st.metric("Total Usage", stats['total_usage'])
    with col3:
        st.metric("Avg Success Rate", f"{stats['avg_success_rate']:.0%}")

    st.markdown("---")

    if st.button("🔄 Process New Ticket", type="primary", use_container_width=True):
        # Reset session state
        st.session_state.phase = 'input'
        st.session_state.ticket_text = ""
        st.session_state.ticket_subject = ""
        st.session_state.classification = None
        st.session_state.entities = None
        st.session_state.suggested_articles = []
        st.session_state.selected_article = None
        st.session_state.resolution_feedback = {'success': None, 'notes': ''}
        st.session_state.kb_action = None
        st.rerun()


def main():
    """Main application"""
    init_session_state()

    # Sidebar
    st.sidebar.title("🎫 Ticket Resolution Flow")

    # Show current phase
    phases = {
        'input': '1️⃣ Ticket Input',
        'classified': '2️⃣ Classification',
        'suggested': '3️⃣ Resolution',
        'resolved': '4️⃣ Learning',
        'learned': '✅ Complete'
    }

    current_phase = st.session_state.phase
    st.sidebar.markdown("### Current Phase")
    st.sidebar.info(phases.get(current_phase, 'Unknown'))

    # Show all phases with status
    st.sidebar.markdown("### Workflow")
    for phase_key, phase_name in phases.items():
        if phase_key == current_phase:
            st.sidebar.markdown(f"**➡️ {phase_name}**")
        elif list(phases.keys()).index(phase_key) < list(phases.keys()).index(current_phase):
            st.sidebar.markdown(f"✅ {phase_name}")
        else:
            st.sidebar.markdown(f"⚪ {phase_name}")

    st.sidebar.markdown("---")

    # Display classification info if available
    display_classification_info()

    # Route to correct phase
    if current_phase == 'input':
        phase_input()
    elif current_phase == 'classified':
        phase_classified()
    elif current_phase == 'suggested':
        phase_suggested()
    elif current_phase == 'resolved':
        phase_resolved()
    elif current_phase == 'learned':
        phase_learned()
    else:
        st.error(f"Unknown phase: {current_phase}")


if __name__ == "__main__":
    main()
