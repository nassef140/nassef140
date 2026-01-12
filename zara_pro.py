import streamlit as st
import yfinance as yf
import pandas as pd
import os

# إعدادات الهاتف
st.set_page_config(page_title="Zara Pro Radar", layout="wide")
DATA_FILE = "zara_data_final.csv"

# وظيفة الألوان (أخضر=قوي، أحمر=ضعيف)
def apply_color(val):
    color = '#27ae60' if val >= 70 else '#f1c40f' if val >= 40 else '#e74c3c'
    return f'background-color: {color}; color: black; font-weight: bold'

st.title("🦅 رادار زارا برو - السوق المصري")

# قائمة الأسهم
TICKERS = ["COMI.CA", "FWRY.CA", "SWDY.CA", "ABUK.CA", "ETEL.CA", "ADIB.CA"]

if st.button("🚀 ابدأ المسح والتحليل"):
    storage = []
    progress_bar = st.progress(0)
    table_placeholder = st.empty()
    
    for idx, sym in enumerate(TICKERS):
        try:
            df = yf.download(sym, period="1mo", progress=False)
            if not df.empty:
                curr = round(float(df['Close'].iloc[-1]), 2)
                h_max = df['High'].max()
                l_min = df['Low'].min()
                # معادلة القوة
                score = round(((h_max - curr) / (h_max - l_min)) * 100) if h_max != l_min else 0
                
                storage.append({"الرمز": sym.replace(".CA", ""), "السعر": curr, "القوة %": score})
                # تحديث الجدول حياً
                table_placeholder.table(pd.DataFrame(storage).style.applymap(apply_color, subset=['القوة %']))
        except: continue
        progress_bar.progress((idx + 1) / len(TICKERS))
    
    if storage:
        pd.DataFrame(storage).to_csv(DATA_FILE, index=False)
        st.success("✅ اكتمل التحديث!")

# عرض البيانات القديمة بأمان
if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
    st.write("### 📊 آخر نتائج مسجلة:")
    st.table(pd.read_csv(DATA_FILE).style.applymap(apply_color, subset=['القوة %']))
