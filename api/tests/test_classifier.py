"""
Tests for the classifier service.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.classifier import ClassifierService


@pytest.fixture
def mock_db():
    """Mock database session."""
    return MagicMock()


@pytest.fixture
def mock_zoho_service():
    """Mock Zoho service."""
    mock = AsyncMock()
    mock.get_ticket_with_threads.return_value = ({
        "id": "123456",
        "subject": "Test Subject",
        "description": "Test Description",
    }, [])
    return mock


@pytest.fixture
def mock_cache_service():
    """Mock cache service."""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = True
    return mock


@pytest.fixture
def sample_ticket_text():
    """Sample ticket text for testing."""
    return """
Subject: Problem with Mazda Steele inventory

Hi Support,

We're having an issue with the inventory feed for Mazda Steele (ID: 2618).
Some vehicles are showing as available even though they were sold last week.

Can you please check the PBS import?

Thanks,
Véronique Fournier
"""


@pytest.fixture
def expected_classification():
    """Expected classification for the sample ticket."""
    return {
        "contact": "Véronique Fournier",
        "dealer_name": "Mazda Steele",
        "dealer_id": "2618",
        "rep": "Véronique Fournier",
        "category": "Problem / Bug",
        "sub_category": "Import",
        "syndicator": "",
        "inventory_type": ""
    }


@pytest.mark.asyncio
async def test_classify_ticket(
    mock_db, mock_zoho_service, mock_cache_service,
    sample_ticket_text, expected_classification
):
    """Test classify_ticket method."""
    # Mock the OpenAI API call
    with patch("app.services.classifier.ClassifierService._call_openai_classifier") as mock_call_openai:
        # Setup the mock to return a raw classification
        mock_call_openai.return_value = expected_classification
        
        # Create the classifier service
        service = ClassifierService(mock_db, mock_zoho_service, mock_cache_service)
        
        # Call the classify_ticket method
        fields, raw = await service.classify_ticket(
            ticket_id="123456",
            ticket_text=sample_ticket_text
        )
        
        # Verify the call to OpenAI
        mock_call_openai.assert_called_once()
        
        # Verify the returned fields match the expected classification
        assert fields == expected_classification
        assert raw == expected_classification
        
        # Verify cache was used
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_called_once()


@pytest.mark.asyncio
async def test_classify_ticket_with_cache(
    mock_db, mock_zoho_service, mock_cache_service,
    expected_classification
):
    """Test classify_ticket method with cache hit."""
    # Setup cache to return a result
    mock_cache_service.get.return_value = (expected_classification, expected_classification)
    
    # Create the classifier service
    service = ClassifierService(mock_db, mock_zoho_service, mock_cache_service)
    
    # Call the classify_ticket method
    fields, raw = await service.classify_ticket(ticket_id="123456")
    
    # Verify cache was used
    mock_cache_service.get.assert_called_once()
    
    # Verify OpenAI was not called
    assert fields == expected_classification
    assert raw == expected_classification


@pytest.mark.asyncio
async def test_classify_ticket_with_zoho(
    mock_db, mock_zoho_service, mock_cache_service,
    expected_classification
):
    """Test classify_ticket method with Zoho data."""
    # Mock the OpenAI API call
    with patch("app.services.classifier.ClassifierService._call_openai_classifier") as mock_call_openai:
        # Setup the mock to return a raw classification
        mock_call_openai.return_value = expected_classification
        
        # Create the classifier service
        service = ClassifierService(mock_db, mock_zoho_service, mock_cache_service)
        
        # Call the classify_ticket method with just a ticket ID
        fields, raw = await service.classify_ticket(ticket_id="123456")
        
        # Verify Zoho was called to get ticket data
        mock_zoho_service.get_ticket_with_threads.assert_called_once_with("123456")
        
        # Verify the call to OpenAI
        mock_call_openai.assert_called_once()
        
        # Verify the returned fields match the expected classification
        assert fields == expected_classification
        assert raw == expected_classification


@pytest.mark.asyncio
async def test_validate_classification(
    mock_db, mock_zoho_service, mock_cache_service,
    expected_classification
):
    """Test _validate_classification method."""
    # Create a raw classification with invalid values
    raw_classification = {
        "contact": "Véronique Fournier",
        "dealer_name": "Mazda Steele",
        "dealer_id": "2618",
        "rep": "Véronique Fournier",
        "category": "Invalid Category",  # Invalid
        "sub_category": "Invalid Sub Category",  # Invalid
        "syndicator": "Invalid Syndicator",  # Invalid
        "inventory_type": "Invalid Type"  # Invalid
    }
    
    # Create the classifier service with mocked _lookup_dealer
    service = ClassifierService(mock_db, mock_zoho_service, mock_cache_service)
    service._lookup_dealer = MagicMock(return_value={
        "dealer_name": "Mazda Steele",
        "dealer_id": "2618",
        "rep": "Véronique Fournier"
    })
    
    # Test the validation
    with patch("app.services.classifier.settings") as mock_settings:
        # Mock the valid values
        mock_settings.VALID_CATEGORIES = ["Problem / Bug", "Product Activation — New Client"]
        mock_settings.VALID_SUBCATEGORIES = ["Import", "Export"]
        mock_settings.VALID_INVENTORY_TYPES = ["New", "Used", "Demo", "New + Used"]
        service.approved_syndicators = set(["kijiji", "autotrader"])
        
        # Call the method
        result = service._validate_classification(raw_classification, "Sample text")
        
        # Verify invalid values were cleared
        assert result["contact"] == "Véronique Fournier"
        assert result["dealer_name"] == "Mazda Steele"
        assert result["dealer_id"] == "2618"
        assert result["rep"] == "Véronique Fournier"
        assert result["category"] == ""
        assert result["sub_category"] == ""
        assert result["syndicator"] == ""
        assert result["inventory_type"] == ""


@pytest.mark.asyncio
async def test_store_classification(
    mock_db, mock_zoho_service, mock_cache_service,
    expected_classification
):
    """Test store_classification method."""
    # Mock the database query
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = None  # No existing classification
    
    # Create the classifier service
    service = ClassifierService(mock_db, mock_zoho_service, mock_cache_service)
    
    # Call the method
    with patch("app.services.classifier.Classification") as mock_classification, \
         patch("app.services.classifier.AuditLog") as mock_audit_log:
        
        # Mock the new classification
        mock_new_classification = MagicMock()
        mock_classification.return_value = mock_new_classification
        
        # Call the method
        result = await service.store_classification(
            ticket_id="123456",
            classification=expected_classification,
            raw_classification=expected_classification,
            ticket_subject="Test Subject",
            ticket_content="Test Content"
        )
        
        # Verify the new classification was created
        mock_classification.assert_called_once()
        
        # Verify it was added to the database
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
        
        # Verify the audit log was created
        mock_audit_log.assert_called_once()
        
        # Verify the result
        assert result == mock_new_classification


@pytest.mark.asyncio
async def test_push_to_zoho(
    mock_db, mock_zoho_service, mock_cache_service
):
    """Test push_to_zoho method."""
    # Mock the database query
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    
    # Create a mock classification
    mock_classification = MagicMock()
    mock_classification.category = "Problem / Bug"
    mock_classification.sub_category = "Import"
    mock_classification.syndicator = "Kijiji"
    mock_classification.inventory_type = "New"
    
    # Set up the query to return the mock classification
    mock_query.first.return_value = mock_classification
    
    # Mock Zoho update_ticket to return success
    mock_zoho_service.update_ticket.return_value = (True, [])
    
    # Create the classifier service
    service = ClassifierService(mock_db, mock_zoho_service, mock_cache_service)
    
    # Call the method
    with patch("app.services.classifier.AuditLog") as mock_audit_log:
        result = await service.push_to_zoho(ticket_id="123456")
        
        # Verify Zoho update was called
        mock_zoho_service.update_ticket.assert_called_once()
        
        # Verify the classification was updated
        assert mock_classification.is_pushed
        assert mock_classification.pushed_at is not None
        
        # Verify the audit log was created
        mock_audit_log.assert_called_once()
        
        # Verify the result
        assert result["ticket_id"] == "123456"
        assert result["status"] == "success"