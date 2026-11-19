"""
JAK Data Analytics
Forecasting Service

Provides reusable time-series forecasting functionality.

Features:
- Time-series preparation
- Data aggregation
- Naive forecasting
- Moving average forecasting
- Exponential smoothing
- Holt trend forecasting
- Seasonal forecasting
- ARIMA forecasting
- Forecast evaluation
- Future predictions
- Confidence intervals

This module does not depend on Streamlit.
"""

import warnings

import numpy as np
import pandas as pd

from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
)


# ==================================================
# VALIDATION
# ==================================================

def validate_dataframe(data):
    """Validate input dataset."""

    if not isinstance(data, pd.DataFrame):
        raise TypeError(
            "Input must be a pandas DataFrame."
        )

    if data.empty:
        raise ValueError(
            "The dataset is empty."
        )

    return True


def validate_series(series):
    """Validate numerical time-series values."""

    values = pd.to_numeric(
        pd.Series(series),
        errors="coerce"
    )

    values = values.replace(
        [np.inf, -np.inf],
        np.nan
    ).dropna()

    if len(values) < 3:
        raise ValueError(
            "At least three valid observations are required."
        )

    return values.astype(float)


def validate_forecast_periods(periods):
    """Validate forecast horizon."""

    if not isinstance(periods, int) or isinstance(periods, bool):
        raise ValueError(
            "Forecast periods must be an integer."
        )

    if not 1 <= periods <= 10000:
        raise ValueError(
            "Forecast periods must be between 1 and 10000."
        )


# ==================================================
# PREPARE TIME SERIES
# ==================================================

def prepare_time_series(
    data,
    date_column,
    value_column,
    frequency=None,
    aggregation="sum",
):
    """
    Prepare a dataset for time-series forecasting.

    Supported aggregations:
    - sum
    - mean
    - median
    - min
    - max
    - count
    """

    validate_dataframe(data)

    if date_column not in data.columns:
        raise ValueError(
            f"Unknown date column: {date_column}"
        )

    if value_column not in data.columns:
        raise ValueError(
            f"Unknown value column: {value_column}"
        )

    allowed = [
        "sum",
        "mean",
        "median",
        "min",
        "max",
        "count",
    ]

    if aggregation not in allowed:
        raise ValueError(
            "Unsupported aggregation method."
        )

    cleaned = data[
        [date_column, value_column]
    ].copy()

    cleaned[date_column] = pd.to_datetime(
        cleaned[date_column],
        errors="coerce"
    )

    cleaned[value_column] = pd.to_numeric(
        cleaned[value_column],
        errors="coerce"
    )

    cleaned = cleaned.replace(
        [np.inf, -np.inf],
        np.nan
    ).dropna()

    if cleaned.empty:
        raise ValueError(
            "No valid date and numerical observations were found."
        )

    cleaned = cleaned.sort_values(
        date_column
    )

    cleaned = cleaned.set_index(
        date_column
    )

    if frequency:

        if aggregation == "count":
            result = cleaned.resample(
                frequency
            )[value_column].count()

        else:
            result = getattr(
                cleaned.resample(frequency)[value_column],
                aggregation
            )()

    else:
        result = cleaned.groupby(
            level=0
        )[value_column].agg(
            aggregation
        )

    result = result.dropna()

    if len(result) < 3:
        raise ValueError(
            "At least three time periods are required after aggregation."
        )

    return result.astype(float)


# ==================================================
# FORECAST METRICS
# ==================================================

def calculate_forecast_metrics(
    actual,
    predicted,
):
    """Calculate forecasting evaluation metrics."""

    actual = np.asarray(
        actual,
        dtype=float
    )

    predicted = np.asarray(
        predicted,
        dtype=float
    )

    if len(actual) != len(predicted):
        raise ValueError(
            "Actual and predicted values must have equal lengths."
        )

    valid = (
        np.isfinite(actual)
        & np.isfinite(predicted)
    )

    actual = actual[valid]
    predicted = predicted[valid]

    if len(actual) == 0:
        raise ValueError(
            "No valid observations are available for evaluation."
        )

    mse = mean_squared_error(
        actual,
        predicted
    )

    nonzero = actual != 0

    mape = (
        float(
            np.mean(
                np.abs(
                    (actual[nonzero] - predicted[nonzero])
                    / actual[nonzero]
                )
            ) * 100
        )
        if nonzero.any()
        else None
    )

    return {
        "mae": float(
            mean_absolute_error(
                actual,
                predicted
            )
        ),
        "mse": float(mse),
        "rmse": float(
            np.sqrt(mse)
        ),
        "mape": mape,
        "observations": len(actual),
    }


# ==================================================
# NAIVE FORECAST
# ==================================================

def naive_forecast(
    series,
    periods=12,
):
    """Forecast future values using the last observation."""

    values = validate_series(series)

    validate_forecast_periods(periods)

    forecast = np.repeat(
        values.iloc[-1],
        periods
    )

    return pd.Series(
        forecast,
        name="forecast"
    )


# ==================================================
# MOVING AVERAGE FORECAST
# ==================================================

