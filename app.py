import streamlit as st
import yfinance as yf
import pandas as pd
import os
import time

# إعدادات النسخة الاحترافية للهاتف
DATA_FILE = "zara_egypt_pro.csv"
st.set_page_config(page_title="Zara Egypt Pro", layout="wide")

# القائمة الموسعة (أهم أسهم السوق المصري للوصول لـ 200)
TICKERS = [
    "COMI.CA", "FWRY.CA", "SWDY.CA", "TMGH.CA", "ABUK.CA", "MFPC.CA", "ETEL.CA",
    "BTEL.CA", "ESRS.CA", "EKHO.CA", "CIEB.CA", "ADIB.CA", "ORAS.CA", "ORWE.CA",
    "PHDC.CA", "MNHD.CA", "HELI.CA", "ELSH.CA", "PORT.CA", "AMER.CA", "ARCC.CA",
    "UNIT.CA", "LCSW.CA", "ACGC.CA", "ASCM.CA", "AJWA.CA", "RMDA.CA", "ISPH.CA",
    "EGAL.CA", "CCAP.CA", "RAYA.CA", "TAQA.CA", "ALCN.CA", "DSMC.CA", "MPRC.CA",
    "HRHO.CA", "ATQA.CA", "DAPH.CA", "EEII.CA", "MBSC.CA", "EDBM.CA", "QNBA.CA",
    "CANA.CA", "SAUD.CA", "FAIT.CA", "EXPA.CA", "MICH.CA", "SPMD.CA", "DICE.CA",
    "ZMID.CA", "EMFD.CA", "IFAP.CA", "AFMC.CA", "MCQE.CA", "SKPC.CA", "AMOC.CA",
    "KABO.CA", "ORAS.CA", "OIH.CA", "GBCO.CA", "AUTO.CA", "EITP.CA", "RAQT.CA"
    # يمكنك الاستمرار في إضافة أي رمز تتابعه بنفس الصيغة (الرمز + .CA)
]

st.title("🦅 رادار زارا برو - السوق المصري")

if st.button("🔄 تحديث شامل لكافة الأسهم"):
    storage = []
    progress = st.progress(0)
    status = st.empty()
    
    for idx, sym in enumerate(TICKERS):
        status.text(f"⏳ فحص السهم {idx+1} من {len(TICKERS)}: {sym}")
        try:
            # جلب البيانات
            df = yf.download(sym, period="1mo", interval="1d", progress=False)
            if not df.empty:
                curr = df['Close'].iloc[-1]
                h_max = df['High'].max()
                l_min = df['Low'].min()
                # حساب قوة السهم (Score)
                # إذا كان السعر قريب من القاع الشهري، تكون الفرصة أكبر
                score = round(((h_max - curr) / (h_max - l_min)) * 100) if h_max != l_min else 0
                
                storage.append({
                    "الرمز": sym.replace(".CA", ""), 
                    "السعر": round(float(curr), 2),
                    "القوة %": score,
                    "أعلى سعر": round(float(h_max), 2)
                })
        except: continue
        
        # حماية الهاتف من التعليق
        if (idx + 1) % 10 == 0: time.sleep(1)
        progress.progress((idx + 1) / len(TICKERS))
    
    if storage:
        pd.DataFrame(storage).to_csv(DATA_FILE, index=False)
        st.success("✅ تم تحديث الرادار بنجاح!")

# عرض النتائج في جدول احترافي
if os.path.exists(DATA_FILE):
    st.subheader("📊 تحليل الفرص الحالية")
    df_final = pd.read_csv(DATA_FILE)
    
    # فلترة لإظهار الأسهم القوية فقط (أعلى من 70%)
    df_strong = df_final[df_final["القوة %"] > 70].sort_values(by="القوة %", ascending=False)
    
    st.write("🔥 **فرص ذهبية (قريبة من القاع الشهري):**")
    st.table(df_strong.head(10))
    
    st.write("📑 **كافة الأسهم:**")
    st.dataframe(df_final.sort_values(by="الرمز"), use_container_width=True)
else:
    st.info("اضغط على الزر في الأعلى لبدء المسح الشامل.")
