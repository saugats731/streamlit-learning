import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import io

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(page_title="Fund Dashboard", page_icon="📈", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #e6edf3; }
    section[data-testid="stSidebar"] { background-color: #161b22; }
    .kpi-card {
        background: linear-gradient(135deg, #1f2937, #111827);
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 18px 20px;
        text-align: center;
    }
    .kpi-label { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 1.4px; margin-bottom: 6px; }
    .kpi-value { font-size: 28px; font-weight: 700; color: #f0f6fc; }
    .kpi-pos   { font-size: 12px; color: #3fb950; margin-top: 4px; }
    .kpi-neg   { font-size: 12px; color: #f85149; margin-top: 4px; }
    .section-hdr {
        font-size: 12px; font-weight: 600; color: #58a6ff;
        text-transform: uppercase; letter-spacing: 2px;
        margin: 24px 0 10px; border-left: 3px solid #58a6ff; padding-left: 10px;
    }
    #MainMenu{visibility:hidden;} footer{visibility:hidden;} header{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PLOTLY HELPERS
# ─────────────────────────────────────────────
BG = "#161b22"; PAPER = "#0d1117"; FC = "#8b949e"
C1, C2, CB = "#58a6ff", "#3fb950", "#f0883e"

def base(title=""):
    return dict(
        title=dict(text=title, font=dict(color=FC, size=12), x=0.01),
        plot_bgcolor=BG, paper_bgcolor=PAPER,
        font=dict(color=FC, size=11),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=FC)),
        xaxis=dict(showgrid=False, color=FC),
        yaxis=dict(showgrid=True, gridcolor="#21262d", color=FC),
    )

# ─────────────────────────────────────────────
# SIDEBAR — FILE UPLOAD
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 Fund Dashboard")
    st.markdown("---")
    uploaded = st.file_uploader("Upload your Excel file", type=["xlsx"])
    st.markdown("---")
    st.markdown("**Expected columns:**")
    st.markdown("`Date, ShareClass1, ShareClass2,`\n`Benchmark, SC1_Return, SC2_Return,`\n`Benchmark_Return`")
    st.markdown("---")
    st.markdown("*Download the template below to get started.*")

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
@st.cache_data
def load_data(file_bytes):
    df = pd.read_excel(io.BytesIO(file_bytes), header=1)   # row 2 = real headers
    df.columns = df.columns.str.strip()
    # Rename last "Benchmark" column to Benchmark_Return if needed
    cols = list(df.columns)
    if cols.count("Benchmark") == 2:
        idx = [i for i,c in enumerate(cols) if c=="Benchmark"]
        cols[idx[1]] = "Benchmark_Return"
        df.columns = cols
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
    df = df.sort_values("Date").reset_index(drop=True)
    # Ensure returns are decimals (if someone enters 2.41 instead of 0.0241)
    for col in ["SC1_Return","SC2_Return","Benchmark_Return"]:
        if col in df.columns and df[col].abs().max() > 1:
            df[col] = df[col] / 100
    return df

if uploaded:
    df = load_data(uploaded.read())
else:
    # ── Demo data so the dashboard renders without upload
    dates = pd.date_range("2019-12-31", periods=25, freq="ME")
    np.random.seed(7)
    nav1 = 150.2 * np.cumprod(np.concatenate([[1], 1 + np.random.normal(0.008,0.03,24)]))
    nav2 = 320.0 * np.cumprod(np.concatenate([[1], 1 + np.random.normal(0.006,0.025,24)]))
    bmk  = 1020.32 * np.cumprod(np.concatenate([[1], 1 + np.random.normal(0.005,0.035,24)]))
    r1 = np.concatenate([[0], np.diff(nav1)/nav1[:-1]])
    r2 = np.concatenate([[0], np.diff(nav2)/nav2[:-1]])
    rb = np.concatenate([[0], np.diff(bmk)/bmk[:-1]])
    df = pd.DataFrame({"Date":dates,"ShareClass1":nav1,"ShareClass2":nav2,"Benchmark":bmk,
                       "SC1_Return":r1,"SC2_Return":r2,"Benchmark_Return":rb})
    st.info("📂 No file uploaded — showing demo data. Upload your Excel file in the sidebar.")

# ─────────────────────────────────────────────
# SIDEBAR FILTERS (after data loaded)
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    min_d, max_d = df["Date"].min(), df["Date"].max()
    date_range = st.date_input("Date range", [min_d, max_d], min_value=min_d, max_value=max_d)
    if len(date_range) == 2:
        df = df[(df["Date"] >= pd.Timestamp(date_range[0])) & (df["Date"] <= pd.Timestamp(date_range[1]))]

# ─────────────────────────────────────────────
# COMPUTED METRICS
# ─────────────────────────────────────────────
def total_return(series): return (series.iloc[-1] / series.iloc[0] - 1) * 100
def ann_vol(rets):         return rets.std() * np.sqrt(12) * 100
def sharpe(rets):
    excess = rets.mean() * 12
    vol    = rets.std()  * np.sqrt(12)
    return excess / vol if vol else 0
def max_dd(nav):
    roll_max = nav.cummax()
    dd = (nav - roll_max) / roll_max
    return dd.min() * 100

tr1  = total_return(df["ShareClass1"])
tr2  = total_return(df["ShareClass2"])
trb  = total_return(df["Benchmark"])
vol1 = ann_vol(df["SC1_Return"].iloc[1:])
vol2 = ann_vol(df["SC2_Return"].iloc[1:])
sh1  = sharpe(df["SC1_Return"].iloc[1:])
sh2  = sharpe(df["SC2_Return"].iloc[1:])
dd1  = max_dd(df["ShareClass1"])
dd2  = max_dd(df["ShareClass2"])

# cumulative returns indexed to 100
df["SC1_Cum"] = (1 + df["SC1_Return"]).cumprod() * 100
df["SC2_Cum"] = (1 + df["SC2_Return"]).cumprod() * 100
df["BMK_Cum"] = (1 + df["Benchmark_Return"]).cumprod() * 100

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<h1 style='color:#f0f6fc;font-size:24px;margin-bottom:2px;'>📈 Fund Performance Dashboard</h1>
<p style='color:#8b949e;font-size:12px;margin-top:0;'>Monthly NAV & Returns Analysis</p>
<hr style='border-color:#30363d;margin-bottom:16px;'>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# KPI ROW
# ─────────────────────────────────────────────
k = st.columns(5)
def kpi(col, label, val, sub="", pos=True):
    sub_html = f'<div class="{"kpi-pos" if pos else "kpi-neg"}">{sub}</div>' if sub else ""
    col.markdown(f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
                 f'<div class="kpi-value">{val}</div>{sub_html}</div>', unsafe_allow_html=True)

kpi(k[0], "SC1 Total Return",  f"{tr1:+.1f}%",  f"vs BMK {tr1-trb:+.1f}%", tr1>=trb)
kpi(k[1], "SC2 Total Return",  f"{tr2:+.1f}%",  f"vs BMK {tr2-trb:+.1f}%", tr2>=trb)
kpi(k[2], "Benchmark Return",  f"{trb:+.1f}%",  None)
kpi(k[3], "SC1 Sharpe Ratio",  f"{sh1:.2f}",    f"SC2: {sh2:.2f}", sh1>=sh2)
kpi(k[4], "SC1 Max Drawdown",  f"{dd1:.1f}%",   f"SC2: {dd2:.1f}%", dd1>=dd2)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# ROW 1: Cumulative performance + NAV levels
# ─────────────────────────────────────────────
st.markdown('<div class="section-hdr">Cumulative Performance</div>', unsafe_allow_html=True)
c1, c2 = st.columns([3,2])

with c1:
    fig = go.Figure()
    for col, name, color, dash in [
        ("SC1_Cum","ShareClass1",C1,"solid"),
        ("SC2_Cum","ShareClass2",C2,"solid"),
        ("BMK_Cum","Benchmark",  CB,"dot"),
    ]:
        fig.add_trace(go.Scatter(x=df["Date"], y=df[col], name=name,
            line=dict(color=color, width=2, dash=dash)))
    fig.update_layout(**base("Growth of 100 (Base = Start Date)"))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    fig2 = go.Figure()
    for col, name, color in [("ShareClass1","SC1",C1),("ShareClass2","SC2",C2),("Benchmark","BMK",CB)]:
        fig2.add_trace(go.Scatter(x=df["Date"], y=df[col], name=name, line=dict(color=color, width=2)))
    fig2.update_layout(**base("NAV / Index Level"))
    st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────
# ROW 2: Monthly returns bar + Rolling vol + Drawdown
# ─────────────────────────────────────────────
st.markdown('<div class="section-hdr">Monthly Returns & Risk</div>', unsafe_allow_html=True)
c3, c4 = st.columns(2)

with c3:
    fig3 = go.Figure()
    dates_lbl = df["Date"].dt.strftime("%b %y")
    for col, name, color in [("SC1_Return","SC1",C1),("SC2_Return","SC2",C2),("Benchmark_Return","BMK",CB)]:
        fig3.add_trace(go.Bar(x=dates_lbl, y=df[col]*100, name=name,
            marker_color=color, opacity=0.8))
    fig3.update_layout(**base("Monthly Returns (%)"), barmode="group")
    fig3.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig3, use_container_width=True)

with c4:
    roll = 6
    df["Vol1"] = df["SC1_Return"].rolling(roll).std() * np.sqrt(12) * 100
    df["Vol2"] = df["SC2_Return"].rolling(roll).std() * np.sqrt(12) * 100
    df["VolB"] = df["Benchmark_Return"].rolling(roll).std() * np.sqrt(12) * 100
    fig4 = go.Figure()
    for col, name, color in [("Vol1","SC1",C1),("Vol2","SC2",C2),("VolB","BMK",CB)]:
        fig4.add_trace(go.Scatter(x=df["Date"], y=df[col], name=name, line=dict(color=color,width=2)))
    fig4.update_layout(**base(f"{roll}-Month Rolling Volatility (Ann. %)"))
    fig4.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig4, use_container_width=True)

# ─────────────────────────────────────────────
# ROW 3: Drawdown + Return distribution
# ─────────────────────────────────────────────
c5, c6 = st.columns(2)

with c5:
    for col, name in [("ShareClass1","SC1_DD"),("ShareClass2","SC2_DD"),("Benchmark","BMK_DD")]:
        rm = df[col].cummax(); df[name] = (df[col] - rm) / rm * 100
    fig5 = go.Figure()
    for col, name, color in [("SC1_DD","SC1",C1),("SC2_DD","SC2",C2),("BMK_DD","BMK",CB)]:
        fig5.add_trace(go.Scatter(x=df["Date"], y=df[col], name=name,
            fill="tozeroy", line=dict(color=color,width=1.5), fillcolor=color.replace("#","rgba(").rstrip(")")+",0.1)"))
    fig5.update_layout(**base("Drawdown from Peak (%)"))
    fig5.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig5, use_container_width=True)

with c6:
    fig6 = go.Figure()
    for col, name, color in [("SC1_Return","SC1",C1),("SC2_Return","SC2",C2)]:
        fig6.add_trace(go.Histogram(x=df[col].iloc[1:]*100, name=name,
            marker_color=color, opacity=0.7, nbinsx=15))
    fig6.update_layout(**base("Return Distribution (%)"), barmode="overlay")
    fig6.update_xaxes(ticksuffix="%")
    st.plotly_chart(fig6, use_container_width=True)

# ─────────────────────────────────────────────
# STATS TABLE
# ─────────────────────────────────────────────
st.markdown('<div class="section-hdr">Summary Statistics</div>', unsafe_allow_html=True)
stats = pd.DataFrame({
    "Metric": ["Total Return","Ann. Volatility","Sharpe Ratio","Max Drawdown","Best Month","Worst Month"],
    "ShareClass1": [f"{tr1:.2f}%", f"{vol1:.2f}%", f"{sh1:.2f}", f"{dd1:.2f}%",
                    f"{df['SC1_Return'].max()*100:.2f}%", f"{df['SC1_Return'].min()*100:.2f}%"],
    "ShareClass2": [f"{tr2:.2f}%", f"{vol2:.2f}%", f"{sh2:.2f}", f"{dd2:.2f}%",
                    f"{df['SC2_Return'].max()*100:.2f}%", f"{df['SC2_Return'].min()*100:.2f}%"],
    "Benchmark":   [f"{trb:.2f}%", f"{ann_vol(df['Benchmark_Return'].iloc[1:]):.2f}%",
                    f"{sharpe(df['Benchmark_Return'].iloc[1:]):.2f}", f"{max_dd(df['Benchmark']):.2f}%",
                    f"{df['Benchmark_Return'].max()*100:.2f}%", f"{df['Benchmark_Return'].min()*100:.2f}%"],
})
st.dataframe(stats.set_index("Metric"), use_container_width=True)

# ─────────────────────────────────────────────
# RAW DATA
# ─────────────────────────────────────────────
with st.expander("📋 View Raw Data"):
    disp = df[["Date","ShareClass1","ShareClass2","Benchmark","SC1_Return","SC2_Return","Benchmark_Return"]].copy()
    disp["Date"] = disp["Date"].dt.strftime("%d/%m/%Y")
    st.dataframe(disp, use_container_width=True)
