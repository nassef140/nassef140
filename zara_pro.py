import streamlit as st
import yfinance as yf
import pandas as pd
import os
import time
from datetime import datetime, timedelta

# --- [1. إعدادات المنظومة والقاموس] ---
st.set_page_config(page_title="Zara Pro - Ultimate Database Edition", layout="wide")

# قائمة الأسهم القيادية (EGX 30) - تحفظ في الملف للتحليل وتستبعد من مسح الـ 50
EGX30_LIST = [
    "COMI.CA", "FWRY.CA", "SWDY.CA", "TMGH.CA", "ABUK.CA", "MFPC.CA", "ETEL.CA", 
    "CIEB.CA", "ADIB.CA", "HRHO.CA", "BTEL.CA", "ESRS.CA", "IRAX.CA", "EKHO.CA", 
    "AMOC.CA", "SKPC.CA", "ORAS.CA", "EMFD.CA", "HELI.CA", "MNHD.CA", "PHDC.CA"
]

# قاموس أسهم الفرص (EGX 70/100) - يمكنك التوسع حتى 200 سهم
EGX70_100_DB = {
    "ARCC.CA": "العربية للأسمنت", "UNIT.CA": "المتحدة للإسكان", "LCSW.CA": "ليسكو مصر",
    "ACGC.CA": "حليج الأقطان", "ASCM.CA": "أسيك للتعدين", "AJWA.CA": "أجواء",
    "RMDA.CA": "راميدا", "ISPH.CA": "ابن سينا فارما", "EGAL.CA": "مصر للألومنيوم",
    "CCAP.CA": "القلعة", "RAYA.CA": "راية القابضة", "TAQA.CA": "طاقة عربية",
    "ALCN.CA": "الاسكندرية للحاويات", "DSMC.CA": "الدلتا للسكر", "MPRC.CA": "مدينة الإنتاج الإعلامي"
}

# دمج القوائم للملف الشامل
FULL_TICKER_LIST = {**EGX70_100_DB, **{k: "قيادي (EGX30)" for k in EGX30_LIST}}
DATA_FILE = "zara_market_cache.csv"

# --- [2. محرك التحديث وجلب البيانات] ---
def refresh_market_data():
    with st.spinner("🔄 جاري تحديث قاعدة البيانات الشاملة (EGX 30 + 70 + 100)..."):
        all_results = []
        progress_bar = st.progress(0)
        tickers = list(FULL_TICKER_LIST.items())
        
        for idx, (sym, name) in enumerate(tickers):
            try:
                # جلب بيانات كافية لتحليل 21 يوم تداول
                df = yf.download(sym, period="1mo", interval="1h", progress=False)
                if not df.empty and len(df) >= 21:
                    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                    df_21 = df.tail(21 * 7) # 21 يوم عمل
                    
                    curr = float(df_21['Close'].iloc[-1])
                    h_max = float(df_21['High'].max())
                    l_min = float(df_21['Low'].min())
                    fvg = 1 if (df_21['Low'].iloc[-1] > df_21['High'].iloc[-3]) else 0
                    open_p = float(df_21['Open'].iloc[-1])
                    
                    all_results.append([sym, name, curr, h_max, l_min, fvg, open_p, datetime.now()])
                progress_bar.progress((idx + 1) / len(tickers))
            except: continue
        
        if all_results:
            pd.DataFrame(all_results, columns=['Symbol', 'Name', 'Price', 'High', 'Low', 'FVG', 'Open', 'LastUpdate']).to_csv(DATA_FILE, index=False)
            st.success(f"✅ تم تحديث {len(all_results)} سهم بنجاح.")
            time.sleep(1)
            st.rerun()

