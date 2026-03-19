"""Tests for authentication service."""
import pytest
from datetime import datetime, timedelta

from app.services.auth import AuthService
from app.schemas.auth import RegisterRequest, LoginRequest
from app.models.user import User


class TestPasswordHashing:
    """Test password hashing functionality."""

    def test_password_hash_is_different_from_plain(self):
        """Password hash should be different from plain password."""
        password = "MySecretPassword123!"
        hashed = AuthService.get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_same_password_hashes_differently(self):
        """Same password should produce different hashes (due to salt)."""
        password = "MySecretPassword123!"
        hash1 = AuthService.get_password_hash(password)
        hash2 = AuthService.get_password_hash(password)
        assert hash1 != hash2

    def test_verify_correct_password(self):
        """Verify should return True for correct password."""
        password = "MySecretPassword123!"
        hashed = AuthService.get_password_hash(password)
        assert AuthService.verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        """Verify should return False for incorrect password."""
        password = "MySecretPassword123!"
        hashed = AuthService.get_password_hash(password)
        assert AuthService.verify_password("WrongPassword", hashed) is False


class TestJWTTokens:
    """Test JWT token creation and decoding."""

    def test_create_access_token(self):
        """Access token should be created successfully."""
        data = {"user_id": "test-user-123", "email": "test@example.com", "role": "customer"}
        token = AuthService.create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_access_token(self):
        """Valid access token should decode correctly."""
        data = {"user_id": "test-user-123", "email": "test@example.com", "role": "customer"}
        token = AuthService.create_access_token(data)
        payload = AuthService.decode_token(token)

        assert payload["user_id"] == "test-user-123"
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "customer"
        assert payload["type"] == "access"

    def test_decode_refresh_token_has_correct_type(self):
        """Refresh token should have type='refresh'."""
        data = {"user_id": "test-user-123", "email": "test@example.com", "role": "customer"}
        token = AuthService.create_refresh_token(data)
        payload = AuthService.decode_token(token)

        assert payload["type"] == "refresh"

    def test_decode_invalid_token_raises_exception(self):
        """Invalid token should raise HTTPException."""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            AuthService.decode_token("invalid.token.here")
        assert exc_info.value.status_code == 401

    def test_access_token_contains_expiry(self):
        """Access token should have expiry time."""
        data = {"user_id": "test-user-123", "email": "test@example.com", "role": "customer"}
        token = AuthService.create_access_token(data)
        payload = AuthService.decode_token(token)

        assert "exp" in payload
        exp = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        assert exp > now


class TestUserRegistration:
    """Test user registration."""

    @pytest.mark.asyncio
    async def test_register_new_user(self, db_session):
        """New user should be registered successfully."""
        request = RegisterRequest(
            email="newuser@example.com",
            password="Password123!",
            full_name="New User",
            phone="+1234567890"
        )

        user = await AuthService.register(db_session, request)

        assert user.email == "newuser@example.com"
        assert user.full_name == "New User"
        assert user.role == "customer"
        assert user.kyc_level == 0
        assert user.kyc_status == "pending"

    @pytest.mark.asyncio
    async def test_register_duplicate_email_fails(self, db_session):
        """Registering with existing email should fail."""
        from fastapi import HTTPException

        request = RegisterRequest(
            email="duplicate@example.com",
            password="Password123!",
            full_name="First User",
            phone="+1234567890"
        )
        await AuthService.register(db_session, request)

        with pytest.raises(HTTPException) as exc_info:
            await AuthService.register(db_session, request)

        assert exc_info.value.status_code == 400
        assert "already registered" in exc_info.value.detail


class TestUserLogin:
    """Test user login."""

    @pytest.mark.asyncio
    async def test_login_valid_credentials(self, db_session):
        """Login with valid credentials should succeed."""
        register_request = RegisterRequest(
            email="loginuser@example.com",
            password="LoginPass123!",
            full_name="Login User",
            phone="+1234567890"
        )
        await AuthService.register(db_session, register_request)

        login_request = LoginRequest(
            email="loginuser@example.com",
            password="LoginPass123!"
        )
        tokens = await AuthService.login(db_session, login_request)

        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, db_session):
        """Login with wrong password should fail."""
        from fastapi import HTTPException

        register_request = RegisterRequest(
            email="wrongpass@example.com",
            password="CorrectPass123!",
            full_name="Wrong Pass User",
            phone="+1234567890"
        )
        await AuthService.register(db_session, register_request)

        login_request = LoginRequest(
            email="wrongpass@example.com",
            password="WrongPassword!"
        )

        with pytest.raises(HTTPException) as exc_info:
            await AuthService.login(db_session, login_request)

        assert exc_info.value.status_code == 401
        assert "Invalid email or password" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, db_session):
        """Login with nonexistent email should fail."""
        from fastapi import HTTPException

        login_request = LoginRequest(
            email="nonexistent@example.com",
            password="SomePassword123!"
        )

        with pytest.raises(HTTPException) as exc_info:
            await AuthService.login(db_session, login_request)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_login_increments_failed_attempts(self, db_session):
        """Failed login should increment failed_login_attempts."""
        from fastapi import HTTPException

        register_request = RegisterRequest(
            email="failedattempts@example.com",
            password="CorrectPass123!",
            full_name="Failed Attempts User",
            phone="+1234567890"
        )
        user = await AuthService.register(db_session, register_request)

        login_request = LoginRequest(
            email="failedattempts@example.com",
            password="WrongPassword!"
        )

        for _ in range(4):
            with pytest.raises(HTTPException):
                await AuthService.login(db_session, login_request)

        assert user.failed_login_attempts >= 4

    @pytest.mark.asyncio
    async def test_login_account_lockout(self, db_session):
        """Account should lock after 5 failed attempts."""
        from fastapi import HTTPException

        register_request = RegisterRequest(
            email="lockout@example.com",
            password="CorrectPass123!",
            full_name="Lockout User",
            phone="+1234567890"
        )
        await AuthService.register(db_session, register_request)

        login_request = LoginRequest(
            email="lockout@example.com",
            password="WrongPassword!"
        )

        for _ in range(5):
            try:
                await AuthService.login(db_session, login_request)
            except HTTPException:
                pass

        login_request.password = "CorrectPass123!"
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.login(db_session, login_request)

        assert exc_info.value.status_code == 423
        assert "locked" in exc_info.value.detail.lower()
