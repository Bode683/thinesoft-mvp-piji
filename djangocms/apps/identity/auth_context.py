"""
Authentication context extracted from Keycloak JWT tokens.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class AuthContext:
    """
    Holds authentication context extracted from Keycloak token.
    Attached to request as request.auth_context

    This is the source of truth for:
    - User identity (keycloak_id, username, email)
    - Platform-level roles (realm_roles)
    - Client-specific roles (client_roles)
    """
    keycloak_id: str
    username: str
    email: str
    first_name: str = ""
    last_name: str = ""
    realm_roles: List[str] = field(default_factory=list)
    client_roles: List[str] = field(default_factory=list)
    raw_token: Dict[str, Any] = field(default_factory=dict)

    def has_realm_role(self, role: str) -> bool:
        """Check if user has a specific realm role."""
        return role in self.realm_roles

    def has_client_role(self, role: str) -> bool:
        """Check if user has a specific client role."""
        return role in self.client_roles

    def is_platform_admin(self) -> bool:
        """
        Check if user is a platform administrator.
        Platform admin is the ONLY realm role we check in Django.
        """
        return self.has_realm_role("platform_admin")

    @property
    def full_name(self) -> str:
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
