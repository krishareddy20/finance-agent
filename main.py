"""
Finance Agent - Personal Life OS
Entry point with all 5 upgrades wired in.

Usage:
  python main.py                    # Run full cycle
  python main.py --email-only       # Email scan only
  python main.py --sms-test         # SMS test mode
  python main.py --report           # Monthly report
  python main.py --dashboard        # Terminal dashboard
  python main.py --eval             # Run evaluation suite
  python main.py --eval --quick     # Quick eval (classifier + regression)
  python main.py --train            # Retrain ML classifier
  python main.py --schedule         # Daily scheduled run
"""

import argparse
import schedule
import time
import os

from tools.storage_tool import StorageTool
from tools.gmail_tool import GmailTool
from tools.calendar_tool import CalendarTool
from tools.budget_tool import BudgetTool
from tools.vector_memory import VectorMemory
from ml.classifier import TransactionClassifier

from agents.email_agent import EmailAgent
from agents.decision_agent import DecisionAgent
from agents.action_agent import ActionAgent
from agents.memory_agent import MemoryAgent
from agents.insight_agent import InsightAgent

USER_EMAIL = os.getenv("USER_EMAIL", "you@gmail.com")


def build_agents(enable_sms=False, sms_test_mode=False):
    storage    = StorageTool()
    gmail      = GmailTool()
    calendar   = CalendarTool()
    budget     = BudgetTool(storage)
    vmem       = VectorMemory()           # Upgrade 1: vector memory
    classifier = TransactionClassifier()  # Upgrade 3: ML classifier

    email_agent    = EmailAgent(gmail)
    decision_agent = DecisionAgent(        # Upgrade 2: ReAct inside
        budget_tool=budget,
        vector_memory=vmem,
        classifier=classifier,
        storage_tool=storage,
    )
    action_agent   = ActionAgent(calendar, gmail, storage, USER_EMAIL)
    memory_agent   = MemoryAgent(storage)
    insight_agent  = InsightAgent(storage, budget)

    agents = {
        "email":    email_agent,
        "decision": decision_agent,
        "action":   action_agent,
        "memory":   memory_agent,
        "insight":  insight_agent,
        "storage":  storage,
        "vmem":     vmem,
        "clf":      classifier,
        "sms":      None,
    }

    if enable_sms or sms_test_mode:
        try:
            from tools.sms_tool import SMSTool
            from agents.sms_agent import SMSAgent
            sms_tool  = SMSTool() if not sms_test_mode else _DummySMSTool()
            agents["sms"] = SMSAgent(sms_tool, test_mode=sms_test_mode)
            print("  [SMS] SMS agent loaded.")
        except Exception as e:
            print(f"  [SMS] Could not load SMS agent: {e}")

    return agents


class _DummySMSTool:
    def get_sample_messages(self):
        from tools.sms_tool import SMSTool
        dummy = object.__new__(SMSTool)
        return dummy.get_sample_messages()
    def fetch_sms(self, **kwargs):
        return self.get_sample_messages()


def process_transactions(txns, agents, memory, source="email"):
    for txn in txns:
        print(f"\n  Processing [{source}]: {txn.description} — ₹{txn.amount}")
        txn.id = agents["storage"].save_transaction(txn)

        if source == "sms":
            if "[CREDIT]" not in txn.description:
                if agents["decision"].is_over_budget(txn):
                    print(f"  WARNING: {txn.category} budget is over 80%!")
            agents["memory"].record_decision(txn, "pay", memory)
            continue

        decision, reasoning, confidence = agents["decision"].evaluate(txn, memory)
        print(f"  Decision: {decision} (confidence: {confidence:.0%}) — {reasoning}")

        if agents["decision"].is_over_budget(txn):
            print(f"  WARNING: This would exceed 80% of {txn.category} budget!")

        if decision == "pay":
            if agents["decision"].requires_approval(txn):
                user_choice = agents["action"].request_approval(txn, reasoning)
                if user_choice == "y":
                    agents["action"].mark_paid(txn)
                    agents["memory"].record_decision(txn, "pay", memory)
                elif user_choice == "n":
                    agents["action"].mark_ignored(txn)
                    agents["memory"].record_decision(txn, "ignored", memory)
                elif user_choice == "remind":
                    agents["action"].schedule_reminder(txn, save=True)
                    agents["memory"].record_decision(txn, "reminded", memory)
            else:
                agents["action"].mark_paid(txn)
                agents["memory"].record_decision(txn, "pay", memory)
                print("  Auto-approved (below threshold).")
        elif decision == "remind":
            agents["action"].schedule_reminder(txn)
            agents["memory"].record_decision(txn, "reminded", memory)
        else:
            agents["action"].mark_ignored(txn)
            agents["memory"].record_decision(txn, "ignored", memory)


