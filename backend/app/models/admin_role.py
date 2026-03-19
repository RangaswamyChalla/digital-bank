"""Admin Roles and Permissions Model"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

# Association table for admin roles and permissions
admin_permissions = Table(
    'admin_role_permissions',
    Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('admin_roles.id'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id'), primary_key=True)
)


class AdminRole(Base):
    __tablename__ = "admin_roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)  # Super Admin, Admin, Auditor
    description = Column(String(500), nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    permissions = relationship(
        "Permission",
        secondary=admin_permissions,
        back_populates="roles",
        cascade="all, delete"
    )
    users = relationship("User", back_populates="admin_role")
    
    def __repr__(self):
        return f"<AdminRole {self.name}>"


class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)  # view_users, manage_kyc, etc
    description = Column(String(500), nullable=True)
    category = Column(String(50), nullable=False)  # users, kyc, transactions, fraud, system
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    roles = relationship(
        "AdminRole",
        secondary=admin_permissions,
        back_populates="permissions"
    )
    
    def __repr__(self):
        return f"<Permission {self.name}>"


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String(200), nullable=False)  # "viewed_user", "blocked_account", etc
    entity_type = Column(String(50), nullable=False)  # "user", "transaction", "fraud_alert"
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    
    details = Column(String(1000), nullable=True)  # JSON string for additional data
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(300), nullable=True)
    
    status = Column(String(20), default="success")  # success, failure
    error_message = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="activity_logs")
    
    def __repr__(self):
        return f"<ActivityLog {self.action} - {self.entity_type}>"
