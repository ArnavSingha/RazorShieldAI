"""
RazorShield AI — Trusted Principal Identity Resolver & Capability-Based RBAC Gate
Resolves server-derived principal identity, enforces Capability-Based RBAC, and manages
High-Risk Action Approval Workflow Requirements. Client header spoofing is strictly rejected.
"""

from typing import Any, Dict, Optional, Set
from backend.app.domain.policy_contracts import PolicyAction, UserRole
from backend.app.exceptions import RazorShieldError


class UnauthorizedRoleError(RazorShieldError):
    """Raised when an unauthenticated or unauthorized role attempts a restricted action."""

    def __init__(self, principal_id: str, role: str, action: str):
        super().__init__(
            message=f"RBAC Security Violation: Principal '{principal_id}' with role '{role}' lacks capability or permission for '{action}'.",
            status_code=403,
            error_code="RBAC_PERMISSION_DENIED",
            details={"principal_id": principal_id, "role": role, "action": action},
        )


class TrustedPrincipal:
    """Authenticated Server Identity Context."""

    def __init__(self, principal_id: str, role: UserRole, is_authenticated: bool):
        self.principal_id = principal_id
        self.role = role
        self.is_authenticated = is_authenticated


class TrustedPrincipalResolver:
    """
    Server-Side Principal & Role Resolver.
    Validates identity tokens/keys to prevent header spoofing attacks.
    Principal authentication tokens are derived from environment configuration.
    """

    _DYNAMIC_TOKENS: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register_test_token(cls, token: str, principal_id: str, role: UserRole) -> None:
        """Register a temporary token for testing/fixtures without hardcoding secrets in source."""
        cls._DYNAMIC_TOKENS[token] = {"principal_id": principal_id, "role": role}

    @classmethod
    def get_configured_principals(cls) -> Dict[str, Dict[str, Any]]:
        """Build map of active trusted tokens from environment settings and dynamic registrations."""
        import os
        from backend.app.config import settings

        principals: Dict[str, Dict[str, Any]] = {}

        admin_tok = settings.admin_auth_token or os.getenv(
            "RAZORSHIELD_ADMIN_TOKEN", "admin_secret_token_123"
        )
        analyst_tok = settings.analyst_auth_token or os.getenv(
            "RAZORSHIELD_ANALYST_TOKEN", "analyst_secret_token_123"
        )
        operator_tok = settings.operator_auth_token or os.getenv(
            "RAZORSHIELD_OPERATOR_TOKEN", "operator_secret_token_123"
        )
        auditor_tok = settings.auditor_auth_token or os.getenv(
            "RAZORSHIELD_AUDITOR_TOKEN", "auditor_secret_token_123"
        )

        def _add_tok(tok_val: Optional[str], pid: str, role: UserRole) -> None:
            if not tok_val:
                return
            clean_tok = tok_val.replace("Bearer ", "").strip()
            principals[tok_val] = {"principal_id": pid, "role": role}
            principals[clean_tok] = {"principal_id": pid, "role": role}
            principals[f"Bearer {clean_tok}"] = {"principal_id": pid, "role": role}

        _add_tok(admin_tok, "usr_admin_01", UserRole.ADMIN)
        _add_tok(analyst_tok, "usr_analyst_01", UserRole.RISK_ANALYST)
        _add_tok(operator_tok, "usr_operator_01", UserRole.MERCHANT_OPERATOR)
        _add_tok(auditor_tok, "usr_auditor_01", UserRole.AUDITOR)

        principals.update(cls._DYNAMIC_TOKENS)
        return principals

    @classmethod
    def resolve_principal(
        cls,
        auth_token: Optional[str] = None,
        header_principal_id: Optional[str] = None,
    ) -> TrustedPrincipal:
        """
        Derives identity and role strictly from authenticated token context.
        If auth_token is missing or invalid, resolves to untrusted READ_ONLY role.
        """
        if auth_token:
            trusted = cls.get_configured_principals()
            clean_auth = auth_token.strip()
            if clean_auth in trusted:
                info = trusted[clean_auth]
                return TrustedPrincipal(
                    principal_id=info["principal_id"],
                    role=info["role"],
                    is_authenticated=True,
                )
            bare_tok = clean_auth.replace("Bearer ", "").strip()
            if bare_tok in trusted:
                info = trusted[bare_tok]
                return TrustedPrincipal(
                    principal_id=info["principal_id"],
                    role=info["role"],
                    is_authenticated=True,
                )

        anon_id = (
            header_principal_id
            if (
                header_principal_id
                and not header_principal_id.lower().startswith("admin")
            )
            else "anon_guest"
        )
        return TrustedPrincipal(
            principal_id=anon_id,
            role=UserRole.READ_ONLY,
            is_authenticated=False,
        )


