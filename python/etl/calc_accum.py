"""
ETL module for calculating and updating accumulation indicators.

This module provides functions to trigger the calculation and storage
of hidden accumulation scores and setups in the database.
"""

from sqlalchemy import text
from tools.logger import get_logger
from database import get_db_engine

logger = get_logger(__name__)


def update_hidden_accum_snapshots() -> dict:
    """
    Call the stored procedure to update hidden accumulation snapshots.
    
    This procedure incrementally updates the at.indicator_snapshot table
    with new hidden accumulation scores and setup flags from the v_hidden_20 view.
    
    Returns:
        dict: Result containing:
            - success (bool): Whether the procedure executed successfully
            - rows_affected (int): Number of rows inserted/updated
            - message (str): Status message
            
    Raises:
        Exception: If database connection or procedure execution fails
    """
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            # Call the stored procedure
            logger.info("Calling stored procedure: at.update_hidden_accum_snapshots()")
            conn.execute(text("CALL at.update_hidden_accum_snapshots()"))
            
            # Get the number of affected rows from the last log entry
            result = conn.execute(text("""
                SELECT rows_inserted, message 
                FROM at.run_log 
                ORDER BY started_at DESC 
                LIMIT 1
            """))
            row = result.fetchone()
            
            conn.commit()
            
            if row:
                rows_inserted, message = row
                logger.info(f"Procedure completed: {message} ({rows_inserted} rows)")
                return {
                    "success": True,
                    "rows_affected": rows_inserted,
                    "message": message
                }
            else:
                logger.warning("Procedure completed but no log entry found")
                return {
                    "success": True,
                    "rows_affected": 0,
                    "message": "Procedure completed (no log entry)"
                }
                    
    except Exception as e:
        logger.error(f"Error calling update_hidden_accum_snapshots: {e}", exc_info=True)
        return {
            "success": False,
            "rows_affected": 0,
            "message": f"Error: {str(e)}"
        }


if __name__ == "__main__":
    # Run the update when script is executed directly
    logger.info("Starting hidden accumulation snapshots update...")
    result = update_hidden_accum_snapshots()
    
    if result["success"]:
        logger.info(f"[SUCCESS] Update completed: {result['message']}")
    else:
        logger.error(f"[FAILED] Update failed: {result['message']}")
