# 📈 Multi-Agent Finance Dashboard

A powerful AI-driven dashboard that analyzes stock financials and news using legendary investment strategies.

- 🧠 Powered by [IO.NET](https://io.net/) API for running large LLMs like **meta-llama-3-70B**.
- 🤖 Multiple agents: **Warren Buffett**, **Benjamin Graham**, **Peter Lynch**.
- 📊 Combines real-time financial data, technical indicators, and top news sentiment.

---

## 🚀 Features

- Fetch real-time stock financials (P/E, PEG, ROE, D/E, RSI, MACD, SMA, Volatility).
- Analyze top news headlines from trusted sources (Forbes, Bloomberg, CNBC, etc.).
- Three AI agents provide distinct investment analyses based on their philosophies.
- Sentiment detection: Bullish / Bearish / Neutral.
- Fully interactive dashboard powered by Streamlit.

---

## ⚡ How to Run Locally

1. Clone the repo:

```bash
git clone https://github.com/azizdeniz890/multi-agent-finance.git
cd multi-agent-finance
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Launch the Streamlit app:

```bash
streamlit run app.py
```

---

## 🔑 Important Note

This project **requires an IO.NET API KEY** to function.  
You must set your API Key either via:

- `.env` file (`OPENAI_API_KEY=your_key_here`)  
or  
- Streamlit sidebar input.

**Keys can be obtained from:** [https://io.net](https://io.net)

---

## 📄 License

This project is licensed under the MIT License.

---

## 📚 Acknowledgements

- This project was inspired by [Virattt's AI Hedge Fund](https://github.com/virattt/ai-hedge-fund).
- Special thanks to [IO.NET](https://io.net/) for providing GPU compute resources.
- Based on the timeless investing wisdom of Warren Buffett, Benjamin Graham, and Peter Lynch.
---

## 💬 Example Output

Each agent returns:

- 📋 Their reasoning and insights
- 📈 A final sentiment (Bullish / Bearish / Neutral)
- ✅ Recommendation (Buy, Hold, Sell)

---

## 🛡️ Disclaimer

This project is **for educational purposes only**.  
It **does not constitute financial advice**. Always perform your own due diligence before making any investment decisions.

---

## 📫 Contact

If you like this project or have any feedback, feel free to reach out!

- GitHub: [azizdeniz890](https://github.com/azizdeniz890)
- Email: azizdeniz098@gmail.com

---

# 🌟 Happy Investing with AI! 🌟
