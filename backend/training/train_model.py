"""
Training script for the fraud detection ML model.
Generates synthetic training data and trains an XGBoost classifier.

Usage:
    python -m training.train_model --epochs 10 --model-path app/ml/models/fraud_model.pkl
"""
import argparse
import asyncio
import pickle
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import random

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_synthetic_transaction(
    user_id: str,
    is_fraud: bool,
    timestamp: datetime = None
) -> Dict:
    """Generate a synthetic transaction for training."""
    if timestamp is None:
        timestamp = datetime.utcnow()

    base_amount = random.uniform(10, 5000)

    if is_fraud:
        # Fraudulent transactions have suspicious patterns
        amount = random.choice([
            base_amount,
            random.uniform(5000, 15000),  # High amount
            random.uniform(1, 100),  # Very low amount (testing)
        ])
        merchant = random.choice([
            "Crypto Exchange",
            "Online Casino",
            "Forex Trading",
            "Lottery Purchase",
            "Wire Transfer Service",
            "Unknown Merchant",
        ])
        location = random.choice([
            "Nigeria",
            "Russia",
            "China",
            "Unknown Location",
            "Romania",
            "Ukraine",
        ])
        is_round = random.random() > 0.7
        hour = random.choice([3, 4, 2, 1])  # Unusual hours
        same_day = random.random() > 0.5
        failed_ratio = random.uniform(0.3, 0.8)
    else:
        # Normal transactions
        amount = base_amount
        merchant = random.choice([
            "Amazon",
            "Walmart",
            "Netflix",
            "Spotify",
            "Grocery Store",
            "Gas Station",
            "Restaurant",
            "Salary Deposit",
            "Utility Bill",
        ])
        location = "United States"
        is_round = random.random() > 0.5
        hour = random.choice([9, 10, 11, 14, 15, 16, 18, 19, 20])
        same_day = random.random() > 0.7
        failed_ratio = random.uniform(0, 0.1)

    if is_round:
        amount = float(int(amount))

    # Create timestamp at specified hour
    timestamp = timestamp.replace(hour=hour, minute=0, second=0, microsecond=0)

    return {
        "user_id": user_id,
        "amount": amount,
        "merchant": merchant,
        "location": location,
        "created_at": timestamp,
        "is_round": 1.0 if is_round else 0.0,
        "same_day_previous": 1.0 if same_day else 0.0,
        "failed_ratio": failed_ratio,
        "is_fraud": 1.0 if is_fraud else 0.0,
    }


def generate_user_profile() -> Dict:
    """Generate a synthetic user profile."""
    account_age_days = random.randint(30, 3650)  # 1 month to 10 years
    kyc_level = random.choice([0, 1, 1, 1, 2])  # Weighted towards level 1

    return {
        "account_age_days": account_age_days,
        "kyc_level": kyc_level,
        "avg_transaction_amount": random.uniform(50, 500),
        "max_transaction_amount": random.uniform(500, 5000),
    }


def extract_features(transaction: Dict, user_profile: Dict, history: List[Dict]) -> Dict:
    """Extract features from a transaction (simplified for training)."""
    features = {}

    # Amount features
    amount = transaction["amount"]
    avg = user_profile["avg_transaction_amount"]
    max_amt = user_profile["max_transaction_amount"]

    features["amount_normalized"] = amount / max(avg, 1)
    features["amount_to_max_ratio"] = amount / max(max_amt, 1)
    features["is_round_amount"] = transaction["is_round"]

    # Velocity features
    features["transaction_count_1h"] = random.randint(0, 10)
    features["transaction_count_24h"] = random.randint(1, 20)
    features["amount_1h"] = random.uniform(0, 2000)
    features["amount_24h"] = random.uniform(100, 10000)
    features["avg_amount_1h"] = features["amount_1h"] / max(features["transaction_count_1h"], 1)

    # Behavioral features
    features["amount_deviation_from_mean"] = abs(amount - avg) / max(avg, 1)
    features["unusual_hour"] = 1.0 if transaction["created_at"].hour in [2, 3, 4, 5] else 0.0
    features["weekend_transaction"] = 1.0 if transaction["created_at"].weekday() >= 5 else 0.0

    # Location features
    features["location_changed"] = 1.0 if random.random() > 0.8 else 0.0
    features["impossible_travel_score"] = random.uniform(0, 0.3) if features["location_changed"] else 0.0

    # Merchant features
    merchant = transaction["merchant"].lower()
    high_risk = any(k in merchant for k in ["crypto", "casino", "gambling", "lottery", "adult", "forex"])
    features["merchant_risk_score"] = 0.9 if high_risk else 0.2
    features["high_risk_merchant"] = 1.0 if high_risk else 0.0

    # Account features
    features["account_age_days"] = user_profile["account_age_days"]
    features["kyc_level"] = user_profile["kyc_level"]
    features["is_new_account"] = 1.0 if user_profile["account_age_days"] < 30 else 0.0

    # Transaction pattern features
    features["same_day_previous_transaction"] = transaction["same_day_previous"]
    features["failed_transaction_ratio"] = transaction["failed_ratio"]

    return features


