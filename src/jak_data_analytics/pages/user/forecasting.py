"""
JAK Data Analytics
Forecasting Module

Features:
- Automatic date column detection
- Date and numerical variable selection
- Data frequency configuration
- Historical trend analysis
- Naive forecasting
- Moving average forecasting
- Exponential smoothing
- ARIMA forecasting
- Forecast evaluation
- Interactive forecast visualisation
- Forecast result downloads

Forecasting results are estimates, not guarantees.
"""

import hashlib

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
)

from ...ui.layout import (
    render_topbar,
    render_page_intro,
    render_section_heading,
)

from ...ui.theme import show_footer


# =========================================================
# SESSION STATE
# =========================================================

def initialize_forecasting_state():

    defaults = {
        "jak_forecasting_results": None,
        "jak_latest_forecast": None,
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


# =========================================================
# DATASET RETRIEVAL
# =========================================================

def get_datasets():

    datasets = st.session_state.get(
        "jak_datasets",
        []
    )

    if not isinstance(datasets, list):
        return []

    return [
        item for item in datasets
        if (
            isinstance(item, dict)
            and isinstance(item.get("data"), pd.DataFrame)
            and not item["data"].empty
        )
    ]


def render_dataset_selector():

    datasets = get_datasets()

    if not datasets:

        st.warning(
            "No valid datasets are available. Upload a dataset first."
        )

        return None, None

    options = {}

    for index, item in enumerate(datasets):

        name = str(
            item.get("name") or f"Dataset {index + 1}"
        )

        display_name = name

        if display_name in options:
            display_name = f"{name} ({index + 1})"

        options[display_name] = item

    selected_name = st.selectbox(
        "Select Dataset",
        list(options.keys()),
        key="jak_forecasting_dataset",
    )

    return options[selected_name], selected_name


# =========================================================
# DATASET FINGERPRINT
# =========================================================

def get_dataset_fingerprint(data):

    try:

        values_hash = pd.util.hash_pandas_object(
            data,
            index=True,
        ).values.tobytes()

        return hashlib.sha256(
            values_hash
        ).hexdigest()

    except Exception:

        return hashlib.sha256(
            str(data.shape).encode("utf-8")
        ).hexdigest()


# =========================================================
# DATE COLUMN DETECTION
# =========================================================

def detect_date_columns(data):
    """
    Identify columns containing dates.

    Supports:
    - pandas datetime columns
    - date strings
    - timestamp strings
    """

    candidates = []

    for column in data.columns:

        values = data[column].dropna()

        if values.empty:
            continue

        if pd.api.types.is_datetime64_any_dtype(
            data[column]
        ):

            candidates.append(column)
            continue

        # Numeric columns are not automatically interpreted
        # as dates because ordinary measurements could be
        # mistaken for Unix timestamps.
        if pd.api.types.is_numeric_dtype(
            data[column]
        ):
            continue

        try:

            parsed = pd.to_datetime(
                values.astype(str),
                errors="coerce",
                format="mixed",
            )

            valid_ratio = parsed.notna().mean()

            if (
                valid_ratio >= 0.70
                and parsed.nunique() >= 3
            ):

                candidates.append(column)

        except (ValueError, TypeError):

            continue

    return candidates


# =========================================================
# FORECASTING HERO
# =========================================================

def render_forecasting_hero():

    with st.container(border=True):

        st.caption("JAK ANALYTICS INTELLIGENCE")

        st.subheader(
            "📈 Forecasting Intelligence Studio"
        )

        st.write(
            """
            Discover historical patterns, analyse trends and
            estimate future values using statistical time
            series forecasting techniques.
            """
        )


# =========================================================
# DATASET OVERVIEW
# =========================================================

def render_dataset_overview(data):

    date_count = len(
        detect_date_columns(data)
    )

    numeric_count = len(
        data.select_dtypes(
            include="number"
        ).columns
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Records",
        f"{len(data):,}"
    )

    col2.metric(
        "Total Columns",
        len(data.columns)
    )

    col3.metric(
        "Date Columns",
        date_count
    )

    col4.metric(
        "Numeric Columns",
        numeric_count
    )


# =========================================================
# TIME SERIES SETTINGS
# =========================================================

def render_time_series_settings(data):

    render_section_heading(
        "Time Series Configuration",
        "Identify the date and numerical variable you want to forecast."
    )

    date_options = detect_date_columns(data)

    if not date_options:

        st.warning(
            """
            JAK could not automatically identify a date column.

            Select a column containing valid dates manually.
            Your dataset must have a date or time column to
            perform time-series forecasting.
            """
        )

        date_options = data.columns.tolist()

    if not date_options:

        st.error("No columns are available.")

        return None

    col1, col2 = st.columns(2)

    with col1:

        date_column = st.selectbox(
            "Date / Time Column",
            date_options,
            key="jak_forecasting_date_column",
        )

    # Exclude the selected date column from numerical options.
    numeric_options = [
        column
        for column in data.select_dtypes(
            include="number"
        ).columns.tolist()
        if column != date_column
    ]

    # Also allow numeric-looking text measurements.
    # Only columns that can be converted to numbers are included.
    for column in data.columns:

        if column == date_column:
            continue

        if column in numeric_options:
            continue

        converted = pd.to_numeric(
            data[column],
            errors="coerce",
        )

        if converted.notna().sum() >= 3:

            numeric_options.append(column)

    if not numeric_options:

        st.error(
            "No numerical variable is available apart from "
            "the selected date column. Add a numerical "
            "measurement such as rainfall, temperature, "
            "humidity or crop yield."
        )

        return None

    with col2:

        value_column = st.selectbox(
            "Variable to Forecast",
            numeric_options,
            key="jak_forecasting_value_column",
        )

    if date_column == value_column:

        st.error(
            "The date and numerical columns must be different."
        )

        return None

    col3, col4 = st.columns(2)

    with col3:

        frequency_options = {
            "Daily": "D",
            "Weekly": "W",
            "Monthly": "MS",
            "Quarterly": "QS",
            "Yearly": "YS",
        }

        frequency_name = st.selectbox(
            "Time Frequency",
            list(frequency_options.keys()),
            index=2,
            key="jak_forecasting_frequency",
        )

        frequency = frequency_options[frequency_name]

    with col4:

        aggregation = st.selectbox(
            "Aggregation Method",
            [
                "Mean",
                "Sum",
                "Maximum",
                "Minimum",
            ],
            key="jak_forecasting_aggregation",
        )

    return {
        "date_column": date_column,
        "value_column": value_column,
        "frequency": frequency,
        "frequency_name": frequency_name,
        "aggregation": aggregation,
    }


# =========================================================
# TIME SERIES PREPARATION
# =========================================================

def prepare_time_series(
    data,
    date_column,
    value_column,
    frequency,
    aggregation,
):

    if date_column not in data.columns:

        raise ValueError(
            "The selected date column does not exist."
        )

    if value_column not in data.columns:

        raise ValueError(
            "The selected numerical column does not exist."
        )

    if date_column == value_column:

        raise ValueError(
            "Select different columns for date and numerical values."
        )

    working = data[
        [date_column, value_column]
    ].copy()

    working[date_column] = pd.to_datetime(
        working[date_column],
        errors="coerce",
        format="mixed",
    )

    working[value_column] = pd.to_numeric(
        working[value_column],
        errors="coerce",
    )

    working = working.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    working = working.dropna(
        subset=[
            date_column,
            value_column,
        ]
    )

    if working.empty:

        raise ValueError(
            "No valid date and numerical values were found. "
            "Check your selected columns."
        )

    working = working.sort_values(
        date_column
    )

    working = working.set_index(
        date_column
    )

    if aggregation == "Sum":

        series = working[value_column].resample(
            frequency
        ).sum(min_count=1)

    elif aggregation == "Maximum":

        series = working[value_column].resample(
            frequency
        ).max()

    elif aggregation == "Minimum":

        series = working[value_column].resample(
            frequency
        ).min()

    else:

        series = working[value_column].resample(
            frequency
        ).mean()

    series = series.replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()

    if len(series) < 8:

        raise ValueError(
            f"Only {len(series)} valid time periods were found. "
            "At least 8 periods are required for forecasting. "
            "Try a different frequency or use more historical data."
        )

    if not isinstance(
        series.index,
        pd.DatetimeIndex,
    ):

        raise ValueError(
            "The prepared time series must have a valid date index."
        )

    if not np.isfinite(
        series.to_numpy(dtype=float)
    ).all():

        raise ValueError(
            "The prepared time series contains invalid values."
        )

    return series.astype(float)


# =========================================================
# HISTORICAL ANALYSIS
# =========================================================

def render_historical_analysis(series):

    render_section_heading(
        "Historical Data Analysis",
        "Review historical values before generating forecasts."
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Observations",
        f"{len(series):,}",
    )

    col2.metric(
        "Average",
        f"{series.mean():,.2f}",
    )

    col3.metric(
        "Minimum",
        f"{series.min():,.2f}",
    )

    col4.metric(
        "Maximum",
        f"{series.max():,.2f}",
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=series.index,
            y=series.values,
            mode="lines",
            name="Historical Values",
        )
    )

    fig.update_layout(
        title="Historical Time Series",
        xaxis_title="Date",
        yaxis_title="Value",
        height=420,
        template="plotly_white",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    with st.expander("View Historical Data"):

        historical = series.rename(
            "Value"
        ).reset_index()

        st.dataframe(
            historical,
            use_container_width=True,
            hide_index=True,
        )


# =========================================================
# NAIVE FORECASTING
# =========================================================

def naive_forecast(train, periods):

    last_value = float(train.iloc[-1])

    return np.repeat(
        last_value,
        periods,
    )


# =========================================================
# MOVING AVERAGE FORECASTING
# =========================================================

def moving_average_forecast(
    train,
    periods,
    window,
):

    if window < 1:

        raise ValueError(
            "Moving average window must be positive."
        )

    if len(train) < window:

        raise ValueError(
            "The historical dataset is too small "
            "for the selected moving average window."
        )

    history = list(
        train.astype(float)
    )

    predictions = []

    for _ in range(periods):

        next_value = float(
            np.mean(history[-window:])
        )

        predictions.append(next_value)

        history.append(next_value)

    return np.asarray(
        predictions,
        dtype=float,
    )


# =========================================================
# EXPONENTIAL SMOOTHING
# =========================================================

def exponential_smoothing_forecast(
    train,
    periods,
    seasonal_periods=0,
):

    if len(train) < 4:

        raise ValueError(
            "Not enough observations for exponential smoothing."
        )

    if seasonal_periods:

        if len(train) < seasonal_periods * 2:

            raise ValueError(
                "Seasonal exponential smoothing requires "
                "at least two complete seasonal cycles."
            )

        model = ExponentialSmoothing(
            train,
            trend="add",
            seasonal="add",
            seasonal_periods=seasonal_periods,
            initialization_method="estimated",
        )

    else:

        model = ExponentialSmoothing(
            train,
            trend="add",
            initialization_method="estimated",
        )

    fitted = model.fit(
        optimized=True
    )

    forecast = fitted.forecast(
        periods
    )

    return np.asarray(
        forecast,
        dtype=float,
    )


# =========================================================
# ARIMA FORECASTING
# =========================================================

def arima_forecast(
    train,
    periods,
    order,
):

    model = ARIMA(
        train,
        order=order,
    )

    fitted = model.fit()

    forecast = fitted.forecast(
        steps=periods
    )

    return np.asarray(
        forecast,
        dtype=float,
    )


# =========================================================
# FORECAST ENGINE
# =========================================================

def generate_forecast(
    series,
    model_name,
    forecast_periods,
    seasonal_periods=0,
    moving_window=3,
    arima_order=(1, 1, 1),
):

    if len(series) < 8:

        raise ValueError(
            "At least 8 observations are required."
        )

    if forecast_periods < 1:

        raise ValueError(
            "Forecast period must be at least 1."
        )

    if not np.isfinite(
        series.to_numpy(dtype=float)
    ).all():

        raise ValueError(
            "The time series contains invalid numerical values."
        )

    test_count = max(
        1,
        int(len(series) * 0.2),
    )

    train = series.iloc[:-test_count]

    test = series.iloc[-test_count:]

    if len(train) < 5:

        raise ValueError(
            "Not enough historical observations for evaluation."
        )

    def run_model(training_data, periods):

        if model_name == "Naive Forecast":

            return naive_forecast(
                training_data,
                periods,
            )

        if model_name == "Moving Average":

            return moving_average_forecast(
                training_data,
                periods,
                moving_window,
            )

        if model_name == "Exponential Smoothing":

            return exponential_smoothing_forecast(
                training_data,
                periods,
                seasonal_periods,
            )

        if model_name == "ARIMA":

            return arima_forecast(
                training_data,
                periods,
                arima_order,
            )

        raise ValueError(
            "Unknown forecasting model."
        )

    # Evaluate using the most recent historical observations.
    test_predictions = run_model(
        train,
        len(test),
    )

    if not np.isfinite(test_predictions).all():

        raise ValueError(
            "The model generated invalid evaluation predictions."
        )

    mae = mean_absolute_error(
        test.to_numpy(),
        test_predictions,
    )

    rmse = np.sqrt(
        mean_squared_error(
            test.to_numpy(),
            test_predictions,
        )
    )

    # Refit using all available historical data.
    future_values = run_model(
        series,
        forecast_periods,
    )

    if not np.isfinite(future_values).all():

        raise ValueError(
            "The model generated invalid future forecast values."
        )

    return {
        "future_values": future_values,
        "test_predictions": test_predictions,
        "actual_test": test,
        "train": train,
        "test": test,
        "mae": float(mae),
        "rmse": float(rmse),
        "model_name": model_name,
    }


# =========================================================
# FUTURE DATE GENERATION
# =========================================================

def create_future_index(
    series,
    periods,
    frequency,
):

    return pd.date_range(
        start=series.index[-1],
        periods=periods + 1,
        freq=frequency,
    )[1:]


# =========================================================
# FORECAST RESULTS
# =========================================================

def render_forecast_results(
    series,
    results,
    frequency,
):

    render_section_heading(
        "Forecast Results",
        "Review the forecast and model evaluation."
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Forecasting Model",
        results["model_name"],
    )

    col2.metric(
        "Mean Absolute Error",
        f"{results['mae']:,.3f}",
    )

    col3.metric(
        "Root Mean Squared Error",
        f"{results['rmse']:,.3f}",
    )

    future_index = create_future_index(
        series,
        len(results["future_values"]),
        frequency,
    )

    forecast_series = pd.Series(
        results["future_values"],
        index=future_index,
        name="Forecast",
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=series.index,
            y=series.values,
            mode="lines",
            name="Historical Data",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=forecast_series.index,
            y=forecast_series.values,
            mode="lines+markers",
            name="Forecast",
        )
    )

    fig.add_vline(
        x=series.index[-1],
        line_dash="dash",
        annotation_text="Forecast Starts",
    )

    fig.update_layout(
        title="Historical Data and Future Forecast",
        xaxis_title="Date",
        yaxis_title="Forecasted Value",
        height=480,
        template="plotly_white",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    render_section_heading(
        "Forecasted Values",
        "Estimated values for the selected future periods."
    )

    forecast_table = forecast_series.reset_index()

    forecast_table.columns = [
        "Date",
        "Forecasted Value",
    ]

    st.dataframe(
        forecast_table,
        use_container_width=True,
        hide_index=True,
    )

    csv_data = forecast_table.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "⬇️ Download Forecast Results",
        data=csv_data,
        file_name="jak_forecast_results.csv",
        mime="text/csv",
        key="jak_download_forecast",
    )

    st.session_state["jak_latest_forecast"] = {
        "model": results["model_name"],
        "forecast": forecast_table,
        "mae": results["mae"],
        "rmse": results["rmse"],
    }


