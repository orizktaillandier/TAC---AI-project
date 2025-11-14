"""
Knowledge Base Builder - AI-Powered Documentation System
Automatically generates and maintains support documentation from resolved tickets
"""

import streamlit as st
import json
from datetime import datetime
from knowledge_base import KnowledgeBase
from documentation_generator import DocumentationGenerator
# from kb_browser import KBBrowser  # Commented out - not available

# Page config
st.set_page_config(
    page_title="KB Builder - Demo",
    page_icon="📚",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        margin-top: 0.5rem;
    }
    .kb-article {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #007bff;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "knowledge_base" not in st.session_state:
    st.session_state.knowledge_base = KnowledgeBase()
    # Add some sample articles
    st.session_state.knowledge_base.add_article({
        "title": "Kijiji Export Not Working",
        "problem": "Dealer reports that their vehicles are not appearing on Kijiji",
        "solution": "This is typically caused by authentication issues with the Kijiji API",
        "steps": [
            "Verify dealer's Kijiji account is active",
            "Check API credentials in our system",
            "Re-authenticate Kijiji connection",
            "Trigger manual sync"
        ],
        "category": "Syndicator Bug",
        "syndicator": "Kijiji",
        "tags": ["kijiji", "export", "api", "authentication"],
        "resolution_time": "15 minutes"
    })

    st.session_state.knowledge_base.add_article({
        "title": "PBS Import Fails with Error 500",
        "problem": "PBS inventory import returns HTTP 500 error",
        "solution": "PBS API throttling or temporary outage",
        "steps": [
            "Check PBS status page",
            "Wait 10 minutes and retry",
            "If persists, contact PBS support",
            "Enable import retry queue"
        ],
        "category": "Import Issue",
        "provider": "PBS",
        "tags": ["pbs", "import", "api", "error"],
        "resolution_time": "5 minutes"
    })

if "doc_generator" not in st.session_state:
    try:
        st.session_state.doc_generator = DocumentationGenerator()
        st.session_state.doc_generator_ready = True
    except Exception as e:
        st.session_state.doc_generator_ready = False
        st.session_state.doc_generator_error = str(e)

if "resolved_tickets" not in st.session_state:
    try:
        with open("mock_data/resolved_tickets.json", "r") as f:
            st.session_state.resolved_tickets = json.load(f)
    except:
        st.session_state.resolved_tickets = []

# Header
st.title("📚 Knowledge Base Builder")
st.markdown("### Automatically Generate & Maintain Support Documentation")

# Sidebar
with st.sidebar:
    st.header("📚 KB Stats")

    kb_stats = st.session_state.knowledge_base.get_stats()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{kb_stats['total_articles']}</div>
            <div class="metric-label">Articles</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{kb_stats['total_views']}</div>
            <div class="metric-label">Total Views</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🎯 Key Features")
    st.markdown("""
    - ✅ AI-Generated Articles
    - ✅ Gap Analysis
    - ✅ Smart Search & Matching
    - ✅ Coverage Tracking
    - ✅ Auto-Documentation
    """)

    st.markdown("---")
    st.markdown("### 💡 Business Value")
    st.markdown("""
    - **Faster** ticket resolution
    - **Consistent** support quality
    - **Reduced** training time
    - **Better** knowledge retention
    """)

    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("""
    This system automatically generates
    knowledge base articles from resolved
    support tickets, ensuring documentation
    stays current and comprehensive.
    """)

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Coverage Analysis",
    "✍️ Generate Articles",
    "📚 KB Dashboard",
    "🔍 Search & Match",
    "🌐 KB Browser"
])

