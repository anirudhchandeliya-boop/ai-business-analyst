import streamlit as st
import pandas as pd
import numpy as np
import time

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(page_title="AI Business Analyst - By Anirudh", layout="wide")

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
# PAYWALL — reads valid unlock codes from Secrets (comma-separated), e.g.
# UNLOCK_CODES = "ABC123,XYZ789"
# This is a REAL gate: full data is not rendered at all until a valid code is entered.
# =============================================================================
try:
    VALID_CODES = [c.strip() for c in st.secrets["UNLOCK_CODES"].split(",")]
except Exception:
    VALID_CODES = []

if "unlocked" not in st.session_state:
    st.session_state.unlocked = False

# --- HEADER ---
st.title("📊 AI-Driven Business Analyst Dashboard")
st.markdown("#### Ek Tool - Sab Business Ke Liye")

business_mode = st.selectbox(
    "Aap Kaunsa Business Karte Ho? Select Karo 👇",
    ["Amazon / Flipkart Seller", "Instagram / Boutique Store", "Dropshipping / Shopify", "Small Local Business / Kirana"],
    index=0
)
st.caption(
    "ℹ️ Business type abhi report ki language/labels adjust karta hai. Column detection (fees/cost/GST) "
    "sab modes ke liye same generic logic use karta hai — agar aapke CSV mein platform-specific column "
    "names hain (jaise 'Referral Fee'), unhe neeche 'Detected columns' mein verify zaroor karein."
)
st.markdown("---")

# --- INSTRUCTIONS ---
st.markdown("### 🛠️ How to use this tool:")
col_step1, col_step2, col_step3 = st.columns(3)
with col_step1:
    st.info("##### 1. Upload CSV\nApni sales sheet ko .CSV format mein upload karein.")
with col_step2:
    st.info(f"##### 2. Auto-Detect for {business_mode}\nTool aapke columns se Fees/GST/Ad/Cost detect karega.")
with col_step3:
    st.info("##### 3. Get Profit Report\nReal profit, Loss Alert aur Action Plan dekho.")

st.write("")
st.markdown("### 📥 Upload Your Dataset Here")
uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])
st.markdown("---")


@st.cache_data
def load_csv(file):
    return pd.read_csv(file)


def clean_numeric_column(series):
    """Convert messy numeric column to float while PRESERVING negative signs
    (refunds, discounts, adjustments should not lose their '-')."""
    s = series.astype(str).str.strip()
    s = s.str.replace(r'[^\d.\-]', '', regex=True)
    return pd.to_numeric(s, errors='coerce').fillna(0)


