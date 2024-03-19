import polars as pl

SCHEMA = {
    "timestamp": pl.Datetime("ms"),
    "rainc": pl.Float32,
    "qrain_120.0": pl.Float32,
    "rho_120.0": pl.Float32,
    "wsp_120.0": pl.Float32,
    "qrain_150.0": pl.Float32,
    "rho_150.0": pl.Float32,
    "wsp_150.0": pl.Float32,
}


def read_weather_data(path: str) -> pl.LazyFrame:
    """Read weather data.

    See ``SCHEMA`` variable for the expected CSV structure.

    Returns:
        pl.LazyFrame: A lazy frame with columns ``time`` and ``wind_speed``.
    """
    data = (
        pl.read_csv(path, schema=SCHEMA)
        .lazy()
        .select(
            [
                pl.col("timestamp").alias("time"),
                pl.col("wsp_150.0").alias("wind_speed"),
            ]
        )
        .set_sorted(pl.col("time"))
    )

    return data