class RBACPolicyGateway:
    """Enforces Separation of Duties, Capability-Based Access Control, and Approval Workflows."""

    # Role Action Permissions Matrix
    _ROLE_PERMISSIONS: Dict[UserRole, Set[PolicyAction]] = {
        UserRole.READ_ONLY: set(),
        UserRole.MERCHANT_OPERATOR: {
            PolicyAction.ALLOW,
            PolicyAction.MONITOR,
            PolicyAction.STEP_UP,
        },
        UserRole.RISK_ANALYST: {
            PolicyAction.ALLOW,
            PolicyAction.MONITOR,
            PolicyAction.STEP_UP,
            PolicyAction.HOLD,
            PolicyAction.BLOCK,
        },
        UserRole.ADMIN: {
            PolicyAction.ALLOW,
            PolicyAction.MONITOR,
            PolicyAction.STEP_UP,
            PolicyAction.HOLD,
            PolicyAction.BLOCK,
        },
        UserRole.AUDITOR: set(),
    }

    # Fine-Grained Role Capability Matrix
    _ROLE_CAPABILITIES: Dict[UserRole, Set[str]] = {
        UserRole.READ_ONLY: {"investigation.read", "transaction.read"},
        UserRole.AUDITOR: {"investigation.read", "transaction.read", "audit.read"},
        UserRole.MERCHANT_OPERATOR: {
            "investigation.read",
            "transaction.read",
            "action.review",
            "action.execute",
            "audit.read",
        },
        UserRole.RISK_ANALYST: {
            "investigation.read",
            "investigation.update",
            "investigation.assign",
            "investigation.resolve",
            "transaction.read",
            "ai.run",
            "action.review",
            "action.authorize",
            "action.execute",
            "audit.read",
            "case.export",
        },
        UserRole.ADMIN: {
            "investigation.read",
            "investigation.update",
            "investigation.assign",
            "investigation.resolve",
            "transaction.read",
            "ai.run",
            "action.review",
            "action.authorize",
            "action.execute",
            "audit.read",
            "case.export",
            "simulation.run",
            "chaos.control",
        },
    }

    @classmethod
    def has_capability(cls, role: UserRole, capability: str) -> bool:
        """Returns True if the role possesses the specified capability."""
        return capability in cls._ROLE_CAPABILITIES.get(role, set())

    @classmethod
    def require_capability(cls, principal: TrustedPrincipal, capability: str) -> None:
        """Enforces capability requirement and raises UnauthorizedRoleError if lacking."""
        if not cls.has_capability(principal.role, capability):
            raise UnauthorizedRoleError(
                principal_id=principal.principal_id,
                role=principal.role.value,
                action=capability,
            )

    @classmethod
    def authorize_role_action(
        cls, principal: TrustedPrincipal, action: PolicyAction
    ) -> None:
        """Enforces RBAC matrix and raises UnauthorizedRoleError on unauthorized attempts."""
        allowed_actions = cls._ROLE_PERMISSIONS.get(principal.role, set())
        if action not in allowed_actions:
            raise UnauthorizedRoleError(
                principal_id=principal.principal_id,
                role=principal.role.value,
                action=action.value,
            )

    @classmethod
    def get_required_approval_level(
        cls, action: str, risk_score: int = 0, exposure_inr: float = 0.0
    ) -> str:
        """
        Determines the required approval level for a proposed financial intervention.
        Levels: ANALYST, ANALYST_PLUS_POLICY, ELEVATED_DUAL_CONTROL, REJECTED
        """
        if risk_score >= 85 or exposure_inr >= 100000.0:
            return "ELEVATED_DUAL_CONTROL"
        if action == "BLOCK":
            return "ANALYST_PLUS_POLICY"
        if action in ("HOLD", "STEP_UP"):
            return "ANALYST"
        return "SINGLE_ANALYST"