def moving_average_forecast(
    series,
    periods=12,
    window=3,
):
    """Forecast using a rolling average of recent observations."""

    values = validate_series(series)

    validate_forecast_periods(periods)

    if not isinstance(window, int) or isinstance(window, bool):
        raise ValueError(
            "Window must be an integer."
        )

    if not 1 <= window <= len(values):
        raise ValueError(
            "Window must be between 1 and the number of observations."
        )

    average = values.tail(
        window
    ).mean()

    forecast = np.repeat(
        average,
        periods
    )

    return pd.Series(
        forecast,
        name="forecast"
    )


# ==================================================
# EXPONENTIAL SMOOTHING
# ==================================================

def exponential_smoothing_forecast(
    series,
    periods=12,
    trend=None,
    seasonal=None,
    seasonal_periods=None,
):
    """
    Forecast using Holt-Winters exponential smoothing.

    trend:
    - None
    - add
    - mul

    seasonal:
    - None
    - add
    - mul
    """

    values = validate_series(series)

    validate_forecast_periods(periods)

    if trend not in [None, "add", "mul"]:
        raise ValueError(
            "Trend must be None, 'add' or 'mul'."
        )

    if seasonal not in [None, "add", "mul"]:
        raise ValueError(
            "Seasonal must be None, 'add' or 'mul'."
        )

    if seasonal is not None:

        if seasonal_periods is None:
            raise ValueError(
                "Seasonal periods must be provided."
            )

        if not isinstance(seasonal_periods, int):
            raise ValueError(
                "Seasonal periods must be an integer."
            )

        if seasonal_periods < 2:
            raise ValueError(
                "Seasonal periods must be at least 2."
            )

        if len(values) < seasonal_periods * 2:
            raise ValueError(
                "At least two complete seasonal cycles are required."
            )

    if seasonal == "mul" and (values <= 0).any():
        raise ValueError(
            "Multiplicative seasonality requires positive values."
        )

    if trend == "mul" and (values <= 0).any():
        raise ValueError(
            "Multiplicative trend requires positive values."
        )

    model = ExponentialSmoothing(
        values,
        trend=trend,
        seasonal=seasonal,
        seasonal_periods=seasonal_periods,
        initialization_method="estimated",
    )

    fitted = model.fit(
        optimized=True
    )

    forecast = fitted.forecast(
        periods
    )

    return {
        "model": fitted,
        "forecast": forecast.rename("forecast"),
        "fitted_values": fitted.fittedvalues,
    }


# ==================================================
# ARIMA FORECAST
# ==================================================

def arima_forecast(
    series,
    periods=12,
    order=(1, 1, 1),
):
    """
    Forecast using ARIMA.

    Order format:
    (p, d, q)
    """

    values = validate_series(series)

    validate_forecast_periods(periods)

    if (
        not isinstance(order, (tuple, list))
        or len(order) != 3
        or any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
            for value in order
        )
    ):
        raise ValueError(
            "ARIMA order must contain three non-negative integers."
        )

    if sum(order) == 0:
        raise ValueError(
            "At least one ARIMA order parameter must be greater than zero."
        )

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        model = ARIMA(
            values,
            order=tuple(order)
        )

        fitted = model.fit()

        prediction = fitted.get_forecast(
            steps=periods
        )

        forecast = prediction.predicted_mean

        intervals = prediction.conf_int()

    return {
        "model": fitted,
        "forecast": forecast.rename("forecast"),
        "lower_bound": intervals.iloc[:, 0],
        "upper_bound": intervals.iloc[:, 1],
    }


# ==================================================
# TRAIN AND TEST SPLIT
# ==================================================

def time_series_train_test_split(
    series,
    test_size=0.2,
):
    """Split time-series data without random shuffling."""

    values = validate_series(series)

    if not 0.05 <= test_size <= 0.5:
        raise ValueError(
            "Test size must be between 0.05 and 0.5."
        )

    split_index = int(
        len(values) * (1 - test_size)
    )

    if split_index < 2:
        raise ValueError(
            "Not enough observations for training."
        )

    if len(values) - split_index < 1:
        raise ValueError(
            "Not enough observations for testing."
        )

    return (
        values.iloc[:split_index].copy(),
        values.iloc[split_index:].copy(),
    )


# ==================================================
# EVALUATE NAIVE FORECAST
# ==================================================

def evaluate_naive_forecast(
    series,
    test_size=0.2,
):
    """Evaluate naive forecasting on a chronological holdout."""

    train, test = time_series_train_test_split(
        series,
        test_size
    )

    predictions = np.repeat(
        train.iloc[-1],
        len(test)
    )

    return {
        "model": "Naive Forecast",
        "metrics": calculate_forecast_metrics(
            test.values,
            predictions
        ),
        "actual": test,
        "predicted": pd.Series(
            predictions,
            index=test.index,
            name="predicted"
        ),
    }


# ==================================================
# EVALUATE MOVING AVERAGE
# ==================================================

