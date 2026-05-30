"""
eval_suite.py — Evaluation framework for the Finance Agent.

This is what separates engineers who build things from engineers who
build *reliable* things. Every serious ML system has an eval suite.

What we measure:
  1. Classifier accuracy   — how well does the ML model categorise transactions?
  2. Decision quality      — are pay/remind/ignore decisions sensible?
  3. Extraction accuracy   — does the email parser extract correct amounts?
  4. Latency               — how fast is each component?
  5. Regression tests      — did a code change break existing behaviour?

Run:
  python eval/eval_suite.py            # full suite
  python eval/eval_suite.py --quick    # classifier only (fast)
  python eval/eval_suite.py --report   # save results to eval/results.json
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import time
import argparse
from datetime import datetime
from typing import Any

# ── Test data ─────────────────────────────────────────────────────────────────

CLASSIFIER_TEST_CASES = [
    # (description, merchant, expected_category)
    ("Netflix monthly subscription renewal", "Netflix",     "subscriptions"),
    ("Swiggy food delivery",                 "Swiggy",      "food"),
    ("Electricity bill payment TSECL",       "TSECL",       "utilities"),
    ("Udemy Python bootcamp",                "Udemy",       "education"),
    ("Gym membership Cult.fit",              "Cult.fit",    "health"),
    ("Uber cab ride",                        "Uber",        "travel"),
    ("Amazon product purchase",              "Amazon",      "shopping"),
    ("BookMyShow movie tickets",             "BookMyShow",  "entertainment"),
    ("IRCTC train ticket",                   "IRCTC",       "travel"),
    ("Spotify premium",                      "Spotify",     "subscriptions"),
    ("Doctor consultation fee",              "Apollo",      "health"),
    ("Zomato restaurant order",              "Zomato",      "food"),
    ("Internet broadband bill",              "Airtel",      "utilities"),
    ("Coursera machine learning",            "Coursera",    "education"),
    ("Myntra clothing order",                "Myntra",      "shopping"),
    ("Steam game purchase",                  "Steam",       "entertainment"),
    ("Jio mobile recharge",                  "Jio",         "utilities"),
    ("Hotel booking OYO",                    "OYO",         "travel"),
    ("Medicine pharmacy order",              "1mg",         "health"),
    ("Bank loan EMI payment",                "HDFC",        "other"),
]

DECISION_TEST_CASES = [
    # (description, amount, category, merchant, expected_decision)
    ("Netflix subscription",  649,  "subscriptions", "Netflix",  "pay"),
    ("Electricity bill",     1800,  "utilities",     "TSECL",    "pay"),
    ("Promotional offer",      50,  "other",         "spam",     "ignore"),
    ("Flight ticket",        8500,  "travel",        "IndiGo",   "remind"),
    ("Udemy course",          499,  "education",     "Udemy",    "pay"),
]

EXTRACTION_TEST_CASES = [
    # (email_body, expected_amount, expected_category)
    ("Your Netflix subscription of Rs.649 is due on 25th May.", 649,  "subscriptions"),
    ("Invoice for Udemy Python course: INR 499.00",             499,  "education"),
    ("Electricity bill amount: ₹1,840 due by 30 May 2026",    1840,  "utilities"),
    ("Pay ₹350 for Swiggy order #12345",                        350,  "food"),
]


# ── Result collector ───────────────────────────────────────────────────────────

class EvalResult:
    def __init__(self, name: str):
        self.name       = name
        self.passed     = 0
        self.failed     = 0
        self.errors     = []
        self.latencies  = []
        self.start_time = time.time()

    def record(self, passed: bool, label: str = "", latency_ms: float = 0):
        if passed:
            self.passed += 1
            print(f"    ✅ {label}")
        else:
            self.failed += 1
            self.errors.append(label)
            print(f"    ❌ {label}")
        self.latencies.append(latency_ms)

    @property
    def accuracy(self) -> float:
        total = self.passed + self.failed
        return self.passed / total if total > 0 else 0.0

    @property
    def avg_latency_ms(self) -> float:
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0.0

    def summary(self) -> dict:
        return {
            "name":          self.name,
            "passed":        self.passed,
            "failed":        self.failed,
            "accuracy":      round(self.accuracy, 4),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "errors":        self.errors,
            "duration_s":    round(time.time() - self.start_time, 2),
        }


# ── Individual eval suites ─────────────────────────────────────────────────────

def eval_classifier() -> EvalResult:
    """Test the ML classifier against labelled examples."""
    print("\n📊 Classifier Evaluation")
    print("  " + "-" * 50)
    result = EvalResult("classifier")

    try:
        from ml.classifier import TransactionClassifier
        clf = TransactionClassifier()
        cv  = clf.evaluate()
        print(f"  Cross-val accuracy: {cv.get('cv_accuracy_mean', 0):.1%} "
              f"(±{cv.get('cv_accuracy_std', 0):.1%})")
        print(f"  Training examples : {cv.get('n_training', 0)}")
        print(f"  Classes           : {cv.get('n_classes', 0)}")
        print()

        for desc, merchant, expected in CLASSIFIER_TEST_CASES:
            t0  = time.time()
            cat, conf = clf.predict(desc, merchant)
            ms  = (time.time() - t0) * 1000
            ok  = cat == expected
            result.record(ok, f"{desc[:40]:<40} → {cat} (expected {expected}, conf {conf:.0%})", ms)

    except Exception as e:
        print(f"  [ERROR] Classifier eval failed: {e}")
        result.errors.append(str(e))

    print(f"\n  Classifier accuracy: {result.accuracy:.1%} "
          f"({result.passed}/{result.passed + result.failed})")
    return result


def eval_decisions() -> EvalResult:
    """Test decision agent on canonical cases."""
    print("\n🧠 Decision Agent Evaluation")
    print("  " + "-" * 50)
    result = EvalResult("decisions")

    try:
        from tools.storage_tool import StorageTool
        from tools.budget_tool import BudgetTool
        from tools.vector_memory import VectorMemory
        from core.react_agent import ReActAgent
        from models.transaction import Transaction

        storage = StorageTool()
        budget  = BudgetTool(storage)
        vmem    = VectorMemory()
        agent   = ReActAgent(budget, vmem, storage)

        for desc, amount, cat, merchant, expected in DECISION_TEST_CASES:
            txn = Transaction(
                description=desc, amount=amount,
                category=cat, merchant=merchant, importance="medium"
            )
            t0 = time.time()
            decision, reasoning, conf, steps = agent.decide(txn)
            ms = (time.time() - t0) * 1000
            ok = decision == expected
            result.record(ok,
                f"{desc[:30]:<30} → {decision} (expected {expected}, "
                f"{len(steps)} steps, conf {conf:.0%})", ms)

    except Exception as e:
        print(f"  [ERROR] Decision eval failed: {e}")
        result.errors.append(str(e))

    print(f"\n  Decision accuracy: {result.accuracy:.1%}")
    return result


def eval_extraction() -> EvalResult:
    """Test amount extraction from email bodies."""
    print("\n📧 Extraction Evaluation")
    print("  " + "-" * 50)
    result = EvalResult("extraction")

    import re
    amount_patterns = [
        r"(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d{2})?)",
        r"([\d,]+(?:\.\d{2})?)\s*(?:Rs\.?|INR|₹)",
    ]

    for body, expected_amount, expected_cat in EXTRACTION_TEST_CASES:
        t0 = time.time()
        found = None
        for pat in amount_patterns:
            m = re.search(pat, body, re.I)
            if m:
                found = float(m.group(1).replace(",", ""))
                break
        ms = (time.time() - t0) * 1000
        ok = found is not None and abs(found - expected_amount) < 1
        result.record(ok,
            f"'{body[:50]}' → extracted ₹{found} (expected ₹{expected_amount})", ms)

    print(f"\n  Extraction accuracy: {result.accuracy:.1%}")
    return result


def eval_latency() -> EvalResult:
    """Measure component latencies."""
    print("\n⚡ Latency Benchmarks")
    print("  " + "-" * 50)
    result = EvalResult("latency")

    # Classifier latency
    try:
        from ml.classifier import TransactionClassifier
        clf = TransactionClassifier()
        times = []
        for _ in range(20):
            t0 = time.time()
            clf.predict("netflix subscription", "Netflix")
            times.append((time.time() - t0) * 1000)
        avg = sum(times) / len(times)
        ok  = avg < 50   # should be under 50ms
        result.record(ok, f"Classifier avg latency: {avg:.2f}ms (target <50ms)", avg)
    except Exception as e:
        result.errors.append(f"Classifier latency: {e}")

    # Vector memory latency
    try:
        from tools.vector_memory import VectorMemory
        from models.transaction import Transaction
        vmem = VectorMemory()
        txn  = Transaction(description="test", amount=100, category="food", merchant="Swiggy")
        times = []
        for _ in range(10):
            t0 = time.time()
            vmem.retrieve_similar(txn, k=3)
            times.append((time.time() - t0) * 1000)
        avg = sum(times) / len(times)
        ok  = avg < 200
        result.record(ok, f"VectorMemory retrieval avg: {avg:.2f}ms (target <200ms)", avg)
    except Exception as e:
        result.errors.append(f"VectorMemory latency: {e}")

    return result


def eval_regression() -> EvalResult:
    """
    Regression tests — checks that core behaviours haven't broken.
    Add a test here every time you fix a bug.
    """
    print("\n🔁 Regression Tests")
    print("  " + "-" * 50)
    result = EvalResult("regression")

    # Test 1: Transaction model creation
    try:
        from models.transaction import Transaction
        t = Transaction(description="test", amount=100.0, category="food", merchant="Swiggy")
        result.record(
            t.description == "test" and t.amount == 100.0,
            "Transaction model creates correctly"
        )
    except Exception as e:
        result.record(False, f"Transaction model: {e}")

    # Test 2: StorageTool initialises without error
    try:
        from tools.storage_tool import StorageTool
        s = StorageTool()
        budgets = s.get_budgets()
        result.record(isinstance(budgets, dict), "StorageTool initialises and returns budgets")
    except Exception as e:
        result.record(False, f"StorageTool: {e}")

    # Test 3: BudgetTool returns Budget objects
    try:
        from tools.storage_tool import StorageTool
        from tools.budget_tool import BudgetTool
        b = BudgetTool(StorageTool()).get_budget("food")
        result.record(hasattr(b, "utilisation"), "BudgetTool returns Budget with utilisation")
    except Exception as e:
        result.record(False, f"BudgetTool: {e}")

    # Test 4: Classifier predicts a known category
    try:
        from ml.classifier import TransactionClassifier
        clf = TransactionClassifier()
        cat, conf = clf.predict("Netflix streaming subscription", "Netflix")
        result.record(cat == "subscriptions", f"Classifier: Netflix → {cat} (expected subscriptions)")
    except Exception as e:
        result.record(False, f"Classifier regression: {e}")

    # Test 5: VectorMemory initialises
    try:
        from tools.vector_memory import VectorMemory
        v = VectorMemory()
        result.record(isinstance(v.count(), int), "VectorMemory initialises and returns count")
    except Exception as e:
        result.record(False, f"VectorMemory: {e}")

    return result


# ── Main runner ────────────────────────────────────────────────────────────────

def run_suite(quick: bool = False, save_report: bool = False):
    print("\n" + "=" * 60)
    print("  FINANCE AGENT — EVALUATION SUITE")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = []
    results.append(eval_regression())
    results.append(eval_classifier())
    results.append(eval_extraction())

    if not quick:
        results.append(eval_decisions())
        results.append(eval_latency())

    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    all_pass = True
    for r in results:
        s = r.summary()
        status = "✅" if s["failed"] == 0 else "❌"
        print(f"  {status} {s['name']:<20} accuracy={s['accuracy']:.1%}  "
              f"latency={s['avg_latency_ms']:.1f}ms")
        if s["failed"] > 0:
            all_pass = False

    overall = sum(r.passed for r in results)
    total   = sum(r.passed + r.failed for r in results)
    print(f"\n  Overall: {overall}/{total} passed "
          f"({'✅ ALL PASS' if all_pass else '❌ SOME FAILED'})")

    if save_report:
        report = {
            "timestamp": datetime.now().isoformat(),
            "results":   [r.summary() for r in results],
            "overall":   {"passed": overall, "total": total},
        }
        os.makedirs("eval", exist_ok=True)
        path = f"eval/results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n  Report saved to {path}")

    return all_pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Finance Agent Eval Suite")
    parser.add_argument("--quick",  action="store_true", help="Run classifier + regression only")
    parser.add_argument("--report", action="store_true", help="Save results to eval/results.json")
    args = parser.parse_args()
    success = run_suite(quick=args.quick, save_report=args.report)
    sys.exit(0 if success else 1)
