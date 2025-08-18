"""
SQLAlchemy models for the database.
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    """User model for authentication."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Classification(Base):
    """Stores ticket classification results."""
    __tablename__ = "classifications"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String, index=True, nullable=False)
    
    # Classified Fields
    contact = Column(String)
    dealer_name = Column(String, index=True)
    dealer_id = Column(String, index=True)
    rep = Column(String, index=True)
    category = Column(String, index=True)
    sub_category = Column(String, index=True)
    syndicator = Column(String, index=True)
    inventory_type = Column(String)
    
    # Status fields
    is_pushed = Column(Boolean, default=False)
    pushed_at = Column(DateTime(timezone=True), nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Raw classification data
    raw_classification = Column(JSON, nullable=True)
    
    # Ticket data
    ticket_subject = Column(String, nullable=True)
    ticket_content = Column(Text, nullable=True)
    ticket_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="classifications")
    audit_logs = relationship("AuditLog", back_populates="classification")
    
    def __repr__(self):
        return f"<Classification(ticket_id={self.ticket_id}, dealer_name={self.dealer_name})>"


class AuditLog(Base):
    """Audit logs for all actions."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False, index=True)
    entity_id = Column(String, nullable=False, index=True)
    details = Column(JSON, nullable=True)
    status = Column(String, nullable=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    classification_id = Column(Integer, ForeignKey("classifications.id"), nullable=True)
    
    # Relationships
    user = relationship("User")
    classification = relationship("Classification", back_populates="audit_logs")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<AuditLog(action={self.action}, entity_type={self.entity_type}, entity_id={self.entity_id})>"


class Dealer(Base):
    """Dealer information table."""
    __tablename__ = "dealers"
    
    id = Column(Integer, primary_key=True, index=True)
    dealer_id = Column(String, unique=True, index=True, nullable=False)
    dealer_name = Column(String, index=True, nullable=False)
    rep_name = Column(String, index=True)
    
    # Additional fields
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    province = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    website = Column(String, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Dealer(dealer_id={self.dealer_id}, dealer_name={self.dealer_name})>"


class Syndicator(Base):
    """Syndicator information table."""
    __tablename__ = "syndicators"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Syndicator(name={self.name})>"


class ZohoToken(Base):
    """Zoho token cache."""
    __tablename__ = "zoho_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    access_token = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ZohoToken(expires_at={self.expires_at})>"
