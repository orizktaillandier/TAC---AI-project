"""
KB Agent Chat - Conversational AI Interface for Knowledge Base Management
Natural language interface for creating, updating, deleting, and browsing KB articles
"""

import streamlit as st
import json
import os
import logging
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from knowledge_base import KnowledgeBase

load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# KB Agent Tools/Functions
KB_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_kb",
            "description": "Search knowledge base articles by query, category, syndicator, provider, or other filters",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query text"
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by category (e.g., 'Syndicator Bug', 'Data Provider Issue')"
                    },
                    "syndicator": {
                        "type": "string",
                        "description": "Filter by syndicator name"
                    },
                    "provider": {
                        "type": "string",
                        "description": "Filter by provider name"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_article",
            "description": "Get full details of a specific KB article by ID to display in preview panel",
            "parameters": {
                "type": "object",
                "properties": {
                    "article_id": {
                        "type": "integer",
                        "description": "The ID of the article to retrieve"
                    }
                },
                "required": ["article_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_article",
            "description": "Create a new KB article with the provided information",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Article title"},
                    "problem": {"type": "string", "description": "Problem description"},
                    "solution": {"type": "string", "description": "Solution description"},
                    "steps": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Step-by-step resolution instructions"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for categorization"
                    },
                    "category": {"type": "string", "description": "Main category"},
                    "syndicator": {"type": "string", "description": "Related syndicator (or empty string)"},
                    "provider": {"type": "string", "description": "Related provider (or empty string)"}
                },
                "required": ["title", "problem", "solution", "steps", "category"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_article",
            "description": "Update an existing KB article with new information",
            "parameters": {
                "type": "object",
                "properties": {
                    "article_id": {
                        "type": "integer",
                        "description": "The ID of the article to update"
                    },
                    "updates": {
                        "type": "object",
                        "description": "Fields to update (can include title, problem, solution, steps, tags, etc.)"
                    },
                    "change_reason": {
                        "type": "string",
                        "description": "Reason for the update"
                    }
                },
                "required": ["article_id", "updates"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_article",
            "description": "Delete a KB article. ONLY call this after user explicitly confirms deletion with 'yes', 'confirm', or similar affirmative response.",
            "parameters": {
                "type": "object",
                "properties": {
                    "article_id": {
                        "type": "integer",
                        "description": "The ID of the article to delete"
                    }
                },
                "required": ["article_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_kb_stats",
            "description": "Get knowledge base statistics and analytics",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_low_performers": {
                        "type": "boolean",
                        "description": "Include list of low-performing articles"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_articles",
            "description": "List all KB articles with optional filters",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Filter by category"},
                    "syndicator": {"type": "string", "description": "Filter by syndicator"},
                    "provider": {"type": "string", "description": "Filter by provider"},
                    "limit": {"type": "integer", "description": "Maximum number of articles to return"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_articles",
            "description": "Get top N most-used articles sorted by usage_count. Use this for queries like 'most used', 'top 5', 'highest usage', etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of top articles to return (default: 5)"
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["usage_count", "success_rate", "views"],
                        "description": "Metric to sort by (default: usage_count)"
                    }
                }
            }
        }
    }
]


def execute_kb_function(function_name, arguments, kb):
    """Execute KB operations based on function calls"""
    args = json.loads(arguments) if isinstance(arguments, str) else arguments

    if function_name == "search_kb":
        query = args.get("query", "")
        classification = {
            "category": args.get("category", ""),
            "syndicator": args.get("syndicator", ""),
            "provider": args.get("provider", "")
        }
        results = kb.search_articles(query, classification)
        return {
            "success": True,
            "results": [{
                "id": r["article"]["id"],
                "title": r["article"]["title"],
                "category": r["article"].get("category", ""),
                "score": r["score"],
                "confidence": r["confidence"]
            } for r in results[:10]]  # Return top 10
        }

    elif function_name == "get_article":
        article_id = args["article_id"]
        article = kb.get_article(article_id)
        if article:
            # Update preview panel in session state
            st.session_state.preview_article = article
            return {"success": True, "article": article}
        return {"success": False, "error": f"Article {article_id} not found"}

    elif function_name == "create_article":
        # Set defaults for optional fields
        article_data = {
            "title": args["title"],
            "problem": args["problem"],
            "solution": args["solution"],
            "steps": args["steps"],
            "tags": args.get("tags", []),
            "category": args["category"],
            "syndicator": args.get("syndicator", ""),
            "provider": args.get("provider", "")
        }
        article_id = kb.add_article(article_data)
        return {"success": True, "article_id": article_id, "message": f"Created article #{article_id}"}

    elif function_name == "update_article":
        article_id = args["article_id"]
        updates = args["updates"]
        change_reason = args.get("change_reason", "Updated via KB Agent Chat")
        success = kb.update_article(article_id, updates, change_reason)
        if success:
            return {"success": True, "message": f"Updated article #{article_id}"}
        return {"success": False, "error": f"Failed to update article #{article_id}"}

    elif function_name == "delete_article":
        article_id = args["article_id"]
        success = kb.delete_article(article_id)
        if success:
            return {"success": True, "message": f"Deleted article #{article_id}"}
        return {"success": False, "error": f"Failed to delete article #{article_id}"}

    elif function_name == "get_kb_stats":
        stats = kb.get_stats()
        result = {
            "total_articles": stats["total_articles"],
            "total_usage": stats["total_usage"],
            "avg_success_rate": stats["avg_success_rate"],
            "articles_by_category": stats["articles_by_category"]
        }
        if args.get("include_low_performers"):
            result["low_performers"] = stats.get("low_performing_articles", [])
        return {"success": True, "stats": result}

    elif function_name == "list_articles":
        all_articles = kb.articles
        filtered = all_articles

        # Apply filters
        if args.get("category"):
            filtered = [a for a in filtered if a.get("category") == args["category"]]
        if args.get("syndicator"):
            filtered = [a for a in filtered if a.get("syndicator") == args["syndicator"]]
        if args.get("provider"):
            filtered = [a for a in filtered if a.get("provider") == args["provider"]]

        limit = args.get("limit", 20)
        filtered = filtered[:limit]

        return {
            "success": True,
            "articles": [{
                "id": a["id"],
                "title": a["title"],
                "category": a.get("category", ""),
                "syndicator": a.get("syndicator", ""),
                "provider": a.get("provider", "")
            } for a in filtered]
        }

    elif function_name == "get_top_articles":
        all_articles = kb.articles
        limit = args.get("limit", 5)
        sort_by = args.get("sort_by", "usage_count")

        # Sort by the specified metric (descending)
        sorted_articles = sorted(
            all_articles,
            key=lambda a: a.get(sort_by, 0),
            reverse=True
        )[:limit]

        return {
            "success": True,
            "articles": [{
                "id": a["id"],
                "title": a["title"],
                "category": a.get("category", ""),
                "usage_count": a.get("usage_count", 0),
                "success_rate": a.get("success_rate", 0),
                "views": a.get("views", 0)
            } for a in sorted_articles]
        }

    return {"success": False, "error": f"Unknown function: {function_name}"}


def _format_tools_for_responses_api(tools):
    """Transform tools format for Responses API compatibility"""
    # Responses API expects tools with type and name at top level
    formatted_tools = []
    for tool in tools:
        if "function" in tool:
            func_def = tool["function"]
            formatted_tool = {
                "type": tool.get("type", "function"),  # Include type
                "name": func_def.get("name"),
                "description": func_def.get("description"),
                "parameters": func_def.get("parameters", {})
            }
            formatted_tools.append(formatted_tool)
        else:
            # Already in correct format, but ensure type is present
            if "type" not in tool:
                tool["type"] = "function"
            formatted_tools.append(tool)
    return formatted_tools


def chat_with_agent(user_message, conversation_history, kb, client):
    """Send message to AI agent and handle function calls using Responses API for GPT-5"""

    # Build context from conversation history
    system_prompt = conversation_history[0]["content"]  # System message

    # Build conversation context as text (Responses API uses 'input' not 'messages')
    context_parts = [system_prompt]
    for msg in conversation_history[1:]:  # Skip system message
        if msg["role"] == "user":
            context_parts.append(f"User: {msg['content']}")
        elif msg["role"] == "assistant":
            context_parts.append(f"Assistant: {msg['content']}")

    # Add current user message
    context_parts.append(f"User: {user_message}")
    full_input = "\n\n".join(context_parts)

    # Format tools for Responses API
    formatted_tools = _format_tools_for_responses_api(KB_TOOLS)

    # Call AI with Responses API (GPT-5)
    try:
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
            input=full_input,
            reasoning={"effort": os.getenv("OPENAI_REASONING_EFFORT", "low")},
            tools=formatted_tools
        )
    except Exception as e:
        logger.error(f"API call failed: {str(e)}")
        raise Exception(f"Failed to communicate with OpenAI API: {str(e)}. Please check your API key and internet connection.")

    # Handle function calls
    if hasattr(response, 'tool_calls') and response.tool_calls:
        # Execute all function calls
        tool_results_text = []
        for tool_call in response.tool_calls:
            function_name = tool_call.function.name
            function_args = tool_call.function.arguments

            # Execute the function
            function_result = execute_kb_function(function_name, function_args, kb)
            tool_results_text.append(f"Tool '{function_name}' returned: {json.dumps(function_result)}")

        # Get final response after tool execution
        final_input = full_input + "\n\nTool Results:\n" + "\n".join(tool_results_text)
        try:
            final_response = client.responses.create(
                model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
                input=final_input,
                reasoning={"effort": os.getenv("OPENAI_REASONING_EFFORT", "low")},
                previous_response_id=response.id,  # Pass CoT from previous turn
                tools=formatted_tools  # Include tools in final response too
            )
        except Exception as e:
            logger.error(f"Final response API call failed: {str(e)}")
            # Fallback: return a message based on the tool results
            response_text = f"I've executed the requested action. {tool_results_text[0] if tool_results_text else 'Action completed.'}"
            conversation_history.append({"role": "user", "content": user_message})
            conversation_history.append({"role": "assistant", "content": response_text})
            return response_text

        # Extract response text safely - try multiple attributes
        response_text = None
        if hasattr(final_response, 'output_text'):
            response_text = final_response.output_text
        elif hasattr(final_response, 'text'):
            response_text = final_response.text
        elif hasattr(final_response, 'content'):
            response_text = final_response.content
        else:
            # Last resort: convert to string
            response_text = str(final_response)
            logger.warning(f"Response object structure unexpected. Available attributes: {dir(final_response)}")
        
        if not response_text or response_text.strip() == "":
            response_text = "I've completed the requested action. Is there anything else you'd like to know?"

        # Add to conversation history
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": response_text})

        return response_text
    else:
        # No function calls, just return the message
        # Extract response text safely
        response_text = getattr(response, 'output_text', None) or getattr(response, 'text', None) or str(response)
        if not response_text or response_text.strip() == "":
            response_text = "I'm here to help! What would you like to know about the knowledge base?"

        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": response_text})

        return response_text


