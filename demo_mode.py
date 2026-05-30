"""
demo_mode.py — Seeds the database with realistic sample data for demo/recruiter access.
Run this once before deploying: python demo_mode.py
Or it runs automatically in the dashboard if no transactions exist.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timedelta
from tools.storage_tool import StorageTool
from models.transaction import Transaction


DEMO_TRANSACTIONS = [
    # May 2026
    ("Swiggy Food Order",           480,  "food",          "Swiggy",      "paid",    "sms",    "2026-05-23"),
    ("Netflix Subscription",         649,  "subscriptions", "Netflix",     "paid",    "email",  "2026-05-22"),
    ("Udemy Python Bootcamp",        499,  "education",     "Udemy",       "reminded","email",  "2026-05-21"),
    ("Amazon Purchase",             1299,  "shopping",      "Amazon",      "paid",    "sms",    "2026-05-20"),
    ("Electricity Bill TSECL",      1840,  "utilities",     "TSECL",       "paid",    "email",  "2026-05-19"),
    ("Gym Membership Cult.fit",      999,  "health",        "Cult.fit",    "ignored", "email",  "2026-05-18"),
    ("Uber Ride",                    220,  "travel",        "Uber",        "paid",    "sms",    "2026-05-17"),
    ("Zomato Gold Membership",       299,  "food",          "Zomato",      "paid",    "email",  "2026-05-16"),
    ("GitHub Pro Subscription",      850,  "subscriptions", "GitHub",      "paid",    "email",  "2026-05-15"),
    ("IndiGo Flight Ticket",        4100,  "travel",        "IndiGo",      "paid",    "email",  "2026-05-14"),
    ("Coursera ML Course",          2200,  "education",     "Coursera",    "paid",    "email",  "2026-05-13"),
    ("BigBasket Grocery",           1800,  "food",          "BigBasket",   "paid",    "sms",    "2026-05-12"),
    ("Adobe Creative Cloud",        1200,  "subscriptions", "Adobe",       "reminded","email",  "2026-05-11"),
    ("BookMyShow Movie",             800,  "entertainment", "BookMyShow",  "paid",    "email",  "2026-05-10"),
    ("Myntra Clothing Order",       1500,  "shopping",      "Myntra",      "paid",    "sms",    "2026-05-09"),
    ("Internet Bill Airtel",         999,  "utilities",     "Airtel",      "paid",    "email",  "2026-05-08"),
    ("Swiggy Order Lunch",           350,  "food",          "Swiggy",      "paid",    "sms",    "2026-05-07"),
    ("Rapido Bike Taxi",              80,  "travel",        "Rapido",      "paid",    "sms",    "2026-05-06"),
    ("Steam Game Purchase",          599,  "entertainment", "Steam",       "paid",    "email",  "2026-05-05"),
    ("1mg Medicine Order",           450,  "health",        "1mg",         "paid",    "email",  "2026-05-04"),
    ("Ola Cab Ride",                 180,  "travel",        "Ola",         "paid",    "sms",    "2026-05-03"),
    ("Spotify Premium",              119,  "subscriptions", "Spotify",     "paid",    "email",  "2026-05-02"),
    ("Decathlon Equipment",         2200,  "shopping",      "Decathlon",   "paid",    "email",  "2026-05-01"),

    # April 2026
    ("Netflix Subscription",         649,  "subscriptions", "Netflix",     "paid",    "email",  "2026-04-22"),
    ("Swiggy Order",                 420,  "food",          "Swiggy",      "paid",    "sms",    "2026-04-20"),
    ("Electricity Bill",            1720,  "utilities",     "TSECL",       "paid",    "email",  "2026-04-19"),
    ("Flipkart Sale Order",         3200,  "shopping",      "Flipkart",    "paid",    "sms",    "2026-04-15"),
    ("Udemy Course",                 399,  "education",     "Udemy",       "paid",    "email",  "2026-04-12"),
    ("OYO Hotel Stay",              2800,  "travel",        "OYO",         "paid",    "email",  "2026-04-10"),
    ("Gym Membership",               999,  "health",        "Cult.fit",    "paid",    "email",  "2026-04-08"),
    ("Zomato Delivery",              380,  "food",          "Zomato",      "paid",    "sms",    "2026-04-05"),
    ("GitHub Pro",                   850,  "subscriptions", "GitHub",      "paid",    "email",  "2026-04-03"),
    ("Doctor Consultation",          800,  "health",        "Apollo",      "paid",    "email",  "2026-04-01"),

    # March 2026
    ("Netflix Subscription",         649,  "subscriptions", "Netflix",     "paid",    "email",  "2026-03-22"),
    ("Swiggy Orders",                890,  "food",          "Swiggy",      "paid",    "sms",    "2026-03-18"),
    ("Electricity Bill",            1680,  "utilities",     "TSECL",       "paid",    "email",  "2026-03-17"),
    ("Amazon Shopping",             2100,  "shopping",      "Amazon",      "paid",    "sms",    "2026-03-14"),
    ("Flight Ticket",               5200,  "travel",        "AirIndia",    "paid",    "email",  "2026-03-10"),
    ("Coursera Subscription",       1500,  "education",     "Coursera",    "paid",    "email",  "2026-03-08"),
    ("Pharmacy",                     320,  "health",        "Apollo",      "paid",    "sms",    "2026-03-05"),
    ("Spotify",                      119,  "subscriptions", "Spotify",     "paid",    "email",  "2026-03-02"),
]


DEMO_MEMORY = {
    "trusted_merchants": ["netflix", "spotify", "github", "tsecl", "airtel", "swiggy"],
    "ignored_merchants": ["coupondunia", "magicpin"],
    "category_priorities": {
        "utilities":      9,
        "health":         8,
        "education":      8,
        "food":           7,
        "subscriptions":  6,
        "travel":         6,
        "shopping":       5,
        "entertainment":  4,
        "other":          3,
    },
    "approval_counts": {
        "netflix": 5,
        "swiggy":  8,
        "github":  4,
        "tsecl":   6,
    }
}


def seed_demo_data(storage: StorageTool, force: bool = False):
    """
    Seeds demo transactions into the database.
    Only runs if the database is empty (or force=True).
    """
    existing = storage.get_all_transactions(limit=5)
    if existing and not force:
        return False   # already has data

    print("  [Demo] Seeding demo data...")

    for desc, amount, cat, merchant, status, source, date_str in DEMO_TRANSACTIONS:
        txn = Transaction(
            description  = desc,
            amount       = float(amount),
            category     = cat,
            merchant     = merchant,
            status       = status,
            source       = source,
            created_at   = f"{date_str}T12:00:00",
        )
        storage.save_transaction(txn)

    # Seed memory
    for key, value in DEMO_MEMORY.items():
        storage.save_memory(key, value)

    print(f"  [Demo] Seeded {len(DEMO_TRANSACTIONS)} transactions and memory.")
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Re-seed even if data exists")
    args = parser.parse_args()

    storage = StorageTool()
    seeded  = seed_demo_data(storage, force=args.force)
    if seeded:
        print("✅ Demo data seeded successfully!")
        print("   Run: streamlit run dashboard/app.py")
    else:
        print("ℹ️  Database already has data. Use --force to re-seed.")
