# 💳 Finance Agent — Personal AI Finance OS

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-6c63ff?style=for-the-badge)](https://finance-agent-hswzkck9cgkpqq9uknvw5u.streamlit.app)
[![GitHub](https://img.shields.io/badge/GitHub-krishareddy20-black?style=for-the-badge&logo=github)](https://github.com/krishareddy20/finance-agent)



# 💳 Finance Agent — Personal Life OS

An intelligent personal finance agent that reads your Gmail, detects financial events,
makes smart decisions using a **free LLM via OpenRouter** (no paid API needed),
schedules reminders in Google Calendar, tracks spending in SQLite, and learns from your behaviour.

---

## 🏗 Project Structure

```
finance-agent/
├── main.py                    # Entry point & orchestrator
├── config.py                  # Thresholds, categories, model choice
├── requirements.txt
├── .env                       # Your secrets (copy from .env.example)
│
├── agents/
│   ├── email_agent.py         # Gmail reader & financial event extractor
│   ├── decision_agent.py      # pay / remind / ignore engine
│   ├── action_agent.py        # Calendar, email sender, approval flow
│   ├── memory_agent.py        # Learns from your decisions over time
│   ├── sms_agent.py           # Parses bank SMS alerts
│   └── insight_agent.py       # Reports & spending analysis
│
├── tools/
│   ├── llm_tool.py            # ← OpenRouter free LLM (replaces Anthropic SDK)
│   ├── gmail_tool.py          # Gmail API wrapper
│   ├── calendar_tool.py       # Google Calendar API wrapper
│   ├── budget_tool.py         # Budget calculations
│   ├── storage_tool.py        # SQLite transaction DB
│   └── sms_tool.py            # ADB-based SMS reader
│
├── models/
│   ├── transaction.py         # Transaction dataclass
│   ├── budget.py              # Budget dataclass
│   └── memory.py              # Memory dataclass
│
└── dashboard/
    └── app.py                 # Streamlit web UI
```

---

## ⚡ Quick Setup (Step by Step)

### Step 1 — Clone & install dependencies

```bash
git clone <your-repo>
cd finance-agent
pip install -r requirements.txt
```

### Step 2 — Get a FREE OpenRouter API key

1. Go to [https://openrouter.ai](https://openrouter.ai) and sign up (free)
2. Go to **Keys** → **Create Key**
3. Copy your key (starts with `sk-or-v1-...`)
4. Free models available with no credits: `meta-llama/llama-3.1-8b-instruct:free`, `mistralai/mistral-7b-instruct:free`

### Step 3 — Create your `.env` file

```bash
cp .env.example .env
```

Edit `.env`:
```
OPENROUTER_API_KEY=sk-or-v1-your-key-here
USER_EMAIL=you@gmail.com
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json
DB_PATH=finance_agent.db
```

### Step 4 — Set up Gmail & Google Calendar API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g. "Finance Agent")
3. Enable these two APIs:
   - **Gmail API**
   - **Google Calendar API**
4. Go to **Credentials → Create Credentials → OAuth 2.0 Client ID**
5. Choose **Desktop App**, click Create, then **Download JSON**
6. Save the downloaded file as **`credentials.json`** in the project root
7. On first run a browser window opens — sign in with your Gmail account
8. A `token.json` is saved automatically for future runs (do not share this file)

### Step 5 — Configure your monthly budget

Edit `config.py` → `DEFAULT_BUDGET` (amounts in ₹):

```python
DEFAULT_BUDGET = {
    "education":      5000,
    "subscriptions":  1000,
    "food":           8000,
    # add/edit as needed
}
```

---

## 🚀 Running the Agent

### Scan emails and process transactions
```bash
python main.py
```

### Email scan only
```bash
python main.py --email-only
```

### Test SMS parsing (no phone needed)
```bash
python main.py --sms-test
```

### Show spending dashboard in terminal
```bash
python main.py --dashboard
```

### Generate a monthly report
```bash
python main.py --report
```

### Generate a weekly report
```bash
python main.py --report weekly
```

### Show bank balance from SMS
```bash
python main.py --balance
```

### Run the learning pass manually
```bash
python main.py --learn
```

### Run on a daily schedule (8am every day)
```bash
python main.py --schedule
```

### Launch the Streamlit web dashboard
```bash
streamlit run dashboard/app.py
```
Then open [http://localhost:8501](http://localhost:8501)

---

## 🆓 Free LLM — How It Works

The file `tools/llm_tool.py` replaces the Anthropic SDK entirely.
It calls OpenRouter's OpenAI-compatible endpoint with free models:

```
Priority order:
1. meta-llama/llama-3.1-8b-instruct:free
2. mistralai/mistral-7b-instruct:free
3. google/gemma-2-9b-it:free
```

If one model is down or rate-limited, it automatically tries the next one.
No credits needed — just a free OpenRouter account.

---

## 🔒 Security Notes

- `token.json` and `credentials.json` contain your OAuth secrets — **never commit them to Git**
- Add both to `.gitignore`:
  ```
  token.json
  credentials.json
  .env
  finance_agent.db
  ```
- All data is stored locally in SQLite — nothing leaves your machine except Gmail/Calendar API calls and OpenRouter LLM calls

---

## 💡 How Each Agent Works

| Agent | What it does |
|---|---|
| **EmailAgent** | Fetches unread Gmail, filters for financial keywords, sends to LLM to extract amount/category/deadline |
| **DecisionAgent** | Checks budget utilisation + user memory, asks LLM for pay/remind/ignore recommendation |
| **ActionAgent** | Handles terminal approval prompt, creates Google Calendar reminders, updates SQLite status |
| **MemoryAgent** | Tracks approval counts, promotes merchants to "trusted" after 3 approvals, learns patterns via LLM |
| **InsightAgent** | Generates terminal dashboard, monthly/weekly AI reports, savings tips |
| **SMSAgent** | Parses bank SMS (regex-based, no LLM needed) to auto-record already-completed transactions |

---

## 📺 Streamlit Dashboard Pages

| Page | What it shows |
|---|---|
| Dashboard | Bar chart of budget vs spend, pie chart of spending distribution |
| Transactions | Filterable table of all recorded transactions |
| Budget | Edit monthly limits per category |
| Reports | Generate AI-written monthly/weekly reports and savings tips |
| Memory | Trusted/ignored merchants, category priorities, trigger learning pass |

---

## 🔧 Extending the Agent

### Add a new spending category
1. Add it to `DEFAULT_BUDGET` in `config.py`
2. Add detection keywords to `CATEGORIES` in `config.py`

### Change the free LLM model
Edit `OPENROUTER_MODEL` in `config.py`. Browse free models at [openrouter.ai/models?q=free](https://openrouter.ai/models?q=free).

### Add Telegram notifications
Replace `request_approval()` in `agents/action_agent.py` with a Telegram Bot API call.

### Add WhatsApp/UPI notifications
Use the Twilio API in `agents/action_agent.py`.
