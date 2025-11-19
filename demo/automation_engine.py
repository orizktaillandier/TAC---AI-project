"""
Tier 1 Automated Resolution Engine
Based on real D2CMedia workflow for Product Activation - Existing Client
"""
from typing import Dict, List, Any, Tuple
from datetime import datetime
import time
import pandas as pd

class AutomationEngine:
    """Handles automated resolution for Tier 1 tickets following real workflow"""

    def __init__(self):
        self.execution_log = []
        self.emails_sent = []
        self.internal_comments = []
        self.billing_data = self._load_billing_requirements()
        self.cancelled_feeds = self._load_cancelled_feeds()

    def _load_billing_requirements(self) -> pd.DataFrame:
        """Load billing requirements for dealerships"""
        try:
            return pd.read_csv("data/dealership_billing_requirements.csv", encoding="utf-8")
        except FileNotFoundError:
            # File doesn't exist, return empty DataFrame
            return pd.DataFrame()
        except pd.errors.EmptyDataError:
            # File exists but is empty
            return pd.DataFrame()
        except Exception as e:
            # Other errors (permissions, encoding, etc.)
            print(f"Warning: Could not load billing requirements: {e}")
            return pd.DataFrame()

    def _load_cancelled_feeds(self) -> pd.DataFrame:
        """Load cancelled feeds log"""
        try:
            return pd.read_csv("data/cancelled_feeds.csv", encoding="utf-8")
        except FileNotFoundError:
            # If file doesn't exist, create empty DataFrame with proper columns
            return pd.DataFrame(columns=[
                'Cancellation Date', 'Dealer ID', 'Dealer Name', 'Feed Name',
                'Feed Type', 'Cancelled By', 'Reason', 'Feed ID'
            ])
        except pd.errors.EmptyDataError:
            # File exists but is empty
            return pd.DataFrame(columns=[
                'Cancellation Date', 'Dealer ID', 'Dealer Name', 'Feed Name',
                'Feed Type', 'Cancelled By', 'Reason', 'Feed ID'
            ])
        except Exception as e:
            # Other errors
            print(f"Warning: Could not load cancelled feeds: {e}")
            return pd.DataFrame(columns=[
                'Cancellation Date', 'Dealer ID', 'Dealer Name', 'Feed Name',
                'Feed Type', 'Cancelled By', 'Reason', 'Feed ID'
            ])

    def can_automate(self, classification: Dict[str, str], entities: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Determine if a ticket can be fully automated.

        Returns:
            (can_automate, reason)
        """
        tier = classification.get("tier", "")
        category = classification.get("category", "")

        # Only Tier 1 tickets
        if tier != "Tier 1":
            return False, f"Not Tier 1 (classified as {tier})"

        # Only Product Activation - Existing Client and Product Cancellation
        supported_categories = ["Product Activation — Existing Client", "Product Cancellation"]
        if category not in supported_categories:
            return False, f"Category not supported for automation: {category}"

        # Check if request is simple (only feed setup/cancellation, no additional questions)
        key_actions = entities.get("key_action_items", [])
        problem_indicators = entities.get("problem_indicators", [])

        # If there are problems mentioned, not automatable
        if problem_indicators:
            return False, "Request contains problem indicators - needs human review"

        # Must have syndicator or provider
        syndicator = classification.get("syndicator", "")
        provider = classification.get("provider", "")

        if not syndicator and not provider:
            return False, "No syndicator or provider identified"

        # All checks passed
        return True, f"Simple {category.lower()} request - fully automatable"

    def execute_automation(self, classification: Dict[str, str], entities: Dict[str, Any], ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute full automation workflow based on ticket category.

        Returns:
            Automation result with execution logs, emails, and status
        """
        category = classification.get("category", "")

        if category == "Product Activation — Existing Client":
            return self._automate_product_activation(classification, entities, ticket_data)
        elif category == "Product Cancellation":
            return self._automate_product_cancellation(classification, entities, ticket_data)
        else:
            return {
                "success": False,
                "automated": False,
                "error": f"Unsupported category for automation: {category}"
            }

    def _automate_product_activation(self, classification: Dict[str, str], entities: Dict[str, Any], ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute full automation workflow for Product Activation - Existing Client.

        Workflow:
        1. Send acknowledgment to requester
        2. Tag billing in internal comment
        3. Get billing response (order required?)
        4A. If order required: email rep for order → wait → configure → confirm
        4B. If no order: email rep for approval → wait → configure → confirm

        Returns:
            Automation result with execution logs, emails, and status
        """
        self.execution_log = []
        self.emails_sent = []
        self.internal_comments = []
        start_time = time.time()

        dealer_name = classification.get("dealer_name", "Unknown Dealer")
        dealer_id = classification.get("dealer_id", "")
        rep_name = classification.get("rep", "Rep")
        contact_name = classification.get("contact", "there")
        syndicator = classification.get("syndicator", "")
        provider = classification.get("provider", "")
        inventory_type = classification.get("inventory_type", "Unspecified")

        # Determine feed type
        feed_type = "export" if syndicator else "import"
        feed_name = syndicator if syndicator else provider
        requester_email = ticket_data.get("requester_email", "requester@example.com")

        self._log("🤖 AUTOMATED RESOLUTION INITIATED", "header")
        self._log(f"Ticket Type: Product Activation — Existing Client", "info")
        self._log(f"Dealer: {dealer_name} (ID: {dealer_id})", "info")
        self._log(f"Feed: {feed_name} ({feed_type})", "info")
        self._log("", "spacer")

        try:
            # ============================================================
            # STEP 1: Send Acknowledgment Email to Requester
            # ============================================================
            self._log("STEP 1: Sending acknowledgment to requester", "step")
            time.sleep(0.5)

            ack_email = self._generate_acknowledgment_email(contact_name, feed_name, feed_type)
            self._send_email(
                to=requester_email,
                subject=f"Re: {feed_name} {feed_type} setup - {dealer_name}",
                body=ack_email,
                email_type="acknowledgment"
            )
            self._log(f"✓ Acknowledgment sent to {requester_email}", "success")
            self._log("", "spacer")

            # ============================================================
            # STEP 2: Tag Billing in Internal Comment
            # ============================================================
            self._log("STEP 2: Tagging billing team for order verification", "step")
            time.sleep(0.3)

            billing_comment = self._generate_billing_comment(dealer_name, dealer_id, feed_name, feed_type)
            self._add_internal_comment(
                comment=billing_comment,
                tagged_users=["@billing"],
                comment_type="billing_check"
            )
            self._log("✓ Billing team tagged in internal comment", "success")
            self._log("", "spacer")

            # ============================================================
            # STEP 3: Get Billing Response (from CSV)
            # ============================================================
            self._log("STEP 3: Waiting for billing team response...", "step")
            time.sleep(0.8)  # Simulate response time

            order_required, billing_info = self._check_billing_requirements(dealer_id)

            if order_required:
                self._log(f"✓ Billing Response: ORDER REQUIRED", "warning")
                self._log(f"  Package: {billing_info.get('Package Type', 'N/A')}", "info")
                self._log(f"  Monthly Fee: {billing_info.get('Monthly Fee', 'N/A')}", "info")
                self._log(f"  Notes: {billing_info.get('Notes', 'N/A')}", "info")
            else:
                self._log(f"✓ Billing Response: NO ORDER REQUIRED", "success")
                self._log(f"  Notes: {billing_info.get('Notes', 'Included in existing package')}", "info")

            self._log("", "spacer")

            # ============================================================
            # STEP 4A: Order Required Path
            # ============================================================
            if order_required:
                self._log("STEP 4A: Order Required - Requesting order from rep", "step")
                time.sleep(0.4)

                # Email rep asking for order
                order_request_email = self._generate_order_request_email(
                    rep_name, dealer_name, feed_name, feed_type, billing_info
                )
                self._send_email(
                    to=f"{rep_name.lower().replace(' ', '.')}@d2cmedia.com",
                    subject=f"Order Required: {feed_name} {feed_type} - {dealer_name}",
                    body=order_request_email,
                    email_type="order_request"
                )
                self._log(f"✓ Order request sent to {rep_name}", "success")
                self._log("", "spacer")

                # Wait for order confirmation (simulated)
                self._log("STEP 4A.1: Waiting for order confirmation...", "step")
                time.sleep(1.2)  # Simulate wait time
                self._log("✓ Order confirmed by rep", "success")
                self._log("  Order #: ORD-2025-" + dealer_id, "info")
                self._log("", "spacer")

            # ============================================================
            # STEP 4B: No Order Required - Check if approval needed
            # ============================================================
            else:
                # Check who requested the feed
                requester_is_rep = "rep" in ticket_data.get("requester_email", "").lower()

                if not requester_is_rep:
                    self._log("STEP 4B: No order required - Requesting approval from rep", "step")
                    time.sleep(0.4)

                    # Email rep for approval
                    approval_request_email = self._generate_approval_request_email(
                        rep_name, dealer_name, feed_name, feed_type, requester_email
                    )
                    self._send_email(
                        to=f"{rep_name.lower().replace(' ', '.')}@d2cmedia.com",
                        subject=f"Approval Needed: {feed_name} {feed_type} - {dealer_name}",
                        body=approval_request_email,
                        email_type="approval_request"
                    )
                    self._log(f"✓ Approval request sent to {rep_name}", "success")
                    self._log("", "spacer")

                    # Wait for approval (simulated)
                    self._log("STEP 4B.1: Waiting for rep approval...", "step")
                    time.sleep(1.0)  # Simulate wait time
                    self._log("✓ Approval received from rep", "success")
                    self._log("", "spacer")
                else:
                    self._log("STEP 4B: Rep requested feed directly - no approval needed", "info")
                    self._log("", "spacer")

            # ============================================================
            # STEP 5: Configure Feed
            # ============================================================
            self._log("STEP 5: Configuring feed in system", "step")
            time.sleep(0.6)

            feed_config = self._configure_feed(dealer_id, dealer_name, feed_name, feed_type, inventory_type)
            self._log("✓ Feed configured successfully", "success")
            self._log(f"  Feed ID: {feed_config['feed_id']}", "info")
            self._log(f"  Feed URL: {feed_config['feed_url']}", "info")
            self._log(f"  Inventory Type: {inventory_type}", "info")
            self._log(f"  Status: Active", "info")
            self._log("", "spacer")

            # ============================================================
            # STEP 6: Send Confirmation to 3rd Party/Requester
            # ============================================================
            self._log("STEP 6: Sending confirmation to requester", "step")
            time.sleep(0.4)

            confirmation_email = self._generate_confirmation_email(
                contact_name, dealer_name, feed_name, feed_type, feed_config
            )
            self._send_email(
                to=requester_email,
                subject=f"Completed: {feed_name} {feed_type} setup - {dealer_name}",
                body=confirmation_email,
                email_type="confirmation"
            )
            self._log(f"✓ Confirmation sent to {requester_email}", "success")
            self._log("", "spacer")

            # ============================================================
            # STEP 7: Update Ticket Status
            # ============================================================
            self._log("STEP 7: Updating ticket status", "step")
            time.sleep(0.2)
            self._log("✓ Ticket marked as 'Closed - Automated'", "success")
            self._log("", "spacer")

            execution_time = round(time.time() - start_time, 2)
            self._log(f"🎉 AUTOMATION COMPLETE in {execution_time}s", "header")

            return {
                "success": True,
                "automated": True,
                "execution_log": self.execution_log,
                "emails_sent": self.emails_sent,
                "internal_comments": self.internal_comments,
                "execution_time": execution_time,
                "resolution_status": "Closed - Automated",
                "order_required": order_required,
                "feed_configured": feed_config
            }

        except Exception as e:
            self._log(f"❌ Automation failed: {str(e)}", "error")
            return {
                "success": False,
                "automated": False,
                "execution_log": self.execution_log,
                "emails_sent": self.emails_sent,
                "internal_comments": self.internal_comments,
                "error": str(e)
            }

    def _automate_product_cancellation(self, classification: Dict[str, str], entities: Dict[str, Any], ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute full automation workflow for Product Cancellation.

        Workflow (3rd party requester):
        1. Send acknowledgment to 3rd party
        2. Email rep for approval
        3. Wait for approval
        4. Cancel feed
        5. Log to CSV
        6. Notify syndicator

        Workflow (rep requester):
        1. Cancel feed
        2. Log to CSV
        3. Notify syndicator

        Returns:
            Automation result with execution logs, emails, and status
        """
        self.execution_log = []
        self.emails_sent = []
        self.internal_comments = []
        start_time = time.time()

        dealer_name = classification.get("dealer_name", "Unknown Dealer")
        dealer_id = classification.get("dealer_id", "")
        rep_name = classification.get("rep", "Rep")
        contact_name = classification.get("contact", "there")
        syndicator = classification.get("syndicator", "")
        provider = classification.get("provider", "")
        inventory_type = classification.get("inventory_type", "Unspecified")

        # Determine feed type and name
        feed_type = "export" if syndicator else "import"
        feed_name = syndicator if syndicator else provider
        requester_email = ticket_data.get("requester_email", "requester@example.com")

        # Check if requester is a rep
        requester_is_rep = "rep" in requester_email.lower() or "@d2cmedia.com" in requester_email.lower()

        self._log("🤖 AUTOMATED CANCELLATION INITIATED", "header")
        self._log(f"Ticket Type: Product Cancellation", "info")
        self._log(f"Dealer: {dealer_name} (ID: {dealer_id})", "info")
        self._log(f"Feed: {feed_name} ({feed_type})", "info")
        self._log(f"Requester Type: {'Internal Rep' if requester_is_rep else '3rd Party'}", "info")
        self._log("", "spacer")

        try:
            # ============================================================
            # PATH A: 3rd Party Requester
            # ============================================================
            if not requester_is_rep:
                # STEP 1: Send Acknowledgment to 3rd Party
                self._log("STEP 1: Sending acknowledgment to 3rd party", "step")
                time.sleep(0.4)

                ack_email = self._generate_cancellation_acknowledgment_email(contact_name, feed_name, dealer_name)
                self._send_email(
                    to=requester_email,
                    subject=f"Re: {feed_name} cancellation - {dealer_name}",
                    body=ack_email,
                    email_type="cancellation_acknowledgment"
                )
                self._log(f"✓ Acknowledgment sent to {requester_email}", "success")
                self._log("", "spacer")

                # STEP 2: Email Rep for Approval
                self._log("STEP 2: Requesting cancellation approval from rep", "step")
                time.sleep(0.3)

                approval_email = self._generate_cancellation_approval_email(
                    rep_name, dealer_name, feed_name, requester_email
                )
                self._send_email(
                    to=f"{rep_name.lower().replace(' ', '.')}@d2cmedia.com",
                    subject=f"Approval Needed: Cancel {feed_name} - {dealer_name}",
                    body=approval_email,
                    email_type="cancellation_approval_request"
                )
                self._log(f"✓ Approval request sent to {rep_name}", "success")
                self._log("", "spacer")

                # STEP 3: Wait for Approval
                self._log("STEP 3: Waiting for rep approval...", "step")
                time.sleep(1.0)
                self._log("✓ Approval received from rep", "success")
                self._log("", "spacer")

            # ============================================================
            # PATH B: Rep Requester (no approval needed)
            # ============================================================
            else:
                self._log("STEP 1: Rep-initiated cancellation - no approval needed", "info")
                self._log("", "spacer")

            # ============================================================
            # STEP: Cancel Feed in System
            # ============================================================
            step_num = 4 if not requester_is_rep else 2
            self._log(f"STEP {step_num}: Cancelling feed in system", "step")
            time.sleep(0.5)

            feed_id = f"FEED-{dealer_id}-{feed_name[:4].upper()}"
            self._log(f"✓ Feed cancelled successfully", "success")
            self._log(f"  Feed ID: {feed_id}", "info")
            self._log(f"  Status: Cancelled", "info")
            self._log("", "spacer")

            # ============================================================
            # STEP: Log Cancellation to CSV
            # ============================================================
            step_num += 1
            self._log(f"STEP {step_num}: Logging cancellation to CSV", "step")
            time.sleep(0.3)

            self._log_cancellation(
                dealer_id=dealer_id,
                dealer_name=dealer_name,
                feed_name=feed_name,
                feed_type=feed_type,
                cancelled_by=rep_name if requester_is_rep else requester_email,
                feed_id=feed_id
            )
            self._log("✓ Cancellation logged successfully", "success")
            self._log("", "spacer")

            # ============================================================
            # STEP: Notify Syndicator
            # ============================================================
            step_num += 1
            self._log(f"STEP {step_num}: Notifying syndicator of cancellation", "step")
            time.sleep(0.4)

            # Only notify if 3rd party didn't request it (they already know)
            if requester_is_rep:
                notification_email = self._generate_syndicator_notification_email(
                    feed_name, dealer_name, feed_id
                )
                self._send_email(
                    to=f"support@{feed_name.lower().replace(' ', '')}.com",
                    subject=f"Feed Cancelled: {dealer_name}",
                    body=notification_email,
                    email_type="syndicator_notification"
                )
                self._log(f"✓ Syndicator notified of cancellation", "success")
            else:
                self._log(f"✓ Syndicator notification skipped (requester already aware)", "info")

            self._log("", "spacer")

            # ============================================================
            # STEP: Update Ticket Status
            # ============================================================
            step_num += 1
            self._log(f"STEP {step_num}: Updating ticket status", "step")
            time.sleep(0.2)
            self._log("✓ Ticket marked as 'Closed - Automated'", "success")
            self._log("", "spacer")

            execution_time = round(time.time() - start_time, 2)
            self._log(f"🎉 CANCELLATION COMPLETE in {execution_time}s", "header")

            return {
                "success": True,
                "automated": True,
                "execution_log": self.execution_log,
                "emails_sent": self.emails_sent,
                "internal_comments": self.internal_comments,
                "execution_time": execution_time,
                "resolution_status": "Closed - Automated",
                "feed_cancelled": {
                    'feed_id': feed_id,
                    'dealer_id': dealer_id,
                    'dealer_name': dealer_name,
                    'feed_name': feed_name,
                    'feed_type': feed_type,
                    'status': 'Cancelled'
                }
            }

        except Exception as e:
            self._log(f"❌ Automation failed: {str(e)}", "error")
            return {
                "success": False,
                "automated": False,
                "execution_log": self.execution_log,
                "emails_sent": self.emails_sent,
                "internal_comments": self.internal_comments,
                "error": str(e)
            }

    # ============================================================
    # Email Generation Methods
    # ============================================================

    def _generate_acknowledgment_email(self, contact_name: str, feed_name: str, feed_type: str) -> str:
        """Generate acknowledgment email"""
        return f"""Hi {contact_name},

Thanks for reaching out. I will take a look at this {feed_type} feed request and get back to you soon.

Thanks,
AI Support Agent
D2CMedia Support Team"""

    def _generate_billing_comment(self, dealer_name: str, dealer_id: str, feed_name: str, feed_type: str) -> str:
        """Generate internal billing comment"""
        return f"""@billing - Please verify if an order is required for this setup:

Dealer: {dealer_name} (ID: {dealer_id})
Feed: {feed_name} ({feed_type})

Thanks!"""

    def _generate_order_request_email(self, rep_name: str, dealer_name: str, feed_name: str, feed_type: str, billing_info: Dict) -> str:
        """Generate order request email to rep"""
        package = billing_info.get('Package Type', 'Premium')
        fee = billing_info.get('Monthly Fee', '$99')

        return f"""Hi {rep_name},

We received a request to set up {feed_name} {feed_type} for {dealer_name}.

According to billing, this requires a new order:
- Package: {package}
- Monthly Fee: {fee}

Could you please work with the client to place the order? Once confirmed, I'll proceed with the setup.

Thanks,
AI Support Agent
D2CMedia Support Team"""

    def _generate_approval_request_email(self, rep_name: str, dealer_name: str, feed_name: str, feed_type: str, requester_email: str) -> str:
        """Generate approval request email to rep"""
        return f"""Hi {rep_name},

We received a request from {requester_email} to set up {feed_name} {feed_type} for {dealer_name}.

No order is required (included in existing package), but I wanted to confirm with you before proceeding with the setup.

Can you approve this request?

Thanks,
AI Support Agent
D2CMedia Support Team"""

    def _generate_confirmation_email(self, contact_name: str, dealer_name: str, feed_name: str, feed_type: str, feed_config: Dict) -> str:
        """Generate final confirmation email"""
        return f"""Hi {contact_name},

Great news! The {feed_name} {feed_type} feed has been successfully configured for {dealer_name}.

Feed Details:
- Feed ID: {feed_config['feed_id']}
- Feed URL: {feed_config['feed_url']}
- Status: Active
- Inventory Type: {feed_config.get('inventory_type', 'All')}

The feed is now live and will sync automatically. Please allow 24-48 hours for initial data population.

If you have any questions, feel free to reach out!

Best regards,
AI Support Agent
D2CMedia Support Team"""

    def _generate_cancellation_acknowledgment_email(self, contact_name: str, feed_name: str, dealer_name: str) -> str:
        """Generate cancellation acknowledgment email"""
        return f"""Hi {contact_name},

Thanks for letting us know about the {feed_name} cancellation for {dealer_name}. We will proceed with disabling the feed and get back to you shortly.

Thanks,
AI Support Agent
D2CMedia Support Team"""

    def _generate_cancellation_approval_email(self, rep_name: str, dealer_name: str, feed_name: str, requester_email: str) -> str:
        """Generate cancellation approval request email to rep"""
        return f"""Hi {rep_name},

We received a request from {requester_email} to cancel the {feed_name} feed for {dealer_name}.

Can you approve this cancellation request?

Thanks,
AI Support Agent
D2CMedia Support Team"""

    def _generate_syndicator_notification_email(self, feed_name: str, dealer_name: str, feed_id: str) -> str:
        """Generate syndicator notification email"""
        return f"""Hi {feed_name} Team,

This is to inform you that the feed for {dealer_name} (Feed ID: {feed_id}) has been cancelled and is no longer active.

Please update your systems accordingly.

Best regards,
AI Support Agent
D2CMedia Support Team"""

    # ============================================================
    # Helper Methods
    # ============================================================

    def _check_billing_requirements(self, dealer_id: str) -> Tuple[bool, Dict]:
        """Check if order is required for dealer"""
        if self.billing_data.empty:
            return False, {}

        dealer_row = self.billing_data[self.billing_data['Dealer ID'].astype(str) == str(dealer_id)]

        if dealer_row.empty:
            return False, {"Notes": "Dealer not found in billing database"}

        order_required = dealer_row.iloc[0]['Order Required'].strip().lower() == 'yes'
        billing_info = {
            'Package Type': dealer_row.iloc[0]['Package Type'],
            'Monthly Fee': dealer_row.iloc[0]['Monthly Fee'],
            'Notes': dealer_row.iloc[0]['Notes']
        }

        return order_required, billing_info

    def _configure_feed(self, dealer_id: str, dealer_name: str, feed_name: str, feed_type: str, inventory_type: str) -> Dict:
        """Simulate feed configuration"""
        feed_id = f"FEED-{dealer_id}-{feed_name[:4].upper()}"
        feed_url = f"https://feeds.d2cmedia.com/{dealer_id}/{feed_name.lower().replace(' ', '-')}"

        return {
            'feed_id': feed_id,
            'feed_url': feed_url,
            'dealer_id': dealer_id,
            'dealer_name': dealer_name,
            'feed_name': feed_name,
            'feed_type': feed_type,
            'inventory_type': inventory_type,
            'status': 'Active'
        }

    def _send_email(self, to: str, subject: str, body: str, email_type: str):
        """Log an email as sent"""
        self.emails_sent.append({
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'to': to,
            'subject': subject,
            'body': body,
            'type': email_type
        })

    def _add_internal_comment(self, comment: str, tagged_users: List[str], comment_type: str):
        """Log an internal comment"""
        self.internal_comments.append({
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'comment': comment,
            'tagged_users': tagged_users,
            'type': comment_type
        })

    def _log(self, message: str, level: str = "info"):
        """Add entry to execution log"""
        self.execution_log.append({
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "message": message,
            "level": level  # header, step, info, success, warning, error, spacer
        })

    def _log_cancellation(self, dealer_id: str, dealer_name: str, feed_name: str, feed_type: str, cancelled_by: str, feed_id: str):
        """Log cancellation to CSV"""
        import os
        cancellation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_row = pd.DataFrame([{
            'Cancellation Date': cancellation_date,
            'Dealer ID': dealer_id,
            'Dealer Name': dealer_name,
            'Feed Name': feed_name,
            'Feed Type': feed_type,
            'Cancelled By': cancelled_by,
            'Reason': 'Automated cancellation request',
            'Feed ID': feed_id
        }])

        csv_path = "data/cancelled_feeds.csv"

        # If file exists, append; otherwise create new
        if os.path.exists(csv_path):
            existing_data = pd.read_csv(csv_path, encoding="utf-8")
            updated_data = pd.concat([existing_data, new_row], ignore_index=True)
        else:
            updated_data = new_row

        updated_data.to_csv(csv_path, index=False, encoding="utf-8")
