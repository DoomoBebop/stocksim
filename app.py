from flask import Flask, render_template, jsonify, request
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json

app = Flask(__name__)

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


@app.route("/api/tickers/<market>")
def get_tickers(market):
    data = MARKETS.get(market)
    if not data:
        return jsonify({"error": "Unknown market"}), 404
    return jsonify(data["tickers"])


@app.route("/api/price/<ticker>")
def get_current_price(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        price = info.last_price
        currency = getattr(info, "currency", "USD")
        return jsonify({"ticker": ticker, "price": round(price, 4), "currency": currency})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/simulate", methods=["POST"])
def simulate():
    """
    Simulate one position:
    {
      ticker, market,
      buy_type: 'date' | 'condition',
      buy_date: 'YYYY-MM-DD',          # if buy_type == 'date'
      buy_condition_op: '<' | '>',      # if buy_type == 'condition'
      buy_condition_value: float,
      sell_type: 'date' | 'condition',
      sell_date: 'YYYY-MM-DD',
      sell_condition_op: '<' | '>',
      sell_condition_value: float,
      amount: float,                    # euros/USD invested
      leverage: float,                  # 1 = no leverage
      product_type: 'stock' | 'etf' | 'cfd' | 'option_call' | 'option_put',
    }
    """
    data = request.json
    ticker      = data["ticker"]
    buy_type    = data.get("buy_type", "date")
    sell_type   = data.get("sell_type", "date")
    amount      = float(data.get("amount", 1000))
    leverage    = float(data.get("leverage", 1))
    product_type = data.get("product_type", "stock")

    # Date range — fetch enough history
    end_date   = datetime.today()
    start_date = end_date - timedelta(days=5 * 365)

    try:
        hist = yf.download(ticker, start=start_date.strftime("%Y-%m-%d"),
                           end=end_date.strftime("%Y-%m-%d"), auto_adjust=True, progress=False)
        if hist.empty:
            return jsonify({"error": f"No data found for {ticker}"}), 400

        hist = hist[["Close"]].copy()
        hist.index = pd.to_datetime(hist.index)
        prices = hist["Close"].dropna()

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # ── Find buy event ────────────────────────────────────────────────────────
    buy_price = None
    buy_date_actual = None
    buy_note = ""

    if buy_type == "date":
        target = pd.Timestamp(data["buy_date"])
        # Find nearest trading day at or after target
        future = prices[prices.index >= target]
        if future.empty:
            return jsonify({"error": "Buy date is beyond available data or in the future"}), 400
        buy_date_actual = future.index[0]
        buy_price = float(future.iloc[0])
        buy_note = f"Bought on {buy_date_actual.date()} at market open."
    else:
        op  = data.get("buy_condition_op", "<")
        val = float(data.get("buy_condition_value", 0))
        matches = prices[prices < val] if op == "<" else prices[prices > val]
        if matches.empty:
            return jsonify({
                "status": "not_triggered",
                "note": f"Buy condition ({ticker} {op} {val}) was NEVER met in the available history.",
                "buy_triggered": False,
            })
        buy_date_actual = matches.index[0]
        buy_price = float(matches.iloc[0])
        buy_note = f"Condition met on {buy_date_actual.date()}: price was {buy_price:.2f}."

    # ── Find sell event ───────────────────────────────────────────────────────
    after_buy = prices[prices.index > buy_date_actual]
    sell_price = None
    sell_date_actual = None
    sell_note = ""
    still_open = False

    if sell_type == "date":
        target = pd.Timestamp(data["sell_date"])
        available = after_buy[after_buy.index <= target]
        if available.empty:
            # Sell date is before any data after buy — use buy price
            sell_price = buy_price
            sell_date_actual = buy_date_actual
            sell_note = "Sell date is before or at buy date — position closed same day."
        else:
            closest = available.index[available.index.get_indexer([target], method="nearest")[0]]
            sell_price = float(prices.loc[closest])
            sell_date_actual = closest
            sell_note = f"Sold on {sell_date_actual.date()} at {sell_price:.2f}."
    else:
        op  = data.get("sell_condition_op", ">")
        val = float(data.get("sell_condition_value", 0))
        cond = after_buy[after_buy < val] if op == "<" else after_buy[after_buy > val]
        if cond.empty:
            # Condition not yet met — position still open
            sell_price = float(prices.iloc[-1])
            sell_date_actual = prices.index[-1]
            still_open = True
            sell_note = f"Sell condition ({ticker} {op} {val}) NOT YET triggered. Current price: {sell_price:.2f} as of {sell_date_actual.date()}."
        else:
            sell_date_actual = cond.index[0]
            sell_price = float(cond.iloc[0])
            sell_note = f"Sell condition met on {sell_date_actual.date()}: price was {sell_price:.2f}."

    # ── P&L calculation ───────────────────────────────────────────────────────
    shares = (amount / buy_price) * leverage
    raw_return_pct = (sell_price - buy_price) / buy_price  # pre-leverage for display
    leveraged_pct  = raw_return_pct * leverage
    pnl_eur        = amount * leveraged_pct

    # For inverse products (short ETF, put option)
    if product_type in ("option_put",):
        pnl_eur    = -pnl_eur
        leveraged_pct = -leveraged_pct

    final_value = amount + pnl_eur

    # ── Build sparkline data (weekly sampled) ─────────────────────────────────
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
