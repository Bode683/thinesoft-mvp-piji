"""
Keycloak Admin Service

This service uses the djangocms-client (confidential client) to perform
administrative operations on Keycloak via the Admin API.

This is separate from JWT validation - this is for outgoing admin calls only.
"""

from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class KeycloakService:
    """
    Service for Keycloak administrative operations.

    Uses the backend service account (djangocms-client) to:
    - Create/update/delete users
    - Manage roles and groups
    - Perform admin operations

    This is NOT used for validating incoming JWT tokens.
    """

    def __init__(self):
        """Initialize Keycloak Admin client with backend credentials."""
        try:
            self.admin = KeycloakAdmin(
                server_url=settings.KEYCLOAK_SERVER_URL,
                realm_name=settings.KEYCLOAK_REALM,
                client_id=settings.KEYCLOAK_BACKEND_CLIENT_ID,
                client_secret_key=settings.KEYCLOAK_BACKEND_CLIENT_SECRET,
                verify=True
            )
            logger.info(
                f"Keycloak Admin Service initialized "
                f"(realm: {settings.KEYCLOAK_REALM}, "
                f"client: {settings.KEYCLOAK_BACKEND_CLIENT_ID})"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Keycloak Admin: {str(e)}", exc_info=True)
            raise

    def create_user(self, username, email, password=None, first_name='', last_name='', **kwargs):
        """
        Create a new user in Keycloak.

        Args:
            username (str): Username
            email (str): Email address
            password (str, optional): User password
            first_name (str): First name
            last_name (str): Last name
            **kwargs: Additional user attributes

        Returns:
            str: User ID if successful

        Raises:
            KeycloakError: If user creation fails
        """
        try:
            user_payload = {
                "username": username,
                "email": email,
                "firstName": first_name,
                "lastName": last_name,
                "enabled": kwargs.get('enabled', True),
                "emailVerified": kwargs.get('email_verified', False),
            }

            # Add password credentials if provided
            if password:
                user_payload["credentials"] = [{
                    "type": "password",
                    "value": password,
                    "temporary": kwargs.get('temporary_password', False)
                }]

            # Add any additional attributes
            if 'attributes' in kwargs:
                user_payload['attributes'] = kwargs['attributes']

            user_id = self.admin.create_user(user_payload)
            logger.info(f"Created user: {username} (ID: {user_id})")
            return user_id

        except KeycloakError as e:
            logger.error(f"Failed to create user {username}: {str(e)}")
            raise

    def get_user(self, user_id):
        """
        Get user details from Keycloak.

        Args:
            user_id (str): Keycloak user ID

        Returns:
            dict: User details

        Raises:
            KeycloakError: If user not found
        """
        try:
            user = self.admin.get_user(user_id)
            return user
        except KeycloakError as e:
            logger.error(f"Failed to get user {user_id}: {str(e)}")
            raise

    def get_user_by_username(self, username):
        """
        Get user by username.

        Args:
            username (str): Username

        Returns:
            dict: User details or None if not found
        """
        try:
            users = self.admin.get_users({"username": username, "exact": True})
            return users[0] if users else None
        except KeycloakError as e:
            logger.error(f"Failed to get user by username {username}: {str(e)}")
            raise

    def update_user(self, user_id, **kwargs):
        """
        Update user attributes.

        Args:
            user_id (str): Keycloak user ID
            **kwargs: User attributes to update

        Returns:
            None

        Raises:
            KeycloakError: If update fails
        """
        try:
            self.admin.update_user(user_id, kwargs)
            logger.info(f"Updated user: {user_id}")
        except KeycloakError as e:
            logger.error(f"Failed to update user {user_id}: {str(e)}")
            raise

    def delete_user(self, user_id):
        """
        Delete a user from Keycloak.

        Args:
            user_id (str): Keycloak user ID

        Returns:
            None

        Raises:
            KeycloakError: If deletion fails
        """
        try:
            self.admin.delete_user(user_id)
            logger.info(f"Deleted user: {user_id}")
        except KeycloakError as e:
            logger.error(f"Failed to delete user {user_id}: {str(e)}")
            raise

    def assign_realm_role(self, user_id, role_name):
        """
        Assign a realm role to a user.

        Args:
            user_id (str): Keycloak user ID
            role_name (str): Role name

        Returns:
            None

        Raises:
            KeycloakError: If role assignment fails
        """
        try:
            role = self.admin.get_realm_role(role_name)
            self.admin.assign_realm_roles(user_id, [role])
            logger.info(f"Assigned role '{role_name}' to user {user_id}")
        except KeycloakError as e:
            logger.error(
                f"Failed to assign role '{role_name}' to user {user_id}: {str(e)}"
            )
            raise

    def remove_realm_role(self, user_id, role_name):
        """
        Remove a realm role from a user.

        Args:
            user_id (str): Keycloak user ID
            role_name (str): Role name

        Returns:
            None

        Raises:
            KeycloakError: If role removal fails
        """
        try:
            role = self.admin.get_realm_role(role_name)
            self.admin.delete_realm_roles_of_user(user_id, [role])
            logger.info(f"Removed role '{role_name}' from user {user_id}")
        except KeycloakError as e:
            logger.error(
                f"Failed to remove role '{role_name}' from user {user_id}: {str(e)}"
            )
            raise

    def get_user_roles(self, user_id):
        """
        Get all realm roles assigned to a user.

        Args:
            user_id (str): Keycloak user ID

        Returns:
            list: List of role objects

        Raises:
            KeycloakError: If fetching roles fails
        """
        try:
            roles = self.admin.get_realm_roles_of_user(user_id)
            return roles
        except KeycloakError as e:
            logger.error(f"Failed to get roles for user {user_id}: {str(e)}")
            raise

    def add_user_to_group(self, user_id, group_id):
        """
        Add user to a group.

        Args:
            user_id (str): Keycloak user ID
            group_id (str): Keycloak group ID

        Returns:
            None

        Raises:
            KeycloakError: If adding to group fails
        """
        try:
            self.admin.group_user_add(user_id, group_id)
            logger.info(f"Added user {user_id} to group {group_id}")
        except KeycloakError as e:
            logger.error(
                f"Failed to add user {user_id} to group {group_id}: {str(e)}"
            )
            raise

    def remove_user_from_group(self, user_id, group_id):
        """
        Remove user from a group.

        Args:
            user_id (str): Keycloak user ID
            group_id (str): Keycloak group ID

        Returns:
            None

        Raises:
            KeycloakError: If removal from group fails
        """
        try:
            self.admin.group_user_remove(user_id, group_id)
            logger.info(f"Removed user {user_id} from group {group_id}")
        except KeycloakError as e:
            logger.error(
                f"Failed to remove user {user_id} from group {group_id}: {str(e)}"
            )
            raise

    def reset_password(self, user_id, new_password, temporary=False):
        """
        Reset user password.

        Args:
            user_id (str): Keycloak user ID
            new_password (str): New password
            temporary (bool): Whether password should be temporary

        Returns:
            None

        Raises:
            KeycloakError: If password reset fails
        """
        try:
            self.admin.set_user_password(user_id, new_password, temporary)
            logger.info(f"Reset password for user {user_id}")
        except KeycloakError as e:
            logger.error(f"Failed to reset password for user {user_id}: {str(e)}")
            raise


# Singleton instance
_keycloak_service = None


def get_keycloak_service():
    """
    Get singleton instance of KeycloakService.

    Returns:
        KeycloakService: Keycloak admin service instance
    """
    global _keycloak_service
    if _keycloak_service is None:
        _keycloak_service = KeycloakService()
    return _keycloak_service