with tab1:
    st.header("📊 Documentation Coverage Analysis")
    st.markdown("Identify gaps in your knowledge base and prioritize documentation efforts.")

    # Mock ticket data for coverage analysis
    mock_tickets = [
        {"classification": {"category": "Syndicator Bug", "syndicator": "Kijiji"}},
        {"classification": {"category": "Import Issue", "provider": "PBS"}},
        {"classification": {"category": "Syndicator Bug", "syndicator": "AutoTrader"}},
        {"classification": {"category": "Feature Request"}},
        {"classification": {"category": "Syndicator Bug", "syndicator": "Facebook"}},
        {"classification": {"category": "Import Issue", "provider": "CDK"}},
    ]

    coverage = st.session_state.knowledge_base.get_coverage_analysis(mock_tickets)

    # Display coverage metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Articles", coverage["total_articles"])
    with col2:
        st.metric("Coverage %", f"{coverage['coverage_percentage']}%",
                 delta="Good" if coverage['coverage_percentage'] >= 70 else "Needs work",
                 delta_color="normal" if coverage['coverage_percentage'] >= 70 else "inverse")
    with col3:
        st.metric("Documentation Gaps", coverage["gap_count"],
                 delta_color="inverse")
    with col4:
        st.metric("Categories Covered", coverage["covered_categories_count"])

    # Coverage breakdown
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ✅ Covered Categories")
        if coverage["covered_categories"]:
            for category in coverage["covered_categories"]:
                st.success(f"✓ {category}")
        else:
            st.info("No categories covered yet. Generate articles to improve coverage.")

    with col2:
        st.markdown("### ⚠️ Category Gaps")
        if coverage["category_gaps"]:
            for gap in coverage["category_gaps"]:
                priority_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}[gap["priority"]]
                st.warning(f"{priority_color} **{gap['category']}** - {gap['ticket_count']} tickets ({gap['priority']} priority)")
        else:
            st.success("✅ All categories have documentation!")

    # Recommendations
    st.markdown("---")
    st.markdown("### 💡 Recommendations")

    if coverage["gap_count"] > 0:
        st.info(f"""
        **Action Required:** You have {coverage['gap_count']} documentation gaps.

        1. Review the gaps in categories above
        2. Prioritize high-traffic categories
        3. Generate articles from resolved tickets
        4. Aim for at least 80% coverage
        """)
    else:
        st.success("🎉 Excellent coverage! Keep documentation updated as new issues arise.")

with tab2:
    st.header("✍️ Generate KB Articles from Resolved Tickets")

    if not st.session_state.doc_generator_ready:
        st.error("⚠️ AI Documentation Generator not available. Please set OPENAI_API_KEY in .env file.")
    else:
        st.markdown("Transform resolved tickets into searchable knowledge base articles using AI.")

        # Load resolved tickets
        resolved_tickets = st.session_state.resolved_tickets

        if not resolved_tickets:
            st.warning("No resolved tickets available. Add some to mock_data/resolved_tickets.json")
        else:
            st.success(f"✅ Found {len(resolved_tickets)} resolved tickets ready for documentation")

            # Display resolved tickets
            st.markdown("### 📋 Available Resolved Tickets")

            selected_tickets = []
            for i, resolved in enumerate(resolved_tickets):
                ticket = resolved["ticket"]
                resolution = resolved["resolution"]

                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    if st.checkbox(f"**{ticket['ticket_id']}:** {ticket['subject']}", key=f"ticket_{i}"):
                        selected_tickets.append(resolved)
                with col2:
                    st.caption(f"Category: {ticket['classification'].get('category', 'Unknown')}")
                with col3:
                    st.caption(f"Time: {resolution.get('time_to_resolve', 'Unknown')}")

                with st.expander(f"View ticket details"):
                    st.markdown(f"**Problem:** {ticket['text']}")
                    st.markdown(f"**Resolution:** {resolution['resolution']}")
                    if resolution.get('steps'):
                        st.markdown("**Steps taken:**")
                        for step in resolution['steps']:
                            st.markdown(f"- {step}")

            # Generate articles button
            st.markdown("---")
            if selected_tickets:
                if st.button(f"🚀 Generate {len(selected_tickets)} KB Article(s)", type="primary"):
                    progress_bar = st.progress(0)
                    generated_count = 0

                    for idx, resolved in enumerate(selected_tickets):
                        progress_bar.progress((idx + 1) / len(selected_tickets))

                        with st.spinner(f"Generating article {idx + 1} of {len(selected_tickets)}..."):
                            try:
                                article = st.session_state.doc_generator.generate_kb_article(
                                    ticket_data=resolved["ticket"],
                                    resolution_data=resolved["resolution"]
                                )

                                # Add to knowledge base
                                article_id = st.session_state.knowledge_base.add_article(article)
                                generated_count += 1

                                # Clear cache so KB Browser and other tabs see the new article
                                st.cache_resource.clear()

                                st.success(f"✅ Generated: **{article.get('title')}** (ID: {article_id})")

                                # Show preview
                                with st.expander("Preview Generated Article"):
                                    st.markdown(f"**Title:** {article.get('title')}")
                                    st.markdown(f"**Problem:** {article.get('problem')}")
                                    st.markdown(f"**Solution:** {article.get('solution')}")
                                    if article.get('steps'):
                                        st.markdown("**Steps:**")
                                        for i, step in enumerate(article['steps'], 1):
                                            st.markdown(f"{i}. {step}")
                                    st.markdown(f"**Tags:** {', '.join(article.get('tags', []))}")
                            except Exception as e:
                                st.error(f"❌ Failed to generate article: {e}")

                    st.success(f"🎉 Successfully generated {generated_count} KB articles!")
                    st.balloons()
                    st.rerun()
            else:
                st.info("👆 Select tickets above to generate KB articles")

