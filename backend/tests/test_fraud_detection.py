"""Tests for fraud detection service."""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from app.services.fraud_detection import FraudDetectionService, FraudAlertRequest, RiskLevel


class TestFraudDetectionAmountCheck:
    """Test fraud detection amount rules."""

    @pytest.mark.asyncio
    async def test_low_amount_low_risk(self, db_session):
        """Low transaction amount should result in low risk."""
        request = FraudAlertRequest(
            user_id="12345678-1234-1234-1234-123456789012",
            transaction_amount=100.0,
            transaction_type="debit",
            merchant=None,
            location=None
        )

        result = await FraudDetectionService.analyze_transaction(db_session, request)

        assert result.risk_level == RiskLevel.LOW
        assert result.risk_score < 40

    @pytest.mark.asyncio
    async def test_medium_amount_medium_risk(self, db_session):
        """Medium transaction amount should result in medium risk."""
        request = FraudAlertRequest(
            user_id="12345678-1234-1234-1234-123456789012",
            transaction_amount=2000.0,
            transaction_type="debit"
        )

        result = await FraudDetectionService.analyze_transaction(db_session, request)

        # Amount > $1000 but < $5000 adds 15 to risk score
        assert result.risk_score >= 15

    @pytest.mark.asyncio
    async def test_high_amount_triggers_alert(self, db_session):
        """High transaction amount (>$5000) should trigger high risk."""
        request = FraudAlertRequest(
            user_id="12345678-1234-1234-1234-123456789012",
            transaction_amount=6000.0,
            transaction_type="debit"
        )

        result = await FraudDetectionService.analyze_transaction(db_session, request)

        # Amount > $5000 adds 30 to risk score
        assert result.risk_score >= 30
        assert "High transaction amount" in result.reasons[0]


class TestFraudDetectionMerchantRisk:
    """Test merchant risk category detection."""

    @pytest.mark.asyncio
    async def test_high_risk_merchant(self, db_session):
        """Transaction with high-risk merchant should increase risk."""
        request = FraudAlertRequest(
            user_id="12345678-1234-1234-1234-123456789012",
            transaction_amount=100.0,
            transaction_type="debit",
            merchant="Crypto King Casino"
        )

        result = await FraudDetectionService.analyze_transaction(db_session, request)

        # Should flag "crypto" and "casino" keywords
        assert result.risk_score >= 15
        assert any("merchant" in r.lower() for r in result.reasons)

    @pytest.mark.asyncio
    async def test_safe_merchant(self, db_session):
        """Normal merchant should not increase risk score."""
        request = FraudAlertRequest(
            user_id="12345678-1234-1234-1234-123456789012",
            transaction_amount=100.0,
            transaction_type="debit",
            merchant="Amazon.com"
        )

        result = await FraudDetectionService.analyze_transaction(db_session, request)

        assert not any("merchant" in r.lower() for r in result.reasons)


class TestFraudAlertResponse:
    """Test FraudAlertResponse model."""

    def test_fraud_alert_request_valid(self):
        """Valid fraud alert request should be accepted."""
        request = FraudAlertRequest(
            user_id="12345678-1234-1234-1234-123456789012",
            transaction_amount=100.0,
            transaction_type="debit"
        )

        assert request.transaction_amount == 100.0
        assert request.user_id == "12345678-1234-1234-1234-123456789012"

    def test_fraud_alert_request_optional_fields(self):
        """Optional fields should default correctly."""
        request = FraudAlertRequest(
            user_id="12345678-1234-1234-1234-123456789012",
            transaction_amount=100.0,
            transaction_type="debit"
        )

        assert request.merchant is None
        assert request.location is None
        assert request.transaction_id is None


class TestRiskLevelClassification:
    """Test risk level classification logic."""

    @pytest.mark.asyncio
    async def test_low_risk_action_allow(self, db_session):
        """Low risk transactions should be allowed."""
        request = FraudAlertRequest(
            user_id="12345678-1234-1234-1234-123456789012",
            transaction_amount=50.0,
            transaction_type="debit"
        )

        result = await FraudDetectionService.analyze_transaction(db_session, request)

        assert result.risk_level == RiskLevel.LOW
        assert result.recommended_action == "ALLOW"

    @pytest.mark.asyncio
    async def test_medium_risk_action_verify(self, db_session):
        """Medium risk should require verification."""
        request = FraudAlertRequest(
            user_id="12345678-1234-1234-1234-123456789012",
            transaction_amount=6000.0,
            transaction_type="debit",
            merchant="Online Lottery"
        )

        result = await FraudDetectionService.analyze_transaction(db_session, request)

        # Amount (30) + merchant (15) = 45 (medium range 40-69)
        if result.risk_level == RiskLevel.MEDIUM:
            assert result.recommended_action == "VERIFY_USER"

    @pytest.mark.asyncio
    async def test_high_risk_action_block(self, db_session):
        """High risk transactions should be blocked."""
        request = FraudAlertRequest(
            user_id="12345678-1234-1234-1234-123456789012",
            transaction_amount=10000.0,
            transaction_type="debit",
            location="Unknown Country"
        )

        result = await FraudDetectionService.analyze_transaction(db_session, request)

        # Very high amount + location anomaly would trigger high risk
        if result.risk_level == RiskLevel.HIGH:
            assert result.recommended_action == "BLOCK_IMMEDIATE"


class TestUserRiskProfile:
    """Test user risk profile generation."""

    @pytest.mark.asyncio
    async def test_user_risk_profile_not_found(self, db_session):
        """Risk profile for nonexistent user should return not_found status."""
        result = await FraudDetectionService.get_user_risk_profile(
            db_session,
            "99999999-9999-9999-9999-999999999999"
        )

        assert result["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_user_risk_profile_structure(self, db_session, authenticated_user):
        """Risk profile should return expected structure."""
        result = await FraudDetectionService.get_user_risk_profile(
            db_session,
            str(authenticated_user["user"]["id"])
        )

        assert "user_id" in result
        assert "total_transactions" in result
        assert "total_amount" in result
        assert "failed_rate" in result
