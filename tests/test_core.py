"""Tests standard tap features using the built-in SDK tests library."""

import datetime
import os

import pytest
from singer_sdk.testing import get_tap_test_class

from tap_exchangeratehost.client import (
    DATE_FORMAT,
    MAX_DAY_RANGE,
    OneYearAtATimePaginator,
)
from tap_exchangeratehost.tap import TapExchangeRateHost

SAMPLE_CONFIG = {
    "start_date": (
        datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=400)
    ).strftime("%Y-%m-%d"),
    "auth_token": os.environ["AUTH_TOKEN"],
}


# Run standard built-in tap tests from the SDK:
TestTapExchangeRateHost = get_tap_test_class(
    tap_class=TapExchangeRateHost,
    config=SAMPLE_CONFIG,
)


@pytest.mark.parametrize(
    "start_date",
    [
        "2000-01-01",
        "2000-02-29",
        "1939-12-01",
    ],
)
def test_paginator(start_date):
    paginator = OneYearAtATimePaginator(start_date)

    seen_dates = set()
    prev_next_page_token = None

    while not paginator.finished:
        next_page_token = tuple(
            datetime.datetime.strptime(d, DATE_FORMAT).date()
            for d in paginator.current_value
        )

        assert not set(next_page_token).intersection(seen_dates), "date was repeated"
        assert (
            next_page_token[1] - next_page_token[0]
        ).days <= MAX_DAY_RANGE, "more than 365 days between days"
        if prev_next_page_token:
            msg = "new date overlaps with previous date"
            assert prev_next_page_token[1] < next_page_token[0], msg

        seen_dates.update(next_page_token)
        prev_next_page_token = next_page_token

        paginator.advance(None)

    today = datetime.datetime.now(tz=datetime.timezone.utc).date()
    assert next_page_token[1] == today, "final date is not equal to today"
