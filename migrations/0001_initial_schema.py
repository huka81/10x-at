"""
Initial database schema for banking application.

Create accounts and transactions tables.
"""

from yoyo import step

__depends__ = {}

steps = [
    step(
        # Apply
        """
        CREATE TABLE IF NOT EXISTS accounts (
            id SERIAL PRIMARY KEY,
            account_number VARCHAR(50) UNIQUE NOT NULL,
            owner_name VARCHAR(255) NOT NULL,
            balance NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
            currency VARCHAR(3) NOT NULL DEFAULT 'USD',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX idx_accounts_account_number ON accounts(account_number);
        CREATE INDEX idx_accounts_owner_name ON accounts(owner_name);
        """,
        # Rollback
        """
        DROP TABLE IF EXISTS accounts CASCADE;
        """,
    ),
    step(
        # Apply
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
            transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('deposit', 'withdrawal', 'transfer')),
            amount NUMERIC(15, 2) NOT NULL,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX idx_transactions_account_id ON transactions(account_id);
        CREATE INDEX idx_transactions_created_at ON transactions(created_at);
        CREATE INDEX idx_transactions_type ON transactions(transaction_type);
        """,
        # Rollback
        """
        DROP TABLE IF EXISTS transactions CASCADE;
        """,
    ),
]
