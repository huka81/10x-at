import os
from typing import Optional, Tuple

from database import SessionM
from sqlalchemy import text
from tools.encryption import decrypt_password, encrypt_password
from tools.logger import get_logger

logger = get_logger(__name__)

# Database table constant
USERS_TABLE = "at.users"


class AuthenticationError(Exception):
    """Custom exception for authentication errors"""

    pass


def validate_user_credentials(
    username: str, password: str
) -> Tuple[bool, Optional[dict]]:
    """
    Validate user credentials against database

    Args:
        username: Username to validate
        password: Plain text password

    Returns:
        Tuple of (is_valid, user_data) where user_data contains user info if valid
    """
    session = SessionM()

    try:
        # Get the encrypted password from database
        sql = f"""
            SELECT user_id, username, email, is_active, created_at, last_login, password_hash
              FROM {USERS_TABLE} 
             WHERE username = :username 
               AND is_active = true
        """

        result = session.execute(text(sql), {"username": username}).first()

        if result:
            try:
                # Decrypt the stored password and compare with provided password
                stored_password = decrypt_password(result.password_hash)

                if stored_password == password:
                    user_data = {
                        "user_id": result.user_id,
                        "username": result.username,
                        "email": result.email,
                        "is_active": result.is_active,
                        "created_at": result.created_at,
                        "last_login": result.last_login,
                    }

                    # Update last login time
                    update_sql = f"""
                        UPDATE {USERS_TABLE} 
                        SET last_login = CURRENT_TIMESTAMP 
                        WHERE user_id = :user_id
                    """
                    session.execute(text(update_sql), {"user_id": result.user_id})
                    session.commit()

                    logger.info(f"User {username} successfully authenticated")
                    return True, user_data
                else:
                    logger.warning(
                        f"Authentication failed for user: {username} - incorrect password"
                    )
                    return False, None
            except Exception as decrypt_error:
                logger.error(
                    f"Error decrypting password for user {username}: {decrypt_error}"
                )
                return False, None
        else:
            logger.warning(
                f"Authentication failed for user: {username} - user not found"
            )
            return False, None

    except Exception as e:
        logger.error(f"Database error during authentication: {e}")
        session.rollback()
        return False, None
    finally:
        session.close()


def create_user(username: str, email: str, password: str) -> bool:
    """Create a new user"""
    session = SessionM()

    try:
        encrypted_password = encrypt_password(password)

        sql = f"""
        INSERT INTO {USERS_TABLE} (username, email, password_hash)
        VALUES (:username, :email, :password_hash)
        """

        session.execute(
            text(sql),
            {"username": username, "email": email, "password_hash": encrypted_password},
        )
        session.commit()

        logger.info(f"User {username} created successfully")
        return True

    except Exception as e:
        logger.error(f"Error creating user: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def change_password(username: str, new_password: str) -> bool:
    """Change user password"""
    session = SessionM()

    try:
        encrypted_password = encrypt_password(new_password)

        sql = f"""
        UPDATE {USERS_TABLE} 
           SET password_hash = :password_hash, updated_at = CURRENT_TIMESTAMP
         WHERE username = :username
        """

        result = session.execute(
            text(sql), {"username": username, "password_hash": encrypted_password}
        )

        if result.rowcount > 0:
            session.commit()
            logger.info(f"Password changed for user {username}")
            return True
        else:
            logger.warning(f"User {username} not found")
            return False

    except Exception as e:
        logger.error(f"Error changing password: {e}")
        session.rollback()
        return False
    finally:
        session.close()


# Add these functions to your existing users.py file


def get_all_users() -> list:
    """Get all users from database"""
    session = SessionM()

    try:
        sql = f"""
            SELECT user_id, username, email, is_active, created_at, last_login, updated_at
            FROM {USERS_TABLE}
            ORDER BY created_at DESC
        """

        result = session.execute(text(sql))
        users = []

        for row in result:
            users.append(
                {
                    "user_id": row.user_id,
                    "username": row.username,
                    "email": row.email,
                    "is_active": row.is_active,
                    "created_at": row.created_at,
                    "last_login": row.last_login,
                    "updated_at": row.updated_at,
                }
            )

        logger.info(f"Retrieved {len(users)} users")
        return users

    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return []
    finally:
        session.close()


def deactivate_user(user_id: int) -> bool:
    """Deactivate a user"""
    session = SessionM()

    try:
        sql = f"""
            UPDATE {USERS_TABLE} 
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = :user_id
        """

        result = session.execute(text(sql), {"user_id": user_id})

        if result.rowcount > 0:
            session.commit()
            logger.info(f"User {user_id} deactivated")
            return True
        else:
            logger.warning(f"User {user_id} not found")
            return False

    except Exception as e:
        logger.error(f"Error deactivating user: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def activate_user(user_id: int) -> bool:
    """Activate a user"""
    session = SessionM()

    try:
        sql = f"""
            UPDATE {USERS_TABLE} 
            SET is_active = TRUE, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = :user_id
        """

        result = session.execute(text(sql), {"user_id": user_id})

        if result.rowcount > 0:
            session.commit()
            logger.info(f"User {user_id} activated")
            return True
        else:
            logger.warning(f"User {user_id} not found")
            return False

    except Exception as e:
        logger.error(f"Error activating user: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def delete_user(user_id: int) -> bool:
    """Delete a user (use with caution)"""
    session = SessionM()

    try:
        sql = f"""
            DELETE FROM {USERS_TABLE} 
            WHERE user_id = :user_id
        """

        result = session.execute(text(sql), {"user_id": user_id})

        if result.rowcount > 0:
            session.commit()
            logger.info(f"User {user_id} deleted")
            return True
        else:
            logger.warning(f"User {user_id} not found")
            return False

    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        session.rollback()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    # Example usage
    # create_user("testuser", "test@example.com", "password123")
    # validate_user_credentials("testuser", "password123")
    # change_password("testuser", "newpassword123")
    # validate_user_credentials("testuser", "password123")
    # validate_user_credentials("testuser", "newpassword123")
    p = encrypt_password("password123")
    print(p)
    import os

    p = encrypt_password(os.getenv("DB_PASSWORD"))
    print(p)
