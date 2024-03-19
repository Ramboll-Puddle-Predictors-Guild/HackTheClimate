import polars as pl

SCHEMA = {
    "Country": pl.Categorical,
    "ISO3 Code": pl.Categorical,
    "Datetime (UTC)": pl.Datetime("ms"),
    "Datetime (Local)": pl.Datetime("ms"),
    "Price (EUR/MWhe)": pl.Float32,
}


def read_price_data(path: str) -> pl.LazyFrame:
    """Read the price history.

    See ``SCHEMA`` variable for the expected CSV structure.

    Returns:
        pl.LazyFrame: A lazy frame with columns ``time`` and ``price``.
    """
    price_data = (
        pl.read_csv(path, schema=SCHEMA)
        .lazy()
        .select(
            [
                pl.col("Datetime (Local)").alias("time"),
                pl.col("Price (EUR/MWhe)").alias("price"),
            ]
        )
    )
    price_data = price_data.set_sorted(pl.col("time"))
    price_data = price_data.filter(pl.col("time").dt.year() < 2020)
    return price_data
