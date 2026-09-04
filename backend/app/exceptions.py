"""
RazorShield AI — Exception Hierarchy & Taxonomy
Domain exceptions preserving original cause lineage and correlation details.
"""

from typing import Any


class RazorShieldError(Exception):
    """Base exception for all RazorShield AI platform errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.cause = cause

    def to_dict(self, request_id: str = "", correlation_id: str = "") -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
            "request_id": request_id,
            "correlation_id": correlation_id,
        }


class ValidationError(RazorShieldError):
    """Raised when incoming payment event violates boundary constraints."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details,
            cause=cause,
        )


class IdempotencyConflictError(RazorShieldError):
    """Raised when exact duplicate event request is received."""

    def __init__(
        self,
        message: str,
        existing_response: dict[str, Any],
        cause: BaseException | None = None,
    ):
        super().__init__(
            message=message,
            error_code="IDEMPOTENCY_CONFLICT",
            status_code=409,
            details={"existing_response": existing_response},
            cause=cause,
        )


class IdempotencyInProgressError(RazorShieldError):
    """Raised when duplicate concurrent request is currently being processed."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="IDEMPOTENCY_IN_PROGRESS",
            status_code=409,
            details=details,
        )


class AuditPersistenceError(RazorShieldError):
    """Raised when cryptographically chained audit record cannot be committed to ledger."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ):
        super().__init__(
            message=message,
            error_code="AUDIT_PERSISTENCE_FAILURE",
            status_code=500,
            details=details,
            cause=cause,
        )


class DependencyUnavailableError(RazorShieldError):
    """Raised when downstream dependency (e.g. Redis) is unreachable."""

    def __init__(
        self, message: str, dependency_name: str, cause: BaseException | None = None
    ):
        super().__init__(
            message=message,
            error_code="DEPENDENCY_UNAVAILABLE",
            status_code=503,
            details={"dependency": dependency_name},
            cause=cause,
        )
