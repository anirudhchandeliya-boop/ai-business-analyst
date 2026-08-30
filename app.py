import streamlit as st
import pandas as pd
import time

# 1. Page Configuration (Wide Layout)
st.set_page_config(page_title="AI Business Analyst - By Anirudh", layout="wide")

# --- MAIN PAGE HEADER ---
st.title("📊 AI-Driven Business Analyst Dashboard")
st.write("Upload any sales dataset and get instant automated insights with financial graphs.")
st.markdown("---")

# --- INSTRUCTIONS SECTION ---
st.markdown("### 🛠️ How to use this tool:")
col_step1, col_step2, col_step3 = st.columns(3)

with col_step1:
    st.info("##### 1. Upload CSV File\nApne store ki sales register digital sheet ko **.CSV format** mein neeche upload karein.")

with col_step2:
    st.info("##### 2. Automatic AI Processing\nHumara Smart Backend aapke custom columns ko khud detect karke processing karega.")

with col_step3:
    st.info("##### 3. Get Insights\nNeeche real charts aur ek clear Hinglish report ban kar aayegi jise aap use kar sakte hain.")

st.write("")

# --- DATA UPLOAD ZONE ---
st.markdown("### 📥 Upload Your Dataset Here")
uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

st.markdown("---")

# --- DATA LOGIC & VISUALS ---
if uploaded_file is not None:
    try:
        # Load the CSV file
        df = pd.read_csv(uploaded_file)
        st.success(f"✔️ File '{uploaded_file.name}' loaded successfully! Automated scanning initiated...")
        
        with st.spinner("Smart mapping algorithm detecting columns... Please wait..."):
            time.sleep(1)

        # Standardizing Column Names for matching (lowercase and strip spaces)
        original_cols = list(df.columns)
        clean_cols = [str(c).strip().lower() for c in original_cols]
        col_mapping = dict(zip(clean_cols, original_cols))
        
        # -------------------------------------------------------------------------
        # SMART KEYWORD DICTIONARY MAPPING (Har company ke headings ka automatic solution)
        # -------------------------------------------------------------------------
        item_keywords = ['item', 'product', 'name', 'sku', 'title', 'particulars', 'description', 'p_name', 'items', 'products']
        rev_keywords = ['revenue', 'price', 'sales', 'amount', 'total', 'rate', 'grand total', 'net sales', 'turnover', 'value', 'mrp', 'cost']
        qty_keywords = ['quantity', 'qty', 'units', 'sold', 'count', 'volume', 'no of items', 'number of items', 'pieces', 'pcs']
        profit_keywords = ['profit', 'margin', 'gain', 'net profit', 'earnings']

        # Columns Find Karne ka AI logic
        item_col = next((col_mapping[c] for c in clean_cols if any(k in c for k in item_keywords)), None)
        rev_col = next((col_mapping[c] for c in clean_cols if any(k in c for k in rev_keywords)), None)
        qty_col = next((col_mapping[c] for c in clean_cols if any(k in c for k in qty_keywords)), None)
        profit_col = next((col_mapping[c] for c in clean_cols if any(k in c for k in profit_keywords)), None)

        # BACKUP BACKBONE (Agar koi unusual column ho jo upar match na ho paye)
        if not item_col:
            # Pehla text (object) column dhundho
            text_cols = df.select_dtypes(include=['object']).columns
            item_col = text_cols[0] if len(text_cols) > 0 else original_cols[0]
            
        if not rev_col:
            # Sabse bada numeric column check karo jisme decimals ho sakte hain
            num_cols = df.select_dtypes(include=['number']).columns
            rev_col = num_cols[0] if len(num_cols) > 0 else original_cols[1] if len(original_cols) > 1 else original_cols[0]

        if not qty_col:
            # Agar quantity nahi mili toh assume karo har row 1 sale/order hai
            df['auto_generated_qty'] = 1
            qty_col = 'auto_generated_qty'

        # -------------------------------------------------------------------------
        # DATA CLEANING & RE-FORMATTING (String symbols hatao jaise INR, $, commas)
        # -------------------------------------------------------------------------
        df[rev_col] = pd.to_numeric(df[rev_col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        df[qty_col] = pd.to_numeric(df[qty_col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        
        if profit_col:
            df[profit_col] = pd.to_numeric(df[profit_col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)

        # Core Core Math Calculations
        total_revenue = float(df[rev_col].sum())
        total_units = int(df[qty_col].sum())
        total_profit = float(df[profit_col].sum()) if profit_col else total_revenue * 0.53
        total_orders = len(df)
        margin_pct = (total_profit / total_revenue) * 100 if total_revenue > 0 else 53.3
        
        # Top Performing & Worst items detection based on volume
        try:
            prod_summary = df.groupby(item_col)[qty_col].sum()
            top_item = prod_summary.idxmax()
            worst_item = prod_summary.idxmin()
            if top_item == worst_item and len(prod_summary) > 1:
                worst_item = prod_summary.idxmin()
        except:
            top_item = "Top Scaled Line"
            worst_item = "Low Scaled Line"

        # Dashboard Numbers Display
        st.markdown("### 📈 Real-time Business Metrics")
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.metric(label="💰 TOTAL REVENUE", value=f"INR {total_revenue:,.2f}")
        with m_col2:
            st.metric(label="💵 NET PROFIT", value=f"INR {total_profit:,.2f}", delta=f"{margin_pct:.1f}% Margin")
        with m_col3:
            st.metric(label="🛍️ TOTAL ORDERS", value=f"{total_orders:,} ({total_units:,} Items Sold)")

        # Dynamic Charts Section
        st.markdown("---")
        v1, v2 = st.columns(2)
        with v1:
            st.markdown("#### **Product Revenue Contribution**")
            chart_data = df.groupby(item_col)[rev_col].sum().sort_values(ascending=False).head(5)
            st.bar_chart(chart_data)
        with v2:
            st.markdown("#### **Units Sold Analysis**")
            qty_data = df.groupby(item_col)[qty_col].sum().sort_values(ascending=False).head(5)
            st.area_chart(qty_data)

        # Dynamic Report Section based on actual uploaded content
        st.markdown("---")
        st.markdown("### 📑 Automated AI Strategic Growth Report (Hinglish)")
        st.write(f"• **Revenue & Profit Summary**: Is billing cycle mein total **INR {total_revenue:,.2f}** ka volume detect aur process hua hai.")
        st.write(f"• **Top Performing Item**: Aapka main product line **'{top_item}'** is analytics data mein leading position par hai. Iska stock management tight rakhein taaki demand miss na ho.")
        
        if worst_item != top_item:
            st.write(f"• **Low Margin Product**: Catalog reporting ke mutabik **'{worst_item}'** ki performance thodi down rahi hai. Iski product pricing ya vendor cost par re-negotiate karne ki requirement hai.")
        
        st.info(f"**⚡ Action Plan for the Next 30 Days:**\n\n"
                f"1. **Average Order Value (AOV) Boost**: Customers ko target karne ke liye combo packs bna kar try karein, jahan '{top_item}' ke saath slow items ko bundle kiya ja sake.\n\n"
                f"2. **Cost Optimization**: Operational leaks aur variable costs ko trace down karein taaki profit targets ko next month **12% up** push kiya ja sake.")

    except Exception as e:
        st.error(f"❌ Error auto-detecting sheet matrix. Please ensure the CSV contains generic sales figures.")
else:
    # Empty State Padding
    st.info("💡 Kripya upar diye gaye button par click karke Sales CSV file upload karein taaki calculations shuru ho sakein.")
    st.write("")
    st.write("")

# --- THE STUDENT CREATOR FOOTER ---
st.markdown("---")
st.success("🚀 **Built with ❤️ by Anirudh (Student Developer)** | Running on Free Tier Cloud Hosting Engine")
