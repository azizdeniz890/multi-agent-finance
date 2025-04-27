#!/usr/bin/env python3
# buffett_finance_agent.py

import os
import re
import sys
import time
import logging
import feedparser
import yfinance as yf
from dotenv import load_dotenv
from iointel import Agent, Workflow
from urllib.parse import urlparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Setup logging to stdout
logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format="%(asctime)s %(levelname)s: %(message)s")

console = Console()

# Load API key
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY ortam değişkeni bulunamadı.", file=sys.stderr)
    sys.exit(1)

# ----------------------------------------
# Buffett Agent
# ----------------------------------------
SYSTEM_PROMPT = """
You are a Warren Buffett AI agent. Decide on investment signals based on Warren Buffett's principles:
- Circle of Competence: Only invest in businesses you understand
- Margin of Safety (> 30%): Buy at a significant discount to intrinsic value
- Economic Moat: Look for durable competitive advantages
- Quality Management: Seek conservative, shareholder-oriented teams
- Financial Strength: Favor low debt, strong returns on equity
- Long-term Horizon: Invest in businesses, not just stocks
- Sell only if fundamentals deteriorate or valuation far exceeds intrinsic value

When providing your reasoning, be thorough and specific by:
1. Explaining the key factors that influenced your decision the most (both positive and negative)
2. Highlighting how the company aligns with or violates specific Buffett principles
3. Providing quantitative evidence where relevant (e.g., specific margins, ROE values, debt levels)
4. Concluding with a Buffett-style assessment of the investment opportunity
5. Using Warren Buffett's voice and conversational style in your explanation

Follow these guidelines strictly. Output as plain text suitable for terminal display.
""".strip()
buffett_agent = Agent(
    name="Buffett Agent",
    instructions=SYSTEM_PROMPT,
    model="meta-llama/Llama-3.3-70B-Instruct",
    api_key=OPENAI_API_KEY,
    base_url="https://api.intelligence.io.solutions/api/v1"
)

# ----------------------------------------
# Graham Agent
# ----------------------------------------
GRAHAM_SYSTEM_PROMPT = """
You are a Benjamin Graham AI agent, making investment decisions using his principles:
1. Insist on a margin of safety by buying below intrinsic value (e.g., using Graham Number, net-net).
2. Emphasize the company's financial strength (low leverage, ample current assets).
3. Prefer stable earnings over multiple years.
4. Consider dividend record for extra safety.
5. Avoid speculative or high-growth assumptions; focus on proven metrics.

When providing your reasoning, be thorough and specific by:
1. Explaining the key valuation metrics that influenced your decision the most (Graham Number, NCAV, P/E, etc.)
2. Highlighting the specific financial strength indicators (current ratio, debt levels, etc.)
3. Referencing the stability or instability of earnings over time
4. Providing quantitative evidence with precise numbers
5. Comparing current metrics to Graham's specific thresholds (e.g., "Current ratio of 2.5 exceeds Graham's minimum of 2.0")
6. Using Benjamin Graham's conservative, analytical voice and style in your explanation

Follow these guidelines strictly. Output as plain text suitable for terminal display.
""".strip()
graham_agent = Agent(
    name="Graham Agent",
    instructions=GRAHAM_SYSTEM_PROMPT,
    model="meta-llama/Llama-3.3-70B-Instruct",
    api_key=OPENAI_API_KEY,
    base_url="https://api.intelligence.io.solutions/api/v1"
)

# ----------------------------------------
# Lynch Agent
# ----------------------------------------
LYNCH_SYSTEM_PROMPT = """
You are a Peter Lynch AI agent. You make investment decisions based on Peter Lynch's well-known principles:
1. Invest in What You Know: Emphasize understandable businesses, possibly discovered in everyday life.
2. Growth at a Reasonable Price (GARP): Rely on the PEG ratio as a prime metric.
3. Look for 'Ten-Baggers': Companies capable of growing earnings and share price substantially.
4. Steady Growth: Prefer consistent revenue/earnings expansion, less concern about short-term noise.
5. Avoid High Debt: Watch for dangerous leverage.
6. Management & Story: A good 'story' behind the stock, but not overhyped or too complex.

When you provide your reasoning, do it in Peter Lynch's voice:
- Cite the PEG ratio
- Mention 'ten-bagger' potential if applicable
- Refer to personal or anecdotal observations (e.g., "If my kids love the product...")
- Use practical, folksy language
- Provide key positives and negatives
- Conclude with a clear stance: bullish, bearish, or neutral

Follow these guidelines strictly. Output as plain text suitable for terminal display.
""".strip()
lynch_agent = Agent(
    name="Lynch Agent",
    instructions=LYNCH_SYSTEM_PROMPT,
    model="meta-llama/Llama-3.3-70B-Instruct",
    api_key=OPENAI_API_KEY,
    base_url="https://api.intelligence.io.solutions/api/v1"
)

TRUSTED_SOURCES = [
    "Forbes", "Bloomberg", "Reuters", "CNBC",
    "Financial Times", "Business Insider", "Wall Street Journal",
    "The Economist", "MarketWatch"
]