def evaluate_moving_average(
    series,
    window=3,
    test_size=0.2,
):
    """Evaluate moving average using walk-forward predictions."""

    values = validate_series(series)

    train, test = time_series_train_test_split(
        values,
        test_size
    )

    if not isinstance(window, int) or isinstance(window, bool):
        raise ValueError(
            "Window must be an integer."
        )

    if not 1 <= window <= len(train):
        raise ValueError(
            "Window must be between 1 and the training size."
        )

    history = list(train.values)
    predictions = []

    for _ in range(len(test)):

        prediction = np.mean(
            history[-window:]
        )

        predictions.append(
            prediction
        )

        history.append(
            prediction
        )

    predicted = pd.Series(
        predictions,
        index=test.index,
        name="predicted"
    )

    return {
        "model": "Moving Average",
        "metrics": calculate_forecast_metrics(
            test.values,
            predicted.values
        ),
        "actual": test,
        "predicted": predicted,
    }


# ==================================================
# EVALUATE EXPONENTIAL SMOOTHING
# ==================================================

def evaluate_exponential_smoothing(
    series,
    trend=None,
    seasonal=None,
    seasonal_periods=None,
    test_size=0.2,
):
    """Evaluate exponential smoothing on a chronological holdout."""

    train, test = time_series_train_test_split(
        series,
        test_size
    )

    if seasonal is not None:

        if seasonal_periods is None:
            raise ValueError(
                "Seasonal periods must be provided."
            )

        if len(train) < seasonal_periods * 2:
            raise ValueError(
                "Training data must contain at least two complete seasonal cycles."
            )

    result = exponential_smoothing_forecast(
        train,
        periods=len(test),
        trend=trend,
        seasonal=seasonal,
        seasonal_periods=seasonal_periods,
    )

    predicted = result["forecast"]

    predicted.index = test.index

    return {
        "model": "Exponential Smoothing",
        "metrics": calculate_forecast_metrics(
            test.values,
            predicted.values
        ),
        "actual": test,
        "predicted": predicted,
        "fitted_model": result["model"],
    }


# ==================================================
# EVALUATE ARIMA
# ==================================================

def evaluate_arima(
    series,
    order=(1, 1, 1),
    test_size=0.2,
):
    """Evaluate ARIMA using chronological holdout data."""

    train, test = time_series_train_test_split(
        series,
        test_size
    )

    result = arima_forecast(
        train,
        periods=len(test),
        order=order,
    )

    predicted = result["forecast"]

    predicted.index = test.index

    return {
        "model": "ARIMA",
        "metrics": calculate_forecast_metrics(
            test.values,
            predicted.values
        ),
        "actual": test,
        "predicted": predicted,
        "fitted_model": result["model"],
    }


# ==================================================
# GENERATE FUTURE DATE INDEX
# ==================================================

def generate_future_index(
    series,
    periods,
    frequency=None,
):
    """Generate future dates using the time-series frequency."""

    validate_forecast_periods(periods)

    if not isinstance(series.index, pd.DatetimeIndex):
        raise ValueError(
            "Time series must have a DatetimeIndex."
        )

    inferred = frequency or getattr(
        series.index,
        "freqstr",
        None
    )

    if inferred is None:
        inferred = pd.infer_freq(
            series.index
        )

    if inferred is None:
        raise ValueError(
            "Could not determine time frequency. Supply a frequency such as D, W, MS or QS."
        )

    return pd.date_range(
        start=series.index[-1],
        periods=periods + 1,
        freq=inferred
    )[1:]


# ==================================================
# BUILD FORECAST TABLE
# ==================================================

def build_forecast_table(
    series,
    forecast,
    lower_bound=None,
    upper_bound=None,
):
    """Combine historical and forecast values into one table."""

    if not isinstance(series, pd.Series):
        raise TypeError(
            "Historical data must be a pandas Series."
        )

    if not isinstance(forecast, pd.Series):
        forecast = pd.Series(
            forecast
        )

    historical = pd.DataFrame({
        "date": series.index,
        "value": series.values,
        "type": "Historical",
    })

    future = pd.DataFrame({
        "date": forecast.index,
        "value": forecast.values,
        "type": "Forecast",
    })

    if lower_bound is not None:
        future["lower_bound"] = np.asarray(
            lower_bound
        )

    if upper_bound is not None:
        future["upper_bound"] = np.asarray(
            upper_bound
        )

    return pd.concat(
        [historical, future],
        ignore_index=True
    )


# ==================================================
# COMPARE FORECASTING MODELS
# ==================================================

def compare_forecasting_models(
    series,
    test_size=0.2,
):
    """Compare supported baseline forecasting models."""

    results = []

    methods = [
        ("Naive Forecast", evaluate_naive_forecast),
        ("Moving Average", evaluate_moving_average),
        ("Exponential Smoothing", evaluate_exponential_smoothing),
        ("ARIMA", evaluate_arima),
    ]

    for name, function in methods:

        try:

            result = function(
                series,
                test_size=test_size
            )

            results.append({
                "model": name,
                **result["metrics"],
                "status": "Success",
            })

        except Exception as error:

            results.append({
                "model": name,
                "mae": None,
                "mse": None,
                "rmse": None,
                "mape": None,
                "observations": 0,
                "status": f"Unavailable: {str(error)}",
            })

    return pd.DataFrame(
        results
    )