#!/usr/bin/env python3
"""
Calculate a per-symbol composite implied volatility from Schwab option chains.

Definition used here:
  1. For each expiration, take the N strikes nearest the underlying price.
  2. Combine valid CALL/PUT contract IVs with vega weighting.
  3. Convert expiration IV to total variance (IV^2 * T).
  4. Interpolate total variance to TARGET_DTE (default: 30 days).

Inputs:
  ./token.json
  blob/optionSymbols.txt

Credentials:
  SCHWAB_APP_KEY
  SCHWAB_APP_SECRET

Output:
  stdout table + blob/composite_iv.csv
"""

from __future__ import annotations

import csv
from dotenv import load_dotenv
import math
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from schwab.auth import client_from_token_file
from schwab.client import Client


load_dotenv()
TOKEN_PATH = Path("token.json")
SYMBOLS_PATH = Path("blob/optionSymbols.txt")
OUTPUT_PATH = Path("blob/composite_iv.csv")

TARGET_DTE = 30
MIN_DTE = 7
MAX_DTE = 60
STRIKE_COUNT = 20  # Schwab: strikes above/below ATM to request
ATM_STRIKE_LEVELS = 3  # strikes nearest spot used for each expiration
REQUEST_PAUSE_SECONDS = 0.20




@dataclass
class ExpiryIV:
    dte: int
    expiry: str
    iv: float  # decimal, e.g. 0.253 = 25.3%
    contracts_used: int


@dataclass
class CompositeIVResult:
    symbol: str
    underlying_price: float
    datetime : datetime
    iv: float | None  # decimal
    lower_dte: int | None
    upper_dte: int | None
    contracts_used: int
    status: str


