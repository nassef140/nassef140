import streamlit as st
import yfinance as yf
import pandas as pd
import os

# نسخة الرادار التفاعلية (صديقة للهاتف)
DATA_FILE = "zara_live_db.csv"
st.set_page_config(page_title="Zara Live Radar", layout="wide")

# القائمة (يمكنك زيادتها لـ 200)
TICKERS = ["COMI.CA", "FWRY.CA", "SWDY.CA", "ABUK.CA", "ETEL.CA", "RAQT.CA"] # أضف بقية الرموز هنا

st.title("🦅 رادار زارا برو - التحديث الحي")

if st.button("🔄 بدء المسح التفاعلي"):
    storage = []
    # مسح الملف القديم للبدء من جديد
    if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
    
    status = st.empty()
    table_placeholder = st.empty() # مكان مخصص لتحديث الجدول حياً
    
    for idx, sym in enumerate(TICKERS):
        status.info(f"⏳ فحص: {sym} ({idx+1}/{len(TICKERS)})")
        try:
            df = yf.download(sym, period="1mo", progress=False)
            if not df.empty:
                curr = round(float(df['Close'].iloc[-1]), 2)
                storage.append({"الرمز": sym.replace(".CA", ""), "السعر": curr})
                
                # تحديث الجدول أمام عينك فوراً مع كل سهم
                table_placeholder.table(pd.DataFrame(storage))
        except: continue

    # الحفظ النهائي
    pd.DataFrame(storage).to_csv(DATA_FILE, index=False)
    st.success("✅ اكتمل المسح الشامل!")

# عرض البيانات المخزنة في حال إعادة فتح التطبيق
if os.path.exists(DATA_FILE) and not st.session_state.get('running'):
    st.write("### 📊 آخر بيانات مسجلة:")
    st.dataframe(pd.read_csv(DATA_FILE), use_container_width=True)
