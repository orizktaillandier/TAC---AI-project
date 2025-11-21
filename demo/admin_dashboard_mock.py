"""
Mock Admin Dashboard Data Source
Simulates fetching data from Admin Dashboard for automated step execution
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


class AdminDashboardMock:
    """Mock Admin Dashboard API - simulates real dashboard data"""
    
    def __init__(self):
        """Initialize with mock dealer data"""
        self.dealers_data = self._load_mock_dealers()
    
    def _load_mock_dealers(self) -> Dict[str, Dict[str, Any]]:
        """Load mock dealer data"""
        # Generate realistic mock data
        dealers = {}
        
        # Sample dealers from classification
        dealer_names = [
            "Dealership_1", "Dealership_2", "Dealership_3", 
            "Dealership_4", "Dealership_5", "Dealership_6"
        ]
        
        syndicators = [
            "Syndicator_Export_1", "Syndicator_Export_2", "Syndicator_Export_3",
            "Syndicator_Export_4", "Kijiji", "AutoTrader", "Facebook"
        ]
        
        providers = [
            "Provider_Import_1", "Provider_Import_2", "Provider_Import_3",
            "PBS", "Polk", "CDK"
        ]
        
        for dealer_name in dealer_names:
            # Generate random feed statuses
            exports = []
            imports = []
            
            # Ensure unique syndicators per dealer (no duplicates)
            available_syndicators = syndicators.copy()
            num_exports = random.randint(2, 4)
            
            # 2-4 export feeds per dealer
            for i in range(num_exports):
                if available_syndicators:
                    syndicator = random.choice(available_syndicators)
                    available_syndicators.remove(syndicator)  # Remove to avoid duplicates
                else:
                    syndicator = f"Syndicator_Export_{i+1}"
                
                # Ensure at least 1-2 active exports per dealer
                if i < 2:
                    status = "Active"  # First 2 are always active
                else:
                    status = random.choice(["Active", "Active", "Inactive", "Error"])
                
                last_updated = (datetime.now() - timedelta(
                    hours=random.randint(0, 48) if status == "Active" else random.randint(72, 720)
                )).isoformat()
                
                exports.append({
                    "feed_name": syndicator,
                    "status": status,
                    "last_updated": last_updated,
                    "feed_id": f"EXPORT_{dealer_name}_{i+1}",
                    "inventory_count": random.randint(50, 500) if status == "Active" else 0,
                    "last_successful_sync": last_updated if status == "Active" else None
                })
            
            # Ensure unique providers per dealer (no duplicates)
            available_providers = providers.copy()
            num_imports = random.randint(1, 3)
            
            # 1-3 import feeds per dealer
            for i in range(num_imports):
                if available_providers:
                    provider = random.choice(available_providers)
                    available_providers.remove(provider)  # Remove to avoid duplicates
                else:
                    provider = f"Provider_Import_{i+1}"
                
                # Ensure at least 1 active import per dealer
                if i == 0:
                    status = "Active"  # First import is always active
                else:
                    status = random.choice(["Active", "Active", "Inactive"])
                
                last_updated = (datetime.now() - timedelta(
                    hours=random.randint(0, 24) if status == "Active" else random.randint(48, 240)
                )).isoformat()
                
                imports.append({
                    "feed_name": provider,
                    "status": status,
                    "last_updated": last_updated,
                    "feed_id": f"IMPORT_{dealer_name}_{i+1}",
                    "inventory_count": random.randint(100, 1000) if status == "Active" else 0,
                    "last_successful_sync": last_updated if status == "Active" else None
                })
            
            # Generate activity log
            activity_log = []
            for j in range(random.randint(5, 15)):
                activity_log.append({
                    "timestamp": (datetime.now() - timedelta(hours=random.randint(0, 168))).isoformat(),
                    "action": random.choice([
                        "Feed sync completed",
                        "Inventory updated",
                        "Feed status changed",
                        "Manual sync triggered",
                        "Error occurred",
                        "Feed disabled",
                        "Feed enabled"
                    ]),
                    "status": random.choice(["Success", "Success", "Success", "Warning", "Error"]),
                    "details": f"Processed {random.randint(10, 500)} items"
                })
            
            dealers[dealer_name] = {
                "dealer_id": f"DEALER_{dealer_names.index(dealer_name) + 1}",
                "dealer_name": dealer_name,
                "exports": exports,
                "imports": imports,
                "activity_log": sorted(activity_log, key=lambda x: x['timestamp'], reverse=True)[:10],
                "last_login": (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
                "account_status": random.choice(["Active", "Active", "Active", "Suspended", "Trial"])
            }
        
        return dealers
    
    def get_dealer_info(self, dealer_name: str) -> Optional[Dict[str, Any]]:
        """Get dealer information from Admin Dashboard"""
        # Normalize dealer name
        dealer_name = dealer_name.strip()
        
        # Try exact match first
        if dealer_name in self.dealers_data:
            return self.dealers_data[dealer_name]
        
        # Try case-insensitive match
        for key, value in self.dealers_data.items():
            if key.lower() == dealer_name.lower():
                return value
        
        # Try partial match
        for key, value in self.dealers_data.items():
            if dealer_name.lower() in key.lower() or key.lower() in dealer_name.lower():
                return value
        
        logger.warning(f"Dealer not found: {dealer_name}")
        return None
    
    def get_feed_status(self, dealer_name: str, feed_name: str = None, feed_type: str = "export") -> Optional[Dict[str, Any]]:
        """Get feed status for a dealer"""
        dealer_info = self.get_dealer_info(dealer_name)
        if not dealer_info:
            return None
        
        feeds = dealer_info.get("imports" if feed_type.lower() == "import" else "exports", [])
        
        if feed_name:
            # Find specific feed
            for feed in feeds:
                if feed_name.lower() in feed["feed_name"].lower() or feed["feed_name"].lower() in feed_name.lower():
                    return feed
            return None
        else:
            # Return all feeds
            return feeds
    
    def get_activity_log(self, dealer_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get activity log for a dealer"""
        dealer_info = self.get_dealer_info(dealer_name)
        if not dealer_info:
            return []
        
        return dealer_info.get("activity_log", [])[:limit]
    
    def check_feed_active(self, dealer_name: str, feed_name: str) -> Dict[str, Any]:
        """Check if a specific feed is active"""
        feed = self.get_feed_status(dealer_name, feed_name)
        
        if not feed:
            return {
                "found": False,
                "status": "Not Found",
                "message": f"Feed '{feed_name}' not found for {dealer_name}"
            }
        
        return {
            "found": True,
            "status": feed["status"],
            "is_active": feed["status"] == "Active",
            "last_updated": feed["last_updated"],
            "feed_id": feed["feed_id"],
            "inventory_count": feed.get("inventory_count", 0),
            "last_successful_sync": feed.get("last_successful_sync")
        }
    
    def get_all_feeds_status(self, dealer_name: str) -> Dict[str, Any]:
        """Get status of all feeds for a dealer"""
        dealer_info = self.get_dealer_info(dealer_name)
        if not dealer_info:
            return {
                "dealer_found": False,
                "exports": [],
                "imports": []
            }
        
        return {
            "dealer_found": True,
            "dealer_name": dealer_name,
            "dealer_id": dealer_info["dealer_id"],
            "exports": dealer_info["exports"],
            "imports": dealer_info["imports"],
            "account_status": dealer_info["account_status"]
        }
    
    # ========== ACTION EXECUTION METHODS ==========
    
    def enable_feed(self, dealer_name: str, feed_name: str, feed_type: str = "export") -> Dict[str, Any]:
        """Enable/activate a feed"""
        dealer_info = self.get_dealer_info(dealer_name)
        if not dealer_info:
            return {"success": False, "message": f"Dealer {dealer_name} not found"}
        
        feeds = dealer_info.get("imports" if feed_type.lower() == "import" else "exports", [])
        
        # Find and update feed
        for feed in feeds:
            if feed_name.lower() in feed["feed_name"].lower() or feed["feed_name"].lower() in feed_name.lower():
                feed["status"] = "Active"
                feed["last_updated"] = datetime.now().isoformat()
                feed["last_successful_sync"] = feed["last_updated"]
                
                # Add to activity log
                dealer_info["activity_log"].insert(0, {
                    "timestamp": datetime.now().isoformat(),
                    "action": f"Feed enabled: {feed['feed_name']}",
                    "status": "Success",
                    "details": f"Feed ID: {feed['feed_id']}"
                })
                dealer_info["activity_log"] = dealer_info["activity_log"][:20]  # Keep last 20
                
                return {
                    "success": True,
                    "message": f"Feed {feed['feed_name']} enabled successfully",
                    "feed_id": feed["feed_id"],
                    "status": feed["status"]
                }
        
        return {"success": False, "message": f"Feed {feed_name} not found"}
    
    def disable_feed(self, dealer_name: str, feed_name: str, feed_type: str = "export") -> Dict[str, Any]:
        """Disable/deactivate a feed"""
        dealer_info = self.get_dealer_info(dealer_name)
        if not dealer_info:
            return {"success": False, "message": f"Dealer {dealer_name} not found"}
        
        feeds = dealer_info.get("imports" if feed_type.lower() == "import" else "exports", [])
        
        # Find and update feed
        for feed in feeds:
            if feed_name.lower() in feed["feed_name"].lower() or feed["feed_name"].lower() in feed_name.lower():
                feed["status"] = "Inactive"
                feed["last_updated"] = datetime.now().isoformat()
                
                # Add to activity log
                dealer_info["activity_log"].insert(0, {
                    "timestamp": datetime.now().isoformat(),
                    "action": f"Feed disabled: {feed['feed_name']}",
                    "status": "Success",
                    "details": f"Feed ID: {feed['feed_id']}"
                })
                dealer_info["activity_log"] = dealer_info["activity_log"][:20]
                
                return {
                    "success": True,
                    "message": f"Feed {feed['feed_name']} disabled successfully",
                    "feed_id": feed["feed_id"],
                    "status": feed["status"]
                }
        
        return {"success": False, "message": f"Feed {feed_name} not found"}
    
    def add_new_export(self, dealer_name: str, syndicator_name: str) -> Dict[str, Any]:
        """Add a new export feed"""
        dealer_info = self.get_dealer_info(dealer_name)
        if not dealer_info:
            return {"success": False, "message": f"Dealer {dealer_name} not found"}
        
        # Check if feed already exists
        for feed in dealer_info["exports"]:
            if syndicator_name.lower() in feed["feed_name"].lower():
                return {
                    "success": False,
                    "message": f"Feed for {syndicator_name} already exists",
                    "feed_id": feed["feed_id"]
                }
        
        # Generate new feed ID
        feed_id = f"FEED-{random.randint(10000, 99999)}"
        
        # Create new feed
        new_feed = {
            "feed_name": syndicator_name,
            "status": "Inactive",  # Starts inactive, needs to be enabled
            "last_updated": datetime.now().isoformat(),
            "feed_id": feed_id,
            "inventory_count": 0,
            "last_successful_sync": None
        }
        
        dealer_info["exports"].append(new_feed)
        
        # Add to activity log
        dealer_info["activity_log"].insert(0, {
            "timestamp": datetime.now().isoformat(),
            "action": f"New export feed added: {syndicator_name}",
            "status": "Success",
            "details": f"Feed ID: {feed_id}"
        })
        dealer_info["activity_log"] = dealer_info["activity_log"][:20]
        
        return {
            "success": True,
            "message": f"New export feed added for {syndicator_name}",
            "feed_id": feed_id,
            "feed": new_feed
        }
    
    def force_refresh_feed(self, dealer_name: str, feed_name: str, feed_type: str = "import") -> Dict[str, Any]:
        """Force refresh/trigger immediate sync for a feed"""
        dealer_info = self.get_dealer_info(dealer_name)
        if not dealer_info:
            return {"success": False, "message": f"Dealer {dealer_name} not found"}
        
        feeds = dealer_info.get("imports" if feed_type.lower() == "import" else "exports", [])
        
        # Find and update feed
        for feed in feeds:
            if feed_name.lower() in feed["feed_name"].lower() or feed["feed_name"].lower() in feed_name.lower():
                feed["last_updated"] = datetime.now().isoformat()
                if feed["status"] == "Active":
                    feed["last_successful_sync"] = feed["last_updated"]
                    feed["inventory_count"] = random.randint(50, 500)  # Simulate updated count
                
                # Add to activity log
                dealer_info["activity_log"].insert(0, {
                    "timestamp": datetime.now().isoformat(),
                    "action": f"Force refresh triggered: {feed['feed_name']}",
                    "status": "Success",
                    "details": f"Feed ID: {feed['feed_id']}"
                })
                dealer_info["activity_log"] = dealer_info["activity_log"][:20]
                
                return {
                    "success": True,
                    "message": f"Force refresh completed for {feed['feed_name']}",
                    "feed_id": feed["feed_id"],
                    "last_updated": feed["last_updated"]
                }
        
        return {"success": False, "message": f"Feed {feed_name} not found"}
    
    def get_feed_id(self, dealer_name: str, feed_name: str, feed_type: str = "export") -> Optional[str]:
        """Get Feed ID for a specific feed"""
        feed = self.get_feed_status(dealer_name, feed_name, feed_type)
        if feed:
            return feed.get("feed_id")
        return None
    
    def download_feed_file(self, dealer_name: str, feed_name: str, feed_type: str = "export") -> Dict[str, Any]:
        """Generate/download feed file for review"""
        dealer_info = self.get_dealer_info(dealer_name)
        if not dealer_info:
            return {"success": False, "message": f"Dealer {dealer_name} not found"}
        
        feeds = dealer_info.get("imports" if feed_type.lower() == "import" else "exports", [])
        
        # Find feed
        feed = None
        for f in feeds:
            if feed_name.lower() in f["feed_name"].lower() or f["feed_name"].lower() in feed_name.lower():
                feed = f
                break
        
        if not feed:
            return {"success": False, "message": f"Feed {feed_name} not found"}
        
        # Generate mock file content
        file_name = f"{feed['feed_id']}_{feed['feed_name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        file_size = random.randint(50000, 500000)  # 50KB to 500KB
        
        # Add to activity log
        dealer_info["activity_log"].insert(0, {
            "timestamp": datetime.now().isoformat(),
            "action": f"Feed file downloaded: {feed['feed_name']}",
            "status": "Success",
            "details": f"File: {file_name} ({file_size} bytes)"
        })
        dealer_info["activity_log"] = dealer_info["activity_log"][:20]
        
        return {
            "success": True,
            "message": f"Feed file generated successfully",
            "file_name": file_name,
            "file_size": file_size,
            "feed_id": feed["feed_id"],
            "feed_name": feed["feed_name"],
            "content_preview": f"<?xml version='1.0'?><feed><id>{feed['feed_id']}</id><name>{feed['feed_name']}</name>...</feed>"
        }
    
    def save_settings(self, dealer_name: str, feed_name: str, feed_type: str = "import") -> Dict[str, Any]:
        """Save feed settings/configuration"""
        dealer_info = self.get_dealer_info(dealer_name)
        if not dealer_info:
            return {"success": False, "message": f"Dealer {dealer_name} not found"}
        
        feeds = dealer_info.get("imports" if feed_type.lower() == "import" else "exports", [])
        
        # Find feed
        feed = None
        for f in feeds:
            if feed_name.lower() in f["feed_name"].lower() or f["feed_name"].lower() in feed_name.lower():
                feed = f
                break
        
        if not feed:
            return {"success": False, "message": f"Feed {feed_name} not found"}
        
        # Add to activity log
        dealer_info["activity_log"].insert(0, {
            "timestamp": datetime.now().isoformat(),
            "action": f"Settings saved for feed: {feed['feed_name']}",
            "status": "Success",
            "details": f"Feed ID: {feed['feed_id']}"
        })
        dealer_info["activity_log"] = dealer_info["activity_log"][:20]
        
        return {
            "success": True,
            "message": f"Settings saved successfully for {feed['feed_name']}",
            "feed_id": feed["feed_id"]
        }
    
    def add_new_client(self, dealer_name: str) -> Dict[str, Any]:
        """Add/create a new client profile"""
        # Check if client already exists
        if dealer_name in self.dealers_data:
            return {
                "success": False,
                "message": f"Client {dealer_name} already exists",
                "dealer_id": self.dealers_data[dealer_name]["dealer_id"]
            }
        
        # Create new client (in real system, this would create a new entry)
        # For mock, we'll just return success
        return {
            "success": True,
            "message": f"New client profile created for {dealer_name}",
            "dealer_id": f"DEALER_NEW_{len(self.dealers_data) + 1}",
            "note": "Client profile created. You can now configure feeds."
        }
    
    def select_syndicator(self, dealer_name: str, syndicator_name: str) -> Dict[str, Any]:
        """Select syndicator from dropdown (prepares for feed creation)"""
        dealer_info = self.get_dealer_info(dealer_name)
        if not dealer_info:
            return {"success": False, "message": f"Dealer {dealer_name} not found"}
        
        return {
            "success": True,
            "message": f"Syndicator {syndicator_name} selected",
            "syndicator_name": syndicator_name,
            "next_step": "Click 'Enable' to activate the feed"
        }
    
    def confirm_action(self, dealer_name: str) -> Dict[str, Any]:
        """Confirm action in popup dialog"""
        return {
            "success": True,
            "message": "Action confirmed successfully"
        }
    
    def get_client_configuration(self, dealer_name: str) -> Dict[str, Any]:
        """
        Get client configuration summary - Active exports and imports
        Returns a clean summary for display
        """
        dealer_info = self.get_dealer_info(dealer_name)
        if not dealer_info:
            return {
                "dealer_name": dealer_name,
                "dealer_found": False,
                "active_exports": [],
                "active_imports": []
            }
        
        # Get only active feeds
        active_exports = [
            feed["feed_name"] 
            for feed in dealer_info.get("exports", []) 
            if feed.get("status") == "Active"
        ]
        
        active_imports = [
            feed["feed_name"] 
            for feed in dealer_info.get("imports", []) 
            if feed.get("status") == "Active"
        ]
        
        return {
            "dealer_name": dealer_name,
            "dealer_id": dealer_info.get("dealer_id"),
            "dealer_found": True,
            "active_exports": active_exports,
            "active_imports": active_imports,
            "account_status": dealer_info.get("account_status", "Unknown")
        }

