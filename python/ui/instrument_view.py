# instrument_view.py
from tools.logger import get_logger
from typing import List, Tuple, Optional

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


def display_recommendation(recommendation_id: int, xtb_instrument_id: int) -> None:
    """
    Display recommendation details in an expander.

    Args:
        recommendation_id: ID of the recommendation
        xtb_instrument_id: XTB instrument ID
    """
    reco = reporting.get_recommendation(recommendation_id, xtb_instrument_id)

    reco_type = reco.get("type", "unknown") if reco else "unknown"
    icon = recommendation_type_icons.get(reco_type, "📋")  # Default clipboard icon

    if reco_type == "tactical":
        with st.expander(
            f"{icon} Rekomendacja taktyczna nr {recommendation_id}",
            expanded=False,
        ):
            if reco:
                st.write(f"**Data rekomendacji:** {reco.get('ins_ts') or '-'}")
                st.write(f"**Data newsu:** {reco.get('news_date') or '-'}")
                st.write(f"**Tytuł:** {reco.get('title') or '-'}")

                # Format rationale with markdown if available
                rationale = reco.get("rationale") or "-"
                if rationale != "-":
                    st.markdown(f"**Uzasadnienie:**")
                    st.markdown(rationale)
                else:
                    st.write(f"**Uzasadnienie:** {rationale}")

                # Format link as clickable if available
                link = reco.get("link")
                if link and link != "-":
                    st.markdown(f"**Link:** [🔗 Otwórz artykuł]({link})")
                else:
                    st.write(f"**Link:** -")
            else:
                st.info(
                    "Brak powiązanej rekomendacji – pozycja otwarta ręcznie lub bezpośrednio przez użytkownika."
                )
    elif reco_type == "strategic":
        with st.expander(
            f"{icon} Rekomendacja strategiczna nr {recommendation_id}",
            expanded=False,
        ):
            if reco:
                st.write(f"**Typ:** {icon} {reco.get('type') or '-'}")
                st.write(f"**Data rekomendacji:** {reco.get('ins_ts') or '-'}")

                # Format analyses with markdown if available
                instrument_analysis = reco.get("instrument_analysis") or "-"
                if instrument_analysis != "-":
                    st.markdown(f"**Analiza instrumentu:**")
                    st.markdown(instrument_analysis)
                else:
                    st.write(f"**Analiza instrumentu:** {instrument_analysis}")

                price_analysis = reco.get("price_analysis") or "-"
                if price_analysis != "-":
                    st.markdown(f"**Analiza cenowa:**")
                    st.markdown(price_analysis)
                else:
                    st.write(f"**Analiza cenowa:** {price_analysis}")
            else:
                st.info(
                    "Brak powiązanej rekomendacji – pozycja otwarta ręcznie lub bezpośrednio przez użytkownika."
                )
    else:
        # Handle other types or unknown types
        type_display = reco_type if reco_type != "unknown" else "nieznany"
        with st.expander(
            f"{icon} Rekomendacja zakupu ({type_display})", expanded=False
        ):
            if reco:
                st.write(f"**Typ:** {icon} {reco.get('type') or '-'}")
                st.write(f"**Data rekomendacji:** {reco.get('ins_ts') or '-'}")

                # Display all available fields
                for key, value in reco.items():
                    if key not in ["type", "ins_ts"] and value and value != "-":
                        # Format field name nicely
                        field_name = key.replace("_", " ").title()
                        if key in [
                            "rationale",
                            "instrument_analysis",
                            "price_analysis",
                        ]:
                            st.markdown(f"**{field_name}:**")
                            st.markdown(value)
                        elif key == "link":
                            st.markdown(f"**{field_name}:** [🔗 Otwórz]({value})")
                        else:
                            st.write(f"**{field_name}:** {value}")
            else:
                st.info(
                    "Brak powiązanej rekomendacji – pozycja otwarta ręcznie lub bezpośrednio przez użytkownika."
                )


