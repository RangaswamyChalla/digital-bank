"""
ML Fraud Detection Model Service.
Wraps the trained model for inference.
"""
import pickle
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class FraudDetectionModel:
    """
    ML-based fraud detection service.

    Loads a pre-trained XGBoost model and provides inference.
    Falls back to rule-based scoring when model is unavailable.
    """

    def __init__(self, model_path: str = None):
        self.model = None
        self.model_path = model_path
        self._feature_names = [
            "amount_normalized",
            "amount_to_max_ratio",
            "is_round_amount",
            "transaction_count_1h",
            "transaction_count_24h",
            "amount_1h",
            "amount_24h",
            "avg_amount_1h",
            "amount_deviation_from_mean",
            "unusual_hour",
            "weekend_transaction",
            "location_changed",
            "impossible_travel_score",
            "merchant_risk_score",
            "high_risk_merchant",
            "account_age_days",
            "kyc_level",
            "is_new_account",
            "same_day_previous_transaction",
            "failed_transaction_ratio",
        ]
        self._load_model()

    def _load_model(self) -> None:
        """Load the trained model from disk."""
        if self.model_path is None:
            self.model_path = Path(__file__).parent / "fraud_model.pkl"

        try:
            if Path(self.model_path).exists():
                with open(self.model_path, "rb") as f:
                    self.model = pickle.load(f)
                logger.info(f"Loaded fraud detection model from {self.model_path}")
            else:
                logger.warning(
                    f"Model file not found at {self.model_path}. "
                    "Fraud detection will use rule-based fallback."
                )
                self.model = None
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None

    def predict(self, features: Dict[str, float]) -> Tuple[float, float]:
        """
        Predict fraud probability for given features.

        Args:
            features: Dictionary of feature values

        Returns:
            Tuple of (fraud_probability, risk_score)
            fraud_probability is between 0 and 1
            risk_score is between 0 and 100
        """
        if self.model is None:
            return self._rule_based_fallback(features)

        try:
            # Convert features dict to feature vector in correct order
            feature_vector = np.array([[features.get(name, 0.0) for name in self._feature_names]])

            # Get fraud probability
            fraud_prob = float(self.model.predict_proba(feature_vector)[0][1])

            # Convert to risk score (0-100)
            risk_score = fraud_prob * 100

            return fraud_prob, risk_score

        except Exception as e:
            logger.error(f"Model prediction failed: {e}")
            return self._rule_based_fallback(features)

    def _rule_based_fallback(self, features: Dict[str, float]) -> Tuple[float, float]:
        """
        Rule-based fallback when ML model is unavailable.

        This replicates the original rule-based fraud detection logic.
        """
        score = 0.0

        # Amount scoring (max 30 points)
        amount_norm = features.get("amount_normalized", 0)
        if amount_norm > 10:
            score += 30
        elif amount_norm > 5:
            score += 15

        # Frequency scoring (max 25 points)
        txn_count_1h = features.get("transaction_count_1h", 0)
        if txn_count_1h > 5:
            score += 25
        elif txn_count_1h > 3:
            score += 15

        # Location scoring (max 35 points)
        if features.get("location_changed", 0) == 1.0:
            score += 20
        if features.get("impossible_travel_score", 0) > 0.5:
            score += 15

        # Merchant scoring (max 15 points)
        if features.get("high_risk_merchant", 0) == 1.0:
            score += 15
        else:
            score += features.get("merchant_risk_score", 0) * 15

        # Account age scoring (max 10 points)
        if features.get("is_new_account", 0) == 1.0:
            score += 10

        # Cap at 100
        risk_score = min(score, 100.0)

        # Convert to probability (rough approximation)
        fraud_prob = risk_score / 100.0

        return fraud_prob, risk_score

    def predict_batch(self, features_list: list) -> list:
        """Predict fraud for multiple transactions."""
        return [self.predict(f) for f in features_list]

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from the model."""
        if self.model is None:
            return {}

        try:
            importances = self.model.feature_importances_
            return {
                name: float(imp)
                for name, imp in zip(self._feature_names, importances)
            }
        except Exception as e:
            logger.error(f"Failed to get feature importance: {e}")
            return {}


# Singleton instance
_fraud_model: Optional[FraudDetectionModel] = None


def get_fraud_model() -> FraudDetectionModel:
    """Get the singleton fraud detection model instance."""
    global _fraud_model
    if _fraud_model is None:
        _fraud_model = FraudDetectionModel()
    return _fraud_model
