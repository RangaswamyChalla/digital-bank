"""
AI Fraud Detection Service for Digital Bank
Implements rule-based fraud detection with ML-ready architecture
"""
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.transaction import Transaction
from app.models.user import User


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


class FraudDetectionService:
    """Production-grade fraud detection with rule-based system"""
    
    # Configuration
    HIGH_AMOUNT_THRESHOLD = 5000  # Amount that triggers alert
    UNUSUAL_FREQUENCY_THRESHOLD = 5  # Transactions in 1 hour
    MULTIPLE_LOCATIONS_THRESHOLD = 2  # Different locations in 15 mins
    
    HIGH_RISK_SCORE = 70
    MEDIUM_RISK_SCORE = 40
    
    @staticmethod
    async def analyze_transaction(
        db: AsyncSession,
        request: FraudAlertRequest
    ) -> FraudAlertResponse:
        """
        Analyze transaction for fraud risk
        Returns risk assessment with recommended actions
        """
        reasons = []
        risk_score = 0
        
        # Rule 1: Check transaction amount
        amount_risk = FraudDetectionService._check_amount(
            request.transaction_amount, reasons
        )
        risk_score += amount_risk
        
        # Rule 2: Check transaction frequency
        user_id = request.user_id
        frequency_risk = await FraudDetectionService._check_frequency(
            db, user_id, reasons
        )
        risk_score += frequency_risk
        
        # Rule 3: Check location anomaly
        location_risk = await FraudDetectionService._check_location_anomaly(
            db, user_id, request.location, reasons
        )
        risk_score += location_risk
        
        # Rule 4: Check account velocity
        velocity_risk = await FraudDetectionService._check_account_velocity(
            db, user_id, reasons
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
            recommended_action=recommended_action
        )
    
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

        # First get user's account IDs, then query transactions
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

        # Get user's account IDs
        result = await db.execute(
            select(Account.id).where(Account.user_id == uuid.UUID(user_id))
        )
        user_account_ids = [row[0] for row in result.all()]

        if not user_account_ids:
            return 0

        # Get last transaction location
        result = await db.execute(
            select(Transaction).where(
                Transaction.from_account_id.in_(user_account_ids)
            ).order_by(Transaction.created_at.desc()).limit(1)
        )
        last_transaction = result.scalar_one_or_none()

        if last_transaction and last_transaction.location:
            if last_transaction.location != current_location:
                # Check time difference - if too close, high risk
                time_diff = datetime.utcnow() - last_transaction.created_at

                if time_diff.total_seconds() < 900:  # 15 minutes
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

        # Get user's account IDs first
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
        
        # High-risk merchant categories
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

        # Get user's account IDs first
        result = await db.execute(
            select(Account.id).where(Account.user_id == uuid.UUID(user_id))
        )
        user_account_ids = [row[0] for row in result.all()]

        # Get transaction history using account IDs
        transactions = []
        if user_account_ids:
            result = await db.execute(
                select(Transaction).where(Transaction.from_account_id.in_(user_account_ids))
            )
            transactions = result.scalars().all()

        # Calculate metrics
        total_transactions = len(transactions)
        total_amount = sum(t.amount for t in transactions) if transactions else 0
        avg_amount = total_amount / total_transactions if total_transactions > 0 else 0

        # Get failed transactions
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
