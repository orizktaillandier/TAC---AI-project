# 📚 Knowledge Base Builder Demo

## Two Separate Applications

We now have **TWO separate applications** for your hackathon demo:

### 1. 🎯 Ticket Classification System (`demo_app.py`)
The original AI-powered ticket classification system with:
- Ticket Classification with GPT-5
- Sentiment Analysis
- Proactive Issue Detection
- Client Health Monitoring
- Revenue Impact Analysis
- Automation Engine

**To run:**
```bash
streamlit run demo_app.py
```
Opens at: http://localhost:8501

### 2. 📚 Knowledge Base Builder (`kb_builder_app.py`)
The new documentation system your boss requested with:
- Automatic KB article generation from resolved tickets
- Coverage gap analysis
- Smart search and similarity matching
- Knowledge base dashboard
- Export/Import functionality

**To run:**
```bash
streamlit run kb_builder_app.py
```
Opens at: http://localhost:8505

## Files Created

### Core Modules
- `knowledge_base.py` - KB management system
- `documentation_generator.py` - AI-powered article generator
- `sentiment_analysis.py` - Enhanced sentiment analysis
- `proactive_detection.py` - System-wide pattern detection

### Data
- `mock_data/resolved_tickets.json` - Sample resolved tickets for demo

### Applications
- `demo_app.py` - Original classification system (unchanged)
- `kb_builder_app.py` - New KB Builder application

## Demo Strategy

**Phase 1: Show KB Builder First**
1. Run `kb_builder_app.py`
2. Show how it generates documentation from resolved tickets
3. Demonstrate coverage analysis and gap identification
4. Show search and similarity matching
5. Emphasize: "Well-maintained KB = foundation for automation"

**Phase 2: Show Classification System**
1. Run `demo_app.py`
2. Show existing classification capabilities
3. Mention how KB articles could enable auto-resolution
4. Let them make the connection to full automation

## Key Features to Highlight

### Knowledge Base Builder
✅ **Automatic Documentation** - AI generates articles from resolutions
✅ **Gap Analysis** - Identifies missing documentation
✅ **Smart Search** - Finds relevant articles instantly
✅ **Coverage Tracking** - Ensures comprehensive documentation
✅ **Quality Control** - Tracks helpful articles and views

### Business Value
- **Faster Resolution** - Agents find answers immediately
- **Consistency** - Same solution every time
- **Training** - New agents learn faster
- **Foundation** - Enables future automation

## Notes
- Both apps run independently
- All data is mock/sample data for security
- OpenAI API key needed for article generation (optional)
- Apps can run simultaneously on different ports

## Your Boss's Vision
"If the knowledge base is well maintained, we then have the solution for every ticket"
→ This KB Builder directly addresses that vision!