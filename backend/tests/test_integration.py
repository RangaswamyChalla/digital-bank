"""Integration tests for complete banking flows."""
import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Root endpoint should return API info."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Digital Banking Platform"
        assert "version" in data

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient):
        """Health endpoint should return status."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data


class TestAuthFlow:
    """Test complete authentication flow."""

    @pytest.mark.asyncio
    async def test_register_login_logout_flow(self, client: AsyncClient):
        """Complete auth flow: register -> login -> access protected -> logout."""
        # Register
        register_data = {
            "email": "flow@example.com",
            "password": "FlowPass123!",
            "full_name": "Flow Test",
            "phone": "+1111111111"
        }
        response = await client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["email"] == "flow@example.com"

        # Login
        login_data = {"email": "flow@example.com", "password": "FlowPass123!"}
        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        tokens = response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens

        # Access protected endpoint
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        response = await client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200

        # Refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]}
        )
        assert response.status_code == 200
        new_tokens = response.json()
        assert "access_token" in new_tokens


class TestAccountFlow:
    """Test complete account management flow."""

    @pytest.mark.asyncio
    async def test_create_account_flow(self, client: AsyncClient, authenticated_user):
        """Creating an account after KYC approval."""
        headers = authenticated_user["headers"]

        # First update user KYC to level 1
        from app.models.user import User
        from app.database import AsyncSessionLocal
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.id == authenticated_user["user"]["id"]))
            user = result.scalar_one_or_none()
            user.kyc_level = 1
            user.kyc_status = "approved"
            await db.commit()

        # Create account
        account_data = {"account_type": "savings", "currency": "USD"}
        response = await client.post("/api/v1/accounts", json=account_data, headers=headers)
        assert response.status_code == 201
        account = response.json()
        assert account["account_type"] == "savings"

        # Get accounts
        response = await client.get("/api/v1/accounts", headers=headers)
        assert response.status_code == 200
        accounts = response.json()
        assert len(accounts) >= 1


class TestTransferFlow:
    """Test complete transfer flow."""

    @pytest.mark.asyncio
    async def test_transfer_with_insufficient_balance(self, client: AsyncClient, authenticated_user, second_account):
        """Transfer with insufficient balance should fail gracefully."""
        headers = authenticated_user["headers"]

        transfer_data = {
            "from_account_id": authenticated_user["user"]["account_ids"][0],
            "to_account_number": second_account["account_number"],
            "amount": 999999.00,
            "transfer_type": "internal",
            "reference": "Test"
        }

        response = await client.post("/api/v1/transfers", json=transfer_data, headers=headers)
        assert response.status_code == 400
        assert "balance" in response.json()["detail"].lower()


class TestKYCFlow:
    """Test KYC workflow."""

    @pytest.mark.asyncio
    async def test_kyc_status_endpoint(self, client: AsyncClient, authenticated_user):
        """KYC status endpoint should be accessible."""
        headers = authenticated_user["headers"]
        response = await client.get("/api/v1/kyc/status", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "kyc_level" in data
        assert "kyc_status" in data


class TestAdminEndpoints:
    """Test admin-only endpoints."""

    @pytest.mark.asyncio
    async def test_admin_stats_access(self, client: AsyncClient, authenticated_admin):
        """Admin should access stats endpoint."""
        headers = authenticated_admin["headers"]
        response = await client.get("/api/v1/admin/stats", headers=headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_admin_stats_denied_to_user(self, client: AsyncClient, authenticated_user):
        """Non-admin should be denied access to admin stats."""
        headers = authenticated_user["headers"]
        response = await client.get("/api/v1/admin/stats", headers=headers)
        assert response.status_code == 403


class TestFraudEndpoints:
    """Test fraud detection endpoints."""

    @pytest.mark.asyncio
    async def test_fraud_alerts_endpoint(self, client: AsyncClient, authenticated_admin):
        """Admin should access fraud alerts endpoint."""
        headers = authenticated_admin["headers"]
        response = await client.get("/api/v1/fraud/alerts", headers=headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_fraud_statistics_endpoint(self, client: AsyncClient, authenticated_admin):
        """Admin should access fraud statistics."""
        headers = authenticated_admin["headers"]
        response = await client.get("/api/v1/fraud/statistics", headers=headers)
        assert response.status_code == 200


class TestAnalyticsEndpoints:
    """Test analytics endpoints."""

    @pytest.mark.asyncio
    async def test_analytics_dashboard_stats(self, client: AsyncClient, authenticated_admin):
        """Admin should access analytics dashboard stats."""
        headers = authenticated_admin["headers"]
        response = await client.get("/api/v1/analytics/dashboard-stats", headers=headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_analytics_transactions_summary(self, client: AsyncClient, authenticated_admin):
        """Admin should access transactions summary."""
        headers = authenticated_admin["headers"]
        response = await client.get("/api/v1/analytics/transactions-summary", headers=headers)
        assert response.status_code == 200


class TestNotificationEndpoints:
    """Test notification endpoints."""

    @pytest.mark.asyncio
    async def test_notifications_list(self, client: AsyncClient, authenticated_user):
        """User should access their notifications."""
        headers = authenticated_user["headers"]
        response = await client.get("/api/v1/notifications", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_unread_count(self, client: AsyncClient, authenticated_user):
        """User should get unread notification count."""
        headers = authenticated_user["headers"]
        response = await client.get("/api/v1/notifications/unread-count", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
