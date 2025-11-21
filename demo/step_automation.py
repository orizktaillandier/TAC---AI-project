"""
Step Automation Engine
Analyzes KB steps and automatically fetches data from Admin Dashboard
Comprehensive pattern matching to work with all existing and future KB articles
"""

import re
import logging
from typing import Dict, Any, List, Optional
from admin_dashboard_mock import AdminDashboardMock

logger = logging.getLogger(__name__)


class StepAutomation:
    """Automates KB steps by fetching data automatically"""
    
    def __init__(self):
        """Initialize step automation"""
        self.dashboard = AdminDashboardMock()
    
    def analyze_step(self, step: str, ticket_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a step and determine if it can be automated
        Comprehensive pattern matching for all KB article variations
        
        Args:
            step: The step text to analyze
            ticket_context: Ticket classification and context
        
        Returns:
            Dictionary with automation info
        """
        step_lower = step.lower()
        dealer_name = ticket_context.get('dealer_name', '')
        syndicator = ticket_context.get('syndicator', '')
        provider = ticket_context.get('provider', '')
        
        automation = {
            "can_automate": False,
            "automation_type": None,
            "data": None,
            "display_format": None
        }
        
        if not dealer_name:
            return automation  # Can't automate without dealer name
        
        # ========== PATTERN 1: ACTIONABLE STEPS (Execute Actions) ==========
        # These steps can be executed directly via buttons
        
        # Enable/Activate Feed
        # More flexible: match "enable" or "activate" button even without explicit "feed" mention
        if any(keyword in step_lower for keyword in ["enable", "activate", "turn on"]):
            # Check if it's about feed/export/import OR if it's a button click
            if any(keyword in step_lower for keyword in ["feed", "export", "import", "button", "click"]):
                automation["can_automate"] = True
                automation["automation_type"] = "action"
                automation["action_type"] = "enable_feed"
                automation["display_format"] = "action_button"
                
                feed_name = syndicator or provider or ""
                feed_type = "export" if any(kw in step_lower for kw in ["export", "syndicator"]) else "import"
                
                automation["action_params"] = {
                    "dealer_name": dealer_name,
                    "feed_name": feed_name,
                    "feed_type": feed_type
                }
                return automation
        
        # Disable/Deactivate Feed
        # More flexible: match "disable" button even without explicit "feed" mention
        if any(keyword in step_lower for keyword in ["disable", "deactivate", "turn off", "cancel"]):
            # Check if it's about feed/export/import OR if it's a button click
            if any(keyword in step_lower for keyword in ["feed", "export", "import", "button", "red"]):
                automation["can_automate"] = True
                automation["automation_type"] = "action"
                automation["action_type"] = "disable_feed"
                automation["display_format"] = "action_button"
                
                feed_name = syndicator or provider or ""
                feed_type = "export" if any(kw in step_lower for kw in ["export", "syndicator"]) else "import"
                
                automation["action_params"] = {
                    "dealer_name": dealer_name,
                    "feed_name": feed_name,
                    "feed_type": feed_type
                }
                return automation
        
        # Add New Export/Import
        # More flexible: match "add new export" button even with variations
        if any(keyword in step_lower for keyword in ["add new", "create", "add"]):
            if any(keyword in step_lower for keyword in ["export", "import", "feed", "button"]):
                automation["can_automate"] = True
                automation["automation_type"] = "action"
                automation["action_type"] = "add_new_export" if "export" in step_lower else "add_new_import"
                automation["display_format"] = "action_button"
                
                # Extract syndicator/provider name from step or context
                feed_name = syndicator or provider or ""
                if not feed_name:
                    # Try to extract from step text
                    match = re.search(r"(syndicator|provider)[_\s]+[\w\d]+", step_lower, re.IGNORECASE)
                    if match:
                        feed_name = match.group(0).strip()
                
                automation["action_params"] = {
                    "dealer_name": dealer_name,
                    "feed_name": feed_name
                }
                return automation
        
        # Copy Feed ID
        if any(keyword in step_lower for keyword in ["copy", "get", "retrieve", "note"]):
            if any(keyword in step_lower for keyword in ["feed id", "feedid", "feed_id"]):
                automation["can_automate"] = True
                automation["automation_type"] = "action"
                automation["action_type"] = "copy_feed_id"
                automation["display_format"] = "action_button"
                
                feed_name = syndicator or provider or ""
                feed_type = "export" if any(kw in step_lower for kw in ["export", "syndicator"]) else "import"
                
                automation["action_params"] = {
                    "dealer_name": dealer_name,
                    "feed_name": feed_name,
                    "feed_type": feed_type
                }
                return automation
        
        # Force Refresh/Force Export
        # More flexible: match "force refresh" or "force export" button
        if any(keyword in step_lower for keyword in ["force", "trigger", "refresh", "manual"]):
            if any(keyword in step_lower for keyword in ["refresh", "export", "import", "sync", "button"]):
                automation["can_automate"] = True
                automation["automation_type"] = "action"
                automation["action_type"] = "force_refresh"
                automation["display_format"] = "action_button"
                
                feed_name = syndicator or provider or ""
                feed_type = "import" if "import" in step_lower else "export"
                
                automation["action_params"] = {
                    "dealer_name": dealer_name,
                    "feed_name": feed_name,
                    "feed_type": feed_type
                }
                return automation
        
        # Download Feed File
        if any(keyword in step_lower for keyword in ["download", "get", "retrieve", "export", "save"]):
            if any(keyword in step_lower for keyword in ["feed file", "feedfile", "file", "export file"]):
                automation["can_automate"] = True
                automation["automation_type"] = "action"
                automation["action_type"] = "download_feed_file"
                automation["display_format"] = "action_button"
                
                feed_name = syndicator or provider or ""
                feed_type = "export" if any(kw in step_lower for kw in ["export", "syndicator"]) else "import"
                
                automation["action_params"] = {
                    "dealer_name": dealer_name,
                    "feed_name": feed_name,
                    "feed_type": feed_type
                }
                return automation
        
        # Save Settings
        if any(keyword in step_lower for keyword in ["save", "apply"]):
            if any(keyword in step_lower for keyword in ["settings", "configuration", "config", "changes"]):
                automation["can_automate"] = True
                automation["automation_type"] = "action"
                automation["action_type"] = "save_settings"
                automation["display_format"] = "action_button"
                
                feed_name = syndicator or provider or ""
                feed_type = "import" if "import" in step_lower else "export"
                
                automation["action_params"] = {
                    "dealer_name": dealer_name,
                    "feed_name": feed_name,
                    "feed_type": feed_type
                }
                return automation
        
        # Add New Client / Create Client Profile
        if any(keyword in step_lower for keyword in ["add new client", "create client", "new client"]):
            automation["can_automate"] = True
            automation["automation_type"] = "action"
            automation["action_type"] = "add_new_client"
            automation["display_format"] = "action_button"
            
            automation["action_params"] = {
                "dealer_name": dealer_name
            }
            return automation
        
        # Select from Dropdown (for syndicator/provider selection)
        if any(keyword in step_lower for keyword in ["select", "choose", "pick"]):
            if any(keyword in step_lower for keyword in ["syndicator", "provider", "dropdown", "from the"]):
                automation["can_automate"] = True
                automation["automation_type"] = "action"
                automation["action_type"] = "select_syndicator"
                automation["display_format"] = "action_button"
                
                # Extract syndicator/provider name
                feed_name = syndicator or provider or ""
                if not feed_name:
                    match = re.search(r"(syndicator|provider)[_\s]+[\w\d]+", step_lower, re.IGNORECASE)
                    if match:
                        feed_name = match.group(0).strip()
                
                automation["action_params"] = {
                    "dealer_name": dealer_name,
                    "feed_name": feed_name
                }
                return automation
        
        # Confirm Action (for popup dialogs)
        if any(keyword in step_lower for keyword in ["confirm", "approve", "accept"]):
            if any(keyword in step_lower for keyword in ["action", "dialog", "popup", "button"]):
                automation["can_automate"] = True
                automation["automation_type"] = "action"
                automation["action_type"] = "confirm_action"
                automation["display_format"] = "action_button"
                
                automation["action_params"] = {
                    "dealer_name": dealer_name
                }
                return automation
        
        # ========== PATTERN 2: Dealer Profile/Info Access ==========
        # Matches: "Log into Admin Dashboard", "Search for dealer", "Click on dealer's name", 
        # "Open their profile", "Navigate to dealer", "Access dealer page", etc.
        dealer_access_patterns = [
            "log into", "log in to", "login", "access", "navigate to", "go to",
            "search for", "find the dealer", "locate the dealer",
            "click on", "open", "view", "see", "dealer's profile", "dealer profile",
            "client page", "client's page", "dealer page", "dealer's page",
            "click 'clients'", "clients in the", "clients section"
        ]
        
        # More flexible: match if ANY dealer access pattern OR mentions dealer/client/dashboard
        if any(pattern in step_lower for pattern in dealer_access_patterns) or \
           any(keyword in step_lower for keyword in ["dealer", "client", "admin dashboard", "dashboard"]):
            automation["can_automate"] = True
            automation["automation_type"] = "dealer_info"
            automation["display_format"] = "dealer_card"
            
            dealer_info = self.dashboard.get_dealer_info(dealer_name)
            if dealer_info:
                automation["data"] = {
                    "dealer_name": dealer_info["dealer_name"],
                    "dealer_id": dealer_info["dealer_id"],
                    "account_status": dealer_info["account_status"],
                    "last_login": dealer_info["last_login"]
                }
            return automation
        
        # ========== PATTERN 3: Exports/Imports Tab Access ==========
        # Matches: "Click the 'Exports' tab", "Click the 'Imports' tab", 
        # "Check both 'Imports' and 'Exports' tabs", "View exports", etc.
        exports_tab_patterns = ["exports tab", "export tab", "click 'exports'", "view exports", "export section"]
        imports_tab_patterns = ["imports tab", "import tab", "click 'imports'", "view imports", "import section"]
        both_tabs_patterns = ["both", "exports and imports", "imports and exports", "all feeds", "all tabs"]
        
        is_exports_tab = any(pattern in step_lower for pattern in exports_tab_patterns)
        is_imports_tab = any(pattern in step_lower for pattern in imports_tab_patterns)
        is_both_tabs = any(pattern in step_lower for pattern in both_tabs_patterns)
        
        if is_exports_tab or is_imports_tab or is_both_tabs:
            automation["can_automate"] = True
            automation["automation_type"] = "feed_status"
            automation["display_format"] = "feeds_table"
            
            all_feeds = self.dashboard.get_all_feeds_status(dealer_name)
            if all_feeds.get("dealer_found"):
                # Filter based on which tab(s) mentioned
                if is_both_tabs:
                    # Show both
                    automation["data"] = all_feeds
                elif is_exports_tab:
                    # Show only exports
                    automation["data"] = {
                        "dealer_found": True,
                        "dealer_name": all_feeds.get("dealer_name"),
                        "dealer_id": all_feeds.get("dealer_id"),
                        "exports": all_feeds.get("exports", []),
                        "imports": []
                    }
                elif is_imports_tab:
                    # Show only imports
                    automation["data"] = {
                        "dealer_found": True,
                        "dealer_name": all_feeds.get("dealer_name"),
                        "dealer_id": all_feeds.get("dealer_id"),
                        "exports": [],
                        "imports": all_feeds.get("imports", [])
                    }
            return automation
        
        # ========== PATTERN 4: Feed Status Check ==========
        # Matches: "Check feed status", "Verify status", "Find syndicator", 
        # "Check if syndicator is listed", "Look for Active status", etc.
        # More flexible: match if ANY status check pattern OR feed mention
        status_check_patterns = [
            "check", "verify", "confirm", "find", "locate", "see", "view",
            "status", "active", "inactive", "error", "working", "running",
            "is listed", "already listed", "exists", "present", "look for"
        ]
        feed_mention_patterns = [
            "feed", "export", "import", "syndicator", "provider", 
            "integration", "connection"
        ]
        
        # Match if step contains status check keywords OR feed keywords
        if any(pattern in step_lower for pattern in status_check_patterns) or \
           any(pattern in step_lower for pattern in feed_mention_patterns):
            automation["can_automate"] = True
            automation["automation_type"] = "feed_status"
            
            # Try to find feed name from step or context
            feed_name = syndicator or provider or ""
            
            # Extract feed name from step if mentioned (e.g., "Find Syndicator_Export_1")
            feed_match = re.search(r'(syndicator|provider|export|import)[_\s]+[\w\d]+', step_lower, re.IGNORECASE)
            if feed_match:
                feed_name = feed_match.group(0).replace("_", "_").strip()
            
            if feed_name:
                # Specific feed
                feed_data = self.dashboard.check_feed_active(dealer_name, feed_name)
                automation["data"] = feed_data
                automation["display_format"] = "status_badge"
            else:
                # All feeds
                all_feeds = self.dashboard.get_all_feeds_status(dealer_name)
                automation["data"] = all_feeds
                automation["display_format"] = "feeds_table"
            return automation
        
        # ========== PATTERN 5: Last Updated/Timestamp Check ==========
        # Matches: "Check Last Updated", "Check timestamp", "Verify last activity",
        # "Check Last Export", "Recent update", etc.
        timestamp_patterns = [
            "last updated", "last update", "timestamp", "last activity", 
            "last export", "last import", "last sync", "last refresh",
            "recent", "recently", "within", "should be", "check when",
            "when was", "how recent"
        ]
        
        if any(pattern in step_lower for pattern in timestamp_patterns):
            automation["can_automate"] = True
            automation["automation_type"] = "last_updated"
            automation["display_format"] = "timestamp"
            
            # Try to get feed-specific timestamp
            feed_name = syndicator or provider or ""
            if feed_name:
                feed_data = self.dashboard.check_feed_active(dealer_name, feed_name)
                if feed_data.get("found"):
                    automation["data"] = {
                        "last_updated": feed_data.get("last_updated"),
                        "formatted": self._format_timestamp(feed_data.get("last_updated")),
                        "feed_name": feed_name
                    }
                else:
                    # Fallback to most recent feed
                    all_feeds = self.dashboard.get_all_feeds_status(dealer_name)
                    most_recent = None
                    for feed in (all_feeds.get("exports", []) + all_feeds.get("imports", [])):
                        if not most_recent or feed.get("last_updated", "") > most_recent.get("last_updated", ""):
                            most_recent = feed
                    if most_recent:
                        automation["data"] = {
                            "last_updated": most_recent.get("last_updated"),
                            "formatted": self._format_timestamp(most_recent.get("last_updated")),
                            "feed_name": most_recent.get("feed_name", "")
                        }
            else:
                # Get most recent from all feeds
                all_feeds = self.dashboard.get_all_feeds_status(dealer_name)
                most_recent = None
                for feed in (all_feeds.get("exports", []) + all_feeds.get("imports", [])):
                    if not most_recent or feed.get("last_updated", "") > most_recent.get("last_updated", ""):
                        most_recent = feed
                if most_recent:
                    automation["data"] = {
                        "last_updated": most_recent.get("last_updated"),
                        "formatted": self._format_timestamp(most_recent.get("last_updated")),
                        "feed_name": most_recent.get("feed_name", "")
                    }
            return automation
        
        # ========== PATTERN 6: Activity Log Review ==========
        # Matches: "Review Activity Log", "Check log", "Review recent operations",
        # "Check activity", "View operations", "Check if sold vehicles removed", etc.
        activity_log_patterns = [
            "activity log", "activity", "log", "operations", "recent operations",
            "recent activity", "check log", "review log", "view log", "see log",
            "operations log", "action log", "event log", "history",
            "sold vehicles", "removed", "changes", "updates"
        ]
        
        if any(pattern in step_lower for pattern in activity_log_patterns):
            automation["can_automate"] = True
            automation["automation_type"] = "activity_log"
            automation["display_format"] = "activity_table"
            
            activity_log = self.dashboard.get_activity_log(dealer_name, limit=10)
            automation["data"] = {
                "entries": activity_log,
                "count": len(activity_log)
            }
            return automation
        
        # ========== PATTERN 7: Status Verification After Action ==========
        # Matches: "Verify the status changed", "Confirm status is", 
        # "Check that status is", "Ensure status is", etc.
        verify_status_patterns = [
            "verify", "confirm", "check that", "ensure", "make sure",
            "status changed", "status is", "changed to", "is now"
        ]
        
        if any(pattern in step_lower for pattern in verify_status_patterns):
            if any(keyword in step_lower for keyword in ["status", "active", "inactive", "enabled", "disabled"]):
                automation["can_automate"] = True
                automation["automation_type"] = "feed_status"
                automation["display_format"] = "status_badge"
                
                feed_name = syndicator or provider or ""
                if feed_name:
                    feed_data = self.dashboard.check_feed_active(dealer_name, feed_name)
                    automation["data"] = feed_data
                else:
                    all_feeds = self.dashboard.get_all_feeds_status(dealer_name)
                    automation["data"] = all_feeds
                    automation["display_format"] = "feeds_table"
                return automation
        
        return automation
    
    def _format_timestamp(self, timestamp: str) -> str:
        """Format timestamp for display"""
        if not timestamp:
            return "N/A"
        
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp)
            now = datetime.now()
            diff = now - dt
            
            if diff.days > 0:
                return f"{diff.days} day(s) ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hour(s) ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minute(s) ago"
            else:
                return "Just now"
        except:
            return timestamp
    
    def process_steps(self, steps: List[str], ticket_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process all steps and add automation data
        
        Args:
            steps: List of step strings
            ticket_context: Ticket classification and context
        
        Returns:
            List of step dictionaries with automation data
        """
        processed_steps = []
        
        for step in steps:
            automation = self.analyze_step(step, ticket_context)
            processed_steps.append({
                "step_text": step,
                "automation": automation
            })
        
        return processed_steps

