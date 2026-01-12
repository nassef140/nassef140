import streamlit as st
import yfinance as yf
import pandas as pd
import os

# إعدادات الهاتف
st.set_page_config(page_title="Zara Pro Radar", layout="wide")

st.title("🦅 رادار زارا برو - مصر")

# قائمة الأسهم المختارة (يمكنك زيادتها)
TICKERS = ["COMI.CA", "FWRY.CA", "SWDY.CA", "ABUK.CA", "ETEL.CA"]

if st.button("🚀 ابدأ المسح والتحليل"):
    results = []
    # مكان عرض الجدول الحي
    table_placeholder = st.empty()
    
    for sym in TICKERS:
        try:
            df = yf.download(sym, period="1mo", progress=False)
            if not df.empty:
                last_p = round(float(df['Close'].iloc[-1]), 2)
                results.append({"الرمز": sym.replace(".CA", ""), "السعر": last_p})
                # عرض الجدول سهم بسهم
                table_placeholder.table(pd.DataFrame(results))
        except: continue
    
    if results:
        pd.DataFrame(results).to_csv("zara_db.csv", index=False)
        st.success("✅ تم تحديث البيانات بنجاح!")

# عرض البيانات القديمة لضمان عدم تعليق الصفحة
if os.path.exists("zara_db.csv") and os.path.getsize("zara_db.csv") > 0:
    st.write("📊 آخر نتائج محفوظة:")
    st.dataframe(pd.read_csv("zara_db.csv"))
