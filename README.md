# Ticker Co-Movement Analyzer

Enter two tickers (stocks, ETFs, or crypto) and a date range. The app plots
both price charts and reports what percent of trading days the two tickers
moved in the same direction (both up or both down).

## How the metric works

For each day in range:
- Compute each ticker's price change vs. the prior day (up / down / flat).
- Days where either ticker is flat (no change) are excluded from the count.
- Co-movement = (days both moved the same direction) / (days both moved at all).

Example: Stock A goes up every day, Stock B goes up on half the days →
co-movement = 0.50.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints (usually http://localhost:8501).

## Push to GitHub

From inside this project folder:

```bash
git init
git add .
git commit -m "Initial commit: ticker co-movement analyzer"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git push -u origin main
```

(Create the empty repo on GitHub first at github.com/new — don't
initialize it with a README so there's no merge conflict.)

## Deploy to Streamlit Community Cloud

1. Go to https://share.streamlit.io and sign in with GitHub.
2. Click **New app**.
3. Pick your repo, the `main` branch, and set the main file path to `app.py`.
4. Click **Deploy**. Streamlit installs `requirements.txt` automatically and
   gives you a public URL.

## Notes

- Crypto tickers on Yahoo Finance use the `-USD` suffix, e.g. `BTC-USD`,
  `ETH-USD`. The app auto-converts a handful of common shorthand symbols
  (`BTC`, `ETH`, `SOL`, etc.), but for anything else use the `-USD` form.
- Data comes from Yahoo Finance via the `yfinance` library — free, no API
  key needed, but occasionally rate-limits on very heavy use.
