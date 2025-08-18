# Automotive Ticket Classifier

A modern, AI-powered system for classifying automotive syndication support tickets using OpenAI GPT models. The system automatically extracts key information from tickets, including dealer information, categories, and syndicators.

## Features

- **AI-Powered Classification**: Uses OpenAI GPT models to analyze and classify tickets
- **Bilingual Support**: Works with both English and French tickets
- **Robust Dealer Recognition**: Accurately identifies dealers from various text patterns
- **Zoho Desk Integration**: Seamlessly integrates with Zoho Desk API
- **Batch Processing**: Efficiently classifies and updates multiple tickets
- **Performance Optimization**: Includes Redis caching for improved performance
- **User-Friendly Interface**: Streamlit UI for easy interaction
- **Comprehensive Analytics**: Track classification performance and metrics
- **Containerization**: Docker and Docker Compose support for easy deployment
- **Database Persistence**: Stores classifications and audit logs in PostgreSQL

## System Architecture

The system consists of the following components:

- **FastAPI Backend**: RESTful API for ticket classification and Zoho integration
- **Streamlit Frontend**: User-friendly interface for interacting with the system
- **PostgreSQL Database**: Stores classifications, mappings, and audit logs
- **Redis Cache**: Improves performance by caching common operations
- **Docker**: Containerization for easy deployment and scaling

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Zoho Desk API credentials
- OpenAI API key
- CSV files for syndicators and dealer mappings

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/auto-ticket-classifier.git
   cd auto-ticket-classifier
   ```

2. Copy the example environment file and update with your credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. Place your CSV files in the `data` directory:
   - `syndicators.csv`: List of syndicators
   - `rep_dealer_mapping.csv`: Mapping of dealers to reps

4. Start the services using Docker Compose:
   ```bash
   docker-compose up -d
   ```

5. Access the UI at http://localhost:8501

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Application environment (development, staging, production, user) | development |
| `DEBUG` | Enable debug mode | true |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OPENAI_MODEL` | OpenAI model to use | gpt-4o-mini |
| `ZOHO_CLIENT_ID` | Zoho client ID | - |
| `ZOHO_CLIENT_SECRET` | Zoho client secret | - |
| `ZOHO_REFRESH_TOKEN` | Zoho refresh token | - |
| `ZOHO_BASE_URL` | Zoho API base URL | https://desk.zoho.com/api/v1 |
| `ZOHO_ORG_ID` | Zoho organization ID | - |
| `POSTGRES_USER` | PostgreSQL username | postgres |
| `POSTGRES_PASSWORD` | PostgreSQL password | postgres |
| `POSTGRES_DB` | PostgreSQL database name | auto_classifier |
| `USE_REDIS` | Enable Redis caching | true |
| `SECRET_KEY` | Secret key for authentication | change_this_in_production |

## API Endpoints

### Classification

- **POST /classify**: Classify a single ticket
- **POST /jobs/classify-push-batch**: Classify a batch of tickets

### Zoho Integration

- **POST /push**: Push a classification to Zoho
- **GET /tickets/{ticket_id}**: Get a ticket from Zoho
- **GET /tickets/{ticket_id}/threads**: Get threads for a ticket

### Monitoring

- **GET /health**: Health check endpoint
- **GET /metrics**: Service metrics endpoint

## UI Pages

- **Classifier**: Classify tickets by ID or text
- **Ticket Management**: Batch classify and manage tickets
- **Analytics**: View performance metrics and statistics
- **Settings**: Configure application settings

## Data Structure

The system classifies tickets with the following fields:

- **contact**: Contact person
- **dealer_name**: Dealer name
- **dealer_id**: Dealer ID
- **rep**: Rep name
- **category**: Ticket category
- **sub_category**: Ticket sub-category
- **syndicator**: Syndicator
- **inventory_type**: Inventory type

## Development

### Running Locally

To run the services locally without Docker:

1. Install Python dependencies:
   ```bash
   # API
   cd api
   pip install -r requirements.txt
   
   # UI
   cd ui
   pip install -r requirements.txt
   ```

2. Start the API:
   ```bash
   cd api
   uvicorn main:app --reload --port 8088
   ```

3. Start the UI:
   ```bash
   cd ui
   streamlit run main.py
   ```

### Database Migrations

The system uses Alembic for database migrations:

```bash
cd api
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

## Testing

Run tests using pytest:

```bash
cd api
pytest
```

## Production Deployment

For production deployment, make the following changes:

1. Set `ENVIRONMENT=production` in the `.env` file
2. Generate a secure `SECRET_KEY`
3. Use a managed database service instead of the Docker PostgreSQL container
4. Set up proper authentication for the UI
5. Configure proper logging and monitoring

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for providing the GPT models
- FastAPI and Streamlit for the excellent frameworks
- All contributors and users of this project