# Repository Guidelines

## Project Structure & Module Organization
This is a Python-based banking application with Streamlit frontend and PostgreSQL backend. The codebase centers on:

- `banking/` - Domain logic with `banking.py` implementing business rules, `types.py` defining domain models, and `test_banking.py` providing pytest coverage. The `banking-spec.md` documents functional requirements.
- `db/` - Database layer with `connection.py` for PostgreSQL connections, `models.py` for data entities, and `crud.py` for database operations.
- `migrations/` - Yoyo migration scripts for database schema management.
- `app.py` - Main Streamlit application entry point.
- `prompts/` - Prompt experiments (English and Polish variants).
- `charts/` - Mermaid diagram specifications.
- `docs/` - Static documentation assets.

Root-level configs (`pyproject.toml`, `requirements.txt`, `yoyo.ini`) drive tooling.

## Build, Test, and Development Commands
Install dependencies with `pip install -r requirements.txt`. Configure database by copying `.env.example` to `.env` and updating credentials. Run migrations with `yoyo apply --config yoyo.ini`. 

Execute tests using `pytest` or `pytest --cov=.` for coverage reports. When developing, keep tests running via `pytest --watch` or `ptw` to catch regressions early.

Start the application with `streamlit run app.py`.

## Coding Style & Naming Conventions
Write Python 3.11+ code with strict type hints (mypy-compatible). Avoid `Any` types where possible. Format with Black (100-char line length). Use `snake_case` for functions/variables and `PascalCase` for classes. Prefer dataclasses and immutable structures. Keep domain logic in `banking/`, database operations in `db/`, and UI in `app.py` or `pages/`.

Follow PEP 8 standards with 4-space indentation. Use type hints consistently:
```python
def process_withdrawal(account: BankAccount, request: WithdrawalRequest) -> Union[WithdrawalResult, WithdrawalError]:
    ...
```

## Testing Guidelines
Pytest is the testing framework. Mirror the class-based structure from `banking/test_banking.py`, using descriptive class names like `TestAccountCreation` and test methods prefixed with `test_should_*`. Place test files as `test_*.py` beside the code they verify.

Cover both happy paths and error conditions (e.g., `INVALID_AMOUNT`, `ACCOUNT_NOT_FOUND`, `INSUFFICIENT_FUNDS`). Use fixtures for reusable test data. When adding features, update `banking-spec.md` and ensure tests assert both behavior and error messages explicitly.

## Database Guidelines
Use Yoyo migrations for all schema changes. Never modify the database schema directly. Create migrations with `yoyo new -m "description"`. Each migration should include both apply and rollback steps.

Follow these patterns:
- Use `Decimal` for currency amounts
- Include proper foreign keys and indexes
- Add timestamps (`created_at`, `updated_at`) to all tables
- Use enums for fixed value sets (e.g., transaction types)

## Commit & Pull Request Guidelines
Follow Conventional Commits (e.g., `feat: add withdrawal validation`, `fix: handle currency mismatch`, `chore: update dependencies`). Scope commits tightly and include test cases when fixing bugs.

PRs should:
- Link to tracked tasks
- Summarize behavioral changes
- Include pytest output showing passing tests
- Update relevant documentation
- Request review when changing shared abstractions or database schema
