import streamlit as st
import yfinance as yf
import pandas as pd
import os
import time
from datetime import datetime, timedelta

# --- [1. إعدادات المنظومة والقوائم] ---
st.set_page_config(page_title="Zara Pro - Database Edition", layout="wide")

# القائمة الكاملة (EGX 30 + 70 + 100) - سيتم حفظ الجميع في الملف
EGX30 = ["COMI.CA", "FWRY.CA", "SWDY.CA", "TMGH.CA", "ABUK.CA", "MFPC.CA", "ETEL.CA", "CIEB.CA", "ADIB.CA", "HRHO.CA"]
EGX70_100 = {
    "ARCC.CA": "العربية للأسمنت", "UNIT.CA": "المتحدة للإسكان", "LCSW.CA": "ليسكو مصر",
    "ACGC.CA": "حليج الأقطان", "ASCM.CA": "أسيك للتعدين", "AJWA.CA": "أجواء",
    "RMDA.CA": "راميدا", "ISPH.CA": "ابن سينا فارما", "EGAL.CA": "مصر للألومنيوم",
    "CCAP.CA": "القلعة", "RAYA.CA": "راية القابضة", "TAQA.CA": "طاقة عربية",
    "ALCN.CA": "الاسكندرية للحاويات", "DSMC.CA": "الدلتا للسكر", "MPRC.CA": "مدينة الإنتاج الإعلامي"
}

# دمج الجميع في قائمة واحدة لملف البيانات
FULL_LIST = {**EGX70_100, **{k: "سهم قيادي (EGX30)" for k in EGX30}}
DATA_FILE = "zara_db.csv"

# --- [2. وظائف إدارة البيانات والملف المحدث] ---
def refresh_database():
    """تقوم هذه الوظيفة بجلب البيانات من الإنترنت وحفظها في ملف CSV"""
    all_data = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    tickers = list(FULL_LIST.items())
    for idx, (sym, name) in enumerate(tickers):
        status_text.text(f"🔍 جاري جلب: {sym}")
        try:
            # جلب بيانات كافية لتحليل 21 يوم
            df = yf.download(sym, period="1mo", interval="1h", progress=False)
            if not df.empty and len(df) >= 21:
                if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                df_21 = df.tail(21 * 7)
                
                curr = float(df_21['Close'].iloc[-1])
                h_max = float(df_21['High'].max())
                l_min = float(df_21['Low'].min())
                fvg = 1 if (df_21['Low'].iloc[-1] > df_21['High'].iloc[-3]) else 0
                open_p = float(df_21['Open'].iloc[-1])
                
                all_data.append([sym, name, curr, h_max, l_min, fvg, open_p, datetime.now()])
        except: continue
        progress_bar.progress((idx + 1) / len(tickers))
    
    if all_data:
        pd.DataFrame(all_data, columns=['Symbol', 'Name', 'Price', 'High', 'Low', 'FVG', 'Open', 'LastUpdate']).to_csv(DATA_FILE, index=False)
        st.success("✅ تم تحديث قاعدة البيانات بنجاح!")
        time.sleep(1)
        st.rerun()

# --- [3. محرك الاستراتيجية (التحليل من الملف المحلي)] ---
def analyze_from_db(symbol):
    if not os.path.exists(DATA_FILE): return None
    db = pd.read_csv(DATA_FILE)
    row = db[db['Symbol'] == symbol]
    if row.empty: return None
    
    r = row.iloc[0]
    curr, h_max, l_min = float(r['Price']), float(r['High']), float(r['Low'])
    fvg = bool(r['FVG'])
    
    # استراتيجية زارا (21 يوم)
    fib_618 = l_min + (h_max - l_min) * 0.618
    stop = round(l_min * 0.985, 2)
    target = round(h_max, 2)
    rr = round((target - curr) / (curr - stop), 2) if (curr - stop) > 0 else 0
    
    score = 0
    if curr <= fib_618: score += 40
    if rr >= 2: score += 30
    if fvg: score += 20
    if curr > float(r['Open']): score += 10
    
    return {
        "الرمز": r['Symbol'].split(".")[0], "الاسم": r['Name'], "القوة": score,
        "السعر": curr, "م:ع": f"1:{rr}", "SMC": "✅" if fvg else "⚠️",
        "Target": target, "Stop": stop, "Fib": round(fib_618, 2),
        "T1": round(curr + (target - curr) * 0.5, 2), "T3": round(target * 1.15, 2)
    }

# --- [4. الواجهة الرسومية والتحديث] ---
st.title("🦅 منظومة زارا برو - النسخة المحدثة كلياً")

# تحديث تلقائي كل 30 دقيقة
if os.path.exists(DATA_FILE):
    file_time = datetime.fromtimestamp(os.path.getmtime(DATA_FILE))
    if datetime.now() - file_time > timedelta(minutes=30):
        refresh_database()
else:
    refresh_database()

# أزرار التحكم
c1, c2 = st.columns([5, 1])
with c1: st.info(f"📅 آخر تحديث للبيانات: {datetime.fromtimestamp(os.path.getmtime(DATA_FILE)).strftime('%H:%M:%S')}")
with c2: 
    if st.button("🔄 تحديث يدوي"): refresh_database()

tab1, tab2 = st.tabs(["🚀 مسح الـ 50 الأقوى", "🔍 تقرير خريطة الطريق التفصيلي"])

with tab1:
    if st.button("🏁 تشغيل المسح والترتيب"):
        results = []
        # مسح أسهم EGX 70/100 فقط واستبعاد الـ 30
        for sym in EGX70_100.keys():
            res = analyze_from_db(sym)
            if res: results.append(res)
        
        if results:
            df = pd.DataFrame(results).sort_values(by="القوة", ascending=False).reset_index(drop=True)
            df.insert(0, 'الترتيب', range(1, len(df) + 1))
            st.table(df[["الترتيب", "الرمز", "الاسم", "القوة", "السعر", "م:ع", "SMC"]].head(50))

with tab2:
    code = st.text_input("أدخل الرمز (مثل UNIT أو ARCC):").upper().strip()
    if st.button("📊 عرض التقرير") and code:
        res = analyze_from_db(f"{code}.CA")
        if res:
            st.markdown(f"### 🖋️ تقرير: {res['الرمز']} ({res['الاسم']})")
            col1, col2, col3 = st.columns(3)
            col1.metric("السعر الحالي", res['السعر'])
            col2.metric("المستهدف الرئيسي", res['Target'])
            col3.metric("وقف الخسارة", res['Stop'])
            st.success(f"قوة الاستراتيجية: {res['القوة']}% | بصمة السيولة: {res['SMC']} | المنطقة الذهبية: تحت {res['Fib']}")
        else:
            st.error("السهم غير موجود في قاعدة البيانات المحدثة.")
