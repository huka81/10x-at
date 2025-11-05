"""Data models for the banking application."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Account:
    """Bank account model."""

    id: Optional[int]
    account_number: str
    owner_name: str
    balance: Decimal
    currency: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    def to_dict(self) -> dict:
        """Convert account to dictionary."""
        return {
            "id": self.id,
            "account_number": self.account_number,
            "owner_name": self.owner_name,
            "balance": float(self.balance),
            "currency": self.currency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class Transaction:
    """Transaction model."""

    id: Optional[int]
    account_id: int
    transaction_type: str  # 'deposit', 'withdrawal', 'transfer'
    amount: Decimal
    description: Optional[str]
    created_at: Optional[datetime]

    def to_dict(self) -> dict:
        """Convert transaction to dictionary."""
        return {
            "id": self.id,
            "account_id": self.account_id,
            "transaction_type": self.transaction_type,
            "amount": float(self.amount),
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
