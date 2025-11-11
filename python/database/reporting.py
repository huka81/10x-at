import pandas as pd
from sqlalchemy import text
from enum import Enum

from database.crud import get_oid_by_symbol, get_xtb_instrument_id
from datetime import datetime
from database import get_db_engine
from tools.logger import get_logger


class TypeScale(Enum):
    lin = "lin"
    log = "log"

class TimeRange(Enum):
    ONE_DAY = "1d"
    THREE_DAYS = "3d"
    FIVE_DAYS = "5d"
    TEN_DAYS = "10d"
    ONE_MONTH = "1m"
    THREE_MONTHS = "3m"
    SIX_MONTHS = "6m"
    ONE_YEAR = "1r"
    THREE_YEARS = "3l"
    FIVE_YEARS = "5l"
    MAX = "max"


# Ensure logger is configured only once
logger = get_logger(__name__)


def get_accum_score_points() -> pd.DataFrame:
    """
    Retrieve accumulated score points for instruments with active accumulation setup.
    
    Returns:
        pd.DataFrame: DataFrame containing columns:
            - oid: Object identifier for the instrument
            - ts: Timestamp of the snapshot
            - hidden_accum_score: Rounded accumulation score (2 decimal places)
    
    Raises:
        Exception: If database query fails
    """
    sql = """
    SELECT s.oid
          , s.ts
          , ROUND(CAST("values"->>'hidden_accum_score' AS NUMERIC), 2) AS hidden_accum_score 
      FROM "at".indicator_snapshot s
     WHERE "values"->>'hidden_accum_setup' = 'true'
    """
    engine = get_db_engine()
    print("Fetching accumulated score points for instruments with active accumulation setup")
    
    try:
        df = pd.read_sql(text(sql), engine)
        df = df.convert_dtypes()
        return df
    except Exception as e:
        print(f"Error fetching accumulated score points: {e}")
        raise e


def get_accum_profile_data() -> pd.DataFrame:
    """
    Retrieve profile data for instruments with active accumulation setup.
    
    Fetches company profile information joined with the latest accumulation timestamp
    for instruments that have an active hidden accumulation setup.
    
    Returns:
        pd.DataFrame: DataFrame containing columns:
            - oid: Object identifier for the instrument
            - last_ts: Most recent timestamp with active accumulation setup
            - xtb_long_name: Full instrument name from XTB
            - br_code: Biznes Radar symbol code
            - branch: Industry branch/sector
            - descript: Company description
            - intro_date: IPO/introduction date
            - volume: Trading volume
            - capitalization: Market capitalization
            - enterprive_value: Enterprise value
    
    Raises:
        Exception: If database query fails
    """
    sql = """
    SELECT m.oid
          , ha.last_ts
          , m.xtb_long_name
          , p.br_code
          , p.branch
          , p.descript
          , p.intro_date
          , p.volume
          , p.capitalization
          , p.enterprive_value
      FROM raw.br_profile_v p
      JOIN raw.xtb2br_map_v m
        ON p.br_code = m.br_symbol
      JOIN (SELECT oid
                  , MAX(ts) AS last_ts
              FROM "at".indicator_snapshot s
             WHERE "values"->>'hidden_accum_setup' = 'true'
             GROUP BY oid) ha
        ON m.oid = ha.oid
    """
    engine = get_db_engine()
    print("Fetching profile data for instruments with active accumulation setup")
    
    try:
        df = pd.read_sql(text(sql), engine)
        df = df.convert_dtypes()
        return df
    except Exception as e:
        print(f"Error fetching accumulation profile data: {e}")
        raise e



    

def get_quotes(
    xtb_instrument_id: int = None, br_symbol: str = None, days_back: int = 10
) -> pd.DataFrame:
    """
    Retrieve instrument quotes from the last X days.
    
    Fetches historical quotes from trans.br_quotes and combines them with today's
    quotes from trans.xtb_portfolio_quotes. One row represents one quote reading.
    
    Args:
        xtb_instrument_id: XTB instrument identifier. If None, br_symbol must be provided.
        br_symbol: Biznes Radar symbol. Used to lookup xtb_instrument_id if not provided.
        days_back: Number of days of historical data to retrieve. Defaults to 10.
    
    Returns:
        pd.DataFrame: Combined and sorted quotes DataFrame containing columns:
            - oid: Object identifier
            - instrument_id: XTB instrument identifier
            - raw_ts: Raw timestamp
            - day_nbr: Day number (YYYYMMDD format)
            - ts_dt: Timestamp as datetime
            - weekday: Day of week abbreviation
            - min: Minimum price in period
            - max: Maximum price in period
            - open: Opening price
            - close: Closing price
            - volume: Trading volume
            - amount: Trading amount
    
    Raises:
        Exception: If instrument lookup or database query fails
    
    Note:
        Either xtb_instrument_id or br_symbol must be provided.
    """
    if br_symbol and not xtb_instrument_id:
        xtb_instrument_id = get_xtb_instrument_id(br_symbol=br_symbol)
    oid = get_oid_by_symbol(xtb_instrument_id=xtb_instrument_id)
    engine = get_db_engine()
    
    sql_hist = """
        select q.oid
            , m.xtb_instrument_id instrument_id
            , q.raw_ts
            , q.day_nbr 
            , q.ts_dt
	        , TO_CHAR(ts_dt, 'Dy') weekday
            , q.min
            , q.max
            , q.open
            , q.close
            , q.volume
            , q.amount
        from trans.br_quotes q
        join raw.xtb2br_map_v m
            on q.oid = m.oid
        where grain = '1m'
        and day_nbr < to_char(current_timestamp, 'YYYYMMDD')::int
        AND q.ts_dt > current_timestamp - (:days_back || ' days')::INTERVAL
        and q.oid = :oid
        """
    db_quotes_hist_df = pd.read_sql(
        text(sql_hist),
        engine,
        params={
            "xtb_instrument_id": xtb_instrument_id,
            "days_back": str(days_back),
            "oid": oid
        },
    )
    db_quotes_hist_df = db_quotes_hist_df.convert_dtypes()

    sql_today = """
       select m.oid
            , q.instrument_id
            , q.raw_ts 
            , q.day_nbr 
            , q.ts_dt
	        , TO_CHAR(ts_dt, 'Dy') weekday
            , q.min
            , q.max
            , q.open
            , q.close
            , 1 volume
            , q.close amount 
        from trans.xtb_portfolio_quotes q
        join raw.xtb2br_map_v m
            on q.instrument_id = m.xtb_instrument_id 
        where day_nbr = to_char(current_timestamp, 'YYYYMMDD')::int
        and q.instrument_id = :xtb_instrument_id
    """
    print(
        f"Fetching quotes for XTB Instrument ID: {xtb_instrument_id}, Days Back: {days_back}"
    )

    db_quotes_today_df = pd.read_sql(
        text(sql_today),
        engine,
        params={
            "xtb_instrument_id": xtb_instrument_id,
            "days_back": str(days_back),
            "oid": oid
        },
    )
    db_quotes_today_df = db_quotes_today_df.convert_dtypes()

    db_quotes_df = pd.concat([db_quotes_hist_df, db_quotes_today_df], ignore_index=True)
    db_quotes_df = db_quotes_df.sort_values(by=["ts_dt"]).reset_index(drop=True)

    
    return db_quotes_df





if __name__ == "__main__":
    # Przykładowe użycie funkcji
    xtb_instrument_id = 7185
    quotes = get_quotes(xtb_instrument_id=xtb_instrument_id, days_back=2)
    print("\nQuotes:")
    print(quotes.head())
