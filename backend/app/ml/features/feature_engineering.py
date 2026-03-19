"""
Feature engineering module for fraud detection ML model.
Extracts meaningful features from transaction data.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
import uuid


class FeatureEngineering:
    """Feature engineering for fraud detection model."""

    @staticmethod
    def extract_transaction_features(
        transaction_data: Dict,
        historical_transactions: List[Dict],
        user_profile: Dict
    ) -> Dict[str, float]:
        """
        Extract features from a single transaction and historical context.

        Features include:
        - Transaction amount features
        - Velocity features (frequency, amount over time)
        - Behavioral features (deviation from normal)
        - Time-based features
        - Merchant risk features
        """
        features = {}

        # === Amount Features ===
        amount = float(transaction_data.get("amount", 0))

        # Normalized amount relative to user's average
        user_avg = user_profile.get("avg_transaction_amount", 1)
        features["amount_normalized"] = amount / max(user_avg, 1)

        # Amount relative to user's max
        user_max = user_profile.get("max_transaction_amount", 1)
        features["amount_to_max_ratio"] = amount / max(user_max, 1)

        # Is this a round number (common for fraud)
        features["is_round_amount"] = 1.0 if amount == int(amount) else 0.0

        # === Velocity Features ===
        features["transaction_count_1h"] = len([
            t for t in historical_transactions
            if _is_within_hours(t.get("created_at"), 1)
        ])

        features["transaction_count_24h"] = len([
            t for t in historical_transactions
            if _is_within_hours(t.get("created_at"), 24)
        ])

        # Amount velocity (total in last hour)
        features["amount_1h"] = sum(
            float(t.get("amount", 0))
            for t in historical_transactions
            if _is_within_hours(t.get("created_at"), 1)
        )

        features["amount_24h"] = sum(
            float(t.get("amount", 0))
            for t in historical_transactions
            if _is_within_hours(t.get("created_at"), 24)
        )

        # Average amount in last hour vs typical
        if features["transaction_count_1h"] > 0:
            features["avg_amount_1h"] = features["amount_1h"] / features["transaction_count_1h"]
        else:
            features["avg_amount_1h"] = 0

        # === Behavioral Features ===
        # Deviation from user's typical amount
        features["amount_deviation_from_mean"] = abs(amount - user_avg) / max(user_avg, 1)

        # Deviation from typical transaction time
        features["unusual_hour"] = 1.0 if _is_unusual_hour(
            transaction_data.get("created_at")
        ) else 0.0

        # Weekend/holiday transaction
        features["weekend_transaction"] = 1.0 if _is_weekend(
            transaction_data.get("created_at")
        ) else 0.0

        # === Location Features ===
        # Location change detection
        last_location = historical_transactions[0].get("location") if historical_transactions else None
        current_location = transaction_data.get("location")

        if last_location and current_location and last_location != current_location:
            features["location_changed"] = 1.0
            # Time since last transaction
            time_diff = _get_time_diff_hours(
                transaction_data.get("created_at"),
                historical_transactions[0].get("created_at")
            )
            # Speed of location change (impossible travel)
            distance_km = _estimate_distance_km(last_location, current_location)
            features["impossible_travel_score"] = min(distance_km / max(time_diff, 0.1), 1.0)
        else:
            features["location_changed"] = 0.0
            features["impossible_travel_score"] = 0.0

        # === Merchant Features ===
        merchant = transaction_data.get("merchant", "").lower()
        features["merchant_risk_score"] = _get_merchant_risk_score(merchant)

        # High risk keywords
        high_risk_keywords = ["crypto", "gambling", "casino", "lottery", "adult", "forex"]
        features["high_risk_merchant"] = 1.0 if any(k in merchant for k in high_risk_keywords) else 0.0

        # === Account Features ===
        features["account_age_days"] = user_profile.get("account_age_days", 0)
        features["kyc_level"] = user_profile.get("kyc_level", 0)
        features["is_new_account"] = 1.0 if features["account_age_days"] < 30 else 0.0

        # === Transaction Pattern Features ===
        features["same_day_previous_transaction"] = 1.0 if _had_transaction_same_day(
            historical_transactions, transaction_data.get("created_at")
        ) else 0.0

        # Ratio of failed transactions
        total_txns = len(historical_transactions)
        if total_txns > 0:
            failed_txns = len([t for t in historical_transactions if t.get("status") == "failed"])
            features["failed_transaction_ratio"] = failed_txns / total_txns
        else:
            features["failed_transaction_ratio"] = 0.0

        return features

    @staticmethod
    def get_user_profile(db: AsyncSession, user_id: str) -> Dict:
        """Get user's historical transaction profile for feature engineering."""
        # This would query the database for user's transaction history
        # and compute aggregate statistics
        pass


