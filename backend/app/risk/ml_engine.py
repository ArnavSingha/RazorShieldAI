"""
RazorShield AI — Real Isolation Forest ML Anomaly Engine
Unsupervised anomaly detection scoring customer transaction feature vectors.
Requires scikit-learn IsolationForest backend; fails cleanly into DEGRADED_NO_ML if unavailable.
"""

import math
import random
from typing import Tuple

from backend.app.domain.models import CustomerProfile, MLRiskResult, TransactionEvent
from backend.app.domain.reason_codes import ReasonCode

try:
    from sklearn.ensemble import IsolationForest as SklearnIsolationForest

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class RealIsolationForestModel:
    """Reproducible, mathematical Isolation Forest model using scikit-learn."""

    def __init__(self, n_estimators: int = 50, max_samples: int = 100, seed: int = 42):
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.seed = seed
        self.sklearn_model = None
        self.is_fitted = False

        if SKLEARN_AVAILABLE:
            self.sklearn_model = SklearnIsolationForest(
                n_estimators=n_estimators, random_state=seed, contamination=0.05
            )

    def fit_synthetic_baseline(self) -> None:
        """Trains/fits model on 200 normal synthetic customer purchasing profiles."""
        if self.sklearn_model is None:
            self.is_fitted = False
            return

        rng = random.Random(self.seed)
        normal_dataset: list[list[float]] = []
        for _ in range(200):
            amount_ratio = max(0.1, rng.gauss(1.0, 0.3))
            log_amount = rng.gauss(7.5, 0.5)
            dev_mismatch = 0.0 if rng.random() > 0.05 else 1.0
            ip_mismatch = 0.0 if rng.random() > 0.08 else 1.0
            normal_dataset.append([amount_ratio, log_amount, dev_mismatch, ip_mismatch])

        self.sklearn_model.fit(normal_dataset)
        self.is_fitted = True

    def fit_features(self, feature_matrix: list[list[float]]) -> None:
        """Fits IsolationForest model on extracted training feature matrix."""
        if self.sklearn_model is not None and feature_matrix:
            self.sklearn_model.fit(feature_matrix)
            self.is_fitted = True

    def score_sample(self, features: list[float]) -> Tuple[float, float, bool]:
        """
        Returns (raw_anomaly_score, normalized_score_0_to_1, is_valid).
        Fails cleanly if scikit-learn is not installed or model is uninitialized.
        """
        if not SKLEARN_AVAILABLE or self.sklearn_model is None or not self.is_fitted:
            return 0.0, 0.0, False

        raw_decision = float(self.sklearn_model.decision_function([features])[0])
        normalized = min(1.0, max(0.0, 0.5 - raw_decision))
        return round(raw_decision, 4), round(normalized, 4), True


class MLEngine:
    """Production Isolation Forest Anomaly Detection Engine."""

    def __init__(self, model_version: str = "iforest-v1.2.0-real"):
        self.model_version = model_version
        self.model = RealIsolationForestModel(n_estimators=50, seed=42)
        self.model.fit_synthetic_baseline()

    def fit_baseline(self, events: list[TransactionEvent]) -> None:
        """Fits IsolationForest model on training event observations."""
        feature_matrix = []
        for e in events:
            prof = CustomerProfile(customer_id=e.customer_id)
            feats = self._extract_features(e, prof)
            feature_matrix.append(feats)
        self.model.fit_features(feature_matrix)

    def _extract_features(
        self, event: TransactionEvent, customer_profile: CustomerProfile
    ) -> list[float]:
        amount_ratio = event.amount / max(
            1.0, customer_profile.avg_transaction_amount_30d
        )
        log_amount = math.log1p(event.amount)
        device_mismatch = (
            1.0
            if (
                customer_profile.primary_device_id
                and event.device_id != customer_profile.primary_device_id
            )
            else 0.0
        )
        ip_mismatch = (
            1.0
            if (
                customer_profile.primary_ip
                and event.ip_address != customer_profile.primary_ip
            )
            else 0.0
        )
        return [amount_ratio, log_amount, device_mismatch, ip_mismatch]

    def predict_anomaly(
        self, event: TransactionEvent, customer_profile: CustomerProfile
    ) -> MLRiskResult:
        features = self._extract_features(event, customer_profile)
        raw_score, normalized_score, is_valid = self.model.score_sample(features)

        if not is_valid:
            raise RuntimeError(
                "IsolationForest model unavailable. Engine entering DEGRADED_NO_ML state."
            )

        return MLRiskResult(
            model_version=self.model_version,
            raw_anomaly_score=raw_score,
            normalized_score=normalized_score,
            confidence=0.92,
            reason_metadata={
                "sklearn_backend_active": True,
                "amount_ratio_to_baseline": round(features[0], 2),
                "device_mismatch": bool(features[2]),
                "ip_mismatch": bool(features[3]),
                "reason_code": ReasonCode.ISOLATION_FOREST_ANOMALY
                if normalized_score > 0.6
                else "NORMAL_ML_BASELINE",
                "note": "Raw anomaly score derived from IsolationForest decision function.",
            },
        )
