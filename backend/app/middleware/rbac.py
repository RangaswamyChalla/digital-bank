"""
Role-Based Access Control (RBAC) Middleware and Utilities
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.admin_role import AdminRole, Permission
from app.routers.users import get_current_user


class PermissionChecker:
    """Check if user has required permissions"""
    
    def __init__(self, required_permission: str):
        self.required_permission = required_permission
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """Verify user has the required permission"""
        
        # Super admins have all permissions
        if current_user.role == "super_admin":
            return current_user
        
        # If not admin, deny access
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Check if user has admin role assigned
        if not current_user.admin_role_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No admin role assigned"
            )
        
        # Get admin role with permissions
        result = await db.execute(
            select(AdminRole).where(AdminRole.id == current_user.admin_role_id)
        )
        admin_role = result.scalar_one_or_none()
        
        if not admin_role or not admin_role.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role inactive"
            )
        
        # Check if role has the permission
        permission_names = [p.name for p in admin_role.permissions]
        
        if self.required_permission not in permission_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{self.required_permission}' required"
            )
        
        return current_user


# Predefined permission checkers
check_manage_users = PermissionChecker("manage_users")
check_manage_kyc = PermissionChecker("manage_kyc")
check_manage_fraud = PermissionChecker("manage_fraud")
check_view_analytics = PermissionChecker("view_analytics")
check_manage_admins = PermissionChecker("manage_admins")
check_audit_logs = PermissionChecker("audit_logs")


class AdminRoleDefaults:
    """Default admin roles and their permissions"""
    
    @staticmethod
    def get_super_admin_permissions():
        """Super Admin - Full access"""
        return [
            "manage_users", "manage_kyc", "manage_fraud",
            "manage_accounts", "manage_transactions", "view_analytics",
            "manage_admins", "audit_logs", "system_settings"
        ]
    
    @staticmethod
    def get_admin_permissions():
        """Admin - Most access except admins management"""
        return [
            "manage_users", "manage_kyc", "manage_fraud",
            "manage_accounts", "manage_transactions", "view_analytics",
            "audit_logs"
        ]
    
    @staticmethod
    def get_auditor_permissions():
        """Auditor - Read-only access"""
        return [
            "view_users", "view_kyc", "view_fraud",
            "view_accounts", "view_transactions", "view_analytics",
            "audit_logs"
        ]


async def get_user_permissions(
    user_id: str,
    db: AsyncSession
) -> list:
    """Get all permissions for a user"""
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return []
    
    # Super admin has all permissions
    if user.role == "super_admin":
        return AdminRoleDefaults.get_super_admin_permissions()
    
    # If no admin role, no permissions
    if not user.admin_role_id:
        return []
    
    # Get role permissions
    role_result = await db.execute(
        select(AdminRole).where(AdminRole.id == user.admin_role_id)
    )
    admin_role = role_result.scalar_one_or_none()
    
    if not admin_role:
        return []
    
    return [p.name for p in admin_role.permissions]


async def initialize_default_roles(db: AsyncSession):
    """Initialize default admin roles and permissions"""
    
    # Create permissions
    permissions_data = {
        "manage_users": ("Manage users", "users"),
        "view_users": ("View users", "users"),
        "manage_kyc": ("Manage KYC", "kyc"),
        "view_kyc": ("View KYC", "kyc"),
        "manage_fraud": ("Manage fraud alerts", "fraud"),
        "view_fraud": ("View fraud alerts", "fraud"),
        "manage_accounts": ("Manage accounts", "accounts"),
        "view_accounts": ("View accounts", "accounts"),
        "manage_transactions": ("Manage transactions", "transactions"),
        "view_transactions": ("View transactions", "transactions"),
        "view_analytics": ("View analytics", "analytics"),
        "manage_admins": ("Manage admin roles", "system"),
        "audit_logs": ("Access audit logs", "system"),
        "system_settings": ("System settings", "system"),
    }
    
    created_permissions = {}
    
    for perm_name, (description, category) in permissions_data.items():
        result = await db.execute(
            select(Permission).where(Permission.name == perm_name)
        )
        perm = result.scalar_one_or_none()
        
        if not perm:
            perm = Permission(
                name=perm_name,
                description=description,
                category=category
            )
            db.add(perm)
        
        created_permissions[perm_name] = perm
    
    await db.flush()
    
    # Create roles
    roles_data = {
        "Super Admin": AdminRoleDefaults.get_super_admin_permissions(),
        "Admin": AdminRoleDefaults.get_admin_permissions(),
        "Auditor": AdminRoleDefaults.get_auditor_permissions(),
    }
    
    for role_name, perm_names in roles_data.items():
        result = await db.execute(
            select(AdminRole).where(AdminRole.name == role_name)
        )
        role = result.scalar_one_or_none()
        
        if not role:
            role = AdminRole(
                name=role_name,
                description=f"{role_name} role",
                permissions=[created_permissions[name] for name in perm_names if name in created_permissions]
            )
            db.add(role)
    
    await db.commit()
