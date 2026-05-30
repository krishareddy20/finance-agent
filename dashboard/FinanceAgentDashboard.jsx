import { useState, useEffect, useRef } from "react";
import { AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadialBarChart, RadialBar } from "recharts";

const COLORS = {
  bg: "#0a0a0f",
  surface: "#111118",
  card: "#16161f",
  border: "#1e1e2e",
  accent: "#6c63ff",
  accentGlow: "rgba(108,99,255,0.15)",
  green: "#00d4aa",
  greenGlow: "rgba(0,212,170,0.12)",
  red: "#ff4d6d",
  amber: "#ffb347",
  blue: "#4da6ff",
  purple: "#c084fc",
  text: "#e2e8f0",
  muted: "#64748b",
  dim: "#334155",
};

const budgetData = [
  { category: "Food", spent: 6200, limit: 8000, color: COLORS.green },
  { category: "Shopping", spent: 2800, limit: 3000, color: COLORS.amber },
  { category: "Travel", spent: 4100, limit: 5000, color: COLORS.blue },
  { category: "Education", spent: 3200, limit: 5000, color: COLORS.purple },
  { category: "Health", spent: 900, limit: 2000, color: COLORS.green },
  { category: "Subscriptions", spent: 850, limit: 1000, color: COLORS.red },
  { category: "Utilities", spent: 2100, limit: 3000, color: COLORS.accent },
  { category: "Entertainment", spent: 1200, limit: 2000, color: COLORS.amber },
];

const spendingTrend = [
  { month: "Oct", amount: 18200, savings: 4800 },
  { month: "Nov", amount: 21500, savings: 3200 },
  { month: "Dec", amount: 26800, savings: 1500 },
  { month: "Jan", amount: 19400, savings: 5200 },
  { month: "Feb", amount: 17800, savings: 6100 },
  { month: "Mar", amount: 22100, savings: 4100 },
  { month: "Apr", amount: 15300, savings: 8200 },
  { month: "May", amount: 21350, savings: 5850 },
];

const transactions = [
  { id: 1, desc: "Swiggy Order", merchant: "Swiggy", amount: 480, category: "Food", status: "paid", date: "May 23", source: "sms", icon: "🍔" },
  { id: 2, desc: "Netflix Subscription", merchant: "Netflix", amount: 649, category: "Subscriptions", status: "paid", date: "May 22", source: "email", icon: "🎬" },
  { id: 3, desc: "Udemy Python Course", merchant: "Udemy", amount: 499, category: "Education", status: "reminded", date: "May 21", source: "email", icon: "📚" },
  { id: 4, desc: "Amazon Purchase", merchant: "Amazon", amount: 1299, category: "Shopping", status: "paid", date: "May 20", source: "sms", icon: "📦" },
  { id: 5, desc: "Electricity Bill", merchant: "TSECL", amount: 1840, category: "Utilities", status: "paid", date: "May 19", source: "email", icon: "⚡" },
  { id: 6, desc: "Gym Membership", merchant: "Cult.fit", amount: 999, category: "Health", status: "ignored", date: "May 18", source: "email", icon: "💪" },
  { id: 7, desc: "Uber Ride", merchant: "Uber", amount: 220, category: "Travel", status: "paid", date: "May 17", source: "sms", icon: "🚗" },
  { id: 8, desc: "Zomato Gold", merchant: "Zomato", amount: 299, category: "Food", status: "paid", date: "May 16", source: "email", icon: "🥘" },
];

const pieData = budgetData.map(b => ({ name: b.category, value: b.spent, color: b.color }));

const aiInsights = [
  { icon: "⚠️", text: "Subscriptions at 85% of budget — Netflix renewal due in 3 days", type: "warning" },
  { icon: "✅", text: "Health spending well within limits — ₹1,100 remaining this month", type: "success" },
  { icon: "💡", text: "You saved ₹5,850 this month — 21% more than last month!", type: "info" },
  { icon: "🎯", text: "Shopping near limit. Consider delaying Amazon wishlist purchases", type: "warning" },
];

