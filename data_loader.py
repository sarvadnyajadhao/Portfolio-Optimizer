"""
data_loader.py
Handles fetching and cleaning historical price data.

Kept separate from optimizer.py so the math engine has zero network
dependency and can be tested offline. This module needs internet access
and the `yfinance` package (see requirements.txt) — install and run it
on your own machine, not inside a restricted sandbox.

NSE tickers (Nifty 50 stocks) need a ".NS" suffix on Yahoo Finance,
e.g. "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS". US tickers are used as-is.
"""

import numpy as np
import pandas as pd
import yfinance as yf

TRADING_DAYS = 252


def fetch_price_data(tickers, start="2021-01-01", end=None, price_field="Close"):
    """
    Download adjusted close prices for a list of tickers.
    Returns a DataFrame: rows = dates, columns = tickers.
    """
    raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)

    # yfinance returns a MultiIndex column frame for >1 ticker, a flat frame for 1.
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw[price_field]
    else:
        prices = raw[[price_field]]
        prices.columns = tickers

    return clean_price_data(prices)


# --------------------------------------------------------------------------
# Multi-currency support
# --------------------------------------------------------------------------
# Yahoo Finance returns prices in whatever currency the *local exchange*
# trades in. Mix an Indian (.NS), a German (.DE), and a US stock together
# and you have rupees, euros, and dollars sitting in the same table — you
# MUST convert to one currency before comparing returns or optimizing a
# portfolio across them, otherwise "performance" partly just measures FX
# moves, not the companies.

SUFFIX_TO_CURRENCY = {
    ".NS": "INR",   # India (NSE)
    ".BO": "INR",   # India (BSE)
    ".DE": "EUR",   # Germany (DAX)
    ".PA": "EUR",   # France (CAC 40)
    ".L": "GBP",    # London
}

# (Yahoo FX ticker, operation to turn the local price into USD)
FX_TICKERS = {
    "INR": ("USDINR=X", "divide"),      # USDINR=X = how many INR per 1 USD -> divide INR price by it
    "EUR": ("EURUSD=X", "multiply"),    # EURUSD=X = how many USD per 1 EUR -> multiply EUR price by it
    "GBP": ("GBPUSD=X", "multiply"),
}


def infer_currency(ticker: str) -> str:
    """Guess a ticker's trading currency from its Yahoo Finance suffix. Defaults to USD."""
    for suffix, currency in SUFFIX_TO_CURRENCY.items():
        if ticker.upper().endswith(suffix):
            return currency
    return "USD"


def convert_to_common_currency(prices: pd.DataFrame, start, end, target="USD"):
    """
    Convert every column of `prices` into `target` currency (USD by default)
    using historical FX rates, so returns across India/US/Europe are
    genuinely comparable. Returns a new DataFrame with the same shape.
    """
    currencies = {ticker: infer_currency(ticker) for ticker in prices.columns}
    needed = {c for c in currencies.values() if c != target}
    if not needed:
        return prices.copy()  # everything already in the target currency

    fx_cache = {}
    for currency in needed:
        fx_ticker, op = FX_TICKERS[currency]
        fx_raw = yf.download(fx_ticker, start=start, end=end, auto_adjust=True, progress=False)["Close"]
        fx_series = fx_raw.reindex(prices.index).ffill().bfill()
        fx_cache[currency] = (fx_series, op)

    converted = prices.copy()
    for ticker, currency in currencies.items():
        if currency == target:
            continue
        fx_series, op = fx_cache[currency]
        if op == "divide":
            converted[ticker] = converted[ticker] / fx_series.values.ravel()
        elif op == "multiply":
            converted[ticker] = converted[ticker] * fx_series.values.ravel()
    return converted


def clean_price_data(prices: pd.DataFrame):
    """
    Basic data-hygiene pass:
    - drop tickers that came back completely empty (bad symbol / delisted)
    - forward-fill isolated gaps (holidays that don't line up across exchanges)
    - drop any remaining rows with NaNs (e.g. leading days before an IPO)
    """
    prices = prices.dropna(axis=1, how="all")
    prices = prices.ffill()
    prices = prices.dropna(axis=0, how="any")
    return prices


def compute_returns(prices: pd.DataFrame):
    """Daily log returns from a price DataFrame."""
    return np.log(prices / prices.shift(1)).dropna()


def annualize_stats(daily_returns: pd.DataFrame):
    """Annualized mean return vector and covariance matrix from daily log returns."""
    mean_returns = daily_returns.mean() * TRADING_DAYS
    cov_matrix = daily_returns.cov() * TRADING_DAYS
    return mean_returns, cov_matrix


def train_test_split_by_date(daily_returns: pd.DataFrame, split_date):
    """Split a returns DataFrame into in-sample (<= split_date) and out-of-sample (> split_date)."""
    in_sample = daily_returns[daily_returns.index <= split_date]
    out_sample = daily_returns[daily_returns.index > split_date]
    return in_sample, out_sample


if __name__ == "__main__":
    # Example run — needs internet. Mixed India / US / Europe universe to
    # show off the currency conversion; swap tickers for your own basket.
    tickers = ["RELIANCE.NS", "AAPL", "SAP.DE", "MC.PA", "TCS.NS", "MSFT"]
    start, end = "2021-01-01", None

    prices_local = fetch_price_data(tickers, start=start, end=end)
    prices_usd = convert_to_common_currency(prices_local, start=start, end=end)

    returns = compute_returns(prices_usd)
    mean_returns, cov_matrix = annualize_stats(returns)
    print(prices_usd.tail())
    print("\nAnnualized mean returns (USD-converted):\n", mean_returns)
