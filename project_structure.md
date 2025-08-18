# Automotive Ticket Classifier

## Project Structure

```
auto-ticket-classifier/
├── docker-compose.yml           # All services definition
├── .env                         # Environment variables (from your existing file)
├── README.md                    # Project documentation
│
├── api/                         # FastAPI service
│   ├── Dockerfile
│   ├── main.py                  # API entrypoint
│   ├── requirements.txt
│   ├── alembic/                 # Database migrations
│   ├── app/
│   │   ├── __init__.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py        # Configuration management
│   │   │   ├── security.py      # Authentication
│   │   │   └── logging.py       # Logging setup
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── session.py       # Database session management
│   │   │   └── models/          # SQLAlchemy models
│   │   ├── schemas/             # Pydantic models
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py          # Dependency injection
│   │   │   ├── endpoints/       # API routes
│   │   │   └── error_handlers.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── classifier.py    # Core classification logic
│   │   │   ├── zoho.py          # Zoho API integration
│   │   │   ├── openai.py        # OpenAI integration
│   │   │   └── cache.py         # Redis cache integration
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── dealer.py        # Dealer name extraction logic
│   │       ├── text.py          # Text preprocessing
│   │       └── validation.py    # Data validation
│   └── tests/                   # API tests
│
├── ui/                          # Streamlit UI
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                  # Streamlit entrypoint
│   └── pages/                   # Streamlit pages
│       ├── classifier.py        # Classification page
│       ├── management.py        # Ticket management
│       ├── analytics.py         # Performance analytics
│       └── settings.py          # Configuration page
│
├── data/                        # Data files
│   ├── syndicators.csv          # Syndicator mappings
│   ├── rep_dealer_mapping.csv   # Rep-dealer mappings
│   └── schema/                  # JSON schema files for validation
│
└── scripts/                     # Utility scripts
    ├── setup.sh                 # Setup script
    ├── backup.py                # Database backup
    └── seed_data.py             # Initialize data
```
