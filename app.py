from flask import Flask, render_template, jsonify, request
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json
import urllib.request

app = Flask(__name__)

# ── Data source registry ──────────────────────────────────────────────────────
DATA_SOURCES = {
    "yahoo":   {"label": "Yahoo Finance",        "note": "Gratuit · historique illimité · actions, ETF, crypto"},
    "stooq":   {"label": "Stooq",                "note": "Gratuit · bon pour actions EU/JP/US"},
    "binance": {"label": "Binance API",           "note": "Gratuit · crypto uniquement · très fiable"},
    "fred":    {"label": "FRED (Federal Reserve)","note": "Gratuit · données macro & indices économiques"},
}

def fetch_history(ticker, start_date, end_date, source="yahoo"):
    """Unified fetch returning a pandas Series of daily close prices."""

    start = pd.Timestamp(start_date)
    end   = pd.Timestamp(end_date)

    # ── Yahoo Finance ─────────────────────────────────────────────────────────
    if source == "yahoo":
        hist = yf.download(ticker, start=start_date, end=end_date,
                           auto_adjust=True, progress=False)
        if hist.empty:
            raise ValueError(f"Aucune donnée Yahoo Finance pour {ticker}")
        close = hist["Close"]
        # yfinance >=0.2.x may return DataFrame with MultiIndex columns
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        return close.dropna()

    # ── Stooq ─────────────────────────────────────────────────────────────────
    elif source == "stooq":
        # Stooq uses lowercase ticker, dots for some indices
        t = ticker.lower().replace("-", ".").replace("^", "")
        s = start.strftime("%Y%m%d")
        e = end.strftime("%Y%m%d")
        url = f"https://stooq.com/q/d/l/?s={t}&d1={s}&d2={e}&i=d"
        try:
            df = pd.read_csv(url, parse_dates=["Date"], index_col="Date")
            if df.empty or "Close" not in df.columns:
                raise ValueError("empty")
            return df["Close"].dropna().sort_index()
        except Exception:
            raise ValueError(f"Stooq : impossible de charger {ticker}. Vérifiez le ticker (ex: AAPL.US, CDR.PL)")

    # ── Binance (crypto only) — fallback to Yahoo if geo-blocked ────────────
    elif source == "binance":
        symbol = ticker.upper().replace("-USD", "USDT").replace("-USDT", "USDT").replace("/", "")
        if not symbol.endswith("USDT"):
            symbol = symbol + "USDT"
        s_ms = int(start.timestamp() * 1000)
        e_ms = int(end.timestamp() * 1000)
        # Try Binance.com first, then binance.us, then fallback Yahoo
        endpoints = [
            f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&startTime={s_ms}&endTime={e_ms}&limit=1000",
            f"https://api.binance.us/api/v3/klines?symbol={symbol}&interval=1d&startTime={s_ms}&endTime={e_ms}&limit=1000",
        ]
        for url in endpoints:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=8) as r:
                    data = json.loads(r.read())
                if data and isinstance(data, list):
                    dates  = [pd.Timestamp(d[0], unit="ms") for d in data]
                    closes = [float(d[4]) for d in data]
                    return pd.Series(closes, index=dates, name="Close").dropna()
            except Exception:
                continue
        # Geo-blocked or unavailable — fallback to Yahoo Finance for crypto
        hist = yf.download(ticker, start=start_date, end=end_date,
                           auto_adjust=True, progress=False)
        if hist.empty:
            raise ValueError(f"Binance indisponible dans votre région et Yahoo Finance n'a pas de données pour {ticker}.")
        close = hist["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        return close.dropna()

    # ── FRED ─────────────────────────────────────────────────────────────────
    elif source == "fred":
        # FRED series IDs: SP500, NASDAQCOM, DJIA, DGS10, CPIAUCSL, etc.
        series = ticker.upper()
        s = start.strftime("%Y-%m-%d")
        e = end.strftime("%Y-%m-%d")
        url = (f"https://fred.stlouisfed.org/graph/fredgraph.csv"
               f"?id={series}&vintage_date={e}")
        try:
            df = pd.read_csv(url, parse_dates=["DATE"], index_col="DATE",
                             na_values=[".", ""])
            df = df.dropna()
            if df.empty:
                raise ValueError("empty")
            col = df.columns[0]
            series_data = df[col].astype(float)
            series_data = series_data[(series_data.index >= start) & (series_data.index <= end)]
            if series_data.empty:
                raise ValueError("no data in range")
            return series_data.dropna()
        except Exception:
            raise ValueError(f"FRED : série '{series}' introuvable. Ex: SP500, NASDAQCOM, DJIA, DGS10, CPIAUCSL")

# ── Market index definitions ──────────────────────────────────────────────────
MARKETS = {
    "S&P 500": {
        "index": "^GSPC",
        "tickers": [
            ("AAPL",  "Apple Inc."),
            ("MSFT",  "Microsoft Corp."),
            ("NVDA",  "NVIDIA Corp."),
            ("AMZN",  "Amazon.com Inc."),
            ("GOOGL", "Alphabet Inc."),
            ("META",  "Meta Platforms"),
            ("TSLA",  "Tesla Inc."),
            ("AVGO",  "Broadcom Inc."),
            ("BRK-B", "Berkshire Hathaway"),
            ("JPM",   "JPMorgan Chase"),
            ("LLY",   "Eli Lilly"),
            ("V",     "Visa Inc."),
            ("UNH",   "UnitedHealth Group"),
            ("XOM",   "Exxon Mobil"),
            ("MA",    "Mastercard"),
            ("JNJ",   "Johnson & Johnson"),
            ("COST",  "Costco Wholesale"),
            ("HD",    "Home Depot"),
            ("NFLX",  "Netflix Inc."),
            ("AMD",   "Advanced Micro Devices"),
            ("WMT",   "Walmart Inc."),
            ("BAC",   "Bank of America"),
            ("PG",    "Procter & Gamble"),
            ("CRM",   "Salesforce Inc."),
            ("ORCL",  "Oracle Corp."),
            ("MRK",   "Merck & Co."),
            ("CVX",   "Chevron Corp."),
            ("ABBV",  "AbbVie Inc."),
            ("KO",    "Coca-Cola Co."),
            ("PEP",   "PepsiCo Inc."),
            ("TMO",   "Thermo Fisher"),
            ("ACN",   "Accenture plc"),
            ("CSCO",  "Cisco Systems"),
            ("LIN",   "Linde plc"),
            ("MCD",   "McDonald's Corp."),
            ("ABT",   "Abbott Laboratories"),
            ("DHR",   "Danaher Corp."),
            ("TXN",   "Texas Instruments"),
            ("NEE",   "NextEra Energy"),
            ("INTU",  "Intuit Inc."),
            ("PM",    "Philip Morris"),
            ("AMGN",  "Amgen Inc."),
            ("IBM",   "IBM Corp."),
            ("RTX",   "RTX Corp."),
            ("GE",    "GE Aerospace"),
            ("QCOM",  "Qualcomm Inc."),
            ("HON",   "Honeywell Intl."),
            ("SPGI",  "S&P Global"),
            ("CAT",   "Caterpillar Inc."),
            ("NOW",   "ServiceNow Inc."),
        ]
    },
    "CAC 40": {
        "index": "^FCHI",
        "tickers": [
            ("AI.PA",   "Air Liquide"),
            ("AIR.PA",  "Airbus SE"),
            ("ALO.PA",  "Alstom SA"),
            ("ATO.PA",  "Atos SE"),
            ("BN.PA",   "Danone SA"),
            ("BNP.PA",  "BNP Paribas"),
            ("CA.PA",   "Carrefour SA"),
            ("CAP.PA",  "Capgemini SE"),
            ("CS.PA",   "AXA SA"),
            ("DG.PA",   "Vinci SA"),
            ("DSY.PA",  "Dassault Systèmes"),
            ("ENGI.PA", "Engie SA"),
            ("EL.PA",   "EssilorLuxottica"),
            ("ERF.PA",  "Eurofins Scientific"),
            ("GLE.PA",  "Société Générale"),
            ("HO.PA",   "Thales SA"),
            ("KER.PA",  "Kering SA"),
            ("LHN.PA",  "Lafarge Holcim"),
            ("LR.PA",   "Legrand SA"),
            ("MC.PA",   "LVMH"),
            ("ML.PA",   "Michelin"),
            ("MT.PA",   "ArcelorMittal"),
            ("OR.PA",   "L'Oréal SA"),
            ("ORA.PA",  "Orange SA"),
            ("PUB.PA",  "Publicis Groupe"),
            ("RI.PA",   "Pernod Ricard"),
            ("RMS.PA",  "Hermès Intl."),
            ("SAF.PA",  "Safran SA"),
            ("SAN.PA",  "Sanofi SA"),
            ("SGO.PA",  "Saint-Gobain"),
            ("STLAM.PA","Stellantis NV"),
            ("STM.PA",  "STMicroelectronics"),
            ("SU.PA",   "Schneider Electric"),
            ("TEC.PA",  "Technip Energies"),
            ("TTE.PA",  "TotalEnergies SE"),
            ("URW.PA",  "Unibail-Rodamco"),
            ("VIE.PA",  "Veolia Environ."),
            ("VIV.PA",  "Vivendi SE"),
            ("WLN.PA",  "Worldline SA"),
        ]
    },
    "NASDAQ 100": {
        "index": "^NDX",
        "tickers": [
            ("AAPL",  "Apple Inc."),
            ("MSFT",  "Microsoft Corp."),
            ("NVDA",  "NVIDIA Corp."),
            ("AMZN",  "Amazon.com Inc."),
            ("META",  "Meta Platforms"),
            ("GOOGL", "Alphabet Class A"),
            ("GOOG",  "Alphabet Class C"),
            ("TSLA",  "Tesla Inc."),
            ("AVGO",  "Broadcom Inc."),
            ("COST",  "Costco Wholesale"),
            ("NFLX",  "Netflix Inc."),
            ("AMD",   "Advanced Micro Devices"),
            ("QCOM",  "Qualcomm Inc."),
            ("INTU",  "Intuit Inc."),
            ("AMAT",  "Applied Materials"),
            ("ISRG",  "Intuitive Surgical"),
            ("ADP",   "ADP Inc."),
            ("BKNG",  "Booking Holdings"),
            ("MU",    "Micron Technology"),
            ("LRCX",  "Lam Research"),
            ("PANW",  "Palo Alto Networks"),
            ("SNPS",  "Synopsys Inc."),
            ("CRWD",  "CrowdStrike"),
            ("KLAC",  "KLA Corp."),
            ("ADI",   "Analog Devices"),
            ("MDLZ",  "Mondelez Intl."),
            ("REGN",  "Regeneron Pharma"),
            ("PDD",   "PDD Holdings"),
            ("MELI",  "MercadoLibre"),
            ("ASML",  "ASML Holding"),
            ("ABNB",  "Airbnb Inc."),
            ("DXCM",  "DexCom Inc."),
            ("FTNT",  "Fortinet Inc."),
            ("MRVL",  "Marvell Technology"),
            ("GEHC",  "GE HealthCare"),
            ("CEG",   "Constellation Energy"),
            ("DASH",  "DoorDash Inc."),
            ("IDXX",  "IDEXX Laboratories"),
            ("TTD",   "The Trade Desk"),
            ("ZS",    "Zscaler Inc."),
        ]
    },
    "Crypto": {
        "index": "BTC-USD",
        "tickers": [
            ("BTC-USD",  "Bitcoin"),
            ("ETH-USD",  "Ethereum"),
            ("BNB-USD",  "Binance Coin"),
            ("SOL-USD",  "Solana"),
            ("XRP-USD",  "XRP"),
            ("ADA-USD",  "Cardano"),
            ("AVAX-USD", "Avalanche"),
            ("DOGE-USD", "Dogecoin"),
            ("DOT-USD",  "Polkadot"),
            ("MATIC-USD","Polygon"),
            ("SHIB-USD", "Shiba Inu"),
            ("LTC-USD",  "Litecoin"),
            ("LINK-USD", "Chainlink"),
            ("UNI-USD",  "Uniswap"),
            ("ATOM-USD", "Cosmos"),
            ("XLM-USD",  "Stellar"),
            ("NEAR-USD", "NEAR Protocol"),
            ("ARB-USD",  "Arbitrum"),
            ("OP-USD",   "Optimism"),
            ("INJ-USD",  "Injective"),
        ]
    },
    "ETF": {
        "index": "SPY",
        "tickers": [
            ("SPY",  "SPDR S&P 500 ETF"),
            ("QQQ",  "Invesco Nasdaq ETF"),
            ("VTI",  "Vanguard Total Mkt"),
            ("IWM",  "iShares Russell 2000"),
            ("DIA",  "SPDR Dow Jones ETF"),
            ("GLD",  "SPDR Gold Shares"),
            ("SLV",  "iShares Silver Trust"),
            ("TLT",  "iShares 20Y+ Bonds"),
            ("HYG",  "iShares High Yield"),
            ("XLF",  "Financial Select SPDR"),
            ("XLK",  "Technology Select SPDR"),
            ("XLE",  "Energy Select SPDR"),
            ("ARKK", "ARK Innovation ETF"),
            ("ARKG", "ARK Genomic ETF"),
            ("SQQQ", "ProShares UltraPro Short QQQ"),
            ("TQQQ", "ProShares UltraPro QQQ"),
            ("UVXY", "ProShares Ultra VIX"),
            ("VXUS", "Vanguard Intl. Stock"),
            ("VO",   "Vanguard Mid-Cap ETF"),
            ("SCHD", "Schwab US Dividend ETF"),
            ("SOXX", "iShares Semis ETF"),
            ("WCLD", "WisdomTree Cloud ETF"),
            ("BOTZ", "Robo Global AI & Robotics"),
        ]
    },
}

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", markets=list(MARKETS.keys()))


@app.route("/api/sources")
def get_sources():
    return jsonify(DATA_SOURCES)


@app.route("/api/tickers/<market>")
def get_tickers(market):
    data = MARKETS.get(market)
    if not data:
        return jsonify({"error": "Unknown market"}), 404
    return jsonify(data["tickers"])


@app.route("/api/price/<ticker>")
def get_current_price(ticker):
    source = request.args.get("source", "yahoo")
    try:
        if source == "binance":
            symbol = ticker.upper().replace("-USD", "USDT").replace("-USDT", "USDT")
            if not symbol.endswith("USDT"):
                symbol += "USDT"
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as r:
                d = json.loads(r.read())
            price = float(d["price"])
            currency = "USDT"
        else:
            t = yf.Ticker(ticker)
            price = t.fast_info.last_price
            currency = getattr(t.fast_info, "currency", "USD")
        return jsonify({"ticker": ticker, "price": round(price, 4), "currency": currency})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/simulate", methods=["POST"])
def simulate():
    data         = request.json
    ticker       = data["ticker"]
    source       = data.get("source", "yahoo")
    buy_type     = data.get("buy_type", "date")
    sell_type    = data.get("sell_type", "date")
    amount       = float(data.get("amount", 1000))
    leverage     = float(data.get("leverage", 1))
    product_type = data.get("product_type", "stock")

    today      = datetime.today()
    # Start fetch from 30 days before buy date (or 5y ago max) to today+1
    if buy_type == "date" and data.get("buy_date"):
        fetch_start = (pd.Timestamp(data["buy_date"]) - timedelta(days=30)).strftime("%Y-%m-%d")
    else:
        fetch_start = (today - timedelta(days=5 * 365)).strftime("%Y-%m-%d")
    fetch_end = (today + timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        prices = fetch_history(ticker, fetch_start, fetch_end, source=source)
        if prices.empty:
            return jsonify({"error": f"Aucune donnée pour {ticker} via {source}. Vérifiez le ticker et la source."}), 400
        prices.index = pd.to_datetime(prices.index)
        prices = prices.sort_index().dropna()
        if len(prices) < 2:
            return jsonify({"error": f"Données insuffisantes pour {ticker} sur la période demandée."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # find buy
    buy_price = None
    buy_date_actual = None
    buy_note = ""

    if buy_type == "date":
        target = pd.Timestamp(data["buy_date"])
        future = prices[prices.index >= target]
        if future.empty:
            return jsonify({"error": f"La date d'achat ({data['buy_date']}) est dans le futur ou au-delà des données disponibles. Le simulateur ne peut tester que des dates passées."}), 400
        buy_date_actual = future.index[0]
        buy_price = float(future.iloc[0])
        buy_note = f"Achete le {buy_date_actual.date()} a {buy_price:.4f}."
    else:
        op  = data.get("buy_condition_op", "<")
        val = float(data.get("buy_condition_value", 0))
        matches = prices[prices < val] if op == "<" else prices[prices > val]
        if matches.empty:
            return jsonify({
                "status": "not_triggered",
                "note": f"Condition d'achat ({ticker} {op} {val}) jamais atteinte dans l'historique disponible.",
                "buy_triggered": False,
            })
        buy_date_actual = matches.index[0]
        buy_price = float(matches.iloc[0])
        buy_note = f"Condition atteinte le {buy_date_actual.date()}: prix = {buy_price:.4f}."

    # find sell
    after_buy = prices[prices.index > buy_date_actual]
    sell_price = None
    sell_date_actual = None
    sell_note = ""
    still_open = False

    if sell_type == "date":
        target = pd.Timestamp(data["sell_date"])
        available = after_buy[after_buy.index <= target]
        if available.empty:
            sell_price = buy_price
            sell_date_actual = buy_date_actual
            sell_note = "Date de vente avant ou egale a l'achat — position fermee le meme jour."
        else:
            idx = available.index.get_indexer([target], method="nearest")[0]
            closest = available.index[idx]
            sell_price = float(prices.loc[closest])
            sell_date_actual = closest
            sell_note = f"Vendu le {sell_date_actual.date()} a {sell_price:.4f}."
    else:
        op  = data.get("sell_condition_op", ">")
        val = float(data.get("sell_condition_value", 0))
        cond = after_buy[after_buy < val] if op == "<" else after_buy[after_buy > val]
        if cond.empty:
            sell_price = float(prices.iloc[-1])
            sell_date_actual = prices.index[-1]
            still_open = True
            sell_note = f"Condition de vente ({ticker} {op} {val}) pas encore atteinte. Prix actuel: {sell_price:.4f} au {sell_date_actual.date()}."
        else:
            sell_date_actual = cond.index[0]
            sell_price = float(cond.iloc[0])
            sell_note = f"Condition atteinte le {sell_date_actual.date()}: prix = {sell_price:.4f}."

    # P&L
    shares = (amount / buy_price) * leverage
    raw_return_pct = (sell_price - buy_price) / buy_price
    leveraged_pct  = raw_return_pct * leverage
    pnl_eur        = amount * leveraged_pct

    if product_type == "option_put":
        pnl_eur = -pnl_eur
        leveraged_pct = -leveraged_pct

    final_value = amount + pnl_eur

    # sparkline
    window = prices[(prices.index >= buy_date_actual) & (prices.index <= sell_date_actual)]
    step   = max(1, len(window) // 60)
    spark  = window.iloc[::step]
    sparkline = [{"date": str(d.date()), "price": round(float(p), 4)}
                 for d, p in zip(spark.index, spark.values)]

    return jsonify({
        "status": "ok",
        "buy_triggered": True,
        "still_open": still_open,
        "ticker": ticker,
        "source": source,
        "buy_price": round(buy_price, 4),
        "buy_date": str(buy_date_actual.date()),
        "sell_price": round(sell_price, 4),
        "sell_date": str(sell_date_actual.date()),
        "amount_invested": round(amount, 2),
        "leverage": leverage,
        "product_type": product_type,
        "shares": round(shares, 6),
        "pnl_eur": round(pnl_eur, 2),
        "pnl_pct": round(leveraged_pct * 100, 2),
        "raw_pct": round(raw_return_pct * 100, 2),
        "final_value": round(final_value, 2),
        "buy_note": buy_note,
        "sell_note": sell_note,
        "sparkline": sparkline,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
