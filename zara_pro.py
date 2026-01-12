import streamlit as st
import yfinance as yf
import pandas as pd
import os

# 1. إعدادات المتصفح (جعل الواجهة عريضة ومناسبة للهاتف)
st.set_page_config(page_title="Zara Fast Radar", layout="wide")
DATA_FILE = "zara_fast_data.csv"

# 2. وظيفة التنسيق اللوني (أخضر=قوة، أصفر=مراقبة، أحمر=خطر)
def color_strength(val):
    if val >= 70: color = '#27ae60' # أخضر
    elif val >= 40: color = '#f1c40f' # أصفر
    else: color = '#e74c3c' # أحمر
    return f'background-color: {color}; color: black; font-weight: bold'

st.title("🦅 رادار زارا - أقوى 10 أسهم قيادية")
st.markdown("---")

# 3. قائمة الأسهم الـ 10 الأكثر نشاطاً في السوق المصري
TICKERS = [
    "COMI.CA", "FWRY.CA", "SWDY.CA", "ABUK.CA", "MFPC.CA",
    "ETEL.CA", "TMGH.CA", "ADIB.CA", "ORAS.CA", "ARCC.CA"
]

# 4. زر بدء العمل
if st.button("🚀 ابدأ المسح والتحليل الفوري"):
    results = []
    progress_bar = st.progress(0)
    placeholder = st.empty() # مكان تحديث البيانات حياً
    
    for idx, sym in enumerate(TICKERS):
        try:
            # جلب بيانات شهر كامل (فحص سريع)
            df = yf.download(sym, period="1mo", interval="1d", progress=False)
            if not df.empty:
                curr = round(float(df['Close'].iloc[-1]), 2)
                h_max = df['High'].max()
                l_min = df['Low'].min()
                
                # معادلة القوة (كلما زادت النسبة، زاد احتمال الارتداد للأعلى)
                score = round(((h_max - curr) / (h_max - l_min)) * 100) if h_max != l_min else 0
                
                results.append({
                    "الرمز": sym.replace(".CA", ""),
                    "السعر": curr,
                    "القوة %": score,
                    "أعلى سعر": round(float(h_max), 2)
                })
                
                # تحديث الجدول أمامك فوراً (استخدام dataframe ليكون أخف)
                live_df = pd.DataFrame(results).sort_values(by="القوة %", ascending=False)
                placeholder.dataframe(live_df.style.applymap(color_strength, subset=['القوة %']), use_container_width=True)
        except:
            continue
        
        # تحديث شريط التقدم
        progress_bar.progress((idx + 1) / len(TICKERS))
    
    if results:
        pd.DataFrame(results).to_csv(DATA_FILE, index=False)
        st.success("✅ تم تحديث البيانات بنجاح!")

# 5. عرض آخر فحص تم حفظه (لحماية التطبيق من الخطأ الأحمر)
if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
    st.write("### 📊 آخر فحص تم حفظه في ذاكرة الهاتف:")
    try:
        df_saved = pd.read_csv(DATA_FILE)
        st.dataframe(
            df_saved.sort_values(by="القوة %", ascending=False).style.applymap(color_strength, subset=['القوة %']), 
            use_container_width=True
        )
    except:
        st.warning("يرجى الضغط على زر المسح لتحديث البيانات.")

# زر لمسح الذاكرة إذا رغبت
if st.sidebar.button("🗑️ مسح الذاكرة المؤقتة"):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
        st.rerun()
