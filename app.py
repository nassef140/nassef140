import streamlit as st
import yfinance as yf
import pandas as pd
import os
import time

# إعدادات بسيطة
DATA_FILE = "zara_mobile_db.csv"
st.set_page_config(page_title="Zara Mobile", layout="wide")

# القائمة (أضف الـ 200 سهم هنا)
TICKERS = ["ARCC.CA", "UNIT.CA", "COMI.CA", "FWRY.CA", "ETEL.CA", "ABUK.CA"]

st.title("🛡️ منظومة زارا - نسخة الهاتف")

# زر البدء
if st.button("🏁 بدء المزامنة الآن"):
    storage = []
    progress = st.progress(0)
    status = st.empty()
    
    for idx, sym in enumerate(TICKERS):
        status.text(f"⏳ جاري فحص: {sym}")
        try:
            # طلب بيانات مبسط جداً لتقليل استهلاك الإنترنت
            df = yf.download(sym, period="1mo", interval="1d", progress=False)
            if not df.empty:
                curr = df['Close'].iloc[-1]
                storage.append({"الرمز": sym, "السعر": round(float(curr), 2)})
        except:
            continue
        progress.progress((idx + 1) / len(TICKERS))
    
    if storage:
        pd.DataFrame(storage).to_csv(DATA_FILE, index=False)
        st.success("✅ اكتمل التحميل! اسحب الشاشة للأسفل لرؤية الجدول.")

# عرض النتائج بدون تعليق
if os.path.exists(DATA_FILE):
    st.subheader("📊 أحدث أسعار السوق")
    df_show = pd.read_csv(DATA_FILE)
    st.dataframe(df_show, use_container_width=True)
else:
    st.info("لا توجد بيانات مخزنة. اضغط على الزر في الأعلى.")