# --- [3. محرك الاستراتيجية (التحليل من ملف الـ CSV)] ---
def analyze_stock(symbol):
    if not os.path.exists(DATA_FILE): return None
    db = pd.read_csv(DATA_FILE)
    row = db[db['Symbol'] == symbol]
    if row.empty: return None
    
    r = row.iloc[0]
    curr, h_max, l_min = float(r['Price']), float(r['High']), float(r['Low'])
    fvg = bool(r['FVG'])
    
    # حساب الاستراتيجية (21 يوم عمل)
    fib_618 = l_min + (h_max - l_min) * 0.618
    stop = round(l_min * 0.985, 2)
    target = round(h_max, 2)
    rr = round((target - curr) / (curr - stop), 2) if (curr - stop) > 0 else 0
    
    # نظام التنقيط الاحترافي
    score = 0
    if curr <= fib_618: score += 40      # السعر في منطقة خصم
    if rr >= 2: score += 30               # جودة مخاطرة ممتازة
    if fvg: score += 20                   # رصد سيولة ذكية
    if curr > float(r['Open']): score += 10 # زخم إيجابي
    
    return {
        "Symbol": r['Symbol'].split(".")[0], 
        "Name": r['Name'], 
        "Score": score,
        "Price": curr, 
        "RR": f"1:{rr}", 
        "SMC": "قوية ✅" if fvg else "⚠️",
        "Target": target, 
        "Stop": stop, 
        "Fib": round(fib_618, 2),
        "T1": round(curr + (target - curr) * 0.5, 2), 
        "T3": round(target * 1.15, 2)
    }

# --- [4. واجهة المستخدم الرسومية] ---
st.title("🛡️ منظومة زارا برو - نسخة الملف الذكي المحدث")

# تحديث تلقائي كل 30 دقيقة
if os.path.exists(DATA_FILE):
    last_mod = datetime.fromtimestamp(os.path.getmtime(DATA_FILE))
    if datetime.now() - last_mod > timedelta(minutes=30):
        refresh_market_data()
else:
    refresh_market_data()

# شريط التحكم العلوي
col_status, col_btn = st.columns([5, 1])
with col_status:
    st.info(f"📅 آخر تحديث للبيانات: {datetime.fromtimestamp(os.path.getmtime(DATA_FILE)).strftime('%Y-%m-%d %H:%M:%S')}")
with col_btn:
    if st.button("🔄 تحديث البيانات الآن"):
        refresh_market_data()

tab1, tab2 = st.tabs(["🚀 مسح نخبة الـ 50 (EGX 70/100)", "🔍 تقرير خريطة الطريق التفصيلي"])

with tab1:
    st.subheader("أفضل 50 فرصة استثمارية مرتبة تنازلياً")
    if st.button("🏁 تشغيل المسح والفرز"):
        results = []
        # المسح لأسهم EGX 70/100 فقط (الاستبعاد الضمني للـ 30)
        for sym in EGX70_100_DB.keys():
            res = analyze_stock(sym)
            if res: results.append(res)
        
        if results:
            df_final = pd.DataFrame(results).sort_values(by="Score", ascending=False).reset_index(drop=True)
            df_final.insert(0, 'الترتيب', range(1, len(df_final) + 1))
            st.table(df_final[["الترتيب", "Symbol", "Name", "Score", "Price", "RR", "SMC"]].head(50))
        else:
            st.error("لا توجد بيانات متاحة حالياً.")

with tab2:
    st.subheader("🖋️ استخراج تقرير التحليل المعمق (يشمل كافة الأسهم)")
    user_input = st.text_input("أدخل رمز السهم (مثال: ARCC):").upper().strip()
    if st.button("📊 إصدار التقرير") and user_input:
        res = analyze_stock(f"{user_input}.CA")
        if res:
            st.markdown(f"## 📽️ تقرير خريطة الطريق: {res['Symbol']} ({res['Name']})")
            st.write("---")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("السعر الحالي", f"{res['Price']} ج.م")
            c2.metric("هدف أول", f"{res['T1']} ج.م")
            c3.metric("مستهدف رئيسي", f"{res['Target']} ج.م")
            c4.metric("وقف الخسارة", f"{res['Stop']} ج.م")
            
            st.info(f"بصمة السيولة: {res['SMC']} | منطقة الخصم الذهبية: تحت {res['Fib']}")
            st.success(f"قوة الاستراتيجية: {res['Score']}% | جودة الصفقة (RR): {res['RR']} | هدف بعيد: {res['T3']}")
        else:
            st.error("الرمز غير موجود أو لم يتم تحديث بياناته.")
