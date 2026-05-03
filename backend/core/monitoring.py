"""
TokenLens — Google Cloud Monitoring Integration
=================================================
Emits custom metrics to Cloud Monitoring:
  - token_savings_ratio
  - cache_hit_rate
  - cost_per_request
"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger("tokenlens.monitoring")

# Cloud Monitoring metric type prefix
METRIC_PREFIX = "custom.googleapis.com/tokenlens"


class CloudMetricsEmitter:
    """
    Emits custom metrics to Google Cloud Monitoring.
    Falls back to local logging when not running on GCP.
    """

    def __init__(self) -> None:
        self._client = None
        self._project_id: Optional[str] = os.environ.get("GOOGLE_CLOUD_PROJECT")
        self._project_path: Optional[str] = None
        self._initialized = False
        self._initialize()

    def _initialize(self) -> None:
        """Attempt to set up the Cloud Monitoring client."""
        if not self._project_id:
            logger.info("Cloud Monitoring: GOOGLE_CLOUD_PROJECT not set, using local logging")
            return

        try:
            from google.cloud import monitoring_v3

            self._client = monitoring_v3.MetricServiceClient()
            self._project_path = f"projects/{self._project_id}"
            self._initialized = True
            logger.info("Cloud Monitoring initialized for project=%s", self._project_id)
        except Exception as e:
            logger.info("Cloud Monitoring not available: %s", e)

    def emit_token_savings(self, ratio: float) -> None:
        """Emit token_savings_ratio metric (0.0 - 1.0)."""
        self._emit_gauge(f"{METRIC_PREFIX}/token_savings_ratio", ratio)

    def emit_cache_hit_rate(self, rate: float) -> None:
        """Emit cache_hit_rate metric (0.0 - 100.0)."""
        self._emit_gauge(f"{METRIC_PREFIX}/cache_hit_rate", rate)

    def emit_cost_per_request(self, cost: float) -> None:
        """Emit cost_per_request metric in USD."""
        self._emit_gauge(f"{METRIC_PREFIX}/cost_per_request", cost)

    def _emit_gauge(self, metric_type: str, value: float) -> None:
        """Write a gauge metric value to Cloud Monitoring."""
        if not self._initialized or not self._client:
            logger.debug("Metric (local): %s = %.6f", metric_type, value)
            return

        try:
            from google.api import metric_pb2
            from google.cloud import monitoring_v3
            from google.protobuf import timestamp_pb2
            import time

            series = monitoring_v3.TimeSeries()
            series.metric.type = metric_type
            series.resource.type = "global"

            now = time.time()
            seconds = int(now)
            nanos = int((now - seconds) * 1e9)

            interval = monitoring_v3.TimeInterval()
            interval.end_time = timestamp_pb2.Timestamp(seconds=seconds, nanos=nanos)

            point = monitoring_v3.Point()
            point.interval = interval
            point.value.double_value = value
            series.points = [point]

            self._client.create_time_series(
                request={
                    "name": self._project_path,
                    "time_series": [series],
                }
            )
            logger.debug("Metric emitted: %s = %.6f", metric_type, value)
        except Exception as e:
            logger.warning("Failed to emit metric %s: %s", metric_type, e)
