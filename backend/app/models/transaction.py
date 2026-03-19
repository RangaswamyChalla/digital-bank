import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    from_account_id = Column(String(36), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    to_account_id = Column(String(36), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    from_account_number = Column(String(10), nullable=False, index=True)
    to_account_number = Column(String(10), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD")
    transaction_type = Column(String(20), nullable=False)  # credit, debit, transfer
    transfer_type = Column(String(20), nullable=False)  # internal, external
    reference = Column(String(255), nullable=True)
    status = Column(String(20), default="pending", index=True)  # pending, completed, failed
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)  # Location of transaction
    merchant = Column(String(255), nullable=True)  # Merchant name
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    failure_reason = Column(Text, nullable=True)

    # Composite indexes for common queries
    __table_args__ = (
        Index('ix_transactions_from_account_created', 'from_account_id', 'created_at'),
        Index('ix_transactions_to_account_created', 'to_account_id', 'created_at'),
        Index('ix_transactions_status_created', 'status', 'created_at'),
    )

    # Relationships
    from_account = relationship("Account", foreign_keys=[from_account_id], back_populates="sent_transactions")
    to_account = relationship("Account", foreign_keys=[to_account_id], back_populates="received_transactions")
    fraud_alert = relationship("FraudAlert", back_populates="transaction", uselist=False)
