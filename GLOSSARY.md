# Glossary — plain-language explanations

A quick reference for every term this project uses. Written so you can
explain the project confidently in an interview or on your GitHub README,
not just run the code.

### Portfolio
A collection of investments (stocks, in this project) held together, each
making up some **weight** (percentage) of the total money invested.

### Return
How much an investment grew (or shrank) over a period, in percent.
"Expected return" is a forecast, usually estimated as the average of past
daily returns, scaled up to a yearly number.

### Volatility (a.k.a. risk, standard deviation)
How much an investment's price bounces around. A high-volatility stock
swings wildly day to day; a low-volatility one moves slowly and steadily.
In this project, "risk" and "volatility" are used interchangeably — that's
the standard (if imperfect) convention in Modern Portfolio Theory.

### Covariance / Correlation
How two stocks move *together*. If they always rise and fall on the same
days, they're highly correlated — combining them barely reduces your risk.
If one zigs when the other zags (low or negative correlation), combining
them smooths out the bumps. This is the mathematical basis for
diversification: "don't put all your eggs in one basket" only works if the
baskets don't all fall at once.

### Covariance matrix
A table of every pair of stocks' covariance with each other (plus each
stock's own volatility on the diagonal). This is the key ingredient that
lets the optimizer know not just how risky each stock is alone, but how
much risk survives once they're combined.

### Sharpe Ratio
Return earned *per unit of risk taken*, after subtracting a "risk-free"
baseline (see below):

```
Sharpe = (Portfolio Return − Risk-Free Rate) / Portfolio Volatility
```

Higher is better. A portfolio with 12% return and 10% volatility has a
better Sharpe ratio than one with 15% return and 20% volatility, even
though the second has a higher raw return — it took much more risk to get
there.

### Risk-free rate
The return you could get with essentially zero risk — usually a
government bond yield (e.g. Indian 10-year G-Sec, or US Treasury bills).
It's the baseline every risky investment has to beat to be "worth it."

### Modern Portfolio Theory (MPT)
Harry Markowitz's 1952 idea (which won a Nobel Prize) that you shouldn't
judge a stock in isolation — you should judge how it changes your *whole
portfolio's* risk and return, because of the diversification effect above.

### Efficient Frontier
If you plot every possible portfolio's risk (x-axis) against its return
(y-axis), most combinations are "dumb" — you could get the same return for
less risk, or more return for the same risk. The efficient frontier is the
curve of portfolios where that's no longer true: each point is the *best
possible return for that level of risk*. Nothing above/left of the curve
is achievable; nothing below/right of it is worth choosing.

### Max-Sharpe Portfolio
The single point on the efficient frontier with the best risk-adjusted
return — the "optimal" portfolio if you don't have a personal preference
for more or less risk.

### Minimum-Volatility Portfolio
The single point on the efficient frontier with the lowest possible risk,
regardless of return — for a more conservative investor.

### Monte Carlo simulation
Instead of solving the math exactly, generate thousands of *random*
portfolios and plot them. Used here as a visual sanity check: the real
efficient frontier (solved exactly) should sit right along the top-left
edge of the random cloud. If it doesn't, something's wrong with the math.

### SLSQP (Sequential Least Squares Programming)
The specific optimization algorithm (`scipy.optimize.minimize(method="SLSQP")`)
used to actually solve for the best weights. You don't need to know its
internals — just that it's a standard, reliable method for "find the best
values subject to constraints" problems like this one.

### Constraints & bounds
Rules the optimizer must respect. Here: weights must sum to 100%
(`fully invested`), and each weight must be between 0% and 100%
(`long-only` — no short-selling, unless you toggle that on).

### Long-only vs. short-selling
Long-only means you can only buy stocks (weights ≥ 0). Short-selling means
betting a stock will *fall*, which shows up as a negative weight. Riskier
and more complex — off by default in this project.

### VaR (Value at Risk)
"On a bad day (say, the worst 5% of days historically), how much could I
expect to lose?" A 1-day 95% VaR of 2% means: historically, only 5% of
days were worse than a 2% loss.

### CVaR (Conditional VaR, a.k.a. Expected Shortfall)
A follow-up to VaR: "*given* that we're in that bad 5% of days, what's the
average loss?" CVaR is always worse than VaR — it answers "how bad is bad,"
not just "where does bad start."

### Backtest
Testing a strategy on historical data it wasn't optimized on, to see how it
would have performed. This project fits weights on the first 70% of the
date range, then holds them fixed and checks performance on the remaining
30% ("out-of-sample") — a basic, honest way to check the strategy isn't
just memorizing the past.

### Benchmark (equal-weight)
A simple comparison point: what if you'd just split your money equally
across all the stocks instead of optimizing? If your optimized portfolio
can't beat this, the optimization isn't adding value.

### FX (foreign exchange) conversion
When you mix stocks from different countries (India, US, Europe), their
prices are quoted in different currencies (₹, $, €). Before comparing or
combining them, this project converts everything to one currency (USD)
using historical exchange rates — otherwise a stock could look like it
"grew" only because its home currency strengthened, not because the
company did well.
