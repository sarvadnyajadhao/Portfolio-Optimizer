# Portfolio Optimizer (Modern Portfolio Theory)

A Python tool that builds Max-Sharpe and Minimum-Volatility portfolios from
real market data across **multiple global markets** (India, US, Germany,
France), traces the efficient frontier, handles the currency conversion
that mixing those markets requires, and reports basic risk metrics
(VaR/CVaR) — with an interactive Streamlit dashboard on top.

New to the finance/stats terms used below (Sharpe ratio, efficient frontier,
VaR, etc.)? See **[GLOSSARY.md](GLOSSARY.md)** for a plain-language explanation
of every one.

## Project structure

```
portfolio_optimizer/
├── optimizer.py      # Pure math engine (MPT, SLSQP, Monte Carlo, VaR/CVaR) — no network calls
├── data_loader.py     # Fetches, cleans, and currency-converts price data via yfinance
├── app.py             # Streamlit dashboard tying the two together
├── requirements.txt
├── GLOSSARY.md        # Plain-language explanation of every term used
├── LICENSE
└── README.md
```

`optimizer.py` has zero dependency on `data_loader.py`, so the math can be
tested offline with synthetic data (run `python optimizer.py` — it already
does this as a self-check).

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running it

**CLI sanity check (no data download, pure math):**
```bash
python optimizer.py
```

**Fetch data and print stats for a fixed ticker list:**
```bash
python data_loader.py
```

**Full interactive dashboard:**
```bash
streamlit run app.py
```
Then enter tickers in the sidebar — mix markets freely, e.g.
`RELIANCE.NS, AAPL, SAP.DE, MC.PA, TCS.NS, MSFT`.

| Market | Suffix | Example |
|---|---|---|
| India (NSE) | `.NS` | `RELIANCE.NS`, `TCS.NS`, `HDFCBANK.NS` |
| Germany (DAX 40) | `.DE` | `SAP.DE`, `SIE.DE`, `ALV.DE` |
| France (CAC 40) | `.PA` | `MC.PA` (LVMH), `OR.PA` (L'Oréal), `TTE.PA` |
| US | none | `AAPL`, `MSFT`, `GOOGL` |

Prices come back in each exchange's local currency (₹ / € / $). The app
detects this and converts everything to USD using historical FX rates
before computing returns or optimizing — otherwise a stock could look
like it "grew" purely because its currency strengthened. See
`convert_to_common_currency()` in `data_loader.py`, and the FX section of
GLOSSARY.md.

## What's implemented

- **Expected return, variance, Sharpe ratio** — the standard MPT formulas
- **Max-Sharpe** and **Min-Volatility** portfolios via `scipy.optimize.minimize`
  (SLSQP), long-only by default with an optional short-selling toggle
- **Efficient frontier**: swept by solving min-vol at a grid of target returns
- **Monte Carlo cloud**: random long-only portfolios plotted for visual
  cross-check against the analytical frontier
- **Historical VaR & CVaR** at the 95% confidence level (non-parametric —
  no normal-distribution assumption)
- **Naive backtest**: weights fit on the first 70% of history, held fixed,
  evaluated out-of-sample against an equal-weight benchmark

## Known limitations (worth stating in a writeup, not hiding)

- Expected returns are estimated from **historical means**, which are
  notoriously noisy forward-looking estimates — this is the single biggest
  weakness of textbook MPT, not a bug in this code
- The backtest has **no rebalancing, transaction costs, or slippage** —
  it is a lower bound on real-world friction, not a performance claim
- VaR/CVaR are computed from the same historical window used to fit the
  portfolio, so they describe the past, not a guaranteed future loss bound

## Roadmap for extending this (in rough order of effort)

1. **Rolling-window backtest** — instead of one train/test split, re-optimize
   weights every N days on a trailing window and chain the results together
   (a real walk-forward backtest instead of the current single-split version)
2. **Benchmark comparison** — pull Nifty 50 or S&P 500 as a benchmark series
   and report tracking error / information ratio alongside Sharpe
3. **Black-Litterman model** — blend market-implied equilibrium returns with
   your own views, rather than relying purely on historical means (addresses
   the biggest limitation above)
4. **Hierarchical Risk Parity (HRP)** — a robustness alternative to
   mean-variance optimization that doesn't require inverting the covariance
   matrix, so it degrades more gracefully with many correlated assets
5. **Factor exposure** — regress portfolio returns on Fama-French factors
   or a simple momentum/value/size split, useful if this feeds into the
   same finance-research workflow as your Nifty macro paper

## Presenting this on GitHub / your CV

This was built as a portfolio piece (for a Master's application, not a
college submission), so a few things worth doing before you link it:

1. **Add screenshots** of the dashboard (frontier chart + allocation pies)
   to this README — GitHub visitors judge a project by its README image
   before they read a single line of code.
2. **One-line CV description**: something like *"Built a multi-market
   (India/US/Europe) portfolio optimizer implementing Modern Portfolio
   Theory — Max-Sharpe/Min-Vol optimization, efficient frontier, VaR/CVaR,
   and an out-of-sample backtest, deployed as an interactive Streamlit app."*
3. **Deploy it** (optional but strong): Streamlit Community Cloud
   (streamlit.io/cloud) hosts `app.py` for free straight from a GitHub repo,
   so you can link a *live demo*, not just code.
4. Keep the **Known limitations** section above in the README as-is — for
   a finance-adjacent Master's application, showing you understand a
   model's weaknesses is more convincing than only showing it "working."
   ## Screenshots

### Portfolio Optimization Dashboard
![Portfolio Optimization Dashboard](portfolio_optimizer_screenshot_1.png)

### Efficient Frontier & Portfolio Allocation
![Efficient Frontier and Portfolio Allocation](portfolio_optimizer_screenshot_2.png)

### Risk Analysis & Backtesting
![Risk Analysis and Backtesting](portfolio_optimizer_screenshot_3.png)
