"""
Analytics page for the Streamlit UI.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


def render_analytics_page(api_client):
    """
    Render the analytics page.
    
    Args:
        api_client: API client instance
    """
    st.title("📊 Analytics")
    st.markdown(
        """
        View performance metrics and statistics for the classifier.
        """
    )
    
    # Get metrics from API
    with st.spinner("Loading metrics..."):
        metrics, error = api_client.get_metrics()
    
    if error:
        st.error(f"Error loading metrics: {error}")
        return
    
    if not metrics:
        st.warning("No metrics data available")
        return
    
    # Create tabs for different analytics views
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Performance", "Trends", "Classifications"])
    
    with tab1:
        _render_overview_metrics(metrics)
    
    with tab2:
        _render_performance_metrics(metrics)
    
    with tab3:
        _render_trends_analysis(metrics)
    
    with tab4:
        _render_classification_analytics(api_client)


def _render_overview_metrics(metrics: Dict[str, Any]):
    """
    Render overview metrics section.
    
    Args:
        metrics: Metrics data from API
    """
    st.subheader("System Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        uptime_hours = metrics.get('uptime', 0) / 3600
        st.metric("Uptime", f"{uptime_hours:.1f} hours")
    
    with col2:
        processed = metrics.get('processed', 0)
        st.metric("Processed Tickets", f"{processed:,}")
    
    with col3:
        success_rate = metrics.get('success_rate', 0)
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    with col4:
        avg_time = metrics.get('avg_processing_time', 0)
        st.metric("Avg. Processing Time", f"{avg_time:.2f}s")
    
    # Status indicators
    st.subheader("System Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        active_workers = metrics.get('active_workers', 0)
        st.metric("Active Workers", active_workers)
        
        # Health indicator
        if active_workers > 0:
            st.success("🟢 System Operational")
        else:
            st.warning("🟡 No Active Workers")
    
    with col2:
        queue_size = metrics.get('queue_size', 0)
        st.metric("Queue Size", queue_size)
        
        if queue_size > 100:
            st.warning("⚠️ High Queue Load")
        elif queue_size > 50:
            st.info("📋 Moderate Queue Load")
        else:
            st.success("✅ Low Queue Load")
    
    with col3:
        # Calculate efficiency score
        if processed > 0 and uptime_hours > 0:
            efficiency = processed / uptime_hours
            st.metric("Tickets/Hour", f"{efficiency:.1f}")
        else:
            st.metric("Tickets/Hour", "N/A")


def _render_performance_metrics(metrics: Dict[str, Any]):
    """
    Render performance metrics section.
    
    Args:
        metrics: Metrics data from API
    """
    st.subheader("Performance Analysis")
    
    # Recent activity data
    activity_data = {
        "Period": ["Last Minute", "Last Hour", "Last Day"],
        "Classifications": [
            len(metrics.get('last_minute', {})),
            len(metrics.get('last_hour', {})),
            len(metrics.get('last_day', {}))
        ]
    }
    
    activity_df = pd.DataFrame(activity_data)
    
    # Create performance charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Activity chart
        fig_activity = px.bar(
            activity_df,
            x="Period",
            y="Classifications",
            title="Recent Activity",
            color="Classifications",
            color_continuous_scale="viridis"
        )
        fig_activity.update_layout(height=400)
        st.plotly_chart(fig_activity, use_container_width=True)
    
    with col2:
        # Success rate gauge
        success_rate = metrics.get('success_rate', 0)
        
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = success_rate,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Success Rate (%)"},
            delta = {'reference': 90},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_gauge.update_layout(height=400)
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    # Detailed activity breakdown
    st.subheader("Activity Breakdown")
    
    # Combine all activity periods
    all_activity = {}
    for period, data in [
        ("Last Minute", metrics.get('last_minute', {})),
        ("Last Hour", metrics.get('last_hour', {})),
        ("Last Day", metrics.get('last_day', {}))
    ]:
        for action, count in data.items():
            if action not in all_activity:
                all_activity[action] = {}
            all_activity[action][period] = count
    
    if all_activity:
        activity_breakdown_df = pd.DataFrame(all_activity).fillna(0).T
        st.dataframe(activity_breakdown_df, use_container_width=True)
    else:
        st.info("No recent activity data available")


def _render_trends_analysis(metrics: Dict[str, Any]):
    """
    Render trends analysis section.
    
    Args:
        metrics: Metrics data from API
    """
    st.subheader("Trend Analysis")
    
    # Mock trend data (in a real implementation, this would come from historical metrics)
    # Generate sample trend data for demonstration
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
    
    # Create sample data that shows realistic trends
    import numpy as np
    np.random.seed(42)  # For reproducible results
    
    base_volume = 50
    trend_data = {
        'Date': dates,
        'Classifications': np.random.poisson(base_volume, len(dates)) + np.sin(np.arange(len(dates)) * 0.2) * 10,
        'Success_Rate': np.random.normal(92, 5, len(dates)).clip(80, 100),
        'Avg_Processing_Time': np.random.normal(2.5, 0.5, len(dates)).clip(1, 5)
    }
    
    trend_df = pd.DataFrame(trend_data)
    
    # Volume trend
    st.subheader("Classification Volume Trend (30 Days)")
    fig_volume = px.line(
        trend_df,
        x='Date',
        y='Classifications',
        title='Daily Classifications',
        markers=True
    )
    fig_volume.update_layout(height=400)
    st.plotly_chart(fig_volume, use_container_width=True)
    
    # Multi-metric trend
    col1, col2 = st.columns(2)
    
    with col1:
        fig_success = px.line(
            trend_df,
            x='Date',
            y='Success_Rate',
            title='Success Rate Trend',
            markers=True,
            color_discrete_sequence=['green']
        )
        fig_success.update_layout(height=300)
        st.plotly_chart(fig_success, use_container_width=True)
    
    with col2:
        fig_time = px.line(
            trend_df,
            x='Date',
            y='Avg_Processing_Time',
            title='Avg Processing Time Trend',
            markers=True,
            color_discrete_sequence=['orange']
        )
        fig_time.update_layout(height=300)
        st.plotly_chart(fig_time, use_container_width=True)
    
    # Summary statistics
    st.subheader("30-Day Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_classifications = trend_df['Classifications'].sum()
        st.metric("Total Classifications", f"{total_classifications:,}")
    
    with col2:
        avg_daily = trend_df['Classifications'].mean()
        st.metric("Avg Daily Volume", f"{avg_daily:.1f}")
    
    with col3:
        avg_success_rate = trend_df['Success_Rate'].mean()
        st.metric("Avg Success Rate", f"{avg_success_rate:.1f}%")
    
    with col4:
        avg_processing_time = trend_df['Avg_Processing_Time'].mean()
        st.metric("Avg Processing Time", f"{avg_processing_time:.2f}s")


def _render_classification_analytics(api_client):
    """
    Render classification analytics section.
    
    Args:
        api_client: API client instance
    """
    st.subheader("Classification Analytics")
    
    # Note: In a real implementation, this would fetch classification data from the API
    # For now, we'll show what this section would contain
    
    st.info("📊 Classification breakdown analytics would be displayed here")
    
    # Mock data for demonstration (replace with real API call)
    # classification_data, error = api_client.get_classification_analytics()
    
    # Create sample classification distribution
    categories = [
        "Problem / Bug", "Product Activation — New Client", "Product Activation — Existing Client",
        "Product Cancellation", "General Question", "Analysis / Review", "Other"
    ]
    
    import numpy as np
    np.random.seed(42)
    category_counts = np.random.multinomial(1000, [0.3, 0.15, 0.15, 0.1, 0.15, 0.1, 0.05])
    
    category_data = {
        'Category': categories,
        'Count': category_counts
    }
    category_df = pd.DataFrame(category_data)
    
    # Category distribution
    col1, col2 = st.columns(2)
    
    with col1:
        fig_pie = px.pie(
            category_df,
            values='Count',
            names='Category',
            title='Classification Distribution by Category'
        )
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        fig_bar = px.bar(
            category_df.sort_values('Count', ascending=True),
            x='Count',
            y='Category',
            orientation='h',
            title='Classification Counts by Category'
        )
        fig_bar.update_layout(height=400)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Syndicator analytics
    st.subheader("Syndicator Distribution")
    
    syndicators = ["Kijiji", "AutoTrader", "Cars.com", "CarGurus", "Facebook", "Google", "Other"]
    syndicator_counts = np.random.multinomial(800, [0.25, 0.2, 0.15, 0.15, 0.1, 0.1, 0.05])
    
    syndicator_data = {
        'Syndicator': syndicators,
        'Count': syndicator_counts
    }
    syndicator_df = pd.DataFrame(syndicator_data)
    
    fig_syndicator = px.bar(
        syndicator_df.sort_values('Count', ascending=False),
        x='Syndicator',
        y='Count',
        title='Classifications by Syndicator',
        color='Count',
        color_continuous_scale='viridis'
    )
    fig_syndicator.update_layout(height=400)
    st.plotly_chart(fig_syndicator, use_container_width=True)
    
    # Top dealers
    st.subheader("Top Dealers by Classification Volume")
    
    # Mock dealer data
    dealers = [
        "Honda Downtown", "Toyota City", "Ford Central", "Mazda North",
        "Chevrolet West", "Nissan East", "Hyundai South", "Subaru Valley"
    ]
    dealer_counts = np.random.multinomial(500, [0.2, 0.18, 0.15, 0.12, 0.1, 0.1, 0.08, 0.07])
    
    dealer_data = {
        'Dealer': dealers,
        'Classifications': dealer_counts
    }
    dealer_df = pd.DataFrame(dealer_data).sort_values('Classifications', ascending=False)
    
    st.dataframe(dealer_df, use_container_width=True)
    
    # Language distribution
    st.subheader("Language Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        language_data = {
            'Language': ['English', 'French'],
            'Count': [750, 250]
        }
        language_df = pd.DataFrame(language_data)
        
        fig_lang = px.pie(
            language_df,
            values='Count',
            names='Language',
            title='Ticket Language Distribution'
        )
        st.plotly_chart(fig_lang, use_container_width=True)
    
    with col2:
        # Confidence score distribution
        confidence_scores = np.random.beta(8, 2, 1000) * 100  # Beta distribution for realistic confidence scores
        
        fig_confidence = px.histogram(
            x=confidence_scores,
            nbins=20,
            title='Classification Confidence Score Distribution',
            labels={'x': 'Confidence Score (%)', 'y': 'Count'}
        )
        st.plotly_chart(fig_confidence, use_container_width=True)


def _create_sample_trend_data(days: int = 30) -> pd.DataFrame:
    """
    Create sample trend data for demonstration.
    
    Args:
        days: Number of days of data to generate
        
    Returns:
        DataFrame with sample trend data
    """
    import numpy as np
    
    dates = pd.date_range(start=datetime.now() - timedelta(days=days), end=datetime.now(), freq='D')
    
    # Create realistic patterns
    base_volume = 50
    weekly_pattern = np.sin(np.arange(len(dates)) * 2 * np.pi / 7) * 15  # Weekly pattern
    trend = np.linspace(0, 10, len(dates))  # Slight upward trend
    noise = np.random.normal(0, 5, len(dates))  # Random variation
    
    classifications = (base_volume + weekly_pattern + trend + noise).clip(0, None).astype(int)
    
    # Success rate with slight correlation to volume (busy days might have slightly lower success rates)
    base_success = 92
    volume_effect = -(classifications - base_volume) * 0.1  # Higher volume slightly reduces success rate
    success_noise = np.random.normal(0, 2, len(dates))
    success_rate = (base_success + volume_effect + success_noise).clip(80, 100)
    
    # Processing time inversely correlated with success rate
    base_time = 2.5
    success_effect = (100 - success_rate) * 0.02  # Lower success rate means longer processing time
    time_noise = np.random.normal(0, 0.3, len(dates))
    processing_time = (base_time + success_effect + time_noise).clip(1, 6)
    
    return pd.DataFrame({
        'Date': dates,
        'Classifications': classifications,
        'Success_Rate': success_rate,
        'Avg_Processing_Time': processing_time
    })