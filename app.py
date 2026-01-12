import streamlit as st
import yfinance as yf
import pandas as pd
import os
import time

# إعدادات الصفحة
st.set_page_config(page_title="Zara Pro Shield", layout="wide")
DATA_FILE = "zara_final_data.csv"

# وظيفة التلوين الذكي
def apply_color(val):
    if val >= 70: color = '#27ae60' # أخضر (قوي)
    elif val >= 30: color = '#f1c40f' # أصفر (محايد)
    else: color = '#e74c3c' # أحمر (ضعيف)
    return f'background-color: {color}; color: black; font-weight: bold'

st.title("🦅 رادار زارا برو - نسخة الهاتف")

# قائمة الأسهم المختارة
TICKERS = ["COMI.CA", "FWRY.CA", "SWDY.CA", "ABUK.CA", "ETEL.CA", "ADIB.CA", "MFPC.CA", "ARCC.CA", "TMGH.CA", "ORAS.CA"]

if st.button("🔄 بدء المسح والتحليل اللوني"):
    storage = []
    progress = st.progress(0)
    table_placeholder = st.empty()
    
    for idx, sym in enumerate(TICKERS):
        try:
            df = yf.download(sym, period="1mo", interval="1d", progress=False)
            if not df.empty:
                curr = round(float(df['Close'].iloc[-1]), 2)
                h_max = df['High'].max()
                l_min = df['Low'].min()
                # حساب القوة
                score = round(((h_max - curr) / (h_max - l_min)) * 100) if h_max != l_min else 0
                
                storage.append({
                    "الرمز": sym.replace(".CA", ""),
                    "السعر": curr,
                    "القوة %": score,
                    "أعلى شهر": round(float(h_max), 2)
                })
                # تحديث العرض حياً
                table_placeholder.table(pd.DataFrame(storage).sort_values(by="القوة %", ascending=False).style.applymap(apply_color, subset=['القوة %']))
        except: continue
        progress.progress((idx + 1) / len(TICKERS))
    
    if storage:
        # حفظ البيانات فقط إذا كانت القائمة غير فارغة
        pd.DataFrame(storage).to_csv(DATA_FILE, index=False)
        st.success("✅ تم تحديث جميع البيانات بنجاح!")

# --- معالجة خطأ EmptyDataError ---
if os.path.exists(DATA_FILE):
    try:
        # التأكد من أن الملف ليس فارغاً قبل قراءته
        if os.path.getsize(DATA_FILE) > 0:
            st.write("### 📊 آخر فحص تم حفظه:")
            df_saved = pd.read_csv(DATA_FILE)
            st.table(df_saved.sort_values(by="القوة %", ascending=False).style.applymap(apply_color, subset=['القوة %']))
        else:
            st.info("⚠️ ملف البيانات فارغ، يرجى تشغيل المسح من الزر أعلاه.")
    except Exception as e:
        st.error("حدث خطأ أثناء قراءة البيانات. يرجى الضغط على زر المسح مرة أخرى.")

if st.button("🗑️ مسح الذاكرة وإعادة الضبط"):
    if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
    st.rerun()
