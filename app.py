"""
app.py
Streamlit dashboard for the portfolio optimizer.

Run with:
    streamlit run app.py
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_loader import (
    fetch_price_data, compute_returns, annualize_stats, train_test_split_by_date,
    infer_currency, convert_to_common_currency,
)
from optimizer import (
    max_sharpe_portfolio, min_volatility_portfolio, efficient_frontier,
    monte_carlo_portfolios, portfolio_performance, historical_var_cvar,
    backtest_fixed_weights,
)

st.set_page_config(page_title="Portfolio Optimizer", layout="wide")
st.title("📈 Portfolio Optimizer — Modern Portfolio Theory")
st.caption("Max-Sharpe & Min-Volatility optimization, efficient frontier, VaR/CVaR, and a simple backtest.")

# --------------------------------------------------------------------------
# Sidebar controls
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("Settings")
    default_tickers = "RELIANCE.NS, AAPL, SAP.DE, MC.PA, TCS.NS, MSFT"
    ticker_input = st.text_input(
        "Tickers (comma-separated)", value=default_tickers,
        help=(
            "Mix markets freely. Suffixes tell Yahoo Finance which exchange: "
            ".NS = NSE India (RELIANCE.NS, TCS.NS), .DE = Germany/DAX (SAP.DE, SIE.DE), "
            ".PA = France/CAC 40 (MC.PA, OR.PA). US stocks need no suffix (AAPL, MSFT)."
        )
    )
    start_date = st.date_input("Start date", value=pd.to_datetime("2021-01-01"))
    end_date = st.date_input("End date", value=pd.to_datetime("today"))
    risk_free_rate = st.slider("Risk-free rate (annual)", 0.0, 0.15, 0.07, 0.005,
                                help="~7% is a reasonable proxy for the Indian 10Y G-Sec yield; use ~0.05 for US T-bills.")
    allow_short = st.checkbox("Allow short-selling (weights can go negative)", value=False)
    convert_currency = st.checkbox("Convert all prices to USD before optimizing", value=True,
                                    help="Turn this off only if every ticker you entered already trades in the same currency.")
    n_frontier_points = st.slider("Efficient frontier resolution", 10, 100, 40)
    n_mc = st.slider("Monte Carlo portfolios (for the scatter cloud)", 500, 20000, 5000, step=500)
    run_button = st.button("Run optimization", type="primary")

weight_bounds = (-1.0, 1.0) if allow_short else (0.0, 1.0)

# --------------------------------------------------------------------------
# Main flow
# --------------------------------------------------------------------------
if run_button:
    tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

    if len(tickers) < 2:
        st.error("Enter at least two tickers to build a diversified portfolio.")
        st.stop()

    with st.spinner(f"Downloading data for {', '.join(tickers)}..."):
        try:
            prices = fetch_price_data(tickers, start=str(start_date), end=str(end_date))
        except Exception as e:
            st.error(f"Data download failed: {e}")
            st.stop()

    if prices.empty or prices.shape[1] < 2:
        st.error("Not enough valid price data came back — check the ticker symbols and date range.")
        st.stop()

    dropped = set(tickers) - set(prices.columns)
    if dropped:
        st.warning(f"Dropped (no data returned): {', '.join(dropped)}")

    currencies_present = {t: infer_currency(t) for t in prices.columns}
    n_currencies = len(set(currencies_present.values()))
    if n_currencies > 1:
        if convert_currency:
            with st.spinner("Converting mixed currencies to USD..."):
                prices = convert_to_common_currency(prices, start=str(start_date), end=str(end_date))
            st.caption(f"Currencies detected: {', '.join(sorted(set(currencies_present.values())))} "
                       "— all converted to USD using historical FX rates before computing returns.")
        else:
            st.warning(f"Mixed currencies detected ({', '.join(sorted(set(currencies_present.values())))}) "
                       "but conversion is off — returns below mix currency movement with company performance.")

    daily_returns = compute_returns(prices)
    mean_returns, cov_matrix = annualize_stats(daily_returns)
    tickers = list(prices.columns)  # keep only tickers that survived cleaning

    # ---- Optimize -------------------------------------------------------
    w_sharpe = max_sharpe_portfolio(mean_returns, cov_matrix, risk_free_rate, weight_bounds)
    w_minvol = min_volatility_portfolio(mean_returns, cov_matrix, weight_bounds)

    ret_s, vol_s, sharpe_s = portfolio_performance(w_sharpe, mean_returns, cov_matrix, risk_free_rate)
    ret_v, vol_v, sharpe_v = portfolio_performance(w_minvol, mean_returns, cov_matrix, risk_free_rate)

    # ---- Headline metrics -------------------------------------------------
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏆 Max-Sharpe Portfolio")
        m1, m2, m3 = st.columns(3)
        m1.metric("Return", f"{ret_s:.2%}")
        m2.metric("Volatility", f"{vol_s:.2%}")
        m3.metric("Sharpe", f"{sharpe_s:.2f}")
    with col2:
        st.subheader("🛡️ Min-Volatility Portfolio")
        m1, m2, m3 = st.columns(3)
        m1.metric("Return", f"{ret_v:.2%}")
        m2.metric("Volatility", f"{vol_v:.2%}")
        m3.metric("Sharpe", f"{sharpe_v:.2f}")

    # ---- Allocation pies ---------------------------------------------------
    pie_col1, pie_col2 = st.columns(2)
    with pie_col1:
        fig = go.Figure(data=[go.Pie(labels=tickers, values=w_sharpe, hole=0.4)])
        fig.update_layout(title="Max-Sharpe Allocation", height=350)
        st.plotly_chart(fig, use_container_width=True)
    with pie_col2:
        fig = go.Figure(data=[go.Pie(labels=tickers, values=w_minvol, hole=0.4)])
        fig.update_layout(title="Min-Volatility Allocation", height=350)
        st.plotly_chart(fig, use_container_width=True)

    # ---- Efficient frontier + Monte Carlo cloud ----------------------------
    st.subheader("Efficient Frontier")
    with st.spinner("Tracing the efficient frontier and sampling random portfolios..."):
        frontier_df = efficient_frontier(mean_returns, cov_matrix, n_points=n_frontier_points, weight_bounds=weight_bounds)
        mc_df = monte_carlo_portfolios(mean_returns, cov_matrix, n_portfolios=n_mc, risk_free_rate=risk_free_rate)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=mc_df["volatility"], y=mc_df["return"], mode="markers",
        marker=dict(size=4, color=mc_df["sharpe"], colorscale="Viridis", showscale=True, colorbar=dict(title="Sharpe")),
        name="Random portfolios", opacity=0.5,
    ))
    fig.add_trace(go.Scatter(
        x=frontier_df["volatility"], y=frontier_df["return"], mode="lines",
        line=dict(color="black", width=3), name="Efficient frontier",
    ))
    fig.add_trace(go.Scatter(
        x=[vol_s], y=[ret_s], mode="markers", marker=dict(color="red", size=14, symbol="star"),
        name="Max Sharpe",
    ))
    fig.add_trace(go.Scatter(
        x=[vol_v], y=[ret_v], mode="markers", marker=dict(color="blue", size=14, symbol="diamond"),
        name="Min Volatility",
    ))
    fig.update_layout(xaxis_title="Annualized Volatility", yaxis_title="Annualized Return", height=550)
    st.plotly_chart(fig, use_container_width=True)

    # ---- Weight tables ------------------------------------------------------
    st.subheader("Allocation Detail")
    weights_df = pd.DataFrame({"Ticker": tickers, "Max-Sharpe": w_sharpe, "Min-Vol": w_minvol})
    weights_df["Max-Sharpe"] = weights_df["Max-Sharpe"].map(lambda x: f"{x:.2%}")
    weights_df["Min-Vol"] = weights_df["Min-Vol"].map(lambda x: f"{x:.2%}")
    st.dataframe(weights_df, use_container_width=True, hide_index=True)

    # ---- VaR / CVaR ----------------------------------------------------------
    st.subheader("Risk: Historical VaR & CVaR (Max-Sharpe portfolio)")
    risk_stats = historical_var_cvar(daily_returns, w_sharpe, confidence=0.95)
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("1-day VaR (95%)", f"{risk_stats['daily_VaR']:.2%}")
    r2.metric("1-day CVaR (95%)", f"{risk_stats['daily_CVaR']:.2%}")
    r3.metric("Annualized VaR (95%)", f"{risk_stats['annualized_VaR']:.2%}")
    r4.metric("Annualized CVaR (95%)", f"{risk_stats['annualized_CVaR']:.2%}")
    st.caption("Historical (non-parametric) VaR/CVaR from realized daily returns — no normality assumption.")

    # ---- Simple out-of-sample backtest ---------------------------------------
    st.subheader("Backtest: Weights Fixed on First 70% of History, Held on Last 30%")
    split_idx = int(len(daily_returns) * 0.7)
    split_date = daily_returns.index[split_idx]
    in_sample, out_sample = train_test_split_by_date(daily_returns, split_date)

    if len(out_sample) > 5:
        in_mean, in_cov = annualize_stats(in_sample)
        w_bt = max_sharpe_portfolio(in_mean, in_cov, risk_free_rate, weight_bounds)
        growth = backtest_fixed_weights(out_sample, w_bt)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=growth.index, y=growth.values, mode="lines", name="Portfolio (out-of-sample)"))
        equal_weight_growth = backtest_fixed_weights(out_sample, np.repeat(1 / len(tickers), len(tickers)))
        fig.add_trace(go.Scatter(x=equal_weight_growth.index, y=equal_weight_growth.values,
                                  mode="lines", name="Equal-weight benchmark", line=dict(dash="dash")))
        fig.update_layout(xaxis_title="Date", yaxis_title="Value (start = 100)", height=400)
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"In-sample: {in_sample.index[0].date()} to {split_date.date()} · "
                   f"Out-of-sample: {split_date.date()} to {out_sample.index[-1].date()}. "
                   "Weights are optimized once on in-sample data and held fixed — this is a naive "
                   "backtest with no rebalancing, transaction costs, or slippage.")
    else:
        st.info("Not enough history to run a meaningful out-of-sample backtest — widen the date range.")

else:
    st.info("Set your tickers and options in the sidebar, then click **Run optimization**.")
    st.markdown("""
**What this does**
1. Downloads historical prices for the tickers you specify (via Yahoo Finance)
2. Computes annualized expected returns and the covariance matrix
3. Solves for the **Max-Sharpe** and **Min-Volatility** portfolios (SLSQP, long-only by default)
4. Traces the full **efficient frontier** and overlays a Monte Carlo cloud of random portfolios
5. Reports **historical VaR/CVaR** and a simple **train/test backtest** against an equal-weight benchmark

**Notes**
- You can mix exchanges freely: `.NS` = NSE India, `.DE` = Germany (DAX 40), `.PA` = France (CAC 40),
  no suffix = US. Yahoo Finance returns each ticker's prices in its own local currency — see the
  currency note in the README before comparing returns across markets.
- This assumes independent, historically-representative returns going forward — a standard MPT
  caveat worth stating explicitly in any writeup.
""")
