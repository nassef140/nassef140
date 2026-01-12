import streamlit as st
import yfinance as yf
import pandas as pd
import os

# 1. إعدادات نسخة الهاتف
st.set_page_config(page_title="Zara Pro Mobile", layout="wide")
DATA_FILE = "zara_data.csv"

# 2. وظيفة التلوين (أخضر = شراء، أحمر = خطر)
def color_fix(val):
    color = '#27ae60' if val >= 70 else '#f1c40f' if val >= 40 else '#e74c3c'
    return f'background-color: {color}; color: black; font-weight: bold'

st.title("🦅 رادار زارا - نسخة الهاتف")

# 3. قائمة الأسهم
TICKERS = ["COMI.CA", "FWRY.CA", "SWDY.CA", "ABUK.CA", "ETEL.CA", "ADIB.CA", "MFPC.CA"]

if st.button("🚀 ابدأ المسح الآن"):
    storage = []
    status = st.empty()
    table_placeholder = st.empty()
    
    for idx, sym in enumerate(TICKERS):
        status.info(f"⏳ فحص: {sym}")
        try:
            # جلب البيانات
            df = yf.download(sym, period="1mo", interval="1d", progress=False)
            if not df.empty:
                curr = round(float(df['Close'].iloc[-1]), 2)
                h_max = df['High'].max()
                l_min = df['Low'].min()
                # حساب القوة
                score = round(((h_max - curr) / (h_max - l_min)) * 100) if h_max != l_min else 0
                
                storage.append({"الرمز": sym.replace(".CA", ""), "السعر": curr, "القوة %": score})
                
                # إظهار الجدول فوراً مع كل سهم جديد
                table_placeholder.table(pd.DataFrame(storage).style.applymap(color_fix, subset=['القوة %']))
        except: continue
    
    if storage:
        pd.DataFrame(storage).to_csv(DATA_FILE, index=False)
        st.success("✅ اكتمل المسح!")

# 4. عرض آخر نتائج محفوظة (حتى لو أغلقت الصفحة)
if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
    st.write("### 📊 آخر نتائج مسجلة:")
    st.table(pd.read_csv(DATA_FILE).style.applymap(color_fix, subset=['القوة %']))
