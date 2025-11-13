# 🎫 Self-Improving Ticket Resolution System

## The Complete Flow

This system implements an **intelligent, self-improving ticket resolution workflow** that gets smarter with every ticket:

```
📥 Ticket arrives
   ↓
🎯 AI classifies ticket (category, tier, priority, syndicator, provider)
   ↓
💡 AI suggests relevant KB articles with confidence scores
   ↓
👤 Agent tries suggested solution
   ↓
✅ Did it work?
   ├─ YES → ✓ Update success stats, done!
   └─ NO → Show edge cases OR collect new resolution
          ↓
      🤖 AI analyzes: Add new? Update? Edge case?
          ↓
      📚 KB intelligently updated
```

## Key Features

### 1. Intelligent KB Management

The system **never blindly adds** knowledge. AI decides:

- **Add New Article**: Truly new issue type not in KB
- **Update Existing**: Better solution for existing issue
- **Add Edge Case**: Variant of existing issue (same root cause, different symptoms)
- **Merge**: Duplicate articles detected
- **None**: Resolution doesn't add value to KB

### 2. Edge Case Tracking

When a standard solution doesn't work:
- System shows **relevant edge cases** based on context (syndicator, provider, category)
- Edge cases are **ranked by relevance** and success rate
- Each edge case tracks its own success rate and usage
- Prevents KB bloat while capturing important variations

### 3. Company SOPs Preloaded

Starts with 8 realistic SOPs covering:
- Kijiji API issues
- PBS/Polk imports
- AutoTrader pricing
- Facebook photos
- CarGurus duplicates
- CDK/DMS integration
- Feature mapping
- Website caching

### 4. Self-Improving Loop

Every ticket resolution:
- Updates article success rates
- Tracks what works and what doesn't
- Identifies low-performing articles for review
- Suggests KB cleanup (archive outdated, merge duplicates)

## Applications

### App 1: Ticket Resolution Flow (`ticket_resolution_flow.py`)
**The Main Demo** - Shows the complete self-improving loop

```bash
streamlit run ticket_resolution_flow.py --server.port 8501
```

**What it demonstrates:**
1. Ticket classification with AI
2. KB article suggestions with confidence scores
3. Resolution feedback loop
4. Edge case handling
5. Intelligent KB updates (add/update/edge case decisions)

**Use this to show Pierre-Olivier** the complete vision!

### App 2: KB Builder (`kb_builder_app.py`)
**KB Management Dashboard**

```bash
streamlit run kb_builder_app.py --server.port 8505
```

Features:
- Coverage analysis
- Generate articles from resolved tickets
- KB dashboard
- Search & match
- **Nuclino-like browser** with AI search

### App 3: Ticket Classifier (`demo_app.py`)
**Original classification demo**

```bash
streamlit run demo_app.py --server.port 8502
```

## Architecture

### Core Modules

**`kb_intelligence.py`** - The Brain
- Analyzes resolutions and decides KB actions
- Tracks success rates and usage stats
- Manages edge cases
- Suggests KB cleanup

**`knowledge_base.py`** - The Storage
- Article management
- Similarity matching
- Coverage analysis
- Search functionality

**`documentation_generator.py`** - The Writer
- AI-powered article generation
- Improvement suggestions
- Extracts structure from plain text

**`ticket_classifier.py`** - The Classifier
- Multi-dimensional classification
- Category, tier, priority
- Syndicator/provider detection

**`kb_browser.py`** - The UI
- Nuclino-like interface
- AI-powered semantic search
- Multiple view modes

### Data

**`mock_data/company_sops.json`**
- 8 pre-loaded SOPs
- Realistic dealership support scenarios
- Edge cases included
- Success rate tracking

**`mock_data/resolved_tickets.json`**
- Sample resolved tickets for testing

## Demo Strategy

### Phase 1: The Problem
"Support tickets are repetitive. Same issues, different dealers. Knowledge is scattered."

### Phase 2: The Solution (Documentation)
Show `kb_builder_app.py`:
- "We can automatically generate KB articles from resolutions"
- "Agents find answers instantly with AI search"
- "KB stays current and comprehensive"

### Phase 3: The Magic (Self-Improvement)
Show `ticket_resolution_flow.py`:
- "System suggests solutions from KB"
- "When they don't work, edge cases are shown"
- "New resolutions are intelligently added"
- "AI decides: new article, update, or edge case"
- **"KB gets smarter with every ticket"**

