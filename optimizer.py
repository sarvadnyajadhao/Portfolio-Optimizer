"""
optimizer.py
Core Modern Portfolio Theory (MPT) engine.

Everything here works on plain numpy arrays / pandas objects so it can be
reused from a CLI script, a Streamlit app, or a Jupyter notebook without
any Yahoo Finance / network dependency. Keeping the math separate from the
data-fetching layer (data_loader.py) also makes this module unit-testable
with synthetic data.
"""

import numpy as np
import pandas as pd
import scipy.optimize as sco

TRADING_DAYS = 252


# --------------------------------------------------------------------------
# Core performance metrics
# --------------------------------------------------------------------------

def portfolio_performance(weights, mean_returns, cov_matrix, risk_free_rate=0.05):
    """
    Annualized return, volatility, and Sharpe ratio for a given weight vector.

    weights, mean_returns : array-like, shape (n_assets,)
    cov_matrix            : array-like, shape (n_assets, n_assets), annualized
    risk_free_rate        : annual risk-free rate (e.g. 0.07 for a 7% T-bill)
    """
    weights = np.asarray(weights)
    ret = float(np.sum(mean_returns * weights))
    vol = float(np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))))
    sharpe = (ret - risk_free_rate) / vol if vol > 0 else np.nan
    return ret, vol, sharpe


def _neg_sharpe(weights, mean_returns, cov_matrix, risk_free_rate):
    return -portfolio_performance(weights, mean_returns, cov_matrix, risk_free_rate)[2]


def _volatility(weights, mean_returns, cov_matrix):
    return portfolio_performance(weights, mean_returns, cov_matrix)[1]


def _neg_return(weights, mean_returns, cov_matrix):
    return -portfolio_performance(weights, mean_returns, cov_matrix)[0]


# --------------------------------------------------------------------------
# Constraint / bound helpers
# --------------------------------------------------------------------------

def _default_bounds(n_assets, weight_bounds=(0.0, 1.0)):
    return tuple(weight_bounds for _ in range(n_assets))


def _fully_invested_constraint():
    return {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}


# --------------------------------------------------------------------------
# Optimizers
# --------------------------------------------------------------------------

def max_sharpe_portfolio(mean_returns, cov_matrix, risk_free_rate=0.05,
                          weight_bounds=(0.0, 1.0)):
    """Solve for the weights that maximize the Sharpe ratio (long-only by default)."""
    n = len(mean_returns)
    args = (mean_returns, cov_matrix, risk_free_rate)
    constraints = (_fully_invested_constraint(),)
    bounds = _default_bounds(n, weight_bounds)
    init_guess = np.repeat(1.0 / n, n)

    result = sco.minimize(_neg_sharpe, init_guess, args=args, method="SLSQP",
                           bounds=bounds, constraints=constraints)
    if not result.success:
        raise RuntimeError(f"Max-Sharpe optimization failed: {result.message}")
    return result.x


def min_volatility_portfolio(mean_returns, cov_matrix, weight_bounds=(0.0, 1.0)):
    """Solve for the minimum-variance portfolio."""
    n = len(mean_returns)
    args = (mean_returns, cov_matrix)
    constraints = (_fully_invested_constraint(),)
    bounds = _default_bounds(n, weight_bounds)
    init_guess = np.repeat(1.0 / n, n)

    result = sco.minimize(_volatility, init_guess, args=args, method="SLSQP",
                           bounds=bounds, constraints=constraints)
    if not result.success:
        raise RuntimeError(f"Min-Volatility optimization failed: {result.message}")
    return result.x


def efficient_return_portfolio(target_return, mean_returns, cov_matrix,
                                weight_bounds=(0.0, 1.0)):
    """Minimum-volatility portfolio for a given target annual return (one frontier point)."""
    n = len(mean_returns)
    args = (mean_returns, cov_matrix)
    constraints = (
        _fully_invested_constraint(),
        {"type": "eq", "fun": lambda w: portfolio_performance(w, mean_returns, cov_matrix)[0] - target_return},
    )
    bounds = _default_bounds(n, weight_bounds)
    init_guess = np.repeat(1.0 / n, n)

    result = sco.minimize(_volatility, init_guess, args=args, method="SLSQP",
                           bounds=bounds, constraints=constraints)
    return result.x if result.success else None


