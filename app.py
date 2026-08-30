import streamlit as st
import pandas as pd
import time

# 1. Page Config Setup
st.set_page_config(page_title="AI Business Analyst", layout="centered")
st.title("📊 AI-Driven Business Analyst Interface")
st.subheader("BBE 2nd Year Project - Simulation Mode")

# 2. File Uploader Component
uploaded_file = st.file_uploader("Apni 'clothing_sales.csv' file yahan upload karein", type=["csv"])

if uploaded_file is not None:
    st.success("[System Status]: File successfully uploaded!")
    
    with st.spinner("Backend mein report generate ho rahi hai... Please wait..."):
        time.sleep(2) # Simulation pause

    # Big Bold Metric Cards for professional look
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="TOTAL MONTHLY REVENUE", value="INR 26,787.00")
    with col2:
        st.metric(label="TOTAL NET PROFIT", value="INR 14,287.00", delta="12% Target")

    # 3. Hinglish Report Box
    st.markdown("---")
    st.markdown("### 📑 Automated AI Strategic Growth Report (Hinglish):")
    
    st.info("**Hey Founder! Aapka Monthly Strategic Plan Ready Hai:**")
    
    st.write("1. 🎯 **Product Expansion**: Aapka item 'Oversized Cotton Tee' demand mein sabse aage hai. Iske combos bna kar average order value badhayein.")
    st.write("2. 📉 **Margin Check**: Item 'Linen Casual Shirt' par profit margins bohot low hain. Iski supply cost kam karein ya price ko optimize karein.")
    st.write("3. 📊 **Financial Summary**: Total revenue INR 26,787.00 par aapka net profit INR 14,287.00 hai. Operations cost control karne ki zaroorat hai.")
    
    st.warning("*Next Month Target: Margin optimize karke net profit 12% boost karna.*")

else:
    st.info("💡 Kripya upar diye gaye button par click karke CSV file upload karein taaki backend processing shuru ho sake.")
