# AI-Powered Ticket Classification System

**Hackathon Demo - Fall 2025**

An intelligent system that automatically classifies support tickets using GPT-5, predicts churn risk, identifies upsell opportunities, and detects sales opportunities from ticket content.

---

## 🎯 What This Does

- **Ticket Classification**: GPT-5 powered classification with 82% accuracy
- **Client Health Scoring**: 0-100 health score with churn prediction
- **Revenue Impact Dashboard**: Real-time tracking of $202K ARR portfolio
- **AI Upsell Intelligence**: Identifies $36K in upsell opportunities
- **Sales Opportunity Detection**: Finds expansion opportunities from tickets
- **Tier-based Automation**: Routes tickets (Tier 1/2/3) automatically

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Python 3.11+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Setup

```bash
# Clone the repository
git clone https://github.com/orizktaillandier/TAC---AI-project.git
cd TAC---AI-project/demo

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your OpenAI API key

# Run the demo
streamlit run demo_app.py
```

The app will open at `http://localhost:8501`

---

## 📊 Business Impact

### Cost Savings
- **$45K/year** automation efficiency (1,825 tickets/year)
- **30 minutes saved** per Tier 1 ticket

### Revenue Protection
- **$83K at-risk** identified through churn analysis
- Proactive intervention recommendations

### Revenue Generation
- **$36K** in upsell opportunities detected
- Real-time sales opportunity identification

### Performance
- **82% accuracy** on classification
- **~2 seconds** per ticket classification
- **$0.01 cost** per classification with GPT-5-mini

---

## 📁 Project Structure

```
TAC---AI-project/
├── demo/                       # Main demo application
│   ├── demo_app.py            # Streamlit interface
│   ├── classifier.py          # GPT-5 classification
│   ├── automation_engine.py   # Tier routing logic
│   ├── client_health.py       # Health scoring & churn
│   ├── upsell_intelligence.py # Upsell detection
│   ├── sales_intelligence.py  # Sales opportunity detection
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example          # API key template
│   ├── README.md             # Detailed demo instructions
│   ├── data/                 # Mock business data
│   └── mock_data/            # Sample tickets
├── GITHUB_PREP.md            # GitHub push guide
├── READY_FOR_GITHUB.md       # Security summary
└── SECURITY_CHECKLIST.md     # Security audit
```

---

## 🎨 Features

### 1. Ticket Classification Dashboard
- Classify 11 sample tickets with GPT-5
- Extract contact, dealer, category, tier, syndicator
- View sentiment analysis and suggested responses
- See tier-based automation routing

### 2. Revenue Impact Dashboard
- Portfolio ARR tracking ($202K)
- Automation cost savings calculations
- Churn risk revenue analysis
- Tier distribution visualization

### 3. Client Health & Churn Prediction
- 0-100 health score per dealer
- Churn probability predictions
- Revenue at-risk calculations
- Proactive intervention suggestions

### 4. AI Upsell Intelligence
- Behavioral pattern analysis
- Package upgrade recommendations
- Revenue potential per dealer
- Priority and confidence scores

### 5. Sales Opportunity Detection
- Multi-location expansion opportunities
- Feature upgrade requests from tickets
- Revenue calculations per opportunity
- Real-time detection from support conversations

---

## 🔒 Security & Privacy

- ✅ **No real customer data** - All mock/demo data
- ✅ **No API keys in repo** - Template provided in `.env.example`
- ✅ **No production integrations** - Standalone demo
- ✅ **Comprehensive security audit** - See `SECURITY_CHECKLIST.md`

---

## 🛠️ Technology Stack

- **Python 3.11+** - Core language
- **Streamlit** - Web interface
- **OpenAI GPT-5** - AI classification (gpt-5-mini)
- **Pandas** - Data manipulation
- **Mock Data** - No database required

---

## 📖 Documentation

- **[Demo README](demo/README.md)** - Detailed setup and features
- **[Security Checklist](SECURITY_CHECKLIST.md)** - Security audit details
- **[GitHub Prep Guide](GITHUB_PREP.md)** - Deployment instructions

---

## 🎯 Use Cases

### For Support Teams
- Instant ticket routing (no manual triage)
- Automated responses for Tier 1 tickets
- Faster response times = happier customers

### For Account Managers
- Proactive churn prevention alerts
- Revenue-at-risk visibility
- Upsell opportunity notifications

### For Sales Teams
- Real-time expansion opportunities
- Multi-location lead detection
- Feature upgrade requests from support

### For Leadership
- Portfolio health visibility
- Revenue impact metrics
- ROI tracking ($45K savings + $36K opportunities)

---

## 🏆 What Makes This Special

1. **Money-Focused**: Shows actual $ impact, not just "saves time"
2. **Predictive**: Identifies issues BEFORE they become problems
3. **Production-Ready**: Clean architecture, proper error handling
4. **Privacy-First**: Mock data, secure API key management

---

## 📧 Questions?

- **Repository**: https://github.com/orizktaillandier/TAC---AI-project
- **Setup Issues**: See [demo/README.md](demo/README.md)
- **Security Concerns**: See [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md)

---

**Built for the Cars Commerce Hackathon Fall 2025**