with tab3:
    st.header("📚 Knowledge Base Dashboard")

    kb = st.session_state.knowledge_base
    stats = kb.get_stats()

    if stats["total_articles"] == 0:
        st.info("📝 No articles in knowledge base yet. Generate some articles from resolved tickets!")
    else:
        # Overall stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Articles", stats["total_articles"])
        with col2:
            st.metric("Total Views", stats["total_views"])
        with col3:
            st.metric("Helpful Marks", stats["total_helpful"])
        with col4:
            st.metric("Avg Views/Article", stats["avg_views"])

        # Category breakdown
        st.markdown("---")
        st.markdown("### 📊 Articles by Category")

        if stats["categories"]:
            for category, count in stats["categories"].items():
                percentage = (count / stats["total_articles"]) * 100
                st.markdown(f"""
                <div style="background-color: rgba(99, 102, 241, 0.1); padding: 0.75rem; border-radius: 0.25rem; margin: 0.5rem 0;">
                    <strong>{category}</strong>: {count} articles ({percentage:.0f}%)
                    <div style="background-color: rgba(99, 102, 241, 0.3); height: 8px; border-radius: 4px; margin-top: 0.5rem;">
                        <div style="background-color: #6366f1; height: 8px; border-radius: 4px; width: {percentage}%;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # All articles
        st.markdown("---")
        st.markdown("### 📄 All Knowledge Base Articles")

        # Sort options
        sort_by = st.selectbox("Sort by:", ["Most Recent", "Most Viewed", "Most Helpful", "Title (A-Z)"])

        articles = kb.articles.copy()
        if sort_by == "Most Recent":
            articles.sort(key=lambda x: x['created_at'], reverse=True)
        elif sort_by == "Most Viewed":
            articles.sort(key=lambda x: x['views'], reverse=True)
        elif sort_by == "Most Helpful":
            articles.sort(key=lambda x: x['helpful_count'], reverse=True)
        else:  # Title (A-Z)
            articles.sort(key=lambda x: x['title'])

        for article in articles:
            with st.expander(f"📄 **{article['title']}** | Views: {article['views']} | Helpful: {article['helpful_count']}"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**Category:** {article['category']}")
                    if article.get('syndicator') and article['syndicator'] != "N/A":
                        st.markdown(f"**Syndicator:** {article['syndicator']}")
                    if article.get('provider') and article['provider'] != "N/A":
                        st.markdown(f"**Provider:** {article['provider']}")

                    st.markdown("---")
                    st.markdown(f"**Problem:** {article['problem']}")
                    st.markdown(f"**Solution:** {article['solution']}")

                    if article.get('steps'):
                        st.markdown("**Resolution Steps:**")
                        for i, step in enumerate(article['steps'], 1):
                            st.markdown(f"{i}. {step}")

                    if article.get('tags'):
                        st.markdown(f"**Tags:** {', '.join(article['tags'])}")

                with col2:
                    if st.button(f"👍 Mark Helpful", key=f"helpful_{article['id']}"):
                        kb.mark_helpful(article['id'])
                        st.success("Marked as helpful!")
                        st.rerun()

                    if st.button(f"👁️ View", key=f"view_{article['id']}"):
                        kb.increment_view(article['id'])
                        st.info("View counted!")
                        st.rerun()

                    st.caption(f"Created: {article['created_at'][:10]}")
                    if article.get('resolution_time'):
                        st.caption(f"Resolution: {article['resolution_time']}")

        # Export/Import functionality
        st.markdown("---")
        st.markdown("### 💾 Export/Import Knowledge Base")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Export KB to JSON"):
                json_export = kb.export_kb()
                st.download_button(
                    label="Download KB JSON",
                    data=json_export,
                    file_name=f"kb_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

        with col2:
            uploaded_file = st.file_uploader("📤 Import KB from JSON", type=["json"])
            if uploaded_file:
                try:
                    json_data = uploaded_file.read().decode("utf-8")
                    kb.import_kb(json_data)
                    st.success("✅ Knowledge base imported successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Import failed: {e}")

with tab4:
    st.header("🔍 Search & Match Similar Issues")
    st.markdown("Search the knowledge base and find similar articles for new tickets.")

    search_mode = st.radio("Search Mode:", ["Keyword Search", "Find Similar for Ticket"], horizontal=True)

    if search_mode == "Keyword Search":
        st.markdown("### 🔍 Search Knowledge Base")

        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input("Enter search keywords:", placeholder="e.g., Kijiji export not working")
        with col2:
            category_filter = st.selectbox("Filter by category:",
                                          ["All"] + list(set(a["category"] for a in st.session_state.knowledge_base.articles)))

        if search_query:
            category = None if category_filter == "All" else category_filter
            results = st.session_state.knowledge_base.search_articles(search_query, category)

            if results:
                st.success(f"✅ Found {len(results)} matching articles")

                for result in results[:10]:  # Top 10 results
                    relevance_emoji = "🔥" if result['relevance_score'] >= 15 else "🔸" if result['relevance_score'] >= 8 else "🔹"

                    with st.expander(f"{relevance_emoji} **{result['title']}** (Relevance: {result['relevance_score']})"):
                        st.markdown(f"**Category:** {result['category']}")
                        if result.get('syndicator', 'N/A') != 'N/A':
                            st.markdown(f"**Syndicator:** {result['syndicator']}")
                        if result.get('provider', 'N/A') != 'N/A':
                            st.markdown(f"**Provider:** {result['provider']}")

                        st.markdown("---")
                        st.markdown(f"**Problem:** {result['problem']}")
                        st.markdown(f"**Solution:** {result['solution']}")

                        if result.get('steps'):
                            st.markdown("**Steps:**")
                            for i, step in enumerate(result['steps'], 1):
                                st.markdown(f"{i}. {step}")

                        st.caption(f"Views: {result['views']} | Helpful: {result['helpful_count']}")
            else:
                st.warning("No matching articles found. Try different keywords.")

    else:  # Find Similar for Ticket
        st.markdown("### 🎯 Find Similar KB Articles for a Ticket")

        ticket_text = st.text_area("Enter ticket description:", height=150,
                                   placeholder="Paste the ticket content to find similar KB articles...")

        col1, col2, col3 = st.columns(3)
        with col1:
            category = st.selectbox("Category:",
                                   ["Syndicator Bug", "Import Issue", "Feature Request", "Configuration", "Other"])
        with col2:
            syndicator = st.selectbox("Syndicator (if applicable):",
                                     ["N/A", "Kijiji", "AutoTrader", "Facebook", "Trader", "Cars.com"])
        with col3:
            provider = st.selectbox("Provider (if applicable):",
                                   ["N/A", "PBS", "CDK", "DealerSocket", "VinSolutions"])

        if st.button("🔍 Find Similar Articles", type="primary") and ticket_text:
            classification = {
                "category": category,
                "syndicator": syndicator if syndicator != "N/A" else None,
                "provider": provider if provider != "N/A" else None
            }

            with st.spinner("Searching for similar articles..."):
                similar = st.session_state.knowledge_base.find_similar_articles(
                    ticket_text, classification, threshold=3
                )

            if similar:
                st.success(f"✅ Found {len(similar)} similar articles")

                for match in similar[:5]:  # Top 5 matches
                    article = match["article"]
                    confidence = match["confidence"]

                    confidence_emoji = "🎯" if confidence >= 70 else "🎲" if confidence >= 40 else "🎰"
                    confidence_color = "green" if confidence >= 70 else "orange" if confidence >= 40 else "red"

                    with st.expander(f"{confidence_emoji} **{article['title']}** | Confidence: {confidence}%",
                                    expanded=(confidence >= 70)):

                        # Confidence indicator
                        st.markdown(f"""
                        <div style="background: linear-gradient(90deg, {confidence_color} {confidence}%, #e0e0e0 {confidence}%);
                                   height: 10px; border-radius: 5px; margin-bottom: 1rem;"></div>
                        """, unsafe_allow_html=True)

                        st.markdown(f"**Similarity Score:** {match['similarity_score']}")

                        if match.get("matching_reasons"):
                            st.markdown("**Why this matches:**")
                            for reason in match["matching_reasons"]:
                                st.markdown(f"- {reason}")

                        st.markdown("---")
                        st.markdown(f"**Problem:** {article['problem']}")
                        st.markdown(f"**Solution:** {article['solution']}")

                        if article.get('steps'):
                            st.markdown("**Resolution Steps:**")
                            for i, step in enumerate(article['steps'], 1):
                                st.markdown(f"{i}. {step}")

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("👍 This helped", key=f"similar_helpful_{article['id']}"):
                                st.session_state.knowledge_base.mark_helpful(article['id'])
                                st.success("Thanks for the feedback!")
                        with col2:
                            st.caption(f"Category: {article['category']}")
                            st.caption(f"Views: {article['views']} | Helpful: {article['helpful_count']}")
            else:
                st.info("""
                No similar articles found. This might be a new type of issue.

                **Next steps:**
                1. Resolve the ticket manually
                2. Document the resolution
                3. Generate a KB article for future reference
                """)

with tab5:
    # Create and render the KB Browser
    # kb_browser = KBBrowser(st.session_state.knowledge_base)
    # kb_browser.render_browser()
    st.info("KB Browser functionality moved to main navigation. Use the sidebar to access KB Browser.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
    📚 Knowledge Base Builder | Built for Cars Commerce Hackathon Fall 2025
</div>
""", unsafe_allow_html=True)