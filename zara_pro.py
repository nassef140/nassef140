import streamlit as st
import yfinance as yf
import pandas as pd
import os
import time

# إعدادات واجهة الهاتف
st.set_page_config(page_title="Zara Egypt Pro", layout="wide")
DATA_FILE = "egypt_market_data.csv"

# وظيفة التنسيق اللوني (نظام الإشارات الضوئية)
def color_score(val):
    if val >= 70: color = '#27ae60' # أخضر (منطقة شراء قوية)
    elif val >= 40: color = '#f1c40f' # أصفر (منطقة مراقبة)
    else: color = '#e74c3c' # أحمر (منطقة قمة/جني أرباح)
    return f'background-color: {color}; color: black; font-weight: bold'

st.title("🦅 رادار زارا برو - السوق المصري")

# القائمة الشاملة لأهم 50 سهم (EGX 30 + الأسهم النشطة)
TICKERS = [
    "COMI.CA", "FWRY.CA", "SWDY.CA", "ABUK.CA", "MFPC.CA", "ETEL.CA", "TMGH.CA",
    "ADIB.CA", "ORAS.CA", "EKHO.CA", "ESRS.CA", "AMOC.CA", "SKPC.CA", "PHDC.CA",
    "HELI.CA", "MNHD.CA", "JUFO.CA", "CIEB.CA", "ORWE.CA", "ARCC.CA", "BTEL.CA",
    "CCAP.CA", "RAYA.CA", "ISPH.CA", "RMDA.CA", "EGAL.CA", "HRHO.CA", "EFIC.CA",
    "POUL.CA", "EDIT.CA", "IDRE.CA", "BINV.CA", "ALCN.CA", "DSMC.CA", "MTIE.CA",
    "AUTO.CA", "GBCO.CA", "DSCW.CA", "UNIT.CA", "LCSW.CA", "ACGC.CA", "ASCM.CA",
    "AJWA.CA", "PORT.CA", "AMER.CA", "ELSH.CA", "ATQA.CA", "DAPH.CA", "MICH.CA"
]

if st.button("🔄 بدء المسح الشامل لـ 50 سهم"):
    storage = []
    progress = st.progress(0)
    status_text = st.empty()
    table_placeholder = st.empty()
    
    for idx, sym in enumerate(TICKERS):
        status_text.text(f"⏳ فحص {idx+1}/{len(TICKERS)}: {sym}")
        try:
            # جلب بيانات شهر كامل لتحليل القوة
            df = yf.download(sym, period="1mo", interval="1d", progress=False)
            if not df.empty:
                curr = round(float(df['Close'].iloc[-1]), 2)
                h_max = df['High'].max()
                l_min = df['Low'].min()
                
                # معادلة رادار زارا: قياس بعد السعر عن القاع الشهري
                score = round(((h_max - curr) / (h_max - l_min)) * 100) if h_max != l_min else 0
                
                storage.append({
                    "الرمز": sym.replace(".CA", ""),
                    "السعر الحالي": curr,
                    "القوة %": score,
                    "أعلى سعر (شهر)": round(float(h_max), 2)
                })
                
                # ترتيب الجدول تلقائياً ليظهر القوي في الأعلى
                live_df = pd.DataFrame(storage).sort_values(by="القوة %", ascending=False)
                table_placeholder.table(live_df.style.applymap(color_score, subset=['القوة %']))
        except:
            continue
        
        progress.progress((idx + 1) / len(TICKERS))
    
    if storage:
        pd.DataFrame(storage).to_csv(DATA_FILE, index=False)
        st.success("✅ تم تحديث كافة الأسهم بنجاح!")

# عرض البيانات المحفوظة عند فتح التطبيق مجدداً
if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
    st.write("---")
    st.subheader("📊 آخر نتائج الفحص المحفوظة")
    df_saved = pd.read_csv(DATA_FILE)
    st.table(df_saved.sort_values(by="القوة %", ascending=False).style.applymap(color_score, subset=['القوة %']))
