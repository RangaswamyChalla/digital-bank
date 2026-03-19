"""Tests for account service."""
import pytest
from decimal import Decimal

from app.services.account import AccountService
from app.schemas.account import AccountCreate


class TestAccountCreation:
    """Test account creation."""

    @pytest.mark.asyncio
    async def test_create_account_success(self, db_session, authenticated_user):
        """Creating a new account should succeed."""
        account_data = AccountCreate(
            account_type="checking",
            currency="USD"
        )

        account = await AccountService.create_account(
            db_session,
            authenticated_user["user"]["id"],
            account_data
        )

        assert account is not None
        assert account.account_type == "checking"
        assert account.currency == "USD"
        assert account.balance == Decimal("0")
        assert account.status == "active"

    @pytest.mark.asyncio
    async def test_create_multiple_accounts(self, db_session, authenticated_user):
        """User should be able to create multiple accounts."""
        account_data = AccountCreate(account_type="savings", currency="USD")
        account1 = await AccountService.create_account(db_session, authenticated_user["user"]["id"], account_data)

        account_data.account_type = "checking"
        account2 = await AccountService.create_account(db_session, authenticated_user["user"]["id"], account_data)

        assert account1.id != account2.id
        assert account1.account_type == "savings"
        assert account2.account_type == "checking"

    @pytest.mark.asyncio
    async def test_create_account_kyc_required(self, db_session):
        """Account creation should require KYC level 1."""
        from app.services.auth import AuthService
        from app.schemas.auth import RegisterRequest

        # Create user without KYC
        register_request = RegisterRequest(
            email="lowkyc@example.com",
            password="Password123!",
            full_name="Low KYC User",
            phone="+1234567890"
        )
        user = await AuthService.register(db_session, register_request)

        account_data = AccountCreate(account_type="savings", currency="USD")

        from app.middleware.error_handling import ValidationException
        with pytest.raises(ValidationException) as exc_info:
            await AccountService.create_account(db_session, user.id, account_data)

        assert "kyc" in exc_info.value.detail.lower() or "kyc" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_create_account_kyc_approved(self, db_session, authenticated_user):
        """User with KYC level 1 should be able to create account."""
        from app.models.user import User
        from sqlalchemy import select

        # Update user KYC level
        result = await db_session.execute(select(User).where(User.id == authenticated_user["user"]["id"]))
        user = result.scalar_one_or_none()
        user.kyc_level = 1
        user.kyc_status = "approved"
        await db_session.commit()

        account_data = AccountCreate(account_type="savings", currency="USD")
        account = await AccountService.create_account(db_session, authenticated_user["user"]["id"], account_data)

        assert account is not None
        assert account.status == "active"


class TestAccountRetrieval:
    """Test account retrieval operations."""

    @pytest.mark.asyncio
    async def test_get_user_accounts(self, db_session, authenticated_user):
        """Should retrieve all accounts for a user."""
        accounts = await AccountService.get_user_accounts(
            db_session,
            authenticated_user["user"]["id"]
        )

        assert isinstance(accounts, list)
        assert len(accounts) >= 1

    @pytest.mark.asyncio
    async def test_get_account_balance(self, db_session, user_account):
        """Should retrieve account balance."""
        balance = await AccountService.get_account_balance(
            db_session,
            user_account["id"]
        )

        assert balance is not None
        assert isinstance(balance, Decimal)

    @pytest.mark.asyncio
    async def test_get_nonexistent_account(self, db_session):
        """Getting nonexistent account should return None."""
        from uuid import uuid4

        accounts = await AccountService.get_user_accounts(
            db_session,
            uuid4()
        )

        assert accounts == []


class TestAccountValidation:
    """Test account validation rules."""

    def test_account_create_valid_savings(self):
        """Valid savings account should be created."""
        account_data = AccountCreate(account_type="savings", currency="USD")
        assert account_data.account_type == "savings"

    def test_account_create_valid_checking(self):
        """Valid checking account should be created."""
        account_data = AccountCreate(account_type="checking", currency="EUR")
        assert account_data.account_type == "checking"

    def test_account_create_valid_fixed_deposit(self):
        """Valid fixed deposit account should be created."""
        account_data = AccountCreate(account_type="fixed_deposit", currency="USD")
        assert account_data.account_type == "fixed_deposit"

    def test_account_create_invalid_type(self):
        """Invalid account type should be rejected."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AccountCreate(account_type="invalid_type", currency="USD")

    def test_account_create_invalid_currency(self):
        """Invalid currency code should be rejected."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AccountCreate(account_type="savings", currency="INVALID")
