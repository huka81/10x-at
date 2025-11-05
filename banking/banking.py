"""Banking operations implementation."""
from decimal import Decimal
from datetime import datetime
import uuid
from typing import Union

from banking.types import (
    BankAccount,
    WithdrawalRequest,
    WithdrawalResult,
    WithdrawalError,
    Transaction,
)


def create_account(account: BankAccount) -> Union[BankAccount, WithdrawalError]:
    """
    Create a new bank account with validation.

    Args:
        account: BankAccount object to create.

    Returns:
        BankAccount if valid, WithdrawalError if validation fails.
    """
    # Validate balance is not negative
    if account.balance < 0:
        return WithdrawalError(
            code="INVALID_AMOUNT", message="Account balance cannot be negative"
        )

    # Validate balance is positive (not zero)
    if account.balance == 0:
        return WithdrawalError(
            code="INVALID_AMOUNT", message="Initial account balance must be positive"
        )

    return account


def process_withdrawal(
    account: BankAccount, withdrawal: WithdrawalRequest
) -> Union[WithdrawalResult, WithdrawalError]:
    """
    Process a withdrawal request.

    Args:
        account: The bank account to withdraw from.
        withdrawal: The withdrawal request details.

    Returns:
        WithdrawalResult if successful, WithdrawalError if validation fails.
    """
    # Validate account ID matches
    if account.id != withdrawal.account_id:
        return WithdrawalError(
            code="ACCOUNT_NOT_FOUND", message="Account ID does not match withdrawal request"
        )

    # Validate amount is positive
    if withdrawal.amount <= 0:
        return WithdrawalError(
            code="INVALID_AMOUNT", message="Withdrawal amount must be positive"
        )

    # Validate currency matches
    if account.currency != withdrawal.currency:
        return WithdrawalError(
            code="INVALID_AMOUNT",
            message=f"Currency mismatch: account is {account.currency}, withdrawal is {withdrawal.currency}",
        )

    # Validate sufficient funds
    if withdrawal.amount > account.balance:
        return WithdrawalError(
            code="INSUFFICIENT_FUNDS",
            message=f"Insufficient funds: balance {account.balance}, withdrawal {withdrawal.amount}",
        )

    # Process withdrawal
    new_balance = account.balance - withdrawal.amount
    transaction = Transaction(
        id=str(uuid.uuid4()),
        amount=withdrawal.amount,
        currency=withdrawal.currency,
        timestamp=withdrawal.timestamp,
        remaining_balance=new_balance,
    )

    # Update account balance
    account.balance = new_balance

    return WithdrawalResult(
        success=True,
        message="Withdrawal processed successfully",
        transaction=transaction,
    )
