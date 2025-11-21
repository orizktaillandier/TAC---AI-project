"""
Gap Analysis Dashboard
Visualizes knowledge gaps and search analytics
"""

import streamlit as st
import pandas as pd
from gap_analysis import GapAnalyzer
from knowledge_base import KnowledgeBase

def main():
    """Main gap analysis dashboard"""
    st.set_page_config(
        page_title="KB Gap Analysis",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Knowledge Base Gap Analysis")
    st.markdown("Identify knowledge gaps and improve KB coverage")
    st.markdown("---")
    
    # Initialize
    gap_analyzer = GapAnalyzer()
    kb = KnowledgeBase()
    
    # Sidebar filters
    with st.sidebar:
        st.header("Filters")
        days = st.slider("Analysis Period (days)", 1, 90, 30)
        st.markdown("---")
        
        # Cache stats
        if st.button("🔄 Refresh Data"):
            st.rerun()
    
    # Main content
    col1, col2, col3, col4 = st.columns(4)
    
    # Get analytics
    analytics = gap_analyzer.get_search_analytics(days=days)
    
    with col1:
        st.metric("Total Searches", analytics['total_searches'])
    
    with col2:
        st.metric("Success Rate", f"{analytics['success_rate']}%")
    
    with col3:
        st.metric("Failed Searches", analytics['failed_searches'])
    
    with col4:
        st.metric("Avg Results/Search", f"{analytics['avg_results_per_search']:.1f}")
    
    st.markdown("---")
    
    # Knowledge Gaps Section
    st.subheader("🔍 Knowledge Gaps (Failed Searches)")
    
    gaps = analytics['knowledge_gaps']
    
    if gaps:
        # Create DataFrame for display
        gaps_df = pd.DataFrame(gaps)
        
        # Priority color coding
        def color_priority(val):
            if val == 'high':
                return 'background-color: #ffebee'
            elif val == 'medium':
                return 'background-color: #fff3e0'
            else:
                return 'background-color: #e8f5e9'
        
        # Display table
        st.dataframe(
            gaps_df[['query', 'frequency', 'priority', 'first_seen', 'last_seen']].style.applymap(
                color_priority, subset=['priority']
            ),
            use_container_width=True,
            hide_index=True
        )
        
        # Show top gap details
        if st.expander("📝 View Top Gap Details"):
            for i, gap in enumerate(gaps[:5], 1):
                st.markdown(f"### Gap #{i}: {gap['query']}")
                st.write(f"**Frequency:** {gap['frequency']} times")
                st.write(f"**Priority:** {gap['priority']}")
                st.write(f"**First Seen:** {gap['first_seen']}")
                st.write(f"**Last Seen:** {gap['last_seen']}")
                if gap.get('classifications'):
                    st.write(f"**Related Categories:** {', '.join(set(gap['classifications']))}")
                st.markdown("---")
    else:
        st.info("✅ No knowledge gaps found! All searches are finding results.")
    
    st.markdown("---")
    
    # Most Searched Topics
    st.subheader("🔎 Most Searched Topics")
    
    most_searched = analytics['most_searched']
    if most_searched:
        searched_df = pd.DataFrame(most_searched)
        st.bar_chart(searched_df.set_index('query')['count'])
        st.dataframe(searched_df, use_container_width=True, hide_index=True)
    else:
        st.info("No search data available yet.")
    
    st.markdown("---")
    
    # Trends Section
    st.subheader("📈 Search Trends")
    
    trends = gap_analyzer.get_trends(days=min(days, 30))
    
    if trends['daily_trends']:
        trends_df = pd.DataFrame(trends['daily_trends'])
        trends_df['date'] = pd.to_datetime(trends_df['date'])
        trends_df = trends_df.set_index('date')
        
        # Line chart
        st.line_chart(trends_df[['total', 'successful', 'failed']])
        
        # Success rate chart
        st.line_chart(trends_df[['success_rate']])
    else:
        st.info("No trend data available yet.")
    
    st.markdown("---")
    
    # Recommendations
    st.subheader("💡 Recommendations")
    
    if gaps:
        high_priority_gaps = [g for g in gaps if g['priority'] == 'high']
        if high_priority_gaps:
            st.warning(f"⚠️ **{len(high_priority_gaps)} high-priority gaps** detected. Consider creating KB articles for these topics.")
            for gap in high_priority_gaps[:3]:
                st.write(f"- **{gap['query']}** (searched {gap['frequency']} times)")
        else:
            st.success("✅ No high-priority gaps. KB coverage is good!")
    else:
        st.success("✅ Excellent! No knowledge gaps detected.")

if __name__ == "__main__":
    main()

