from __future__ import annotations
from dataclasses import dataclass
from typing import List, Literal, Optional, Tuple, Dict
import numpy as np

from .model import OptionParams, price_option

LegType = Literal["call", "put"]
LegSide = Literal["long", "short"]


@dataclass
class OptionLeg:
    kind: LegType
    side: LegSide
    quantity: int
    strike: float
    premium_override: Optional[float] = None

    def signed(self) -> int:
        return 1 if self.side == "long" else -1


@dataclass
class Strategy:
    name: str
    legs: List[OptionLeg]


@dataclass
class BreakevenResult:
    breakevens: List[float]
    max_profit: Optional[float]
    max_loss: Optional[float]


StrategyTemplate = Literal[
    "Long Call",
    "Short Call",
    "Long Put",
    "Short Put",
    "Bull Call Spread",
    "Bear Call Spread",
    "Bull Put Spread",
    "Bear Put Spread",
    "Long Straddle",
    "Short Straddle",
    "Long Strangle",
    "Short Strangle",
    "Long Call Butterfly",
]


def _payoff_for_leg(kind: LegType, side: LegSide, strike: float, S: np.ndarray) -> np.ndarray:
    if kind == "call":
        base = np.maximum(0.0, S - strike)
    else:
        base = np.maximum(0.0, strike - S)
    return base if side == "long" else -base


def evaluate_strategy(
    strategy: Strategy,
    base_params: OptionParams,
    S_grid: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, Dict[int, float], float, BreakevenResult]:
    # Price each leg with CRR unless premium_override provided
    leg_prices: Dict[int, float] = {}
    total_premium: float = 0.0
    for idx, leg in enumerate(strategy.legs):
        params = OptionParams(
            S0=base_params.S0,
            K=leg.strike,
            r=base_params.r,
            q=base_params.q,
            sigma=base_params.sigma,
            T=base_params.T,
            n=base_params.n,
            option_type="call" if leg.kind == "call" else "put",
            exercise=base_params.exercise,
        )
        model_price = price_option(params)
        used_price = model_price if leg.premium_override is None else float(leg.premium_override)
        leg_prices[idx] = used_price
        total_premium += leg.quantity * leg.signed() * used_price

    payoff = np.zeros_like(S_grid, dtype=float)
    for leg in strategy.legs:
        payoff += leg.quantity * _payoff_for_leg(leg.kind, leg.side, leg.strike, S_grid)

    profit = payoff - total_premium

    ber = _breakevens_and_extrema(S_grid, profit)
    return payoff, profit, leg_prices, total_premium, ber


def _breakevens_and_extrema(S: np.ndarray, profit: np.ndarray) -> BreakevenResult:
    zeros: List[float] = []
    for i in range(1, len(S)):
        y0, y1 = profit[i - 1], profit[i]
        if (y0 == 0) or (y1 == 0):
            if y0 == 0:
                zeros.append(float(S[i - 1]))
            if y1 == 0:
                zeros.append(float(S[i]))
        elif (y0 < 0 and y1 > 0) or (y0 > 0 and y1 < 0):
            x0, x1 = S[i - 1], S[i]
            # Linear interpolation
            x = x0 + (0 - y0) * (x1 - x0) / (y1 - y0)
            zeros.append(float(x))

    max_profit = float(np.max(profit)) if np.isfinite(np.max(profit)) else None
    min_profit = float(np.min(profit)) if np.isfinite(np.min(profit)) else None
    # For common strategies, min_profit is bounded; leave None if +/- inf not present
    return BreakevenResult(breakevens=sorted(set([round(z, 6) for z in zeros])), max_profit=max_profit, max_loss=min_profit)


def build_strategy_from_template(
    template: StrategyTemplate,
    K1: float,
    K2: Optional[float] = None,
    K3: Optional[float] = None,
    qty: int = 1,
) -> Strategy:
    if qty <= 0:
        raise ValueError("Quantity must be positive")

    if template == "Long Call":
        return Strategy(template, [OptionLeg("call", "long", qty, K1)])
    if template == "Short Call":
        return Strategy(template, [OptionLeg("call", "short", qty, K1)])
    if template == "Long Put":
        return Strategy(template, [OptionLeg("put", "long", qty, K1)])
    if template == "Short Put":
        return Strategy(template, [OptionLeg("put", "short", qty, K1)])

    if template == "Bull Call Spread":
        if K2 is None or not (K1 < K2):
            raise ValueError("Bull Call: require K1 < K2")
        return Strategy(template, [
            OptionLeg("call", "long", qty, K1),
            OptionLeg("call", "short", qty, K2),
        ])
    if template == "Bear Call Spread":
        if K2 is None or not (K1 < K2):
            raise ValueError("Bear Call: require K1 < K2")
        return Strategy(template, [
            OptionLeg("call", "short", qty, K1),
            OptionLeg("call", "long", qty, K2),
        ])
    if template == "Bull Put Spread":
        if K2 is None or not (K1 < K2):
            raise ValueError("Bull Put: require K1 < K2")
        return Strategy(template, [
            OptionLeg("put", "short", qty, K2),
            OptionLeg("put", "long", qty, K1),
        ])
    if template == "Bear Put Spread":
        if K2 is None or not (K1 < K2):
            raise ValueError("Bear Put: require K1 < K2")
        return Strategy(template, [
            OptionLeg("put", "long", qty, K2),
            OptionLeg("put", "short", qty, K1),
        ])
    if template == "Long Straddle":
        return Strategy(template, [
            OptionLeg("call", "long", qty, K1),
            OptionLeg("put", "long", qty, K1),
        ])
    if template == "Short Straddle":
        return Strategy(template, [
            OptionLeg("call", "short", qty, K1),
            OptionLeg("put", "short", qty, K1),
        ])
    if template == "Long Strangle":
        if K2 is None or not (K1 < K2):
            raise ValueError("Strangle: require K1 < K2")
        return Strategy(template, [
            OptionLeg("put", "long", qty, K1),
            OptionLeg("call", "long", qty, K2),
        ])
    if template == "Short Strangle":
        if K2 is None or not (K1 < K2):
            raise ValueError("Strangle: require K1 < K2")
        return Strategy(template, [
            OptionLeg("put", "short", qty, K1),
            OptionLeg("call", "short", qty, K2),
        ])
    if template == "Long Call Butterfly":
        if K2 is None or K3 is None or not (K1 < K2 < K3):
            raise ValueError("Butterfly: require K1 < K2 < K3")
        return Strategy(template, [
            OptionLeg("call", "long", qty, K1),
            OptionLeg("call", "short", qty * 2, K2),
            OptionLeg("call", "long", qty, K3),
        ])

    raise ValueError("Unknown template")
