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
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 16px;
        font-weight: 600;
    }
    .stButton>button, .stDownloadButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# OPTIONAL AI (Gemini free tier) — key read from Streamlit Secrets, hidden from users
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
st.markdown('<p class="sub-header">Apni sales CSV upload karo, seconds mein real profit, loss alerts aur AI-powered report paao — bilkul free.</p>', unsafe_allow_html=True)

with st.expander("ℹ️ Ye tool kya karta hai? (About)"):
    st.write(
        "Ye tool aapke sales data (CSV file) ko analyze karke asli profit calculate karta hai — sirf revenue nahi, "
        "balki product cost, platform fees, shipping, GST aur ad spend jaise sab expenses kaat kar. Ye batata hai "
        "kaunse products loss mein hain, kaunsa platform format (Amazon/Meesho/Shopify) detect hua hai, aur returns/RTO "
        "orders ko automatically exclude karke accurate numbers deta hai. Koi Excel formula ya coding knowledge nahi chahiye."
    )

st.markdown("---")

business_mode = st.selectbox(
    "Aap Kaunsa Business Karte Ho? Select Karo 👇",
    ["Amazon / Flipkart Seller", "Instagram / Boutique Store", "Dropshipping / Shopify", "Small Local Business / Kirana"],
    index=0
)
st.caption(
    "ℹ️ Business type report ki language/labels adjust karta hai. Column detection sab modes ke liye same "
    "generic logic use karta hai — 'Detected Columns' panel mein hamesha verify karein."
)
st.markdown("---")

# --- HOW IT WORKS ---
st.markdown("### 🛠️ How to use this tool")
col_step1, col_step2, col_step3 = st.columns(3)
with col_step1:
    st.info("##### 1. Upload CSV\nApni sales sheet ko .CSV format mein upload karein, ya neeche demo data try karein.")
with col_step2:
    st.info(f"##### 2. Auto-Detect for {business_mode}\nTool aapke columns se Fees/GST/Ad/Cost/Platform detect karega.")
with col_step3:
    st.info("##### 3. Get Profit Report\nReal profit, Loss Alert, interactive charts aur AI Report dekho.")

st.write("")

