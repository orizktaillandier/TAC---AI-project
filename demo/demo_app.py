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

load_dotenv()

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
    # Custom CSS
    st.markdown("""
    <style>
        .main {
            padding: 1rem;
        }
        .stButton>button {
            width: 100%;
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

    # Header
    st.title("🎯 AI-Powered Ticket Classifier")
    st.markdown("### Intelligent Support Ticket Classification")

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

    # Main content
    st.header("Classify a Support Ticket")

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

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Ticket Input")

        input_method = st.radio(
            "Input Method:",
            ["Direct Text Input", "Load Sample Ticket"],
            horizontal=True
        )

        if input_method == "Load Sample Ticket":
            if st.session_state.mock_tickets:
                ticket_options = [
                    f"{t['ticket_id']} - {t['subject'][:50]}..."
                    for t in st.session_state.mock_tickets
                ]
                selected = st.selectbox("Select a sample ticket:", ticket_options)

                if selected:
                    idx = int(selected.split(" - ")[0]) - 12345
                    if 0 <= idx < len(st.session_state.mock_tickets):
                        ticket = st.session_state.mock_tickets[idx]
                        ticket_subject = st.text_input("Subject:", value=ticket["subject"])
                        ticket_text = st.text_area(
                            "Ticket Content:",
                            value=ticket["description"],
                            height=200
                        )
                    else:
                        ticket_subject = st.text_input("Subject:")
                        ticket_text = st.text_area("Ticket Content:", height=200)
            else:
                st.warning("No sample tickets available")
                ticket_subject = st.text_input("Subject:")
                ticket_text = st.text_area("Ticket Content:", height=200)
        else:
            ticket_subject = st.text_input("Subject:")
            ticket_text = st.text_area(
                "Ticket Content:",
                placeholder="Paste ticket content here...",
                height=200
            )

        classify_button = st.button("🚀 Classify with AI", type="primary")

    with col2:
        st.subheader("GPT-5 Powered")
        st.info("""
        This classifier uses **GPT-5-mini** to:

        - Extract key information
        - Classify tickets accurately
        - Determine priority tiers
        - Identify syndicators/providers
        """)

    # Classification logic
    if classify_button:
        if not ticket_text.strip():
            st.error("Please enter ticket content")
        else:
            with st.spinner("Classifying ticket..."):
                result = st.session_state.classifier.classify(ticket_text, ticket_subject)

                if result.get("success"):
                    st.success("✅ Classification Complete!")

                    classification = result["classification"]
                    entities = result.get("entities", {})
                    suggested_response = result.get("suggested_response", "")

                    # Display classification results
                    st.markdown("---")
                    st.subheader("📋 Classification Results")
                    st.markdown("**All 10 Extracted Fields:**")

                    # Row 1: Main Classification
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Category", classification.get("category", "N/A"))
                    with col2:
                        st.metric("Sub-Category", classification.get("sub_category", "N/A"))
                    with col3:
                        st.metric("Tier", classification.get("tier", "N/A"))
                    with col4:
                        st.metric("Inventory Type", classification.get("inventory_type", "N/A"))

                    # Row 2: Dealer Information
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Contact", classification.get("contact", "N/A"))
                    with col2:
                        st.metric("Dealer Name", classification.get("dealer_name", "N/A"))
                    with col3:
                        st.metric("Dealer ID", classification.get("dealer_id", "N/A"))
                    with col4:
                        st.metric("Rep", classification.get("rep", "N/A"))

                    # Row 3: Integration
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Syndicator", classification.get("syndicator", "N/A") or "N/A")
                    with col2:
                        st.metric("Provider", classification.get("provider", "N/A") or "N/A")

                    # Sentiment Analysis Display
                    sentiment = result.get("sentiment", {})
                    if sentiment:
                        st.markdown("---")
                        st.markdown("### 💭 Sentiment & Urgency Analysis")

                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            sentiment_label = sentiment.get("label", "Neutral")
                            sentiment_score = sentiment.get("score", 0)

                            # Color-coded sentiment badge
                            if sentiment_score > 20:
                                st.success(f"🟢 {sentiment_label} (+{sentiment_score})")
                            elif sentiment_score < -20:
                                st.error(f"🔴 {sentiment_label} ({sentiment_score})")
                            else:
                                st.info(f"🟡 {sentiment_label} ({sentiment_score})")

                        with col2:
                            urgency = sentiment.get("urgency_level", "Medium")
                            urgency_icons = {
                                "Critical": "⚡",
                                "High": "🔥",
                                "Medium": "⚠️",
                                "Low": "📋"
                            }
                            icon = urgency_icons.get(urgency, "📋")
                            if urgency in ["Critical", "High"]:
                                st.warning(f"{icon} Urgency: {urgency}")
                            else:
                                st.metric("Urgency", f"{icon} {urgency}")

                        with col3:
                            escalation_risk = sentiment.get("escalation_risk", "Low")
                            if escalation_risk in ["High", "Critical"]:
                                st.error(f"⚠️ Risk: {escalation_risk}")
                            elif escalation_risk == "Medium":
                                st.warning(f"⚠️ Risk: {escalation_risk}")
                            else:
                                st.success(f"✅ Risk: {escalation_risk}")

                        with col4:
                            flags = sentiment.get("flags", [])
                            if flags:
                                st.metric("Flags", len(flags))
                            else:
                                st.metric("Flags", "None")

                        # Show flags and recommendations if present
                        if flags:
                            with st.expander("🚩 Alert Flags", expanded=True):
                                for flag in flags:
                                    if "CRITICAL" in flag:
                                        st.error(f"• {flag}")
                                    elif "HIGH" in flag or "EXECUTIVE" in flag:
                                        st.warning(f"• {flag}")
                                    else:
                                        st.info(f"• {flag}")

                        recommendations = sentiment.get("recommendations", [])
                        if recommendations:
                            with st.expander("💡 Recommended Actions"):
                                for rec in recommendations:
                                    st.markdown(f"• {rec}")

                    # Entities (additional context)
                    if entities:
                        with st.expander("🔍 Extracted Entities & Context"):
                            st.json(entities)

                    # Suggested response
                    if suggested_response:
                        with st.expander("💬 AI Suggested Response"):
                            st.markdown(suggested_response)

                    # ========== STEP 2: KB SEARCH & RESOLUTION ==========
                    st.markdown("---")
                    st.subheader("🎯 Step 2: Resolution from Knowledge Base")

                    if st.session_state.kb_ready:
                        with st.spinner("Searching Knowledge Base for relevant solutions..."):
                            # Search KB using classification
                            kb_results = st.session_state.kb.search_articles(
                                query=ticket_text,
                                classification=classification
                            )

                            if kb_results:
                                # Check if confidence is low (KB gap detected)
                                best_confidence = kb_results[0]['confidence'] if kb_results else 0
                                if best_confidence < 50:
                                    st.warning(f"🔍 **KB Coverage Gap Detected!** Best match confidence is only {best_confidence}%. This ticket type may need a new KB article.")

                                st.success(f"✅ Found {len(kb_results)} relevant KB articles")

                                # Show top 3 results
                                st.markdown("**Top Matching Articles:**")
                                for i, result in enumerate(kb_results[:3], 1):
                                    article = result['article']
                                    confidence = result['confidence']
                                    col1, col2 = st.columns([3, 1])
                                    with col1:
                                        st.markdown(f"{i}. **{article.get('title', 'Untitled')}**")
                                    with col2:
                                        st.markdown(f"*Confidence: {confidence}%*")

                                st.markdown("---")

                                # Use AI to analyze and select best article
                                with st.spinner("AI is analyzing the best solution for this ticket..."):
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

    For example, if KB says "Visit client page", adapt it to "Visit Dealership_3 page" (using actual dealer name).

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

                                        # Display AI analysis
                                        st.success("✅ AI Analysis Complete!")

                                        # Show selected article
                                        selected_idx = ai_analysis.get("selected_article_id", 1) - 1
                                        if selected_idx >= 0 and selected_idx < len(top_articles):
                                            selected_article = top_articles[selected_idx]['article']
                                            st.info(f"**Selected Solution:** {selected_article.get('title')}")

                                        # Show confidence
                                        confidence = ai_analysis.get("confidence", 0)
                                        confidence_color = "🟢" if confidence >= 80 else "🟡" if confidence >= 60 else "🔴"
                                        st.metric("AI Confidence", f"{confidence_color} {confidence}%")

                                        # Show edge cases if detected
                                        edge_cases = ai_analysis.get("edge_cases_detected", [])
                                        if edge_cases:
                                            st.warning("⚠️ **Edge Cases Detected:**")
                                            for edge_case in edge_cases:
                                                st.markdown(f"- {edge_case}")

                                        # Show resolution steps
                                        st.markdown("### 📋 Resolution Steps for Agent")
                                        resolution_steps = ai_analysis.get("resolution_steps", [])
                                        for i, step in enumerate(resolution_steps, 1):
                                            st.markdown(f"**{i}.** {step}")

                                        # Show additional notes
                                        notes = ai_analysis.get("additional_notes", "")
                                        if notes:
                                            st.info(f"**💡 Note:** {notes}")

                                        # Show reasoning in expander
                                        reasoning = ai_analysis.get("reasoning", "")
                                        if reasoning:
                                            with st.expander("🧠 AI Reasoning"):
                                                st.markdown(reasoning)

                                        # Quick feedback: Thumbs Up/Down
                                        st.markdown("---")
                                        st.markdown("**Quick Feedback: Was this KB article helpful?**")
                                        col1, col2, col3 = st.columns([1, 1, 4])

                                        # Get the actual article ID from the selected index
                                        selected_index = ai_analysis.get("selected_article_id", 1) - 1  # Convert to 0-based index
                                        selected_article_id = None
                                        if 0 <= selected_index < len(top_articles):
                                            selected_article_id = top_articles[selected_index]['article'].get('id')
                                        with col1:
                                            if st.button("👍 Helpful", key=f"upvote_{selected_article_id}", use_container_width=True):
                                                if st.session_state.kb.vote_article(selected_article_id, 'up'):
                                                    st.success("Thanks for the feedback!")
                                                    st.rerun()

                                        with col2:
                                            if st.button("👎 Not Helpful", key=f"downvote_{selected_article_id}", use_container_width=True):
                                                if st.session_state.kb.vote_article(selected_article_id, 'down'):
                                                    st.info("Feedback recorded. Please provide details in Step 3 below.")
                                                    st.rerun()

                                        # Show current vote score
                                        article = st.session_state.kb.get_article(selected_article_id)
                                        if article:
                                            upvotes = article.get('upvotes', 0)
                                            downvotes = article.get('downvotes', 0)
                                            vote_score = article.get('vote_score', 0)
                                            if upvotes + downvotes > 0:
                                                with col3:
                                                    st.caption(f"📊 Score: {vote_score} ({upvotes}👍 / {downvotes}👎)")

                                        # Get the actual article ID from the selected index
                                        selected_index = ai_analysis.get("selected_article_id", 1) - 1  # Convert to 0-based index
                                        actual_article_id = None
                                        if 0 <= selected_index < len(top_articles):
                                            actual_article_id = top_articles[selected_index]['article'].get('id')

                                        # Cache resolution data for Step 3
                                        st.session_state.current_resolution = {
                                            "steps": resolution_steps,
                                            "selected_article_id": actual_article_id,
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
                                        st.markdown(f"**Problem:** {best_article.get('problem')}")
                                        st.markdown(f"**Solution:** {best_article.get('solution')}")
                                        st.markdown("**Steps:**")
                                        for i, step in enumerate(best_article.get('steps', []), 1):
                                            st.markdown(f"{i}. {step}")
                            else:
                                st.warning("⚠️ No matching KB articles found. This may require manual handling.")
                                st.info("💡 This ticket might be a new type of issue that should be added to the KB after resolution.")
                    else:
                        st.error(f"⚠️ Knowledge Base not ready: {st.session_state.get('kb_error', 'Unknown error')}")

                else:
                    st.error(f"❌ Classification failed: {result.get('error', 'Unknown error')}")

    # ========== STEP 3: FEEDBACK & KB LEARNING ==========
    # This is OUTSIDE the classify_button block so form submissions work
    st.markdown("---")
    st.subheader("🎓 Step 3: KB Learning & Feedback")

    st.write(f"DEBUG: current_ticket_data exists = {st.session_state.current_ticket_data is not None}")

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
            st.write(f"DEBUG: submit_feedback={submit_feedback}, resolution_failed={resolution_failed}, actual_solution length={len(actual_solution.strip())}")
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