def _is_within_hours(timestamp, hours: int) -> bool:
    """Check if timestamp is within N hours from now."""
    if not timestamp:
        return False
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp)
    return (datetime.utcnow() - timestamp).total_seconds() < hours * 3600


def _is_unusual_hour(timestamp) -> bool:
    """Check if transaction is at an unusual hour (2am-5am)."""
    if not timestamp:
        return False
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp)
    hour = timestamp.hour
    return 2 <= hour <= 5


def _is_weekend(timestamp) -> bool:
    """Check if transaction is on weekend."""
    if not timestamp:
        return False
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp)
    return timestamp.weekday() >= 5


def _get_time_diff_hours(ts1, ts2) -> float:
    """Get time difference in hours between two timestamps."""
    if not ts1 or not ts2:
        return 24.0  # Default to 24 hours
    if isinstance(ts1, str):
        ts1 = datetime.fromisoformat(ts1)
    if isinstance(ts2, str):
        ts2 = datetime.fromisoformat(ts2)
    diff = abs((ts1 - ts2).total_seconds())
    return max(diff / 3600, 0.1)


def _estimate_distance_km(location1: str, location2: str) -> float:
    """
    Estimate distance between two locations in km.
    In production, this would use a geocoding API.
    For now, returns a mock value based on string similarity.
    """
    # This is a simplified mock - in production, use:
    # - Haversine formula with lat/lon coordinates
    # - Or a geocoding API (Google Maps, Mapbox)
    if not location1 or not location2:
        return 0.0
    if location1 == location2:
        return 0.0
    # Mock: different country codes indicate ~5000km
    if location1[:2] != location2[:2]:
        return 5000.0
    # Same country, different city: ~100km
    return 100.0


def _get_merchant_risk_score(merchant: str) -> float:
    """Get risk score for merchant category."""
    if not merchant:
        return 0.0

    merchant_lower = merchant.lower()

    # High risk categories
    if any(k in merchant_lower for k in ["crypto", "bitcoin", "casino", "gambling", "lottery"]):
        return 0.9
    if any(k in merchant_lower for k in ["adult", "dating", "escort"]):
        return 0.8
    if any(k in merchant_lower for k in ["forex", "trading", "investment"]):
        return 0.6
    if any(k in merchant_lower for k in ["money transfer", "remittance", "wire"]):
        return 0.5

    # Low risk categories
    if any(k in merchant_lower for k in ["grocery", "supermarket", "utilities", "salary"]):
        return 0.1

    return 0.3  # Default medium risk


def _had_transaction_same_day(transactions: List[Dict], current_timestamp) -> bool:
    """Check if there was a transaction earlier the same day."""
    if not current_timestamp or not transactions:
        return False
    if isinstance(current_timestamp, str):
        current_timestamp = datetime.fromisoformat(current_timestamp)

    current_date = current_timestamp.date()
    for t in transactions:
        t_created = t.get("created_at")
        if isinstance(t_created, str):
            t_created = datetime.fromisoformat(t_created)
        if t_created and t_created.date() == current_date:
            return True
    return False
