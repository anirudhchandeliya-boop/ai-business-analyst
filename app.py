import streamlit as st
import pandas as pd
import numpy as np
import time

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
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; padding: 8px 16px; font-weight: 600; }
    .stButton>button, .stDownloadButton>button { border-radius: 8px; font-weight: 600; }
    .exec-summary {
        background: #fffbeb; border-left: 4px solid #f59e0b; border-radius: 8px;
        padding: 14px 18px; color: #1a1a1a;
    }
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    AI_AVAILABLE = True
except Exception:
    GEMINI_KEY = None
    AI_AVAILABLE = False

# =============================================================================
# HEADER
# =============================================================================
st.markdown('<p class="main-header">📊 AI-Driven Business Analyst Dashboard</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Apni sales CSV upload karo, seconds mein real profit, trends aur AI-powered report paao — bilkul free.</p>', unsafe_allow_html=True)

with st.expander("ℹ️ Ye tool kya karta hai? (About)"):
    st.write(
        "Ye tool aapke sales data (CSV file) ko analyze karke asli profit calculate karta hai — cost, fees, shipping, "
        "GST aur ad spend kaat kar. Jitne bhi columns aapki CSV mein honge (date, payment mode, category, discount, "
        "return status), tool unhe use karke utni hi detailed report banayega. Koi column missing ho toh sirf wo "
        "specific section skip hota hai — baaki poori report aapko milti hai, kabhi report dena mana nahi karte."
    )

st.markdown("---")

business_mode = st.selectbox(
    "Aap Kaunsa Business Karte Ho? Select Karo 👇",
    ["Amazon / Flipkart Seller", "Instagram / Boutique Store", "Dropshipping / Shopify", "Small Local Business / Kirana"],
    index=0
)
st.caption("ℹ️ Business type sirf report ki language/labels adjust karta hai. Column detection sabke liye same hai — 'Detected Columns' panel mein verify karein.")
st.markdown("---")

st.markdown("### 🛠️ How to use this tool")
col_step1, col_step2, col_step3 = st.columns(3)
with col_step1:
    st.info("##### 1. Upload CSV\nApni sales sheet ko .CSV format mein upload karein, ya demo data try karein.")
with col_step2:
    st.info(f"##### 2. Auto-Detect for {business_mode}\nTool jo bhi columns milein (date, payment, category, fees) unhe use karega.")
with col_step3:
    st.info("##### 3. Get Full Report\nJitna data utni detailed report — kabhi report incomplete nahi milegi.")

st.write("")

# =============================================================================
# DEMO DATA
# =============================================================================
@st.cache_data
def get_demo_data():
    dates = pd.date_range("2026-08-01", periods=10, freq="3D")
    return pd.DataFrame({
        "Order Date": dates,
        "Product Name": ["Cotton Kurti", "Denim Jacket", "Silk Saree", "Cotton Kurti", "Leather Bag",
                          "Denim Jacket", "Printed Tshirt", "Silk Saree", "Leather Bag", "Printed Tshirt"],
        "Category": ["Ethnic Wear", "Western Wear", "Ethnic Wear", "Ethnic Wear", "Accessories",
                     "Western Wear", "Western Wear", "Ethnic Wear", "Accessories", "Western Wear"],
        "Order Status": ["Delivered", "Delivered", "RTO", "Delivered", "Delivered",
                          "Cancelled", "Delivered", "Delivered", "Delivered", "Delivered"],
        "Payment Mode": ["Prepaid", "COD", "COD", "Prepaid", "Prepaid", "COD", "Prepaid", "COD", "Prepaid", "COD"],
        "Sale Price": [899, 2499, 4999, 899, 1899, 2499, 499, 4999, 1899, 499],
        "Quantity": [3, 1, 1, 2, 1, 1, 5, 2, 2, 4],
        "Discount": [50, 0, 200, 50, 0, 0, 20, 200, 0, 20],
        "Product Cost": [400, 1200, 2500, 400, 900, 1200, 200, 2500, 900, 200],
        "Referral Fee": [90, 250, 500, 90, 190, 250, 50, 500, 190, 50],
        "Shipping": [60, 90, 120, 60, 80, 90, 40, 120, 80, 40],
        "GST": [45, 125, 250, 45, 95, 125, 25, 250, 95, 25],
    })


