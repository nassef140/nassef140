import streamlit as st
import yfinance as yf
import pandas as pd
import os
import time

# إعدادات النسخة النهائية للهاتف
DATA_FILE = "zara_full_mobile.csv"
st.set_page_config(page_title="Zara Pro Mobile", layout="wide")

# القائمة الموسعة (أهم أسهم السوق المصري)
TICKERS = [
    "ARCC.CA", "UNIT.CA", "COMI.CA", "FWRY.CA", "ETEL.CA", "ABUK.CA", "MFPC.CA", 
    "BTEL.CA", "SWDY.CA", "TMGH.CA", "ESRS.CA", "ORAS.CA", "EKHO.CA", "CIEB.CA", 
    "ADIB.CA", "PHDC.CA", "HELI.CA", "MNHD.CA", "ELSH.CA", "AMER.CA", "CCAP.CA", 
    "RAYA.CA", "TAQA.CA", "ISPH.CA", "RMDA.CA", "EGAL.CA", "ALCN.CA", "DSMC.CA"
    # يمكنك إضافة أي رمز آخر هنا بنفس التنسيق
]

st.title("🦅 منظومة زارا برو - السوق المصري")

if st.button("🔄 تحديث الـ 200 سهم (مزامنة آمنة)"):
    storage = []
    progress = st.progress(0)
    status = st.empty()
    
    for idx, sym in enumerate(TICKERS):
        status.text(f"⏳ فحص السهم {idx+1} من {len(TICKERS)}: {sym}")
        try:
            # استخدام interval يومي لسرعة التحميل على الهاتف
            df = yf.download(sym, period="1mo", interval="1d", progress=False)
            if not df.empty:
                curr = df['Close'].iloc[-1]
                # حساب بسيط لقوة السهم (أعلى سعر في شهر)
                h_max = df['High'].max()
                storage.append({
                    "الرمز": sym.replace(".CA", ""), 
                    "السعر": round(float(curr), 2),
                    "أعلى شهر": round(float(h_max), 2)
                })
        except: continue
        
        # استراحة قصيرة جداً كل 5 أسهم لتجنب تعليق المتصفح
        if (idx + 1) % 5 == 0: time.sleep(1)
        progress.progress((idx + 1) / len(TICKERS))
    
    if storage:
        pd.DataFrame(storage).to_csv(DATA_FILE, index=False)
        st.success("✅ اكتمل تحديث كافة الأسهم!")

# عرض النتائج
if os.path.exists(DATA_FILE):
    st.subheader("📊 تقرير الفرص المتاحة")
    df_final = pd.read_csv(DATA_FILE)
    # ترتيب الأسهم من الأرخص للأغلى أو حسب القوة
    st.dataframe(df_final.sort_values(by="السعر"), use_container_width=True)
else:
    st.info("اضغط على زر التحديث بالأعلى لجلب بيانات السوق.")
