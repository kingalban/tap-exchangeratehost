"""ExchangeRateHost entry point."""

from __future__ import annotations

from tap_exchangeratehost.tap import TapExchangeRateHost

TapExchangeRateHost.cli()
