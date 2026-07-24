import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta

st.set_page_config(page_title="Ticker Co-Movement Analyzer", layout="wide")

st.title("📈 Ticker Co-Movement Analyzer")
st.caption(
    "Compare two tickers (stocks, ETFs, or crypto) over a date range and see "
    "what percent of days they moved in the same direction (both up or both down)."
)

# ---------- Helpers ----------

def normalize_ticker(raw: str) -> str:
    """Light cleanup so common crypto shorthand still resolves via yfinance."""
    t = raw.strip().upper()
    crypto_aliases = {
        "BTC": "BTC-USD", "ETH": "ETH-USD", "SOL": "SOL-USD",
        "DOGE": "DOGE-USD", "ADA": "ADA-USD", "XRP": "XRP-USD",
        "LTC": "LTC-USD", "BNB": "BNB-USD", "MATIC": "MATIC-USD",
        "AVAX": "AVAX-USD",
    }
    return crypto_aliases.get(t, t)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_prices(ticker: str, start: date, end: date) -> pd.Series:
    df = yf.download(ticker, start=start, end=end + timedelta(days=1),
                      progress=False, auto_adjust=True)
    if df.empty:
        return pd.Series(dtype=float)
    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close.name = ticker
    return close


def compute_comovement(s1: pd.Series, s2: pd.Series):
    """Return (agreement_pct, merged_df_with_directions, n_days_compared)."""
    df = pd.concat([s1, s2], axis=1).dropna()
    df.columns = ["p1", "p2"]
    if len(df) < 2:
        return None, df, 0

    ret1 = df["p1"].diff().dropna()
    ret2 = df["p2"].diff().dropna()

    dir1 = ret1.apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    dir2 = ret2.apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))

    combined = pd.DataFrame({"dir1": dir1, "dir2": dir2}).dropna()
    # Only count days where both actually moved (exclude flat/no-change days from either)
    moved = combined[(combined["dir1"] != 0) & (combined["dir2"] != 0)]

    if len(moved) == 0:
        return None, combined, 0

    same_direction = (moved["dir1"] == moved["dir2"]).sum()
    agreement_pct = same_direction / len(moved)

    return agreement_pct, combined, len(moved)


# ---------- Sidebar inputs ----------

with st.sidebar:
    st.header("Inputs")
    ticker1_raw = st.text_input("Ticker 1", value="AAPL")
    ticker2_raw = st.text_input("Ticker 2", value="MSFT")

    default_end = date.today()
    default_start = default_end - timedelta(days=180)

    start_date = st.date_input("Start date", value=default_start,
                                max_value=default_end)
    end_date = st.date_input("End date", value=default_end,
                              max_value=default_end)

    st.caption("Tip: for crypto, use tickers like `BTC-USD`, `ETH-USD` "
               "(or just `BTC`, `ETH` — we'll convert common ones for you).")

    run = st.button("Analyze", type="primary", use_container_width=True)

# ---------- Main logic ----------

if run:
    if start_date >= end_date:
        st.error("Start date must be before end date.")
        st.stop()

    t1 = normalize_ticker(ticker1_raw)
    t2 = normalize_ticker(ticker2_raw)

    if not t1 or not t2:
        st.error("Please enter both tickers.")
        st.stop()

    with st.spinner(f"Fetching data for {t1} and {t2}..."):
        s1 = fetch_prices(t1, start_date, end_date)
        s2 = fetch_prices(t2, start_date, end_date)

    if s1.empty:
        st.error(f"Couldn't find data for '{t1}'. Check the ticker symbol.")
        st.stop()
    if s2.empty:
        st.error(f"Couldn't find data for '{t2}'. Check the ticker symbol.")
        st.stop()

    agreement_pct, direction_df, n_days = compute_comovement(s1, s2)

    if agreement_pct is None:
        st.error("Not enough overlapping trading days to compare these two tickers "
                  "in the selected range.")
        st.stop()

    # --- Metric ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Co-movement", f"{agreement_pct:.2f}")
    col2.metric("Days compared", n_days)
    col3.metric("Days moved together", int((direction_df.loc[
        (direction_df['dir1'] != 0) & (direction_df['dir2'] != 0), 'dir1'
    ] == direction_df.loc[
        (direction_df['dir1'] != 0) & (direction_df['dir2'] != 0), 'dir2'
    ]).sum()))

    st.markdown(
        f"**{t1}** and **{t2}** moved in the same direction "
        f"(**{agreement_pct*100:.1f}%**) of the days compared between "
        f"**{start_date}** and **{end_date}**."
    )

    # --- Chart: dual y-axis price chart ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=s1.index, y=s1.values, name=t1, yaxis="y1", mode="lines"
    ))
    fig.add_trace(go.Scatter(
        x=s2.index, y=s2.values, name=t2, yaxis="y2", mode="lines"
    ))

    fig.update_layout(
        title=f"{t1} vs {t2} — Price Chart ({start_date} to {end_date})",
        xaxis=dict(title="Date"),
        yaxis=dict(title=f"{t1} Price", side="left"),
        yaxis2=dict(title=f"{t2} Price", side="right", overlaying="y"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=550,
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("See daily direction data"):
        display_df = direction_df.copy()
        display_df.columns = [f"{t1} direction", f"{t2} direction"]
        display_df = display_df.replace({1: "Up", -1: "Down", 0: "Flat"})
        st.dataframe(display_df, use_container_width=True)

else:
    st.info("Enter two tickers and a date range in the sidebar, then click **Analyze**.")
