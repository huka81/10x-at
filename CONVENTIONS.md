# Coding Conventions

## Python Style Guide

- Use Python 3.11+ with type hints enabled
- Follow PEP 8 style guide
- Use Black formatter (100-char line length)
- Prefer `const` assignment patterns where applicable
- Avoid `Any` type - use specific types or `Union` types
- Use `snake_case` for functions and variables
- Use `PascalCase` for classes
- Use dataclasses for data structures
- Use `Decimal` for currency amounts, never `float`
- Always include docstrings for public functions and classes

## Type Hints

```python
from typing import Union, Optional, List
from decimal import Decimal

def process_withdrawal(
    account: BankAccount, 
    request: WithdrawalRequest
) -> Union[WithdrawalResult, WithdrawalError]:
    """Process a withdrawal request."""
    pass
```

## Testing

- Use pytest for all tests
- Use descriptive test names: `test_should_reject_negative_balance`
- Organize tests in classes: `TestAccountCreation`, `TestWithdrawalProcessing`
- Use fixtures for shared test data
- Aim for >80% code coverage

## Database

- Use Yoyo migrations for schema changes
- Always use `Decimal` for currency amounts
- Include proper indexes on frequently queried columns
- Add timestamps to all tables
- Use foreign keys with proper constraints

## Code Organization

- Domain logic in `banking/`
- Database layer in `db/`
- UI components in `app.py` and `pages/`
- Migrations in `migrations/`
- Keep modules focused and single-purpose
