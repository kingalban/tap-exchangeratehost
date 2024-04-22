"""Stream type classes for tap-exchangeratehost."""

from __future__ import annotations

import typing as t

from singer_sdk import typing as th  # JSON Schema typing helpers

from tap_exchangeratehost.client import ExchangeRateHostStream


class TimeframeStream(ExchangeRateHostStream):
    """Define custom stream."""

    name = "timeframe"
    path = "/timeframe"
    primary_keys: t.ClassVar[list[str]] = ["date", "source_currency", "dest_currency"]
    replication_key = "date"
    schema = th.PropertiesList(
        th.Property("date", th.DateTimeType, description="Date of the quote"),
        th.Property(
            "source_currency",
            th.StringType,
            description="{source}{destination} currency codes",
        ),
        th.Property(
            "dest_currency",
            th.StringType,
            description="{source}{destination} currency codes",
        ),
        th.Property(
            "quote", th.NumberType, description="Quoted rate between currencies"
        ),
    ).to_dict()