# =========================================================
# FORECASTING CONFIGURATION
# =========================================================

def render_forecasting_configuration(series):

    render_section_heading(
        "Forecasting Configuration",
        "Choose the forecasting technique and prediction period."
    )

    model_name = st.selectbox(
        "Forecasting Algorithm",
        [
            "Naive Forecast",
            "Moving Average",
            "Exponential Smoothing",
            "ARIMA",
        ],
        key="jak_forecasting_model",
    )

    forecast_periods = st.number_input(
        "Number of Future Periods",
        min_value=1,
        max_value=365,
        value=12,
        key="jak_forecasting_periods",
    )

    moving_window = 3
    seasonal_periods = 0
    arima_order = (1, 1, 1)

    if model_name == "Moving Average":

        maximum_window = min(
            24,
            len(series) - 1,
        )

        moving_window = st.slider(
            "Moving Average Window",
            min_value=2,
            max_value=maximum_window,
            value=min(3, maximum_window),
            key="jak_moving_average_window",
        )

    elif model_name == "Exponential Smoothing":

        use_seasonality = st.checkbox(
            "Use Seasonal Forecasting",
            value=False,
            key="jak_use_seasonality",
        )

        if use_seasonality:

            maximum_season = min(
                24,
                len(series) // 2,
            )

            seasonal_periods = st.number_input(
                "Periods per Seasonal Cycle",
                min_value=2,
                max_value=maximum_season,
                value=min(12, maximum_season),
                key="jak_seasonal_periods",
            )

            seasonal_periods = int(seasonal_periods)

    elif model_name == "ARIMA":

        col1, col2, col3 = st.columns(3)

        with col1:

            p = st.number_input(
                "AR Order (p)",
                min_value=0,
                max_value=5,
                value=1,
                key="jak_arima_p",
            )

        with col2:

            d = st.number_input(
                "Differencing (d)",
                min_value=0,
                max_value=2,
                value=1,
                key="jak_arima_d",
            )

        with col3:

            q = st.number_input(
                "MA Order (q)",
                min_value=0,
                max_value=5,
                value=1,
                key="jak_arima_q",
            )

        arima_order = (
            int(p),
            int(d),
            int(q),
        )

    return {
        "model_name": model_name,
        "forecast_periods": int(forecast_periods),
        "moving_window": int(moving_window),
        "seasonal_periods": int(seasonal_periods),
        "arima_order": arima_order,
    }


