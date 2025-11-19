# Required Files Documentation
## Last Updated: 2025-11-18
## Status: COMPLETE INVENTORY

---

## ESSENTIAL FILES - DO NOT DELETE

### 🎯 Main Entry Point
- **unified_kb_system.py** - Main application entry, navigation system

### 📱 Core Interfaces (4 Main Apps)
1. **demo_app.py** - Agent Interface (ticket classification & resolution)
2. **kb_browser.py** - Knowledge Base Browser interface
3. **kb_agent_chat.py** - KB Management Chat interface
4. **kb_audit_dashboard.py** - Feedback & Audit Dashboard

### 🧠 Core AI/Processing Modules
- **classifier.py** - Ticket classification engine (GPT-5)
- **knowledge_base.py** - KB management, search, and storage
- **documentation_generator.py** - Auto-generates KB articles from tickets
- **kb_intelligence.py** - Intelligent KB matching and suggestions

### 📊 Supporting Intelligence Modules
- **sentiment_analysis.py** - Analyzes ticket sentiment
- **proactive_detection.py** - Detects patterns across tickets
- **pattern_monitor.py** - Caches pattern detection results
- **feedback_manager.py** - Manages agent feedback on KB articles
- **kb_audit_log.py** - Tracks KB usage and effectiveness
- **kb_health_monitor.py** - Monitors KB health metrics

### 🚀 Additional Features
- **automation_engine.py** - Automation workflows
- **sales_intelligence.py** - Sales opportunity detection
- **upsell_intelligence.py** - Upsell opportunity analysis
- **client_health.py** - Client health scoring
- **ticket_resolution_flow.py** - Resolution workflow management

### 📦 Utility Scripts
- **generate_embeddings.py** - Generate embeddings for KB articles

### 🔧 Configuration Files
- **.env** - Environment variables (API keys, model settings)
- **requirements.txt** - Python package dependencies

### 📚 Documentation
- **README.md** - Main documentation
- **README_KB.md** - KB system documentation
- **README_COMPLETE_SYSTEM.md** - Complete system overview
- **DEMO_WALKTHROUGH.md** - Demo presentation guide

---

## DATA FILES - REQUIRED

### Mock Data (mock_data/)
- **knowledge_base.json** - KB articles storage
- **resolved_tickets.json** - Historical resolved tickets
- **company_sops.json** - Company-specific SOPs
- **pending_feedback.json** - Pending agent feedback
- **kb_audit_log.json** - KB audit trail
- **sample_tickets.json** - Sample tickets for testing

### Reference Data (data/)
- **syndicators.csv** - Syndicator definitions
- **import_providers.csv** - Import provider definitions
- **rep_dealer_mapping.csv** - Rep to dealer mappings
- **dealer_revenue.json** - Dealer revenue data
- **dealership_billing_requirements.csv** - Billing requirements
- **cancelled_feeds.csv** - Cancelled feed tracking

---

## TEMPORARY/CLEANUP FILES - CAN BE REMOVED

### Temporary Scripts (One-time use)
- **fix_demo_app.py** - One-time fix script
- **fix_indentation.py** - One-time indentation fix
- **restructure_app.py** - One-time restructuring script
- **simplify_kb.py** - One-time simplification script
- **remove_company_names.py** - One-time company name removal
- **clear_feedback.py** - Utility to clear feedback
- **test_workflow.py** - Testing script

### Deprecated/Unused
- **kb_builder_app.py** - OLD KB builder interface (replaced by kb_agent_chat.py)

### Backup Files
- **.env.backup** - Backup of .env file
- **.env.example** - Example .env template

---

## DEPENDENCIES MATRIX

```
unified_kb_system.py
├── demo_app.py
│   ├── classifier.py
│   ├── knowledge_base.py
│   ├── sentiment_analysis.py
│   └── proactive_detection.py
├── kb_browser.py
│   └── knowledge_base.py
├── kb_agent_chat.py
│   └── knowledge_base.py
└── kb_audit_dashboard.py
    ├── feedback_manager.py
    └── kb_audit_log.py

Supporting Modules:
- documentation_generator.py (used by multiple)
- kb_intelligence.py (used by knowledge_base.py)
- pattern_monitor.py (used by demo_app.py)
- kb_health_monitor.py (monitoring)
- automation_engine.py (automation)
- sales/upsell_intelligence.py (opportunity detection)
- client_health.py (client metrics)
```

---

## ENVIRONMENT REQUIREMENTS

### Required in .env:
```
OPENAI_API_KEY=<your-key>
OPENAI_MODEL=gpt-5-mini
OPENAI_REASONING_EFFORT=low
```

### Python Packages (requirements.txt):
- streamlit
- openai
- pandas
- numpy
- python-dotenv
- scikit-learn
- plotly

---

## TOTAL FILE COUNT
- **Essential Python Files:** 22
- **Data/Config Files:** 12
- **Documentation:** 4
- **Temporary/Removable:** 10

## VERIFIED WORKING
✅ All 4 main interfaces tested and working
✅ All supporting modules load successfully
✅ All required data files present
✅ GPT-5 API properly configured across all files