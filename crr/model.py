from __future__ import annotations
from dataclasses import dataclass
from typing import List, Literal, Tuple, Dict
import math
import numpy as np

OptionType = Literal["call", "put"]
ExerciseType = Literal["european", "american"]


@dataclass
class OptionParams:
    S0: float
    K: float
    r: float  # risk-free rate (annual, continuous comp.)
    q: float  # dividend yield (annual, continuous comp.)
    sigma: float  # volatility (annual)
    T: float  # time to maturity in years
    n: int  # number of steps
    option_type: OptionType
    exercise: ExerciseType


def compute_crr_parameters(params: OptionParams) -> Dict[str, float]:
    if params.n <= 0:
        raise ValueError("n must be positive")
    if params.T <= 0:
        raise ValueError("T must be positive")
    dt = params.T / params.n
    if dt <= 0:
        raise ValueError("Invalid dt")

    u = math.exp(params.sigma * math.sqrt(dt))
    d = 1.0 / u
    growth = math.exp((params.r - params.q) * dt)
    denom = (u - d)
    if denom == 0:
        raise ValueError("u equals d; invalid parameters")
    p = (growth - d) / denom
    # Numerical guard: clamp to [0,1]
    p = max(0.0, min(1.0, p))
    disc = math.exp(-params.r * dt)
    return {"u": u, "d": d, "p": p, "dt": dt, "disc": disc}


def build_stock_lattice(params: OptionParams) -> List[List[float]]:
    c = compute_crr_parameters(params)
    u, d = c["u"], c["d"]
    stock: List[List[float]] = []
    for i in range(params.n + 1):
        level = [params.S0 * (u ** j) * (d ** (i - j)) for j in range(i + 1)]
        stock.append(level)
    return stock


def build_option_lattice(params: OptionParams) -> List[List[float]]:
    stock = build_stock_lattice(params)
    c = compute_crr_parameters(params)
    p, disc = c["p"], c["disc"]

    # terminal payoffs
    last = stock[-1]
    if params.option_type == "call":
        values = [max(0.0, s - params.K) for s in last]
    else:
        values = [max(0.0, params.K - s) for s in last]

    opt_lattice: List[List[float]] = [None] * (params.n + 1)
    opt_lattice[-1] = values

    for i in range(params.n - 1, -1, -1):
        level_vals: List[float] = []
        for j in range(i + 1):
            cont = disc * (p * opt_lattice[i + 1][j + 1] + (1 - p) * opt_lattice[i + 1][j])
            if params.exercise == "american":
                s_ij = stock[i][j]
                if params.option_type == "call":
                    intrinsic = max(0.0, s_ij - params.K)
                else:
                    intrinsic = max(0.0, params.K - s_ij)
                level_vals.append(max(cont, intrinsic))
            else:
                level_vals.append(cont)
        opt_lattice[i] = level_vals

    return opt_lattice


def price_option(params: OptionParams) -> float:
    lattice = build_option_lattice(params)
    return float(lattice[0][0])


def terminal_distribution(params: OptionParams) -> Tuple[np.ndarray, np.ndarray]:
    c = compute_crr_parameters(params)
    u, d, p = c["u"], c["d"], c["p"]
    n = params.n
    S_T = np.array([params.S0 * (u ** j) * (d ** (n - j)) for j in range(n + 1)], dtype=float)

    # Stable discrete binomial probabilities via multiplicative recursion
    probs = np.zeros(n + 1, dtype=float)
    probs[0] = (1 - p) ** n
    for j in range(1, n + 1):
        probs[j] = probs[j - 1] * (p / (1 - p)) * (n - j + 1) / j if (1 - p) > 0 else 0.0
    # Guard against numerical drift
    total = probs.sum()
    if total > 0:
        probs /= total

    return S_T, probs
