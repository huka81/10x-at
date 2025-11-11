"""
User management utility for creating and managing users.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.users import create_user, change_password, validate_user_credentials
from tools.logger import get_logger

logger = get_logger(__name__)


def create_admin_user():
    """Create default admin user"""
    try:
        success = create_user("admin", "admin@example.com", "admin123")
        if success:
            print("✅ Admin user created successfully!")
            print("Username: admin")
            print("Password: admin123")
            print("Email: admin@example.com")
        else:
            print("❌ Failed to create admin user (may already exist)")
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")


def create_test_user():
    """Create test user"""
    try:
        success = create_user("testuser", "test@example.com", "test123")
        if success:
            print("✅ Test user created successfully!")
            print("Username: testuser")
            print("Password: test123")
            print("Email: test@example.com")
        else:
            print("❌ Failed to create test user (may already exist)")
    except Exception as e:
        print(f"❌ Error creating test user: {e}")


def test_authentication():
    """Test authentication with created users"""
    print("\n🔍 Testing authentication...")

    # Test admin user
    is_valid, user_data = validate_user_credentials("admin", "admin123")
    if is_valid:
        print("✅ Admin authentication successful")
        print(f"   User ID: {user_data['user_id']}")
        print(f"   Username: {user_data['username']}")
        print(f"   Email: {user_data['email']}")
    else:
        print("❌ Admin authentication failed")

    # Test with wrong password
    is_valid, _ = validate_user_credentials("admin", "wrongpassword")
    if not is_valid:
        print("✅ Correctly rejected wrong password")
    else:
        print("❌ Security issue: accepted wrong password")


def interactive_user_creation():
    """Interactive user creation"""
    print("\n👤 Interaktywne tworzenie użytkownika")
    print("=" * 40)

    try:
        username = input("Nazwa użytkownika: ").strip()
        email = input("Email: ").strip()
        password = input("Hasło: ").strip()

        if not username or not email or not password:
            print("❌ Wszystkie pola są wymagane!")
            return

        success = create_user(username, email, password)
        if success:
            print(f"✅ Użytkownik {username} utworzony pomyślnie!")
        else:
            print("❌ Nie udało się utworzyć użytkownika")

    except KeyboardInterrupt:
        print("\n❌ Anulowano tworzenie użytkownika")
    except Exception as e:
        print(f"❌ Błąd: {e}")


def main():
    """Main function"""
    print("🔐 Trading Portfolio - Zarządzanie użytkownikami")
    print("=" * 50)

    while True:
        print("\nWybierz opcję:")
        print("1. Utwórz użytkownika admin")
        print("2. Utwórz użytkownika testowego")
        print("3. Utwórz nowego użytkownika (interaktywnie)")
        print("4. Przetestuj uwierzytelnianie")
        print("5. Wyjście")

        choice = input("\nWybór (1-5): ").strip()

        if choice == "1":
            create_admin_user()
        elif choice == "2":
            create_test_user()
        elif choice == "3":
            interactive_user_creation()
        elif choice == "4":
            test_authentication()
        elif choice == "5":
            print("👋 Do widzenia!")
            break
        else:
            print("❌ Nieprawidłowy wybór. Spróbuj ponownie.")


if __name__ == "__main__":
    main()
