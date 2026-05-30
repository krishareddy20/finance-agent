"""
Finance Agent Dashboard — Demo-ready with auto seeding
Run: streamlit run dashboard/app.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from tools.storage_tool import StorageTool
from tools.budget_tool import BudgetTool
from models.transaction import Transaction

st.set_page_config(page_title="Finance Agent 💳", page_icon="💳", layout="wide")
st.markdown("""
<style>
.stApp{background-color:#0f172a;color:#e2e8f0}
.block-container{padding-top:1.5rem}
div[data-testid="metric-container"]{background:#1e293b;border-radius:12px;padding:16px;border:1px solid #334155}
.stButton>button{background:#6c63ff;color:white;border:none;border-radius:8px;font-weight:600}
.stButton>button:hover{background:#5a52d5;color:white}
h1,h2,h3{color:#e2e8f0!important}
.report-box{background:#1e293b;border-radius:16px;padding:28px;border:1px solid #334155;line-height:1.9}
.tip-card{background:#1e293b;border-radius:12px;padding:16px 20px;margin-bottom:10px;border-left:4px solid #6c63ff}
.tip-card.green{border-left-color:#00d4aa}
.tip-card.amber{border-left-color:#ffb347}
.tip-card.red{border-left-color:#ff4d6d}
.react-step{background:#1e293b;border-radius:10px;padding:14px 18px;margin-bottom:8px;border-left:3px solid #6c63ff}
.stDownloadButton>button{background:#00d4aa;color:#0f172a;border:none;border-radius:8px;font-weight:700}
.demo-banner{background:linear-gradient(135deg,#1e1b4b,#312e81);border:1px solid #6c63ff;
             border-radius:12px;padding:14px 20px;margin-bottom:20px}
</style>
""", unsafe_allow_html=True)

# ── Auto-seed demo data if DB is empty ───────────────────────────────────────
@st.cache_resource
def get_tools():
    storage = StorageTool()
    budget  = BudgetTool(storage)
    # Auto-seed if empty
    try:
        from demo_mode import seed_demo_data
        seed_demo_data(storage, force=False)
    except Exception:
        pass
    return storage, budget

@st.cache_resource
def get_classifier():
    try:
        from ml.classifier import TransactionClassifier
        return TransactionClassifier()
    except Exception:
        return None

@st.cache_resource
def get_vector_memory():
    try:
        from tools.vector_memory import VectorMemory
        return VectorMemory()
    except Exception:
        return None

storage, budget_tool = get_tools()
month = datetime.now().strftime("%Y-%m")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💳 FinanceOS")
    st.markdown("*Personal Finance Agent*")
    st.markdown("---")

    # Demo mode toggle
    demo_mode = st.toggle("🎭 Demo Mode", value=True,
        help="Shows sample data. Turn off when using your real Gmail.")
    if demo_mode:
        st.caption("Showing sample data for demo purposes.")

    st.markdown("---")
    page = st.radio("Navigate", [
        "📊 Dashboard",
        "➕ Add Transaction",
        "📧 Scan Gmail",
        "📱 SMS Simulation",
        "📋 Transactions",
        "💰 Budget",
        "📝 Reports & Tips",
        "🔬 AI Engine",
        "🧠 Memory",
    ])
    st.markdown("---")
    st.markdown("🟢 **Agent Active**")
    st.caption("ReAct · RAG · ML Classifier")
    st.markdown("---")
    st.markdown("**Tech Stack**")
    st.caption("Python · Streamlit · SQLite")
    st.caption("OpenRouter LLM (Free)")
    st.caption("Gmail OAuth · Google Calendar")
    st.caption("ChromaDB · scikit-learn")

# ── Demo banner ───────────────────────────────────────────────────────────────
def show_demo_banner():
    if demo_mode:
        st.markdown("""
        <div class="demo-banner">
            🎭 <strong>Demo Mode</strong> — Showing realistic sample data.
            This agent connects to real Gmail, parses bank SMS, and uses
            a free LLM (Llama 3.1 8B via OpenRouter) for smart decisions.
        </div>
        """, unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def make_report_text(budgets, txns, period="Monthly"):
    total_spent = sum(b.spent for b in budgets.values())
    total_limit = sum(b.limit for b in budgets.values())
    pct = (total_spent/total_limit*100) if total_limit else 0
    verdict = "On Track" if pct<75 else ("Caution" if pct<90 else "Over Budget")
    lines = [f"FINANCE AGENT - {period.upper()} REPORT",
             f"Period: {month}  |  Generated: {datetime.now().strftime('%d %b %Y %H:%M')}",
             "="*60, "", f"STATUS: {verdict}",
             f"  Total Budget : Rs.{total_limit:,.0f}",
             f"  Total Spent  : Rs.{total_spent:,.0f}  ({pct:.1f}% used)",
             f"  Remaining    : Rs.{total_limit-total_spent:,.0f}",
             f"  Transactions : {len(txns)}", "", "CATEGORY BREAKDOWN:"]
    for cat, b in sorted(budgets.items()):
        bar = "X"*int(b.utilisation*10) + "."*(10-int(b.utilisation*10))
        lines.append(f"  {cat.capitalize():<16} {bar}  Rs.{b.spent:>7,.0f} / Rs.{b.limit:>7,.0f}")
    lines += ["", "="*60, "Generated by Finance Agent - ReAct + RAG + ML Classifier"]
    return "\n".join(lines)

def get_saving_tips(budgets, txns):
    tips = []
    total_spent = sum(b.spent for b in budgets.values())
    total_limit = sum(b.limit for b in budgets.values())
    for cat, b in budgets.items():
        if b.utilisation >= 1.0:
            tips.append(("red", f"🚨 {cat.capitalize()} OVER budget by Rs.{b.spent-b.limit:,.0f}. Pause spending."))
        elif b.utilisation >= 0.85:
            tips.append(("amber", f"⚠️ {cat.capitalize()} at {b.utilisation:.0%}. Only Rs.{b.remaining:,.0f} left."))
    if budgets.get("food") and budgets["food"].utilisation > 0.6:
        tips.append(("amber", "🍔 Food spending high. Cook at home 3x/week — saves Rs.1,500-2,000/month."))
    if budgets.get("subscriptions") and budgets["subscriptions"].utilisation > 0.7:
        tips.append(("amber", "📺 Audit subscriptions — cancel anything unused in the last 2 weeks."))
    if budgets.get("shopping") and budgets["shopping"].utilisation > 0.6:
        tips.append(("amber", "🛍️ Try 48-hour rule: wait 2 days before buying anything above Rs.500."))
    if budgets.get("health") and budgets["health"].utilisation < 0.4:
        tips.append(("green", "💪 Health budget well managed. Consider investing in a preventive checkup."))
    if budgets.get("education") and budgets["education"].utilisation < 0.3:
        tips.append(("green", "📚 Education budget barely used. Great time to invest in a course!"))
    savings = total_limit - total_spent
    if savings > 0:
        tips.append(("green", f"💰 Saved Rs.{savings:,.0f} ({savings/total_limit*100:.0f}% of budget). Move to savings account."))
    tips.append(("green", "📊 Track UPI spending weekly — most underestimate food & shopping by 30%."))
    tips.append(("amber", "💡 Use cashback cards for subscriptions — earn 1-5% back on every purchase."))
    return tips

# ── Dashboard ─────────────────────────────────────────────────────────────────
if page == "📊 Dashboard":
    show_demo_banner()
    st.title("📊 Dashboard")
    st.caption(f"Month: {month}")

    budgets     = budget_tool.get_all_budgets(month)
    total_spent = sum(b.spent for b in budgets.values())
    total_limit = sum(b.limit for b in budgets.values())
    all_txns    = storage.get_all_transactions(limit=500)
    this_month  = [t for t in all_txns if t["created_at"][:7] == month]

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Spent",  f"Rs.{total_spent:,.0f}")
    c2.metric("Total Budget", f"Rs.{total_limit:,.0f}")
    c3.metric("Remaining",    f"Rs.{total_limit-total_spent:,.0f}")
    c4.metric("Transactions", len(this_month))

    st.markdown("---")
    col1, col2 = st.columns([2,1])
    with col1:
        cats  = list(budgets.keys())
        spent = [b.spent for b in budgets.values()]
        lims  = [b.limit for b in budgets.values()]
        fig = go.Figure(data=[
            go.Bar(name="Spent",  x=cats, y=spent, marker_color="#6c63ff"),
            go.Bar(name="Budget", x=cats, y=lims,  marker_color="#334155"),
        ])
        fig.update_layout(barmode="group", title="Budget vs Spending",
            paper_bgcolor="#1e293b", plot_bgcolor="#1e293b",
            font_color="#e2e8f0", margin=dict(t=40,b=0))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        if any(s > 0 for s in spent):
            fig2 = px.pie(values=spent, names=cats, title="Spending Split",
                color_discrete_sequence=px.colors.qualitative.Set3, hole=0.4)
            fig2.update_layout(paper_bgcolor="#1e293b", font_color="#e2e8f0",
                margin=dict(t=40,b=0), showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

    # Trend chart
    all_txns_df = pd.DataFrame(storage.get_all_transactions(limit=500))
    if not all_txns_df.empty:
        all_txns_df["month"] = all_txns_df["created_at"].str[:7]
        monthly = all_txns_df.groupby("month")["amount"].sum().reset_index()
        fig3 = px.area(monthly, x="month", y="amount", title="Spending Trend",
            color_discrete_sequence=["#6c63ff"])
        fig3.update_layout(paper_bgcolor="#1e293b", plot_bgcolor="#1e293b",
            font_color="#e2e8f0", margin=dict(t=40,b=0))
        fig3.update_traces(fill='tozeroy', fillcolor='rgba(108,99,255,0.15)')
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("### Recent Transactions")
    if this_month:
        st.dataframe(pd.DataFrame(this_month[:8])[["description","amount","category","status","source"]],
            use_container_width=True, hide_index=True)
    else:
        st.info("No transactions this month. Demo data is from previous months — check Transactions page.")

# ── Add Transaction ───────────────────────────────────────────────────────────
elif page == "➕ Add Transaction":
    show_demo_banner()
    st.title("➕ Add Transaction Manually")
    with st.form("manual_entry", clear_on_submit=True):
        col1,col2 = st.columns(2)
        desc     = col1.text_input("Description *", placeholder="e.g. Netflix Subscription")
        merchant = col2.text_input("Merchant", placeholder="e.g. Netflix")
        col3,col4 = st.columns(2)
        amount   = col3.number_input("Amount (Rs.) *", min_value=0.0, step=10.0)
        category = col4.selectbox("Category", ["food","subscriptions","utilities","health","travel","entertainment","shopping","education","other"])
        col5,col6 = st.columns(2)
        status   = col5.selectbox("Status", ["paid","pending","reminded","ignored"])
        source   = col6.selectbox("Source", ["manual","email","sms"])
        importance = st.select_slider("Importance", ["low","medium","high"], value="medium")
        if st.form_submit_button("💾 Save Transaction"):
            if not desc or amount <= 0:
                st.error("Description and Amount required.")
            else:
                storage.save_transaction(Transaction(description=desc, amount=amount,
                    category=category, merchant=merchant, importance=importance,
                    source=source, status=status))
                st.success(f"✅ Saved: {desc} — Rs.{amount:,.0f}")
                st.balloons()

    st.markdown("---")
    st.markdown("### ⚡ Quick Add")
    quick = [("🍔 Swiggy",350,"food","Swiggy"),("🎬 Netflix",649,"subscriptions","Netflix"),
             ("⚡ Electricity",1800,"utilities","TSECL"),("🚗 Uber",220,"travel","Uber"),
             ("📦 Amazon",1299,"shopping","Amazon"),("💪 Gym",999,"health","Cult.fit")]
    cols = st.columns(3)
    for i,(d,a,c,m) in enumerate(quick):
        with cols[i%3]:
            if st.button(f"{d} — Rs.{a:,}", key=f"q{i}"):
                storage.save_transaction(Transaction(description=d,amount=a,category=c,merchant=m,status="paid",source="manual"))
                st.success("Added!")

# ── Scan Gmail ────────────────────────────────────────────────────────────────
elif page == "📧 Scan Gmail":
    st.title("📧 Scan Gmail")
    if demo_mode:
        st.info("📧 In demo mode, Gmail scanning is simulated. In production, this connects to real Gmail via OAuth and scans unread emails for payment/invoice keywords, then uses the LLM to extract amount, category, merchant, and deadline.")
        st.markdown("**What it does in production:**")
        st.markdown("- Connects via Gmail OAuth2")
        st.markdown("- Fetches unread emails matching financial keywords")
        st.markdown("- Sends each email to LLM for extraction")
        st.markdown("- Returns structured Transaction objects")
        st.markdown("- Marks emails as read after processing")
    else:
        max_emails = st.slider("Max emails to scan", 5, 50, 25)
        if st.button("🔍 Scan Now"):
            with st.spinner("Scanning Gmail..."):
                try:
                    from tools.gmail_tool import GmailTool
                    from agents.email_agent import EmailAgent
                    txns = EmailAgent(GmailTool()).scan_and_extract(max_emails=max_emails)
                    if not txns:
                        st.warning("No financial emails found.")
                    else:
                        st.success(f"Found {len(txns)} financial email(s)!")
                        for txn in txns:
                            with st.expander(f"📧 {txn.description} — Rs.{txn.amount:,.0f}"):
                                ca,cb,cc = st.columns(3)
                                if ca.button("✅ Pay",    key=f"p_{txn.email_id}"): txn.status="paid";     storage.save_transaction(txn); st.success("Saved!")
                                if cb.button("🔔 Remind", key=f"r_{txn.email_id}"): txn.status="reminded"; storage.save_transaction(txn); st.success("Saved!")
                                if cc.button("❌ Ignore", key=f"i_{txn.email_id}"): txn.status="ignored";  storage.save_transaction(txn); st.info("Ignored.")
                except Exception as e:
                    st.error(f"Error: {e}")

# ── SMS ───────────────────────────────────────────────────────────────────────
elif page == "📱 SMS Simulation":
    show_demo_banner()
    st.title("📱 SMS Bank Alert Parser")
    st.info("💡 Parses Indian bank SMS alerts using regex patterns. On a real Android phone via USB+ADB, reads actual SMS messages.")

    sample_sms = [
        {"sender":"HDFCBK",  "body":"Dear Customer, Rs.1,299.00 debited from A/c XX1234 on 23-May for Amazon. Avl Bal: Rs.18,450.50","date":datetime.now().isoformat()},
        {"sender":"ICICIBK", "body":"INR 499.00 debited from your account for Netflix subscription. Available Balance: INR 12,300.00","date":datetime.now().isoformat()},
        {"sender":"SBIINB",  "body":"Your A/c XXXX5678 is credited with Rs.25,000.00 on 23-May-26. Avl Bal Rs.37,300.00","date":datetime.now().isoformat()},
        {"sender":"HDFCBK",  "body":"Rs.480.00 debited from A/c XX1234 for Swiggy on 22-May. Avl Bal: Rs.17,970.50","date":datetime.now().isoformat()},
        {"sender":"AXISBK",  "body":"INR 220.00 spent on Uber on 22-May-26 via Axis Bank Card XX9012. Available Bal: INR 8,100.00","date":datetime.now().isoformat()},
        {"sender":"KOTAKB",  "body":"Rs.1,840.00 debited from A/c XX4567 towards TSECL Electricity Bill. Balance: Rs.22,160.00","date":datetime.now().isoformat()},
    ]
    for msg in sample_sms:
        with st.expander(f"📱 {msg['sender']} — {msg['body'][:55]}..."):
            st.code(msg["body"])

    if st.button("🔄 Parse & Save All"):
        from agents.sms_agent import SMSAgent
        class M:
            def get_sample_messages(self): return sample_sms
            def fetch_sms(self,**kw): return sample_sms
        txns = SMSAgent(M(), test_mode=True).scan_and_extract(days_back=7)
        if txns:
            for t in txns: storage.save_transaction(t)
            st.success(f"Saved {len(txns)} SMS transactions!")
            st.dataframe(pd.DataFrame([{"Description":t.description[:50],"Amount":f"Rs.{t.amount:,.0f}","Category":t.category} for t in txns]),use_container_width=True,hide_index=True)

    st.markdown("---")
    st.markdown("### Paste Your Own Bank SMS")
    with st.form("sms_form"):
        sender   = st.text_input("Bank", value="HDFCBK")
        sms_body = st.text_area("SMS", placeholder="Rs.500.00 debited from A/c XX1234 for Swiggy. Avl Bal: Rs.10,000.00")
        if st.form_submit_button("Parse & Save"):
            from agents.sms_agent import SMSAgent
            class S:
                def get_sample_messages(self): return [{"sender":sender,"body":sms_body,"date":datetime.now().isoformat()}]
                def fetch_sms(self,**kw): return self.get_sample_messages()
            txns = SMSAgent(S(),test_mode=True).scan_and_extract()
            if txns:
                for t in txns: storage.save_transaction(t)
                st.success(f"Saved: {txns[0].description} — Rs.{txns[0].amount}")
            else: st.warning("Could not parse that SMS.")

# ── Transactions ──────────────────────────────────────────────────────────────
elif page == "📋 Transactions":
    show_demo_banner()
    st.title("📋 All Transactions")
    txns = storage.get_all_transactions(limit=500)
    if not txns:
        st.info("No transactions yet.")
    else:
        df = pd.DataFrame(txns)
        c1,c2,c3 = st.columns(3)
        sc = c1.selectbox("Category", ["All"]+sorted(df["category"].unique().tolist()))
        ss = c2.selectbox("Status",   ["All"]+sorted(df["status"].unique().tolist()))
        so = c3.selectbox("Source",   ["All"]+sorted(df["source"].unique().tolist()))
        if sc!="All": df=df[df["category"]==sc]
        if ss!="All": df=df[df["status"]==ss]
        if so!="All": df=df[df["source"]==so]
        st.dataframe(df[["id","description","amount","category","merchant","status","source","created_at"]],use_container_width=True,hide_index=True)
        ca,cb = st.columns(2)
        ca.metric("Shown", len(df))
        cb.metric("Total", f"Rs.{df['amount'].sum():,.2f}")
        st.download_button("📥 Download CSV", df.to_csv(index=False), "transactions.csv", "text/csv")

# ── Budget ────────────────────────────────────────────────────────────────────
elif page == "💰 Budget":
    show_demo_banner()
    st.title("💰 Budget Settings")
    budgets = budget_tool.get_all_budgets(month)
    ts = sum(b.spent for b in budgets.values())
    tl = sum(b.limit for b in budgets.values())
    c1,c2,c3 = st.columns(3)
    c1.metric("Total Budget", f"Rs.{tl:,.0f}")
    c2.metric("Total Spent",  f"Rs.{ts:,.0f}")
    c3.metric("Remaining",    f"Rs.{tl-ts:,.0f}")
    st.markdown("---")
    for cat,b in sorted(budgets.items()):
        col1,col2 = st.columns([3,1])
        pct = min(int((b.spent/b.limit)*100),100) if b.limit>0 else 0
        col1.progress(pct/100, text=f"{cat.capitalize()} — Rs.{b.spent:,.0f} / Rs.{b.limit:,.0f} ({pct}%)")
        nl = col2.number_input("",value=float(b.limit),step=500.0,key=f"b_{cat}",label_visibility="collapsed")
        if nl!=b.limit: budget_tool.update_limit(cat,nl); st.success(f"Updated {cat} to Rs.{nl:,.0f}")

# ── Reports ───────────────────────────────────────────────────────────────────
elif page == "📝 Reports & Tips":
    show_demo_banner()
    st.title("📝 Reports & Savings Tips")
    budgets = budget_tool.get_all_budgets(month)
    txns    = storage.get_all_transactions(limit=500)
    this_m  = [t for t in txns if t["created_at"][:7]==month]
    total_spent = sum(b.spent for b in budgets.values())
    total_limit = sum(b.limit for b in budgets.values())
    pct_used = (total_spent/total_limit*100) if total_limit else 0
    if pct_used<75: st.success(f"✅ On track! Spent Rs.{total_spent:,.0f} of Rs.{total_limit:,.0f} ({pct_used:.1f}%)")
    elif pct_used<90: st.warning(f"⚠️ Caution — Rs.{total_spent:,.0f} of Rs.{total_limit:,.0f} ({pct_used:.1f}%)")
    else: st.error(f"🚨 Over budget! Rs.{total_spent:,.0f} of Rs.{total_limit:,.0f} ({pct_used:.1f}%)")
    st.markdown("---")
    tab1,tab2 = st.tabs(["📄 Monthly Report","💡 Savings Tips"])
    with tab1:
        report_text = make_report_text(budgets, this_m)
        c1,c2,c3 = st.columns(3)
        c1.metric("Total Spent",f"Rs.{total_spent:,.0f}"); c2.metric("Total Budget",f"Rs.{total_limit:,.0f}"); c3.metric("Transactions",len(txns))
        st.markdown("---")
        for cat,b in sorted(budgets.items(),key=lambda x:x[1].spent,reverse=True):
            pct = min(b.utilisation,1.0)
            color = "#ff4d6d" if pct>=0.9 else ("#ffb347" if pct>=0.75 else "#00d4aa")
            ca,cb = st.columns([4,1])
            ca.progress(pct, text=f"{cat.capitalize()}: Rs.{b.spent:,.0f} / Rs.{b.limit:,.0f}")
            cb.markdown(f"<span style='color:{color};font-weight:700'>{pct*100:.0f}%</span>",unsafe_allow_html=True)
        st.markdown("---")
        cd1,cd2 = st.columns(2)
        cd1.download_button("📥 Download Report (.txt)", report_text, f"finance_report_{month}.txt","text/plain")
        if txns: cd2.download_button("📊 Download Data (.csv)",pd.DataFrame(txns).to_csv(index=False),f"transactions_{month}.csv","text/csv")
    with tab2:
        tips = get_saving_tips(budgets, this_m)
        for tip_type,tip_text in tips:
            color_map={"red":"#ff4d6d","amber":"#ffb347","green":"#00d4aa"}
            color = color_map.get(tip_type,"#6c63ff")
            st.markdown(f'<div class="tip-card {tip_type}"><span style="font-size:14px;color:#e2e8f0">{tip_text}</span></div>',unsafe_allow_html=True)
        tips_text = f"FINANCE AGENT - SAVINGS TIPS\nGenerated: {datetime.now().strftime('%d %b %Y')}\n{'='*50}\n\n"
        for i,(t,txt) in enumerate(tips,1): tips_text+=f"{i}. {txt}\n\n"
        st.download_button("📥 Download Tips (.txt)", tips_text, f"savings_tips_{month}.txt","text/plain")

# ── AI Engine ─────────────────────────────────────────────────────────────────
elif page == "🔬 AI Engine":
    show_demo_banner()
    st.title("🔬 AI Engine")
    st.caption("Live view into the ML classifier, ReAct reasoning, vector memory, and eval suite")

    tab1,tab2,tab3,tab4 = st.tabs(["🤖 ML Classifier","🧩 ReAct Reasoning","🗄️ Vector Memory","📊 Eval Suite"])

    with tab1:
        st.markdown("### 🤖 ML Transaction Classifier")
        st.markdown("**TF-IDF + Logistic Regression** trained on 200+ labelled examples. Runs in <5ms — far faster than an LLM call. Corrects category before the decision agent runs.")
        clf = get_classifier()
        if clf is None:
            st.warning("Run: `pip install scikit-learn`")
        else:
            try:
                metrics = clf.evaluate()
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("CV Accuracy",   f"{metrics.get('cv_accuracy_mean',0):.1%}")
                c2.metric("Std Dev",       f"+-{metrics.get('cv_accuracy_std',0):.1%}")
                c3.metric("Training Size", metrics.get('n_training',0))
                c4.metric("Categories",    metrics.get('n_classes',0))
            except Exception as e:
                st.warning(f"Metrics error: {e}")

            st.markdown("---")
            st.markdown("#### Try the Classifier")
            col1,col2 = st.columns(2)
            test_desc    = col1.text_input("Description", placeholder="Netflix monthly subscription")
            test_merchant= col2.text_input("Merchant",    placeholder="Netflix")
            if st.button("🔍 Classify"):
                if test_desc:
                    try:
                        top3 = clf.predict_top3(test_desc, test_merchant)
                        for i,(cat,conf) in enumerate(top3):
                            color = "#00d4aa" if i==0 else ("#6c63ff" if i==1 else "#64748b")
                            label = "Top prediction" if i==0 else f"#{i+1}"
                            st.markdown(f"""
                            <div style="background:#1e293b;border-radius:10px;padding:14px 18px;
                                        margin-bottom:8px;border-left:3px solid {color}">
                                <span style="color:{color};font-weight:700">{label}</span>
                                <span style="color:#e2e8f0;font-size:16px;margin-left:12px">{cat.capitalize()}</span>
                                <span style="color:#64748b;font-size:13px;margin-left:8px">{conf:.1%} confidence</span>
                                <div style="height:6px;background:#0f172a;border-radius:99px;margin-top:8px">
                                    <div style="height:100%;width:{conf*100:.0f}%;background:{color};border-radius:99px"></div>
                                </div>
                            </div>""", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error: {e}")

            st.markdown("---")
            st.markdown("#### Batch Test")
            test_cases = [("Netflix subscription","Netflix"),("Swiggy food delivery","Swiggy"),
                          ("Electricity bill","TSECL"),("Udemy Python course","Udemy"),
                          ("Uber cab ride","Uber"),("Amazon purchase","Amazon"),
                          ("Doctor consultation","Apollo"),("Flight ticket","IndiGo")]
            if st.button("Run Batch Test"):
                results = []
                for desc,merch in test_cases:
                    cat,conf = clf.predict(desc,merch)
                    results.append({"Description":desc,"Merchant":merch,"Predicted":cat,"Confidence":f"{conf:.0%}"})
                st.dataframe(pd.DataFrame(results),use_container_width=True,hide_index=True)

    with tab2:
        st.markdown("### 🧩 ReAct Reasoning Engine")
        st.markdown("**Reason + Act** pattern: the agent thinks step by step, calls tools (check budget, retrieve similar decisions, check merchant history), then decides. Every step is logged for full explainability.")
        col1,col2 = st.columns(2)
        r_desc     = col1.text_input("Description",  placeholder="Netflix subscription renewal", key="rd")
        r_merchant = col2.text_input("Merchant",     placeholder="Netflix", key="rm")
        col3,col4 = st.columns(2)
        r_amount   = col3.number_input("Amount (Rs.)", min_value=0.0, value=649.0, step=10.0)
        r_category = col4.selectbox("Category", ["subscriptions","food","utilities","health","travel","entertainment","shopping","education","other"])
        if st.button("🚀 Run ReAct Agent"):
            if not r_desc:
                st.warning("Enter a description.")
            else:
                with st.spinner("Running ReAct reasoning..."):
                    try:
                        from tools.vector_memory import VectorMemory
                        from core.react_agent import ReActAgent
                        from models.transaction import Transaction
                        vmem  = get_vector_memory() or VectorMemory()
                        agent = ReActAgent(budget_tool, vmem, storage)
                        txn   = Transaction(description=r_desc,amount=r_amount,category=r_category,merchant=r_merchant,importance="medium")
                        decision,reasoning,confidence,steps = agent.decide(txn)
                        color = {"pay":"#00d4aa","remind":"#ffb347","ignore":"#64748b"}.get(decision,"#6c63ff")
                        st.markdown(f"""
                        <div style="background:#1e293b;border-radius:14px;padding:20px 24px;
                                    border:2px solid {color};margin-bottom:20px">
                            <div style="font-size:22px;font-weight:700;color:{color}">Decision: {decision.upper()}</div>
                            <div style="color:#e2e8f0;margin-top:6px">{reasoning}</div>
                            <div style="color:#64748b;font-size:13px;margin-top:4px">Confidence: {confidence:.0%} · {len(steps)} reasoning steps</div>
                        </div>""", unsafe_allow_html=True)
                        if steps:
                            st.markdown("#### Reasoning Steps")
                            for i,step in enumerate(steps,1):
                                with st.expander(f"Step {i}: {step.action}", expanded=(i==1)):
                                    st.markdown(f"""
                                    <div style="background:#0f172a;border-radius:8px;padding:12px;margin-bottom:6px;border-left:3px solid #c084fc">
                                        <span style="color:#c084fc;font-weight:600;font-size:11px">THOUGHT</span><br>
                                        <span style="color:#e2e8f0">{step.thought}</span></div>
                                    <div style="background:#0f172a;border-radius:8px;padding:12px;margin-bottom:6px;border-left:3px solid #4da6ff">
                                        <span style="color:#4da6ff;font-weight:600;font-size:11px">ACTION</span><br>
                                        <code style="color:#4da6ff">{step.action}</code></div>
                                    <div style="background:#0f172a;border-radius:8px;padding:12px;border-left:3px solid #00d4aa">
                                        <span style="color:#00d4aa;font-weight:600;font-size:11px">OBSERVE</span><br>
                                        <span style="color:#e2e8f0">{step.observation}</span></div>
                                    """, unsafe_allow_html=True)
                        else:
                            st.info("No reasoning steps (LLM unavailable — used rule-based fallback).")
                    except Exception as e:
                        st.error(f"ReAct error: {e}")

    with tab3:
        st.markdown("### 🗄️ Vector Memory (RAG)")
        st.markdown("Every decision is embedded and stored in **ChromaDB**. New transactions retrieve semantically similar past decisions via cosine similarity — giving the LLM richer context. Same architecture as production RAG systems.")
        vmem = get_vector_memory()
        if vmem is None:
            st.warning("Run: `pip install chromadb`")
        else:
            stats = vmem.get_stats()
            c1,c2,c3 = st.columns(3)
            c1.metric("Backend", stats["backend"])
            c2.metric("Stored Decisions", stats["total_docs"])
            c3.metric("Storage", "Local ChromaDB")
            st.markdown("---")
            search_desc = st.text_input("Search similar past decisions", placeholder="Netflix subscription payment")
            if st.button("🔍 Search"):
                if search_desc:
                    from models.transaction import Transaction
                    t = Transaction(description=search_desc,amount=0,category="other",merchant="")
                    result = vmem.retrieve_similar(t,k=5)
                    st.code(result)

    with tab4:
        st.markdown("### 📊 Evaluation Suite")
        st.markdown("Measures classifier accuracy, extraction quality, and component latency. Run after every code change to catch regressions.")
        run_quick = st.checkbox("Quick mode (classifier + regression only)", value=True)
        if st.button("▶️ Run Eval Suite"):
            with st.spinner("Running..."):
                try:
                    from eval.eval_suite import eval_regression, eval_classifier, eval_extraction
                    results = [eval_regression(), eval_classifier(), eval_extraction()]
                    data = [{"Suite":r.name,"Passed":r.passed,"Failed":r.failed,"Accuracy":f"{r.accuracy:.1%}","Status":"✅" if r.failed==0 else "❌"} for r in results]
                    st.dataframe(pd.DataFrame(data),use_container_width=True,hide_index=True)
                    fig = go.Figure(data=[go.Bar(
                        x=[r["Suite"] for r in data],
                        y=[float(r["Accuracy"].strip("%"))/100 for r in data],
                        marker_color=["#00d4aa" if r["Status"]=="✅" else "#ff4d6d" for r in data],
                        text=[r["Accuracy"] for r in data], textposition="outside")])
                    fig.update_layout(title="Accuracy by Suite",yaxis=dict(range=[0,1.15],tickformat=".0%"),
                        paper_bgcolor="#1e293b",plot_bgcolor="#1e293b",font_color="#e2e8f0")
                    st.plotly_chart(fig,use_container_width=True)
                    if all(r.failed==0 for r in results): st.success("🎉 All tests passed!")
                except Exception as e:
                    st.error(f"Eval error: {e}")

# ── Memory ────────────────────────────────────────────────────────────────────
elif page == "🧠 Memory":
    show_demo_banner()
    st.title("🧠 Agent Memory")
    trusted = storage.load_memory("trusted_merchants",[])
    ignored = storage.load_memory("ignored_merchants",[])
    prios   = storage.load_memory("category_priorities",{})
    c1,c2 = st.columns(2)
    c1.markdown("### ✅ Trusted Merchants")
    c1.write(trusted or "None yet")
    c2.markdown("### 🚫 Ignored Merchants")
    c2.write(ignored or "None yet")
    if prios:
        fig = px.bar(x=list(prios.keys()),y=list(prios.values()),
            labels={"x":"Category","y":"Priority"},color=list(prios.values()),color_continuous_scale="Purples")
        fig.update_layout(paper_bgcolor="#1e293b",plot_bgcolor="#1e293b",font_color="#e2e8f0")
        st.plotly_chart(fig,use_container_width=True)
    if st.button("🔄 Run Learning Pass"):
        from agents.memory_agent import MemoryAgent
        m = MemoryAgent(storage)
        st.success(m.learn_from_history(m.load()))
        st.rerun()
