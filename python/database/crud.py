import pandas as pd
from database import engine
from sqlalchemy import text
from tools.logger import get_logger

current_module_name = __name__
logger = get_logger(current_module_name)


def get_oid_by_symbol(
    br_symbol: str = None,
    xtb_symbol: str = None,
    symbol3: str = None,
    xtb_instrument_id: int = None,
) -> int:
    """
    Get OID (Object ID) by various symbol identifiers.
    
    Args:
        br_symbol: BiznesRadar symbol
        xtb_symbol: XTB platform symbol
        symbol3: First 3 characters of XTB symbol
        xtb_instrument_id: XTB instrument identifier
        
    Returns:
        Object ID if found, None otherwise
    """
    try:
        if br_symbol:
            query = f'''
                SELECT oid
                FROM raw.xtb2br_map_v
                WHERE upper(br_symbol) = upper('{br_symbol}')
            '''
        elif xtb_symbol:
            query = f'''
                SELECT oid
                FROM raw.xtb2br_map_v
                WHERE upper(xtb_symbol) = upper('{xtb_symbol}')
            '''
        elif symbol3:
            query = f'''
                SELECT oid
                  FROM raw.xtb2br_map_v
                 WHERE upper(left(xtb_symbol, 3)) = upper('{symbol3}')
            '''
        elif xtb_instrument_id:
            query = f'''
                SELECT oid
                  FROM raw.xtb2br_map_v
                 WHERE xtb_instrument_id = {xtb_instrument_id}
            '''
        else:
            return None

        result = pd.read_sql(query, engine)
        oid = int(result["oid"].values[0])

        return oid if oid else None
    except Exception as e:
        logger.error(f"Error: {e}")
        return None


def get_xtb_instrument_id(br_symbol: str = None, xtb_symbol: str = None) -> int:
    """
    Get XTB instrument ID by BiznesRadar or XTB symbol.
    
    Args:
        br_symbol: BiznesRadar symbol
        xtb_symbol: XTB platform symbol
        
    Returns:
        XTB instrument ID if found, None otherwise
    """
    try:
        query = f'''
            SELECT xtb_instrument_id
              FROM raw.xtb2br_map_v
             WHERE 1=1 
        '''
        if br_symbol:
            query += f" AND upper(br_symbol) = upper('{br_symbol}')"
        if xtb_symbol:
            query += f" AND xtb_symbol = {xtb_symbol}"
        query += f" LIMIT 1"

        result = pd.read_sql(query, engine)
        xtb_instrument_id = int(result["xtb_instrument_id"].values[0])

        return xtb_instrument_id if xtb_instrument_id else None
    except Exception as e:
        logger.error(f"Error: {e}")
        return None


def get_br_symbol_by_xtb(xtb_symbol: str = None, xtb_instrument_id: int = None) -> str:
    """
    Get BiznesRadar symbol by XTB symbol or instrument ID.
    
    Args:
        xtb_symbol: XTB platform symbol
        xtb_instrument_id: XTB instrument identifier
        
    Returns:
        BiznesRadar symbol if found, None otherwise
    """
    try:
        if not xtb_symbol and not xtb_instrument_id:
            logger.error(
                "At least one of xtb_symbol or xtb_instrument_id must be provided"
            )
            return None

        query = f'''
            SELECT br_symbol
              FROM raw.xtb2br_map_v
             WHERE 1=1 
        '''
        if xtb_symbol:
            query += f" AND xtb_symbol = '{xtb_symbol}'"
        if xtb_instrument_id:
            query += f" AND xtb_instrument_id = {xtb_instrument_id}"

        result = pd.read_sql(query, engine)
        br_symbol = result["br_symbol"].values[0]

        return br_symbol if br_symbol else None
    except Exception as e:
        logger.error(f"Error: {e}")
        return None


def get_profile_for_symbol(br_symbol: str = None, instrument_id: int = None) -> dict:
    """
    Retrieve profile information for a specific stock symbol from BiznesRadar.

    This function queries the raw.br_symbol_profile_flat_v view to get detailed
    company profile information including branch, start date, description,
    enterprise value, capitalization and value/capitalization percentage.

    Args:
        br_symbol: BiznesRadar symbol identifier (e.g., 'PKN', '11-BIT-STUDIOS')
        instrument_id: XTB instrument identifier

    Returns:
        Dictionary containing profile information with keys:
            - br_symbol: The BiznesRadar symbol
            - period_ts: Timestamp of the profile data
            - branch: Industry/sector classification
            - start_date: IPO or debut date
            - description: Company description
            - enterprise_value: Enterprise value (decimal)
            - capitalization: Market capitalization (decimal)
            - value_capitalization_perc: Difference between EV and capitalization as percentage

    Examples:
        >>> profile = get_profile_for_symbol("PKN")
        >>> print(f"Company branch: {profile['branch']}")
        >>> print(f"Market cap: {profile['capitalization']}")
    """
    logger.info(f"Retrieving profile information for symbol {br_symbol}")

    try:
        if not br_symbol and not instrument_id:
            logger.error("Both br_symbol and instrument_id are None")
            return None

        query = '''
            SELECT p.br_symbol, 
                   p.period_ts,
                   p.branch,
                   p.start_date,
                   p.description,
                   p.enterprise_value,
                   p.capitalization,
                   p.value_capitalization_perc
              FROM raw.br_symbol_profile_flat_v p
              join raw.xtb2br_map_v m
                on p.br_symbol = m.br_symbol
             where 1=1 
            '''
        if br_symbol:
            query += f" AND upper(p.br_symbol) = upper('{br_symbol}')"
        if instrument_id:
            query += f" AND m.xtb_instrument_id = {instrument_id}"
        query += f" LIMIT 1"

        result = pd.read_sql(text(query), engine)

        if not result.empty:
            profile_data = result.iloc[0].to_dict()

            # Ensure numeric values are properly typed
            for numeric_field in [
                "enterprise_value",
                "capitalization",
                "value_capitalization_perc",
            ]:
                if profile_data.get(numeric_field) is not None:
                    profile_data[numeric_field] = float(profile_data[numeric_field])

            logger.info(
                f"Profile information found for {br_symbol}: {profile_data['branch']}"
            )
            return profile_data
        else:
            logger.warning(f"No profile information found for symbol {br_symbol}")
            return None

    except Exception as e:
        logger.error(f"Error retrieving profile for {br_symbol}: {e}", exc_info=True)
        return None
