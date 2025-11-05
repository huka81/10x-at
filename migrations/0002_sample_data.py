"""
Add sample data for testing.

Insert sample accounts and transactions.
"""

from yoyo import step

__depends__ = {"0001_initial_schema"}

steps = [
    step(
        # Apply
        """
        INSERT INTO accounts (account_number, owner_name, balance, currency) VALUES
            ('ACC001', 'John Doe', 1000.00, 'USD'),
            ('ACC002', 'Jane Smith', 2500.50, 'USD'),
            ('ACC003', 'Bob Johnson', 500.00, 'EUR');
        """,
        # Rollback
        """
        DELETE FROM accounts WHERE account_number IN ('ACC001', 'ACC002', 'ACC003');
        """,
    ),
]