st.markdown("### 📥 Upload Your Dataset Here")
col_up1, col_up2 = st.columns([3, 1])
with col_up1:
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])
with col_up2:
    st.write("")
    st.write("")
    use_demo = st.button("🎮 Try Demo Data")

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
    return "Generic / Unknown"


RETURN_STATUS_VALUES = ["rto", "return", "returned", "cancelled", "canceled", "refund", "refunded", "lost", "damaged"]

active_df = None
active_filename = None

if use_demo:
    active_df = get_demo_data()
    active_filename = "demo_data.csv"
    st.info("🎮 Demo data loaded — sample data hai taaki aap tool try kar sakein.")
elif uploaded_file is not None:
    active_df = load_csv(uploaded_file)
    active_filename = uploaded_file.name

if active_df is not None:
    try:
        df = active_df.copy()
        if df.empty:
            st.warning("⚠️ File mein koi rows nahi hain.")
            st.stop()

        progress_bar = st.progress(0, text="Reading file...")
        time.sleep(0.15)
        progress_bar.progress(20, text="Detecting columns...")
        time.sleep(0.15)

        original_cols = list(df.columns)
        clean_cols = [str(c).strip().lower() for c in original_cols]
        col_mapping = dict(zip(clean_cols, original_cols))
        platform = detect_platform(original_cols)

        # ---------------- Keyword dictionaries ----------------
        item_keywords = ['item', 'product', 'name', 'sku', 'title', 'particulars', 'description']
        rev_keywords = ['revenue', 'sales', 'amount', 'grand total', 'net sales', 'turnover', 'total', 'price', 'rate', 'sale price', 'mrp']
        qty_keywords = ['quantity', 'qty', 'units', 'sold', 'count', 'volume', 'pieces']
        cost_keywords = ['product cost', 'purchase price', 'purchase cost', 'kharid', 'buy price', 'cogs']
        fee_keywords = ['referral fee', 'closing fee', 'commission', 'platform fee', 'marketplace fee', 'fee']
        ship_keywords = ['shipping', 'courier', 'delivery charge', 'logistics']
        gst_keywords = ['gst', 'tax', 'vat']
        ad_keywords = ['ad spend', 'advertising', 'fb ads', 'marketing spend', 'ppc']
        status_keywords = ['order status', 'status', 'reason for credit entry', 'shipment status']
        date_keywords = ['date', 'order date', 'purchase date', 'created at', 'timestamp']
        payment_keywords = ['payment mode', 'payment method', 'payment type']
        category_keywords = ['category', 'sub category', 'segment', 'department']
        discount_keywords = ['discount', 'coupon', 'promo code', 'promo']

        used_cols = set()

        def find_col(keywords):
            for c in clean_cols:
                real_col = col_mapping[c]
                if real_col in used_cols:
                    continue
                if any(k in c for k in keywords):
                    used_cols.add(real_col)
                    return real_col
            return None

        item_col = find_col(item_keywords)
        rev_col = find_col(rev_keywords)
        qty_col = find_col(qty_keywords)
        cost_col = find_col(cost_keywords)
        fee_col = find_col(fee_keywords)
        ship_col = find_col(ship_keywords)
        gst_col = find_col(gst_keywords)
        ad_col = find_col(ad_keywords)
        status_col = find_col(status_keywords)
        date_col = find_col(date_keywords)
        payment_col = find_col(payment_keywords)
        category_col = find_col(category_keywords)
        discount_col = find_col(discount_keywords)

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

        progress_bar.progress(40, text="Cleaning data & handling returns...")
        time.sleep(0.15)

        for col in [rev_col, qty_col, cost_col, fee_col, ship_col, gst_col, ad_col, discount_col]:
            if col and col in df.columns:
                df[col] = clean_numeric_column(df[col])

        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

        excluded_count = 0
        if status_col:
            status_lower = df[status_col].astype(str).str.lower()
            is_returned = status_lower.apply(lambda x: any(k in x for k in RETURN_STATUS_VALUES))
            excluded_count = int(is_returned.sum())
            df_returns_only = df[is_returned].copy()
            df = df[~is_returned].copy()
        else:
            df_returns_only = pd.DataFrame()

        progress_bar.progress(65, text="Calculating profit & margins...")
        time.sleep(0.15)

        df['Real_Cost'] = df[cost_col] if cost_col else 0
        df['Real_Fee'] = df[fee_col] if fee_col else 0
        df['Real_Ship'] = df[ship_col] if ship_col else 0
        df['Real_GST'] = df[gst_col] if gst_col else 0
        df['Real_Ad'] = df[ad_col] if ad_col else 0
        df['Real_Profit'] = df[rev_col] - df['Real_Cost'] - df['Real_Fee'] - df['Real_Ship'] - df['Real_GST'] - df['Real_Ad']
        df['Margin_%'] = np.where(df[rev_col] != 0, (df['Real_Profit'] / df[rev_col] * 100), 0)
        df['Margin_%'] = df['Margin_%'].round(2)

        total_revenue = float(df[rev_col].sum())
        total_profit = float(df['Real_Profit'].sum())
        total_units = int(df[qty_col].sum())
        total_orders = len(df)
        margin_pct = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        has_expense_data = any([cost_col, fee_col, ship_col, gst_col, ad_col])

        prod_summary = df.groupby(item_col).agg(
            **{rev_col: (rev_col, 'sum'), 'Real_Profit': ('Real_Profit', 'sum'),
               qty_col: (qty_col, 'sum'), 'Margin_%': ('Margin_%', 'mean')}
        ).sort_values(by='Real_Profit', ascending=False)

        top_item = prod_summary.index[0] if len(prod_summary) > 0 else "N/A"
        worst_item = prod_summary.index[-1] if len(prod_summary) > 0 else "N/A"
        loss_products = prod_summary[prod_summary['Real_Profit'] < 0]

        progress_bar.progress(100, text="Done!")
        time.sleep(0.2)
        progress_bar.empty()

        st.success(f"✔️ '{active_filename}' processed successfully! ({business_mode} mode)")

        with st.expander("🔍 Detected columns & platform (verify before trusting numbers)"):
            st.write(f"- **Detected platform format:** `{platform}`")
            st.write(f"- **Item/Product:** `{item_col}`" + (" _(auto-guessed)_" if item_auto else ""))
            st.write(f"- **Revenue:** `{rev_col}`" + (" _(auto-guessed)_" if rev_auto else ""))
            st.write(f"- **Quantity:** `{qty_col}`" + (" _(defaulted to 1/row)_" if qty_auto else ""))
            st.write(f"- **Product Cost:** `{cost_col if cost_col else 'Not found — treated as ₹0'}`")
            st.write(f"- **Platform Fee/Commission:** `{fee_col if fee_col else 'Not found — treated as ₹0'}`")
            st.write(f"- **Shipping:** `{ship_col if ship_col else 'Not found — treated as ₹0'}`")
            st.write(f"- **GST/Tax:** `{gst_col if gst_col else 'Not found — treated as ₹0'}`")
            st.write(f"- **Ad Spend:** `{ad_col if ad_col else 'Not found — treated as ₹0'}`")
            st.write(f"- **Order Status:** `{status_col if status_col else 'Not found'}`")
            st.write(f"- **Order Date:** `{date_col if date_col else 'Not found'}`")
            st.write(f"- **Payment Mode:** `{payment_col if payment_col else 'Not found'}`")
            st.write(f"- **Category:** `{category_col if category_col else 'Not found'}`")
            st.write(f"- **Discount:** `{discount_col if discount_col else 'Not found'}`")
            if status_col and excluded_count > 0:
                st.info(f"ℹ️ Excluded **{excluded_count}** returned/cancelled/RTO orders from calculations.")

        if not has_expense_data:
            st.warning("⚠️ Cost/fee/shipping/GST/ad column detect nahi hui — 'Real Profit' abhi sirf revenue ke barabar hai.")

        # =====================================================================
        # TABS
        # =====================================================================
        tab_overview, tab_trends, tab_products, tab_report = st.tabs(
            ["📈 Overview", "📅 Trends & Insights", "📦 Product Detail", "📑 Report"]
        )

        # ---------------- OVERVIEW ----------------
        with tab_overview:
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("💰 TOTAL REVENUE", f"INR {total_revenue:,.0f}")
            with m2:
                if has_expense_data:
                    st.metric("💵 REAL PROFIT", f"INR {total_profit:,.0f}", delta=f"{margin_pct:.1f}% Margin")
                else:
                    st.metric("💵 REAL PROFIT", "Incomplete")
            with m3:
                st.metric("🛍️ TOTAL ORDERS", f"{total_orders} ({total_units} units)")
            with m4:
                st.metric("🚨 LOSS PRODUCTS", f"{len(loss_products)} Items")

            if len(loss_products) > 0:
                st.error(f"🚨 LOSS ALERT: {len(loss_products)} product(s) loss mein hain!")
                st.dataframe(loss_products[[rev_col, 'Real_Profit', 'Margin_%']], use_container_width=True)
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
                    st.markdown("#### Paisa Kaha Kata? (Fee Breakdown)")
                    if has_expense_data:
                        fee_breakup = {
                            "Product Cost": df['Real_Cost'].sum(),
                            "Fees/Commission": df['Real_Fee'].sum() + df['Real_Ad'].sum(),
                            "Shipping": df['Real_Ship'].sum(),
                            "GST/Tax": df['Real_GST'].sum(),
                            "Your Profit": max(total_profit, 0)
                        }
                        fee_df = pd.DataFrame(list(fee_breakup.items()), columns=['Type', 'Amount'])
                        fee_df = fee_df[fee_df['Amount'] > 0]
                        fig2 = px.pie(fee_df, names='Type', values='Amount', hole=0.4)
                        fig2.update_layout(height=380)
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.caption("Fee breakdown ke liye cost/fee/GST/shipping/ad column chahiye.")
                PLOTLY_OK = True
            except ImportError:
                st.caption("Interactive charts ke liye 'plotly' package chahiye (requirements.txt mein add karein).")
                st.bar_chart(df.groupby(item_col)['Real_Profit'].sum().sort_values(ascending=False))
                PLOTLY_OK = False

        # ---------------- TRENDS & INSIGHTS (new) ----------------
        with tab_trends:
            any_insight_shown = False

            # --- Date-based trend ---
            if date_col:
                any_insight_shown = True
                st.markdown("#### 📅 Revenue Trend Over Time")
                trend_df = df.dropna(subset=[date_col]).groupby(df[date_col].dt.date)[rev_col].sum().reset_index()
                trend_df.columns = ["Date", "Revenue"]
                if PLOTLY_OK and len(trend_df) > 0:
                    import plotly.express as px
                    fig_trend = px.line(trend_df, x="Date", y="Revenue", markers=True)
                    fig_trend.update_layout(height=350)
                    st.plotly_chart(fig_trend, use_container_width=True)
                elif len(trend_df) > 0:
                    st.line_chart(trend_df.set_index("Date"))
                if len(trend_df) >= 2:
                    first_half = trend_df.iloc[:len(trend_df)//2]['Revenue'].sum()
                    second_half = trend_df.iloc[len(trend_df)//2:]['Revenue'].sum()
                    if first_half > 0:
                        change = ((second_half - first_half) / first_half) * 100
                        trend_word = "growth 📈" if change > 0 else "decline 📉"
                        st.info(f"ℹ️ Period ke doosre half mein revenue mein **{abs(change):.1f}% {trend_word}** dikha pehle half ke comparison mein.")
                st.markdown("---")
            else:
                st.caption("📅 Revenue trend dekhne ke liye CSV mein ek Date/Order Date column chahiye — abhi nahi mila.")

            # --- Payment mode / COD-RTO breakdown ---
            if payment_col:
                any_insight_shown = True
                st.markdown("#### 💳 Payment Mode Breakdown")
                pay_summary = df.groupby(payment_col).agg(
                    Orders=(payment_col, 'count'), Revenue=(rev_col, 'sum')
                ).reset_index()
                st.dataframe(pay_summary, use_container_width=True)

                if status_col and len(df_returns_only) > 0:
                    all_orders_by_payment = active_df.groupby(payment_col).size() if payment_col in active_df.columns else None
                    if all_orders_by_payment is not None:
                        returned_by_payment = df_returns_only.groupby(payment_col).size()
                        rto_rate = (returned_by_payment / all_orders_by_payment * 100).fillna(0).round(1)
                        st.write("**RTO/Return Rate by Payment Mode:**")
                        st.dataframe(rto_rate.reset_index().rename(columns={0: "RTO Rate %"}), use_container_width=True)
                        high_rto = rto_rate[rto_rate > 20]
                        if len(high_rto) > 0:
                            st.warning(f"⚠️ **{', '.join(high_rto.index.astype(str))}** mein RTO rate 20% se zyada hai — isse profit kaafi kam ho sakta hai.")
                st.markdown("---")
            else:
                st.caption("💳 Payment mode insights ke liye CSV mein 'Payment Mode' column chahiye — abhi nahi mila.")

            # --- Category-wise summary ---
            if category_col:
                any_insight_shown = True
                st.markdown("#### 🗂️ Category-wise Performance")
                cat_summary = df.groupby(category_col).agg(
                    Revenue=(rev_col, 'sum'), Profit=('Real_Profit', 'sum'), Orders=(category_col, 'count')
                ).sort_values("Profit", ascending=False).reset_index()
                st.dataframe(cat_summary, use_container_width=True)
                st.markdown("---")
            else:
                st.caption("🗂️ Category-wise breakdown ke liye CSV mein 'Category' column chahiye — abhi nahi mila.")

            # --- Discount impact ---
            if discount_col:
                any_insight_shown = True
                st.markdown("#### 🏷️ Discount Impact")
                total_discount = float(df[discount_col].sum())
                discount_pct_of_revenue = (total_discount / total_revenue * 100) if total_revenue > 0 else 0
                st.write(f"Total discount diya gaya: **INR {total_discount:,.0f}** ({discount_pct_of_revenue:.1f}% of revenue)")
                st.markdown("---")
            else:
                st.caption("🏷️ Discount impact ke liye CSV mein 'Discount' column chahiye — abhi nahi mila.")

            # --- Pareto (80/20) insight ---
            any_insight_shown = True
            st.markdown("#### 🎯 Pareto Insight (80/20 Rule)")
            pareto_df = prod_summary[[rev_col]].sort_values(rev_col, ascending=False).copy()
            pareto_df['Cumulative %'] = (pareto_df[rev_col].cumsum() / pareto_df[rev_col].sum() * 100).round(1)
            products_for_80 = (pareto_df['Cumulative %'] <= 80).sum() + 1
            total_products = len(pareto_df)
            if total_products > 0:
                pct_products = (products_for_80 / total_products) * 100
                st.info(f"ℹ️ Sirf **{products_for_80} product(s)** ({pct_products:.0f}% of your catalog) aapke **80% revenue** generate kar rahe hain. Inventory aur marketing inhi products pe focus karein.")

            if not any_insight_shown:
                st.info("Zyada insights ke liye apni CSV mein Date, Payment Mode, Category, ya Discount jaisi columns add karke dobara upload karein.")

        # ---------------- PRODUCT DETAIL ----------------
        with tab_products:
            st.markdown("#### 📦 Full Product-wise Breakdown")
            display_df = prod_summary.reset_index().rename(columns={
                item_col: "Product", rev_col: "Revenue", 'Real_Profit': "Profit", qty_col: "Units Sold", 'Margin_%': "Margin %"
            })
            st.dataframe(display_df.sort_values("Profit", ascending=False), use_container_width=True)
            st.caption("Table ko column header pe click karke sort kar sakte ho.")

        # ---------------- REPORT ----------------
        with tab_report:
            # --- Executive Summary ---
            st.markdown("#### 📋 Executive Summary")
            exec_lines = [
                f"**Revenue:** INR {total_revenue:,.0f} across {total_orders} orders" +
                (f", INR {total_profit:,.0f} real profit ({margin_pct:.1f}% margin)." if has_expense_data else " (profit not fully calculable — expense data missing)."),
                f"**Top performer:** '{top_item}'.",
            ]
            if len(loss_products) > 0:
                exec_lines.append(f"**Warning:** {len(loss_products)} product(s) currently operating at a loss, worst being '{worst_item}'.")
            if date_col and 'change' in dir():
                pass
            exec_summary_html = "<br>".join(exec_lines)
            st.markdown(f'<div class="exec-summary">{exec_summary_html}</div>', unsafe_allow_html=True)
            st.markdown("---")

            def build_data_summary():
                lines = [
                    f"Business type: {business_mode}",
                    f"Platform detected: {platform}",
                    f"Total revenue: INR {total_revenue:,.0f}",
                    f"Real profit: INR {total_profit:,.0f} ({margin_pct:.1f}% margin)" if has_expense_data else "Expense data incomplete.",
                    f"Total orders: {total_orders}",
                    f"Top item by profit: {top_item}",
                    f"Loss-making items: {len(loss_products)}",
                ]
                if excluded_count:
                    lines.append(f"Excluded {excluded_count} returned/RTO/cancelled orders.")
                if discount_col:
                    lines.append(f"Total discount given: INR {float(df[discount_col].sum()):,.0f}")
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
                            "the best product and any loss-making products with a fix suggestion, and a 2-3 point "
                            "30-day action plan. Only use the numbers given, do not invent figures.\n\n" + build_data_summary()
                        )
                        model = genai.GenerativeModel("gemini-1.5-flash")
                        response = model.generate_content(prompt)
                        report_text = response.text
                        st.write(report_text)
                        ai_used = True
                except Exception as ai_err:
                    st.warning(f"AI generation failed ({ai_err}), showing rule-based report.")

            if not ai_used:
                st.markdown(f"### 📑 {business_mode} ke liye Report (Rule-Based, Hinglish)")
                report_text = (
                    f"Revenue Summary: Is cycle me total INR {total_revenue:,.0f} ka business hua.\n"
                    + (f"Asli Munafa: Sab kharche kaat ke asli profit INR {total_profit:,.0f} ({margin_pct:.1f}% margin) hai.\n"
                       if has_expense_data else "Asli Munafa: Expense columns na milne ki wajah se accurate profit calculate nahi ho saka.\n")
                    + f"Hero Product: '{top_item}' sabse zyada profit de raha hai.\n"
                )
                st.write(report_text)
                if len(loss_products) > 0:
                    danger_line = f"Danger Product: '{worst_item}' pe loss ho raha hai — pricing ya cost dobara check karein."
                    st.write(danger_line)
                    report_text += danger_line + "\n"
                    action_plan = (
                        f"Action Plan (Next 30 Days):\n"
                        f"1. AOV Boost: '{top_item}' ke saath slow items ka combo banao.\n"
                        f"2. Cost Cut: {fee_col or 'Fees'} aur {ship_col or 'Shipping'} check karo.\n"
                        "3. Track Weekly: Har hafte report re-run karke trend dekhein."
                    )
                    st.success(action_plan)
                    report_text += action_plan

            # --- Break-even calculator ---
            st.markdown("---")
            st.markdown("#### ⚖️ Break-Even Calculator (optional)")
            fixed_costs = st.number_input("Aapke monthly fixed costs kitne hain? (rent, salary, etc — optional, ₹)", min_value=0, step=500)
            if fixed_costs > 0:
                profit_per_unit = (total_profit / total_units) if total_units > 0 else 0
                if profit_per_unit > 0:
                    breakeven_units = fixed_costs / profit_per_unit
                    st.info(f"ℹ️ Break-even ke liye aapko approx **{breakeven_units:.0f} units** bechni hongi (based on current avg profit/unit of INR {profit_per_unit:.1f}).")
                else:
                    st.warning("⚠️ Abhi aapka average profit-per-unit zero ya negative hai, isliye break-even calculate nahi ho sakta — pehle per-unit profit positive karna hoga.")

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
                    pdf.cell(0, 12, brand_name, ln=True)
                    pdf.set_font("Helvetica", "", 10)
                    pdf.cell(0, 8, f"{business_mode}  |  Platform: {platform}", ln=True)
                    pdf.ln(4)
                    pdf.set_font("Helvetica", "B", 13)
                    pdf.cell(0, 8, "Key Metrics", ln=True)
                    pdf.set_font("Helvetica", "", 11)
                    pdf.cell(0, 7, f"Total Revenue: INR {total_revenue:,.0f}", ln=True)
                    pdf.cell(0, 7, f"Real Profit: INR {total_profit:,.0f} ({margin_pct:.1f}% margin)" if has_expense_data else "Real Profit: Not available", ln=True)
                    pdf.cell(0, 7, f"Total Orders: {total_orders}", ln=True)
                    pdf.cell(0, 7, f"Loss-making Items: {len(loss_products)}", ln=True)
                    pdf.ln(4)
                    pdf.set_font("Helvetica", "B", 13)
                    pdf.cell(0, 8, "Report", ln=True)
                    pdf.set_font("Helvetica", "", 11)
                    clean_text = report_text.encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 6, clean_text)
                    pdf_bytes = bytes(pdf.output(dest='S'))
                    st.download_button("📄 Download Branded PDF", data=pdf_bytes,
                                        file_name=f"{brand_name}_report.pdf", mime="application/pdf")
                except Exception as pdf_err:
                    st.caption(f"PDF export unavailable ({pdf_err}). Add 'fpdf2' to requirements.txt.")

        # =====================================================================
        # FEEDBACK
        # =====================================================================
        st.markdown("---")
        st.markdown("### 💬 Aapka Feedback")
        fb_col1, fb_col2 = st.columns(2)
        with fb_col1:
            st.write("Report kaisi lagi?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("👍 Useful"):
                    st.success("Shukriya! Feedback note kar liya.")
            with c2:
                if st.button("👎 Not Useful"):
                    st.info("Batao kya better ho sakta tha — DM karo Insta pe.")
        with fb_col2:
            willingness = st.number_input("Is tool ke liye aap kitna pay karenge? (₹, optional)", min_value=0, step=50)
            if st.button("Submit"):
                st.success(f"Shukriya! Aapka input (₹{willingness}) note kar liya gaya.")

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")
        st.caption("CSV mein at least ek text column (item/product) aur ek numeric column (revenue) hona chahiye.")
else:
    st.info("💡 Upar CSV upload karein ya 'Try Demo Data' button dabayein.")

# =============================================================================
# FAQ
# =============================================================================
st.markdown("---")
st.markdown("### ❓ Frequently Asked Questions")
with st.expander("Meri CSV upload nahi ho rahi / error aa raha hai?"):
    st.write("Confirm karein file **.csv** format mein hai, aur usme kam se kam ek product/item column aur ek revenue/price column ho.")
with st.expander("Agar meri CSV mein Date/Payment/Category column nahi hai?"):
    st.write("Koi baat nahi — jo columns available honge, unhi ke hisaab se report banegi. Extra columns hone par extra insights (trend chart, payment breakdown) apne aap add ho jaate hain, na hone par sirf wo section skip ho jata hai. Poori report kabhi nahi rukti.")
with st.expander("Kaunse platforms support karte ho?"):
    st.write("Amazon, Flipkart, Meesho, Shopify, ya koi bhi generic sales CSV — tool auto-detect karne ki koshish karta hai, 'Detected Columns' panel mein verify kar lein.")
with st.expander("Mera data safe hai kya?"):
    st.write("Aapki file sirf is session ke liye process hoti hai. Filhal koi login/database nahi hai, isliye data permanently store nahi hota.")
with st.expander("Real Profit revenue jaisa hi kyun dikh raha hai?"):
    st.write("Iska matlab hai aapki CSV mein cost/fee/GST/shipping jaisa koi expense column detect nahi hua. Add karke dobara upload karein.")

st.markdown("---")
st.success("🚀 **Built with ❤️ by Anirudh (Student Developer)**")
