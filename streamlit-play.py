import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Sales Dashboard",
    page_icon="📊",
    layout="wide",
)

# ─────────────────────────────────────────────
# CUSTOM CSS — Power BI dark theme feel
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Background */
    .stApp { background-color: #1a1a2e; color: #e0e0e0; }

    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #16213e; }

    /* KPI cards */
    .kpi-card {
        background: linear-gradient(135deg, #0f3460, #16213e);
        border: 1px solid #e94560;
        border-radius: 12px;
        padding: 20px 24px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(233,69,96,0.15);
    }
    .kpi-label {
        font-size: 13px;
        color: #a0a0c0;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 32px;
        font-weight: 700;
        color: #ffffff;
    }
    .kpi-delta-pos { font-size: 13px; color: #00e396; margin-top: 4px; }
    .kpi-delta-neg { font-size: 13px; color: #e94560; margin-top: 4px; }

    /* Section headers */
    .section-header {
        font-size: 14px;
        font-weight: 600;
        color: #e94560;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin: 24px 0 12px 0;
        border-left: 3px solid #e94560;
        padding-left: 10px;
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# RANDOM DATA GENERATION
# ─────────────────────────────────────────────
np.random.seed(42)

regions    = ["North", "South", "East", "West", "Central"]
products   = ["Laptops", "Phones", "Tablets", "Monitors", "Accessories"]
months     = pd.date_range("2024-01-01", periods=12, freq="MS")
month_labels = [m.strftime("%b %Y") for m in months]

# Monthly revenue & profit
revenue = np.random.randint(120_000, 380_000, 12)
profit  = (revenue * np.random.uniform(0.18, 0.35, 12)).astype(int)
target  = np.random.randint(150_000, 350_000, 12)

df_monthly = pd.DataFrame({
    "Month": month_labels,
    "Revenue": revenue,
    "Profit": profit,
    "Target": target,
})

# Regional sales
df_region = pd.DataFrame({
    "Region": regions,
    "Sales": np.random.randint(200_000, 900_000, 5),
    "Customers": np.random.randint(500, 3000, 5),
})

# Product breakdown
df_product = pd.DataFrame({
    "Product": products,
    "Units": np.random.randint(300, 1500, 5),
    "Revenue": np.random.randint(50_000, 400_000, 5),
})

# Daily sales last 30 days
days = pd.date_range(end=datetime.today(), periods=30)
df_daily = pd.DataFrame({
    "Date": days,
    "Sales": np.random.randint(5000, 25000, 30),
})

# Top customers
customers = [f"Client {chr(65+i)}" for i in range(8)]
df_customers = pd.DataFrame({
    "Customer": customers,
    "Revenue": sorted(np.random.randint(20_000, 200_000, 8), reverse=True),
})

# ─────────────────────────────────────────────
# PLOTLY THEME
# ─────────────────────────────────────────────
CHART_BG   = "#16213e"
PAPER_BG   = "#16213e"
FONT_COLOR = "#c0c0d0"
ACCENT     = "#e94560"
COLORS     = ["#e94560", "#0f3460", "#533483", "#00e396", "#feb019"]

def base_layout(title=""):
    return dict(
        title=dict(text=title, font=dict(color=FONT_COLOR, size=13), x=0.01),
        plot_bgcolor=CHART_BG,
        paper_bgcolor=PAPER_BG,
        font=dict(color=FONT_COLOR, size=11),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=FONT_COLOR)),
    )

# ─────────────────────────────────────────────
# SIDEBAR — FILTERS
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Dashboard Filters")
    st.markdown("---")
    selected_regions = st.multiselect("Region", regions, default=regions)
    selected_products = st.multiselect("Product", products, default=products)
    date_range = st.slider("Month Range", 1, 12, (1, 12))
    st.markdown("---")
    st.markdown("**Data last refreshed:**")
    st.markdown(f"`{datetime.today().strftime('%d %b %Y, %H:%M')}`")

# Apply filters
df_monthly_f  = df_monthly.iloc[date_range[0]-1 : date_range[1]]
df_region_f   = df_region[df_region["Region"].isin(selected_regions)]
df_product_f  = df_product[df_product["Product"].isin(selected_products)]

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<h1 style='color:#ffffff; font-size:26px; margin-bottom:4px;'>
    📊 Sales Performance Dashboard
</h1>
<p style='color:#a0a0c0; font-size:13px; margin-top:0;'>
    FY 2024 · All figures in USD · Powered by Streamlit
</p>
<hr style='border-color:#e94560; margin-bottom:20px;'>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────
total_revenue  = df_monthly_f["Revenue"].sum()
total_profit   = df_monthly_f["Profit"].sum()
total_target   = df_monthly_f["Target"].sum()
avg_margin     = (total_profit / total_revenue * 100) if total_revenue else 0
vs_target      = ((total_revenue - total_target) / total_target * 100) if total_target else 0
total_customers = df_region_f["Customers"].sum()

k1, k2, k3, k4, k5 = st.columns(5)

def kpi(col, label, value, delta=None, positive=True):
    delta_html = ""
    if delta is not None:
        cls = "kpi-delta-pos" if positive else "kpi-delta-neg"
        arrow = "▲" if positive else "▼"
        delta_html = f'<div class="{cls}">{arrow} {delta}</div>'
    col.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>""", unsafe_allow_html=True)

kpi(k1, "Total Revenue",  f"${total_revenue:,.0f}",  f"{abs(vs_target):.1f}% vs target", vs_target >= 0)
kpi(k2, "Total Profit",   f"${total_profit:,.0f}",   f"{avg_margin:.1f}% margin", True)
kpi(k3, "Profit Margin",  f"{avg_margin:.1f}%",      None)
kpi(k4, "Total Customers",f"{total_customers:,}",    "+8.3% MoM", True)
kpi(k5, "Avg Monthly Rev",f"${total_revenue//max(len(df_monthly_f),1):,.0f}", None)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# ROW 1: Revenue vs Target line + Regional bar
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">Revenue & Regional Breakdown</div>', unsafe_allow_html=True)
c1, c2 = st.columns([3, 2])

with c1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_monthly_f["Month"], y=df_monthly_f["Revenue"],
        name="Revenue", line=dict(color="#e94560", width=3),
        fill="tozeroy", fillcolor="rgba(233,69,96,0.08)"
    ))
    fig.add_trace(go.Scatter(
        x=df_monthly_f["Month"], y=df_monthly_f["Target"],
        name="Target", line=dict(color="#feb019", width=2, dash="dot")
    ))
    fig.add_trace(go.Bar(
        x=df_monthly_f["Month"], y=df_monthly_f["Profit"],
        name="Profit", marker_color="#00e396", opacity=0.5
    ))
    fig.update_layout(**base_layout("Revenue vs Target vs Profit"))
    fig.update_xaxes(showgrid=False, tickangle=-30)
    fig.update_yaxes(showgrid=True, gridcolor="#2a2a4a")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    fig2 = px.bar(
        df_region_f.sort_values("Sales"), x="Sales", y="Region",
        orientation="h", color="Sales",
        color_continuous_scale=["#0f3460", "#e94560"],
        text_auto=".2s",
    )
    fig2.update_layout(**base_layout("Sales by Region"))
    fig2.update_traces(textfont_color=FONT_COLOR)
    fig2.update_coloraxes(showscale=False)
    st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────
# ROW 2: Product donut + Daily trend + Top customers
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">Product Mix · Daily Trend · Top Customers</div>', unsafe_allow_html=True)
c3, c4, c5 = st.columns([1.5, 2, 2])

with c3:
    fig3 = px.pie(
        df_product_f, names="Product", values="Revenue",
        hole=0.55, color_discrete_sequence=COLORS,
    )
    fig3.update_layout(**base_layout("Revenue by Product"))
    fig3.update_traces(textinfo="percent+label", textfont_size=11)
    st.plotly_chart(fig3, use_container_width=True)

with c4:
    fig4 = px.area(
        df_daily, x="Date", y="Sales",
        color_discrete_sequence=["#533483"],
    )
    fig4.update_traces(fill="tozeroy", fillcolor="rgba(83,52,131,0.3)", line=dict(color="#e94560"))
    fig4.update_layout(**base_layout("Daily Sales — Last 30 Days"))
    fig4.update_xaxes(showgrid=False)
    fig4.update_yaxes(showgrid=True, gridcolor="#2a2a4a")
    st.plotly_chart(fig4, use_container_width=True)

with c5:
    fig5 = px.bar(
        df_customers, x="Revenue", y="Customer",
        orientation="h", color="Revenue",
        color_continuous_scale=["#0f3460","#e94560"],
        text_auto=".2s",
    )
    fig5.update_layout(**base_layout("Top Customers by Revenue"))
    fig5.update_coloraxes(showscale=False)
    fig5.update_traces(textfont_color=FONT_COLOR)
    st.plotly_chart(fig5, use_container_width=True)

# ─────────────────────────────────────────────
# ROW 3: Scatter + Gauge
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">Efficiency & Target Attainment</div>', unsafe_allow_html=True)
c6, c7 = st.columns([2, 1])

with c6:
    fig6 = px.scatter(
        df_product_f, x="Units", y="Revenue", size="Revenue",
        color="Product", color_discrete_sequence=COLORS,
        text="Product",
    )
    fig6.update_traces(textposition="top center", textfont_size=10)
    fig6.update_layout(**base_layout("Units Sold vs Revenue by Product"))
    fig6.update_xaxes(showgrid=True, gridcolor="#2a2a4a")
    fig6.update_yaxes(showgrid=True, gridcolor="#2a2a4a")
    st.plotly_chart(fig6, use_container_width=True)

with c7:
    attainment = min((total_revenue / total_target * 100) if total_target else 0, 150)
    fig7 = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=attainment,
        number={"suffix": "%", "font": {"color": "#ffffff", "size": 40}},
        delta={"reference": 100, "increasing": {"color": "#00e396"}, "decreasing": {"color": "#e94560"}},
        gauge={
            "axis": {"range": [0, 150], "tickcolor": FONT_COLOR},
            "bar": {"color": "#e94560"},
            "bgcolor": "#0f3460",
            "steps": [
                {"range": [0, 80],  "color": "#1a1a2e"},
                {"range": [80, 100], "color": "#0f3460"},
                {"range": [100, 150], "color": "#16213e"},
            ],
            "threshold": {
                "line": {"color": "#00e396", "width": 3},
                "thickness": 0.8,
                "value": 100,
            },
        },
        title={"text": "Target Attainment", "font": {"color": FONT_COLOR, "size": 14}},
    ))
    fig7.update_layout(paper_bgcolor=PAPER_BG, font=dict(color=FONT_COLOR), margin=dict(l=20,r=20,t=60,b=20))
    st.plotly_chart(fig7, use_container_width=True)

# ─────────────────────────────────────────────
# RAW DATA TABLE (expandable)
# ─────────────────────────────────────────────
with st.expander("📋 View Raw Monthly Data"):
    st.dataframe(
        df_monthly_f.style.format({"Revenue": "${:,.0f}", "Profit": "${:,.0f}", "Target": "${:,.0f}"}),
        use_container_width=True,
    )
