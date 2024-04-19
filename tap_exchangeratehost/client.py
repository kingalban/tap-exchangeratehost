"""REST client handling, including ExchangeRateHostStream base class."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterable, TypeVar

import requests
from singer_sdk.authenticators import APIKeyAuthenticator
from singer_sdk.pagination import BaseAPIPaginator
from singer_sdk.streams import RESTStream

_Auth = Callable[[requests.PreparedRequest], requests.PreparedRequest]

T = TypeVar("T")

NextPageToken = tuple[str, str]

DATE_FORMAT = "%Y-%m-%d"
MAX_DAY_RANGE = 365


class OneYearAtATimePaginator(BaseAPIPaginator):
    """Paginate over a time period, producing non-overlapping date pairs."""

    @staticmethod
    def add_days(date_str: str, days: int) -> tuple[str, bool]:
        """Calculate the date in `days` days, truncating that date to today."""
        new_date = (
            datetime.strptime(date_str, DATE_FORMAT) + timedelta(days=days)  # noqa: DTZ007
        ).date()

        today = datetime.now(tz=timezone.utc).date()
        if new_date > today:
            return today.strftime(DATE_FORMAT), True

        return new_date.strftime(DATE_FORMAT), False

    @property
    def current_value(self) -> NextPageToken:
        """Get the current pagination value.

        Returns:
            Current page value.
        """
        next_date, _ = self.add_days(self._value, MAX_DAY_RANGE)
        return self._value, next_date

    def get_next(self, response: requests.Response) -> str | None:  # noqa: ARG002
        """Get the next starting date, or truncate to today."""
        next_date, is_last = self.add_days(self._value, MAX_DAY_RANGE + 1)
        if is_last:
            return None

        return next_date


class ExchangeRateHostStream(RESTStream):
    """ExchangeRateHost stream class."""

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return "http://api.exchangerate.host/"

    records_jsonpath = "$.quotes[*]"

    @property
    def authenticator(self) -> APIKeyAuthenticator:
        """Return a new authenticator object.

        Returns:
            An authenticator instance.
        """
        return APIKeyAuthenticator.create_for_stream(
            self,
            key="access_key",
            value=self.config.get("auth_token", ""),
            location="params",
        )

    @property
    def http_headers(self) -> dict:
        """Return the http headers needed.

        Returns:
            A dictionary of HTTP headers.
        """
        headers = {}
        if "user_agent" in self.config:
            headers["User-Agent"] = self.config.get("user_agent")
        return headers

    def get_new_paginator(self) -> BaseAPIPaginator:
        """Create a new pagination helper instance.

        If the source API can make use of the `next_page_token_jsonpath`
        attribute, or it contains a `X-Next-Page` header in the response
        then you can remove this method.

        If you need custom pagination that uses page numbers, "next" links, or
        other approaches, please read the guide: https://sdk.meltano.com/en/v0.25.0/guides/pagination-classes.html.

        Returns:
            A pagination helper instance.
        """
        starting_date = self.get_starting_timestamp(None).strftime(DATE_FORMAT)
        return OneYearAtATimePaginator(starting_date)

    def get_url_params(
        self,
        context: dict | None,  # noqa: ARG002
        next_page_token: NextPageToken,
    ) -> dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization.

        Args:
            context: The stream context.
            next_page_token: The next page index or value.

        Returns:
            A dictionary of URL query parameters.
        """
        params: dict = {
            "source": self.config["source_currency"],
            "start_date": next_page_token[0],
            "end_date": next_page_token[1],
        }
        if self.replication_key:
            params["sort"] = "asc"
            params["order_by"] = self.replication_key
        return params

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse the response and return an iterator of result records.

        Args:
            response: The HTTP ``requests.Response`` object.

        Yields:
            Each record from the source.
        """
        if "quotes" in (json_resp := response.json()):
            for quote_date, rates in json_resp["quotes"].items():
                for currencies, rate in rates.items():
                    yield {
                        "date": quote_date,
                        "currency": currencies,
                        "quote": float(rate),
                    }
        else:
            msg = f"response did not include 'quotes'. {json_resp=}"
            raise ValueError(msg)