def generate_training_data(n_samples: int = 10000, fraud_ratio: float = 0.05) -> tuple:
    """
    Generate synthetic training data for fraud detection.

    Args:
        n_samples: Total number of transactions to generate
        fraud_ratio: Ratio of fraudulent transactions (default 5%)

    Returns:
        Tuple of (X, y) where X is feature matrix and y is labels
    """
    logger.info(f"Generating {n_samples} synthetic transactions...")

    n_fraud = int(n_samples * fraud_ratio)
    n_normal = n_samples - n_fraud

    transactions = []

    # Generate normal transactions
    for i in range(n_normal):
        user_id = f"user_{i % 1000}"  # 1000 unique users
        timestamp = datetime.utcnow() - timedelta(days=random.randint(0, 90))
        txn = generate_synthetic_transaction(user_id, is_fraud=False, timestamp=timestamp)
        transactions.append(txn)

    # Generate fraudulent transactions
    for i in range(n_fraud):
        user_id = f"fraud_user_{i % 100}"  # 100 unique fraud users
        timestamp = datetime.utcnow() - timedelta(days=random.randint(0, 90))
        txn = generate_synthetic_transaction(user_id, is_fraud=True, timestamp=timestamp)
        transactions.append(txn)

    # Shuffle
    random.shuffle(transactions)

    # Extract features
    logger.info("Extracting features...")
    X = []
    y = []

    for txn in transactions:
        user_profile = generate_user_profile()
        features = extract_features(txn, user_profile, [])
        feature_vector = [
            features["amount_normalized"],
            features["amount_to_max_ratio"],
            features["is_round_amount"],
            features["transaction_count_1h"],
            features["transaction_count_24h"],
            features["amount_1h"],
            features["amount_24h"],
            features["avg_amount_1h"],
            features["amount_deviation_from_mean"],
            features["unusual_hour"],
            features["weekend_transaction"],
            features["location_changed"],
            features["impossible_travel_score"],
            features["merchant_risk_score"],
            features["high_risk_merchant"],
            features["account_age_days"],
            features["kyc_level"],
            features["is_new_account"],
            features["same_day_previous_transaction"],
            features["failed_transaction_ratio"],
        ]
        X.append(feature_vector)
        y.append(txn["is_fraud"])

    X = np.array(X)
    y = np.array(y)

    logger.info(f"Generated {len(X)} samples with {sum(y)} fraud cases ({sum(y)/len(y)*100:.2f}%)")

    return X, y


def train_model(X_train, y_train, X_test, y_test, model_path: str):
    """Train XGBoost model and save to disk."""
    try:
        import xgboost as xgb
    except ImportError:
        logger.error("XGBoost not installed. Install with: pip install xgboost")
        return None

    logger.info("Training XGBoost model...")

    # Create model
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=sum(y_train == 0) / max(sum(y_train == 1), 1),  # Handle imbalanced data
        random_state=42,
        use_label_encoder=False,
        eval_metric="aucpr",
    )

    # Train
    model.fit(
        X_train,
        y_train,
        eval_set=[(X_test, y_test)],
        verbose=10,
    )

    # Evaluate
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    from sklearn.metrics import classification_report, roc_auc_score, precision_recall_curve

    logger.info("\nClassification Report:")
    logger.info(classification_report(y_test, y_pred))

    try:
        auc = roc_auc_score(y_test, y_pred_proba)
        logger.info(f"ROC AUC Score: {auc:.4f}")
    except:
        pass

    # Feature importance
    feature_names = [
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

    importances = model.feature_importances_
    logger.info("\nTop 10 Feature Importances:")
    for name, imp in sorted(zip(feature_names, importances), key=lambda x: -x[1])[:10]:
        logger.info(f"  {name}: {imp:.4f}")

    # Save model
    logger.info(f"Saving model to {model_path}...")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    logger.info("Model training complete!")
    return model


def main():
    parser = argparse.ArgumentParser(description="Train fraud detection model")
    parser.add_argument("--samples", type=int, default=10000, help="Number of samples to generate")
    parser.add_argument("--fraud-ratio", type=float, default=0.05, help="Fraud ratio")
    parser.add_argument("--model-path", type=str, default="app/ml/models/fraud_model.pkl", help="Model output path")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test set size")
    args = parser.parse_args()

    # Generate data
    X, y = generate_training_data(n_samples=args.samples, fraud_ratio=args.fraud_ratio)

    # Split
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=42, stratify=y
    )

    # Train
    model = train_model(X_train, y_train, X_test, y_test, args.model_path)

    if model is None:
        logger.error("Training failed. Make sure xgboost is installed.")


if __name__ == "__main__":
    main()
