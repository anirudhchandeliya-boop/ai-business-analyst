import streamlit as st
import pandas as pd
import numpy as np
import time
import io
import json
from datetime import datetime

# Optional libraries
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except Exception:
    PLOTLY_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.enums import TA_CENTER
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="AI Business Analyst - By Anirudh",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# STYLING
# =============================================================================
st.markdown("""
<style>
    .main { background: #f7f9fc; }
    .hero {
        padding: 1.5rem 2rem;
        border-radius: 18px;
        background: linear-gradient(135deg, #eef2ff, #f8fafc);
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    .hero h1 { margin-bottom: .25rem; }
    .small-muted { color: #64748b; font-size: .9rem; }
    .metric-card {
        padding: 1rem;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        background: white;
        box-shadow: 0 2px 10px rgba(15, 23, 42, .05);
    }
    .step-card {
        padding: .8rem;
        border-radius: 12px;
        border: 1px solid #dbeafe;
        background: #eff6ff;
        text-align: center;
    }
    .free-badge {
        display: inline-block;
        padding: .3rem .7rem;
        border-radius: 999px;
        background: #dcfce7;
        color: #166534;
        font-weight: 700;
        font-size: .85rem;
    }
    div[data-testid="stMetric"] {
        background: white;
        padding: 12px;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# OPTIONAL AI — Gemini key from Secrets
# =============================================================================
try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    AI_AVAILABLE = True
except Exception:
    GEMINI_KEY = None
    AI_AVAILABLE = False

# =============================================================================
# SESSION STATE — NO LOGIN / NO PAYWALL
# =============================================================================
if "report_history" not in st.session_state:
    st.session_state.report_history = []

if "workspace" not in st.session_state:
    st.session_state.workspace = []

if "feedback" not in st.session_state:
    st.session_state.feedback = {"rating": None, "would_pay": None, "comment": ""}

# =============================================================================
# HELPERS
# =============================================================================
@st.cache_data
def load_csv(file_bytes):
    return pd.read_csv(io.BytesIO(file_bytes))

def clean_numeric_column(series):
    """Convert messy numeric values to float while preserving negative signs."""
    s = series.astype(str).str.strip()
    s = s.str.replace(r"[^\d.\-]", "", regex=True)
    return pd.to_numeric(s, errors="coerce").fillna(0)

def money(x):
    return f"INR {x:,.0f}"

def safe_pct(num, den):
    return round((num / den * 100), 2) if den else 0

def normalize_name(x):
    return str(x).strip().lower()

def detect_platform(columns, filename=""):
    text = " ".join([normalize_name(c) for c in columns]) + " " + normalize_name(filename)
    if "amazon" in text or "settlement" in text or "referral fee" in text or "fba" in text:
        return "Amazon"
    if "shopify" in text or "aliexpress" in text or "cjdrop" in text or "rto" in text:
        return "Shopify / Dropshipping"
    if "instagram" in text or "insta" in text or "making cost" in text:
        return "Instagram / Boutique"
    if "kharid" in text or "bill no" in text or "shop kharcha" in text:
        return "Local / Kirana"
    if "meesho" in text:
        return "Meesho"
    if "flipkart" in text:
        return "Flipkart"
    return "Generic CSV"

def build_pdf(summary, history_rows, business_mode, platform):
    if not REPORTLAB_AVAILABLE:
        return None
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=35, leftMargin=35, topMargin=35, bottomMargin=35)
    styles = getSampleStyleSheet()
    title = styles["Title"]
    title.alignment = TA_CENTER
    story = [
        Paragraph("AI Business Analyst", title),
        Paragraph("By Anirudh — Free Business Analytics Report", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(f"<b>Business:</b> {business_mode}", styles["Normal"]),
        Paragraph(f"<b>Detected platform:</b> {platform}", styles["Normal"]),
        Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}", styles["Normal"]),
        Spacer(1, 12),
    ]
    data = [["Metric", "Value"]] + [[k, str(v)] for k, v in summary.items()]
    table = Table(data, colWidths=[220, 280])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), .5, colors.grey),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("PADDING", (0,0), (-1,-1), 6),
    ]))
    story += [table, Spacer(1, 15), Paragraph("<b>Product Performance</b>", styles["Heading2"])]
    if history_rows:
        rows = [["Product", "Revenue", "Profit", "Margin %"]]
        rows += [[str(r[0]), money(r[1]), money(r[2]), f"{r[3]:.2f}%"] for r in history_rows[:20]]
        pt = Table(rows, colWidths=[180, 100, 100, 80])
        pt.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("GRID", (0,0), (-1,-1), .5, colors.grey),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("PADDING", (0,0), (-1,-1), 5),
        ]))
        story.append(pt)
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# =============================================================================
# HEADER / LANDING
# =============================================================================
st.markdown("""
<div class="hero">
    <span class="free-badge">100% FREE • NO LOGIN • NO PAYWALL</span>
    <h1>📊 AI-Driven Business Analyst Dashboard</h1>
    <p>Ek tool — Amazon, Boutique, Dropshipping aur Local Business ke liye.</p>
    <p class="small-muted">CSV upload karo, automatic analysis dekho, loss identify karo aur action plan pao.</p>
</div>
""", unsafe_allow_html=True)

with st.expander("ℹ️ About this tool — kaise kaam karta hai?", expanded=False):
    st.write(
        "Ye dashboard uploaded sales CSV ke columns ko automatically map karta hai aur "
        "revenue, product cost, fees, shipping, GST, ad spend, profit, margin, loss aur "
        "possible RTO/return impact ka analysis karta hai. Platform detection bhi automatic hai."
    )

business_mode = st.selectbox(
    "Aap Kaunsa Business Karte Ho? 👇",
    [
        "Amazon / Flipkart Seller",
        "Instagram / Boutique Store",
        "Dropshipping / Shopify",
        "Small Local Business / Kirana"
    ],
    index=0
)

# =============================================================================
# SIDEBAR — SAMPLE DATA + WORKSPACE
# =============================================================================
with st.sidebar:
    st.header("🧰 Tools")
    use_demo = st.button("🧪 Load Sample / Demo Data", use_container_width=True)

    st.markdown("---")
    st.subheader("🗂️ Workspace")
    st.caption("No login required. Current session ke reports yahan track honge.")
    if st.session_state.workspace:
        for i, item in enumerate(st.session_state.workspace[-5:], 1):
            st.write(f"{i}. {item}")
    else:
        st.caption("Abhi koi report nahi hai.")

    st.markdown("---")
    st.subheader("❓ Quick FAQ")
    st.write("**Kya data free hai?** Haan, dashboard mein koi paywall nahi.")
    st.write("**Login chahiye?** Nahi.")
    st.write("**AI report?** Gemini key configured ho to AI report; warna rule-based report.")

# =============================================================================
# DEMO DATA
# =============================================================================
demo_data = {
    "Amazon / Flipkart Seller": pd.DataFrame([
        ["A-1001", "Men T-Shirt", 699, 350, 104, 45, 50, 35, "2026-08-25", "FBA"],
        ["A-1002", "Men T-Shirt", 699, 350, 104, 45, 50, 35, "2026-08-26", "FBA"],
        ["A-1003", "Women Kurti", 1199, 600, 179, 45, 60, 60, "2026-08-26", "EasyShip"],
        ["A-1004", "Mobile Cover", 349, 110, 52, 45, 40, 17, "2026-08-27", "Self Ship"],
        ["A-1005", "Bluetooth Earbuds", 1499, 850, 224, 45, 50, 75, "2026-08-27", "FBA"],
    ], columns=["Order ID","Product Name","Sale Price","Product Cost","Referral Fee","Closing Fee","Shipping Fee","GST","Order Date","Fulfillment"]),
    "Instagram / Boutique Store": pd.DataFrame([
        ["INSTA-101","Anarkali Suit",2499,1300,150,300,120,"2026-08-20","Instagram DM","COD"],
        ["INSTA-102","Sharara Set",3199,1800,150,450,160,"2026-08-21","WhatsApp","Prepaid"],
        ["INSTA-103","Cotton Kurta",999,500,150,100,50,"2026-08-22","Instagram DM","COD"],
    ], columns=["Order ID","Design Name","Sale Price","Making Cost","Courier Charge","Insta Ad Spend","Packaging","Order Date","Source","Payment"]),
    "Dropshipping / Shopify": pd.DataFrame([
        ["SH-9001","Pet Hair Remover",799,180,280,45,22,"2026-08-22","FB Ads","AliExpress"],
        ["SH-9002","LED Strip Lights",1299,350,400,60,35,"2026-08-23","FB Ads","CJdropshipping"],
        ["SH-9003","Posture Corrector",699,150,250,45,18,"2026-08-24","TikTok Ads","AliExpress"],
    ], columns=["Order ID","Winning Product","Sale Price","Product Cost (AliExpress)","Ad Spend","Shopify Fee","RTO Loss","Order Date","Ad Platform","Supplier"]),
    "Small Local Business / Kirana": pd.DataFrame([
        ["BILL-501","Atta 10kg",450,410,10,5,"2026-08-20","Cash","Regular"],
        ["BILL-502","Mustard Oil 1L",180,165,5,2,"2026-08-21","UPI","Regular"],
        ["BILL-503","Tea 500g",260,230,10,8,"2026-08-22","Cash","New"],
        ["BILL-504","Sugar 5kg",220,200,10,3,"2026-08-24","Cash","Regular"],
    ], columns=["Bill No","Item Name","Sale Price","Kharid Rate","Shop Kharcha","Transport","Date","Payment Mode","Customer Type"])
}

uploaded_file = st.file_uploader("📥 Upload Your CSV Dataset", type=["csv"])

if use_demo:
    df = demo_data[business_mode].copy()
    source_name = "Demo Data"
    st.info("🧪 Demo dataset loaded.")
elif uploaded_file is not None:
    try:
        df = load_csv(uploaded_file.getvalue())
        source_name = uploaded_file.name
    except Exception as e:
        st.error(f"CSV read error: {e}")
        st.stop()
else:
    st.info("💡 CSV upload karo ya sidebar se Demo Data load karo.")
    st.markdown("---")
    st.subheader("🚀 Start in 3 steps")
    a, b, c = st.columns(3)
    with a:
        st.info("1️⃣ Upload CSV")
    with b:
        st.info("2️⃣ Auto-detection")
    with c:
        st.info("3️⃣ Free full report")
    st.markdown("---")
    with st.expander("📚 FAQ — Frequently Asked Questions"):
        st.write("**Kaunse businesses supported hain?** Amazon/Flipkart, Instagram/Boutique, Dropshipping/Shopify aur Kirana.")
        st.write("**Kya payment karna padega?** Nahi. Is version mein paywall aur Razorpay completely removed hain.")
        st.write("**Kya login chahiye?** Nahi.")
        st.write("**Kya AI mandatory hai?** Nahi. Gemini available na ho to rule-based report chalegi.")
    st.stop()

if df.empty:
    st.warning("⚠️ Uploaded file has no rows.")
    st.stop()

# =============================================================================
# PROGRESS STEPS
# =============================================================================
progress = st.progress(0)
status = st.empty()

status.info("📖 Step 1/4 — Reading dataset...")
time.sleep(0.15)
progress.progress(25)

original_cols = list(df.columns)
clean_cols = [normalize_name(c) for c in original_cols]
col_mapping = dict(zip(clean_cols, original_cols))

status.info("🔎 Step 2/4 — Detecting business/platform columns...")
time.sleep(0.15)

platform = detect_platform(original_cols, source_name)

# Keyword dictionaries
item_keywords = ["item", "product", "name", "sku", "title", "particulars", "description", "design"]
rev_keywords = ["revenue", "sales", "amount", "grand total", "net sales", "turnover", "total", "sale price", "price", "rate"]
qty_keywords = ["quantity", "qty", "units", "sold", "count", "volume", "pieces"]
cost_keywords = ["product cost", "purchase price", "purchase cost", "making cost", "kharid", "buy price", "cogs"]
fee_keywords = ["referral fee", "closing fee", "commission", "platform fee", "marketplace fee", "shopify fee", "fee"]
ship_keywords = ["shipping", "courier", "delivery charge", "logistics", "transport"]
gst_keywords = ["gst", "tax", "vat"]
ad_keywords = ["ad spend", "advertising", "insta ad spend", "marketing spend", "ppc"]
rto_keywords = ["rto", "return loss", "return cost", "refund", "returns"]

used_cols = set()

def find_col(keywords):
    # Exact/strong match first
    for c in clean_cols:
        real = col_mapping[c]
        if real in used_cols:
            continue
        if c in keywords:
            used_cols.add(real)
            return real
    # Substring match second
    for c in clean_cols:
        real = col_mapping[c]
        if real in used_cols:
            continue
        if any(k in c for k in keywords):
            used_cols.add(real)
            return real
    return None

item_col = find_col(item_keywords)
rev_col = find_col(rev_keywords)
qty_col = find_col(qty_keywords)
cost_col = find_col(cost_keywords)
fee_col = find_col(fee_keywords)
ship_col = find_col(ship_keywords)
gst_col = find_col(gst_keywords)
ad_col = find_col(ad_keywords)
rto_col = find_col(rto_keywords)

item_auto = rev_auto = qty_auto = False

if not item_col:
    text_cols = df.select_dtypes(include=["object"]).columns
    item_col = text_cols[0] if len(text_cols) else original_cols[0]
    item_auto = True

if not rev_col:
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols):
        rev_col = numeric_cols[0]
    else:
        rev_col = original_cols[0]
    rev_auto = True

if not qty_col:
    df["auto_generated_qty"] = 1
    qty_col = "auto_generated_qty"
    qty_auto = True

status.info("🧮 Step 3/4 — Cleaning and calculating...")
time.sleep(0.15)
progress.progress(60)

for col in [rev_col, qty_col, cost_col, fee_col, ship_col, gst_col, ad_col, rto_col]:
    if col and col in df.columns:
        df[col] = clean_numeric_column(df[col])

df["Real_Cost"] = df[cost_col] if cost_col else 0
df["Real_Fee"] = df[fee_col] if fee_col else 0
df["Real_Ship"] = df[ship_col] if ship_col else 0
df["Real_GST"] = df[gst_col] if gst_col else 0
df["Real_Ad"] = df[ad_col] if ad_col else 0
df["Real_RTO"] = df[rto_col] if rto_col else 0

# For RTO/refund columns, a positive expense is subtracted.
# If a refund is already negative, adding it back is avoided by using the actual sign.
df["Real_Profit"] = (
    df[rev_col]
    - df["Real_Cost"]
    - df["Real_Fee"]
    - df["Real_Ship"]
    - df["Real_GST"]
    - df["Real_Ad"]
    - df["Real_RTO"].clip(lower=0)
)

df["Margin_%"] = np.where(
    df[rev_col] != 0,
    df["Real_Profit"] / df[rev_col] * 100,
    0
).round(2)

total_revenue = float(df[rev_col].sum())
total_profit = float(df["Real_Profit"].sum())
total_units = float(df[qty_col].sum())
total_orders = len(df)
margin_pct = safe_pct(total_profit, total_revenue)

has_expense_data = any([cost_col, fee_col, ship_col, gst_col, ad_col, rto_col])

prod_summary = (
    df.groupby(item_col)
    .agg(
        Revenue=(rev_col, "sum"),
        Real_Profit=("Real_Profit", "sum"),
        Quantity=(qty_col, "sum"),
        Margin_pct=("Margin_%", "mean")
    )
    .sort_values("Real_Profit", ascending=False)
)

loss_products = prod_summary[prod_summary["Real_Profit"] < 0]
top_item = prod_summary.index[0] if len(prod_summary) else "N/A"
worst_item = prod_summary.index[-1] if len(prod_summary) else "N/A"

status.info("📊 Step 4/4 — Building report...")
time.sleep(0.15)
progress.progress(100)
status.success("✅ Analysis complete — Full report unlocked for everyone.")

# =============================================================================
# DETECTION PANEL
# =============================================================================
with st.expander("🔍 Detected columns — verify before trusting the numbers", expanded=False):
    left, right = st.columns(2)
    with left:
        st.write(f"**Platform:** `{platform}`")
        st.write(f"**Item/Product:** `{item_col}`" + (" _(auto-guessed)_" if item_auto else ""))
        st.write(f"**Revenue:** `{rev_col}`" + (" _(auto-guessed)_" if rev_auto else ""))
        st.write(f"**Quantity:** `{qty_col}`" + (" _(defaulted to 1/row)_" if qty_auto else ""))
        st.write(f"**Product Cost:** `{cost_col or 'Not found — ₹0'}'")
    with right:
        st.write(f"**Platform Fee:** `{fee_col or 'Not found — ₹0'}'")
        st.write(f"**Shipping:** `{ship_col or 'Not found — ₹0'}'")
        st.write(f"**GST/Tax:** `{gst_col or 'Not found — ₹0'}'")
        st.write(f"**Ad Spend:** `{ad_col or 'Not found — ₹0'}'")
        st.write(f"**RTO/Return:** `{rto_col or 'Not found — ₹0'}'")

# =============================================================================
# METRICS
# =============================================================================
st.markdown("### 📈 Business Overview")

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("💰 TOTAL REVENUE", money(total_revenue))
m2.metric("💵 REAL PROFIT", money(total_profit), f"{margin_pct:.1f}% Margin" if has_expense_data else "Expense data incomplete")
m3.metric("🛍️ ORDERS", f"{total_orders:,}")
m4.metric("📦 UNITS", f"{total_units:,.0f}")
m5.metric("🚨 LOSS PRODUCTS", f"{len(loss_products)}")

if not has_expense_data:
    st.warning("⚠️ Expense columns detect nahi hui. Profit complete net profit nahi maana jaana chahiye.")

if len(loss_products):
    st.error(f"🚨 LOSS ALERT: {len(loss_products)} product(s) negative profit mein hain.")
    st.dataframe(
        loss_products.rename(columns={"Margin_pct": "Margin %"}),
        use_container_width=True
    )
    st.write(f"**Action:** `{worst_item}` ki pricing/cost/fees review karo.")

# =============================================================================
# TABS
# =============================================================================
tab_overview, tab_products, tab_report = st.tabs(
    ["📊 Overview", "🛍️ Product Detail", "🤖 Report & Action Plan"]
)

with tab_overview:
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Product Real Profit Contribution")
        chart_data = prod_summary["Real_Profit"].sort_values(ascending=False)
        if PLOTLY_AVAILABLE:
            fig = px.bar(
                x=chart_data.index.astype(str),
                y=chart_data.values,
                labels={"x": "Product", "y": "Real Profit"},
                title="Profit by Product"
            )
            fig.update_layout(xaxis_tickangle=-35)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(chart_data)

    with c2:
        st.markdown("#### Paisa Kaha Kata? — Expense Breakdown")
        if has_expense_data:
            fee_breakup = pd.DataFrame({
                "Type": ["Product Cost", "Fees/Commission", "Shipping/Courier", "GST/Tax", "Ad Spend", "RTO/Return", "Profit"],
                "Amount": [
                    df["Real_Cost"].sum(),
                    df["Real_Fee"].sum(),
                    df["Real_Ship"].sum(),
                    df["Real_GST"].sum(),
                    df["Real_Ad"].sum(),
                    df["Real_RTO"].clip(lower=0).sum(),
                    total_profit
                ]
            })
            fee_breakup = fee_breakup[fee_breakup["Amount"] != 0]
            if PLOTLY_AVAILABLE:
                fig2 = px.bar(
                    fee_breakup,
                    x="Type",
                    y="Amount",
                    title="Revenue Allocation / Expense Breakdown"
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.bar_chart(fee_breakup.set_index("Type"))

    st.markdown("#### 📦 Revenue vs Profit")
    if PLOTLY_AVAILABLE:
        rp = prod_summary.reset_index().rename(columns={item_col: "Product"})
        fig3 = px.bar(
            rp,
            x="Product",
            y=["Revenue", "Real_Profit"],
            barmode="group",
            title="Revenue vs Real Profit"
        )
        fig3.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.bar_chart(prod_summary[["Revenue", "Real_Profit"]])

with tab_products:
    st.markdown("### 🛍️ Complete Product Performance")
    display_products = prod_summary.reset_index().rename(columns={
        item_col: "Product",
        "Revenue": "Revenue",
        "Real_Profit": "Real Profit",
        "Quantity": "Units",
        "Margin_pct": "Margin %"
    })
    display_products["Revenue"] = display_products["Revenue"].round(2)
    display_products["Real Profit"] = display_products["Real Profit"].round(2)
    display_products["Margin %"] = display_products["Margin %"].round(2)
    st.dataframe(display_products, use_container_width=True, hide_index=True)

    st.markdown("### 🔎 Row-level calculated data")
    st.dataframe(df, use_container_width=True, hide_index=True)

with tab_report:
    def build_data_summary():
        lines = [
            f"Business type: {business_mode}",
            f"Detected platform: {platform}",
            f"Source: {source_name}",
            f"Total revenue: INR {total_revenue:,.0f}",
            f"Real profit: INR {total_profit:,.0f} ({margin_pct:.1f}% margin)" if has_expense_data else "Expense data incomplete — profit is not fully net of costs.",
            f"Total orders: {total_orders}",
            f"Total units: {total_units:,.0f}",
            f"Top item by profit: {top_item}",
            f"Loss-making items: {len(loss_products)}",
        ]
        return "\n".join(lines)

    ai_used = False
    if AI_AVAILABLE:
        st.markdown(f"### 🤖 AI Strategic Report — {business_mode}")
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_KEY)
            prompt = (
                f"You are a business analyst for a {business_mode} in India. "
                "Based only on the supplied summary, write a concise Hinglish business report. "
                "Include: one-line summary, best product, loss products if any, likely cost issue, "
                "and a practical 30-day action plan. Never invent numbers.\n\n"
                + build_data_summary()
            )
            with st.spinner("Generating AI insights..."):
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
            st.write(response.text)
            ai_used = True
        except Exception as ai_err:
            st.warning(f"AI generation failed: {ai_err}. Rule-based report shown below.")

    if not ai_used:
        st.markdown(f"### 📑 Business Report — {business_mode}")
        st.write(f"• **Revenue:** Total business revenue is **{money(total_revenue)}**.")
        if has_expense_data:
            st.write(f"• **Real Profit:** Estimated profit after detected expenses is **{money(total_profit)} ({margin_pct:.1f}% margin)**.")
        else:
            st.write("• **Profit:** Complete expense data missing hai, isliye net profit estimate incomplete hai.")
        st.write(f"• **Hero Product:** **{top_item}** sabse zyada total profit contribution de raha hai.")
        if len(loss_products):
            st.write(f"• **Danger Product:** **{worst_item}** negative profit mein hai.")

    st.success(
        f"""⚡ **Next 30 Days Action Plan**

1. **Hero Product Scale:** '{top_item}' ke successful pricing/offer ko optimize karke volume badhao.
2. **Loss Control:** Negative-profit products ki price, product cost, shipping aur platform fees review karo.
3. **Weekly Tracking:** Har week same CSV format mein report re-run karke revenue, profit aur margin compare karo."""
    )

# =============================================================================
# RTO / RETURN ANALYSIS
# =============================================================================
if rto_col:
    st.markdown("---")
    st.subheader("🔄 RTO / Return-Aware Analysis")
    r1, r2, r3 = st.columns(3)
    rto_total = float(df["Real_RTO"].clip(lower=0).sum())
    r1.metric("RTO / Return Cost", money(rto_total))
    r2.metric("Orders with RTO Data", f"{int((df['Real_RTO'] > 0).sum())}")
    r3.metric("Profit After RTO", money(total_profit))
    st.caption("Positive RTO/return cost ko expense maana gaya hai. Refund/adjustment already negative ho to sign preserve hota hai.")

# =============================================================================
# REPORT HISTORY / MULTI-CLIENT SESSION WORKSPACE
# =============================================================================
report_record = {
    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "business": business_mode,
    "platform": platform,
    "source": source_name,
    "revenue": total_revenue,
    "profit": total_profit,
    "margin": margin_pct,
    "orders": total_orders
}

key = json.dumps(report_record, sort_keys=True)
if not any(json.dumps(x, sort_keys=True) == key for x in st.session_state.report_history):
    st.session_state.report_history.append(report_record)
    st.session_state.workspace.append(f"{business_mode} • {platform} • {money(total_profit)}")

st.markdown("---")
with st.expander("🕘 Report History — Current Session"):
    if st.session_state.report_history:
        hist_df = pd.DataFrame(st.session_state.report_history)
        st.dataframe(hist_df, use_container_width=True, hide_index=True)
    else:
        st.caption("No previous reports.")

# =============================================================================
# EXPORTS
# =============================================================================
st.markdown("---")
st.subheader("📥 Export Your Report")

summary_dict = {
    "Business": business_mode,
    "Platform": platform,
    "Revenue": money(total_revenue),
    "Real Profit": money(total_profit),
    "Margin": f"{margin_pct:.2f}%",
    "Orders": total_orders,
    "Units": total_units,
    "Loss Products": len(loss_products),
    "Top Product": top_item,
}

csv_export = display_products.to_csv(index=False).encode("utf-8")
txt_export = build_data_summary()

e1, e2, e3 = st.columns(3)
with e1:
    st.download_button(
        "📥 Download Product CSV",
        data=csv_export,
        file_name="business_product_analysis.csv",
        mime="text/csv",
        use_container_width=True
    )
with e2:
    st.download_button(
        "📄 Download Summary TXT",
        data=txt_export,
        file_name="business_report_summary.txt",
        mime="text/plain",
        use_container_width=True
    )
with e3:
    pdf_bytes = build_pdf(
        summary_dict,
        [
            (idx, row["Revenue"], row["Real_Profit"], row["Margin_pct"])
            for idx, row in prod_summary.iterrows()
        ],
        business_mode,
        platform
    )
    if pdf_bytes:
        st.download_button(
            "📕 Download Branded PDF",
            data=pdf_bytes,
            file_name="AI_Business_Analyst_Report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.warning("PDF export ke liye `reportlab` install karein.")

# =============================================================================
# FEEDBACK
# =============================================================================
st.markdown("---")
st.subheader("💬 Quick Feedback")
st.caption("Login ki zarurat nahi. Tumhari feedback se tool improve karne mein help milegi.")

f1, f2 = st.columns(2)
with f1:
    rating = st.radio("Dashboard kaisa laga?", ["👍 Useful", "😐 Average", "👎 Needs Improvement"], horizontal=True)
with f2:
    would_pay = st.radio("Agar future premium version ho, kya pay karoge?", ["Yes", "Maybe", "No"], horizontal=True)

comment = st.text_area("Optional feedback / suggestion", placeholder="Kya feature aur add hona chahiye?")

if st.button("📨 Submit Feedback"):
    st.session_state.feedback = {
        "rating": rating,
        "would_pay": would_pay,
        "comment": comment
    }
    st.success("🙏 Thanks! Feedback recorded for this session.")

# =============================================================================
# FAQ
# =============================================================================
st.markdown("---")
with st.expander("❓ FAQ — Frequently Asked Questions"):
    st.markdown("""
**1. Kya ye tool free hai?**  
Haan. Is version mein Razorpay, payment link, unlock code aur paywall completely removed hain.

**2. Kya Login/Signup chahiye?**  
Nahi.

**3. Kaunse businesses supported hain?**  
Amazon/Flipkart Seller, Instagram/Boutique, Dropshipping/Shopify aur Small Local Business/Kirana.

**4. Kya CSV ke columns automatically detect hote hain?**  
Haan. Detected-columns panel mein mapping verify kar sakte ho.

**5. Real Profit kaise calculate hota hai?**  
Revenue se detected product cost, fees, shipping, GST, ad spend aur positive RTO/return expenses subtract kiye jaate hain.

**6. Agar column missing ho?**  
Missing expense ko ₹0 maana jaata hai aur dashboard warning deta hai.

**7. AI report kaise chalegi?**  
Gemini API key Streamlit Secrets mein configured ho to AI report generate hogi. Key unavailable hone par rule-based report automatically chalegi.

**8. Kya previous reports save hote hain?**  
Current Streamlit session mein report history/workspace available hai. Permanent cloud database/login system is version mein intentionally nahi hai.

**9. Kya PDF download kar sakte hain?**  
Haan, agar `reportlab` installed hai.

**10. Kya data invent hota hai?**  
Calculations uploaded CSV ke detected data par based hain. AI prompt ko supplied numbers tak limited rakha gaya hai.
""")

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.success("🚀 **Built with ❤️ by Anirudh (Student Developer)** | 1 Free Tool for Multiple Businesses")
st.caption("No login • No paywall • No Razorpay • Full report available")
