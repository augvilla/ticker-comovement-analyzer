import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta

st.set_page_config(page_title="Co-Movement Analyzer", layout="wide", initial_sidebar_state="collapsed")

# ---------------------------------------------------------------------------
# Terminal styling — jet black, amber/orange monospace, no rounded corners.
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');

    html, body, [class*="css"]  {
        font-family: 'IBM Plex Mono', 'Consolas', monospace !important;
    }

    /* Base canvas */
    .stApp {
        background-color: #000000;
        color: #FF8C00;
    }
    section[data-testid="stSidebar"] { display: none; }
    header[data-testid="stHeader"] { background-color: #000000; }
    div.block-container { padding-top: 1.2rem; max-width: 1400px; }

    /* Headings */
    h1, h2, h3, h4, h5, h6 { color: #FF8C00 !important; letter-spacing: 0.5px; }
    p, span, label, .stMarkdown, .stCaption { color: #FFB84D !important; }

    .term-subtitle {
        color: #7A5A2E !important;
        font-size: 0.78rem;
        letter-spacing: 1px;
        margin-top: -6px;
        margin-bottom: 10px;
    }

    .term-title {
        color: #FF8C00 !important;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 700;
        font-size: 2.4rem;
        letter-spacing: 0.5px;
        margin-top: 0.6em;
        margin-bottom: 6px;
    }

    /* Command bar container (native st.container(border=True)) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #FF8C00 !important;
        border-radius: 0px !important;
        background-color: #050505 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] > div { border-radius: 0px !important; }

    .term-label {
        color: #FF8C00 !important;
        font-size: 0.7rem;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 2px;
    }

    /* Text inputs */
    .stTextInput input {
        background-color: #000000 !important;
        color: #FF8C00 !important;
        border: 1px solid #FF8C00 !important;
        border-radius: 0px !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-weight: 600;
        caret-color: #FF8C00;
    }
    .stTextInput input:focus {
        box-shadow: 0 0 0 1px #FF8C00 !important;
        border: 1px solid #FFB84D !important;
    }

    /* Date inputs */
    .stDateInput input {
        background-color: #000000 !important;
        color: #FF8C00 !important;
        border: 1px solid #FF8C00 !important;
        border-radius: 0px !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-weight: 600;
    }
    div[data-baseweb="calendar"] { background-color: #000000 !important; }

    /* Buttons */
    .stButton button {
        background-color: #000000;
        color: #FF8C00;
        border: 1px solid #FF8C00;
        border-radius: 0px;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 700;
        letter-spacing: 1px;
        width: 100%;
        transition: none;
    }
    .stButton button:hover {
        background-color: #FF8C00;
        color: #000000;
        border: 1px solid #FF8C00;
    }

    /* Metrics */
    div[data-testid="stMetric"] {
        background-color: #050505;
        border: 1px solid #FF8C00;
        padding: 10px 14px;
    }
    div[data-testid="stMetricLabel"] {
        color: #FF8C00 !important;
        font-size: 0.7rem;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }
    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-weight: 700;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #050505 !important;
        color: #FF8C00 !important;
        border: 1px solid #FF8C00 !important;
        border-radius: 0px !important;
    }
    div[data-testid="stExpander"] { border: none; }

    /* Dataframe */
    div[data-testid="stDataFrame"] { border: 1px solid #FF8C00; }

    /* Alerts */
    div[data-testid="stAlert"] {
        background-color: #050505;
        color: #FF8C00;
        border: 1px solid #FF8C00;
        border-radius: 0px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------
# Preferred: configure allowed users in Streamlit secrets (Settings > Secrets
# on Streamlit Community Cloud, or a local .streamlit/secrets.toml) as:
#
# [[allowed_users]]
# first_name = "Augustine"
# last_name = "Villalobos"
#
# [[allowed_users]]
# first_name = "David"
# last_name = "Villalobos"
#
# Falls back to the same two names below if no secrets are configured, so
# the app still works immediately without extra setup.

DEFAULT_ALLOWED_USERS = {("augustine", "villalobos"), ("david", "villalobos")}

def get_allowed_users() -> set:
    try:
        configured = st.secrets.get("allowed_users", None)
    except Exception:
        configured = None
    if not configured:
        return DEFAULT_ALLOWED_USERS
    return {
        (entry["first_name"].strip().lower(), entry["last_name"].strip().lower())
        for entry in configured
    }


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


def render_login():
    st.markdown("<br>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.1, 1])
    with mid:
        with st.container(border=True):
            st.markdown("### RESTRICTED ACCESS")
            st.caption("ENTER YOUR FIRST AND LAST NAME TO CONTINUE")
            with st.form("login_form"):
                first = st.text_input("First name", placeholder="FIRST NAME")
                last = st.text_input("Last name", placeholder="LAST NAME")
                submitted = st.form_submit_button("ACCESS TERMINAL", use_container_width=True)

            if submitted:
                key = (first.strip().lower(), last.strip().lower())
                if key in get_allowed_users() and first.strip() and last.strip():
                    st.session_state.authenticated = True
                    st.session_state.user_first_name = first.strip().title()
                    st.rerun()
                else:
                    st.error("ACCESS DENIED — NAME NOT RECOGNIZED.")


if not st.session_state.authenticated:
    st.markdown('<div class="term-title">TICKER CO-MOVEMENT ANALYZER</div>', unsafe_allow_html=True)
    st.markdown('<div class="term-subtitle">CREATED BY AUGUSTINE VILLALOBOS</div>', unsafe_allow_html=True)
    render_login()
    st.stop()

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


# ---------- Header ----------

st.markdown('<div class="term-title">TICKER CO-MOVEMENT ANALYZER</div>', unsafe_allow_html=True)
st.markdown('<div class="term-subtitle">CREATED BY AUGUSTINE VILLALOBOS</div>', unsafe_allow_html=True)
st.caption("TICKER CO-MOVEMENT TERMINAL  |  TWO SYMBOLS  |  ANY RANGE  |  DIRECTION AGREEMENT PERCENTAGE")

# ---------- Top command bar (always visible, not collapsible) ----------

default_start = date(date.today().year, 1, 1)  # YTD
default_end = date.today()

with st.container(border=True):
    c1, c2, c3, c4, c5 = st.columns([1.1, 1.1, 1, 1, 0.8])

    with c1:
        st.markdown('<div class="term-label">TICKER 1</div>', unsafe_allow_html=True)
        ticker1_raw = st.text_input("Ticker 1", value="SPY", label_visibility="collapsed")
    with c2:
        st.markdown('<div class="term-label">TICKER 2</div>', unsafe_allow_html=True)
        ticker2_raw = st.text_input("Ticker 2", value="TLT", label_visibility="collapsed")
    with c3:
        st.markdown('<div class="term-label">START DATE</div>', unsafe_allow_html=True)
        start_date = st.date_input("Start date", value=default_start,
                                    max_value=default_end, label_visibility="collapsed")
    with c4:
        st.markdown('<div class="term-label">END DATE</div>', unsafe_allow_html=True)
        end_date = st.date_input("End date", value=default_end,
                                  max_value=default_end, label_visibility="collapsed")
    with c5:
        st.markdown('<div class="term-label">&nbsp;</div>', unsafe_allow_html=True)
        run = st.button("ANALYZE", type="primary", use_container_width=True)

    st.caption("CRYPTO: USE -USD SUFFIX (E.G. BTC-USD)  |  SHORTHAND BTC / ETH / SOL ETC. AUTO-CONVERTED")

st.write("")

# ---------- Main logic ----------

if run:
    if start_date >= end_date:
        st.error("START DATE MUST BE BEFORE END DATE.")
        st.stop()

    t1 = normalize_ticker(ticker1_raw)
    t2 = normalize_ticker(ticker2_raw)

    if not t1 or not t2:
        st.error("PLEASE ENTER BOTH TICKERS.")
        st.stop()

    with st.spinner(f"FETCHING {t1} / {t2}..."):
        s1 = fetch_prices(t1, start_date, end_date)
        s2 = fetch_prices(t2, start_date, end_date)

    if s1.empty:
        st.error(f"NO DATA FOR '{t1}'. CHECK TICKER SYMBOL.")
        st.stop()
    if s2.empty:
        st.error(f"NO DATA FOR '{t2}'. CHECK TICKER SYMBOL.")
        st.stop()

    agreement_pct, direction_df, n_days = compute_comovement(s1, s2)

    if agreement_pct is None:
        st.error("NOT ENOUGH OVERLAPPING TRADING DAYS TO COMPARE THESE TICKERS IN THE SELECTED RANGE.")
        st.stop()

    moved_mask = (direction_df['dir1'] != 0) & (direction_df['dir2'] != 0)
    days_together = int((direction_df.loc[moved_mask, 'dir1'] == direction_df.loc[moved_mask, 'dir2']).sum())

    corr_value = 2 * agreement_pct - 1

    col1, col2, col3 = st.columns(3)
    col1.metric("CORRELATION", f"{corr_value:.2f}")
    col2.metric("DAYS COMPARED", n_days)
    col3.metric("DAYS MOVED TOGETHER", days_together)

    st.markdown(
        f"**{t1}** and **{t2}** moved in the same direction "
        f"(**{agreement_pct*100:.1f}%**) of the days compared between "
        f"**{start_date}** and **{end_date}**."
    )

    # --- Chart: dual y-axis price chart, terminal styling ---
    RED = "#FF1E1E"
    BLUE = "#1E90FF"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=s1.index, y=s1.values, name=t1, yaxis="y1", mode="lines",
        line=dict(color=RED, width=2.4)
    ))
    fig.add_trace(go.Scatter(
        x=s2.index, y=s2.values, name=t2, yaxis="y2", mode="lines",
        line=dict(color=BLUE, width=2.4)
    ))

    fig.update_layout(
        title=dict(text=f"{t1} VS {t2}  |  {start_date} TO {end_date}",
                    font=dict(color="#FF8C00", family="IBM Plex Mono")),
        xaxis=dict(title="DATE", color="#FF8C00", gridcolor="#2a2a2a",
                   griddash="dot", showline=True, linecolor="#FF8C00"),
        yaxis=dict(title=f"{t1} PRICE", color=RED, gridcolor="#2a2a2a",
                   griddash="dot", showline=True, linecolor=RED),
        yaxis2=dict(title=f"{t2} PRICE", color=BLUE, overlaying="y", side="right",
                    showline=True, linecolor=BLUE),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(color="#FF8C00", family="IBM Plex Mono")),
        hovermode="x unified",
        height=550,
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font=dict(family="IBM Plex Mono", color="#FF8C00"),
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("SEE DAILY DIRECTION DATA"):
        display_df = direction_df.copy()
        display_df.columns = [f"{t1} DIRECTION", f"{t2} DIRECTION"]
        display_df = display_df.replace({1: "UP", -1: "DOWN", 0: "FLAT"})
        st.dataframe(display_df, use_container_width=True)

else:
    st.info("ENTER TWO TICKERS AND A DATE RANGE ABOVE, THEN PRESS ANALYZE.")