def efficient_frontier(mean_returns, cov_matrix, n_points=50, weight_bounds=(0.0, 1.0)):
    """
    Trace the efficient frontier by sweeping target returns between the
    min-vol and max-return portfolios and solving for min-vol at each step.
    Returns a DataFrame with columns: return, volatility, and one weight
    column per asset.
    """
    min_vol_w = min_volatility_portfolio(mean_returns, cov_matrix, weight_bounds)
    min_ret = portfolio_performance(min_vol_w, mean_returns, cov_matrix)[0]
    max_ret = float(np.max(mean_returns))  # single-asset return ceiling

    target_returns = np.linspace(min_ret, max_ret * 0.999, n_points)
    rows = []
    for target in target_returns:
        w = efficient_return_portfolio(target, mean_returns, cov_matrix, weight_bounds)
        if w is None:
            continue
        ret, vol, sharpe = portfolio_performance(w, mean_returns, cov_matrix)
        rows.append({"return": ret, "volatility": vol, "sharpe": sharpe, **{
            f"w_{i}": wi for i, wi in enumerate(w)
        }})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Monte Carlo simulation (useful for a quick visual scatter + as a sanity
# check against the SLSQP solution)
# --------------------------------------------------------------------------

def monte_carlo_portfolios(mean_returns, cov_matrix, n_portfolios=10000,
                            risk_free_rate=0.05, seed=42):
    """Randomly sample long-only portfolios and evaluate return/vol/Sharpe for each."""
    rng = np.random.default_rng(seed)
    n_assets = len(mean_returns)
    weights_record = np.zeros((n_portfolios, n_assets))
    results = np.zeros((n_portfolios, 3))  # return, vol, sharpe

    for i in range(n_portfolios):
        w = rng.random(n_assets)
        w /= np.sum(w)
        weights_record[i] = w
        ret, vol, sharpe = portfolio_performance(w, mean_returns, cov_matrix, risk_free_rate)
        results[i] = [ret, vol, sharpe]

    df = pd.DataFrame(results, columns=["return", "volatility", "sharpe"])
    for i in range(n_assets):
        df[f"w_{i}"] = weights_record[:, i]
    return df


# --------------------------------------------------------------------------
# Risk metrics: historical VaR / CVaR on the realized daily return series
# --------------------------------------------------------------------------

def historical_var_cvar(daily_returns: pd.DataFrame, weights, confidence=0.95):
    """
    Historical (non-parametric) 1-day VaR and CVaR for a weighted portfolio,
    computed directly off realized daily returns (no normality assumption).
    """
    weights = np.asarray(weights)
    port_daily = daily_returns.values @ weights
    var_cutoff = np.percentile(port_daily, (1 - confidence) * 100)
    cvar = port_daily[port_daily <= var_cutoff].mean()
    return {
        "confidence": confidence,
        "daily_VaR": -var_cutoff,
        "daily_CVaR": -cvar,
        "annualized_VaR": -var_cutoff * np.sqrt(TRADING_DAYS),
        "annualized_CVaR": -cvar * np.sqrt(TRADING_DAYS),
    }


# --------------------------------------------------------------------------
# Simple backtest: fit weights on an in-sample window, hold them fixed,
# evaluate cumulative growth on an out-of-sample window
# --------------------------------------------------------------------------

def backtest_fixed_weights(daily_returns: pd.DataFrame, weights, initial_value=100.0):
    """Given a fixed weight vector, return the cumulative portfolio value series."""
    weights = np.asarray(weights)
    port_daily_returns = daily_returns.values @ weights
    growth = initial_value * np.cumprod(1 + port_daily_returns)
    return pd.Series(growth, index=daily_returns.index, name="portfolio_value")


if __name__ == "__main__":
    # Quick self-test with synthetic data (no network needed) so this file
    # can be sanity-checked in isolation.
    rng = np.random.default_rng(0)
    n_assets = 4
    mean_returns = rng.uniform(0.08, 0.18, n_assets)
    A = rng.normal(size=(n_assets, n_assets))
    cov_matrix = (A @ A.T) * 0.02  # positive semi-definite, roughly annualized

    w_sharpe = max_sharpe_portfolio(mean_returns, cov_matrix)
    w_minvol = min_volatility_portfolio(mean_returns, cov_matrix)

    print("Max-Sharpe weights:", np.round(w_sharpe, 3),
          "-> ", portfolio_performance(w_sharpe, mean_returns, cov_matrix))
    print("Min-Vol weights:   ", np.round(w_minvol, 3),
          "-> ", portfolio_performance(w_minvol, mean_returns, cov_matrix))

    frontier = efficient_frontier(mean_returns, cov_matrix, n_points=10)
    print("\nEfficient frontier sample:\n", frontier[["return", "volatility", "sharpe"]])