const statCards = [
  { label: "Total Spent", value: "₹21,350", sub: "this month", delta: "+8.2%", up: false, color: COLORS.accent },
  { label: "Total Saved", value: "₹5,850", sub: "this month", delta: "+42%", up: true, color: COLORS.green },
  { label: "Transactions", value: "47", sub: "this month", delta: "+12", up: true, color: COLORS.blue },
  { label: "Avg/Day", value: "₹689", sub: "daily spend", delta: "-₹48", up: true, color: COLORS.purple },
];

function AnimatedNumber({ target, prefix = "", suffix = "" }) {
  const [current, setCurrent] = useState(0);
  const numTarget = parseInt(target.replace(/[^0-9]/g, "")) || 0;
  useEffect(() => {
    let start = 0;
    const step = Math.ceil(numTarget / 40);
    const timer = setInterval(() => {
      start += step;
      if (start >= numTarget) { setCurrent(numTarget); clearInterval(timer); }
      else setCurrent(start);
    }, 30);
    return () => clearInterval(timer);
  }, [numTarget]);
  return <span>{prefix}{current.toLocaleString()}{suffix}</span>;
}

function BudgetBar({ item, index }) {
  const [width, setWidth] = useState(0);
  const pct = Math.min((item.spent / item.limit) * 100, 100);
  useEffect(() => {
    const t = setTimeout(() => setWidth(pct), 200 + index * 80);
    return () => clearTimeout(t);
  }, [pct, index]);
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
        <span style={{ fontSize: 13, color: COLORS.text, fontWeight: 500 }}>{item.category}</span>
        <span style={{ fontSize: 12, color: pct > 85 ? COLORS.red : COLORS.muted }}>
          ₹{item.spent.toLocaleString()} / ₹{item.limit.toLocaleString()}
        </span>
      </div>
      <div style={{ height: 6, background: COLORS.border, borderRadius: 99, overflow: "hidden" }}>
        <div style={{
          height: "100%", width: `${width}%`, borderRadius: 99,
          background: pct > 85 ? COLORS.red : pct > 70 ? COLORS.amber : item.color,
          transition: "width 0.8s cubic-bezier(.4,0,.2,1)",
          boxShadow: `0 0 8px ${pct > 85 ? COLORS.red : item.color}66`,
        }} />
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  const styles = {
    paid:     { bg: "rgba(0,212,170,0.12)", color: COLORS.green, label: "Paid" },
    reminded: { bg: "rgba(255,179,71,0.12)", color: COLORS.amber, label: "Reminded" },
    ignored:  { bg: "rgba(100,116,139,0.12)", color: COLORS.muted, label: "Ignored" },
    pending:  { bg: "rgba(108,99,255,0.12)", color: COLORS.accent, label: "Pending" },
  };
  const s = styles[status] || styles.pending;
  return (
    <span style={{
      padding: "3px 10px", borderRadius: 99, fontSize: 11, fontWeight: 600,
      background: s.bg, color: s.color, letterSpacing: "0.04em",
    }}>{s.label}</span>
  );
}

