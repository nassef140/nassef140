import streamlit as st
import yfinance as yf
import pandas as pd
import os
import time
from datetime import datetime, timedelta
import pytz

# --- [1. الإعدادات والمزامنة الزمنية] ---
st.set_page_config(page_title="Zara Pro - Cairo Final", layout="wide")
CAIRO_TZ = pytz.timezone('Africa/Cairo')
DATA_FILE = "zara_cairo_database.csv"

# --- [2. قاعدة بيانات الأسهم (نموذج للـ 200 سهم)] ---
# يمكنك إضافة كافة رموز الـ 200 سهم هنا بنفس التنسيق
TICKER_DB = {
    "ARCC.CA": "العربية للأسمنت", "UNIT.CA": "المتحدة للإسكان", "LCSW.CA": "ليسكو مصر",
    "ACGC.CA": "حليج الأقطان", "ASCM.CA": "أسيك للتعدين", "AJWA.CA": "أجواء",
    "RMDA.CA": "راميدا", "ISPH.CA": "ابن سينا فارما", "EGAL.CA": "مصر للألومنيوم",
    "CCAP.CA": "القلعة", "RAYA.CA": "راية القابضة", "TAQA.CA": "طاقة عربية",
    "ALCN.CA": "الاسكندرية للحاويات", "DSMC.CA": "الدلتا للسكر", "MPRC.CA": "مدينة الإنتاج الإعلامي"
}

EGX30_LIST = ["COMI.CA", "FWRY.CA", "SWDY.CA", "TMGH.CA", "ABUK.CA", "MFPC.CA", "ETEL.CA"]

# --- [3. وظيفة التحديث الجذري ومنع الحظر] ---
def refresh_market_data():
    all_stocks = {**TICKER_DB, **{k: "قيادي" for k in EGX30_LIST}}
    storage = []
    
    st.write(f"### 🕒 بدء المزامنة بتوقيت القاهرة: {datetime.now(CAIRO_TZ).strftime('%H:%M:%S')}")
    progress_bar = st.progress(0)
    
    tickers = list(all_stocks.items())
    for idx, (sym, name) in enumerate(tickers):
        try:
            # طلب بيانات شهر لضمان 21 يوم عمل كاملة
            df = yf.download(sym, period="1mo", interval="1h", progress=False)
            if not df.empty and len(df) >= 21:
                if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                df_calc = df.tail(21 * 7) # بيانات 21 يوم تداول
                
                curr = float(df_calc['Close'].iloc[-1])
                h_max = float(df_calc['High'].max())
                l_min = float(df_calc['Low'].min())
                fvg = 1 if (len(df_calc) > 3 and df_calc['Low'].iloc[-1] > df_calc['High'].iloc[-3]) else 0
                open_p = float(df_calc['Open'].iloc[-1])
                
                update_ts = datetime.now(CAIRO_TZ).strftime('%Y-%m-%d %H:%M:%S')
                storage.append([sym, name, curr, h_max, l_min, fvg, open_p, update_ts])
                time.sleep(0.1) # حماية الشبكة
        except: continue
        progress_bar.progress((idx + 1) / len(tickers))
    
    if storage:
        pd.DataFrame(storage, columns=['Symbol', 'Name', 'Price', 'High', 'Low', 'FVG', 'Open', 'LastUpdate']).to_csv(DATA_FILE, index=False)
        st.success("✅ تم تحديث المخزن الرقمي بنجاح!")
        time.sleep(1)
        st.rerun()

# --- [4. محرك التحليل والواجهة] ---
def get_analysis(symbol):
    if not os.path.exists(DATA_FILE): return None
    try:
        db = pd.read_csv(DATA_FILE)
        row = db[db['Symbol'] == symbol]
        if row.empty: return None
        r = row.iloc[0]
        
        # استراتيجية زارا الصارمة (21 يوم)
        curr, h_max, l_min = float(r['Price']), float(r['High']), float(r['Low'])
        fib_618 = l_min + (h_max - l_min) * 0.618
        stop = round(l_min * 0.985, 2)
        target = round(h_max, 2)
        rr = round((target - curr) / (curr - stop), 2) if (curr - stop) > 0 else 0
        
        score = 0
        if curr <= fib_618: score += 40
        if rr >= 2: score += 30
        if bool(r['FVG']): score += 20
        if curr > float(r['Open']): score += 10
        
        return {"الرمز": r['Symbol'].split(".")[0], "الاسم": r['Name'], "القوة": score, "السعر": curr, "م:ع": f"1:{rr}", "SMC": "✅" if bool(r['FVG']) else "⚠️", "Target": target, "Stop": stop, "Fib": round(fib_618, 2)}
    except: return None

# الواجهة الرئيسية
st.title("🛡️ منظومة زارا برو - الإصدار النهائي")

# إدارة المزامنة
if os.path.exists(DATA_FILE):
    df_temp = pd.read_csv(DATA_FILE)
    if not df_temp.empty:
        last_up = df_temp['LastUpdate'].iloc[0].split(' ')[1]
        st.sidebar.info(f"🕒 مزامنة القاهرة: {last_up}")
    if st.sidebar.button("🔄 تحديث شامل (كل 30 دقيقة)"): refresh_market_data()
else:
    st.warning("⚠️ يرجى تأسيس قاعدة البيانات أولاً.")
    if st.button("🆕 تأسيس قاعدة البيانات (توقيت القاهرة)"): refresh_market_data()

tab1, tab2 = st.tabs(["🚀 مسح الـ 50 الأقوى", "🔍 خريطة الطريق التفصيلية"])

with tab1:
    if st.button("🏁 تشغيل المسح والترتيب التنازلي"):
        results = []
        for sym in TICKER_DB.keys():
            res = get_analysis(sym)
            if res: results.append(res)
        
        if results:
            df_final = pd.DataFrame(results).sort_values(by="القوة", ascending=False).reset_index(drop=True)
            df_final.insert(0, 'الترتيب', range(1, len(df_final) + 1))
            st.table(df_final[["الترتيب", "الرمز", "الاسم", "القوة", "السعر", "م:ع", "SMC"]].head(50))

with tab2:
    code = st.text_input("أدخل الرمز للتحليل (مثال: UNIT):").upper().strip()
    if st.button("📊 إصدار تقرير التحليل") and code:
        res = get_analysis(f"{code}.CA")
        if res:
            st.markdown(f"### 📽️ خريطة الطريق: {res['الرمز']} ({res['الاسم']})")
            col1, col2, col3 = st.columns(3)
            col1.metric("السعر الحالي", res['السعر'])
            col2.metric("المستهدف الرئيسي", res['Target'])
            col3.metric("وقف الخسارة", res['Stop'])
            st.success(f"قوة الاستراتيجية: {res['القوة']}% | منطقة الخصم: تحت {res['Fib']}")
