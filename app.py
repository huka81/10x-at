"""
Streamlit Banking Application

Main application file for the banking system frontend.
"""
import streamlit as st
from decimal import Decimal
from datetime import datetime

from banking import create_account, process_withdrawal, BankAccount, AccountOwner, WithdrawalRequest
from db import AccountCRUD, TransactionCRUD, Account, Transaction as DBTransaction

# Page configuration
st.set_page_config(
    page_title="Banking Application",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
    """Main application entry point."""
    st.title("🏦 Banking Application")
    st.markdown("---")

    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Dashboard", "Accounts", "Transactions", "New Account", "Make Withdrawal"],
    )

    if page == "Dashboard":
        show_dashboard()
    elif page == "Accounts":
        show_accounts()
    elif page == "Transactions":
        show_transactions()
    elif page == "New Account":
        show_new_account()
    elif page == "Make Withdrawal":
        show_withdrawal()


def show_dashboard() -> None:
    """Display the dashboard page."""
    st.header("📊 Dashboard")

    col1, col2, col3 = st.columns(3)

    try:
        accounts = AccountCRUD.get_all()

        with col1:
            st.metric("Total Accounts", len(accounts))

        with col2:
            total_balance = sum(acc.balance for acc in accounts)
            st.metric("Total Balance", f"${total_balance:,.2f}")

        with col3:
            transactions = TransactionCRUD.get_all(limit=1000)
            st.metric("Total Transactions", len(transactions))

        # Recent activity
        st.subheader("Recent Accounts")
        if accounts:
            for acc in accounts[:5]:
                with st.expander(f"Account {acc.account_number} - {acc.owner_name}"):
                    st.write(f"**Balance:** ${acc.balance:,.2f} {acc.currency}")
                    st.write(f"**Created:** {acc.created_at}")
        else:
            st.info("No accounts found. Create a new account to get started.")

    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")
        st.info("Make sure PostgreSQL is running and migrations are applied.")


def show_accounts() -> None:
    """Display all accounts."""
    st.header("👥 All Accounts")

    try:
        accounts = AccountCRUD.get_all()

        if accounts:
            for acc in accounts:
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.subheader(f"{acc.owner_name}")
                    st.text(f"Account: {acc.account_number}")

                with col2:
                    st.metric("Balance", f"${acc.balance:,.2f}")
                    st.text(f"Currency: {acc.currency}")

                with col3:
                    if st.button(f"View Transactions", key=f"view_{acc.id}"):
                        st.session_state.selected_account = acc.id

                st.markdown("---")
        else:
            st.info("No accounts found.")

    except Exception as e:
        st.error(f"Error loading accounts: {str(e)}")


def show_transactions() -> None:
    """Display all transactions."""
    st.header("💸 Transactions")

    try:
        account_id = st.number_input("Filter by Account ID (optional)", min_value=0, value=0)

        if account_id > 0:
            transactions = TransactionCRUD.get_by_account(account_id)
        else:
            transactions = TransactionCRUD.get_all()

        if transactions:
            for txn in transactions:
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.text(f"Account ID: {txn.account_id}")
                    st.text(f"Type: {txn.transaction_type.upper()}")

                with col2:
                    st.metric("Amount", f"${txn.amount:,.2f}")

                with col3:
                    st.text(f"{txn.created_at}")

                if txn.description:
                    st.text(f"Description: {txn.description}")

                st.markdown("---")
        else:
            st.info("No transactions found.")

    except Exception as e:
        st.error(f"Error loading transactions: {str(e)}")


def show_new_account() -> None:
    """Display form to create a new account."""
    st.header("➕ Create New Account")

    with st.form("new_account_form"):
        account_number = st.text_input("Account Number", placeholder="e.g., ACC001")
        owner_name = st.text_input("Owner Name", placeholder="e.g., John Doe")
        balance = st.number_input("Initial Balance", min_value=0.01, value=1000.00, step=0.01)
        currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "PLN"])

        submitted = st.form_submit_button("Create Account")

        if submitted:
            if not account_number or not owner_name:
                st.error("Account number and owner name are required.")
            else:
                try:
                    # Create account in database
                    new_account = Account(
                        id=None,
                        account_number=account_number,
                        owner_name=owner_name,
                        balance=Decimal(str(balance)),
                        currency=currency,
                        created_at=None,
                        updated_at=None,
                    )

                    created = AccountCRUD.create(new_account)
                    st.success(f"✅ Account created successfully! ID: {created.id}")
                    st.balloons()

                except Exception as e:
                    st.error(f"Error creating account: {str(e)}")


def show_withdrawal() -> None:
    """Display form to make a withdrawal."""
    st.header("💰 Make Withdrawal")

    try:
        accounts = AccountCRUD.get_all()

        if not accounts:
            st.warning("No accounts available. Please create an account first.")
            return

        account_options = {
            f"{acc.account_number} - {acc.owner_name} (${acc.balance})": acc
            for acc in accounts
        }

        selected = st.selectbox("Select Account", list(account_options.keys()))

        if selected:
            account = account_options[selected]

            with st.form("withdrawal_form"):
                st.info(f"Current Balance: ${account.balance:,.2f} {account.currency}")

                amount = st.number_input(
                    "Withdrawal Amount", min_value=0.01, value=100.00, step=0.01
                )

                description = st.text_area("Description (optional)")

                submitted = st.form_submit_button("Process Withdrawal")

                if submitted:
                    try:
                        # Validate using banking logic
                        bank_account = BankAccount(
                            id=str(account.id),
                            balance=account.balance,
                            currency=account.currency,
                            owner=AccountOwner(
                                id=str(account.id),
                                first_name=account.owner_name.split()[0],
                                last_name=" ".join(account.owner_name.split()[1:]),
                            ),
                        )

                        withdrawal_request = WithdrawalRequest(
                            account_id=str(account.id),
                            amount=Decimal(str(amount)),
                            currency=account.currency,
                            timestamp=datetime.now(),
                        )

                        result = process_withdrawal(bank_account, withdrawal_request)

                        if hasattr(result, "success") and result.success:
                            # Update account balance
                            account.balance = bank_account.balance
                            AccountCRUD.update(account)

                            # Create transaction record
                            transaction = DBTransaction(
                                id=None,
                                account_id=account.id,
                                transaction_type="withdrawal",
                                amount=Decimal(str(amount)),
                                description=description or "Withdrawal",
                                created_at=None,
                            )
                            TransactionCRUD.create(transaction)

                            st.success(f"✅ Withdrawal processed successfully!")
                            st.info(f"New Balance: ${bank_account.balance:,.2f}")
                        else:
                            st.error(f"❌ Withdrawal failed: {result.message}")

                    except Exception as e:
                        st.error(f"Error processing withdrawal: {str(e)}")

    except Exception as e:
        st.error(f"Error loading accounts: {str(e)}")


if __name__ == "__main__":
    main()