# =============================================================================
# DATA SOURCE: real upload OR built-in demo dataset
# =============================================================================
@st.cache_data
def get_demo_data():
    return pd.DataFrame({
        "Product Name": ["Cotton Kurti", "Denim Jacket", "Silk Saree", "Cotton Kurti", "Leather Bag",
                          "Denim Jacket", "Printed Tshirt", "Silk Saree", "Leather Bag", "Printed Tshirt"],
        "Order Status": ["Delivered", "Delivered", "RTO", "Delivered", "Delivered",
                          "Cancelled", "Delivered", "Delivered", "Delivered", "Delivered"],
        "Sale Price": [899, 2499, 4999, 899, 1899, 2499, 499, 4999, 1899, 499],
        "Quantity": [3, 1, 1, 2, 1, 1, 5, 2, 2, 4],
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
    """Convert messy numeric column to float while PRESERVING negative signs."""
    s = series.astype(str).str.strip()
    s = s.str.replace(r'[^\d.\-]', '', regex=True)
    return pd.to_numeric(s, errors='coerce').fillna(0)


def detect_platform(columns):
    """Signature-based guess only — verify with the detected-columns panel."""
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
    st.info("🎮 Demo data loaded — ye sample sales data hai taaki aap tool try kar sakein bina apni CSV ke.")
elif uploaded_file is not None:
    active_df = load_csv(uploaded_file)
    active_filename = uploaded_file.name

if active_df is not None:
    try:
        df = active_df.copy()
        if df.empty:
            st.warning("⚠️ File mein koi rows nahi hain.")
            st.stop()

        # --- PROGRESS STEPS ---
        progress_bar = st.progress(0, text="Reading file...")
        time.sleep(0.2)
        progress_bar.progress(25, text="Detecting columns...")
        time.sleep(0.2)

        original_cols = list(df.columns)
        clean_cols = [str(c).strip().lower() for c in original_cols]
        col_mapping = dict(zip(clean_cols, original_cols))

        platform = detect_platform(original_cols)

        item_keywords = ['item', 'product', 'name', 'sku', 'title', 'particulars', 'description']
        rev_keywords = ['revenue', 'sales', 'amount', 'grand total', 'net sales', 'turnover', 'total', 'price', 'rate', 'sale price', 'mrp']
        qty_keywords = ['quantity', 'qty', 'units', 'sold', 'count', 'volume', 'pieces']
        cost_keywords = ['product cost', 'purchase price', 'purchase cost', 'kharid', 'buy price', 'cogs']
        fee_keywords = ['referral fee', 'closing fee', 'commission', 'platform fee', 'marketplace fee', 'fee']
        ship_keywords = ['shipping', 'courier', 'delivery charge', 'logistics']
        gst_keywords = ['gst', 'tax', 'vat']
        ad_keywords = ['ad spend', 'advertising', 'fb ads', 'marketing spend', 'ppc']
        status_keywords = ['order status', 'status', 'reason for credit entry', 'shipment status']

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

        progress_bar.progress(50, text="Cleaning data & handling returns...")
        time.sleep(0.2)

        for col in [rev_col, qty_col, cost_col, fee_col, ship_col, gst_col, ad_col]:
            if col and col in df.columns:
                df[col] = clean_numeric_column(df[col])

        # RTO / Return exclusion
        excluded_count = 0
        if status_col:
            status_lower = df[status_col].astype(str).str.lower()
            is_returned = status_lower.apply(lambda x: any(k in x for k in RETURN_STATUS_VALUES))
            excluded_count = int(is_returned.sum())
            df = df[~is_returned].copy()

        progress_bar.progress(75, text="Calculating profit & margins...")
        time.sleep(0.2)

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
        time.sleep(0.3)
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
            st.write(f"- **Order Status (for RTO/Return exclusion):** `{status_col if status_col else 'Not found'}`")
            if status_col and excluded_count > 0:
                st.info(f"ℹ️ Excluded **{excluded_count}** returned/cancelled/RTO orders from calculations.")

        if not has_expense_data:
            st.warning("⚠️ Cost/fee/shipping/GST/ad column detect nahi hui — 'Real Profit' abhi sirf revenue ke barabar hai, actual expenses subtract nahi hue.")

        # =====================================================================
        # TABS: Overview / Product Detail / Report
        # =====================================================================
        tab_overview, tab_products, tab_report = st.tabs(["📈 Overview", "📦 Product Detail", "📑 Report"])

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
            except ImportError:
                st.caption("Interactive charts ke liye 'plotly' package chahiye (requirements.txt mein add karein).")
                st.bar_chart(df.groupby(item_col)['Real_Profit'].sum().sort_values(ascending=False))

        with tab_products:
            st.markdown("#### 📦 Full Product-wise Breakdown")
            display_df = prod_summary.reset_index().rename(columns={
                item_col: "Product", rev_col: "Revenue", 'Real_Profit': "Profit", qty_col: "Units Sold", 'Margin_%': "Margin %"
            })
            st.dataframe(display_df.sort_values("Profit", ascending=False), use_container_width=True)
            st.caption("Table ko column header pe click karke sort kar sakte ho.")

        with tab_report:
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
        # FEEDBACK SECTION
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
# FAQ SECTION
# =============================================================================
st.markdown("---")
st.markdown("### ❓ Frequently Asked Questions")
with st.expander("Meri CSV upload nahi ho rahi / error aa raha hai?"):
    st.write("Confirm karein file **.csv** format mein hai (Excel se 'Save As CSV' kar sakte ho), aur usme kam se kam ek product/item column aur ek revenue/price column ho.")
with st.expander("Kaunse platforms support karte ho?"):
    st.write("Amazon, Flipkart, Meesho, Shopify, ya koi bhi generic sales CSV — tool auto-detect karne ki koshish karta hai, but 'Detected Columns' panel mein hamesha verify kar lein.")
with st.expander("Mera data safe hai kya?"):
    st.write("Aapki file sirf is session ke liye process hoti hai analysis ke liye. Filhal koi login/database nahi hai, isliye data kahin permanently store nahi hota.")
with st.expander("Real Profit revenue jaisa hi kyun dikh raha hai?"):
    st.write("Iska matlab hai aapki CSV mein cost/fee/GST/shipping jaisa koi expense column detect nahi hua. In columns ko add karke dobara upload karein accurate profit ke liye.")

st.markdown("---")
st.success("🚀 **Built with ❤️ by Anirudh (Student Developer)**")