if uploaded_file is not None:
    try:
        df = load_csv(uploaded_file)
        if df.empty:
            st.warning("⚠️ Uploaded file has no rows.")
            st.stop()

        st.success(f"✔️ File '{uploaded_file.name}' loaded! {business_mode} mode pe scanning...")
        with st.spinner(f"Smart mapping for {business_mode}..."):
            time.sleep(0.4)

        original_cols = list(df.columns)
        clean_cols = [str(c).strip().lower() for c in original_cols]
        col_mapping = dict(zip(clean_cols, original_cols))

        # ---------------------------------------------------------------
        # KEYWORD DICTIONARIES
        # FIX: 'cost' generic keyword removed and cost/shipping/fee keywords
        # made mutually exclusive so the same column can't be claimed by two
        # categories (this was causing double-counting of the same expense).
        # ---------------------------------------------------------------
        item_keywords = ['item', 'product', 'name', 'sku', 'title', 'particulars', 'description']
        rev_keywords = ['revenue', 'sales', 'amount', 'grand total', 'net sales', 'turnover', 'total', 'price', 'rate', 'sale price', 'mrp']
        qty_keywords = ['quantity', 'qty', 'units', 'sold', 'count', 'volume', 'pieces']
        cost_keywords = ['product cost', 'purchase price', 'purchase cost', 'kharid', 'buy price', 'cogs']
        fee_keywords = ['referral fee', 'closing fee', 'commission', 'platform fee', 'marketplace fee', 'fee']
        ship_keywords = ['shipping', 'courier', 'delivery charge', 'logistics']
        gst_keywords = ['gst', 'tax', 'vat']
        ad_keywords = ['ad spend', 'advertising', 'fb ads', 'marketing spend', 'ppc']

        # FIX: claim columns in a strict priority order so no column gets
        # matched by more than one category.
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

        # ---------------------------------------------------------------
        # TRANSPARENCY PANEL — shows exactly which column was used for what,
        # so a wrong auto-detection can be caught before trusting the numbers.
        # ---------------------------------------------------------------
        with st.expander("🔍 Detected columns (verify before trusting the numbers)"):
            st.write(f"- **Item/Product:** `{item_col}`" + (" _(auto-guessed)_" if item_auto else ""))
            st.write(f"- **Revenue:** `{rev_col}`" + (" _(auto-guessed)_" if rev_auto else ""))
            st.write(f"- **Quantity:** `{qty_col}`" + (" _(defaulted to 1/row)_" if qty_auto else ""))
            st.write(f"- **Product Cost:** `{cost_col if cost_col else 'Not found — treated as ₹0'}`")
            st.write(f"- **Platform Fee/Commission:** `{fee_col if fee_col else 'Not found — treated as ₹0'}`")
            st.write(f"- **Shipping:** `{ship_col if ship_col else 'Not found — treated as ₹0'}`")
            st.write(f"- **GST/Tax:** `{gst_col if gst_col else 'Not found — treated as ₹0'}`")
            st.write(f"- **Ad Spend:** `{ad_col if ad_col else 'Not found — treated as ₹0'}`")
            st.caption("Agar koi column galat detect hua ho ya missing ho, apni CSV mein us column ka naam clearer rakhein aur dobara upload karein.")

        # CLEANING — negative signs preserved
        for col in [rev_col, qty_col, cost_col, fee_col, ship_col, gst_col, ad_col]:
            if col and col in df.columns:
                df[col] = clean_numeric_column(df[col])

        # CORE CALCULATION
        df['Real_Cost'] = df[cost_col] if cost_col else 0
        df['Real_Fee'] = df[fee_col] if fee_col else 0
        df['Real_Ship'] = df[ship_col] if ship_col else 0
        df['Real_GST'] = df[gst_col] if gst_col else 0
        df['Real_Ad'] = df[ad_col] if ad_col else 0

        df['Real_Profit'] = df[rev_col] - df['Real_Cost'] - df['Real_Fee'] - df['Real_Ship'] - df['Real_GST'] - df['Real_Ad']

        # FIX: guard against division by zero producing inf instead of a clean 0
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

        # FIX: loss is now based on ACTUAL negative profit, not an arbitrary
        # ₹20 cutoff that misclassified high-revenue/low-margin items and
        # missed genuinely unprofitable low-revenue items.
        loss_products = prod_summary[prod_summary['Real_Profit'] < 0]

        # METRICS
        st.markdown("### 📈 Real-time Business Metrics")
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.metric(label="💰 TOTAL REVENUE", value=f"INR {total_revenue:,.0f}")
        with m_col2:
            if has_expense_data:
                st.metric(label="💵 REAL PROFIT (Asli Munafa)", value=f"INR {total_profit:,.0f}", delta=f"{margin_pct:.1f}% Margin")
            else:
                st.metric(label="💵 REAL PROFIT", value="Incomplete")
                st.caption("Koi cost/fee/GST column nahi mili — profit sirf revenue ke barabar dikh raha hai, real nahi.")
        with m_col3:
            st.metric(label="🛍️ TOTAL ORDERS", value=f"{total_orders}")
        with m_col4:
            st.metric(label="🚨 LOSS PRODUCTS", value=f"{len(loss_products)} Items")

        if not has_expense_data:
            st.warning("⚠️ Is CSV mein koi cost/fee/shipping/GST/ad column detect nahi hui. 'Real Profit' abhi sirf revenue ke barabar hai — actual expenses subtract nahi hue. Loss Alert bhi accurate nahi hoga jab tak expense data na ho.")

        # LOSS ALERT
        if len(loss_products) > 0:
            st.error(f"🚨 LOSS ALERT: {business_mode} me {len(loss_products)} product loss me hain (negative profit)!")
            st.dataframe(loss_products[[rev_col, 'Real_Profit', 'Margin_%']].head(3 if not st.session_state.unlocked else 20))
            st.write(f"**Action:** '{worst_item}' ka price badhao ya cost/fee re-negotiate karo — ispe sabse zyada loss ho raha hai.")

        # ---------------------------------------------------------------
        # REAL PAYWALL — actually restricts data, not just a message.
        # Full loss table, full chart, and full detailed report only render
        # once a valid unlock code (set in Secrets: UNLOCK_CODES) is entered.
        # ---------------------------------------------------------------
        st.markdown("---")
        if not st.session_state.unlocked:
            st.warning("🔒 Free version: sirf Top 3 products aur summary dikh rahe hain. Full report unlock karne ke liye code daalein.")
            pay_links = {
                "Amazon / Flipkart Seller": ("₹499", "https://rzp.io/l/YOUR-LINK-499"),
                "Instagram / Boutique Store": ("₹299", "https://rzp.io/l/YOUR-LINK-299"),
                "Dropshipping / Shopify": ("₹399", "https://rzp.io/l/YOUR-LINK-399"),
                "Small Local Business / Kirana": ("₹199", "https://rzp.io/l/YOUR-LINK-199"),
            }
            amount, link = pay_links[business_mode]
            col_pay1, col_pay2 = st.columns(2)
            with col_pay1:
                st.link_button(f"🔓 Pay {amount} to Unlock", link)
                entered_code = st.text_input("Payment ke baad mila unlock code yahan daalein")
                if st.button("Unlock Report"):
                    if entered_code.strip() in VALID_CODES and VALID_CODES:
                        st.session_state.unlocked = True
                        st.rerun()
                    else:
                        st.error("❌ Invalid code. Payment ke baad sahi code milega.")
            with col_pay2:
                st.info("Pay karke screenshot Insta pe bhejo, unlock code milega.")
            top_n = 3
        else:
            st.success("✔️ Full report unlocked!")
            top_n = len(prod_summary)

        # CHARTS (respect paywall — only top 3 shown if locked)
        v1, v2 = st.columns(2)
        with v1:
            st.markdown("#### **Product Real Profit Contribution**")
            chart_data = df.groupby(item_col)['Real_Profit'].sum().sort_values(ascending=False).head(top_n if top_n < 6 else 5)
            st.bar_chart(chart_data)
        with v2:
            st.markdown("#### **Paisa Kaha Kata? (Fee Breakdown)**")
            if has_expense_data:
                fee_breakup = {
                    "Product Cost": df['Real_Cost'].sum(),
                    "Fees/Commission": df['Real_Fee'].sum() + df['Real_Ad'].sum(),
                    "Shipping/Courier": df['Real_Ship'].sum(),
                    "GST/Tax": df['Real_GST'].sum(),
                    "Aapka Profit": total_profit
                }
                fee_df = pd.DataFrame(list(fee_breakup.items()), columns=['Type', 'Amount'])
                fee_df = fee_df[fee_df['Amount'] > 0]
                st.bar_chart(fee_df.set_index('Type'))
            else:
                st.caption("Fee breakdown ke liye cost/fee/GST/shipping/ad column chahiye — abhi CSV mein nahi mili.")

        # ---------------------------------------------------------------
        # REPORT — real AI (Gemini, free tier via Secrets) if configured,
        # otherwise clearly-labelled rule-based report.
        # ---------------------------------------------------------------
        st.markdown("---")

        def build_data_summary():
            lines = [
                f"Business type: {business_mode}",
                f"Total revenue: INR {total_revenue:,.0f}",
                f"Real profit: INR {total_profit:,.0f} ({margin_pct:.1f}% margin)" if has_expense_data else "Expense data incomplete — profit is not net of costs.",
                f"Total orders: {total_orders}",
                f"Top item by profit: {top_item}",
                f"Loss-making items: {len(loss_products)}",
            ]
            return "\n".join(lines)

        ai_used = False
        if AI_AVAILABLE and st.session_state.unlocked:
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
                    st.write(response.text)
                    ai_used = True
            except Exception as ai_err:
                st.warning(f"AI generation failed ({ai_err}), showing rule-based report.")

        if not ai_used:
            st.markdown(f"### 📑 {business_mode} ke liye Report (Rule-Based, Hinglish)")
            if not st.session_state.unlocked:
                st.caption("Full detailed report unlock karne ke baad milegi.")
            st.write(f"• **Revenue Summary**: Is cycle me total **INR {total_revenue:,.0f}** ka business hua.")
            if has_expense_data:
                st.write(f"• **Asli Munafa**: Sab kharche kaat ke asli profit **INR {total_profit:,.0f} ({margin_pct:.1f}% margin)** hai.")
            else:
                st.write("• **Asli Munafa**: Expense columns (cost/fee/GST/shipping) na milne ki wajah se accurate profit calculate nahi ho saka.")
            st.write(f"• **Hero Product**: **'{top_item}'** sabse zyada profit de raha hai.")
            if st.session_state.unlocked and len(loss_products) > 0:
                st.write(f"• **Danger Product**: **'{worst_item}'** pe loss ho raha hai — pricing ya cost dobara check karein.")
                st.success(
                    f"**⚡ Action Plan for {business_mode} - Next 30 Days:**\n\n"
                    f"1. **AOV Boost**: '{top_item}' ke saath slow items ka combo banao.\n\n"
                    f"2. **Cost Cut**: {fee_col or 'Fees'} aur {ship_col or 'Shipping'} check karo — agar zyada hai toh vendor/rate renegotiate karo.\n\n"
                    "3. **Track Weekly**: Har hafte report re-run karke trend dekhein."
                )

        # DOWNLOAD
        st.markdown("---")
        st.download_button("📥 Download Summary as TXT", data=build_data_summary(),
                            file_name="business_report_summary.txt", mime="text/plain")

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")
        st.caption("CSV mein at least ek text column (item/product) aur ek numeric column (revenue) hona chahiye.")
else:
    st.info("💡 Upar Business Type select karke CSV upload karein.")
    st.write("")

st.markdown("---")
st.success("🚀 **Built with ❤️ by Anirudh (Student Developer)** | 1 Tool for 4 Businesses | DM for Premium: Insta @anirudh")
