"""
JWKS caching and Keycloak helpers.
"""
import logging
from django.core.cache import caches
from django.conf import settings
import requests

logger = logging.getLogger(__name__)


class JWKSCache:
    """
    Caches JWKS keys with:
    - Per-kid caching
    - Auto-refresh on signature failure
    - Key rotation support
    """
    CACHE_KEY_PREFIX = "keycloak_jwks"
    DEFAULT_TTL = 300  # 5 minutes

    def __init__(self):
        self.cache = caches.get("jwks", caches["default"])
        self.jwks_url = (
            f"{settings.KEYCLOAK_SERVER_URL}"
            f"/realms/{settings.KEYCLOAK_REALM}"
            "/protocol/openid-connect/certs"
        )

    def get_key(self, kid: str, force_refresh: bool = False):
        """
        Get public key by kid, with caching.

        Args:
            kid: Key ID from JWT header
            force_refresh: Force refresh from Keycloak

        Returns:
            Key dict or None if not found
        """
        cache_key = f"{self.CACHE_KEY_PREFIX}:{kid}"

        if not force_refresh:
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"JWKS cache hit for kid: {kid}")
                return cached

        # Fetch fresh JWKS
        logger.debug(f"Fetching JWKS from {self.jwks_url}")
        keys = self._fetch_jwks()
        for key in keys.get("keys", []):
            key_kid = key.get("kid")
            if key_kid:
                key_cache_key = f"{self.CACHE_KEY_PREFIX}:{key_kid}"
                self.cache.set(key_cache_key, key, self.DEFAULT_TTL)
                if key_kid == kid:
                    return key

        logger.warning(f"Key not found in JWKS for kid: {kid}")
        return None

    def _fetch_jwks(self):
        """Fetch JWKS from Keycloak."""
        try:
            response = requests.get(self.jwks_url, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching JWKS from {self.jwks_url}")
            return {"keys": []}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            return {"keys": []}

    def refresh_on_failure(self, kid: str):
        """
        Call this when signature verification fails.
        Forces a refresh of the key in case of rotation.

        Args:
            kid: Key ID that failed verification

        Returns:
            Key dict or None
        """
        logger.info(f"Refreshing key for kid: {kid} due to verification failure")
        return self.get_key(kid, force_refresh=True)

    def clear_cache(self):
        """Clear all cached JWKS keys."""
        # Note: This clears the entire jwks cache
        self.cache.clear()
        logger.info("JWKS cache cleared")


# Singleton instance
_jwks_cache = None


def get_jwks_cache() -> JWKSCache:
    """Get the singleton JWKS cache instance."""
    global _jwks_cache
    if _jwks_cache is None:
        _jwks_cache = JWKSCache()
    return _jwks_cache