def main():
    """Main KB Agent Chat interface"""

    # Custom CSS for chat interface
    st.markdown("""
    <style>
        /* Chat layout */
        .chat-container {
            background-color: #1E293B;
            border-radius: 8px;
            padding: 1rem;
            height: 500px;
            overflow-y: auto;
            margin-bottom: 1rem;
        }

        .chat-message {
            margin-bottom: 1rem;
            padding: 0.75rem;
            border-radius: 8px;
        }

        .user-message {
            background-color: #4A90E2;
            color: white;
            margin-left: 20%;
        }

        .assistant-message {
            background-color: #334155;
            color: #E2E8F0;
            margin-right: 20%;
        }

        .article-preview {
            background-color: #334155;
            border: 1px solid #475569;
            border-radius: 8px;
            padding: 1.5rem;
            height: 600px;
            overflow-y: auto;
        }

        .article-preview h3 {
            color: #60A5FA;
            margin-bottom: 1rem;
        }

        .article-section {
            margin-bottom: 1.5rem;
        }

        .article-section-title {
            color: #94A3B8;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        }

        .article-section-content {
            color: #E2E8F0;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("## 🤖 KB Agent Chat")
    st.markdown("*Conversational AI interface for managing your knowledge base*")
    st.markdown("---")

    # Initialize session state
    if "kb_agent" not in st.session_state:
        st.session_state.kb_agent = KnowledgeBase()

    if "agent_client" not in st.session_state:
        st.session_state.agent_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = [
            {
                "role": "system",
                "content": """You are a direct, efficient KB management assistant.

IMPORTANT RULES:
1. Make reasonable assumptions - don't ask unnecessary clarifying questions
2. Just execute the request and show results immediately
3. Only ask questions if absolutely critical information is missing
4. When user asks for "most used" or "top N", immediately call the function and show results
5. For deletions, ALWAYS ask for explicit confirmation and show what will be deleted
6. Be concise - no unnecessary explanations

Examples of good responses:
- "which article is most used?" → Immediately show the top article(s) by usage_count
- "show top 5" → Immediately show top 5 articles sorted by usage
- "create article about X" → Ask for problem, solution, steps (only essential info)

Examples of bad responses (avoid these):
- Asking "do you mean A or B?" when the answer is obvious
- Asking for clarification on things you can infer from context
- Explaining what you're about to do instead of just doing it

When displaying search results or lists, show article IDs, titles, and key metrics clearly formatted."""
            }
        ]

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    if "preview_article" not in st.session_state:
        st.session_state.preview_article = None

    # Layout: Chat (left) + Preview (right)
    col_chat, col_preview = st.columns([65, 35])

    with col_chat:
        st.markdown("### 💬 Chat")

        # Chat display area - use Streamlit's native chat messages
        for msg in st.session_state.chat_messages:
            role = msg["role"]
            content = msg["content"]

            if role == "user":
                with st.chat_message("user"):
                    st.markdown(content)
            else:
                with st.chat_message("assistant"):
                    st.markdown(content)

        # Chat input
        user_input = st.chat_input("Ask me anything about the KB...")

        if user_input:
            # Add user message to display
            st.session_state.chat_messages.append({
                "role": "user",
                "content": user_input
            })

            # Get AI response
            with st.spinner("Agent is thinking..."):
                try:
                    response = chat_with_agent(
                        user_input,
                        st.session_state.conversation_history,
                        st.session_state.kb_agent,
                        st.session_state.agent_client
                    )

                    # Ensure response is not empty
                    if not response or response.strip() == "":
                        response = "I apologize, but I didn't receive a response. Please try again or rephrase your question."

                    # Add assistant response to display
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": response
                    })

                    st.rerun()
                except Exception as e:
                    error_msg = f"Error communicating with AI agent: {str(e)}"
                    st.error(error_msg)
                    # Add error to chat for visibility
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": f"❌ {error_msg}\n\nPlease check:\n- Your OpenAI API key is set correctly in .env\n- You have API credits available\n- Your internet connection is stable"
                    })
                    st.rerun()

    with col_preview:
        st.markdown("### 📄 Article Preview")

        if st.session_state.preview_article:
            article = st.session_state.preview_article

            st.markdown(f"""
            <div class="article-preview">
                <h3>{article.get('title', 'Untitled')}</h3>

                <div class="article-section">
                    <div class="article-section-title">ID</div>
                    <div class="article-section-content">#{article.get('id', 'N/A')}</div>
                </div>

                <div class="article-section">
                    <div class="article-section-title">Category</div>
                    <div class="article-section-content">{article.get('category', 'N/A')}</div>
                </div>

                <div class="article-section">
                    <div class="article-section-title">Problem</div>
                    <div class="article-section-content">{article.get('problem', 'N/A')}</div>
                </div>

                <div class="article-section">
                    <div class="article-section-title">Solution</div>
                    <div class="article-section-content">{article.get('solution', 'N/A')}</div>
                </div>

                <div class="article-section">
                    <div class="article-section-title">Steps</div>
                    <div class="article-section-content">
                        {'<br>'.join([f"{i+1}. {step}" for i, step in enumerate(article.get('steps', []))])}
                    </div>
                </div>

                <div class="article-section">
                    <div class="article-section-title">Stats</div>
                    <div class="article-section-content">
                        Success Rate: {article.get('success_rate', 0):.0%}<br>
                        Usage Count: {article.get('usage_count', 0)}<br>
                        Views: {article.get('views', 0)}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Clear Preview"):
                st.session_state.preview_article = None
                st.rerun()
        else:
            st.info("Ask the agent to show you an article, and it will appear here!")

        # Quick actions
        st.markdown("---")
        st.markdown("**Quick Actions:**")
        if st.button("📊 Show KB Stats", use_container_width=True):
            st.session_state.chat_messages.append({
                "role": "user",
                "content": "Show me KB statistics"
            })
            st.rerun()

        if st.button("📚 List All Articles", use_container_width=True):
            st.session_state.chat_messages.append({
                "role": "user",
                "content": "List all articles"
            })
            st.rerun()


if __name__ == "__main__":
    main()
