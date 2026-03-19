"""
AI Fraud Detection Service for Digital Bank
Implements ML-based fraud detection with XGBoost model and rule-based fallback.
"""
import uuid
import logging
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.transaction import Transaction
from app.models.user import User

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FraudAlertRequest(BaseModel):
    user_id: str
    transaction_id: Optional[str] = None
    transaction_amount: float
    transaction_type: str
    merchant: Optional[str] = None
    location: Optional[str] = None


class FraudAlertResponse(BaseModel):
    is_suspicious: bool
    risk_level: RiskLevel
    risk_score: float  # 0-100
    reasons: List[str]
    recommended_action: str
    model_used: str = "ml"  # Track whether ML or rule-based was used


class FraudDetectionService:
    """
    ML-powered fraud detection with XGBoost model.
    Falls back to rule-based system when model is unavailable.
    """

    # Rule-based thresholds (used as fallback)
    HIGH_AMOUNT_THRESHOLD = 5000
    UNUSUAL_FREQUENCY_THRESHOLD = 5
    HIGH_RISK_SCORE = 70
    MEDIUM_RISK_SCORE = 40

    # ML Model
    _ml_model = None

    @classmethod
    def _get_ml_model(cls):
        """Lazy load the ML model."""
        if cls._ml_model is None:
            try:
                from app.ml.models.fraud_model import get_fraud_model
                cls._ml_model = get_fraud_model()
                logger.info("ML fraud detection model loaded")
            except Exception as e:
                logger.warning(f"Failed to load ML model: {e}")
                cls._ml_model = None
        return cls._ml_model

    @staticmethod
    async def analyze_transaction(
        db: AsyncSession,
        request: FraudAlertRequest
    ) -> FraudAlertResponse:
        """
        Analyze transaction for fraud risk using ML model.
        Falls back to rule-based system if ML model unavailable.
        """
        ml_model = FraudDetectionService._get_ml_model()

        if ml_model is not None:
            return await FraudDetectionService._analyze_with_ml(db, request, ml_model)
        else:
            return await FraudDetectionService._analyze_with_rules(db, request)

    @staticmethod
    async def _analyze_with_ml(
        db: AsyncSession,
        request: FraudAlertRequest,
        ml_model
    ) -> FraudAlertResponse:
        """Analyze transaction using ML model with enhanced features."""
        reasons = []

        # Extract features
        features = await FraudDetectionService._extract_ml_features(db, request)
        if features is None:
            # Fallback to rules if feature extraction fails
            return await FraudDetectionService._analyze_with_rules(db, request)

        # Get ML prediction
        fraud_prob, ml_risk_score = ml_model.predict(features)

        # Get rule-based score for explainability
        rule_score = await FraudDetectionService._calculate_rule_score(db, request, reasons)

        # Combine ML and rule-based signals
        # Weight: 70% ML, 30% rules
        combined_score = (ml_risk_score * 0.7) + (rule_score * 0.3)

        # Generate explanations
        await FraudDetectionService._add_rule_explanations(db, request, features, reasons)

        # Add ML confidence note
        if fraud_prob > 0.8:
            reasons.append(f"ML model confidence: {fraud_prob:.2%} fraud probability")

        # Determine risk level
        if combined_score >= FraudDetectionService.HIGH_RISK_SCORE:
            risk_level = RiskLevel.HIGH
            recommended_action = "BLOCK_IMMEDIATE"
        elif combined_score >= FraudDetectionService.MEDIUM_RISK_SCORE:
            risk_level = RiskLevel.MEDIUM
            recommended_action = "VERIFY_USER"
        else:
            risk_level = RiskLevel.LOW
            recommended_action = "ALLOW"

        return FraudAlertResponse(
            is_suspicious=risk_level != RiskLevel.LOW,
            risk_level=risk_level,
            risk_score=round(combined_score, 1),
            reasons=reasons if reasons else ["No suspicious activity detected"],
            recommended_action=recommended_action,
            model_used="ml"
        )

    @staticmethod
    async def _analyze_with_rules(
        db: AsyncSession,
        request: FraudAlertRequest
    ) -> FraudAlertResponse:
        """Fallback rule-based analysis."""
        reasons = []
        risk_score = 0

        # Rule 1: Check transaction amount
        amount_risk = FraudDetectionService._check_amount(request.transaction_amount, reasons)
        risk_score += amount_risk

        # Rule 2: Check transaction frequency
        frequency_risk = await FraudDetectionService._check_frequency(
            db, request.user_id, reasons
        )
        risk_score += frequency_risk

        # Rule 3: Check location anomaly
        location_risk = await FraudDetectionService._check_location_anomaly(
            db, request.user_id, request.location, reasons
        )
        risk_score += location_risk

        # Rule 4: Check account velocity
        velocity_risk = await FraudDetectionService._check_account_velocity(
            db, request.user_id, reasons
        )
        risk_score += velocity_risk

        # Rule 5: Check for high-risk merchant
        merchant_risk = FraudDetectionService._check_merchant_risk(
            request.merchant, reasons
        )
        risk_score += merchant_risk

        # Normalize score to 0-100
        risk_score = min(100, max(0, risk_score))

        # Determine risk level
        if risk_score >= FraudDetectionService.HIGH_RISK_SCORE:
            risk_level = RiskLevel.HIGH
            recommended_action = "BLOCK_IMMEDIATE"
        elif risk_score >= FraudDetectionService.MEDIUM_RISK_SCORE:
            risk_level = RiskLevel.MEDIUM
            recommended_action = "VERIFY_USER"
        else:
            risk_level = RiskLevel.LOW
            recommended_action = "ALLOW"

        return FraudAlertResponse(
            is_suspicious=risk_level != RiskLevel.LOW,
            risk_level=risk_level,
            risk_score=risk_score,
            reasons=reasons if reasons else ["No suspicious activity detected"],
            recommended_action=recommended_action,
            model_used="rules"
        )

    @staticmethod
    async def _extract_ml_features(
        db: AsyncSession,
        request: FraudAlertRequest
    ) -> Optional[Dict[str, float]]:
        """Extract features for ML model from transaction and history."""
        from app.models.account import Account

        try:
            features = {}

            # Get user's account IDs
            result = await db.execute(
                select(Account.id).where(Account.user_id == uuid.UUID(request.user_id))
            )
            user_account_ids = [row[0] for row in result.all()]

            if not user_account_ids:
                return None

            # Get user info
            result = await db.execute(
                select(User).where(User.id == uuid.UUID(request.user_id))
            )
            user = result.scalar_one_or_none()
            if not user:
                return None

            # Basic features from request
            amount = float(request.transaction_amount)
            features["transaction_amount"] = amount

            # User profile features
            account_age_days = (datetime.utcnow() - user.created_at).days
            features["account_age_days"] = float(account_age_days)
            features["is_new_account"] = 1.0 if account_age_days < 30 else 0.0
            features["kyc_level"] = float(user.kyc_level)

            # Get transaction history for velocity features
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            one_day_ago = datetime.utcnow() - timedelta(days=1)

            # Recent transactions (1 hour)
            result = await db.execute(
                select(Transaction).where(
                    and_(
                        Transaction.from_account_id.in_(user_account_ids),
                        Transaction.created_at >= one_hour_ago
                    )
                )
            )
            recent_1h = result.scalars().all()

            # Recent transactions (24 hours)
            result = await db.execute(
                select(Transaction).where(
                    and_(
                        Transaction.from_account_id.in_(user_account_ids),
                        Transaction.created_at >= one_day_ago
                    )
                )
            )
            recent_24h = result.scalars().all()

            # Velocity features
            features["transaction_count_1h"] = float(len(recent_1h))
            features["transaction_count_24h"] = float(len(recent_24h))

            amount_1h = sum(float(t.amount) for t in recent_1h)
            amount_24h = sum(float(t.amount) for t in recent_24h)
            features["amount_1h"] = amount_1h
            features["amount_24h"] = amount_24h

            # Average amount features
            if recent_1h:
                features["avg_amount_1h"] = amount_1h / len(recent_1h)
            else:
                features["avg_amount_1h"] = 0.0

            # Amount features
            if recent_24h:
                avg_historical = amount_24h / len(recent_24h)
                max_historical = max(float(t.amount) for t in recent_24h)
            else:
                avg_historical = 100.0
                max_historical = 1000.0

            features["amount_normalized"] = amount / max(avg_historical, 1)
            features["amount_to_max_ratio"] = amount / max(max_historical, 1)
            features["amount_deviation_from_mean"] = abs(amount - avg_historical) / max(avg_historical, 1)
            features["is_round_amount"] = 1.0 if amount == int(amount) else 0.0

            # Time features
            current_hour = datetime.utcnow().hour
            features["unusual_hour"] = 1.0 if 2 <= current_hour <= 5 else 0.0
            features["weekend_transaction"] = 1.0 if datetime.utcnow().weekday() >= 5 else 0.0

            # Location features
            last_txn = recent_24h[0] if recent_24h else None
            if last_txn and last_txn.location and request.location:
                features["location_changed"] = 1.0 if last_txn.location != request.location else 0.0
                if features["location_changed"]:
                    time_diff_hours = (datetime.utcnow() - last_txn.created_at).total_seconds() / 3600
                    # Estimate distance (simplified)
                    if last_txn.location[:2] != request.location[:2]:
                        estimated_distance = 5000.0  # Different country
                    else:
                        estimated_distance = 100.0  # Same country
                    features["impossible_travel_score"] = min(estimated_distance / max(time_diff_hours, 0.1), 1.0)
            else:
                features["location_changed"] = 0.0
                features["impossible_travel_score"] = 0.0

            # Merchant features
            merchant = (request.merchant or "").lower()
            high_risk_keywords = ["crypto", "casino", "gambling", "lottery", "adult", "forex"]
            features["high_risk_merchant"] = 1.0 if any(k in merchant for k in high_risk_keywords) else 0.0
            features["merchant_risk_score"] = FraudDetectionService._get_merchant_risk_score(merchant)

            # Pattern features
            today = datetime.utcnow().date()
            same_day_txns = [t for t in recent_24h if t.created_at.date() == today]
            features["same_day_previous_transaction"] = 1.0 if same_day_txns else 0.0

            # Failed transaction ratio
            if recent_24h:
                failed_count = len([t for t in recent_24h if t.status == "failed"])
                features["failed_transaction_ratio"] = failed_count / len(recent_24h)
            else:
                features["failed_transaction_ratio"] = 0.0

            return features

        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return None

    @staticmethod
    async def _calculate_rule_score(
        db: AsyncSession,
        request: FraudAlertRequest,
        reasons: List[str]
    ) -> float:
        """Calculate rule-based risk score for comparison."""
        score = 0
        score += FraudDetectionService._check_amount(request.transaction_amount, reasons)
        score += await FraudDetectionService._check_frequency(db, request.user_id, reasons)
        score += await FraudDetectionService._check_location_anomaly(
            db, request.user_id, request.location, reasons
        )
        score += await FraudDetectionService._check_account_velocity(db, request.user_id, reasons)
        score += FraudDetectionService._check_merchant_risk(request.merchant, reasons)
        return min(score, 100)

    @staticmethod
    async def _add_rule_explanations(
        db: AsyncSession,
        request: FraudAlertRequest,
        features: Dict[str, float],
        reasons: List[str]
    ) -> None:
        """Add human-readable explanations based on rule triggers."""
        amount = float(request.transaction_amount)

        if amount > FraudDetectionService.HIGH_AMOUNT_THRESHOLD:
            reasons.append(f"High amount: ${amount:,.2f}")

        if features.get("transaction_count_1h", 0) > 5:
            reasons.append(f"High frequency: {int(features['transaction_count_1h'])} txns/hour")

        if features.get("location_changed") == 1.0:
            reasons.append("Location change detected")

        if features.get("high_risk_merchant") == 1.0:
            reasons.append(f"High-risk merchant: {request.merchant}")

        if features.get("is_new_account") == 1.0:
            reasons.append("Transaction from new account")

        if features.get("failed_transaction_ratio", 0) > 0.3:
            reasons.append(f"High failed txn ratio: {features['failed_transaction_ratio']:.0%}")

    @staticmethod
    def _check_amount(amount: float, reasons: List[str]) -> int:
        """Check if transaction amount is unusually high"""
        if amount > FraudDetectionService.HIGH_AMOUNT_THRESHOLD:
            reasons.append(
                f"High transaction amount: ${amount:,.2f} "
                f"(threshold: ${FraudDetectionService.HIGH_AMOUNT_THRESHOLD:,.2f})"
            )
            return 30
        elif amount > 1000:
            reasons.append(f"Large transaction amount: ${amount:,.2f}")
            return 15
        return 0

    @staticmethod
    async def _check_frequency(
        db: AsyncSession,
        user_id: str,
        reasons: List[str]
    ) -> int:
        """Check if user has unusual transaction frequency"""
        from app.models.account import Account
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        result = await db.execute(
            select(Account.id).where(Account.user_id == uuid.UUID(user_id))
        )
        user_account_ids = [row[0] for row in result.all()]

        if not user_account_ids:
            return 0

        result = await db.execute(
            select(Transaction).where(
                and_(
                    Transaction.from_account_id.in_(user_account_ids),
                    Transaction.created_at >= one_hour_ago
                )
            )
        )
        recent_transactions = result.scalars().all()
        transaction_count = len(recent_transactions)

        if transaction_count > FraudDetectionService.UNUSUAL_FREQUENCY_THRESHOLD:
            reasons.append(
                f"Unusual frequency: {transaction_count} transactions in the last hour"
            )
            return 25

        return 0

    @staticmethod
    async def _check_location_anomaly(
        db: AsyncSession,
        user_id: str,
        current_location: Optional[str],
        reasons: List[str]
    ) -> int:
        """Detect rapid location changes"""
        from app.models.account import Account
        if not current_location:
            return 0

        result = await db.execute(
            select(Account.id).where(Account.user_id == uuid.UUID(user_id))
        )
        user_account_ids = [row[0] for row in result.all()]

        if not user_account_ids:
            return 0

        result = await db.execute(
            select(Transaction).where(
                Transaction.from_account_id.in_(user_account_ids)
            ).order_by(Transaction.created_at.desc()).limit(1)
        )
        last_transaction = result.scalar_one_or_none()

        if last_transaction and last_transaction.location:
            if last_transaction.location != current_location:
                time_diff = datetime.utcnow() - last_transaction.created_at
                if time_diff.total_seconds() < 900:
                    reasons.append(
                        f"Location change: {last_transaction.location} → {current_location} "
                        f"in {int(time_diff.total_seconds())} seconds"
                    )
                    return 35

        return 0

    @staticmethod
    async def _check_account_velocity(
        db: AsyncSession,
        user_id: str,
        reasons: List[str]
    ) -> int:
        """Check total transaction amount in short time period"""
        from app.models.account import Account
        one_day_ago = datetime.utcnow() - timedelta(hours=24)

        result = await db.execute(
            select(Account.id).where(Account.user_id == uuid.UUID(user_id))
        )
        user_account_ids = [row[0] for row in result.all()]

        if not user_account_ids:
            return 0

        result = await db.execute(
            select(Transaction).where(
                and_(
                    Transaction.from_account_id.in_(user_account_ids),
                    Transaction.created_at >= one_day_ago
                )
            )
        )
        daily_transactions = result.scalars().all()

        total_amount = sum(t.amount for t in daily_transactions)
        daily_velocity_threshold = 20000

        if total_amount > daily_velocity_threshold:
            reasons.append(
                f"High daily spending velocity: ${total_amount:,.2f} "
                f"(threshold: ${daily_velocity_threshold:,.2f})"
            )
            return 20

        return 0

    @staticmethod
    def _check_merchant_risk(merchant: Optional[str], reasons: List[str]) -> int:
        """Check if merchant is in high-risk category"""
        if not merchant:
            return 0

        high_risk_keywords = [
            "casino", "lottery", "crypto", "forex",
            "adult", "gambling", "darkweb"
        ]

        merchant_lower = merchant.lower()

        for keyword in high_risk_keywords:
            if keyword in merchant_lower:
                reasons.append(f"High-risk merchant category: {merchant}")
                return 15

        return 0

    @staticmethod
    def _get_merchant_risk_score(merchant: str) -> float:
        """Get numerical merchant risk score (0-1)."""
        if not merchant:
            return 0.0

        merchant_lower = merchant.lower()

        if any(k in merchant_lower for k in ["crypto", "casino", "gambling", "lottery"]):
            return 0.9
        if any(k in merchant_lower for k in ["adult", "forex"]):
            return 0.8
        if any(k in merchant_lower for k in ["money transfer", "remittance"]):
            return 0.5
        if any(k in merchant_lower for k in ["grocery", "utility", "salary"]):
            return 0.1

        return 0.3

    @staticmethod
    async def get_user_risk_profile(
        db: AsyncSession,
        user_id: str
    ) -> Dict:
        """Get user's fraud risk profile"""
        from app.models.account import Account
        result = await db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()

        if not user:
            return {"user_id": user_id, "status": "not_found"}

        result = await db.execute(
            select(Account.id).where(Account.user_id == uuid.UUID(user_id))
        )
        user_account_ids = [row[0] for row in result.all()]

        transactions = []
        if user_account_ids:
            result = await db.execute(
                select(Transaction).where(Transaction.from_account_id.in_(user_account_ids))
            )
            transactions = result.scalars().all()

        total_transactions = len(transactions)
        total_amount = sum(t.amount for t in transactions) if transactions else 0
        avg_amount = total_amount / total_transactions if total_transactions > 0 else 0

        failed_transactions = [t for t in transactions if t.status == "failed"]
        failed_rate = len(failed_transactions) / total_transactions if total_transactions > 0 else 0

        return {
            "user_id": user_id,
            "email": user.email,
            "total_transactions": total_transactions,
            "total_amount": float(total_amount),
            "average_amount": float(avg_amount),
            "failed_transactions": len(failed_transactions),
            "failed_rate": round(failed_rate * 100, 2),
            "kyc_level": user.kyc_level,
            "kyc_status": user.kyc_status,
            "is_active": user.is_active,
            "days_active": (datetime.utcnow() - user.created_at).days
        }
