"""CRUD operations for the banking application."""
from typing import List, Optional
from decimal import Decimal
from psycopg2.extras import RealDictCursor
from db.connection import get_db_connection
from db.models import Account, Transaction


class AccountCRUD:
    """CRUD operations for bank accounts."""

    @staticmethod
    def create(account: Account) -> Account:
        """
        Create a new account in the database.

        Args:
            account: Account object to create.

        Returns:
            Account: Created account with generated ID.

        Raises:
            psycopg2.Error: If database operation fails.
        """
        db = get_db_connection()
        conn = db.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO accounts (account_number, owner_name, balance, currency)
                VALUES (%s, %s, %s, %s)
                RETURNING id, created_at, updated_at
                """,
                (account.account_number, account.owner_name, account.balance, account.currency),
            )
            result = cursor.fetchone()
            conn.commit()

            account.id = result["id"]
            account.created_at = result["created_at"]
            account.updated_at = result["updated_at"]

            return account
        finally:
            cursor.close()

    @staticmethod
    def get_by_id(account_id: int) -> Optional[Account]:
        """
        Retrieve an account by ID.

        Args:
            account_id: The account ID.

        Returns:
            Account or None if not found.
        """
        db = get_db_connection()
        conn = db.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, account_number, owner_name, balance, currency, created_at, updated_at
                FROM accounts
                WHERE id = %s
                """,
                (account_id,),
            )
            row = cursor.fetchone()

            if row:
                return Account(
                    id=row["id"],
                    account_number=row["account_number"],
                    owner_name=row["owner_name"],
                    balance=Decimal(str(row["balance"])),
                    currency=row["currency"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            return None
        finally:
            cursor.close()

    @staticmethod
    def get_by_account_number(account_number: str) -> Optional[Account]:
        """
        Retrieve an account by account number.

        Args:
            account_number: The account number.

        Returns:
            Account or None if not found.
        """
        db = get_db_connection()
        conn = db.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, account_number, owner_name, balance, currency, created_at, updated_at
                FROM accounts
                WHERE account_number = %s
                """,
                (account_number,),
            )
            row = cursor.fetchone()

            if row:
                return Account(
                    id=row["id"],
                    account_number=row["account_number"],
                    owner_name=row["owner_name"],
                    balance=Decimal(str(row["balance"])),
                    currency=row["currency"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            return None
        finally:
            cursor.close()

    @staticmethod
    def get_all() -> List[Account]:
        """
        Retrieve all accounts.

        Returns:
            List of all accounts.
        """
        db = get_db_connection()
        conn = db.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, account_number, owner_name, balance, currency, created_at, updated_at
                FROM accounts
                ORDER BY created_at DESC
                """
            )
            rows = cursor.fetchall()

            return [
                Account(
                    id=row["id"],
                    account_number=row["account_number"],
                    owner_name=row["owner_name"],
                    balance=Decimal(str(row["balance"])),
                    currency=row["currency"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]
        finally:
            cursor.close()

    @staticmethod
    def update(account: Account) -> Account:
        """
        Update an existing account.

        Args:
            account: Account object with updated values.

        Returns:
            Updated account.

        Raises:
            ValueError: If account ID is None.
            psycopg2.Error: If database operation fails.
        """
        if account.id is None:
            raise ValueError("Account ID is required for update")

        db = get_db_connection()
        conn = db.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE accounts
                SET account_number = %s, owner_name = %s, balance = %s, currency = %s, updated_at = NOW()
                WHERE id = %s
                RETURNING updated_at
                """,
                (
                    account.account_number,
                    account.owner_name,
                    account.balance,
                    account.currency,
                    account.id,
                ),
            )
            result = cursor.fetchone()
            conn.commit()

            account.updated_at = result["updated_at"]
            return account
        finally:
            cursor.close()

    @staticmethod
    def delete(account_id: int) -> bool:
        """
        Delete an account by ID.

        Args:
            account_id: The account ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        db = get_db_connection()
        conn = db.connect()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM accounts WHERE id = %s", (account_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()


class TransactionCRUD:
    """CRUD operations for transactions."""

    @staticmethod
    def create(transaction: Transaction) -> Transaction:
        """
        Create a new transaction.

        Args:
            transaction: Transaction object to create.

        Returns:
            Created transaction with generated ID.
        """
        db = get_db_connection()
        conn = db.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO transactions (account_id, transaction_type, amount, description)
                VALUES (%s, %s, %s, %s)
                RETURNING id, created_at
                """,
                (
                    transaction.account_id,
                    transaction.transaction_type,
                    transaction.amount,
                    transaction.description,
                ),
            )
            result = cursor.fetchone()
            conn.commit()

            transaction.id = result["id"]
            transaction.created_at = result["created_at"]

            return transaction
        finally:
            cursor.close()

    @staticmethod
    def get_by_account(account_id: int, limit: int = 100) -> List[Transaction]:
        """
        Retrieve transactions for an account.

        Args:
            account_id: The account ID.
            limit: Maximum number of transactions to retrieve.

        Returns:
            List of transactions.
        """
        db = get_db_connection()
        conn = db.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, account_id, transaction_type, amount, description, created_at
                FROM transactions
                WHERE account_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (account_id, limit),
            )
            rows = cursor.fetchall()

            return [
                Transaction(
                    id=row["id"],
                    account_id=row["account_id"],
                    transaction_type=row["transaction_type"],
                    amount=Decimal(str(row["amount"])),
                    description=row["description"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]
        finally:
            cursor.close()

    @staticmethod
    def get_all(limit: int = 100) -> List[Transaction]:
        """
        Retrieve all transactions.

        Args:
            limit: Maximum number of transactions to retrieve.

        Returns:
            List of transactions.
        """
        db = get_db_connection()
        conn = db.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, account_id, transaction_type, amount, description, created_at
                FROM transactions
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cursor.fetchall()

            return [
                Transaction(
                    id=row["id"],
                    account_id=row["account_id"],
                    transaction_type=row["transaction_type"],
                    amount=Decimal(str(row["amount"])),
                    description=row["description"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]
        finally:
            cursor.close()
