import os
from dotenv import load_dotenv

load_dotenv()

# -- API Keys ------------------------------------------------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GMAIL_CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
GMAIL_TOKEN_FILE       = os.getenv("GMAIL_TOKEN_FILE", "token.json")

# -- OpenRouter (FREE — no credits needed) ------------------------------------
# Free models: try these in order if one fails
OPENROUTER_MODEL    = "meta-llama/llama-3.1-8b-instruct:free"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# -- Database ------------------------------------------------------------------
DB_PATH = os.getenv("DB_PATH", "finance_agent.db")

# -- Budget Defaults (monthly, in Rupees) --------------------------------------
DEFAULT_BUDGET = {
    "education":      5000,
    "subscriptions":  1000,
    "entertainment":  2000,
    "food":           8000,
    "utilities":      3000,
    "health":         2000,
    "travel":         5000,
    "shopping":       3000,
    "other":          2000,
}

# -- Decision Thresholds -------------------------------------------------------
AUTO_APPROVE_BELOW        = 200   # auto-approve payments under this amount (₹)
REQUIRE_APPROVAL_ABOVE    = 200   # ask user before paying above this
CRITICAL_PAYMENT_THRESHOLD = 0.8  # warn if payment > 80% of remaining budget

# -- Email Detection Keywords --------------------------------------------------
FINANCIAL_KEYWORDS = [
    "invoice", "payment", "due", "subscription", "renewal", "receipt",
    "bill", "charge", "fee", "registration", "enroll", "course", "purchase",
    "transaction", "amount", "pay now", "overdue", "reminder"
]

CATEGORIES = {
    "education":     ["course", "class", "workshop", "udemy", "coursera", "edx", "training", "certification"],
    "subscriptions": ["netflix", "spotify", "youtube premium", "adobe", "github", "notion", "subscription"],
    "utilities":     ["electricity", "water", "internet", "broadband", "phone bill", "gas"],
    "health":        ["gym", "health", "medical", "doctor", "pharmacy", "insurance"],
    "food":          ["swiggy", "zomato", "grocery", "restaurant", "food"],
    "travel":        ["flight", "hotel", "booking", "airbnb", "uber", "ola", "train"],
    "entertainment": ["movie", "concert", "game", "steam", "play store"],
    "shopping":      ["amazon", "flipkart", "myntra", "order", "purchase"],
}

# -- Report Schedule -----------------------------------------------------------
WEEKLY_REPORT_DAY  = "sunday"
MONTHLY_REPORT_DAY = 1
