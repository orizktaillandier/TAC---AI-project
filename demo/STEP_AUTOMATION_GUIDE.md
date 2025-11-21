# Step Automation Guide

## Overview
The step automation system automatically detects and fetches data from the Admin Dashboard for KB article steps, making the resolution process faster and more efficient.

## Comprehensive Pattern Matching

The system uses **6 comprehensive pattern categories** to detect automatable steps:

### 1. Dealer Profile/Info Access
**Patterns Detected:**
- "Log into Admin Dashboard"
- "Search for dealer name"
- "Click on dealer's name"
- "Open their profile"
- "Navigate to dealer"
- "Access dealer page"
- "Click 'Clients' in sidebar"

**Data Fetched:**
- Dealer ID
- Account Status
- Last Login
- Dealer Name

### 2. Exports/Imports Tab Access
**Patterns Detected:**
- "Click the 'Exports' tab"
- "Click the 'Imports' tab"
- "Check both 'Imports' and 'Exports' tabs"
- "View exports"
- "View imports"
- "Export section"
- "Import section"

**Data Fetched:**
- All export feeds with status
- All import feeds with status
- Feed names and status badges

### 3. Feed Status Check
**Patterns Detected:**
- "Check feed status"
- "Verify status"
- "Find syndicator name"
- "Check if syndicator is listed"
- "Look for Active status"
- "Check if feed exists"
- "Verify feed is working"

**Data Fetched:**
- Specific feed status (if feed name mentioned)
- All feeds status (if no specific feed)
- Active/Inactive/Error status
- Last updated timestamp

### 4. Last Updated/Timestamp Check
**Patterns Detected:**
- "Check Last Updated"
- "Check timestamp"
- "Verify last activity"
- "Check Last Export"
- "Recent update"
- "Within X hours"
- "How recent"

**Data Fetched:**
- Last updated timestamp (formatted)
- Most recent feed activity
- Time since last update

### 5. Activity Log Review
**Patterns Detected:**
- "Review Activity Log"
- "Check log"
- "Review recent operations"
- "Check activity"
- "View operations"
- "Check if sold vehicles removed"
- "Recent changes"

**Data Fetched:**
- Recent activity entries (top 10)
- Operation timestamps
- Action types and status
- Activity count

### 6. Status Verification After Action
**Patterns Detected:**
- "Verify the status changed"
- "Confirm status is"
- "Check that status is"
- "Ensure status is"
- "Status changed to"

**Data Fetched:**
- Current feed status
- Verification of status changes

## How It Works for Future Articles

The system is designed to work with **any future KB article** because:

1. **Flexible Pattern Matching**: Uses keyword-based detection, not exact string matching
2. **Multiple Variations**: Catches common variations of the same action
3. **Context-Aware**: Uses ticket context (dealer name, syndicator, provider) to fetch relevant data
4. **Graceful Fallbacks**: If specific feed isn't found, falls back to showing all feeds
5. **No Hardcoding**: Patterns are generic enough to work with new article structures

## Examples

### Example 1: "Log into Admin Dashboard"
- **Detected as**: Dealer Profile Access
- **Auto-fetches**: Dealer ID, Account Status, Last Login
- **Shows**: Dealer info card inline with step

### Example 2: "Check both 'Imports' and 'Exports' tabs"
- **Detected as**: Tab Access (Both)
- **Auto-fetches**: All export and import feeds
- **Shows**: Complete feeds table with status badges

### Example 3: "Check the 'Last Updated' timestamp"
- **Detected as**: Timestamp Check
- **Auto-fetches**: Most recent feed update time
- **Shows**: Formatted timestamp (e.g., "2 hours ago")

### Example 4: "Review 'Activity Log' for recent operations"
- **Detected as**: Activity Log Review
- **Auto-fetches**: Top 10 recent activities
- **Shows**: Activity log with timestamps and actions

## Adding New Patterns

If you need to add support for new step patterns:

1. Identify the common keywords/phrases
2. Add them to the appropriate pattern list in `step_automation.py`
3. Ensure the pattern matches the intent (dealer info, feed status, etc.)
4. Test with existing articles to ensure no conflicts

## Best Practices for KB Article Authors

To maximize automation coverage when writing KB articles:

1. **Use Standard Phrases**: 
   - ✅ "Check feed status" (automated)
   - ❌ "Look at the feed thing" (not automated)

2. **Mention Tabs Explicitly**:
   - ✅ "Click the 'Exports' tab" (automated)
   - ❌ "Go to exports" (may not be automated)

3. **Use Clear Action Words**:
   - ✅ "Verify", "Check", "Review", "Find" (automated)
   - ❌ Vague descriptions (may not be automated)

4. **Include Context**:
   - Steps that mention "dealer", "feed", "status", "timestamp" are more likely to be automated

## Testing

The system has been tested with:
- All existing KB articles in `knowledge_base.json`
- Various step phrasings and structures
- Different combinations of dealer/syndicator/provider context

## Future Enhancements

Potential improvements:
- Machine learning-based pattern recognition
- Custom pattern definitions per article category
- Integration with real Admin Dashboard API
- Support for more data types (inventory counts, error messages, etc.)

