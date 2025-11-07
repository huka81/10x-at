import streamlit as st
import logging
from typing import Optional
from database.users import validate_user_credentials, AuthenticationError

logger = logging.getLogger(__name__)


def show_login_page():
    """Display the login page"""
    # Remove the set_page_config call from here - it's already set in main.py

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(
            """
        <div style="text-align: center; margin-bottom: 30px;">
            <h1>🔐 AIVestor</h1>
            <p style="color: #666; font-size: 16px;">Zaloguj się do swojego konta</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Login form
        with st.form("login_form"):
            st.markdown("### Logowanie")

            username = st.text_input(
                "Nazwa użytkownika",
                placeholder="Wprowadź nazwę użytkownika",
                help="Podaj swoją nazwę użytkownika",
            )

            password = st.text_input(
                "Hasło",
                type="password",
                placeholder="Wprowadź hasło",
                help="Podaj swoje hasło",
            )

            col_left, col_right = st.columns([1, 1])

            with col_left:
                login_button = st.form_submit_button(
                    "🔑 Zaloguj się", type="primary", use_container_width=True
                )

            with col_right:
                forgot_password = st.form_submit_button(
                    "🔄 Przypomnij hasło", use_container_width=True
                )

        # Handle login
        if login_button:
            if not username or not password:
                st.error("❌ Proszę wypełnić wszystkie pola")
            else:
                with st.spinner("Sprawdzanie danych logowania..."):
                    try:
                        is_valid, user_data = validate_user_credentials(
                            username, password
                        )

                        if is_valid and user_data:
                            # Store user data in session state
                            st.session_state.authenticated = True
                            st.session_state.user_data = user_data
                            st.success("✅ Logowanie pomyślne!")
                            st.rerun()
                        else:
                            st.error("❌ Nieprawidłowa nazwa użytkownika lub hasło")
                    except AuthenticationError as e:
                        st.error(f"❌ Błąd uwierzytelniania: {e}")
                    except Exception as e:
                        st.error(
                            "❌ Wystąpił błąd podczas logowania. Spróbuj ponownie."
                        )
                        logger.error(f"Login error: {e}")

        # Handle forgot password
        if forgot_password:
            st.info("📧 Funkcja przypomnienia hasła zostanie wkrótce dodana")

        # Footer
        st.markdown("---")
        st.markdown(
            "<p style='text-align: center; color: #666; font-size: 12px;'>"
            "© 2025 AIVestor System | Bezpieczne logowanie"
            "</p>",
            unsafe_allow_html=True,
        )


def check_authentication() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get("authenticated", False)


def get_current_user() -> Optional[dict]:
    """Get current user data from session"""
    return st.session_state.get("user_data", None)


def logout():
    """Logout user and clear session"""
    st.session_state.authenticated = False
    st.session_state.user_data = None
    # Clear all session state
    for key in list(st.session_state.keys()):
        if key not in ["authenticated", "user_data"]:
            del st.session_state[key]
    st.rerun()


def show_user_info():
    """Display user information in sidebar"""
    user_data = get_current_user()
    if user_data:
        st.sidebar.markdown(f"### 👤 Witaj, {user_data['username']}!")
        st.sidebar.markdown(f"📧 {user_data['email']}")

        # Show last login if available
        if user_data.get("last_login"):
            last_login = user_data["last_login"]
            if hasattr(last_login, "strftime"):
                last_login_str = last_login.strftime("%Y-%m-%d %H:%M")
                st.sidebar.markdown(f"🕐 Ostatnie logowanie: {last_login_str}")

        # Logout button
        if st.sidebar.button(
            "🚪 Wyloguj się", type="secondary", use_container_width=True
        ):
            logout()

        st.sidebar.markdown("---")


def require_auth(func):
    """Decorator to require authentication for a function"""

    def wrapper(*args, **kwargs):
        if not check_authentication():
            show_login_page()
            return
        return func(*args, **kwargs)

    return wrapper