function NavItem({ icon, label, active, onClick }) {
  return (
    <button onClick={onClick} style={{
      display: "flex", alignItems: "center", gap: 10, width: "100%",
      padding: "10px 14px", borderRadius: 10, border: "none", cursor: "pointer",
      background: active ? COLORS.accentGlow : "transparent",
      color: active ? COLORS.accent : COLORS.muted,
      fontSize: 13, fontWeight: active ? 600 : 400,
      transition: "all 0.2s", textAlign: "left",
      borderLeft: active ? `2px solid ${COLORS.accent}` : "2px solid transparent",
    }}>
      <span style={{ fontSize: 16 }}>{icon}</span>
      {label}
    </button>
  );
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: COLORS.card, border: `1px solid ${COLORS.border}`,
      borderRadius: 10, padding: "10px 14px", fontSize: 12, color: COLORS.text,
    }}>
      <p style={{ margin: "0 0 6px", color: COLORS.muted, fontWeight: 600 }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ margin: "2px 0", color: p.color }}>
          {p.name}: ₹{p.value.toLocaleString()}
        </p>
      ))}
    </div>
  );
};

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [filterStatus, setFilterStatus] = useState("all");
  const [pulse, setPulse] = useState(false);

  useEffect(() => {
    const t = setInterval(() => setPulse(p => !p), 2000);
    return () => clearInterval(t);
  }, []);

  const filtered = filterStatus === "all" ? transactions : transactions.filter(t => t.status === filterStatus);
  const totalSpent = budgetData.reduce((s, b) => s + b.spent, 0);
  const totalBudget = budgetData.reduce((s, b) => s + b.limit, 0);

  return (
    <div style={{
      display: "flex", minHeight: "100vh", background: COLORS.bg,
      fontFamily: "'Inter', -apple-system, sans-serif", color: COLORS.text,
    }}>
      {/* Sidebar */}
      <div style={{
        width: 220, background: COLORS.surface, borderRight: `1px solid ${COLORS.border}`,
        padding: "24px 12px", display: "flex", flexDirection: "column", flexShrink: 0,
      }}>
        {/* Logo */}
        <div style={{ padding: "0 8px 28px", borderBottom: `1px solid ${COLORS.border}`, marginBottom: 20 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{
              width: 34, height: 34, borderRadius: 10,
              background: `linear-gradient(135deg, ${COLORS.accent}, ${COLORS.purple})`,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 16, boxShadow: `0 4px 12px ${COLORS.accentGlow}`,
            }}>💳</div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: COLORS.text }}>FinanceOS</div>
              <div style={{ fontSize: 10, color: COLORS.muted }}>Personal Agent</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 2 }}>
          <NavItem icon="📊" label="Dashboard" active={page === "dashboard"} onClick={() => setPage("dashboard")} />
          <NavItem icon="📋" label="Transactions" active={page === "transactions"} onClick={() => setPage("transactions")} />
          <NavItem icon="💰" label="Budget" active={page === "budget"} onClick={() => setPage("budget")} />
          <NavItem icon="🧠" label="AI Insights" active={page === "insights"} onClick={() => setPage("insights")} />
          <NavItem icon="📈" label="Reports" active={page === "reports"} onClick={() => setPage("reports")} />
        </div>

        {/* Agent status */}
        <div style={{
          padding: "12px 14px", borderRadius: 12,
          background: COLORS.greenGlow, border: `1px solid ${COLORS.green}33`,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
            <div style={{
              width: 7, height: 7, borderRadius: "50%", background: COLORS.green,
              boxShadow: `0 0 ${pulse ? "8px" : "4px"} ${COLORS.green}`,
              transition: "box-shadow 0.5s",
            }} />
            <span style={{ fontSize: 12, fontWeight: 600, color: COLORS.green }}>Agent Active</span>
          </div>
          <div style={{ fontSize: 11, color: COLORS.muted }}>Last scan: 2 min ago</div>
          <div style={{ fontSize: 11, color: COLORS.muted }}>47 emails processed</div>
        </div>
      </div>

      {/* Main content */}
      <div style={{ flex: 1, overflowY: "auto", padding: 28 }}>

        {/* DASHBOARD */}
        {page === "dashboard" && (
          <div>
            {/* Header */}
            <div style={{ marginBottom: 28 }}>
              <h1 style={{ fontSize: 24, fontWeight: 700, margin: "0 0 4px", color: COLORS.text }}>
                Good morning, Krisha 👋
              </h1>
              <p style={{ fontSize: 14, color: COLORS.muted, margin: 0 }}>
                May 2026 · ₹{(totalBudget - totalSpent).toLocaleString()} remaining across all categories
              </p>
            </div>

            {/* Stat cards */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 24 }}>
              {statCards.map((s, i) => (
                <div key={i} style={{
                  background: COLORS.card, border: `1px solid ${COLORS.border}`,
                  borderRadius: 16, padding: "18px 20px",
                  borderTop: `2px solid ${s.color}`,
                }}>
                  <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 8, fontWeight: 500 }}>{s.label}</div>
                  <div style={{ fontSize: 26, fontWeight: 700, color: COLORS.text, marginBottom: 6 }}>
                    {s.value.startsWith("₹") ? "₹" : ""}
                    <AnimatedNumber target={s.value} />
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{
                      fontSize: 11, fontWeight: 600, padding: "2px 7px", borderRadius: 99,
                      background: s.up ? "rgba(0,212,170,0.12)" : "rgba(255,77,109,0.12)",
                      color: s.up ? COLORS.green : COLORS.red,
                    }}>{s.delta}</span>
                    <span style={{ fontSize: 11, color: COLORS.muted }}>{s.sub}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Charts row */}
            <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 20, marginBottom: 24 }}>
              {/* Area chart */}
              <div style={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: "20px 24px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: COLORS.text }}>Spending Trend</div>
                    <div style={{ fontSize: 12, color: COLORS.muted }}>Last 8 months</div>
                  </div>
                  <div style={{ display: "flex", gap: 16, fontSize: 12 }}>
                    <span style={{ color: COLORS.accent }}>● Spent</span>
                    <span style={{ color: COLORS.green }}>● Saved</span>
                  </div>
                </div>
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={spendingTrend}>
                    <defs>
                      <linearGradient id="spentGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={COLORS.accent} stopOpacity={0.3} />
                        <stop offset="95%" stopColor={COLORS.accent} stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="savedGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={COLORS.green} stopOpacity={0.3} />
                        <stop offset="95%" stopColor={COLORS.green} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
                    <XAxis dataKey="month" tick={{ fill: COLORS.muted, fontSize: 12 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: COLORS.muted, fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} />
                    <Tooltip content={<CustomTooltip />} />
                    <Area type="monotone" dataKey="amount" name="Spent" stroke={COLORS.accent} strokeWidth={2} fill="url(#spentGrad)" />
                    <Area type="monotone" dataKey="savings" name="Saved" stroke={COLORS.green} strokeWidth={2} fill="url(#savedGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Pie chart */}
              <div style={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: "20px 24px" }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: COLORS.text, marginBottom: 4 }}>Spend by Category</div>
                <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 16 }}>May 2026</div>
                <ResponsiveContainer width="100%" height={160}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={75} paddingAngle={3} dataKey="value">
                      {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                    </Pie>
                    <Tooltip formatter={(v) => [`₹${v.toLocaleString()}`, ""]} contentStyle={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 8, fontSize: 12 }} />
                  </PieChart>
                </ResponsiveContainer>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "4px 12px", marginTop: 4 }}>
                  {pieData.slice(0, 4).map((d, i) => (
                    <span key={i} style={{ fontSize: 10, color: COLORS.muted, display: "flex", alignItems: "center", gap: 4 }}>
                      <span style={{ width: 6, height: 6, borderRadius: "50%", background: d.color, display: "inline-block" }} />
                      {d.name}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Recent transactions */}
            <div style={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: "20px 24px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: COLORS.text }}>Recent Transactions</div>
                <button onClick={() => setPage("transactions")} style={{
                  fontSize: 12, color: COLORS.accent, background: "none", border: "none", cursor: "pointer", fontWeight: 500,
                }}>View all →</button>
              </div>
              {transactions.slice(0, 4).map(t => (
                <div key={t.id} style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  padding: "10px 0", borderBottom: `1px solid ${COLORS.border}`,
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <div style={{
                      width: 38, height: 38, borderRadius: 10, background: COLORS.surface,
                      display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18,
                    }}>{t.icon}</div>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 500, color: COLORS.text }}>{t.desc}</div>
                      <div style={{ fontSize: 11, color: COLORS.muted }}>{t.date} · {t.source}</div>
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: 14, fontWeight: 600, color: COLORS.text }}>₹{t.amount.toLocaleString()}</div>
                    <StatusBadge status={t.status} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TRANSACTIONS PAGE */}
        {page === "transactions" && (
          <div>
            <div style={{ marginBottom: 24 }}>
              <h1 style={{ fontSize: 22, fontWeight: 700, margin: "0 0 4px" }}>Transactions</h1>
              <p style={{ fontSize: 14, color: COLORS.muted, margin: 0 }}>All financial events detected by the agent</p>
            </div>
            <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
              {["all", "paid", "reminded", "ignored"].map(s => (
                <button key={s} onClick={() => setFilterStatus(s)} style={{
                  padding: "7px 16px", borderRadius: 99, border: `1px solid ${filterStatus === s ? COLORS.accent : COLORS.border}`,
                  background: filterStatus === s ? COLORS.accentGlow : "transparent",
                  color: filterStatus === s ? COLORS.accent : COLORS.muted,
                  fontSize: 12, fontWeight: 500, cursor: "pointer", textTransform: "capitalize",
                }}>{s}</button>
              ))}
            </div>
            <div style={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 16, overflow: "hidden" }}>
              <div style={{
                display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr",
                padding: "12px 20px", borderBottom: `1px solid ${COLORS.border}`,
                fontSize: 11, fontWeight: 600, color: COLORS.muted, letterSpacing: "0.05em", textTransform: "uppercase",
              }}>
                <span>Transaction</span><span>Category</span><span>Source</span><span>Amount</span><span>Status</span>
              </div>
              {filtered.map((t, i) => (
                <div key={t.id} style={{
                  display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr",
                  padding: "14px 20px", borderBottom: i < filtered.length - 1 ? `1px solid ${COLORS.border}` : "none",
                  alignItems: "center", transition: "background 0.15s",
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <span style={{ fontSize: 20 }}>{t.icon}</span>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 500, color: COLORS.text }}>{t.desc}</div>
                      <div style={{ fontSize: 11, color: COLORS.muted }}>{t.merchant} · {t.date}</div>
                    </div>
                  </div>
                  <span style={{ fontSize: 12, color: COLORS.muted }}>{t.category}</span>
                  <span style={{
                    fontSize: 11, padding: "3px 8px", borderRadius: 99,
                    background: t.source === "email" ? "rgba(108,99,255,0.1)" : "rgba(0,212,170,0.1)",
                    color: t.source === "email" ? COLORS.accent : COLORS.green,
                    display: "inline-block", width: "fit-content",
                  }}>{t.source}</span>
                  <span style={{ fontSize: 14, fontWeight: 600, color: COLORS.text }}>₹{t.amount.toLocaleString()}</span>
                  <StatusBadge status={t.status} />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* BUDGET PAGE */}
        {page === "budget" && (
          <div>
            <div style={{ marginBottom: 24 }}>
              <h1 style={{ fontSize: 22, fontWeight: 700, margin: "0 0 4px" }}>Budget Overview</h1>
              <p style={{ fontSize: 14, color: COLORS.muted, margin: 0 }}>Monthly limits vs actual spending — May 2026</p>
            </div>

            {/* Summary bar */}
            <div style={{
              background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 16,
              padding: "20px 24px", marginBottom: 20, display: "flex", gap: 32, alignItems: "center",
            }}>
              <div>
                <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 4 }}>Total Budget</div>
                <div style={{ fontSize: 28, fontWeight: 700, color: COLORS.text }}>₹{totalBudget.toLocaleString()}</div>
              </div>
              <div style={{ width: 1, height: 48, background: COLORS.border }} />
              <div>
                <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 4 }}>Spent</div>
                <div style={{ fontSize: 28, fontWeight: 700, color: COLORS.accent }}>₹{totalSpent.toLocaleString()}</div>
              </div>
              <div style={{ width: 1, height: 48, background: COLORS.border }} />
              <div>
                <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 4 }}>Remaining</div>
                <div style={{ fontSize: 28, fontWeight: 700, color: COLORS.green }}>₹{(totalBudget - totalSpent).toLocaleString()}</div>
              </div>
              <div style={{ flex: 1, marginLeft: 16 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                  <span style={{ fontSize: 12, color: COLORS.muted }}>Overall utilisation</span>
                  <span style={{ fontSize: 12, fontWeight: 600, color: COLORS.text }}>{Math.round((totalSpent / totalBudget) * 100)}%</span>
                </div>
                <div style={{ height: 8, background: COLORS.border, borderRadius: 99, overflow: "hidden" }}>
                  <div style={{
                    height: "100%", width: `${(totalSpent / totalBudget) * 100}%`,
                    background: `linear-gradient(90deg, ${COLORS.accent}, ${COLORS.purple})`,
                    borderRadius: 99,
                  }} />
                </div>
              </div>
            </div>

            {/* Bar chart */}
            <div style={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: "20px 24px", marginBottom: 20 }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: COLORS.text, marginBottom: 20 }}>Category Breakdown</div>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={budgetData} barSize={18} barGap={4}>
                  <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} vertical={false} />
                  <XAxis dataKey="category" tick={{ fill: COLORS.muted, fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: COLORS.muted, fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="limit" name="Budget" fill={COLORS.dim} radius={[4, 4, 0, 0]} />
                  <Bar dataKey="spent" name="Spent" radius={[4, 4, 0, 0]}>
                    {budgetData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Individual bars */}
            <div style={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: "20px 24px" }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: COLORS.text, marginBottom: 20 }}>Detailed Progress</div>
              {budgetData.map((item, i) => <BudgetBar key={i} item={item} index={i} />)}
            </div>
          </div>
        )}

        {/* AI INSIGHTS */}
        {page === "insights" && (
          <div>
            <div style={{ marginBottom: 24 }}>
              <h1 style={{ fontSize: 22, fontWeight: 700, margin: "0 0 4px" }}>AI Insights</h1>
              <p style={{ fontSize: 14, color: COLORS.muted, margin: 0 }}>Powered by OpenRouter free LLM · Llama 3.1 8B</p>
            </div>

            {/* Alert cards */}
            <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 24 }}>
              {aiInsights.map((ins, i) => {
                const colors = { warning: COLORS.amber, success: COLORS.green, info: COLORS.blue };
                const bgs = { warning: "rgba(255,179,71,0.08)", success: "rgba(0,212,170,0.08)", info: "rgba(77,166,255,0.08)" };
                return (
                  <div key={i} style={{
                    background: bgs[ins.type], border: `1px solid ${colors[ins.type]}33`,
                    borderRadius: 14, padding: "16px 20px", display: "flex", alignItems: "center", gap: 14,
                    borderLeft: `3px solid ${colors[ins.type]}`,
                  }}>
                    <span style={{ fontSize: 22 }}>{ins.icon}</span>
                    <span style={{ fontSize: 14, color: COLORS.text }}>{ins.text}</span>
                  </div>
                );
              })}
            </div>

            {/* Trusted / Ignored merchants */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
              <div style={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: "20px 24px" }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: COLORS.green, marginBottom: 16 }}>✅ Trusted Merchants</div>
                {["Swiggy", "Netflix", "Amazon", "TSECL", "Uber"].map(m => (
                  <div key={m} style={{
                    display: "flex", justifyContent: "space-between", alignItems: "center",
                    padding: "9px 0", borderBottom: `1px solid ${COLORS.border}`,
                  }}>
                    <span style={{ fontSize: 13, color: COLORS.text }}>{m}</span>
                    <span style={{ fontSize: 11, color: COLORS.green, background: "rgba(0,212,170,0.1)", padding: "2px 8px", borderRadius: 99 }}>Auto-pay</span>
                  </div>
                ))}
              </div>
              <div style={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: "20px 24px" }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: COLORS.muted, marginBottom: 16 }}>🚫 Ignored Merchants</div>
                {["Cult.fit", "MagicPin", "CouponDunia"].map(m => (
                  <div key={m} style={{
                    display: "flex", justifyContent: "space-between", alignItems: "center",
                    padding: "9px 0", borderBottom: `1px solid ${COLORS.border}`,
                  }}>
                    <span style={{ fontSize: 13, color: COLORS.text }}>{m}</span>
                    <span style={{ fontSize: 11, color: COLORS.muted, background: COLORS.border, padding: "2px 8px", borderRadius: 99 }}>Ignored</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* REPORTS */}
        {page === "reports" && (
          <div>
            <div style={{ marginBottom: 24 }}>
              <h1 style={{ fontSize: 22, fontWeight: 700, margin: "0 0 4px" }}>Reports</h1>
              <p style={{ fontSize: 14, color: COLORS.muted, margin: 0 }}>AI-generated spending analysis</p>
            </div>
            <div style={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: "28px 32px", marginBottom: 20 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
                <div style={{ width: 40, height: 40, borderRadius: 12, background: COLORS.accentGlow, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20 }}>🤖</div>
                <div>
                  <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.text }}>Monthly Report — May 2026</div>
                  <div style={{ fontSize: 12, color: COLORS.muted }}>Generated by Llama 3.1 8B via OpenRouter</div>
                </div>
              </div>
              <div style={{
                fontSize: 14, color: COLORS.text, lineHeight: 1.8,
                padding: 20, background: COLORS.surface, borderRadius: 12,
                borderLeft: `3px solid ${COLORS.accent}`,
              }}>
                <p style={{ margin: "0 0 12px" }}>
                  <strong style={{ color: COLORS.accent }}>Overall: On Track</strong> — You've spent ₹21,350 of your ₹32,000 monthly budget (67%), leaving ₹10,650 for the remaining 8 days.
                </p>
                <p style={{ margin: "0 0 12px" }}>
                  <strong style={{ color: COLORS.amber }}>Watch out:</strong> Subscriptions are at 85% already with a Netflix renewal approaching. Consider reviewing which subscriptions are actively used.
                </p>
                <p style={{ margin: "0 0 12px" }}>
                  <strong style={{ color: COLORS.green }}>Good news:</strong> Health and utilities are well under budget — you're ₹1,100 under on health spending.
                </p>
                <p style={{ margin: 0 }}>
                  <strong style={{ color: COLORS.blue }}>Tip:</strong> At current pace, you'll save approximately ₹5,850 this month — 21% more than April. Reducing food delivery by 2 orders/week could save another ₹800.
                </p>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
              {[
                { label: "Best Month", value: "February", sub: "₹6,100 saved", icon: "🏆", color: COLORS.amber },
                { label: "Biggest Expense", value: "Food", sub: "₹6,200 this month", icon: "📍", color: COLORS.red },
                { label: "Avg Monthly Savings", value: "₹4,869", sub: "last 8 months", icon: "💰", color: COLORS.green },
              ].map((s, i) => (
                <div key={i} style={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: "20px 22px" }}>
                  <div style={{ fontSize: 24, marginBottom: 12 }}>{s.icon}</div>
                  <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 4 }}>{s.label}</div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: s.color, marginBottom: 2 }}>{s.value}</div>
                  <div style={{ fontSize: 12, color: COLORS.muted }}>{s.sub}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