# ----------------------------------------
# Technical Indicators: expanded
# ----------------------------------------
def fetch_price_data(ticker: str) -> dict:
    start = time.time()
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="250d", interval="1d").dropna()

        # Basic price & returns
        last_close = hist["Close"].iloc[-1]
        prev_close = hist["Close"].iloc[-2]
        daily_change = (last_close - prev_close) / prev_close * 100

        # RSI(14)
        delta = hist["Close"].diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        roll_up = up.ewm(span=14).mean()
        roll_down = down.ewm(span=14).mean()
        rsi_last = (100 - (100 / (1 + roll_up/roll_down))).iloc[-1]

        # MACD(12,26)
        ema12 = hist["Close"].ewm(span=12).mean()
        ema26 = hist["Close"].ewm(span=26).mean()
        macd_last = (ema12 - ema26).iloc[-1]

        # Moving Averages
        sma50 = hist["Close"].rolling(window=50).mean().iloc[-1]
        sma200 = hist["Close"].rolling(window=200).mean().iloc[-1]

        # Volatility = stdev of daily returns over last 20 days
        returns = hist["Close"].pct_change().dropna()
        vol20 = returns.rolling(window=20).std().iloc[-1] * (252**0.5)  # annualized

        # Avg volume
        avg_vol30 = hist["Volume"].rolling(window=30).mean().iloc[-1]

        duration = time.time() - start
        logging.info(f"fetch_price_data({ticker}) took {duration:.2f}s")

        return {
            "Last Close": round(last_close, 2),
            "Daily Change %": round(daily_change, 2),
            "RSI (14)": round(rsi_last, 2),
            "MACD (12,26)": round(macd_last, 4),
            "SMA (50)": round(sma50, 2),
            "SMA (200)": round(sma200, 2),
            "Volatility (20d)": f"{vol20:.2%}",
            "Avg Volume (30d)": int(avg_vol30),
        }

    except Exception as e:
        logging.error(f"fetch_price_data error for {ticker}: {e}")
        return {}

# ----------------------------------------
# Fundamental + Technical Data: expanded
# ----------------------------------------
def fetch_financial_data(ticker: str) -> dict:
    start = time.time()
    try:
        info = yf.Ticker(ticker).info or {}
    except Exception as e:
        logging.error(f"fetch_financial_data error for {ticker}: {e}")
        return {}

    fundamentals = {
        # Valuation
        "Market Cap": info.get("marketCap"),
        "Enterprise Value": info.get("enterpriseValue"),
        "Trailing P/E": info.get("trailingPE"),
        "Forward P/E": info.get("forwardPE"),
        "PEG Ratio": info.get("pegRatio"),
        "Price/Book": info.get("priceToBook"),

        # Profitability
        "Total Revenue": info.get("totalRevenue"),
        "Gross Profit": info.get("grossProfit"),
        "Gross Margin": info.get("grossMargins"),
        "Operating Income": info.get("operatingIncome"),
        "Operating Margin": info.get("operatingMargins"),
        "Net Income": info.get("netIncome"),
        "Net Margin": info.get("netMargins"),

        # Liquidity & Debt
        "Current Ratio": info.get("currentRatio"),
        "Quick Ratio": info.get("quickRatio"),
        "Total Debt": info.get("totalDebt"),
        "Debt/Equity": info.get("debtToEquity"),
        "Cash & Equivalents": info.get("totalCash"),

        # Returns
        "Return on Assets": info.get("returnOnAssets"),
        "Return on Equity": info.get("returnOnEquity"),
        "Return on Investment": info.get("returnOnInvestment"),

        # Shares & Dividends
        "Shares Outstanding": info.get("sharesOutstanding"),
        "Dividend Yield": info.get("dividendYield"),
    }

    # Append the expanded technicals
    fundamentals.update(fetch_price_data(ticker))

    duration = time.time() - start
    logging.info(f"fetch_financial_data({ticker}) took {duration:.2f}s")

    return fundamentals


# ----------------------------------------
# News Fetching
# ----------------------------------------
def fetch_news(ticker: str, max_articles: int = 5) -> list:
    start = time.time()
    clean = re.sub(r"[^\w\s]", "", ticker).replace(" ", "+")
    feed = feedparser.parse(
        f"https://news.google.com/rss/search?q={clean}&hl=en-US&gl=US&ceid=US:en"
    )
    news = []
    for entry in feed.entries:
        src = entry.get("source", {}).get("title", "")
        if any(s.lower() in src.lower() for s in TRUSTED_SOURCES):
            news.append({
                "title": entry.title,
                "summary": entry.summary,
                "link": entry.link,
                "source": src
            })
        if len(news) >= max_articles:
            break
    logging.info(f"fetch_news({ticker}) took {time.time()-start:.2f}s")
    return news

