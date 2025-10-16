from __future__ import annotations
from typing import List, Tuple, Optional
import numpy as np
import plotly.graph_objects as go


def plot_lattice(lattice: List[List[float]], title: str, show_edges: bool = True) -> go.Figure:
    x_vals = []
    y_vals = []
    texts = []
    for i, level in enumerate(lattice):
        for j, v in enumerate(level):
            x_vals.append(i)
            y_vals.append(2 * j - i)
            texts.append(f"{v:.4f}")

    node_trace = go.Scatter(
        x=x_vals,
        y=y_vals,
        mode="markers+text",
        text=texts,
        textposition="top center",
        marker=dict(size=10, color="#2E86DE"),
        hoverinfo="text",
        name="Nodes",
    )

    fig = go.Figure()
    if show_edges:
        edge_x = []
        edge_y = []
        for i in range(len(lattice) - 1):
            for j in range(i + 1):
                x0, y0 = i, 2 * j - i
                # to up node
                x1, y1 = i + 1, 2 * (j + 1) - (i + 1)
                edge_x += [x0, x1, None]
                edge_y += [y0, y1, None]
                # to down node
                x2, y2 = i + 1, 2 * j - (i + 1)
                edge_x += [x0, x2, None]
                edge_y += [y0, y2, None]
        fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(color="#B2BEC3", width=1), hoverinfo="skip", showlegend=False))

    fig.add_trace(node_trace)
    fig.update_layout(
        title=title,
        xaxis=dict(title="Step", showgrid=False, zeroline=False),
        yaxis=dict(title="State", showgrid=False, zeroline=False),
        template="plotly_white",
        margin=dict(l=10, r=10, t=50, b=10),
        height=500,
    )
    return fig


def plot_payoff_profit(S: np.ndarray, payoff: np.ndarray, profit: np.ndarray, breakevens: Optional[List[float]] = None) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=S, y=payoff, mode="lines", name="Payoff", line=dict(color="#2ecc71", width=2)))
    fig.add_trace(go.Scatter(x=S, y=profit, mode="lines", name="Profit", line=dict(color="#e74c3c", width=2)))

    if breakevens:
        for be in breakevens:
            fig.add_vline(x=be, line=dict(color="#7f8c8d", width=1, dash="dash"))

    fig.update_layout(
        title="Payoff and Profit at Expiry",
        xaxis_title="Underlying Price at Expiry",
        yaxis_title="Value",
        template="plotly_white",
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def plot_terminal_distribution(S_T: np.ndarray, probs: np.ndarray) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=S_T, y=probs, marker=dict(color="#9b59b6"), name="P(S_T)"))
    fig.update_layout(
        title="Terminal Price Distribution (Risk-Neutral)",
        xaxis_title="S_T",
        yaxis_title="Probability",
        template="plotly_white",
        height=450,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig
