"""
Pydantic schemas for the API.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


# Base Schemas
class BaseSchema(BaseModel):
    class Config:
        orm_mode = True


# Classification Schemas
class ClassificationBase(BaseSchema):
    """Base classification fields."""
    contact: Optional[str] = Field(None, description="Contact person")
    dealer_name: Optional[str] = Field(None, description="Dealer name")
    dealer_id: Optional[str] = Field(None, description="Dealer ID")
    rep: Optional[str] = Field(None, description="Rep name")
    category: Optional[str] = Field(None, description="Ticket category")
    sub_category: Optional[str] = Field(None, description="Ticket sub-category")
    syndicator: Optional[str] = Field(None, description="Syndicator")
    inventory_type: Optional[str] = Field(None, description="Inventory type")


class ClassificationCreate(ClassificationBase):
    """Schema for creating a classification."""
    ticket_id: str = Field(..., description="Zoho Desk ticket ID")
    ticket_subject: Optional[str] = Field(None, description="Ticket subject")
    ticket_content: Optional[str] = Field(None, description="Ticket content")
    ticket_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional ticket metadata")
    raw_classification: Optional[Dict[str, Any]] = Field(None, description="Raw classification output")
    confidence_score: Optional[float] = Field(None, description="Classification confidence score")


class ClassificationUpdate(BaseSchema):
    """Schema for updating a classification."""
    contact: Optional[str] = None
    dealer_name: Optional[str] = None
    dealer_id: Optional[str] = None
    rep: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    syndicator: Optional[str] = None
    inventory_type: Optional[str] = None
    is_pushed: Optional[bool] = None
    pushed_at: Optional[datetime] = None
    confidence_score: Optional[float] = None
    raw_classification: Optional[Dict[str, Any]] = None


class ClassificationResponse(ClassificationBase):
    """Schema for classification response."""
    id: int
    ticket_id: str
    is_pushed: bool
    pushed_at: Optional[datetime] = None
    confidence_score: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ClassificationList(BaseSchema):
    """Schema for list of classifications."""
    items: List[ClassificationResponse]
    total: int
    page: int
    size: int
    pages: int


# Ticket Schemas
class TicketBase(BaseSchema):
    """Base ticket fields from Zoho."""
    id: str
    subject: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    subCategory: Optional[str] = None
    priority: Optional[str] = None
    departmentId: Optional[str] = None
    contactId: Optional[str] = None
    assigneeId: Optional[str] = None
    createdTime: Optional[datetime] = None
    modifiedTime: Optional[datetime] = None


class TicketDetail(TicketBase):
    """Detailed ticket with additional fields."""
    description: Optional[str] = None
    webUrl: Optional[str] = None
    accountId: Optional[str] = None
    assignee: Optional[Dict[str, Any]] = None
    department: Optional[Dict[str, Any]] = None
    contact: Optional[Dict[str, Any]] = None
    account: Optional[Dict[str, Any]] = None
    customFields: Optional[Dict[str, Any]] = None
    cf: Optional[Dict[str, Any]] = None


class TicketList(BaseSchema):
    """Schema for list of tickets."""
    items: List[TicketBase]
    total: int
    page: int
    size: int
    pages: int


class TicketThread(BaseSchema):
    """Schema for ticket thread."""
    id: str
    content: Optional[str] = None
    summary: Optional[str] = None
    fromEmailAddress: Optional[str] = None
    createdTime: Optional[datetime] = None
    author: Optional[Dict[str, Any]] = None


# Classification Job Schemas
class ClassificationRequest(BaseSchema):
    """Schema for classification request."""
    ticket_id: str = Field(..., description="Zoho Desk ticket ID")
    auto_push: Optional[bool] = Field(False, description="Automatically push classification to Zoho")


class BatchClassificationRequest(BaseSchema):
    """Schema for batch classification request."""
    ticket_ids: List[str] = Field(..., description="List of Zoho Desk ticket IDs")
    auto_push: Optional[bool] = Field(False, description="Automatically push classifications to Zoho")


class ClassificationResult(BaseSchema):
    """Schema for classification result."""
    ticket_id: str
    status: str = Field(..., description="Status of the operation (success, error)")
    classification: Optional[ClassificationBase] = None
    pushed: Optional[bool] = None
    errors: Optional[List[str]] = None
    updated: Optional[List[str]] = None


class BatchClassificationResponse(BaseSchema):
    """Schema for batch classification response."""
    ok: int = Field(..., description="Number of successful classifications")
    err: int = Field(..., description="Number of failed classifications")
    results: List[ClassificationResult]


# Zoho Update Schemas
class ZohoPushRequest(BaseSchema):
    """Schema for pushing a classification to Zoho."""
    ticket_id: str
    classification_id: Optional[int] = None
    dry_run: Optional[bool] = Field(False, description="Preview changes without applying them")


class ZohoPushResult(BaseSchema):
    """Schema for push result."""
    ticket_id: str
    status: str
    fields: Optional[List[str]] = None
    errors: Optional[List[str]] = None
    dry_run: bool
    changes: Optional[Dict[str, Any]] = None


# Service Metrics
class ServiceMetrics(BaseSchema):
    """Schema for service metrics."""
    uptime: float
    processed: int
    success_rate: float
    avg_processing_time: float
    active_workers: int
    queue_size: int
    last_minute: Dict[str, int]
    last_hour: Dict[str, int]
    last_day: Dict[str, int]