def display_position_summary(selected_row: pd.Series) -> None:
    """
    Display a nice header summary section for the selected position.

    Args:
        selected_row: Series with the selected position data
    """
    # Extract key data
    symbol = selected_row.get("symbol", "N/A")
    full_name = selected_row.get("full_name", "N/A")
    br_symbol = selected_row.get("br_symbol", "N/A")
    recommendation_type = selected_row.get("recommendation_type", "unknown")
    actual_volume = selected_row.get("actual_volume", 0)
    volume = selected_row.get("volume", 0)
    open_price = selected_row.get("open_price", 0)
    close_price = selected_row.get("close_price", 0)
    open_time_dt = selected_row.get("open_time_dt", "")
    profit = selected_row.get("profit", 0)
    profit_perc = selected_row.get("profit_perc", 0)
    nominal_value = selected_row.get("nominal_value", 0)
    actual_value = selected_row.get("actual_value", 0)
    last_decision = selected_row.get("decision", "N/A")
    instrument_id = selected_row.get("xtb_instrument_id", 0)

    # Determine if position is open or closed
    is_position_open = actual_volume > 0
    position_status = "🟢 OTWARTA" if is_position_open else "🔴 ZAMKNIĘTA"
    status_color = "#28a745" if is_position_open else "#dc3545"

    # Get recommendation icon
    icon = recommendation_type_icons.get(recommendation_type, "📋")

    # Determine profit color and icon
    if profit > 0:
        profit_color = "green"
        profit_icon = "📈"
    elif profit < 0:
        profit_color = "red"
        profit_icon = "📉"
    else:
        profit_color = "gray"
        profit_icon = "➖"

    # Create external link to biznesradar
    url = f"https://www.biznesradar.pl/notowania/{br_symbol}"

    profile_dict = get_profile_for_symbol(instrument_id=instrument_id) or {}
    profile_branch = profile_dict.get("branch", "")
    profile_description = profile_dict.get("description", "")
    profile_enterprise_value = profile_dict.get("enterprise_value", "")
    profile_capitalization = profile_dict.get("capitalization", "")

    # Format profile information
    profile_parts = []
    if profile_branch:
        profile_parts.append(f"<strong>Branża:</strong> {profile_branch}")
    if profile_enterprise_value:
        profile_parts.append(
            f"<strong>Wartość:</strong> {format_currency_human_readable(profile_enterprise_value)}"
        )
    if profile_capitalization:
        profile_parts.append(
            f"<strong>Kapitalizacja:</strong> {format_currency_human_readable(profile_capitalization)}"
        )

    profile_txt = (
        " | ".join(profile_parts) if profile_parts else "Brak danych profilowych"
    )

    # Main header with external link and position status
    st.markdown(
        f"""
        <div style="background: linear-gradient(90deg, #f0f2f6, #ffffff); 
                    padding: 20px; 
                    border-radius: 10px; 
                    border-left: 5px solid {status_color};
                    margin-bottom: 20px;">
            <h2 style="margin: 0; color: #1f77b4;">
                {icon} {full_name} 
                <span style="color: {status_color}; font-size: 18px; margin-left: 15px;">{position_status}</span>
                <a href="{url}" target="_blank" style="text-decoration: none; margin-left: 10px;">
                    <span style="font-size: 20px; color: #1f77b4;">🔗</span>
                </a>
            </h2>
            <p style="margin: 5px 0; color: #666; font-size: 14px;">
                <strong>Symbol:</strong> {symbol} | <strong>Instrument id:</strong> {instrument_id} | <strong>Typ rekomendacji:</strong> {recommendation_type.title()}
            </p>
            <p style="margin: 5px 0; color: #555; font-size: 13px; font-style: italic;">
                {profile_txt}
            </p>
            <p style="margin: 5px 0; color: #555; font-size: 13px; font-style: italic;">
                {profile_description}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Key metrics in columns - adjust labels based on position status
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        profit_label = (
            "💰 Zysk/Strata" if is_position_open else "💰 Zysk/Strata (finalna)"
        )
        st.metric(
            label=profit_label,
            value=f"{profit:.2f} PLN",
            delta=f"{profit_perc:.1f}%",
            delta_color="normal",
        )

    with col2:
        if is_position_open:
            value_label = "📊 Wartość pozycji"
            value_delta = f"z {nominal_value:.2f} PLN"
        else:
            value_label = "📊 Wartość sprzedaży"
            value_delta = f"z {nominal_value:.2f} PLN"

        st.metric(
            label=value_label,
            value=f"{actual_value:.2f} PLN",
            delta=value_delta,
        )

    with col3:
        if is_position_open:
            price_label = "📈 Cena aktualna"
        else:
            price_label = "📈 Cena sprzedaży"

        st.metric(
            label=price_label,
            value=f"{close_price:.2f} PLN",
            delta=f"{((close_price - open_price) / open_price * 100):.1f}%",
        )

    with col4:
        if is_position_open:
            volume_label = "📦 Wolumen aktualny"
            volume_value = f"{actual_volume:,}"
            volume_delta = f"z {volume:,} @ {open_price:.2f} PLN"
        else:
            volume_label = "📦 Wolumen (sprzedano)"
            volume_value = f"{volume:,}"
            volume_delta = f"@ {open_price:.2f} PLN"

        st.metric(
            label=volume_label,
            value=volume_value,
            delta=volume_delta,
        )

    # Timeline section
    timeline_header = (
        "📅 Oś czasu pozycji" if is_position_open else "📅 Historia pozycji"
    )
    st.markdown(f"### {timeline_header}")

    timeline_col1, timeline_col2, timeline_col3 = st.columns(3)

    with timeline_col1:
        recommendation_ts = selected_row.get("recommendation_ts")
        if pd.notna(recommendation_ts):
            st.markdown(
                f"**🎯 Rekomendacja**  \n{recommendation_ts.strftime('%Y-%m-%d %H:%M')}"
            )
        else:
            st.markdown("**🎯 Rekomendacja**  \nBrak danych")

    with timeline_col2:
        open_time_dt = selected_row.get("open_time_dt")
        if pd.notna(open_time_dt):
            st.markdown(
                f"**🔓 Otwarcie pozycji**  \n{open_time_dt.strftime('%Y-%m-%d %H:%M')}"
            )
        else:
            st.markdown("**🔓 Otwarcie pozycji**  \nBrak danych")

    with timeline_col3:
        last_decision_ts = selected_row.get("last_decision_ts")
        if pd.notna(last_decision_ts):
            if is_position_open:
                decision_label = f"**🧠 Ostatnia decyzja ({last_decision})**"
            else:
                decision_label = f"**🔒 Zamknięcie pozycji ({last_decision})**"

            st.markdown(
                f"{decision_label}  \n{last_decision_ts.strftime('%Y-%m-%d %H:%M')}"
            )
        else:
            st.markdown("**🧠 Ostatnia decyzja**  \nBrak danych")

    # Add additional info for closed positions
    if not is_position_open:
        st.info(
            f"📋 **Pozycja zamknięta** - Wszystkie wyświetlane metryki przedstawiają finalne wyniki tej pozycji. "
            f"Wolumen został w pełni sprzedany, a zysk/strata została zrealizowana."
        )

    # Add divider
    #
    st.divider()


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
) -> go.Figure:
    """
    Create a candlestick chart with decision and order markers.

    Args:
        quotes_df: DataFrame with quote data
        decisions_df: DataFrame with decision history
        orders_df: DataFrame with order history

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


def display_history_expanders(
    decisions_df: pd.DataFrame, orders_df: pd.DataFrame, selected_row: pd.Series
) -> None:
    """
    Display expandable sections with decision and order history.

    Args:
        decisions_df: DataFrame with decision history
        orders_df: DataFrame with order history
        selected_row: Series with the selected position data
    """
    # Historia decyzji
    with st.expander("🧠 Historia decyzji (model)", expanded=False):
        if not decisions_df.empty:
            # Convert any problematic columns to string for display
            display_df = decisions_df.copy()

            # Handle explanation column specially - render as markdown
            if "explanation" in display_df.columns:
                st.subheader("📝 Szczegółowe uzasadnienia decyzji")

                for idx, row in display_df.iterrows():
                    explanation = row.get("explanation", "")
                    short_explanation = row.get("short_explanation", "")
                    decision = row.get("decision", "UNKNOWN")
                    timestamp = row.get("ins_ts", "")

                    # Create a nice header for each decision
                    st.markdown(f"### 🎯 Decyzja: **{decision}**")
                    if timestamp:
                        st.markdown(f"**📅 Czas:** {timestamp}")

                    # Render explanation as markdown if it exists
                    if (
                        explanation
                        and str(explanation).strip()
                        and str(explanation) != "nan"
                    ):
                        # Clean up the explanation text
                        cleaned_explanation = (
                            str(explanation).replace("¶", "\n\n").replace("|", "\n- ")
                        )

                        # Render as markdown
                        st.markdown("**💭 Uzasadnienie:**")
                        st.markdown(f"*{short_explanation}*")
                        st.markdown(cleaned_explanation)
                    else:
                        st.info("Brak szczegółowego uzasadnienia dla tej decyzji.")

                    # Add separator between decisions
                    if idx < len(display_df) - 1:
                        st.markdown("---")

                # Also show the dataframe without explanation column for other details
                st.subheader("📊 Tabela decyzji")
                table_df = decisions_df[
                    [
                        "decision_log_id",
                        "ins_ts",
                        "decision",
                        "actual_price",
                        "actual_volume",
                        "new_sl",
                        "new_tp",
                        "actual_sl",
                        "actual_tp",
                        "change_volume",
                    ]
                ]

                # Convert remaining columns to string for display
                for col in table_df.columns:
                    if table_df[col].dtype == "object":
                        table_df[col] = table_df[col].astype(str)

                st.dataframe(table_df)
            else:
                # No explanation column, show regular dataframe
                for col in display_df.columns:
                    if display_df[col].dtype == "object":
                        display_df[col] = display_df[col].astype(str)

                st.dataframe(display_df)
        else:
            st.info("Brak decyzji dla tej pozycji.")

    # Historia operacji
    with st.expander("📋 Historia operacji (realizacja)", expanded=False):
        if not orders_df.empty:
            # Convert any problematic columns to string for display
            display_df = orders_df.copy()
            for col in display_df.columns:
                if display_df[col].dtype == "object":
                    display_df[col] = display_df[col].astype(str)

            st.dataframe(display_df)
        else:
            st.info("Brak zrealizowanych operacji dla tej pozycji.")


def show_recommendation_selector() -> int:
    """
    Display position selector and return selected recommendation_id.

    Returns:
        int: Selected recommendation_id or None if no positions
    """
    # Load portfolio data
    positions_df = load_portfolio_data()
    if positions_df.empty:
        st.warning("Brak otwartych pozycji w portfelu.")
        return None

    # Prepare data for display
    show_df, report_cols = prepare_display_dataframe(positions_df)

    # Initialize session state for selected position index
    if "selected_position_index" not in st.session_state:
        st.session_state.selected_position_index = 0

    # Ensure selected_position_index is within valid range
    if st.session_state.selected_position_index >= len(show_df):
        st.session_state.selected_position_index = 0

    with st.expander("📊 Wybór pozycji", expanded=True):
        # Prepare AgGrid-compatible dataframe and preserve the original index
        grid_df = show_df.drop(columns=["display", "original_positions_index"]).copy()
        # Add the display index as a column to track row mapping in the grid
        grid_df["display_index"] = grid_df.index

        # Convert any problematic columns to string for display
        for col in grid_df.columns:
            if col != "display_index" and grid_df[col].dtype == "object":
                grid_df[col] = grid_df[col].astype(str)

        # Configure AgGrid with pre-selection
        gb = GridOptionsBuilder.from_dataframe(grid_df)
        gb.configure_selection(
            "single",
            use_checkbox=False,
            pre_selected_rows=[st.session_state.selected_position_index],
        )
        gb.configure_grid_options(domLayout="normal")
        # Add row styling to make it obvious the rows are clickable
        gb.configure_grid_options(rowStyle={"cursor": "pointer"})
        # Configure default column settings
        gb.configure_default_column(min_column_width=100)
        # Hide the display_index column from display
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
            key="position_grid",
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
            # Get the selected row data
            selected_row_data = selected_rows[0]

            # Use the display_index to find the correct row in show_df
            if "display_index" in selected_row_data:
                display_index = int(selected_row_data["display_index"])
                if display_index != st.session_state.selected_position_index:
                    st.session_state.selected_position_index = display_index
                    st.rerun()
            else:
                # Fallback: find by symbol
                symbol = selected_row_data.get("symbol", "")
                # Find the matching row in show_df
                for i in range(len(show_df)):
                    if show_df.iloc[i]["symbol"] == symbol:
                        if i != st.session_state.selected_position_index:
                            st.session_state.selected_position_index = i
                            st.rerun()
                        break
    except Exception as e:
        st.error(f"Error processing selection: {e}")
        logger.exception("Error processing AgGrid selection")

    # Get selected position details
    selected_display_index = st.session_state.selected_position_index

    # Ensure the index is valid before accessing the dataframe
    if selected_display_index >= len(show_df):
        selected_display_index = 0
        st.session_state.selected_position_index = 0

    selected_show_row = show_df.iloc[selected_display_index]

    # Get the original position index to access the correct row in positions_df
    original_position_index = selected_show_row["original_positions_index"]
    selected_row = positions_df.iloc[original_position_index]

    # Return the recommendation_id
    return int(selected_row["recommendation_id"])


def show_instrument_view(recommendation_id: int):
    """
    Display instrument view for a specific recommendation.

    Args:
        recommendation_id: ID of the recommendation to display
    """
    if recommendation_id is None:
        st.error("Brak recommendation_id do wyświetlenia")
        return

    # Load portfolio data and filter by recommendation_id
    positions_df = load_portfolio_data()
    if positions_df.empty:
        st.warning("Brak otwartych pozycji w portfelu.")
        return

    # Filter positions to only show the specific recommendation
    filtered_positions = positions_df[
        positions_df["recommendation_id"] == recommendation_id
    ]

    if filtered_positions.empty:
        st.error(f"Nie znaleziono pozycji dla rekomendacji ID: {recommendation_id}")
        st.info("Sprawdź czy rekomendacja istnieje lub czy ma otwarte pozycje.")
        return

    # Use the first (and likely only) position for this recommendation
    selected_row = filtered_positions.iloc[0]

    # Show info about the recommendation being displayed
    st.info(f"📌 Wyświetlanie szczegółów dla rekomendacji ID: **{recommendation_id}**")

    # Extract position details
    xtb_instrument_id = int(selected_row["xtb_instrument_id"])
    symbol = selected_row["symbol"]
    br_symbol = selected_row["br_symbol"]
    full_name = selected_row["full_name"]

    # Display position summary
    display_position_summary(selected_row)

    # Candlestick chart section
    st.subheader("Notowania i operacje")

    # Load data for charts
    recommendation_ts = selected_row.get("recommendation_ts")
    open_time_dt = selected_row.get("open_time_dt")
    close_time_dt = selected_row.get("close_time_dt")

    # Handle NaT and None values safely
    valid_recommendation_ts = None
    if recommendation_ts is not None and pd.notna(recommendation_ts):
        valid_recommendation_ts = recommendation_ts

    valid_open_time_dt = None
    if open_time_dt is not None and pd.notna(open_time_dt):
        valid_open_time_dt = open_time_dt

    # Use the earliest valid timestamp, or fallback to 7 days ago
    earliest_timestamp = None
    if valid_recommendation_ts and valid_open_time_dt:
        earliest_timestamp = min(valid_recommendation_ts, valid_open_time_dt)
    elif valid_recommendation_ts:
        earliest_timestamp = valid_recommendation_ts
    elif valid_open_time_dt:
        earliest_timestamp = valid_open_time_dt
    else:
        earliest_timestamp = pd.Timestamp.now() - pd.Timedelta(days=7)

    # Calculate days back with safety check
    days_back = (
        int((pd.Timestamp.now() - earliest_timestamp).total_seconds() / 60 / 60 / 24)
        + 5
    )  # Add 5 days buffer for better visibility

    # Ensure minimum days_back value
    days_back = max(days_back, 7)  # At least 7 days
    quotes_df = reporting.get_quotes(
        xtb_instrument_id=xtb_instrument_id, days_back=days_back
    )
    decisions_df = reporting.get_decision_history(recommendation_id, xtb_instrument_id)
    orders_df = reporting.get_orders(xtb_instrument_id, recommendation_id)
    reco = reporting.get_recommendation(recommendation_id, xtb_instrument_id)

    if quotes_df.empty:
        st.warning("Brak notowań instrumentu.")
    else:
        # Create and display chart
        try:
            fig = create_candlestick_chart(
                reco, quotes_df, decisions_df, orders_df, close_time_dt
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating chart: {e}")
            logger.exception("Error creating candlestick chart")

    # Show recommendation details
    display_recommendation(recommendation_id, xtb_instrument_id)

    # Display history expanders
    display_history_expanders(decisions_df, orders_df, selected_row)


def show_instrument_management_view():
    """
    Combined view that shows position selector and instrument details.
    This is the main entry point for the instrument management interface.
    """
    # App title
    st.title("Panel inwestora")

    # Check if recommendation_id is provided via URL
    query_params = st.query_params
    url_recommendation_id = None

    if "recommendation_id" in query_params:
        try:
            url_recommendation_id = int(query_params["recommendation_id"])
            # If URL has recommendation_id, go directly to instrument view
            show_instrument_view(url_recommendation_id)
            return
        except (ValueError, TypeError):
            st.error("Nieprawidłowy format recommendation_id w URL")
            return

    # Check if recommendation_id is provided via session state (from portfolio view)
    if "selected_recommendation_id" in st.session_state:
        selected_rec_id = st.session_state.selected_recommendation_id
        # Clear the session state to prevent repeated redirects
        del st.session_state.selected_recommendation_id
        show_instrument_view(selected_rec_id)
        return

    # Normal flow: show selector and then details
    selected_recommendation_id = show_recommendation_selector()

    if selected_recommendation_id is not None:
        st.divider()
        show_instrument_view(selected_recommendation_id)
