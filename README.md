# 10xDevs.pl - Python/Streamlit Banking Application

![](./docs/banner.png)

Warmup repository for [10xDevs.pl](https://10xdevs.pl) - refactored to Python/Streamlit/PostgreSQL

## Stack

- **Language:** Python 3.11+
- **Frontend:** Streamlit
- **Database:** PostgreSQL
- **Migrations:** Yoyo Migrations
- **Testing:** Pytest

## Quick Links

- [Platform szkoleniowa](http://bravecourses.circle.so)

## AI Tooling

- [GitHub Copilot](https://github.com/features/copilot)
- [Cursor](https://www.cursor.com)
- [Windsurf](https://codeium.com/windsurf)
- [Aider](https://aider.chat)
- [Cline](https://cline.bot)

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 14+ running locally or remote
- pip or pipenv for dependency management

## Installation

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure database:**
   - Copy `.env.example` to `.env`
   - Update database credentials in `.env`

3. **Create PostgreSQL database:**
```bash
createdb banking_app
```

4. **Run migrations:**
```bash
yoyo apply --config yoyo.ini
```

## Running the Application

Start the Streamlit application:
```bash
streamlit run app.py
```

The application will be available at http://localhost:8501

## Running Tests

Run all tests with pytest:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=. --cov-report=html
```

## Project Structure

```
├── app.py                    # Main Streamlit application
├── banking/                  # Banking domain logic
│   ├── banking.py           # Core business logic
│   ├── types.py             # Type definitions
│   └── test_banking.py      # Domain tests
├── db/                       # Database layer
│   ├── connection.py        # PostgreSQL connection
│   ├── models.py            # Data models
│   └── crud.py              # CRUD operations
├── migrations/               # Yoyo migration scripts
│   ├── 0001_initial_schema.py
│   └── 0002_sample_data.py
├── .streamlit/              # Streamlit configuration
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Project metadata
└── yoyo.ini                # Migration configuration
```

## Exercises

Test AI-assisted development with these tasks:

1. **Banking System Implementation** - Implement banking operations based on specs and tests
2. **Test Analysis** - Analyze test coverage against specifications
3. **Mermaid Diagrams** - Generate diagrams from `/charts/request.md`
4. **Custom AI Behavior** - Modify AI behavior with custom rules

## Database Management

### Migration Commands

```bash
# Apply all pending migrations
yoyo apply

# Rollback last migration
yoyo rollback

# Check migration status
yoyo list

# Create new migration
yoyo new -m "Description of changes"
```

### Database Schema

**Accounts Table:**
- `id` - Primary key
- `account_number` - Unique account identifier
- `owner_name` - Account owner name
- `balance` - Account balance
- `currency` - Currency code (USD, EUR, etc.)
- `created_at`, `updated_at` - Timestamps

**Transactions Table:**
- `id` - Primary key
- `account_id` - Foreign key to accounts
- `transaction_type` - Type: deposit, withdrawal, transfer
- `amount` - Transaction amount
- `description` - Optional description
- `created_at` - Timestamp

## Features

- ✅ Account creation with validation
- ✅ Withdrawal processing with business rules
- ✅ Transaction history tracking
- ✅ Real-time balance updates
- ✅ Multi-currency support
- ✅ PostgreSQL persistence
- ✅ Streamlit interactive UI

## Development

### Code Quality

Format code with Black:
```bash
black .
```

Lint with Flake8:
```bash
flake8 .
```

Type check with MyPy:
```bash
mypy .
```

## License

ISC
