# Glossary — Plain-Language Explanations

A plain-language reference for the financial, statistical, and optimization
terms used in this project.

### Portfolio
A collection of investments (stocks, in this project) held together, each
making up some **weight** (percentage) of the total money invested.

### Return
How much an investment grew (or shrank) over a period, expressed as a
percentage. "Expected return" in this project is estimated from the
historical average daily return and annualized; it is not a guaranteed
forecast of future performance.

### Volatility (standard deviation)
How much an investment's price bounces around. A high-volatility stock
swings wildly day to day; a low-volatility one moves slowly and steadily.
In this project, "risk" and "volatility" are used interchangeably — that's
the standard (if imperfect) convention in Modern Portfolio Theory.

### Covariance / Correlation
How two stocks' returns move in relation to each other. If they tend to rise
and fall together, they have positive correlation. If they tend to move in
opposite directions, they have negative correlation. Lower correlation can
help reduce overall portfolio risk through diversification.

### Covariance matrix
A table containing the covariance between every pair of stocks. The diagonal
contains each stock's own variance. This lets the optimizer account for both
individual risk and how the stocks move together when calculating portfolio
risk.

### Sharpe Ratio
A measure of risk-adjusted return: how much return a portfolio earns above
the risk-free rate for each unit of volatility taken.
```
Sharpe = (Portfolio Return − Risk-Free Rate) / Portfolio Volatility
```

Higher is better. A portfolio with 12% return and 10% volatility has a
better Sharpe ratio than one with 15% return and 20% volatility, even
though the second has a higher raw return — it took much more risk to get
there.

### Risk-free rate
A reference return from an asset considered to have very low default risk,
often based on government securities. It is used as the baseline for
calculating the Sharpe ratio.

### Modern Portfolio Theory (MPT)
Harry Markowitz's 1952 idea (which won a Nobel Prize) that you shouldn't
judge a stock in isolation — you should judge how it changes your *whole
portfolio's* risk and return, because diversification can change the overall
risk of the portfolio.

### Efficient Frontier
The set of portfolios that offer the best expected return for a given level
of risk, or the lowest risk for a given expected return. Portfolios below
the frontier are inefficient because another portfolio can offer better
risk-return characteristics under the same assumptions and constraints.

### Max-Sharpe Portfolio
The portfolio that maximizes the Sharpe ratio under the model's assumptions
and constraints. It aims to provide the highest expected return relative
to volatility.

### Minimum-Volatility Portfolio
The portfolio with the lowest estimated volatility among the portfolios
allowed by the model's constraints. It focuses on minimizing volatility
rather than maximizing return.

### Monte Carlo simulation
Instead of relying only on the optimization algorithm, the project generates
thousands of random portfolios and plots them. This provides a visual
cross-check: the efficient frontier should lie along the upper-left boundary
of the feasible portfolio cloud under the same assumptions and constraints.

### SLSQP (Sequential Least Squares Programming)
The specific optimization algorithm (`scipy.optimize.minimize(method="SLSQP")`)
used to solve for the portfolio weights that best satisfy the chosen
objective and constraints. You don't need to know its internals — just that
it's a standard numerical optimization method for "find the best values
subject to constraints" problems like this one.

### Constraints & bounds
Rules the optimizer must respect. The portfolio weights must sum to 100%
(fully invested). By default, each weight is constrained between 0% and
100% (long-only). If short-selling is enabled, negative weights are allowed
within the specified bounds.

### Long-only vs. short-selling
Long-only means you can only buy stocks (weights ≥ 0). Short-selling means
betting a stock will *fall*, which shows up as a negative weight. It can
introduce additional risk and complexity — off by default in this project.

### VaR (Value at Risk)
A threshold for potential loss at a chosen confidence level. A 1-day 95%
VaR of 2% means that, based on the historical data used here, losses were
worse than 2% on approximately 5% of trading days.

### CVaR (Conditional VaR, a.k.a. Expected Shortfall)
The average loss among the observations that fall beyond the VaR threshold.
It answers not only where the bad-loss threshold begins, but how severe the
losses are in that tail.

### Backtest
Testing a strategy on historical data that was not used to fit the portfolio,
to evaluate how it would have performed under those historical conditions.
This project fits weights on the first 70% of the date range, then holds
them fixed over the remaining 30% ("out-of-sample"). It is a basic evaluation,
not a guarantee of future performance.

### Benchmark (equal-weight)
The benchmark provides a simple reference point for evaluating whether the
optimization produced useful improvements in risk and/or return.

### FX (foreign exchange) conversion
When you mix stocks from different countries (India, US, Europe), their
prices are quoted in different currencies (₹, $, €). This project converts
the price series to USD using historical exchange rates before calculating
returns and optimizing the portfolio. This allows currency movements to be
incorporated consistently into the analysis.
