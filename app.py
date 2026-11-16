import streamlit as st
import pandas as pd
import numpy as np
import time
import requests

# =============================================================================
# PAGE CONFIG + THEME
# =============================================================================
st.set_page_config(page_title="AI Business Analyst - By Anirudh", layout="wide", page_icon="📊")

st.markdown("""
<style>
    .main-header { font-size: 2.3rem; font-weight: 800; color: #16213e; margin-bottom: 0; }
    .sub-header { color: #6b7280; font-size: 1.05rem; margin-top: 4px; }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #f8f9ff 0%, #eef1ff 100%);
        border: 1px solid #dde1f5;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }
    div[data-testid="stMetric"] [data-testid="stMetricLabel"],
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] * { color: #16213e !important; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"],
    div[data-testid="stMetric"] [data-testid="stMetricValue"] * { color: #0f172a !important; }
    div[data-testid="stMetric"] [data-testid="stMetricDelta"],
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] * { color: #15803d !important; }
    .exec-summary {
        background: #fffbea;
        border-left: 4px solid #f59e0b;
        border-radius: 8px;
        padding: 14px 18px;
        color: #1a1a2e;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; padding: 8px 16px; font-weight: 600; }
    .stButton>button, .stDownloadButton>button { border-radius: 8px; font-weight: 600; }
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE INIT
# =============================================================================
if "use_demo" not in st.session_state:
    st.session_state.use_demo = False

# =============================================================================
# REUSABLE FEEDBACK FORM FUNCTION (FORMSPREE CONNECTED)
# =============================================================================
def render_feedback_form(form_key):
    st.markdown("---")
    st.markdown("### 💬 Aapka Feedback")
    with st.form(form_key, clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            usefulness = st.radio(
                "Report kaisi lagi?",
                ["👍 Useful", "👎 Not Useful"],
                horizontal=True
            )
            willingness = st.number_input(
                "Is tool ke liye aap kitna pay karenge? (₹)",
                min_value=0,
                step=50
            )
        with col2:
            user_review = st.text_area(
                "Aapka Review",
                placeholder="Yahan apna review ya suggestion likhein..."
            )

        submit_btn = st.form_submit_button("Submit")
        if submit_btn:
            FORMSPREE_URL = "https://formspree.io/f/xzerejwe"
            payload = {
                "1_Useful_or_Not": usefulness,
                "2_Kitna_Pay_Karoge": f"₹{willingness}",
                "3_Review": user_review if user_review.strip() else "No text review"
            }
            try:
                res = requests.post(FORMSPREE_URL, data=payload)
                if res.status_code == 200:
                    st.success("🎉 Shukriya! Aapka feedback save ho gaya hai.")
                else:
                    st.error("⚠️ Save nahi ho paya, please dobara try karein.")
            except Exception:
                st.error("⚠️ Network error! Dobara try karein.")

# =============================================================================
# OPTIONAL AI (Gemini) — key read from Streamlit Secrets
# =============================================================================
try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    AI_AVAILABLE = True
except Exception:
    GEMINI_KEY = None
    AI_AVAILABLE = False

# =============================================================================
# HEADER / LANDING SECTION
# =============================================================================
st.markdown('<p class="main-header">📊 AI-Driven Business Analyst Dashboard</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Apni sales CSV upload karo, seconds mein real profit, RTO loss aur AI report paao — bilkul free.</p>', unsafe_allow_html=True)

with st.expander("ℹ️ Ye tool kya karta hai? (About)"):
    st.write(
        "Ye tool aapke sales data (CSV file) ko analyze karke asli profit calculate karta hai — sirf revenue nahi, "
        "balki product cost, platform fees, shipping, RTO/return shipping loss, GST aur ad spend kaat kar. "
        "🔒 **100% Safe & Private:** Hum aapka koi bhi data server par save nahi karte."
    )

st.markdown("---")

business_mode = st.selectbox(
    "Aap Kaunsa Business Karte Ho? Select Karo 👇",
    ["Amazon / Flipkart Seller", "Instagram / Boutique Store", "Dropshipping / Shopify", "Small Local Business / Kirana"],
    index=0
)
st.markdown("---")

st.markdown("### 🛠️ How to use this tool")
col_step1, col_step2, col_step3 = st.columns(3)
with col_step1:
    st.info("##### 1. Upload CSV\nApni sales sheet ko .CSV format mein upload karein, ya neeche demo data try karein.")
with col_step2:
    st.info(f"##### 2. Auto-Detect for {business_mode}\nTool aapke columns se Fees/GST/RTO/Date/Payment detect karega.")
with col_step3:
    st.info("##### 3. Get Full Report\nExecutive Summary, RTO Loss Alert, Trends aur AI Report.")

st.write("")

# =============================================================================
# FEEDBACK SECTION 1: BEFORE CSV UPLOAD BLOCK
# =============================================================================
render_feedback_form("feedback_before_csv")
st.markdown("---")

# =============================================================================
# DATA SOURCE: real upload OR built-in demo dataset
# =============================================================================
@st.cache_data
def get_demo_data():
    dates = pd.date_range("2026-08-01", periods=10, freq="3D").strftime("%d-%m-%Y")
    return pd.DataFrame({
        "Product Name": ["Cotton Kurti", "Denim Jacket", "Silk Saree", "Cotton Kurti", "Leather Bag",
                          "Denim Jacket", "Printed Tshirt", "Silk Saree", "Leather Bag", "Printed Tshirt"],
        "Category": ["Ethnic Wear", "Western Wear", "Ethnic Wear", "Ethnic Wear", "Accessories",
                     "Western Wear", "Western Wear", "Ethnic Wear", "Accessories", "Western Wear"],
        "Order Date": dates,
        "Order Status": ["Delivered", "Delivered", "RTO", "Delivered", "Delivered",
                          "Cancelled", "Delivered", "Delivered", "Delivered", "Delivered"],
        "Payment Mode": ["COD", "Prepaid", "COD", "Prepaid", "COD", "COD", "Prepaid", "Prepaid", "COD", "Prepaid"],
        "Sale Price": [899, 2499, 4999, 899, 1899, 2499, 499, 4999, 1899, 499],
        "Quantity": [3, 1, 1, 2, 1, 1, 5, 2, 2, 4],
        "Product Cost": [400, 1200, 2500, 400, 900, 1200, 200, 2500, 900, 200],
        "Referral Fee": [90, 250, 500, 90, 190, 250, 50, 500, 190, 50],
        "Closing Fee": [20, 40, 60, 20, 30, 40, 15, 60, 30, 15],
        "Shipping": [60, 90, 120, 60, 80, 90, 40, 120, 80, 40],
        "GST": [45, 125, 250, 45, 95, 125, 25, 250, 95, 25],
    })


st.markdown("### 📥 Upload Your Dataset Here")
col_up1, col_up2 = st.columns([3, 1])
with col_up1:
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])
    if uploaded_file is not None:
        st.session_state.use_demo = False
with col_up2:
    st.write("")
    st.write("")
    if st.button("🎮 Try Demo Data"):
        st.session_state.use_demo = True

st.markdown("---")


@st.cache_data
def load_csv(file):
    return pd.read_csv(file)


def clean_numeric_column(series):
    s = series.astype(str).str.strip()
    s = s.str.replace(r'[^\d.\-]', '', regex=True)
    return pd.to_numeric(s, errors='coerce').fillna(0)


def detect_platform(columns):
    col_str = " ".join([str(c).strip().lower() for c in columns])
    if any(k in col_str for k in ["lineitem", "fulfillment status", "financial status"]):
        return "Shopify"
    if any(k in col_str for k in ["reason for credit entry", "supplier discounted price", "sub order no"]):
        return "Meesho"
    if any(k in col_str for k in ["asin"]) or ("order id" in col_str and "sku" in col_str):
        return "Amazon"
    if any(k in col_str for k in ["fsn", "flipkart"]):
        return "Flipkart"
    return "Generic / Custom CSV"


RETURN_STATUS_VALUES = ["rto", "return", "returned", "cancelled", "canceled", "refund", "refunded", "lost", "damaged"]

active_df = None
active_filename = None

if uploaded_file is not None:
    active_df = load_csv(uploaded_file)
    active_filename = uploaded_file.name
elif st.session_state.use_demo:
    active_df = get_demo_data()
    active_filename = "demo_data.csv"
    st.info("🎮 Demo data loaded — sample sales data hai taaki aap tool try kar sakein bina apni CSV ke.")

if active_df is not None:
    try:
        df = active_df.copy()
        if df.empty:
            st.warning("⚠️ File mein koi rows nahi hain.")
            st.stop()

        original_cols = list(df.columns)
        clean_cols = [str(c).strip().lower() for c in original_cols]
        col_mapping = dict(zip(clean_cols, original_cols))
        platform = detect_platform(original_cols)

        item_keywords = ['item', 'product', 'name', 'sku', 'title', 'particulars', 'description']
        rev_keywords = ['revenue', 'sales', 'amount', 'grand total', 'net sales', 'turnover', 'total', 'sale price', 'price', 'rate', 'mrp']
        qty_keywords = ['quantity', 'qty', 'units', 'sold', 'count', 'volume', 'pieces']
        cost_keywords = ['product cost', 'purchase price', 'purchase cost', 'kharid', 'buy price', 'cogs']
        fee_keywords = ['referral fee', 'closing fee', 'commission', 'platform fee', 'marketplace fee', 'handling fee', 'fee']
        ship_keywords = ['shipping', 'courier', 'delivery charge', 'logistics', 'freight']
        gst_keywords = ['gst', 'tax', 'vat', 'igst', 'cgst']
        ad_keywords = ['ad spend', 'advertising', 'fb ads', 'marketing spend', 'ppc']
        status_keywords = ['order status', 'status', 'reason for credit entry', 'shipment status']
        date_keywords = ['order date', 'purchase date', 'invoice date', 'date']
        payment_keywords = ['payment mode', 'payment method', 'payment type']
        category_keywords = ['category', 'product category', 'segment']

        used_cols = set()

        def find_col(keywords):
            for kw in keywords:
                for c in clean_cols:
                    real_col = col_mapping[c]
                    if real_col in used_cols:
                        continue
                    if kw in c:
                        used_cols.add(real_col)
                        return real_col
            return None

        def find_all_cols(keywords):
            matched = []
            for c in clean_cols:
                real_col = col_mapping[c]
                if real_col in used_cols:
                    continue
                if any(kw in c for kw in keywords):
                    used_cols.add(real_col)
                    matched.append(real_col)
            return matched

        item_col = find_col(item_keywords)
        rev_col = find_col(rev_keywords)
        qty_col = find_col(qty_keywords)
        cost_col = find_col(cost_keywords)
        fee_cols = find_all_cols(fee_keywords)
        ship_cols = find_all_cols(ship_keywords)
        gst_cols = find_all_cols(gst_keywords)
        ad_col = find_col(ad_keywords)
        status_col = find_col(status_keywords)
        date_col = find_col(date_keywords)
        payment_col = find_col(payment_keywords)
        category_col = find_col(category_keywords)

        item_auto = rev_auto = qty_auto = False
        if not item_col:
            text_cols = df.select_dtypes(include=['object']).columns
            item_col = text_cols[0] if len(text_cols) > 0 else original_cols[0]
            item_auto = True
        if not rev_col:
            num_cols = df.select_dtypes(include=['number']).columns
            rev_col = num_cols[0] if len(num_cols) > 0 else original_cols[0]
            rev_auto = True
        if not qty_col:
            df['auto_generated_qty'] = 1
            qty_col = 'auto_generated_qty'
            qty_auto = True

        numeric_targets = [rev_col, qty_col, cost_col, ad_col] + fee_cols + ship_cols + gst_cols
        for col in numeric_targets:
            if col and col in df.columns:
                df[col] = clean_numeric_column(df[col])

        rev_col_lower = str(rev_col).lower()
        is_unit_price = any(k in rev_col_lower for k in ['price', 'rate', 'mrp']) and not any(k in rev_col_lower for k in ['total', 'amount', 'revenue', 'sales'])
        if is_unit_price and not qty_auto:
            df['Calc_Revenue'] = df[rev_col] * df[qty_col]
        else:
            df['Calc_Revenue'] = df[rev_col]

        if cost_col:
            df['Calc_Cost'] = (df[cost_col] * df[qty_col]) if (is_unit_price and not qty_auto) else df[cost_col]
        else:
            df['Calc_Cost'] = 0.0

        df['Calc_Fee'] = df[fee_cols].sum(axis=1) if fee_cols else 0.0
        df['Calc_Ship'] = df[ship_cols].sum(axis=1) if ship_cols else 0.0
        df['Calc_GST'] = df[gst_cols].sum(axis=1) if gst_cols else 0.0
        df['Calc_Ad'] = df[ad_col] if ad_col else 0.0

        df_all = df.copy()

        excluded_count = 0
        rto_loss_amount = 0.0
        if status_col:
            status_lower = df[status_col].astype(str).str.lower()
            is_returned = status_lower.apply(lambda x: any(k in x for k in RETURN_STATUS_VALUES))
            excluded_count = int(is_returned.sum())
            rto_df = df[is_returned].copy()
            rto_loss_amount = float((rto_df['Calc_Ship'] + rto_df['Calc_Fee']).sum())
            df = df[~is_returned].copy()

        df['Real_Profit'] = df['Calc_Revenue'] - df['Calc_Cost'] - df['Calc_Fee'] - df['Calc_Ship'] - df['Calc_GST'] - df['Calc_Ad']
        df['Margin_%'] = np.where(df['Calc_Revenue'] != 0, (df['Real_Profit'] / df['Calc_Revenue'] * 100), 0).round(2)

        total_revenue = float(df['Calc_Revenue'].sum())
        gross_delivered_profit = float(df['Real_Profit'].sum())
        net_real_profit = gross_delivered_profit - rto_loss_amount
        total_units = int(df[qty_col].sum())
        total_orders = len(df)
        margin_pct = (net_real_profit / total_revenue * 100) if total_revenue > 0 else 0
        has_expense_data = any([cost_col, fee_cols, ship_cols, gst_cols, ad_col])

        prod_summary = df.groupby(item_col).agg(
            Revenue=('Calc_Revenue', 'sum'),
            Real_Profit=('Real_Profit', 'sum'),
            Units=(qty_col, 'sum'),
            Margin_Pct=('Margin_%', 'mean')
        ).sort_values(by='Real_Profit', ascending=False)

        top_item = prod_summary.index[0] if len(prod_summary) > 0 else "N/A"
        worst_item = prod_summary.index[-1] if len(prod_summary) > 0 else "N/A"
        loss_products = prod_summary[prod_summary['Real_Profit'] < 0]

        trend_available = False
        trend_direction_text = None
        daily = None
        if date_col:
            parsed = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
            if parsed.notna().sum() >= 2:
                trend_df = df.copy()
                trend_df['ParsedDate'] = parsed
                trend_df = trend_df.dropna(subset=['ParsedDate'])
                daily = trend_df.groupby(trend_df['ParsedDate'].dt.date)['Calc_Revenue'].sum().reset_index()
                daily.columns = ['Date', 'Revenue']
                daily = daily.sort_values('Date')
                if len(daily) >= 2:
                    trend_available = True
                    mid = len(daily) // 2
                    first_half_avg = daily['Revenue'].iloc[:mid].mean() if mid > 0 else daily['Revenue'].mean()
                    second_half_avg = daily['Revenue'].iloc[mid:].mean()
                    if first_half_avg > 0:
                        change_pct = ((second_half_avg - first_half_avg) / first_half_avg) * 100
                        direction = "up" if change_pct > 0 else "down"
                        trend_direction_text = f"Recent revenue trend is {direction} {abs(change_pct):.1f}% vs the earlier period."

        payment_available = False
        payment_summary = None
        riskiest_payment = None
        if payment_col and status_col:
            df_all['is_returned_flag'] = df_all[status_col].astype(str).str.lower().apply(
                lambda x: any(k in x for k in RETURN_STATUS_VALUES))
            pay_group = df_all.groupby(payment_col).agg(
                Total_Orders=(payment_col, 'count'),
                Returned_Orders=('is_returned_flag', 'sum'),
                Revenue=('Calc_Revenue', 'sum')
            )
            pay_group['RTO_Rate_%'] = (pay_group['Returned_Orders'] / pay_group['Total_Orders'] * 100).round(1)
            if len(pay_group) > 0:
                payment_available = True
                payment_summary = pay_group
                riskiest_payment = pay_group['RTO_Rate_%'].idxmax()

        category_available = False
        category_summary = None
        if category_col:
            category_summary = df.groupby(category_col).agg(
                Revenue=('Calc_Revenue', 'sum'),
                Real_Profit=('Real_Profit', 'sum')
            ).sort_values(by='Revenue', ascending=False)
            if len(category_summary) > 0:
                category_available = True

        pareto_text = None
        if len(prod_summary) >= 3 and total_revenue > 0:
            rev_sorted = prod_summary['Revenue'].sort_values(ascending=False)
            cum_pct = (rev_sorted.cumsum() / rev_sorted.sum() * 100)
            n_products_80 = min(int((cum_pct <= 80).sum()) + 1, len(rev_sorted))
            pct_of_catalog = (n_products_80 / len(rev_sorted)) * 100
            pareto_text = f"Top {n_products_80} product(s) ({pct_of_catalog:.0f}% of your catalog) generate ~80% of total revenue."

        st.success(f"✔️ '{active_filename}' processed successfully! ({business_mode} mode)")

        with st.expander("🔍 Auto-Mapped Columns & Platform Details"):
            st.write(f"- **Detected platform format:** `{platform}`")
            st.write(f"- **Item/Product:** `{item_col}`" + (" _(auto-guessed)_" if item_auto else ""))
            st.write(f"- **Revenue/Price:** `{rev_col}`" + (" _(multiplied by Qty)_" if (is_unit_price and not qty_auto) else ""))
            st.write(f"- **Quantity:** `{qty_col}`" + (" _(defaulted to 1/row)_" if qty_auto else ""))
            st.write(f"- **Product Cost:** `{cost_col if cost_col else 'Not found'}`")
            st.write(f"- **Platform Fees (Combined):** `{', '.join(fee_cols) if fee_cols else 'Not found'}`")
            st.write(f"- **Shipping:** `{', '.join(ship_cols) if ship_cols else 'Not found'}`")
            st.write(f"- **GST/Tax:** `{', '.join(gst_cols) if gst_cols else 'Not found'}`")
            st.write(f"- **Ad Spend:** `{ad_col if ad_col else 'Not found'}`")
            if status_col and excluded_count > 0:
                st.info(f"ℹ️ Found **{excluded_count}** RTO/returned/cancelled orders. Unka shipping & fee loss (**₹{rto_loss_amount:,.0f}**) net profit se deduct kiya gaya hai.")

        if not has_expense_data:
            st.warning("⚠️ Cost/fee/shipping/GST column detect nahi hui — 'Real Profit' abhi sirf revenue ke barabar hai.")

        # =====================================================================
        # TABS
        # =====================================================================
        tab_overview, tab_trends, tab_products, tab_report = st.tabs(
            ["📈 Overview", "📊 Trends & Insights", "📦 Product Detail", "📑 Report"]
        )

        with tab_overview:
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("💰 DELIVERED REVENUE", f"₹{total_revenue:,.0f}")
            with m2:
                if has_expense_data:
                    st.metric("💵 NET REAL PROFIT", f"₹{net_real_profit:,.0f}", delta=f"{margin_pct:.1f}% Net Margin")
                else:
                    st.metric("💵 NET REAL PROFIT", "Incomplete")
            with m3:
                st.metric("💸 RTO / RETURN LOSS", f"₹{rto_loss_amount:,.0f}", delta=f"{excluded_count} Returns", delta_color="inverse")
            with m4:
                st.metric("🛍️ DELIVERED ORDERS", f"{total_orders} ({total_units} units)")

            if len(loss_products) > 0:
                st.error(f"🚨 LOSS ALERT: {len(loss_products)} product(s) loss mein hain!")
                st.dataframe(
                    loss_products[['Revenue', 'Real_Profit', 'Margin_Pct']],
                    use_container_width=True,
                    column_config={
                        "Revenue": st.column_config.NumberColumn("Revenue", format="₹%d"),
                        "Real_Profit": st.column_config.NumberColumn("Profit", format="₹%d"),
                        "Margin_Pct": st.column_config.NumberColumn("Margin %", format="%.1f%%"),
                    }
                )
                st.write(f"**Action:** '{worst_item}' ka price badhao ya cost/fee re-negotiate karo.")

            st.markdown("---")
            try:
                import plotly.express as px
                v1, v2 = st.columns(2)
                with v1:
                    st.markdown("#### Product Real Profit Contribution")
                    chart_df = df.groupby(item_col)['Real_Profit'].sum().sort_values(ascending=False).reset_index()
                    fig1 = px.bar(chart_df, x=item_col, y='Real_Profit', color='Real_Profit',
                                   color_continuous_scale=['#ef4444', '#22c55e'])
                    fig1.update_layout(showlegend=False, height=380)
                    st.plotly_chart(fig1, use_container_width=True)
                with v2:
                    st.markdown("#### Paisa Kaha Kata? (Expense & RTO Breakdown)")
                    if has_expense_data:
                        fee_breakup = {
                            "Product Cost": df['Calc_Cost'].sum(),
                            "Fees & Ads": df['Calc_Fee'].sum() + df['Calc_Ad'].sum(),
                            "Shipping (Delivered)": df['Calc_Ship'].sum(),
                            "RTO / Return Loss": rto_loss_amount,
                            "GST/Tax": df['Calc_GST'].sum(),
                            "Net Profit": max(net_real_profit, 0)
                        }
                        fee_df = pd.DataFrame(list(fee_breakup.items()), columns=['Type', 'Amount'])
                        fee_df = fee_df[fee_df['Amount'] > 0]
                        fig2 = px.pie(fee_df, names='Type', values='Amount', hole=0.4)
                        fig2.update_layout(height=380)
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.caption("Fee breakdown ke liye cost/fee/GST/shipping column chahiye.")
            except ImportError:
                st.bar_chart(df.groupby(item_col)['Real_Profit'].sum().sort_values(ascending=False))

        with tab_trends:
            st.markdown("#### 📅 Revenue Trend Over Time")
            if trend_available:
                try:
                    import plotly.express as px
                    fig_trend = px.line(daily, x='Date', y='Revenue', markers=True)
                    fig_trend.update_layout(height=350)
                    st.plotly_chart(fig_trend, use_container_width=True)
                    if trend_direction_text:
                        st.info(f"📈 {trend_direction_text}")
                except ImportError:
                    st.line_chart(daily.set_index('Date'))
            else:
                st.caption("Trend chart ke liye CSV mein ek Date column chahiye.")

            st.markdown("---")
            st.markdown("#### 💳 Payment Method & RTO Risk")
            if payment_available:
                st.dataframe(
                    payment_summary,
                    use_container_width=True,
                    column_config={
                        "Revenue": st.column_config.NumberColumn("Revenue", format="₹%d"),
                        "RTO_Rate_%": st.column_config.NumberColumn("RTO Rate", format="%.1f%%"),
                    }
                )
                st.warning(f"⚠️ **{riskiest_payment}** payment mode ka RTO rate sabse zyada hai ({payment_summary.loc[riskiest_payment, 'RTO_Rate_%']}%).")
            else:
                st.caption("COD vs Prepaid / RTO-rate breakdown ke liye Payment Mode aur Order Status column chahiye.")

            st.markdown("---")
            st.markdown("#### 🗂️ Category-wise Performance")
            if category_available:
                st.dataframe(
                    category_summary,
                    use_container_width=True,
                    column_config={
                        "Revenue": st.column_config.NumberColumn("Revenue", format="₹%d"),
                        "Real_Profit": st.column_config.NumberColumn("Profit", format="₹%d"),
                    }
                )
            else:
                st.caption("Category-wise summary ke liye CSV mein ek Category column chahiye.")

            st.markdown("---")
            st.markdown("#### 🎯 80/20 Insight (Pareto)")
            if pareto_text:
                st.info(f"📊 {pareto_text}")
            else:
                st.caption("Kam se kam 3 products chahiye ye insight ke liye.")

            st.markdown("---")
            st.markdown("#### ⚖️ Break-Even Calculator")
            fixed_cost = st.number_input("Monthly fixed costs (rent, salary, etc.) — optional (₹)", min_value=0, step=500)
            profit_per_unit = (net_real_profit / total_units) if total_units > 0 else 0
            if fixed_cost > 0 and profit_per_unit > 0:
                break_even_units = fixed_cost / profit_per_unit
                st.success(f"📌 Break-even: aapko approx **{break_even_units:.0f} units** bechne honge (₹{profit_per_unit:.2f}/unit net profit ke hisaab se) fixed costs cover karne ke liye.")
            elif fixed_cost > 0:
                st.caption("Break-even calculate karne ke liye profit-per-unit positive hona chahiye.")

        with tab_products:
            st.markdown("#### 📦 Full Product-wise Breakdown")
            display_df = prod_summary.rename(columns={
                'Real_Profit': "Profit", 'Units': "Units Sold", 'Margin_Pct': "Margin %"
            })
            st.dataframe(
                display_df.sort_values("Profit", ascending=False),
                use_container_width=True,
                column_config={
                    "Revenue": st.column_config.NumberColumn("Revenue", format="₹%d"),
                    "Profit": st.column_config.NumberColumn("Profit", format="₹%d"),
                    "Margin %": st.column_config.NumberColumn("Margin %", format="%.1f%%"),
                }
            )
            st.caption("Table ko column header pe click karke sort kar sakte ho.")

        with tab_report:
            st.markdown("### 📋 Executive Summary")
            exec_bullets = [f"Delivered revenue this period: **₹{total_revenue:,.0f}** across **{total_orders} orders**."]
            if has_expense_data:
                exec_bullets.append(f"Net real profit (after expenses & RTO loss): **₹{net_real_profit:,.0f}** ({margin_pct:.1f}% net margin).")
            if rto_loss_amount > 0:
                exec_bullets.append(f"Direct shipping/fee loss from {excluded_count} RTO/cancelled orders: **₹{rto_loss_amount:,.0f}**.")
            exec_bullets.append(f"Top performing product: **{top_item}**.")
            if len(loss_products) > 0:
                exec_bullets.append(f"⚠️ **{len(loss_products)} product(s)** are currently running at a loss.")
            if trend_direction_text:
                exec_bullets.append(trend_direction_text)
            if payment_available:
                exec_bullets.append(f"Highest RTO risk on **{riskiest_payment}** orders ({payment_summary.loc[riskiest_payment, 'RTO_Rate_%']}%).")
            if pareto_text:
                exec_bullets.append(pareto_text)
            st.markdown('<div class="exec-summary">' + "<br>".join(f"• {b}" for b in exec_bullets) + '</div>', unsafe_allow_html=True)
            st.markdown("---")

            def build_data_summary():
                lines = [
                    f"Business type: {business_mode}",
                    f"Platform detected: {platform}",
                    f"Delivered revenue: INR {total_revenue:,.0f}",
                    f"Net real profit: INR {net_real_profit:,.0f} ({margin_pct:.1f}% margin)" if has_expense_data else "Expense data incomplete.",
                    f"RTO/Return loss: INR {rto_loss_amount:,.0f} ({excluded_count} orders)",
                    f"Delivered orders: {total_orders}",
                    f"Top item by profit: {top_item}",
                    f"Loss-making items: {len(loss_products)}",
                ]
                if trend_direction_text:
                    lines.append(trend_direction_text)
                if payment_available:
                    lines.append(f"Highest RTO risk payment mode: {riskiest_payment}")
                if pareto_text:
                    lines.append(pareto_text)
                return "\n".join(lines)

            ai_used = False
            report_text = ""
            if AI_AVAILABLE:
                st.markdown(f"### 🤖 AI Strategic Report for {business_mode} (Hinglish)")
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=GEMINI_KEY)
                    with st.spinner("Generating AI insights..."):
                        prompt = (
                            f"You are a business analyst for a {business_mode} in India. Based on this sales data "
                            "summary, write a short strategic report in Hinglish. Include a one-line summary, "
                            "the best product, RTO loss impact, any loss-making products with a fix suggestion, and a 3-point "
                            "30-day action plan. Only use the numbers given, do not invent figures.\n\n" + build_data_summary()
                        )
                        model = genai.GenerativeModel("gemini-2.5-flash")
                        response = model.generate_content(prompt)
                        report_text = response.text
                        st.write(report_text)
                        ai_used = True
                except Exception:
                    st.warning("AI generation unavailable, showing rule-based report.")

            if not ai_used:
                st.markdown(f"### 📑 {business_mode} ke liye Detailed Report (Hinglish)")
                report_text = (
                    f"Revenue Summary: Is cycle me total INR {total_revenue:,.0f} ki delivered sales hui.\n"
                    + (f"Asli Munafa: Sab kharche aur RTO loss kaat ke net profit INR {net_real_profit:,.0f} ({margin_pct:.1f}% margin) hai.\n"
                       if has_expense_data else "Asli Munafa: Expense columns na milne ki wajah se accurate profit calculate nahi ho saka.\n")
                    + (f"RTO Nuksan: {excluded_count} returned/cancelled orders ki wajah se INR {rto_loss_amount:,.0f} ka seedha shipping/fee loss hua.\n" if rto_loss_amount > 0 else "")
                    + f"Hero Product: '{top_item}' sabse zyada profit de raha hai.\n"
                )
                st.write(report_text)
                if len(loss_products) > 0:
                    danger_line = f"Danger Product: '{worst_item}' pe loss ho raha hai — pricing ya cost dobara check karein."
                    st.write(danger_line)
                    report_text += danger_line + "\n"
                if payment_available:
                    pay_line = f"Payment Insight: '{riskiest_payment}' orders mein sabse zyada RTO/return risk hai."
                    st.write(pay_line)
                    report_text += pay_line + "\n"
                if pareto_text:
                    st.write(f"Pareto Insight: {pareto_text}")
                    report_text += pareto_text + "\n"
                action_plan = (
                    f"Action Plan (Next 30 Days):\n"
                    f"1. AOV Boost: '{top_item}' ke saath slow items ka combo banao.\n"
                    f"2. RTO Control: COD orders par WhatsApp confirmation lagao taaki INR {rto_loss_amount:,.0f} ka loss bache.\n"
                    "3. Track Weekly: Har hafte report re-run karke trend dekhein."
                )
                st.success(action_plan)
                report_text += action_plan

            st.markdown("---")
            brand_name = st.text_input("Business/Brand name for exported report", value="My Business")

            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button("📥 Download Summary as TXT", data=build_data_summary() + "\n\n" + report_text,
                                    file_name="business_report_summary.txt", mime="text/plain")
            with col_dl2:
                try:
                    from fpdf import FPDF
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Helvetica", "B", 18)
                    pdf.cell(0, 12, brand_name.encode('latin-1', 'ignore').decode('latin-1'), ln=True)
                    pdf.set_font("Helvetica", "", 10)
                    pdf.cell(0, 8, f"{business_mode}  |  Platform: {platform}", ln=True)
                    pdf.ln(4)
                    pdf.set_font("Helvetica", "B", 13)
                    pdf.cell(0, 8, "Executive Summary", ln=True)
                    pdf.set_font("Helvetica", "", 11)
                    for b in exec_bullets:
                        clean_b = b.replace("**", "").replace("₹", "INR ").encode('latin-1', 'ignore').decode('latin-1')
                        pdf.multi_cell(0, 6, f"- {clean_b}")
                    pdf.ln(3)
                    pdf.set_font("Helvetica", "B", 13)
                    pdf.cell(0, 8, "Detailed Report", ln=True)
                    pdf.set_font("Helvetica", "", 11)
                    clean_text = report_text.replace("₹", "INR ").encode('latin-1', 'ignore').decode('latin-1')
                    pdf.multi_cell(0, 6, clean_text)
                    pdf_bytes = bytes(pdf.output(dest='S'))
                    st.download_button("📄 Download Branded PDF", data=pdf_bytes,
                                        file_name=f"{brand_name}_report.pdf", mime="application/pdf")
                except Exception as pdf_err:
                    st.caption(f"PDF export unavailable ({pdf_err}). Add 'fpdf2' to requirements.txt.")

        # =====================================================================
        # FEEDBACK SECTION 2: INSIDE CSV REPORT BLOCK
        # =====================================================================
        render_feedback_form("feedback_inside_csv")

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")
        st.caption("CSV mein at least ek text column (item/product) aur ek numeric column (revenue) hona chahiye.")
else:
    st.info("💡 Upar CSV upload karein ya 'Try Demo Data' button dabayein.")

# =============================================================================
# FAQ SECTION
# =============================================================================
st.markdown("---")
st.markdown("### ❓ Frequently Asked Questions")
with st.expander("Meri CSV upload nahi ho rahi / error aa raha hai?"):
    st.write("Confirm karein file **.csv** format mein hai, aur usme kam se kam ek product/item column aur ek revenue/price column ho.")
with st.expander("Mera CSV mein Date/Payment/Category column nahi hai, kya report milegi?"):
    st.write("Haan! Tool aapki CSV mein jo bhi columns available hain unhi ke hisaab se report banata hai.")
with st.expander("Mera data safe hai kya?"):
    st.write("Aapki file sirf is session ke liye process hoti hai. Koi login/database nahi hai, isliye data permanently store nahi hota.")

st.markdown("---")
st.success("🚀 **Built with ❤️ by Anirudh (Student Developer)**")
