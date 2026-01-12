import streamlit as st
import yfinance as yf
import pandas as pd
import os
import time

# إعدادات النسخة النهائية المستقرة
DATA_FILE = "zara_egypt_final.csv"
st.set_page_config(page_title="Zara Pro Final", layout="wide")

# القائمة الشاملة لفرسان السوق المصري (يمكنك إضافة أي رمز لاحقاً)
TICKERS = [
    "COMI.CA", "FWRY.CA", "SWDY.CA", "ABUK.CA", "ETEL.CA", "BTEL.CA", "MFPC.CA",
    "TMGH.CA", "ESRS.CA", "ORAS.CA", "EKHO.CA", "ADIB.CA", "CIEB.CA", "ORWE.CA",
    "PHDC.CA", "MNHD.CA", "HELI.CA", "ELSH.CA", "ARCC.CA", "UNIT.CA", "CCAP.CA",
    "RAYA.CA", "TAQA.CA", "ISPH.CA", "RMDA.CA", "EGAL.CA", "ALCN.CA", "DSMC.CA",
    "MPRC.CA", "HRHO.CA", "ATQA.CA", "AMOC.CA", "SKPC.CA", "GBCO.CA", "RAQT.CA"
]

st.title("🦅 رادار زارا برو - النسخة النهائية")

if st.button("🔄 بدء المسح الشامل (تحديث حي)"):
    storage = []
    status = st.empty()
    table_placeholder = st.empty() # لتحديث الجدول سهم بسهم
    
    for idx, sym in enumerate(TICKERS):
        status.info(f"⏳ فحص السهم {idx+1} من {len(TICKERS)}: {sym}")
        try:
            # طلب البيانات الأساسية ليوم واحد لسرعة الاستجابة
            df = yf.download(sym, period="1mo", interval="1d", progress=False)
            if not df.empty:
                curr = round(float(df['Close'].iloc[-1]), 2)
                h_max = round(float(df['High'].max()), 2)
                
                # حساب "قوة الفرصة" (قرب السعر من القاع الشهري)
                l_min = df['Low'].min()
                score = round(((h_max - curr) / (h_max - l_min)) * 100) if h_max != l_min else 0
                
                storage.append({
                    "الرمز": sym.replace(".CA", ""), 
                    "السعر": curr, 
                    "أعلى سعر": h_max,
                    "القوة %": score
                })
                
                # عرض الجدول محدثاً أمامك فوراً
                table_placeholder.table(pd.DataFrame(storage).sort_values(by="القوة %", ascending=False))
        except:
            continue
        
        # استراحة بسيطة كل 10 أسهم لراحة معالج الهاتف
        if (idx + 1) % 10 == 0:
            time.sleep(1)

    # حفظ النسخة النهائية بعد الانتهاء
    pd.DataFrame(storage).to_csv(DATA_FILE, index=False)
    status.success("✅ اكتمل المسح الشامل بنجاح!")

# عرض البيانات المخزنة عند فتح التطبيق
if os.path.exists(DATA_FILE):
    st.sidebar.success("📊 توجد بيانات محفوظة")
    if st.sidebar.button("🗑️ مسح الذاكرة"):
        os.remove(DATA_FILE)
        st.rerun()