# =========================================================
# FORECASTING LIMITATIONS
# =========================================================

def render_forecasting_guidance():

    with st.container(border=True):

        st.warning(
            """
            Forecasting Limitations

            Forecasts depend on historical patterns. Sudden
            market changes, unusual events, missing records,
            seasonal changes and structural breaks can reduce
            accuracy.

            Forecasts should be validated before being used
            for important decisions.
            """
        )


# =========================================================
# MAIN FORECASTING PAGE
# =========================================================

def render_forecasting_page():

    initialize_forecasting_state()

    username = st.session_state.get(
        "jak_user_name",
        "Guest",
    )

    role = st.session_state.get(
        "jak_user_role",
        "User",
    )

    render_topbar(
        username=username,
        role=role,
    )

    render_page_intro(
        "Forecasting",
        "Analyse historical trends and estimate future outcomes.",
    )

    render_forecasting_hero()

    selected_dataset, dataset_name = render_dataset_selector()

    if selected_dataset is None:

        show_footer()
        return

    data = selected_dataset["data"].copy()

    if data.empty:

        st.warning(
            "The selected dataset is empty."
        )

        show_footer()
        return

    dataset_fingerprint = get_dataset_fingerprint(data)

    st.divider()

    render_dataset_overview(data)

    st.divider()

    settings = render_time_series_settings(data)

    if settings is None:

        show_footer()
        return

    try:

        series = prepare_time_series(
            data,
            settings["date_column"],
            settings["value_column"],
            settings["frequency"],
            settings["aggregation"],
        )

    except Exception as error:

        st.error(
            f"Unable to prepare the time series: {error}"
        )

        show_footer()
        return

    st.divider()

    render_historical_analysis(series)

    st.divider()

    configuration = render_forecasting_configuration(series)

    render_forecasting_guidance()

    current_signature = (
        dataset_name,
        dataset_fingerprint,
        settings["date_column"],
        settings["value_column"],
        settings["frequency"],
        settings["aggregation"],
        configuration["model_name"],
        configuration["forecast_periods"],
        configuration["moving_window"],
        configuration["seasonal_periods"],
        configuration["arima_order"],
    )

    saved = st.session_state.get(
        "jak_forecasting_results"
    )

    if (
        isinstance(saved, dict)
        and saved.get("signature") != current_signature
    ):

        st.session_state["jak_forecasting_results"] = None
        saved = None

    if st.button(
        "🚀 Generate Forecast",
        use_container_width=True,
        type="primary",
        key="jak_generate_forecast",
    ):

        try:

            with st.spinner(
                "JAK is analysing historical patterns and generating forecasts..."
            ):

                results = generate_forecast(
                    series=series,
                    model_name=configuration["model_name"],
                    forecast_periods=configuration["forecast_periods"],
                    seasonal_periods=configuration["seasonal_periods"],
                    moving_window=configuration["moving_window"],
                    arima_order=configuration["arima_order"],
                )

            st.session_state["jak_forecasting_results"] = {
                "signature": current_signature,
                "dataset": dataset_name,
                "date_column": settings["date_column"],
                "value_column": settings["value_column"],
                "frequency": settings["frequency"],
                "aggregation": settings["aggregation"],
                "series": series,
                "results": results,
            }

            st.success(
                "Forecast generated successfully!"
            )

            st.rerun()

        except Exception as error:

            st.error(
                f"Forecasting failed: {error}"
            )

    saved = st.session_state.get(
        "jak_forecasting_results"
    )

    if (
        isinstance(saved, dict)
        and saved.get("signature") == current_signature
    ):

        st.divider()

        render_forecast_results(
            saved["series"],
            saved["results"],
            saved["frequency"],
        )

    show_footer()


# =========================================================
# NAVIGATION COMPATIBILITY
# =========================================================

render_forecasting = render_forecasting_page