def run_cycle(agents, scan_email=True, scan_sms=True):
    print("\n Finance Agent — Starting cycle...\n")
    memory = agents["memory"].load()
    found  = False

    if scan_email:
        txns = agents["email"].scan_and_extract(max_emails=25)
        if txns:
            found = True
            process_transactions(txns, agents, memory, source="email")

    if scan_sms and agents["sms"]:
        txns = agents["sms"].scan_and_extract(days_back=7)
        if txns:
            found = True
            process_transactions(txns, agents, memory, source="sms")

    if not found:
        print("No new financial events found.")

    agents["memory"].learn_from_history(memory)
    agents["insight"].print_dashboard()
    print("\n Finance Agent cycle complete.\n")


def main():
    parser = argparse.ArgumentParser(description="Finance Agent")
    parser.add_argument("--email-only", action="store_true")
    parser.add_argument("--sms-only",   action="store_true")
    parser.add_argument("--sms-test",   action="store_true")
    parser.add_argument("--balance",    action="store_true")
    parser.add_argument("--report",     nargs="?", const="monthly", choices=["monthly","weekly"])
    parser.add_argument("--dashboard",  action="store_true")
    parser.add_argument("--learn",      action="store_true")
    parser.add_argument("--schedule",   action="store_true")
    parser.add_argument("--eval",       action="store_true", help="Run evaluation suite")
    parser.add_argument("--quick",      action="store_true", help="Quick eval (with --eval)")
    parser.add_argument("--train",      action="store_true", help="Retrain ML classifier")
    args = parser.parse_args()

    # ── Eval suite (no agents needed) ─────────────────────────────────────
    if args.eval:
        from eval.eval_suite import run_suite
        run_suite(quick=args.quick, save_report=True)
        return

    # ── Retrain classifier ─────────────────────────────────────────────────
    if args.train:
        from tools.storage_tool import StorageTool
        from ml.classifier import TransactionClassifier
        storage = StorageTool()
        clf     = TransactionClassifier()
        clf.retrain_with_db(storage)
        metrics = clf.evaluate()
        print(f"Classifier accuracy: {metrics['cv_accuracy_mean']:.1%} "
              f"(±{metrics['cv_accuracy_std']:.1%})")
        return

    need_sms = args.sms_only or args.sms_test or args.balance
    agents   = build_agents(enable_sms=need_sms, sms_test_mode=args.sms_test)

    if args.report:
        from agents.insight_agent import InsightAgent
        report = agents["insight"].generate_report(period=args.report)
        print(report)
        tips = agents["insight"].savings_recommendation()
        print("\nSavings Tips:\n" + tips)

    elif args.dashboard:
        agents["insight"].print_dashboard()

    elif args.learn:
        memory  = agents["memory"].load()
        insight = agents["memory"].learn_from_history(memory)
        print(f"Learning complete: {insight}")

    elif args.balance:
        if agents["sms"]:
            result = agents["sms"].get_balance_from_sms()
            if result:
                print(f"\n  Bank: {result['sender']}")
                print(f"  Balance: ₹{result['balance']:,.2f}")
                print(f"  As of: {result['date']}")

    elif args.sms_only:
        run_cycle(build_agents(enable_sms=True), scan_email=False, scan_sms=True)

    elif args.sms_test:
        run_cycle(agents, scan_email=False, scan_sms=True)

    elif args.email_only:
        run_cycle(agents, scan_email=True, scan_sms=False)

    elif args.schedule:
        print("Scheduling daily run at 08:00...")
        full = build_agents(enable_sms=True)
        schedule.every().day.at("08:00").do(run_cycle, agents=full)
        schedule.every().sunday.at("09:00").do(
            lambda: print(full["insight"].generate_report("weekly"))
        )
        while True:
            schedule.run_pending()
            time.sleep(60)

    else:
        run_cycle(agents, scan_email=True, scan_sms=False)


if __name__ == "__main__":
    main()
