import os
import sys

UI_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(UI_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
from ui.instrument_view import show_instrument_management_view, show_instrument_view
from ui.auth import (
    check_authentication,
    show_login_page,
    show_user_info,
    get_current_user,
)

# Configure page
st.set_page_config(
    page_title="AIVestor System",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_data" not in st.session_state:
    st.session_state.user_data = None

# Check authentication
if not check_authentication():
    show_login_page()
else:
    # User is authenticated, show main app
    PAGES = {
        "📊 Przegląd instrumentów": {
            "function": show_instrument_management_view,
            "description": "Zarządzaj portfelem instrumentów",
            "icon": "📊",
        },
    }

    # Sidebar with modern design
    with st.sidebar:
        # Modern header with branding
        st.markdown(
            """
        <div style="
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            text-align: center;
            color: white;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        ">
            <h2 style="margin: 0; font-size: 24px;">📈 AIVestor</h2>
            <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 14px;">Autonomous Trading System</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Show user information with modern styling
        show_user_info()

        # Modern navigation menu
        st.markdown(
            """
        <div style="
            background: rgba(255, 255, 255, 0.05);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        ">
            <h3 style="
                margin: 0 0 15px 0;
                color: #333;
                font-size: 18px;
                display: flex;
                align-items: center;
            ">
                🧭 Nawigacja
            </h3>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Create modern menu buttons
        selected_page = None

        for page_name, page_info in PAGES.items():
            # Create custom styled button
            button_style = f"""
                <style>
                .nav-button {{
                    width: 100%;
                    padding: 12px 16px;
                    margin: 8px 0;
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    display: flex;
                    align-items: center;
                    text-decoration: none;
                    color: #333;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                }}
                .nav-button:hover {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
                }}
                .nav-button.active {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
                }}
                .nav-icon {{
                    margin-right: 10px;
                    font-size: 18px;
                }}
                .nav-text {{
                    flex-grow: 1;
                    font-weight: 500;
                }}
                .nav-desc {{
                    font-size: 11px;
                    opacity: 0.8;
                    margin-top: 2px;
                }}
                </style>
            """

            # Use button with callback
            if st.button(
                f"{page_info['icon']} {page_name.split(' ', 1)[1]}",
                key=f"nav_{page_name}",
                help=page_info["description"],
                use_container_width=True,
            ):
                selected_page = page_name
                st.session_state.current_page = page_name

        # Remember last selected page
        if "current_page" not in st.session_state:
            st.session_state.current_page = "📊 Przegląd instrumentów"

        if selected_page is None:
            selected_page = st.session_state.current_page
        else:
            st.session_state.current_page = selected_page

        # Quick stats section
        st.markdown("---")
        st.markdown(
            """
        <div style="
            background: rgba(255, 255, 255, 0.05);
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
        ">
            <h4 style="margin: 0 0 10px 0; color: #333;">📈 Quick Stats</h4>
            <div style="display: flex; justify-content: space-between; font-size: 12px; color: #666;">
                <span>Version: 2.0</span>
                <span>Status: ✅ Online</span>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Optional: Show current user ID for debugging (smaller and less prominent)
        user_data = get_current_user()
        if user_data:
            st.markdown(
                f"<div style='text-align: center; margin-top: 10px;'>"
                f"<small style='color: #999; font-size: 10px;'>User ID: {user_data['user_id']}</small>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # Main content area with modern styling
    # Add breadcrumb navigation
    st.markdown(
        f"""
    <div style="
        background: rgba(255, 255, 255, 0.8);
        padding: 10px 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        border-left: 4px solid #667eea;
    ">
        <div style="display: flex; align-items: center; color: #333;">
            <span style="margin-right: 10px;">🏠 Home</span>
            <span style="margin-right: 10px;">→</span>
            <span style="font-weight: 500;">{selected_page}</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    try:
        # Pass user context to pages if needed
        if selected_page in PAGES:
            # Add loading state
            with st.spinner(f"Ładowanie {selected_page}..."):
                PAGES[selected_page]["function"]()
        else:
            st.error("🚫 Nie znaleziono wybranej strony.")
    except Exception as e:
        st.error(f"❌ Błąd podczas ładowania strony: {e}")

        # Modern error display
        with st.expander("🔍 Szczegóły błędu", expanded=False):
            st.exception(e)

        # Error recovery options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Odśwież stronę", type="primary"):
                st.rerun()
        with col2:
            if st.button("🏠 Powrót do instrumentów"):
                st.session_state.current_page = list(PAGES.keys())[0]
                st.rerun()