def load_symbols(path: Path) -> list[str]:
    """
    Load all desired stock symbols into a list
    help decide which stock IVs to report
    """
    if not path.exists():
        raise FileNotFoundError(f"symbol file not found: {path}")

    symbols: list[str] = []
    seen: set[str] = set()

    for raw_line in path.read_text(encoding = "utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        for token in re.split(r"[\s,]+", line):
            symbol = token.strip().upper()
            if symbol and symbol not in seen:
                symbols.append(symbol)
                seen.add(symbol)

    return symbols


def as_finite_float(value: Any) -> float | None:
    """
    float sanitation function

    """
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def parse_dte(expiry_key: str, contracts: Iterable[dict[str, Any]]) -> int | None:
    """
    date sanitation function

    """
    # Schwab keys are usually "YYYY-MM-DD:DTE".
    try:
        return int(expiry_key.rsplit(":", 1)[1])
    except (IndexError, ValueError):
        pass

    for c in contracts:
        try:
            return int(c["daysToExpiration"])
        except (KeyError, TypeError, ValueError):
            continue
    return None


def valid_contract_iv(contract: dict[str, Any]) -> float | None:
    """
    The thing that actually returns the stock IV
    Return Schwab IV as a decimal. Schwab chain 'volatility' is percent.
    """
    iv_pct = as_finite_float(contract.get("volatility"))
    if iv_pct is None or iv_pct <= 0.0 or iv_pct > 1000.0:
        return None

    # Reject obviously unusable quotes when both sides are present but crossed/zero.
    bid = as_finite_float(contract.get("bid"))
    ask = as_finite_float(contract.get("ask"))
    if bid is not None and ask is not None:
        if bid < 0 or ask <= 0 or ask < bid:
            return None

    return iv_pct / 100.0


def collect_expiry_iv(chain: dict[str, Any], spot: float) -> list[ExpiryIV]:
    """Build near-ATM, call+put, vega-weighted IV for each expiration."""
    # expiry_key -> strike -> contracts (calls + puts)
    grouped: dict[str, dict[float, list[dict[str, Any]]]] = {}

    for map_name in ("callExpDateMap", "putExpDateMap"):
        exp_map = chain.get(map_name) or {}
        for expiry_key, strike_map in exp_map.items():
            expiry_bucket = grouped.setdefault(expiry_key, {})
            for strike_text, contracts in (strike_map or {}).items():
                strike = as_finite_float(strike_text)
                if strike is None or strike <= 0:
                    continue
                expiry_bucket.setdefault(strike, []).extend(contracts or [])

    result: list[ExpiryIV] = []

    for expiry_key, strike_map in grouped.items():
        if not strike_map:
            continue

        all_contracts = [c for cs in strike_map.values() for c in cs]
        dte = parse_dte(expiry_key, all_contracts)
        if dte is None or dte <= 0:
            continue

        nearest_strikes = sorted(
            strike_map,
            key = lambda k: abs(math.log(k / spot)) if spot > 0 and k > 0 else abs(k - spot),
        )[:ATM_STRIKE_LEVELS]

        weighted_iv_sum = 0.0
        weight_sum = 0.0
        contracts_used = 0

        for strike in nearest_strikes:
            for contract in strike_map[strike]:
                iv = valid_contract_iv(contract)
                if iv is None:
                    continue

                vega = as_finite_float(contract.get("vega"))
                # Vega weighting emphasizes the contracts whose prices are most
                # informative about volatility. Fall back to equal weight.
                weight = abs(vega) if vega is not None and abs(vega) > 1e-12 else 1.0

                weighted_iv_sum += iv * weight
                weight_sum += weight
                contracts_used += 1

        if weight_sum <= 0 or contracts_used == 0:
            continue

        expiry_date = expiry_key.split(":", 1)[0]
        result.append(
            ExpiryIV(
                dte = dte,
                expiry = expiry_date,
                iv = weighted_iv_sum / weight_sum,
                contracts_used = contracts_used,
            )
        )

    result.sort(key = lambda x: x.dte)
    return result


def constant_maturity_iv(expiries: list[ExpiryIV], target_dte: int) -> tuple[
                                                                           float, int, int, int, str] | None:
    """
    Interpolate total variance to target_dte.

    Returns: (iv, lower_dte, upper_dte, contracts_used, status)
    """
    if not expiries:
        return None

    # Exact match.
    exact = next((e for e in expiries if e.dte == target_dte), None)
    if exact:
        return exact.iv, exact.dte, exact.dte, exact.contracts_used, "exact"

    lower = max((e for e in expiries if e.dte < target_dte), key = lambda e: e.dte, default = None)
    upper = min((e for e in expiries if e.dte > target_dte), key = lambda e: e.dte, default = None)

    if lower and upper:
        t1 = lower.dte / 365.0
        t2 = upper.dte / 365.0
        tt = target_dte / 365.0

        w1 = lower.iv * lower.iv * t1
        w2 = upper.iv * upper.iv * t2

        # Linear interpolation in total variance, not directly in IV.
        wt = ((t2 - tt) / (t2 - t1)) * w1 + ((tt - t1) / (t2 - t1)) * w2
        iv = math.sqrt(max(wt / tt, 0.0))
        return iv, lower.dte, upper.dte, lower.contracts_used + upper.contracts_used, "interpolated"

    # If we cannot bracket target DTE, use the closest available expiration.
    nearest = min(expiries, key = lambda e: abs(e.dte - target_dte))
    return nearest.iv, nearest.dte, nearest.dte, nearest.contracts_used, "nearest-expiry"


def fetch_composite_iv(client: Client, symbol: str) -> CompositeIVResult:
    """
    THIS FUNCTION RETURNS THE ACTUAL RESULT + EVERYTHING YOU NEED

    :param client: the dataclass used to store API related information
    :param symbol: the stock symbol you want to pass in
    :return: The CompositeIV as a dataclass
    """
    market_date = datetime.now(ZoneInfo("America/New_York")).date()
    from_date = market_date + timedelta(days = MIN_DTE)
    to_date = market_date + timedelta(days = MAX_DTE)

    try:
        response = client.get_option_chain(
            symbol,
            contract_type = Client.Options.ContractType.ALL,
            strike_count = STRIKE_COUNT,
            include_underlying_quote = True,
            strategy = Client.Options.Strategy.SINGLE,
            from_date = from_date,
            to_date = to_date,
        )
    except Exception as exc:
        return CompositeIVResult(symbol, 0.0, None, None, None, 0, f"request-error: {exc}")

    if response.status_code != 200:
        body = response.text.replace("\n", " ")[:240]
        return CompositeIVResult(
            symbol, 0.0, None, None, None, 0,
            f"HTTP {response.status_code}: {body}",
        )

    chain = response.json()
    if chain.get("status") not in (None, "SUCCESS"):
        return CompositeIVResult(
            symbol, 0.0, None, None, None, 0,
            f"chain-status={chain.get('status')}",
        )

    spot = as_finite_float(chain.get("underlyingPrice"))
    if not spot or spot <= 0:
        underlying = chain.get("underlying") or {}
        spot = (
                as_finite_float(underlying.get("mark"))
                or as_finite_float(underlying.get("last"))
                or as_finite_float(underlying.get("close"))
        )

    if not spot or spot <= 0:
        return CompositeIVResult(symbol, 0.0, None, None, None, 0, "no-underlying-price")

    expiries = collect_expiry_iv(chain, spot)
    cm = constant_maturity_iv(expiries, TARGET_DTE)
    if cm is None:
        return CompositeIVResult(symbol, spot, None, None, None, 0, "no-valid-option-iv")

    iv, lower_dte, upper_dte, contracts_used, method = cm
    return CompositeIVResult(
        symbol = symbol,
        underlying_price = spot,
        datetime = datetime.now(),
        iv = iv,
        lower_dte = lower_dte,
        upper_dte = upper_dte,
        contracts_used = contracts_used,
        status = method,
    )


class SchwabIV:
    def __init__(self):
        app_key = os.getenv("SCHWAB_APP_KEY")
        app_secret = os.getenv("SCHWAB_APP_SECRET")
        token_path = os.environ.get("SCHWAB_TOKEN_PATH", "tokens.json")

        if not app_key or not app_secret:
            raise RuntimeError("Missing Schwab credentials")
        try:
            symbols = load_symbols(SYMBOLS_PATH)
        except Exception as exc:
            raise RuntimeError(str(exc))
        if not symbols:
            raise RuntimeError(f"No symbols found in {SYMBOLS_PATH}")

        self.client = client_from_token_file(
            token_path=token_path,
            api_key=app_key,
            app_secret=app_secret,
        )

    def fetch_composite_iv(self, symbol: str) -> CompositeIVResult:
        return fetch_composite_iv(self.client, symbol)