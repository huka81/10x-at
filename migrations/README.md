# Database Migrations

This directory contains Yoyo database migrations for the banking application.

## Usage

### Apply all migrations
```bash
yoyo apply
```

### Apply migrations with specific config
```bash
yoyo apply --config yoyo.ini
```

### Rollback last migration
```bash
yoyo rollback
```

### Check migration status
```bash
yoyo list
```

## Migration Files

Migrations are numbered sequentially:
- `0001_initial_schema.py` - Creates accounts and transactions tables
- `0002_sample_data.py` - Inserts sample data for testing

## Creating New Migrations

Create a new migration file:
```bash
yoyo new -m "Description of migration"
```

Or manually create a file following the pattern: `XXXX_description.py`

Each migration should:
1. Have a unique sequential number
2. Define `__depends__` to specify dependencies
3. Use `step()` with both apply and rollback SQL
