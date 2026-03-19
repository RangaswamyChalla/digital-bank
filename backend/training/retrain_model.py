"""
ML Fraud Detection Retraining Script
Periodically retrains the model with new data.

Usage:
    python -m training.retrain_model --days 90 --output app/ml/models/fraud_model.pkl
"""
import argparse
import asyncio
import pickle
import logging
from datetime import datetime, timedelta
from typing import List, Dict

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


def fetch_historical_transactions(db_url: str, days: int = 90) -> tuple:
    """
    Fetch historical transactions from the database.

    Returns:
        Tuple of (X, y) where X is features and y is labels.
        Labels are derived from fraud_alerts table.
    """
    from app.database import AsyncSessionLocal
    from app.models.transaction import Transaction
    from app.models.fraud_alert import FraudAlert
    from sqlalchemy import select, and_

    # This would fetch real transaction data from the database
    # For now, return None to indicate we need real data
    logger.warning("Real data fetching not implemented - use synthetic data")
    return None, None


def train_with_synthetic_data(n_samples: int, output_path: str):
    """Train model with synthetic data."""
    import sys
    import os

    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from training.train_model import generate_training_data, train_model
    from sklearn.model_selection import train_test_split

    logger.info(f"Generating {n_samples} synthetic training samples...")
    X, y = generate_training_data(n_samples=n_samples, fraud_ratio=0.05)

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train
    model = train_model(X_train, y_train, X_test, y_test, output_path)

    return model


def main():
    parser = argparse.ArgumentParser(description="Retrain fraud detection model")
    parser.add_argument("--days", type=int, default=90, help="Historical data days to fetch")
    parser.add_argument("--output", type=str, default="app/ml/models/fraud_model.pkl", help="Model output path")
    parser.add_argument("--samples", type=int, default=50000, help="Number of synthetic samples")
    parser.add_argument("--use-real-data", action="store_true", help="Use real database data")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.use_real_data:
        # Fetch from real database
        logger.info(f"Fetching historical transactions from last {args.days} days...")
        X, y = fetch_historical_transactions(days=args.days)

        if X is None:
            logger.error("Failed to fetch real data. Falling back to synthetic.")
            train_with_synthetic_data(args.samples, args.output)
    else:
        # Use synthetic data
        train_with_synthetic_data(args.samples, args.output)

    logger.info("Retraining complete!")


if __name__ == "__main__":
    main()
