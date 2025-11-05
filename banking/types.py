"""Type definitions for the banking domain."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal


@dataclass
class AccountOwner:
    """Bank account owner information."""

    id: str
    first_name: str
    last_name: str


@dataclass
class BankAccount:
    """Bank account representation."""

    id: str
    balance: Decimal
    currency: str
    owner: AccountOwner


@dataclass
class WithdrawalRequest:
    """Withdrawal request data."""

    account_id: str
    amount: Decimal
    currency: str
    timestamp: datetime


@dataclass
class Transaction:
    """Transaction details."""

    id: str
    amount: Decimal
    currency: str
    timestamp: datetime
    remaining_balance: Decimal


@dataclass
class WithdrawalResult:
    """Result of a successful withdrawal."""

    success: bool
    message: Optional[str] = None
    transaction: Optional[Transaction] = None


@dataclass
class WithdrawalError:
    """Error during withdrawal processing."""

    code: Literal["INSUFFICIENT_FUNDS", "INVALID_AMOUNT", "ACCOUNT_NOT_FOUND"]
    message: str
