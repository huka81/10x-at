"""Tests for user management functionality."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database import get_session
from database.users import (
    create_user,
    validate_user_credentials,
    change_password,
    get_all_users,
    activate_user,
    deactivate_user,
    delete_user,
    AuthenticationError,
    USERS_TABLE,
)


class TestUserCreation:
    """Test user creation functionality."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Setup: Clean up any test users before each test
        session = get_session()
        try:
            session.execute(
                text(f"DELETE FROM {USERS_TABLE} WHERE username LIKE 'test_%'")
            )
            session.commit()
        finally:
            session.close()

        yield

        # Teardown: Clean up test users after each test
        session = get_session()
        try:
            session.execute(
                text(f"DELETE FROM {USERS_TABLE} WHERE username LIKE 'test_%'")
            )
            session.commit()
        finally:
            session.close()

    def test_should_create_user_successfully(self):
        """Test that a new user can be created successfully."""
        username = "test_user_create"
        email = "test_create@example.com"
        password = "test_password_123"

        result = create_user(username, email, password)

        assert result is True

        # Verify user exists in database
        session = get_session()
        try:
            sql = f"SELECT username, email, is_active FROM {USERS_TABLE} WHERE username = :username"
            user = session.execute(text(sql), {"username": username}).first()

            assert user is not None
            assert user.username == username
            assert user.email == email
            assert user.is_active is True
        finally:
            session.close()

    def test_should_fail_creating_duplicate_user(self):
        """Test that creating a user with duplicate username fails."""
        username = "test_user_duplicate"
        email = "test_dup@example.com"
        password = "test_password_123"

        # Create first user
        result1 = create_user(username, email, password)
        assert result1 is True

        # Try to create duplicate user
        result2 = create_user(username, "different@example.com", "different_pass")
        assert result2 is False

    def test_should_create_user_with_encrypted_password(self):
        """Test that user password is stored encrypted."""
        username = "test_user_encrypted"
        email = "test_encrypted@example.com"
        password = "plain_text_password"

        create_user(username, email, password)

        # Verify password is not stored in plain text
        session = get_session()
        try:
            sql = f"SELECT password_hash FROM {USERS_TABLE} WHERE username = :username"
            result = session.execute(text(sql), {"username": username}).first()

            assert result is not None
            assert result.password_hash != password
            assert len(result.password_hash) > 0
        finally:
            session.close()


class TestUserAuthentication:
    """Test user authentication functionality."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Setup: Create a test user
        self.test_username = "test_auth_user"
        self.test_email = "test_auth@example.com"
        self.test_password = "correct_password_123"

        session = get_session()
        try:
            session.execute(
                text(f"DELETE FROM {USERS_TABLE} WHERE username = :username"),
                {"username": self.test_username},
            )
            session.commit()
        finally:
            session.close()

        create_user(self.test_username, self.test_email, self.test_password)

        yield

        # Teardown
        session = get_session()
        try:
            session.execute(
                text(f"DELETE FROM {USERS_TABLE} WHERE username = :username"),
                {"username": self.test_username},
            )
            session.commit()
        finally:
            session.close()

    def test_should_authenticate_with_correct_credentials(self):
        """Test successful authentication with correct credentials."""
        is_valid, user_data = validate_user_credentials(
            self.test_username, self.test_password
        )

        assert is_valid is True
        assert user_data is not None
        assert user_data["username"] == self.test_username
        assert user_data["email"] == self.test_email
        assert user_data["is_active"] is True
        assert "user_id" in user_data
        assert "created_at" in user_data

    def test_should_fail_authentication_with_wrong_password(self):
        """Test authentication fails with incorrect password."""
        is_valid, user_data = validate_user_credentials(
            self.test_username, "wrong_password"
        )

        assert is_valid is False
        assert user_data is None

    def test_should_fail_authentication_with_nonexistent_user(self):
        """Test authentication fails for non-existent user."""
        is_valid, user_data = validate_user_credentials(
            "nonexistent_user", "any_password"
        )

        assert is_valid is False
        assert user_data is None

    def test_should_update_last_login_on_successful_auth(self):
        """Test that last_login is updated on successful authentication."""
        # Get initial last_login
        session = get_session()
        try:
            sql = f"SELECT last_login FROM {USERS_TABLE} WHERE username = :username"
            initial_result = session.execute(
                text(sql), {"username": self.test_username}
            ).first()
            initial_last_login = initial_result.last_login
        finally:
            session.close()

        # Authenticate
        validate_user_credentials(self.test_username, self.test_password)

        # Check last_login was updated
        session = get_session()
        try:
            updated_result = session.execute(
                text(sql), {"username": self.test_username}
            ).first()
            updated_last_login = updated_result.last_login

            assert updated_last_login is not None
            if initial_last_login is not None:
                assert updated_last_login >= initial_last_login
        finally:
            session.close()

    def test_should_fail_authentication_for_inactive_user(self):
        """Test that inactive users cannot authenticate."""
        # Deactivate user
        session = get_session()
        try:
            sql = f"UPDATE {USERS_TABLE} SET is_active = FALSE WHERE username = :username"
            session.execute(text(sql), {"username": self.test_username})
            session.commit()
        finally:
            session.close()

        # Try to authenticate
        is_valid, user_data = validate_user_credentials(
            self.test_username, self.test_password
        )

        assert is_valid is False
        assert user_data is None


class TestPasswordManagement:
    """Test password change functionality."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        self.test_username = "test_password_user"
        self.test_email = "test_pass@example.com"
        self.initial_password = "initial_password_123"

        session = get_session()
        try:
            session.execute(
                text(f"DELETE FROM {USERS_TABLE} WHERE username = :username"),
                {"username": self.test_username},
            )
            session.commit()
        finally:
            session.close()

        create_user(self.test_username, self.test_email, self.initial_password)

        yield

        session = get_session()
        try:
            session.execute(
                text(f"DELETE FROM {USERS_TABLE} WHERE username = :username"),
                {"username": self.test_username},
            )
            session.commit()
        finally:
            session.close()

    def test_should_change_password_successfully(self):
        """Test that password can be changed successfully."""
        new_password = "new_password_456"

        result = change_password(self.test_username, new_password)

        assert result is True

        # Verify old password no longer works
        is_valid_old, _ = validate_user_credentials(
            self.test_username, self.initial_password
        )
        assert is_valid_old is False

        # Verify new password works
        is_valid_new, user_data = validate_user_credentials(
            self.test_username, new_password
        )
        assert is_valid_new is True
        assert user_data is not None

    def test_should_fail_changing_password_for_nonexistent_user(self):
        """Test that changing password for non-existent user fails."""
        result = change_password("nonexistent_user", "new_password")

        assert result is False

    def test_should_encrypt_new_password(self):
        """Test that new password is stored encrypted."""
        new_password = "new_encrypted_password"

        change_password(self.test_username, new_password)

        # Verify password is not stored in plain text
        session = get_session()
        try:
            sql = f"SELECT password_hash FROM {USERS_TABLE} WHERE username = :username"
            result = session.execute(
                text(sql), {"username": self.test_username}
            ).first()

            assert result is not None
            assert result.password_hash != new_password
            assert len(result.password_hash) > 0
        finally:
            session.close()


