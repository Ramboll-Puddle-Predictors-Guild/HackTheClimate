from typing import Sequence

import polars as pl

from .power_curve import get_power_at_wind_velocity


def join_data(
    weather_data: pl.LazyFrame,
    price_data: pl.LazyFrame,
    power_curve: dict[str, Sequence[float]],
) -> pl.LazyFrame:
    """Join price and weather data on time.

    Args:
        weather_data (pl.LazyFrame): Weather data.
        price_data (pl.LazyFrame): Price data.
        power_curve (dict[str, Sequence[float]]): Power curve. Expected schema is: ..code-block::

            {
                "wind_speed": Sequence[float],
                "power": Sequence[float],
                "rotor_speed": Sequence[float]
            }
    """
    combined_data = weather_data.join(price_data, on="time", how="inner")
    combined_data = combined_data.with_columns(
        power=pl.col("wind_speed").map_elements(lambda value: get_power_at_wind_velocity(value, power_curve) * 1e-6)
    )
    combined_data = combined_data.with_columns(income=pl.col("power") * pl.col("price"))
    combined_data = combined_data.with_columns(
        income_sma=pl.col("income").rolling_mean(window_size="1mo", by="time"),
        price_sma=pl.col("price").rolling_mean(window_size="1mo", by="time"),
    )
    return combined_data
