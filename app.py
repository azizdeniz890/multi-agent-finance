import streamlit as st
import os
from y4 import (
    fetch_price_data,
    fetch_financial_data,
    fetch_news,
    analyze_with_buffett,
    analyze_with_graham,
    analyze_with_lynch
)

# Page config
st.set_page_config(page_title="Multi-Agent Stock Analysis", layout="wide")
st.header("Multi-Agent Stock Analysis")

# Sidebar
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY"))
symbol  = st.sidebar.text_input("Stock Symbol",  value="TSLA").upper()
run     = st.sidebar.button("Analyze")

if api_key:
    os.environ["OPENAI_API_KEY"] = api_key

if run:
    with st.spinner(f"Analyzing {symbol}…"):
        financials   = fetch_financial_data(symbol)
        news_items   = fetch_news(symbol)
        buff_text    = analyze_with_buffett(symbol, financials, news_items)
        graham_text  = analyze_with_graham(symbol)
        lynch_text   = analyze_with_lynch(symbol)

    # Financial metrics
    st.subheader("📈 Financial Metrics")
    st.dataframe(financials)

    # Latest News: title + small "Go" link
    st.subheader("📰 Latest News")
    for idx, item in enumerate(news_items, start=1):
        col1, col2 = st.columns([8, 1])
        col1.write(f"{idx}. {item['title']}")
        col2.markdown(f"[Go]({item['link']})")

    # Verdict helper
    def show_verdict(txt):
        t = txt.lower()
        if "bullish" in t:
            st.success("Bullish")
        elif "bearish" in t:
            st.error("Bearish")
        else:
            st.warning("Neutral")

    # Analyst Opinions
    st.subheader("🤖 Analyst Opinions")

    st.markdown("**Warren Buffett**")
    st.write(buff_text)
    show_verdict(buff_text)

    st.markdown("**Benjamin Graham**")
    st.write(graham_text)
    show_verdict(graham_text)

    st.markdown("**Peter Lynch**")
    st.write(lynch_text)
    show_verdict(lynch_text)
