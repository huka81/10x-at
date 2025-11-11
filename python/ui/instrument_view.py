# instrument_view.py
from tools.logger import get_logger
from typing import List, Tuple, Optional

import markdown
import pandas as pd
import plotly.graph_objs as go
import streamlit as st
from database import reporting
from database.crud import get_oid_by_symbol, get_br_symbol_by_xtb, get_profile_for_symbol
from tools.utils import format_currency_human_readable
from st_aggrid import AgGrid, GridOptionsBuilder

# Set up logging
logger = get_logger(__name__)


# Define icons for different recommendation types
recommendation_type_icons = {
    "tactical": "⚡",  # Lightning bolt for tactical (quick/short-term)
    "strategic": "🎯",  # Target for strategic (long-term focus)
    "fundamental": "📊",  # Chart for fundamental analysis
    "technical": "📈",  # Trending up for technical analysis
}

def load_hidden_acum_df() -> pd.DataFrame:
    """
    Load hidden accumulation data from the database.

    Returns:
        DataFrame containing hidden accumulation data or empty DataFrame if none found
    """
    try:
        hidden_acum_df = reporting.get_accum_score_points()
        return hidden_acum_df
    except Exception as e:
        logger.error(f"Error loading hidden accumulation data: {e}")
        return pd.DataFrame()


def load_profile_data() -> pd.DataFrame:
    """
    Load profile data for instruments with active accumulation setup.
    
    Returns:
        DataFrame with columns: oid, last_ts, xtb_long_name, br_code, branch, 
        descript, intro_date, volume, capitalization, enterprive_value
    """
    try:
        profile_df = reporting.get_accum_profile_data()
        return profile_df
    except Exception as e:
        logger.error(f"Error loading profile data: {e}")
        return pd.DataFrame()


def load_portfolio_data() -> pd.DataFrame:
    """
    Load open positions data from the database.

    Returns:
        DataFrame containing open positions or empty DataFrame if none found
    """
    try:
        positions_df = reporting.get_reporting_positions()
        return positions_df
    except Exception as e:
        logger.error(f"Error loading portfolio data: {e}")
        return pd.DataFrame()


