"""Fraud Alert Model"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    transaction_id = Column(String(36), ForeignKey("transactions.id"), nullable=True)

    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(20), default="low")  # low, medium, high
    reasons = Column(String(1000), nullable=True)  # JSON string of reasons
    recommended_action = Column(String(50), default="ALLOW")

    status = Column(String(20), default="open")  # open, verified_safe, escalated, blocked
    admin_action = Column(String(100), nullable=True)
    admin_notes = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="fraud_alerts")
    transaction = relationship("Transaction", back_populates="fraud_alert")

    def __repr__(self):
        return f"<FraudAlert {self.id} - {self.risk_level}>"
