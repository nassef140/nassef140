import streamlit as st
import yfinance as yf
import pandas as pd
import os
from datetime import datetime

# 1. إعدادات الواجهة (تحسين العرض على شاشة الهاتف)
st.set_page_config(page_title="Zara Pro Fast", layout="wide")
DATABASE = "zara_fast_db.csv"

# 2. وظيفة التلوين الذكي (أخضر = منطقة شراء، أحمر = منطقة جني أرباح)
def color_fix(val):
    if val >= 70: color = '#27ae60' # أخضر
    elif val >= 40: color = '#f1c40f' # أصفر
    else: color = '#e74c3c' # أحمر
    return f'background-color: {color}; color: black; font-weight: bold'

st.title("🛡️ منظومة زارا برو - الإصدار النهائي")
st.markdown(f"🕒 **توقيت القاهرة الآن:** {datetime.now().strftime('%H:%M:%S')}")

# 3. قائمة الـ 10 الكبار (أكثر الأسهم سيولة في البورصة المصرية)
TICKERS = [
    "COMI.CA", "FWRY.CA", "SWDY.CA", "ABUK.CA", "MFPC.CA",
    "ETEL.CA", "TMGH.CA", "ADIB.CA", "ORAS.CA", "ARCC.CA"
]

# 4. زر التشغيل السريع
if st.button("🚀 بدء المسح والتحليل (توقيت القاهرة)"):
    results = []
    progress_bar = st.progress(0)
    table_placeholder = st.empty()
    
    for idx, sym in enumerate(TICKERS):
        try:
            # جلب البيانات (فحص شهر لضمان الدقة)
            df = yf.download(sym, period="1mo", interval="1d", progress=False)
            if not df.empty:
                curr_price = round(float(df['Close'].iloc[-1]), 2)
                month_high = df['High'].max()
                month_low = df['Low'].min()
                
                # معادلة القوة: قياس المسافة من القاع الشهري
                strength = round(((month_high - curr_price) / (month_high - month_low)) * 100) if month_high != month_low else 0
                
                results.append({
                    "الرمز": sym.replace(".CA", ""),
                    "السعر": curr_price,
                    "القوة %": strength,
                    "أعلى سعر": round(float(month_high), 2)
                })
                
                # تحديث العرض فوراً (استخدام dataframe ليكون أخف)
                live_df = pd.DataFrame(results).sort_values(by="القوة %", ascending=False)
                table_placeholder.dataframe(
                    live_df.style.applymap(color_fix, subset=['القوة %']), 
                    use_container_width=True
                )
        except:
            continue
        
        progress_bar.progress((idx + 1) / len(TICKERS))
    
    if results:
        pd.DataFrame(results).to_csv(DATABASE, index=False)
        st.success("✅ تم تحديث قاعدة البيانات بنجاح!")

# 5. عرض النتائج المحفوظة (حماية من الخطأ الأحمر EmptyDataError)
if os.path.exists(DATABASE) and os.path.getsize(DATABASE) > 0:
    st.write("---")
    st.subheader("📊 نتائج الفحص الأخير:")
    df_saved = pd.read_csv(DATABASE)
    st.dataframe(
        df_saved.sort_values(by="القوة %", ascending=False).style.applymap(color_fix, subset=['القوة %']), 
        use_container_width=True
    )
else:
    st.info("⚠️ يرجى الضغط على زر المسح أعلاه لتأسيس قاعدة البيانات لأول مرة.")

# زر جانبي لمسح الذاكرة
if st.sidebar.button("🗑️ إعادة ضبط المنظومة"):
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
        st.rerun()
