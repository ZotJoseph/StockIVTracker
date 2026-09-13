"""
used to calculate SINGLE OPTION CONTRACT IV using
    - Stock price
    - Strike
    - Expiration
    - Interest rate
    - Dividend
    - Option price


this is just one option contract, to find the stock IV calculate the option IV of the closest call and put
relative to the stock price

then boom you got the stock IV of that time.
------------------------------------------------------------
THE FOLLOWING IS WRITTEN BY ChatGPT
"""

import math
from scipy.optimize import brentq
from scipy.stats import norm


def black_scholes_call(S, K, T, r, q, sigma):
    """
    S     = stock price
    K     = strike price
    T     = time to expiration in years
    r     = risk-free interest rate
    q     = dividend yield
    sigma = volatility
    """

    d1 = (
        math.log(S / K)
        + (r - q + 0.5 * sigma**2) * T
    ) / (sigma * math.sqrt(T))

    d2 = d1 - sigma * math.sqrt(T)

    return (
        S * math.exp(-q * T) * norm.cdf(d1)
        - K * math.exp(-r * T) * norm.cdf(d2)
    )


def calculate_iv(S, K, T, r, q, market_price):
    """
    S     = stock price
    K     = strike price
    T     = time to expiration in years
    r     = risk-free interest rate
    q     = dividend yield
    market_price = market price of the CURRENT OPTION

    Find the volatility that makes
    Black-Scholes price = market price.
    """

    def error(sigma):
        theoretical_price = black_scholes_call(
            S, K, T, r, q, sigma
        )

        return theoretical_price - market_price

    # Search between 0.01% and 500% volatility
    iv = brentq(error, 0.0001, 5.0)

    return iv



