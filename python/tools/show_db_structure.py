#!/usr/bin/env python3
"""
Standalone script to connect to the database and display all schemas and tables.

Usage:
    python python/tools/show_db_structure.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "python"))

from sqlalchemy import text
from database import get_db_engine
from tools.logger import get_logger

logger = get_logger(__name__)


def show_database_structure():
    """Display all schemas and their tables from the database."""
    try:
        engine = get_db_engine()
        logger.info("Connected to database successfully")
        
        with engine.connect() as connection:
            # Get all user-defined schemas
            logger.info("Fetching schemas...")
            schema_result = connection.execute(
                text("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                    ORDER BY schema_name
                """)
            )
            schemas = [row[0] for row in schema_result]
            
            if not schemas:
                print("\n❌ No user-defined schemas found in the database")
                return
            
            print(f"\n{'='*80}")
            print(f"DATABASE STRUCTURE")
            print(f"{'='*80}")
            print(f"\nFound {len(schemas)} schema(s):\n")
            
            total_tables = 0
            
            # For each schema, get its tables
            for schema in schemas:
                # Get tables in this schema
                table_result = connection.execute(
                    text("""
                        SELECT table_name, table_type
                        FROM information_schema.tables 
                        WHERE table_schema = :schema 
                        ORDER BY table_name
                    """),
                    {"schema": schema}
                )
                tables = [(row[0], row[1]) for row in table_result]
                
                print(f"📁 Schema: {schema}")
                print(f"   Tables: {len(tables)}")
                
                if tables:
                    print(f"   {'─'*70}")
                    for table_name, table_type in tables:
                        type_icon = "📋" if table_type == "BASE TABLE" else "👁️"
                        print(f"   {type_icon} {table_name} ({table_type})")
                        total_tables += 1
                else:
                    print(f"   ⚠️  No tables found")
                
                print()
            
            print(f"{'='*80}")
            print(f"SUMMARY: {len(schemas)} schema(s), {total_tables} table(s)")
            print(f"{'='*80}\n")
            
            # Additional info: Check specific tables
            print("Checking critical tables:")
            critical_tables = [
                ("at", "users"),
                ("trans", "users"),
                ("at", "instruments"),
                ("trans", "transactions")
            ]
            
            for schema, table in critical_tables:
                try:
                    count_result = connection.execute(
                        text(f"SELECT COUNT(*) FROM {schema}.{table}")
                    )
                    count = count_result.fetchone()[0]
                    print(f"  ✓ {schema}.{table}: {count} records")
                except Exception as e:
                    print(f"  ✗ {schema}.{table}: Not found or error ({str(e)[:50]})")
            
            print()
            
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("\n🔍 Database Structure Inspector\n")
    show_database_structure()
