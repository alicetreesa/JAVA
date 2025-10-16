from __future__ import annotations
import numpy as np
import streamlit as st

from crr.model import OptionParams, build_stock_lattice, build_option_lattice, price_option, terminal_distribution
from crr.strategies import Strategy, OptionLeg, StrategyTemplate, build_strategy_from_template, evaluate_strategy
from crr.plots import plot_lattice, plot_payoff_profit, plot_terminal_distribution

st.set_page_config(page_title="CRR Options Analytics Dashboard", layout="wide", page_icon="📈")

CSS = """
<style>
/**** Global ****/
section.main > div { padding-top: 1rem; }

/**** Header ****/
.block-container { padding-top: 1rem; }
.header {
  background: linear-gradient(90deg, #0f2027, #203a43, #2c5364);
  color: white; border-radius: 12px; padding: 18px 20px; margin-bottom: 8px;
}
.header h1 { margin: 0; font-size: 1.6rem; }
.header p { margin: 0; opacity: 0.85; }

/**** Cards ****/
.card { background: white; border: 1px solid #eef2f7; border-radius: 10px; padding: 14px; }
.card h4 { margin-top: 0; margin-bottom: 8px; }

/* Tighten up plot spacing */
.css-1dp5vir, .css-ocqkz7 { padding-top: 0 !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

st.markdown(
    """
<div class="header">
  <h1>Interactive Binomial (CRR) Options Analytics Dashboard</h1>
  <p>Visualize pricing, lattices, and strategy payoffs with dividend yield and American/European exercise.</p>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("Model Inputs")
    col1, col2 = st.columns(2)
    with col1:
        S0 = st.number_input("Spot (S0)", value=100.0, min_value=0.01, step=1.0, format="%0.2f")
        sigma_pct = st.number_input("Volatility (σ, % p.a.)", value=20.0, min_value=0.0, step=0.5, format="%0.2f")
        T = st.number_input("Maturity (T, years)", value=1.0, min_value=0.01, step=0.05, format="%0.2f")
    with col2:
        r_pct = st.number_input("Risk-free rate (r, % p.a.)", value=5.0, min_value=-10.0, step=0.25, format="%0.2f")
        q_pct = st.number_input("Dividend yield (q, % p.a.)", value=0.0, min_value=0.0, step=0.25, format="%0.2f")
        n = st.slider("Time steps (n)", min_value=1, max_value=250, value=75)

    st.caption("CRR uses risk-neutral p = (e^{(r-q)Δt} - d) / (u - d), u = e^{σ√Δt}, d = 1/u")

    st.subheader("Single Option")
    colk = st.columns(3)
    with colk[0]:
        K = st.number_input("Strike (K)", value=100.0, min_value=0.01, step=1.0, format="%0.2f")
    with colk[1]:
        opt_type = st.selectbox("Type", ["call", "put"], index=0)
    with colk[2]:
        exercise = st.selectbox("Exercise", ["european", "american"], index=0)
    premium_override = st.number_input("Premium override (optional)", value=0.0, min_value=0.0, step=0.1, format="%0.4f")
    use_override = st.checkbox("Use override for profit calc", value=False)

params = OptionParams(
    S0=S0,
    K=K,
    r=r_pct / 100.0,
    q=q_pct / 100.0,
    sigma=sigma_pct / 100.0,
    T=T,
    n=int(n),
    option_type=opt_type,  # type: ignore
    exercise=exercise,  # type: ignore
)

st.write(" ")

single_tab, strategies_tab, custom_tab, dist_tab = st.tabs([
    "Single Option",
    "Strategy Templates",
    "Custom Strategy",
    "Terminal Distribution",
])

with single_tab:
    colA, colB, colC = st.columns([1,1,1])
    price = price_option(params)
    display_premium = premium_override if (use_override and premium_override > 0) else price
    with colA:
        st.metric("CRR Price", f"{price:,.4f}")
    with colB:
        st.metric("Premium used (profit)", f"{display_premium:,.4f}")
    with colC:
        st.metric("Dividend yield", f"{q_pct:.2f}%")

    st.markdown("---")

    # Lattices
    if params.n <= 25:
        stock_lat = build_stock_lattice(params)
        opt_lat = build_option_lattice(params)
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(plot_lattice(stock_lat, "Stock Lattice"), use_container_width=True)
        with c2:
            st.plotly_chart(plot_lattice(opt_lat, "Option Lattice"), use_container_width=True)
    else:
        st.info("For readability, lattice plots are shown only when n ≤ 25.")

    # Payoff/Profit
    S_grid = np.linspace(max(0.0, S0 * 0.05), S0 * 2.5, 400)
    if opt_type == "call":
        payoff = np.maximum(0.0, S_grid - K)
    else:
        payoff = np.maximum(0.0, K - S_grid)
    if exercise == "american":
        st.caption("Payoff at expiry is identical for European and American; profit uses selected premium.")
    profit = payoff - display_premium

    # Breakeven(s)
    zeros = []
    for i in range(1, len(S_grid)):
        y0, y1 = profit[i - 1], profit[i]
        if (y0 == 0) or (y1 == 0):
            if y0 == 0: zeros.append(float(S_grid[i - 1]))
            if y1 == 0: zeros.append(float(S_grid[i]))
        elif (y0 < 0 and y1 > 0) or (y0 > 0 and y1 < 0):
            x0, x1 = S_grid[i - 1], S_grid[i]
            x = x0 + (0 - y0) * (x1 - x0) / (y1 - y0)
            zeros.append(float(x))
    st.plotly_chart(plot_payoff_profit(S_grid, payoff, profit, sorted(set([round(z, 6) for z in zeros]))), use_container_width=True)

    st.caption(f"Legs: calls: {1 if opt_type=='call' else 0}, puts: {1 if opt_type=='put' else 0}. Exercise: {exercise}.")

