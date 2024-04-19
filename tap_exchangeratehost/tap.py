"""ExchangeRateHost tap class."""

from __future__ import annotations

from singer_sdk import Tap
from singer_sdk import typing as th  # JSON schema typing helpers

from tap_exchangeratehost import streams


class TapExchangeRateHost(Tap):
    """ExchangeRateHost tap class."""

    name = "tap-exchangeratehost"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "auth_token",
            th.StringType,
            required=True,
            secret=True,  # Flag config as protected.
            description="The token to authenticate against the API service",
        ),
        th.Property(
            "start_date",
            th.DateTimeType,
            description="The earliest record date to sync",
        ),
        th.Property(
            "source_currency",
            th.StringType,
            default="USD",
            description="Source currency to get exchange rates for. "
            "Only changeable on paid plans.",
        ),
        th.Property(
            "user_agent",
            th.StringType,
            default="singer-tap",
            description="user agent to present to the api",
        ),
    ).to_dict()

    def discover_streams(self) -> list[streams.ExchangeRateHostStream]:
        """Return a list of discovered streams.

        Returns:
            A list of discovered streams.
        """
        return [streams.TimeframeStream(self)]


if __name__ == "__main__":
    TapExchangeRateHost.cli()
