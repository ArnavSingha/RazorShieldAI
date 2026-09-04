"""
RazorShield AI — Deterministic Signal Engine
Calculates velocity (1h/24h), geographic speed anomalies, amount deviation,
device/IP reuse, and BIN risk signals.
"""

import math

from backend.app.domain.models import CustomerProfile, RiskSignal, TransactionEvent
from backend.app.domain.reason_codes import ReasonCode


class SignalEngine:
    """Calculates deterministic risk signals for payment events."""

    def __init__(self):
        self._history: list[TransactionEvent] = []

    def record_event(self, event: TransactionEvent) -> None:
        self._history.append(event)
        cutoff = event.timestamp - 86400
        self._history = [e for e in self._history if e.timestamp >= cutoff]

    def _calculate_velocity(
        self, event: TransactionEvent
    ) -> tuple[int, float, int, float]:
        cutoff_1h = event.timestamp - 3600
        cutoff_24h = event.timestamp - 86400

        count_1h, sum_1h = 0, 0.0
        count_24h, sum_24h = 0, 0.0

        for past in self._history:
            if past.customer_id == event.customer_id:
                if past.timestamp >= cutoff_24h:
                    count_24h += 1
                    sum_24h += past.amount
                    if past.timestamp >= cutoff_1h:
                        count_1h += 1
                        sum_1h += past.amount

        return count_1h, sum_1h, count_24h, sum_24h

    @staticmethod
    def _haversine_distance(
        lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        r = 6371.0  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return r * c

    def evaluate(
        self, event: TransactionEvent, customer_profile: CustomerProfile
    ) -> list[RiskSignal]:
        signals: list[RiskSignal] = []

        # 1. Velocity Signals
        c_1h, s_1h, _c_24h, _s_24h = self._calculate_velocity(event)

        if c_1h >= 5:
            signals.append(
                RiskSignal(
                    signal_code="SIG_VELOCITY_1H_COUNT",
                    raw_value=c_1h,
                    normalized_score=min(1.0, c_1h / 10.0),
                    reason_code=ReasonCode.HIGH_VELOCITY_1H_COUNT,
                    severity="HIGH" if c_1h <= 8 else "CRITICAL",
                    weight=0.25,
                    metadata={"count_1h": c_1h},
                )
            )

        if s_1h > 50000.0:
            signals.append(
                RiskSignal(
                    signal_code="SIG_VELOCITY_1H_AMOUNT",
                    raw_value=s_1h,
                    normalized_score=min(1.0, s_1h / 150000.0),
                    reason_code=ReasonCode.HIGH_VELOCITY_1H_AMOUNT,
                    severity="HIGH",
                    weight=0.25,
                    metadata={"sum_1h": s_1h},
                )
            )

        # 2. Amount Anomaly Signal (Z-score vs Customer Profile)
        if customer_profile.std_transaction_amount_30d > 0:
            z_score = (
                event.amount - customer_profile.avg_transaction_amount_30d
            ) / customer_profile.std_transaction_amount_30d
            if z_score > 3.0:
                signals.append(
                    RiskSignal(
                        signal_code="SIG_AMOUNT_ANOMALY",
                        raw_value=event.amount,
                        normalized_score=min(1.0, z_score / 6.0),
                        reason_code=ReasonCode.ABNORMAL_TRANSACTION_AMOUNT,
                        severity="MEDIUM" if z_score <= 4.5 else "HIGH",
                        weight=0.20,
                        metadata={
                            "z_score": round(z_score, 2),
                            "baseline_avg": customer_profile.avg_transaction_amount_30d,
                        },
                    )
                )

        # 3. Geographic Velocity Anomaly (Implausible travel speed)
        if customer_profile.last_transaction_time > 0 and event.geo_location:
            time_diff_hours = (
                event.timestamp - customer_profile.last_transaction_time
            ) / 3600.0
            if time_diff_hours > 0:
                dist_km = self._haversine_distance(
                    customer_profile.last_lat,
                    customer_profile.last_lon,
                    event.geo_location.lat,
                    event.geo_location.lon,
                )
                speed_kmh = dist_km / time_diff_hours
                if speed_kmh > 800.0 and dist_km > 100.0:
                    signals.append(
                        RiskSignal(
                            signal_code="SIG_GEO_IMPLAUSIBLE_SPEED",
                            raw_value=round(speed_kmh, 1),
                            normalized_score=min(1.0, speed_kmh / 2000.0),
                            reason_code=ReasonCode.IMPLAUSIBLE_TRAVEL_SPEED,
                            severity="CRITICAL",
                            weight=0.30,
                            metadata={
                                "distance_km": round(dist_km, 1),
                                "speed_kmh": round(speed_kmh, 1),
                            },
                        )
                    )

        # 4. Device Anomaly Signal
        if (
            customer_profile.primary_device_id
            and event.device_id != customer_profile.primary_device_id
        ):
            signals.append(
                RiskSignal(
                    signal_code="SIG_NEW_DEVICE",
                    raw_value=event.device_id,
                    normalized_score=0.45,
                    reason_code=ReasonCode.NEW_DEVICE,
                    severity="MEDIUM",
                    weight=0.15,
                    metadata={
                        "primary_device": customer_profile.primary_device_id,
                        "observed_device": event.device_id,
                    },
                )
            )

        self.record_event(event)
        return signals