# ----------------------------------------
# Display Output
# ----------------------------------------
def display_output(ticker, financials, news_items, buff_text, graham_text, lynch_text):
    # Financials table
    fin = Table(title=f"[bold cyan]Metrics for {ticker}[/]")
    fin.add_column("Metric", style="cyan")
    fin.add_column("Value", style="magenta")
    for k, v in financials.items():
        fin.add_row(k, str(v))
    console.print(fin)

    # News table
    nt = Table(title="[bold green]Top News[/]")
    nt.add_column("#", style="cyan", width=4)
    nt.add_column("Source", style="green")
    nt.add_column("Title", style="white")
    for i, it in enumerate(news_items, 1):
        nt.add_row(str(i), it["source"], it["title"])
    console.print(nt)

    # Buffett panel
    style_b = "green" if "bullish" in buff_text.lower() else ("red" if "bearish" in buff_text.lower() else "yellow")
    console.print(Panel.fit(buff_text, title="[bold]Buffett Analysis[/]", border_style=style_b))

    # Graham panel
    style_g = "green" if "bullish" in graham_text.lower() else ("red" if "bearish" in graham_text.lower() else "yellow")
    console.print(Panel.fit(graham_text, title="[bold]Graham Analysis[/]", border_style=style_g))

    # Lynch panel
    style_l = "green" if "bullish" in lynch_text.lower() else ("red" if "bearish" in lynch_text.lower() else "yellow")
    console.print(Panel.fit(lynch_text, title="[bold]Lynch Analysis[/]", border_style=style_l))

# ----------------------------------------
# Buffett Analysis
# ----------------------------------------
def analyze_with_buffett(ticker: str, financials, news_items) -> str:
    # fetch_financial_data(ticker) --> GEREK YOK ARTIK
    # fetch_news(ticker) --> GEREK YOK ARTIK

    # prompt hazırlığı
    prompt = "Financials:\n" + "\n".join(f"{k}: {v}" for k, v in financials.items())
    prompt += "\n\nNews:\n" + "\n".join(f"{it['title']}. {it['summary']}" for it in news_items)
    
    HUMAN_PROMPT = f"""
{prompt}

Provide:
- A concise Buffett-style comment
- Sentiment: bullish or bearish
- Recommendation: Buy, Sell, or Hold
""".strip()
    start = time.time()
    res = Workflow(text=prompt, client_mode=False).custom(
        name="buffett-full-analysis",
        objective="investment analysis",
        instructions=HUMAN_PROMPT,
        agents=[buffett_agent]
    ).run_tasks()
    logging.info(f"Buffett AI took {time.time()-start:.2f}s")
    return next(iter(res["results"].values()))

# ----------------------------------------
# Graham Analysis
# ----------------------------------------
def analyze_with_graham(ticker: str) -> str:
    logging.info(f"Starting Graham analysis for {ticker}")
    fin = fetch_financial_data(ticker)
    news = fetch_news(ticker)
    prompt = "Financials:\n" + "\n".join(f"{k}: {v}" for k, v in fin.items())
    prompt += "\n\nNews:\n" + "\n".join(f"{it['title']}. {it['summary']}" for it in news)
    start = time.time()
    res = Workflow(text=prompt, client_mode=False).custom(
        name="graham-full-analysis",
        objective="investment analysis",
        instructions=prompt,  # Graham system prompt is already in agent
        agents=[graham_agent]
    ).run_tasks()
    logging.info(f"Graham AI took {time.time()-start:.2f}s")
    return next(iter(res["results"].values()))

# ----------------------------------------
# Lynch Analysis
# ----------------------------------------
def analyze_with_lynch(ticker: str) -> str:
    logging.info(f"Starting Lynch analysis for {ticker}")
    fin = fetch_financial_data(ticker)
    news = fetch_news(ticker)
    prompt = "Financials:\n" + "\n".join(f"{k}: {v}" for k, v in fin.items())
    prompt += "\n\nNews:\n" + "\n".join(f"{it['title']}. {it['summary']}" for it in news)
    HUMAN_PROMPT = f"""
{prompt}

Provide a Peter Lynch–style comment:
- Cite PEG ratio
- Mention ten-bagger potential if any
- Use anecdotal, practical language
- Key positives and negatives
- Conclude with stance: bullish, bearish, or neutral
""".strip()
    start = time.time()
    res = Workflow(text=prompt, client_mode=False).custom(
        name="lynch-full-analysis",
        objective="investment analysis",
        instructions=HUMAN_PROMPT,
        agents=[lynch_agent]
    ).run_tasks()
    logging.info(f"Lynch AI took {time.time()-start:.2f}s")
    return next(iter(res["results"].values()))

# ----------------------------------------
# Main
# ----------------------------------------
def main():
    print("Buffett, Graham & Lynch Finance Agent")
    print("Enter a stock ticker (e.g. TSLA, AAPL), or 'q' to quit.")
    while True:
        ticker = input("Ticker: ").strip().upper()
        if ticker == 'Q':
            break
        fin = fetch_financial_data(ticker)
        news = fetch_news(ticker)
        b = analyze_with_buffett(ticker)
        g = analyze_with_graham(ticker)
        l = analyze_with_lynch(ticker)
        display_output(ticker, fin, news, b, g, l)

if __name__ == "__main__":
    main()