def prepare_display_dataframe(
    positions_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Prepare the dataframe for display by selecting relevant columns and formatting.

    Args:
        positions_df: DataFrame with all position data

    Returns:
        Tuple containing:
        - Formatted DataFrame for display
        - List of report columns used
    """
    # Select columns for display (remove recommendation_type from the list since we'll combine it with symbol)
    report_cols = [
        "recommendation_id",
        "symbol",
        "volume",
        "open_price",
        "close_price",
        "actual_value",
        "profit",
        "profit_perc",
        "last_decision_ts",
        "open_time_dt",
    ]

    # Make sure all columns exist in the dataframe
    available_cols = [col for col in report_cols if col in positions_df.columns]

    # Create a copy to avoid modifying the original
    show_df = positions_df[available_cols].copy()

    # Store the original index before sorting
    show_df["original_positions_index"] = positions_df.index

    # Format datetime columns to readable format
    datetime_columns = ["last_decision_ts", "open_time_dt"]
    for col in datetime_columns:
        if col in show_df.columns:
            # Convert to datetime if it's not already, then format
            show_df[col] = pd.to_datetime(show_df[col], errors="coerce")
            show_df[col] = show_df[col].dt.strftime("%Y-%m-%d %H:%M")
            # Replace NaT with empty string
            show_df[col] = show_df[col].fillna("")

    # Combine recommendation_type icon with symbol
    if "recommendation_type" in positions_df.columns and "symbol" in show_df.columns:
        # Map recommendation types to icons
        recommendation_icons = (
            positions_df["recommendation_type"]
            .map(recommendation_type_icons)
            .fillna("📋")
        )  # Default icon for unknown types

        # Combine icon with symbol
        show_df["symbol"] = recommendation_icons + " " + show_df["symbol"]

    # Sort by open time but keep track of original indices
    show_df = show_df.sort_values("open_time_dt", ascending=False).reset_index(
        drop=True
    )
    show_df.index.name = "Lp"

    # Add display column for selectbox
    show_df["display"] = (
        show_df["symbol"]
        + " ["
        + positions_df.loc[
            show_df["original_positions_index"], "xtb_instrument_id"
        ].astype(str)
        + "]"
    )

    # Rename columns to be more human-readable
    column_mapping = {
        "recommendation_id": "📝 ID",
        "symbol": "📊 Instrument",
        "volume": "📦 Wolumen",
        "open_price": "💰 Cena otwarcia",
        "close_price": "💹 Cena aktualna",
        "actual_value": "💎 Wartość aktualna",
        "profit": "📈 Zysk/Strata (PLN)",
        "profit_perc": "📊 Zysk/Strata (%)",
        "open_time_dt": "⏰ Data otwarcia",
        "last_decision_ts": "🧠 Ostatnia decyzja",
    }

    # Apply the column mapping
    show_df = show_df.rename(columns=column_mapping)

    # Update report_cols to reflect the new column names for consistency
    report_cols_renamed = [column_mapping.get(col, col) for col in available_cols]

    return show_df, report_cols_renamed


def select_position(
    show_df: pd.DataFrame, positions_df: pd.DataFrame
) -> Tuple[int, str, int]:
    """
    Handle position selection via selectbox.

    Args:
        show_df: DataFrame prepared for display
        positions_df: Original positions DataFrame

    Returns:
        Tuple containing:
        - instrument_id: XTB instrument ID
        - symbol: Instrument symbol
        - recommendation_id: Associated recommendation ID
    """
    print("show_df")
    print(show_df.head().to_markdown())  # Debugging output

    print("positions_df")
    print(positions_df.head().to_markdown())  # Debugging output

    selected_display = st.selectbox(
        "Wybierz pozycję do podglądu szczegółów:",
        show_df["display"].tolist(),
    )

    selected_index = show_df[show_df["display"] == selected_display].index[0]
    selected_row = positions_df.iloc[selected_index]

    xtb_instrument_id = int(selected_row["xtb_instrument_id"])
    symbol = selected_row["symbol"]
    recommendation_id = int(selected_row["recommendation_id"])

    print(f"Selected position: {symbol} (ID: {xtb_instrument_id})")
    return xtb_instrument_id, symbol, recommendation_id, selected_row





def prepare_timestamp_data(df: pd.DataFrame, timestamp_cols: List[str]) -> pd.DataFrame:
    """
    Convert string timestamp columns to datetime objects.

    Args:
        df: DataFrame containing timestamp columns
        timestamp_cols: List of column names to convert

    Returns:
        DataFrame with converted timestamp columns
    """
    df_copy = df.copy()
    for col in timestamp_cols:
        if col in df_copy.columns and pd.api.types.is_string_dtype(df_copy[col]):
            df_copy[col] = pd.to_datetime(df_copy[col])
    return df_copy


def markdown_to_html(text: str) -> str:
    """
    Convert markdown text to HTML for display in Plotly hover.

    Args:
        text: Markdown formatted text

    Returns:
        HTML formatted text
    """
    if not text or pd.isna(text):
        return "Brak uzasadnienia"

    # Clean up special characters first
    cleaned_text = text.replace("¶", "\n\n").replace("|", "\n- ")

    try:
        # Convert markdown to HTML with basic extensions
        html = markdown.markdown(
            cleaned_text,
            extensions=["nl2br", "tables", "fenced_code"],
            extension_configs={
                "nl2br": {},  # Empty config for nl2br
                "tables": {},
                "fenced_code": {},
            },
        )

        # Clean up paragraph tags for better hover display
        html = html.replace("<p>", "").replace("</p>", "<br>")

        # Remove extra line breaks at the end
        html = html.strip().rstrip("<br>")

    except Exception as e:
        logger.warning(f"Error converting markdown to HTML: {e}")
        # Fallback to simple text processing
        html = cleaned_text.replace("\n", "<br>")

    return html


def create_candlestick_chart(
    reco: dict,
    quotes_df: pd.DataFrame,
    decisions_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    close_time_dt: pd.Timestamp = None,
    accum_df: pd.DataFrame = None,
) -> go.Figure:
    """
    Create a candlestick chart with decision, order markers, and accumulation points.

    Args:
        reco: Recommendation dictionary (can be empty)
        quotes_df: DataFrame with quote data
        decisions_df: DataFrame with decision history
        orders_df: DataFrame with order history
        close_time_dt: Optional close time for the position
        accum_df: DataFrame with accumulation score points (oid, ts, hidden_accum_score)

    Returns:
        Plotly figure object
    """
    if quotes_df.empty:
        raise ValueError("Cannot create chart: quotes_df is empty")

    # Make a copy to avoid modifying the original dataframes
    quotes_df = quotes_df.copy()
    decisions_df = decisions_df.copy() if not decisions_df.empty else pd.DataFrame()
    orders_df = orders_df.copy() if not orders_df.empty else pd.DataFrame()

    # Convert timestamp columns to datetime objects if needed
    timestamp_cols = ["ts_dt", "ts_dt_local"]
    for col in timestamp_cols:
        if col in quotes_df.columns:
            # Force conversion even for object dtype columns
            try:
                quotes_df[col] = pd.to_datetime(quotes_df[col], errors="coerce")
                logger.info(
                    f"Converted {col} to datetime, dtype: {quotes_df[col].dtype}"
                )
            except Exception as e:
                logger.warning(f"Error converting {col} to datetime: {e}")

    if not decisions_df.empty and "ins_ts" in decisions_df.columns:
        try:
            decisions_df["ins_ts"] = pd.to_datetime(
                decisions_df["ins_ts"], errors="coerce"
            )
        except Exception as e:
            logger.warning(f"Error converting ins_ts to datetime: {e}")

    if not orders_df.empty and "ins_ts" in orders_df.columns:
        try:
            orders_df["ins_ts"] = pd.to_datetime(orders_df["ins_ts"], errors="coerce")
        except Exception as e:
            logger.warning(f"Error converting ins_ts to datetime: {e}")

    # Get the timestamp column to use - prefer ts_dt_local if available
    timestamp_col = "ts_dt_local" if "ts_dt_local" in quotes_df.columns else "ts_dt"

    # Verify the timestamp column is properly converted
    if not pd.api.types.is_datetime64_any_dtype(quotes_df[timestamp_col]):
        logger.warning(
            f"Timestamp column {timestamp_col} is not datetime type: {quotes_df[timestamp_col].dtype}"
        )
        # Force conversion one more time
        quotes_df[timestamp_col] = pd.to_datetime(
            quotes_df[timestamp_col], errors="coerce"
        )

    # Create figure
    fig = go.Figure()

    # Add candlestick trace
    fig.add_trace(
        go.Candlestick(
            x=quotes_df[timestamp_col],
            open=quotes_df["open"],
            high=quotes_df["max"],
            low=quotes_df["min"],
            close=quotes_df["close"],
            name="Notowania",
            increasing_line_color="green",
            decreasing_line_color="red",
        )
    )

    reco_ts = reco.get("ins_ts")
    news_ts = reco.get("news_date")
    # Add vertical line for recommendation timestamp if available
    if reco_ts:
        try:
            # Convert recommendation timestamp to datetime if it's a string
            if isinstance(reco_ts, str):
                reco_ts_dt = pd.to_datetime(reco_ts)
            else:
                reco_ts_dt = reco_ts

            # Get min and max price values for the vertical line height
            y_min = quotes_df["min"].min() * 0.995  # Slightly below min
            y_max = quotes_df["max"].max() * 1.005  # Slightly above max

            # Add the vertical line
            fig.add_trace(
                go.Scatter(
                    x=[reco_ts_dt, reco_ts_dt],
                    y=[y_min, y_max],
                    mode="lines",
                    line=dict(
                        color="purple",
                        width=2,
                        dash="dash",
                    ),
                    name="Rekomendacja",
                    hovertemplate="<b>📊 Rekomendacja</b><br>"
                    + f"<b>📅 Czas:</b> {reco_ts}<br>"
                    + "<extra></extra>",
                )
            )

            # Add annotation to the vertical line
            fig.add_annotation(
                x=reco_ts_dt,
                y=y_max,
                text="Rekomendacja",
                showarrow=True,
                arrowhead=1,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor="purple",
                font=dict(
                    size=12,
                    color="purple",
                ),
                align="center",
                bordercolor="purple",
                borderwidth=1,
                borderpad=4,
                bgcolor="white",
                opacity=0.8,
            )
        except Exception as e:
            logger.warning(f"Error adding recommendation timestamp line: {e}")

    # Add horizontal lines for stop loss and take profit
    if not decisions_df.empty:
        active_width = 3
        historical_width = 2
        active_opacity = 1.0
        historical_opacity = 0.6
        decisions_sorted = decisions_df.sort_values("ins_ts").reset_index(drop=True)

        # Get the latest quote time for extending current lines
        try:
            # Ensure we have valid datetime values
            valid_timestamps = quotes_df[timestamp_col].dropna()
            if valid_timestamps.empty:
                logger.warning("No valid timestamps found in quotes data")
                chart_end_time = pd.Timestamp.now()
            else:
                # If close_time_dt is provided, use it as the chart end time
                if close_time_dt is not None and pd.notna(close_time_dt):
                    chart_end_time = close_time_dt
                    logger.info(
                        f"Using provided close_time_dt as chart end time: {chart_end_time}"
                    )
                else:
                    # Otherwise, use the max timestamp from quotes minus 1 minute
                    chart_end_time = valid_timestamps.max() - pd.Timedelta(minutes=1)
                    logger.info(f"Using calculated chart end time: {chart_end_time}")
        except Exception as e:
            logger.warning(f"Error getting timestamp: {e}")
            chart_end_time = pd.Timestamp.now()

        for idx, row in decisions_sorted.iterrows():
            try:
                start_time = row["ins_ts"]
                if pd.isna(start_time):
                    continue

                is_last_decision = idx == len(decisions_sorted) - 1

                # Determine end time based on whether this is the last decision
                if is_last_decision:
                    # Last decision: extend to the end of the chart
                    end_time = chart_end_time
                else:
                    # Historical decisions: end at the next decision time
                    end_time = decisions_sorted.iloc[idx + 1]["ins_ts"]
                    if pd.isna(end_time):
                        end_time = chart_end_time

                # Add stop loss line
                sl_value = row.get("new_sl") or row.get("actual_sl")
                # logger.info(
                #     f"Processing decision row {idx}: SL={sl_value}, TP={row.get('new_tp') or row.get('actual_tp')}"
                # )
                if pd.notnull(sl_value) and sl_value != 0:
                    # logger.info(
                    #     f"Adding Stop Loss line for decision {idx}: SL={sl_value}, Start={start_time}, End={end_time}"
                    # )
                    fig.add_trace(
                        go.Scatter(
                            x=[start_time, end_time],
                            y=[sl_value, sl_value],
                            mode="lines",
                            line=dict(
                                color="red",
                                dash="dot",
                                width=(
                                    active_width
                                    if is_last_decision
                                    else historical_width
                                ),
                            ),
                            opacity=(
                                active_opacity
                                if is_last_decision
                                else historical_opacity
                            ),
                            name="Stop Loss (aktywny)" if is_last_decision else None,
                            hovertemplate="<b>Stop Loss</b><br>"
                            + f"Wartość: {sl_value:.4f}<br>"
                            + f"Status: {'🟢 Aktywny' if is_last_decision else '🔘 Historyczny'}<br>"
                            + f"Okres: {start_time} - {end_time}<extra></extra>",
                            showlegend=is_last_decision,
                        )
                    )

                # Add take profit line
                tp_value = row.get("new_tp") or row.get("actual_tp")
                # logger.info(
                #     f"Processing decision row {idx}: TP={tp_value}, SL={sl_value}"
                # )
                if pd.notnull(tp_value) and tp_value != 0:
                    fig.add_trace(
                        go.Scatter(
                            x=[start_time, end_time],
                            y=[tp_value, tp_value],
                            mode="lines",
                            line=dict(
                                color="green",
                                dash="dot",
                                width=(
                                    active_width
                                    if is_last_decision
                                    else historical_width
                                ),
                            ),
                            opacity=(
                                active_opacity
                                if is_last_decision
                                else historical_opacity
                            ),
                            name="Take Profit (aktywny)" if is_last_decision else None,
                            hovertemplate="<b>Take Profit</b><br>"
                            + f"Wartość: {tp_value:.4f}<br>"
                            + f"Status: {'🟢 Aktywny' if is_last_decision else '🔘 Historyczny'}<br>"
                            + f"Okres: {start_time} - {end_time}<extra></extra>",
                            showlegend=is_last_decision,
                        )
                    )
            except Exception as e:
                logger.warning(f"Error processing decision row {idx}: {e}")
                continue

    # Add decision markers
    decision_colors = {
        "BUY": "#1f77b4",
        "SELL": "#d62728",
        "SL": "#ff7f0e",
        "TP": "#2ca02c",
    }
    decision_symbols = {
        "BUY": "triangle-up",
        "SELL": "triangle-down",
        "SL": "x",
        "TP": "circle",
    }

    if not decisions_df.empty:
        for _, row in decisions_df.iterrows():
            try:
                decision_type = row.get("decision", "UNKNOWN")
                color = decision_colors.get(decision_type, "#7f7f7f")
                symbol = decision_symbols.get(decision_type, "circle")

                # Calculate y-value safely
                if pd.notnull(row.get("actual_price")):
                    y_val = float(row["actual_price"])
                else:
                    # Safely get max close price as fallback
                    try:
                        y_val = float(quotes_df["close"].max())
                    except:
                        y_val = 0.0  # Fallback value

                # Get and format explanation
                explanation = row.get("short_explanation", "")
                explanation_html = markdown_to_html(explanation)

                # Format timestamp for display
                timestamp_str = str(row["ins_ts"])
                change_volume = (
                    str(row["change_volume"]) if "change_volume" in row else "0"
                )
                if pd.notnull(row["ins_ts"]):
                    try:
                        timestamp_obj = pd.to_datetime(row["ins_ts"])
                        timestamp_str = timestamp_obj.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        pass

                # Create custom hover template with formatted HTML
                hover_template = (
                    "<b>🎯 Decyzja: %{customdata[0]}</b><br>"
                    + "<b>📅 Czas:</b> %{customdata[1]}<br>"
                    + "<b>💰 Cena:</b> %{y:.4f}<br>"
                    + "<b>💰 Zmiana wolumenu:</b> %{customdata[3]}<br>"
                    + "<b>📝 Uzasadnienie:</b><br>%{customdata[2]}"
                    + "<extra></extra>"
                )

                fig.add_trace(
                    go.Scatter(
                        x=[row["ins_ts"]],
                        y=[y_val],
                        mode="markers+text",
                        marker=dict(
                            size=12,
                            color=color,
                            symbol=symbol,
                            line=dict(width=2, color="white"),
                        ),
                        text=[decision_type],
                        textposition="top center",
                        textfont=dict(size=10, color="white"),
                        name=f"Decyzja: {decision_type}",
                        customdata=[
                            [
                                decision_type,
                                timestamp_str,
                                explanation_html,
                                change_volume,
                            ]
                        ],
                        hovertemplate=hover_template,
                        showlegend=True,
                    )
                )
            except Exception as e:
                logger.warning(f"Error processing decision marker: {e}")
                continue

    # Add order markers
    if not orders_df.empty:
        for _, row in orders_df.iterrows():
            try:
                if pd.notnull(row.get("order_buy_price")):
                    order_price = float(row["order_buy_price"])

                    # Format order timestamp
                    order_timestamp_str = str(row.get("ins_ts", ""))
                    if pd.notnull(row.get("ins_ts")):
                        try:
                            order_timestamp_obj = pd.to_datetime(row["ins_ts"])
                            order_timestamp_str = order_timestamp_obj.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        except:
                            pass

                    fig.add_trace(
                        go.Scatter(
                            x=[row["ins_ts"]],
                            y=[order_price],
                            mode="markers",
                            marker=dict(
                                size=14,
                                color="#ff7f0e",
                                symbol="diamond",
                                line=dict(width=2, color="white"),
                            ),
                            name="Operacja",
                            hovertemplate="<b>📊 Operacja zakupu</b><br>"
                            + "<b>📅 Czas:</b> "
                            + order_timestamp_str
                            + "<br>"
                            + "<b>💰 Cena:</b> %{y:.4f}<br>"
                            + "<extra></extra>",
                            showlegend=True,
                        )
                    )
            except Exception as e:
                logger.warning(f"Error processing order marker: {e}")
                continue

    # Add accumulation score points if available
    logger.info(f"Processing accumulation points. accum_df is None: {accum_df is None}")
    if accum_df is not None:
        logger.info(f"accum_df shape: {accum_df.shape}")
        logger.info(f"accum_df columns: {accum_df.columns.tolist()}")
        logger.info(f"accum_df first few rows:\n{accum_df.head()}")
    
    if accum_df is not None and not accum_df.empty:
        logger.info(f"Starting to add {len(accum_df)} accumulation points to chart")
        try:
            # Convert timestamp column to datetime if needed
            accum_df_copy = accum_df.copy()
            if "ts" in accum_df_copy.columns:
                logger.info("Converting ts column to datetime")
                accum_df_copy["ts"] = pd.to_datetime(accum_df_copy["ts"], errors="coerce")
                
                # Remove timezone info to match quotes_df (which is tz-naive)
                if accum_df_copy["ts"].dt.tz is not None:
                    logger.info("Removing timezone info from accumulation timestamps")
                    accum_df_copy["ts"] = accum_df_copy["ts"].dt.tz_localize(None)
                
                # Filter out any rows with invalid timestamps
                accum_df_copy = accum_df_copy[accum_df_copy["ts"].notna()]
                logger.info(f"After filtering invalid timestamps: {len(accum_df_copy)} points remain")
                
                if not accum_df_copy.empty:
                    # Create a color scale based on hidden_accum_score
                    # Higher scores = more blue/purple, lower scores = more yellow/orange
                    scores = accum_df_copy["hidden_accum_score"].values
                    logger.info(f"Score range: min={scores.min():.2f}, max={scores.max():.2f}")
                    
                    # Normalize scores to 0-1 range for color mapping
                    if len(scores) > 0:
                        min_score = scores.min()
                        max_score = scores.max()
                        if max_score > min_score:
                            normalized_scores = (scores - min_score) / (max_score - min_score)
                        else:
                            normalized_scores = [0.5] * len(scores)
                    else:
                        normalized_scores = []
                    
                    # Create color list: purple/blue for high scores, yellow/orange for low scores
                    # Using more vibrant colors that stand out
                    colors = []
                    for s in normalized_scores:
                        if s > 0.66:  # High scores - bright blue
                            colors.append('rgb(0, 100, 255)')
                        elif s > 0.33:  # Medium scores - bright purple
                            colors.append('rgb(150, 0, 255)')
                        else:  # Low scores - bright orange
                            colors.append('rgb(255, 140, 0)')
                    
                    logger.info(f"Color mapping completed. Sample colors: {colors[:5]}")
                    
                    # Get close prices at accumulation point timestamps
                    # We'll try to match timestamps to find the corresponding close price
                    y_values = []
                    for idx, ts in enumerate(accum_df_copy["ts"]):
                        # Find the closest quote timestamp
                        time_diffs = abs(quotes_df[timestamp_col] - ts)
                        closest_idx = time_diffs.idxmin()
                        close_price = quotes_df.loc[closest_idx, "close"]
                        y_values.append(close_price)
                        if idx < 3:  # Log first few matches
                            logger.info(f"Point {idx}: ts={ts}, matched price={close_price:.4f}")
                    
                    logger.info(f"Adding trace with {len(y_values)} accumulation points")
                    fig.add_trace(
                        go.Scatter(
                            x=accum_df_copy["ts"],
                            y=y_values,
                            mode="markers",
                            marker=dict(
                                size=18,  # Increased from 10 to 18 for better visibility
                                color=colors,
                                symbol="star",  # Changed to star for better visibility
                                line=dict(width=2, color="black"),  # Black border for contrast
                            ),
                            name="⭐ Punkty akumulacji",
                            customdata=accum_df_copy["hidden_accum_score"].values,
                            hovertemplate="<b>🔍 Punkt akumulacji</b><br>"
                            + "<b>📅 Czas:</b> %{x}<br>"
                            + "<b>💰 Cena:</b> %{y:.4f}<br>"
                            + "<b>📊 Wynik akumulacji:</b> %{customdata:.2f}<br>"
                            + "<extra></extra>",
                            showlegend=True,
                        )
                    )
                    logger.info("Successfully added accumulation points trace to figure")
                else:
                    logger.warning("No valid accumulation points after filtering")
            else:
                logger.warning("Column 'ts' not found in accum_df")
        except Exception as e:
            logger.error(f"Error adding accumulation points: {e}", exc_info=True)
    else:
        logger.info("No accumulation data to display (accum_df is None or empty)")

    # Calculate appropriate Y-axis range based on price data and SL/TP levels
    try:
        # Start with price data
        min_price = quotes_df["min"].min()
        max_price = quotes_df["max"].max()

        # Collect all relevant values for Y-axis range calculation
        all_y_values = [min_price, max_price]

        # Add SL and TP values from decisions_df if available
        if not decisions_df.empty:
            # Get all SL values (both new_sl and actual_sl)
            sl_values = []
            tp_values = []

            for idx, row in decisions_df.iterrows():
                sl_value = row.get("new_sl") or row.get("actual_sl")
                tp_value = row.get("new_tp") or row.get("actual_tp")

                # Only include realistic, non-zero, non-null values
                # Filter out values that are too close to zero (likely erroneous)
                min_realistic_value = (
                    min_price * 0.1
                )  # Must be at least 10% of minimum price

                if (
                    pd.notnull(sl_value)
                    and sl_value != 0
                    and sl_value > min_realistic_value
                ):
                    sl_values.append(sl_value)

                if (
                    pd.notnull(tp_value)
                    and tp_value != 0
                    and tp_value > min_realistic_value
                ):
                    tp_values.append(tp_value)

            # Add SL/TP values to the range calculation
            all_y_values.extend(sl_values)
            all_y_values.extend(tp_values)

        # Calculate range based on all values
        if all_y_values:
            min_value = min(all_y_values)
            max_value = max(all_y_values)

            # Add some padding (5% on each side)
            value_range = max_value - min_value
            padding = value_range * 0.05
            y_min = min_value - padding
            y_max = max_value + padding

            # If range is very small, add minimum padding
            if value_range < max_value * 0.02:  # Less than 2% range
                padding = max_value * 0.02
                y_min = min_value - padding
                y_max = max_value + padding
        else:
            # Fallback to price data only
            price_range = max_price - min_price
            padding = price_range * 0.05
            y_min = min_price - padding
            y_max = max_price + padding

    except Exception as e:
        logger.warning(f"Error calculating Y-axis range: {e}")
        # Fallback to auto scaling
        y_min = None
        y_max = None

    # Update layout with enhanced styling
    fig.update_layout(
        height=600,
        # title=dict(
        #     text="Wykres świecowy z decyzjami i operacjami", x=0.5, font=dict(size=16)
        # ),
        xaxis=dict(
            title="Czas",
            gridcolor="lightgray",
            showgrid=True,
            zeroline=False,
        ),
        yaxis=dict(
            title="Cena",
            gridcolor="lightgray",
            showgrid=True,
            zeroline=False,
            range=[y_min, y_max] if y_min is not None and y_max is not None else None,
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=50, t=60, b=50),
        hovermode="closest",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    # Add range breaks for weekends and after hours
    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # Hide weekends
            dict(bounds=[17, 9], pattern="hour"),  # Hide after hours
        ]
    )

    return fig


def show_instrument_selector() -> Optional[int]:
    """
    Display instrument selector based on profile data and return selected oid.

    Returns:
        int: Selected oid or None if no instruments available
    """
    # Load profile data
    profile_df = load_profile_data()
    if profile_df.empty:
        st.warning("Brak instrumentów z aktywnym setupem akumulacji.")
        return None

    # Initialize session state for selected instrument index
    if "selected_instrument_index" not in st.session_state:
        st.session_state.selected_instrument_index = 0

    # Ensure selected_instrument_index is within valid range
    if st.session_state.selected_instrument_index >= len(profile_df):
        st.session_state.selected_instrument_index = 0

    with st.expander("📊 Wybór instrumentu", expanded=True):
        # Prepare display dataframe
        display_df = profile_df.copy()
        display_df["display_index"] = display_df.index
        
        # Select columns for display
        display_columns = ["oid", "xtb_long_name", "br_code", "branch", "last_ts"]
        grid_df = display_df[display_columns + ["display_index"]].copy()
        
        # Rename columns for better display
        grid_df = grid_df.rename(columns={
            "oid": "🆔 OID",
            "xtb_long_name": "📊 Instrument",
            "br_code": "🔤 Symbol",
            "branch": "🏢 Branża",
            "last_ts": "⏰ Ostatni setup"
        })

        # Convert any problematic columns to string for display
        for col in grid_df.columns:
            if col != "display_index" and grid_df[col].dtype == "object":
                grid_df[col] = grid_df[col].astype(str)

        # Configure AgGrid with pre-selection
        gb = GridOptionsBuilder.from_dataframe(grid_df)
        gb.configure_selection(
            "single",
            use_checkbox=False,
            pre_selected_rows=[st.session_state.selected_instrument_index],
        )
        gb.configure_grid_options(domLayout="normal")
        gb.configure_grid_options(rowStyle={"cursor": "pointer"})
        gb.configure_default_column(min_column_width=100)
        gb.configure_column("display_index", hide=True)
        grid_options = gb.build()

        # Use AgGrid with customized options
        grid_response = AgGrid(
            grid_df,
            gridOptions=grid_options,
            update_mode="SELECTION_CHANGED",
            fit_columns_on_grid_load=True,
            height=300,
            allow_unsafe_jscode=True,
            key="instrument_grid",
            theme="streamlit",
        )

    # Handle row selection
    try:
        selected_rows = grid_response.get("selected_rows", [])

        # Check if selected_rows is a DataFrame and convert to list
        if isinstance(selected_rows, pd.DataFrame):
            if not selected_rows.empty:
                selected_rows = selected_rows.to_dict("records")
            else:
                selected_rows = []

        # Now safely check if we have selected rows
        if selected_rows and len(selected_rows) > 0:
            selected_row_data = selected_rows[0]

            # Use the display_index to find the correct row
            if "display_index" in selected_row_data:
                display_index = int(selected_row_data["display_index"])
                if display_index != st.session_state.selected_instrument_index:
                    st.session_state.selected_instrument_index = display_index
                    st.rerun()
    except Exception as e:
        st.error(f"Error processing selection: {e}")
        logger.exception("Error processing AgGrid selection")

    # Get selected instrument details
    selected_index = st.session_state.selected_instrument_index

    # Ensure the index is valid before accessing the dataframe
    if selected_index >= len(profile_df):
        selected_index = 0
        st.session_state.selected_instrument_index = 0

    selected_row = profile_df.iloc[selected_index]

    # Return the oid
    return int(selected_row["oid"])


def show_instrument_view(oid: int):
    """
    Display instrument view for a specific oid.

    Args:
        oid: Object ID of the instrument to display
    """
    if oid is None:
        st.error("Brak OID do wyświetlenia")
        return

    # Load profile data and filter by oid
    profile_df = load_profile_data()
    if profile_df.empty:
        st.warning("Brak instrumentów z aktywnym setupem akumulacji.")
        return

    # Filter to get the specific instrument
    filtered_profile = profile_df[profile_df["oid"] == oid]

    if filtered_profile.empty:
        st.error(f"Nie znaleziono instrumentu dla OID: {oid}")
        return

    # Get the instrument profile
    instrument_profile = filtered_profile.iloc[0]

    # Show info about the instrument being displayed
    st.info(f"📌 Wyświetlanie szczegółów dla instrumentu: **{instrument_profile['xtb_long_name']}** (OID: {oid})")

    # Extract instrument details
    br_code = instrument_profile.get("br_code", "N/A")
    xtb_long_name = instrument_profile.get("xtb_long_name", "N/A")
    branch = instrument_profile.get("branch", "N/A")
    descript = instrument_profile.get("descript", "N/A")
    intro_date = instrument_profile.get("intro_date", "N/A")
    volume = instrument_profile.get("volume", 0)
    capitalization = instrument_profile.get("capitalization", 0)
    enterprise_value = instrument_profile.get("enterprive_value", 0)
    last_ts = instrument_profile.get("last_ts", "N/A")
    
    print(instrument_profile)
    
    # Format currency values
    volume_formatted = format_currency_human_readable(volume)
    capitalization_formatted = format_currency_human_readable(capitalization)
    enterprise_value_formatted = format_currency_human_readable(enterprise_value)
    # Create external link to biznesradar
    url = f"https://www.biznesradar.pl/notowania/{br_code}"
    
    # Display instrument summary with formatted HTML
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(90deg, #f0f2f6, #ffffff);
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #1f77b4;
            margin-bottom: 20px;
        ">
            <h2 style="margin: 0; color: #1f77b4;">
                📊 {xtb_long_name}
            </h2>
            <p style="margin: 5px 0; color: #666; font-size: 14px;">
                <strong>Symbol:</strong> {br_code} | 
                <strong>Branża:</strong> {branch} | 
                <strong>OID:</strong> {oid}
                <a href="{url}" target="_blank" style="text-decoration: none; margin-left: 10px;">
                    <span style="font-size: 20px; color: #1f77b4;">🔗</span>
                </a>
            </p>
            <p style="margin: 10px 0 5px 0; color: #444; font-size: 13px;">
                <strong>💰 Kapitalizacja:</strong> {capitalization_formatted} | 
                <strong>🏢 Wartość przedsiębiorstwa:</strong> {enterprise_value_formatted}
            </p>
            <p style="margin: 10px 0 5px 0; color: #444; font-size: 13px;">
                <strong>📅 Data debiutu:</strong> {intro_date} | 
                <strong>⏰ Ostatni setup:</strong> {last_ts}
            </p>
            <p style="margin: 14px 0 5px 0; color: #444; font-size: 13px;">
                {descript} 
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Candlestick chart section
    st.subheader("Notowania i punkty akumulacji")

    # Load data for charts - use a reasonable lookback period
    days_back = 365  # Default to 30 days for accumulation analysis
    
    logger.info(f"Loading quotes for instrument: {br_code}, oid: {oid}, days_back: {days_back}")
    # Need to get xtb_instrument_id from oid
    # For now, we'll use br_symbol to get quotes
    quotes_df = reporting.get_quotes(br_symbol=br_code, days_back=days_back)
    logger.info(f"Loaded {len(quotes_df)} quote records")
    
    # Load accumulation points
    logger.info("Loading all accumulation data")
    accum_df = load_hidden_acum_df()
    logger.info(f"Loaded {len(accum_df)} total accumulation records")
    
    # Filter accumulation points for this instrument
    instrument_accum_df = accum_df[accum_df["oid"] == oid] if not accum_df.empty else pd.DataFrame()
    logger.info(f"Filtered to {len(instrument_accum_df)} accumulation points for oid {oid}")
    if not instrument_accum_df.empty:
        logger.info(f"Sample accumulation data:\n{instrument_accum_df.head()}")

    if quotes_df.empty:
        st.warning("Brak notowań instrumentu.")
    else:
        # Create and display chart
        try:
            fig = create_candlestick_chart(
                reco={},  # No recommendation data needed
                quotes_df=quotes_df,
                decisions_df=pd.DataFrame(),  # No decisions
                orders_df=pd.DataFrame(),  # No orders
                close_time_dt=None,
                accum_df=instrument_accum_df  # Pass accumulation points
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating chart: {e}")
            logger.exception("Error creating candlestick chart")


def show_instrument_management_view():
    """
    Combined view that shows instrument selector and instrument details.
    This is the main entry point for the instrument management interface.
    """
    # App title
    st.title("Panel analizy instrumentów")

    # Check if oid is provided via URL
    query_params = st.query_params
    url_oid = None

    if "oid" in query_params:
        try:
            url_oid = int(query_params["oid"])
            # If URL has oid, go directly to instrument view
            show_instrument_view(url_oid)
            return
        except (ValueError, TypeError):
            st.error("Nieprawidłowy format OID w URL")
            return

    # Check if oid is provided via session state
    if "selected_oid" in st.session_state:
        selected_oid = st.session_state.selected_oid
        # Clear the session state to prevent repeated redirects
        del st.session_state.selected_oid
        show_instrument_view(selected_oid)
        return

    # Normal flow: show selector and then details
    selected_oid = show_instrument_selector()

    if selected_oid is not None:
        st.divider()
        show_instrument_view(selected_oid)