### Phase 4: The Vision (Full Automation)
"Once KB is comprehensive enough..."
- Auto-suggest solutions when ticket arrives
- Auto-resolve common issues
- Only escalate truly new or complex cases
- Complete audit trail

## Key Differentiators

### vs Traditional KB Systems:
- ❌ Manual article creation → ✅ AI-generated from resolutions
- ❌ Static articles → ✅ Success rate tracking and updates
- ❌ No edge case tracking → ✅ Context-aware edge cases
- ❌ KB bloat over time → ✅ Intelligent add/update/edge case decisions
- ❌ Keyword search → ✅ AI semantic search

### Business Value:
1. **Faster Resolution**: Agents find answers immediately
2. **Consistency**: Same solution every time
3. **Training**: New agents learn faster
4. **Scalability**: Knowledge captured and reused
5. **Foundation**: Enables full automation

## Technical Requirements

```bash
pip install streamlit openai python-dotenv
```

**Environment Variables** (`.env`):
```
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini
```

## Running the Demo

### Quick Start (Main Demo):
```bash
cd demo
streamlit run ticket_resolution_flow.py
```

### All Apps:
```bash
# Terminal 1: Main ticket resolution flow
streamlit run ticket_resolution_flow.py --server.port 8501

# Terminal 2: KB management dashboard
streamlit run kb_builder_app.py --server.port 8505

# Terminal 3: Original classifier
streamlit run demo_app.py --server.port 8502
```

## Demo Flow

### Test Case 1: Known Issue (Kijiji)
1. Use "Kijiji Feed Issue" template
2. System finds existing SOP
3. Agent marks "Yes, it worked!"
4. Shows success rate updated

### Test Case 2: Edge Case (Kijiji Account Suspended)
1. Use Kijiji template
2. Mark "No, didn't work"
3. System shows edge case for account suspension
4. Agent can mark edge case as successful

### Test Case 3: New Issue
1. Use "New Issue Type" template
2. No KB articles match
3. Agent provides resolution
4. AI analyzes → "Add New Article"
5. New article created

### Test Case 4: Better Solution Found
1. Use PBS template
2. Mark "No, didn't work"
3. Provide better solution
4. AI analyzes → "Update Existing"
5. Article updated with better solution

## What Makes This Special

### The Intelligence Layer
Other systems just store articles. This system:
- **Learns** from every resolution
- **Adapts** articles based on success rates
- **Prevents bloat** with smart add/update decisions
- **Tracks context** with edge cases
- **Self-maintains** with cleanup suggestions

### The Edge Case Innovation
Most KBs handle edge cases poorly:
- Traditional: Create separate articles (causes bloat)
- This system: Nested edge cases with context matching

### The Phased Approach
You're not "scaring them" with automation. You're showing:
1. Documentation → problem everyone agrees on
2. Self-improvement → clear value add
3. Automation → natural next step

## Success Metrics to Track

- **Coverage**: % of tickets with matching KB article
- **Success Rate**: % of suggested solutions that work
- **Time to Resolution**: Before vs after KB implementation
- **Agent Confidence**: Surveys show increased confidence
- **KB Growth**: Healthy growth rate (not exponential bloat)

## Next Steps (Post-Demo)

If approved:
1. **Import actual SOPs** from your company
2. **Connect to ticket system** (Zendesk, Jira, etc.)
3. **Deploy to staging** for pilot team
4. **Collect metrics** over 30 days
5. **Expand to full team**
6. **Phase in automation** based on confidence thresholds

## Files Created

Core:
- `kb_intelligence.py` - Smart KB update manager
- `kb_browser.py` - Nuclino-like interface
- `ticket_resolution_flow.py` - Complete workflow demo

Data:
- `mock_data/company_sops.json` - 8 preloaded SOPs

## The Pitch

**"Every ticket makes us smarter. Every resolution improves the KB. Eventually, the system can resolve most tickets automatically - but we start by building the foundation: comprehensive, accurate, always-current documentation that your team can trust."**

This addresses Pierre-Olivier's vision perfectly:
> "If the knowledge base is well maintained, we then have the solution for every ticket"

You're building that well-maintained KB **automatically**, with AI ensuring quality and preventing bloat.

---

Built for Cars Commerce Hackathon Fall 2025
