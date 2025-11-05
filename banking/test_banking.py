"""Tests for banking operations."""
import pytest
from decimal import Decimal
from datetime import datetime

from banking.banking import create_account, process_withdrawal
from banking.types import BankAccount, WithdrawalRequest, AccountOwner, WithdrawalError


class TestAccountCreation:
    """Tests for account creation."""

    def test_should_create_valid_bank_account(self) -> None:
        """Test creating a valid bank account."""
        account = BankAccount(
            id="acc123",
            balance=Decimal("1000"),
            currency="USD",
            owner=AccountOwner(id="own123", first_name="John", last_name="Doe"),
        )

        result = create_account(account)
        assert result == account

    def test_should_reject_account_creation_with_negative_balance(self) -> None:
        """Test rejecting account with negative balance."""
        account = BankAccount(
            id="acc123",
            balance=Decimal("-100"),
            currency="USD",
            owner=AccountOwner(id="own123", first_name="John", last_name="Doe"),
        )

        result = create_account(account)
        assert isinstance(result, WithdrawalError)
        assert result.code == "INVALID_AMOUNT"
        assert result.message == "Account balance cannot be negative"

    def test_should_reject_account_creation_with_zero_balance(self) -> None:
        """Test rejecting account with zero balance."""
        account = BankAccount(
            id="acc123",
            balance=Decimal("0"),
            currency="USD",
            owner=AccountOwner(id="own123", first_name="John", last_name="Doe"),
        )

        result = create_account(account)
        assert isinstance(result, WithdrawalError)
        assert result.code == "INVALID_AMOUNT"
        assert result.message == "Initial account balance must be positive"


class TestWithdrawalProcessing:
    """Tests for withdrawal processing."""

    @pytest.fixture
    def account(self) -> BankAccount:
        """Create a test account."""
        return BankAccount(
            id="acc123",
            balance=Decimal("1000"),
            currency="USD",
            owner=AccountOwner(id="own123", first_name="John", last_name="Doe"),
        )

    def test_should_process_valid_withdrawal(self, account: BankAccount) -> None:
        """Test processing a valid withdrawal."""
        withdrawal = WithdrawalRequest(
            account_id="acc123",
            amount=Decimal("500"),
            currency="USD",
            timestamp=datetime.now(),
        )

        result = process_withdrawal(account, withdrawal)
        assert hasattr(result, "success")
        assert result.success is True
        assert result.transaction is not None
        assert result.transaction.remaining_balance == Decimal("500")

    def test_should_reject_withdrawal_with_insufficient_funds(
        self, account: BankAccount
    ) -> None:
        """Test rejecting withdrawal with insufficient funds."""
        withdrawal = WithdrawalRequest(
            account_id="acc123",
            amount=Decimal("1500"),
            currency="USD",
            timestamp=datetime.now(),
        )

        result = process_withdrawal(account, withdrawal)
        assert isinstance(result, WithdrawalError)
        assert result.code == "INSUFFICIENT_FUNDS"

    def test_should_reject_withdrawal_with_invalid_amount(
        self, account: BankAccount
    ) -> None:
        """Test rejecting withdrawal with invalid amount."""
        withdrawal = WithdrawalRequest(
            account_id="acc123",
            amount=Decimal("-100"),
            currency="USD",
            timestamp=datetime.now(),
        )

        result = process_withdrawal(account, withdrawal)
        assert isinstance(result, WithdrawalError)
        assert result.code == "INVALID_AMOUNT"

    def test_should_reject_withdrawal_with_zero_amount(self, account: BankAccount) -> None:
        """Test rejecting withdrawal with zero amount."""
        withdrawal = WithdrawalRequest(
            account_id="acc123",
            amount=Decimal("0"),
            currency="USD",
            timestamp=datetime.now(),
        )

        result = process_withdrawal(account, withdrawal)
        assert isinstance(result, WithdrawalError)
        assert result.code == "INVALID_AMOUNT"

    def test_should_reject_withdrawal_with_currency_mismatch(
        self, account: BankAccount
    ) -> None:
        """Test rejecting withdrawal with currency mismatch."""
        withdrawal = WithdrawalRequest(
            account_id="acc123",
            amount=Decimal("500"),
            currency="EUR",
            timestamp=datetime.now(),
        )

        result = process_withdrawal(account, withdrawal)
        assert isinstance(result, WithdrawalError)
        assert result.code == "INVALID_AMOUNT"

    def test_should_reject_withdrawal_with_invalid_account_id(
        self, account: BankAccount
    ) -> None:
        """Test rejecting withdrawal with invalid account ID."""
        withdrawal = WithdrawalRequest(
            account_id="wrong_id",
            amount=Decimal("500"),
            currency="USD",
            timestamp=datetime.now(),
        )

        result = process_withdrawal(account, withdrawal)
        assert isinstance(result, WithdrawalError)
        assert result.code == "ACCOUNT_NOT_FOUND"
