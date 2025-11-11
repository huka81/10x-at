import streamlit as st
import pandas as pd
from typing import Optional
from database.users import (
    create_user,
    change_password,
    validate_user_credentials,
    get_all_users,
    deactivate_user,
    activate_user,
    delete_user,
    AuthenticationError,
)
from ui.auth import get_current_user
from tools.logger import get_logger

logger = get_logger(__name__)


def show_user_management_view():
    """Display the user management page"""
    current_user = get_current_user()

    # Check if current user has admin privileges (you can implement role-based access later)
    if not current_user:
        st.error("❌ Błąd uwierzytelniania")
        return

    st.title("👥 Zarządzanie Użytkownikami")
    st.markdown("---")

    # Create tabs for different management functions
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📋 Lista Użytkowników",
            "➕ Dodaj Użytkownika",
            "🔑 Zmień Hasło",
            "🧪 Test Logowania",
        ]
    )

    with tab1:
        show_users_list()

    with tab2:
        show_create_user_form()

    with tab3:
        show_change_password_form()

    with tab4:
        show_test_authentication()


def show_users_list():
    """Display list of all users"""
    st.subheader("📋 Lista Użytkowników")

    try:
        users_data = get_all_users()

        if not users_data:
            st.info("📭 Brak użytkowników w systemie")
            return

        # Convert to DataFrame for better display
        df = pd.DataFrame(users_data)

        # Format the data for display
        display_df = df.copy()
        display_df["created_at"] = pd.to_datetime(display_df["created_at"]).dt.strftime(
            "%Y-%m-%d %H:%M"
        )
        display_df["last_login"] = pd.to_datetime(display_df["last_login"]).dt.strftime(
            "%Y-%m-%d %H:%M"
        )
        display_df["is_active"] = display_df["is_active"].map(
            {True: "✅ Aktywny", False: "❌ Nieaktywny"}
        )

        # Rename columns for Polish display
        display_df = display_df.rename(
            columns={
                "user_id": "ID",
                "username": "Nazwa użytkownika",
                "email": "Email",
                "is_active": "Status",
                "created_at": "Data utworzenia",
                "last_login": "Ostatnie logowanie",
            }
        )

        # Display the table
        st.dataframe(
            display_df[
                [
                    "ID",
                    "Nazwa użytkownika",
                    "Email",
                    "Status",
                    "Data utworzenia",
                    "Ostatnie logowanie",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

        # User management actions
        st.markdown("### ⚙️ Akcje na użytkownikach")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**🔒 Dezaktywuj użytkownika**")
            user_to_deactivate = st.selectbox(
                "Wybierz użytkownika do dezaktywacji:",
                options=[
                    (row["user_id"], f"{row['username']} ({row['email']})")
                    for _, row in df[df["is_active"] == True].iterrows()
                ],
                format_func=lambda x: x[1] if x else "Brak aktywnych użytkowników",
                key="deactivate_user",
            )

            if st.button("🔒 Dezaktywuj", key="btn_deactivate"):
                if user_to_deactivate:
                    success = deactivate_user(user_to_deactivate[0])
                    if success:
                        st.success(
                            f"✅ Użytkownik {user_to_deactivate[1]} został dezaktywowany"
                        )
                        st.rerun()
                    else:
                        st.error("❌ Nie udało się dezaktywować użytkownika")

        with col2:
            st.markdown("**🔓 Aktywuj użytkownika**")
            user_to_activate = st.selectbox(
                "Wybierz użytkownika do aktywacji:",
                options=[
                    (row["user_id"], f"{row['username']} ({row['email']})")
                    for _, row in df[df["is_active"] == False].iterrows()
                ],
                format_func=lambda x: x[1] if x else "Brak nieaktywnych użytkowników",
                key="activate_user",
            )

            if st.button("🔓 Aktywuj", key="btn_activate"):
                if user_to_activate:
                    success = activate_user(user_to_activate[0])
                    if success:
                        st.success(
                            f"✅ Użytkownik {user_to_activate[1]} został aktywowany"
                        )
                        st.rerun()
                    else:
                        st.error("❌ Nie udało się aktywować użytkownika")

        with col3:
            st.markdown("**🗑️ Usuń użytkownika**")
            current_user = get_current_user()
            users_to_delete = [
                (row["user_id"], f"{row['username']} ({row['email']})")
                for _, row in df.iterrows()
                if row["user_id"] != current_user["user_id"]
            ]  # Don't allow deleting self

            user_to_delete = st.selectbox(
                "Wybierz użytkownika do usunięcia:",
                options=users_to_delete,
                format_func=lambda x: x[1] if x else "Brak użytkowników do usunięcia",
                key="delete_user",
            )

            if st.button("🗑️ Usuń", key="btn_delete", type="secondary"):
                if user_to_delete:
                    if st.button(
                        f"⚠️ Potwierdź usunięcie {user_to_delete[1]}",
                        key="confirm_delete",
                    ):
                        success = delete_user(user_to_delete[0])
                        if success:
                            st.success(
                                f"✅ Użytkownik {user_to_delete[1]} został usunięty"
                            )
                            st.rerun()
                        else:
                            st.error("❌ Nie udało się usunąć użytkownika")

    except Exception as e:
        st.error(f"❌ Błąd podczas pobierania listy użytkowników: {e}")
        logger.error(f"Error getting users list: {e}")


def show_create_user_form():
    """Display form for creating new users"""
    st.subheader("➕ Dodaj Nowego Użytkownika")

    with st.form("create_user_form"):
        col1, col2 = st.columns(2)

        with col1:
            username = st.text_input(
                "Nazwa użytkownika *",
                placeholder="np. jan.kowalski",
                help="Unikalna nazwa użytkownika (tylko litery, cyfry, kropki i podkreślenia)",
            )

            email = st.text_input(
                "Adres email *",
                placeholder="np. jan.kowalski@example.com",
                help="Unikalny adres email użytkownika",
            )

        with col2:
            password = st.text_input(
                "Hasło *",
                type="password",
                placeholder="Minimum 6 znaków",
                help="Bezpieczne hasło dla użytkownika",
            )

            password_confirm = st.text_input(
                "Potwierdź hasło *",
                type="password",
                placeholder="Powtórz hasło",
                help="Powtórz hasło dla potwierdzenia",
            )

        # Quick user templates
        st.markdown("**🎯 Szybkie szablony:**")
        col_temp1, col_temp2, col_temp3 = st.columns(3)

        with col_temp1:
            if st.form_submit_button("👤 Użytkownik testowy", use_container_width=True):
                st.session_state.template_username = "testuser"
                st.session_state.template_email = "test@example.com"
                st.session_state.template_password = "test123"

        with col_temp2:
            if st.form_submit_button("🔧 Administrator", use_container_width=True):
                st.session_state.template_username = "admin2"
                st.session_state.template_email = "admin2@example.com"
                st.session_state.template_password = "admin123"

        with col_temp3:
            if st.form_submit_button("👨‍💼 Manager", use_container_width=True):
                st.session_state.template_username = "manager"
                st.session_state.template_email = "manager@example.com"
                st.session_state.template_password = "manager123"

        # Use template values if set
        if hasattr(st.session_state, "template_username"):
            username = st.session_state.template_username
            email = st.session_state.template_email
            password = st.session_state.template_password
            password_confirm = st.session_state.template_password
            # Clear template
            delattr(st.session_state, "template_username")
            delattr(st.session_state, "template_email")
            delattr(st.session_state, "template_password")

        submitted = st.form_submit_button("➕ Utwórz Użytkownika", type="primary")

        if submitted:
            # Validation
            errors = []

            if not username or not email or not password:
                errors.append("Wszystkie pola są wymagane")

            if password != password_confirm:
                errors.append("Hasła nie są identyczne")

            if len(password) < 6:
                errors.append("Hasło musi mieć minimum 6 znaków")

            if "@" not in email:
                errors.append("Nieprawidłowy format email")

            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                try:
                    success = create_user(username, email, password)
                    if success:
                        st.success(
                            f"✅ Użytkownik {username} został utworzony pomyślnie!"
                        )
                        logger.info(
                            f"User {username} created successfully by {get_current_user()['username']}"
                        )
                        # Clear form
                        st.rerun()
                    else:
                        st.error(
                            "❌ Nie udało się utworzyć użytkownika (prawdopodobnie nazwa lub email już istnieją)"
                        )
                except Exception as e:
                    st.error(f"❌ Błąd podczas tworzenia użytkownika: {e}")
                    logger.error(f"Error creating user: {e}")


def show_change_password_form():
    """Display form for changing user passwords"""
    st.subheader("🔑 Zmień Hasło Użytkownika")

    try:
        users_data = get_all_users()

        if not users_data:
            st.info("📭 Brak użytkowników w systemie")
            return

        with st.form("change_password_form"):
            user_options = [
                (user["user_id"], f"{user['username']} ({user['email']})")
                for user in users_data
                if user["is_active"]
            ]

            selected_user = st.selectbox(
                "Wybierz użytkownika:",
                options=user_options,
                format_func=lambda x: x[1],
                help="Wybierz użytkownika, któremu chcesz zmienić hasło",
            )

            new_password = st.text_input(
                "Nowe hasło",
                type="password",
                placeholder="Minimum 6 znaków",
                help="Nowe bezpieczne hasło",
            )

            confirm_password = st.text_input(
                "Potwierdź nowe hasło",
                type="password",
                placeholder="Powtórz nowe hasło",
            )

            submitted = st.form_submit_button("🔑 Zmień Hasło", type="primary")

            if submitted:
                if not new_password or not confirm_password:
                    st.error("❌ Wszystkie pola są wymagane")
                elif new_password != confirm_password:
                    st.error("❌ Hasła nie są identyczne")
                elif len(new_password) < 6:
                    st.error("❌ Hasło musi mieć minimum 6 znaków")
                else:
                    try:
                        # Get username from selected user
                        selected_username = next(
                            user["username"]
                            for user in users_data
                            if user["user_id"] == selected_user[0]
                        )

                        success = change_password(selected_username, new_password)
                        if success:
                            st.success(
                                f"✅ Hasło dla użytkownika {selected_username} zostało zmienione!"
                            )
                            logger.info(
                                f"Password changed for user {selected_username} by {get_current_user()['username']}"
                            )
                        else:
                            st.error("❌ Nie udało się zmienić hasła")
                    except Exception as e:
                        st.error(f"❌ Błąd podczas zmiany hasła: {e}")
                        logger.error(f"Error changing password: {e}")

    except Exception as e:
        st.error(f"❌ Błąd podczas pobierania listy użytkowników: {e}")


def show_test_authentication():
    """Display authentication testing interface"""
    st.subheader("🧪 Test Uwierzytelniania")

    with st.form("test_auth_form"):
        col1, col2 = st.columns(2)

        with col1:
            test_username = st.text_input(
                "Nazwa użytkownika do testu", placeholder="np. admin"
            )

        with col2:
            test_password = st.text_input(
                "Hasło do testu", type="password", placeholder="Hasło użytkownika"
            )

        submitted = st.form_submit_button("🧪 Testuj Logowanie", type="primary")

        if submitted:
            if not test_username or not test_password:
                st.error("❌ Wprowadź nazwę użytkownika i hasło")
            else:
                with st.spinner("Testowanie logowania..."):
                    try:
                        is_valid, user_data = validate_user_credentials(
                            test_username, test_password
                        )

                        if is_valid and user_data:
                            st.success("✅ Logowanie pomyślne!")

                            # Display user details
                            col1, col2 = st.columns(2)

                            with col1:
                                st.info(f"**👤 Użytkownik:** {user_data['username']}")
                                st.info(f"**📧 Email:** {user_data['email']}")
                                st.info(f"**🆔 ID:** {user_data['user_id']}")

                            with col2:
                                st.info(
                                    f"**📅 Utworzony:** {user_data.get('created_at', 'N/A')}"
                                )
                                st.info(
                                    f"**🕐 Ostatnie logowanie:** {user_data.get('last_login', 'N/A')}"
                                )
                                st.info(
                                    f"**✅ Aktywny:** {'Tak' if user_data.get('is_active') else 'Nie'}"
                                )

                            logger.info(
                                f"Authentication test successful for user {test_username}"
                            )
                        else:
                            st.error(
                                "❌ Logowanie nieudane - nieprawidłowa nazwa użytkownika lub hasło"
                            )
                            logger.warning(
                                f"Authentication test failed for user {test_username}"
                            )

                    except AuthenticationError as e:
                        st.error(f"❌ Błąd uwierzytelniania: {e}")
                    except Exception as e:
                        st.error(f"❌ Wystąpił błąd podczas testowania: {e}")
                        logger.error(f"Authentication test error: {e}")

    # Quick test buttons
    st.markdown("### 🎯 Szybkie testy")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔧 Test Admin", key="test_admin"):
            is_valid, user_data = validate_user_credentials("admin", "admin123")
            if is_valid:
                st.success("✅ Admin test: Sukces")
            else:
                st.error("❌ Admin test: Niepowodzenie")

    with col2:
        if st.button("👤 Test User", key="test_user"):
            is_valid, user_data = validate_user_credentials("testuser", "test123")
            if is_valid:
                st.success("✅ User test: Sukces")
            else:
                st.error("❌ User test: Niepowodzenie")

    with col3:
        if st.button("❌ Test Wrong Password", key="test_wrong"):
            is_valid, user_data = validate_user_credentials("admin", "wrongpassword")
            if not is_valid:
                st.success("✅ Wrong password test: Poprawnie odrzucono")
            else:
                st.error("❌ Wrong password test: BŁĄD BEZPIECZEŃSTWA!")