with strategies_tab:
    st.subheader("Strategy Templates")
    template: StrategyTemplate = st.selectbox(
        "Choose a strategy",
        [
            "Long Call", "Short Call", "Long Put", "Short Put",
            "Bull Call Spread", "Bear Call Spread", "Bull Put Spread", "Bear Put Spread",
            "Long Straddle", "Short Straddle", "Long Strangle", "Short Strangle",
            "Long Call Butterfly",
        ],
        index=0,
    )
    qty = st.number_input("Contract quantity", value=1, min_value=1, step=1)

    K1 = st.number_input("K1", value=float(K), step=1.0)
    needs_K2 = template in {"Bull Call Spread", "Bear Call Spread", "Bull Put Spread", "Bear Put Spread", "Long Strangle", "Short Strangle", "Long Call Butterfly"}
    needs_K3 = template in {"Long Call Butterfly"}
    K2 = None
    K3 = None
    if needs_K2:
        K2 = st.number_input("K2", value=float(K * 1.1), step=1.0)
    if needs_K3:
        K3 = st.number_input("K3", value=float(K * 1.2), step=1.0)

    try:
        strategy = build_strategy_from_template(template, K1, K2, K3, int(qty))
        leg_count_call = sum(leg.quantity for leg in strategy.legs if leg.kind == "call")
        leg_count_put = sum(leg.quantity for leg in strategy.legs if leg.kind == "put")
        st.caption(f"Legs: calls: {leg_count_call}, puts: {leg_count_put}. All legs share T, n, r, q, σ.")
        S_grid = np.linspace(max(0.0, S0 * 0.05), S0 * 2.5, 500)
        payoff, profit, leg_prices, total_prem, ber = evaluate_strategy(strategy, params, S_grid)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Net premium (debit+/credit-)", f"{total_prem:,.4f}")
        with col2:
            st.metric("Max profit (grid)", f"{ber.max_profit:,.4f}")
        with col3:
            st.metric("Max loss (grid)", f"{ber.max_loss:,.4f}")
        st.plotly_chart(plot_payoff_profit(S_grid, payoff, profit, ber.breakevens), use_container_width=True)
    except Exception as e:
        st.error(str(e))

with custom_tab:
    st.subheader("Custom Strategy (Add Legs)")
    num_legs = st.number_input("Number of legs", min_value=1, max_value=10, value=2, step=1)

    legs: list[OptionLeg] = []
    with st.form("custom_legs"):
        for i in range(int(num_legs)):
            st.markdown(f"**Leg {i+1}**")
            c1, c2, c3, c4, c5 = st.columns([1,1,1,1,1])
            with c1:
                kind = st.selectbox(f"Type {i+1}", ["call", "put"], key=f"kind_{i}")
            with c2:
                side = st.selectbox(f"Side {i+1}", ["long", "short"], key=f"side_{i}")
            with c3:
                qty_i = st.number_input(f"Qty {i+1}", min_value=1, value=1, step=1, key=f"qty_{i}")
            with c4:
                strike = st.number_input(f"Strike {i+1}", min_value=0.01, value=K + i * 5.0, step=1.0, key=f"strike_{i}")
            with c5:
                prem_ovr = st.text_input(f"Premium {i+1} (optional)", value="", key=f"prem_{i}")
            po = float(prem_ovr) if prem_ovr.strip() != "" else None
            legs.append(OptionLeg(kind=kind, side=side, quantity=int(qty_i), strike=float(strike), premium_override=po))
        submitted = st.form_submit_button("Evaluate Strategy")

    if submitted:
        strategy = Strategy("Custom", legs)
        leg_count_call = sum(leg.quantity for leg in strategy.legs if leg.kind == "call")
        leg_count_put = sum(leg.quantity for leg in strategy.legs if leg.kind == "put")
        st.caption(f"Legs: calls: {leg_count_call}, puts: {leg_count_put}.")
        S_grid = np.linspace(max(0.0, S0 * 0.05), S0 * 2.5, 700)
        payoff, profit, leg_prices, total_prem, ber = evaluate_strategy(strategy, params, S_grid)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Net premium (debit+/credit-)", f"{total_prem:,.4f}")
        with col2:
            st.metric("Max profit (grid)", f"{ber.max_profit:,.4f}")
        with col3:
            st.metric("Max loss (grid)", f"{ber.max_loss:,.4f}")
        st.plotly_chart(plot_payoff_profit(S_grid, payoff, profit, ber.breakevens), use_container_width=True)

with dist_tab:
    st.subheader("Risk-Neutral Terminal Distribution")
    S_T, probs = terminal_distribution(params)
    st.plotly_chart(plot_terminal_distribution(S_T, probs), use_container_width=True)
    EN = float((S_T * probs).sum())
    st.caption(f"E[S_T] (risk-neutral) ≈ {EN:.4f}")

st.markdown("---")

st.markdown(
    """
<div class="card">
  <h4>Notes</h4>
  <ul>
    <li>Risk-neutral probability uses dividend yield q; American exercise uses early-exercise check at each node.</li>
    <li>Strategy templates enforce common constraints (e.g., spread strike ordering, butterfly 1:-2:1).</li>
    <li>Use the premium override to analyze P/L given a market price.</li>
  </ul>
</div>
""",
    unsafe_allow_html=True,
)
