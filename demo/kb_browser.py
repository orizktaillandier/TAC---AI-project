"""
Knowledge Base Browser - Nuclino/Notion-like Interface
Allows anyone to lookup and browse KB articles at any time
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Import KB module
from knowledge_base import KnowledgeBase

# Page config (with safe handling for unified app import)
try:
    st.set_page_config(
        page_title="Knowledge Base Browser",
        page_icon="📚",
        layout="wide"
    )
except:
    # Already configured by unified app
    pass


@st.cache_resource
def get_kb():
    """Get cached KB instance"""
    return KnowledgeBase()


def init_session_state():
    """Initialize session state variables"""
    if 'selected_article_id' not in st.session_state:
        st.session_state.selected_article_id = None

    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""

    if 'filter_category' not in st.session_state:
        st.session_state.filter_category = "All"


def render_article_card(article: Dict[str, Any], compact: bool = False, kb=None):
    """Render an article card"""
    if compact:
        # Compact view for list
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        with col1:
            if st.button(f"📄 {article.get('title', 'Untitled')}", key=f"select_{article.get('id')}", use_container_width=True):
                st.session_state.selected_article_id = article.get('id')
                st.rerun()

        with col2:
            st.caption(f"{article.get('category', 'N/A')}")

        with col3:
            success_rate = article.get('success_rate', 1.0)
            st.caption(f"✅ {success_rate:.0%}")

        with col4:
            usage = article.get('usage_count', 0)
            st.caption(f"📊 {usage} uses")
    else:
        # Full view
        with st.container():
            st.markdown(f"## {article.get('title', 'Untitled')}")

            # Metadata row
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Category", article.get('category', 'N/A'))
            with col2:
                st.metric("Sub-Category", article.get('sub_category', 'N/A'))
            with col3:
                success_rate = article.get('success_rate', 1.0)
                st.metric("Success Rate", f"{success_rate:.0%}")
            with col4:
                usage = article.get('usage_count', 0)
                st.metric("Usage Count", usage)

            st.markdown("---")

            # Problem
            st.markdown("### 🔍 Problem")
            st.markdown(article.get('problem', 'N/A'))

            # Solution
            st.markdown("### ✅ Solution")
            st.markdown(article.get('solution', 'N/A'))

            # Steps
            if article.get('steps'):
                st.markdown("### 📝 Steps")
                for idx, step in enumerate(article['steps'], 1):
                    st.markdown(f"{idx}. {step}")

            # Tags
            if article.get('tags'):
                st.markdown("### 🏷️ Tags")
                st.markdown(", ".join(f"`{tag}`" for tag in article['tags']))

            # Additional metadata
            st.markdown("---")
            col1, col2 = st.columns(2)

            with col1:
                if article.get('syndicator'):
                    st.markdown(f"**Syndicator:** {article.get('syndicator')}")
                if article.get('provider'):
                    st.markdown(f"**Provider:** {article.get('provider')}")

            with col2:
                if article.get('created_at'):
                    created = datetime.fromisoformat(article['created_at'])
                    st.caption(f"Created: {created.strftime('%Y-%m-%d %H:%M')}")
                if article.get('updated_at'):
                    updated = datetime.fromisoformat(article['updated_at'])
                    st.caption(f"Updated: {updated.strftime('%Y-%m-%d %H:%M')}")

            # Version history
            if article.get('version_history'):
                st.markdown("---")
                st.markdown("### 📜 Version History")
                version_count = len(article['version_history'])
                st.caption(f"This article has {version_count} previous version(s)")

                with st.expander("View Version History", expanded=False):
                    for version in reversed(article['version_history']):
                        version_num = version.get('version', 'Unknown')
                        timestamp = version.get('timestamp', 'Unknown')
                        reason = version.get('change_reason', 'No reason provided')

                        try:
                            ts = datetime.fromisoformat(timestamp)
                            formatted_time = ts.strftime('%Y-%m-%d %H:%M')
                        except:
                            formatted_time = timestamp

                        st.markdown(f"**Version {version_num}** - {formatted_time}")
                        st.caption(f"Change reason: {reason}")

                        prev_state = version.get('previous_state', {})
                        if prev_state:
                            with st.container():
                                # Show key changes
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.caption("**Previous:**")
                                    st.caption(f"Title: {prev_state.get('title', 'N/A')}")
                                    st.caption(f"Solution: {prev_state.get('solution', 'N/A')[:100]}...")
                                    st.caption(f"Steps: {len(prev_state.get('steps', []))} step(s)")
                                    st.caption(f"Success Rate: {prev_state.get('success_rate', 0):.0%}")

                                with col2:
                                    # Show rollback button for administrators
                                    if st.button(f"🔄 Rollback to v{version_num}", key=f"rollback_{article.get('id')}_{version_num}"):
                                        if kb.rollback_article(article.get('id'), version_num):
                                            # Clear cache so all tabs see the rolled-back article
                                            st.cache_resource.clear()
                                            st.success(f"Rolled back to version {version_num}")
                                            st.rerun()
                                        else:
                                            st.error("Rollback failed")
                        st.markdown("---")


def render_kb_browser():
    """Main KB browser interface"""
    st.title("📚 Knowledge Base Browser")
    st.markdown("Browse and search all knowledge base articles")

    # Get KB
    kb = get_kb()

    # Search and filter controls
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        search = st.text_input(
            "🔍 Search articles",
            value=st.session_state.search_query,
            placeholder="Search by title, problem, solution, or tags...",
            key="search_input"
        )
        st.session_state.search_query = search

    with col2:
        # Get all categories
        all_categories = sorted(list(set(a.get('category', 'Unknown') for a in kb.articles if a.get('category'))))
        categories = ["All"] + all_categories

        category_filter = st.selectbox(
            "Category",
            options=categories,
            index=categories.index(st.session_state.filter_category) if st.session_state.filter_category in categories else 0,
            key="category_filter"
        )
        st.session_state.filter_category = category_filter

    with col3:
        # Sort options
        sort_by = st.selectbox(
            "Sort by",
            options=["Most Recent", "Most Used", "Highest Success Rate", "Title A-Z"],
            key="sort_by"
        )

    st.markdown("---")

    # Filter articles
    filtered_articles = kb.articles.copy()

    # Apply search filter
    if search.strip():
        search_lower = search.lower()
        filtered_articles = [
            a for a in filtered_articles
            if (search_lower in a.get('title', '').lower() or
                search_lower in a.get('problem', '').lower() or
                search_lower in a.get('solution', '').lower() or
                any(search_lower in tag.lower() for tag in a.get('tags', [])))
        ]

    # Apply category filter
    if category_filter != "All":
        filtered_articles = [a for a in filtered_articles if a.get('category') == category_filter]

    # Apply sorting
    if sort_by == "Most Recent":
        filtered_articles.sort(key=lambda x: x.get('updated_at', x.get('created_at', '')), reverse=True)
    elif sort_by == "Most Used":
        filtered_articles.sort(key=lambda x: x.get('usage_count', 0), reverse=True)
    elif sort_by == "Highest Success Rate":
        filtered_articles.sort(key=lambda x: x.get('success_rate', 0), reverse=True)
    elif sort_by == "Title A-Z":
        filtered_articles.sort(key=lambda x: x.get('title', '').lower())

    # Show count
    st.info(f"📊 Showing {len(filtered_articles)} of {len(kb.articles)} articles")

    # Layout: List on left, detail on right
    if st.session_state.selected_article_id:
        # Two-column layout when article is selected
        col_list, col_detail = st.columns([1, 2])

        with col_list:
            st.markdown("### Articles")
            if st.button("⬅️ Clear Selection", use_container_width=True):
                st.session_state.selected_article_id = None
                st.rerun()

            st.markdown("---")

            # Show compact list
            for article in filtered_articles:
                render_article_card(article, compact=True, kb=kb)

        with col_detail:
            # Show selected article
            selected = kb.get_article(st.session_state.selected_article_id)
            if selected:
                render_article_card(selected, compact=False, kb=kb)
            else:
                st.error("Article not found")
                st.session_state.selected_article_id = None
                st.rerun()
    else:
        # Full-width list when no article is selected
        st.markdown("### Articles")
        st.markdown("Click on an article to view details")
        st.markdown("---")

        for article in filtered_articles:
            render_article_card(article, compact=True, kb=kb)
            st.markdown("")  # Spacing


def render_kb_stats():
    """Render KB statistics in sidebar"""
    kb = get_kb()
    stats = kb.get_stats()

    st.sidebar.markdown("### 📊 KB Statistics")

    st.sidebar.metric("Total Articles", stats['total_articles'])
    st.sidebar.metric("Total Usage", stats['total_usage'])
    st.sidebar.metric("Avg Success Rate", f"{stats['avg_success_rate']:.0%}")

    st.sidebar.markdown("---")

    # Articles by category
    if stats.get('articles_by_category'):
        st.sidebar.markdown("**Articles by Category:**")
        for category, count in sorted(stats['articles_by_category'].items(), key=lambda x: x[1], reverse=True)[:5]:
            st.sidebar.caption(f"• {category}: {count}")


def main():
    """Main application"""
    init_session_state()

    # Sidebar
    st.sidebar.title("📚 Knowledge Base")
    st.sidebar.markdown("Browse and search all support articles")

    st.sidebar.markdown("---")

    # Stats
    render_kb_stats()

    st.sidebar.markdown("---")

    # Quick actions
    st.sidebar.markdown("### Quick Actions")

    if st.sidebar.button("🔄 Refresh KB", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

    if st.sidebar.button("🏠 Clear Filters", use_container_width=True):
        st.session_state.search_query = ""
        st.session_state.filter_category = "All"
        st.session_state.selected_article_id = None
        st.rerun()

    # Main content
    render_kb_browser()


if __name__ == "__main__":
    main()