class TestUserManagement:
    """Test user management operations (activate, deactivate, delete)."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        self.test_username = "test_mgmt_user"
        self.test_email = "test_mgmt@example.com"
        self.test_password = "test_password_123"

        session = get_session()
        try:
            session.execute(
                text(f"DELETE FROM {USERS_TABLE} WHERE username = :username"),
                {"username": self.test_username},
            )
            session.commit()
        finally:
            session.close()

        create_user(self.test_username, self.test_email, self.test_password)

        # Get user_id
        session = get_session()
        try:
            sql = f"SELECT user_id FROM {USERS_TABLE} WHERE username = :username"
            result = session.execute(
                text(sql), {"username": self.test_username}
            ).first()
            self.user_id = result.user_id
        finally:
            session.close()

        yield

        session = get_session()
        try:
            session.execute(
                text(f"DELETE FROM {USERS_TABLE} WHERE username = :username"),
                {"username": self.test_username},
            )
            session.commit()
        finally:
            session.close()

    def test_should_deactivate_user(self):
        """Test that user can be deactivated."""
        result = deactivate_user(self.user_id)

        assert result is True

        # Verify user is inactive
        session = get_session()
        try:
            sql = f"SELECT is_active FROM {USERS_TABLE} WHERE user_id = :user_id"
            user = session.execute(text(sql), {"user_id": self.user_id}).first()
            assert user.is_active is False
        finally:
            session.close()

    def test_should_activate_user(self):
        """Test that user can be activated."""
        # First deactivate
        deactivate_user(self.user_id)

        # Then activate
        result = activate_user(self.user_id)

        assert result is True

        # Verify user is active
        session = get_session()
        try:
            sql = f"SELECT is_active FROM {USERS_TABLE} WHERE user_id = :user_id"
            user = session.execute(text(sql), {"user_id": self.user_id}).first()
            assert user.is_active is True
        finally:
            session.close()

    def test_should_delete_user(self):
        """Test that user can be deleted."""
        result = delete_user(self.user_id)

        assert result is True

        # Verify user no longer exists
        session = get_session()
        try:
            sql = f"SELECT user_id FROM {USERS_TABLE} WHERE user_id = :user_id"
            user = session.execute(text(sql), {"user_id": self.user_id}).first()
            assert user is None
        finally:
            session.close()

    def test_should_get_all_users(self):
        """Test that all users can be retrieved."""
        users = get_all_users()

        assert isinstance(users, list)
        assert len(users) > 0

        # Find our test user
        test_user = next(
            (u for u in users if u["username"] == self.test_username), None
        )
        assert test_user is not None
        assert test_user["email"] == self.test_email
        assert "user_id" in test_user
        assert "is_active" in test_user
        assert "created_at" in test_user

    def test_should_fail_deactivating_nonexistent_user(self):
        """Test that deactivating non-existent user fails."""
        result = deactivate_user(999999)

        assert result is False

    def test_should_fail_activating_nonexistent_user(self):
        """Test that activating non-existent user fails."""
        result = activate_user(999999)

        assert result is False

    def test_should_fail_deleting_nonexistent_user(self):
        """Test that deleting non-existent user fails."""
        result = delete_user(999999)

        assert result is False
