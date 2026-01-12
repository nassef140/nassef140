import streamlit as st
import yfinance as yf
import pandas as pd
import os
import time
from datetime import datetime, timedelta

# --- [1. إعدادات المنظومة والقاموس] ---
st.set_page_config(page_title="Zara Pro - Sniper Edition", layout="wide")

# القائمة المستهدفة للمسح (EGX 70/100)
TICKER_DB = {
    "ARCC.CA": "العربية للأسمنت", "UNIT.CA": "المتحدة للإسكان", "LCSW.CA": "ليسكو مصر",
    "ACGC.CA": "حليج الأقطان", "ASCM.CA": "أسيك للتعدين", "AJWA.CA": "أجواء",
    "RMDA.CA": "راميدا", "ISPH.CA": "ابن سينا فارما", "EGAL.CA": "مصر للألومنيوم",
    "CCAP.CA": "القلعة", "RAYA.CA": "راية القابضة", "TAQA.CA": "طاقة عربية",
    "ALCN.CA": "الاسكندرية للحاويات", "DSMC.CA": "الدلتا للسكر", "MPRC.CA": "مدينة الإنتاج الإعلامي"
}

# قائمة EGX30 (تُحفظ في الملف للتحليل ولا تظهر في مسح الـ 50)
EGX30_LIST = ["COMI.CA", "FWRY.CA", "SWDY.CA", "TMGH.CA", "ABUK.CA", "MFPC.CA", "ETEL.CA"]

DATA_FILE = "zara_market_data.csv"

# --- [2. وظيفة تحديث البيانات وحماية من الحظر] ---
def refresh_database():
    all_stocks = {**TICKER_DB, **{k: "قيادي (EGX30)" for k in EGX30_LIST}}
    storage = []
    
    st.write("🔄 جاري الاتصال بالبورصة وتأسيس ملف البيانات...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    tickers = list(all_stocks.items())
    for idx, (sym, name) in enumerate(tickers):
        status_text.text(f"⏳ جاري جلب بيانات: {sym}")
        try:
            # الالتزام الصارم ببيانات 21 يوم عمل (نطلب شهر لضمان الاكتمال)
            df = yf.download(sym, period="1mo", interval="1h", progress=False)
            if not df.empty and len(df) >= 21:
                if isinstance(df.columns, pd.MultiIndex): 
                    df.columns = df.columns.get_level_values(0)
                
                df_21 = df.tail(21 * 7) # تحليل 21 يوم تداول فعلي
                
                curr = float(df_21['Close'].iloc[-1])
                h_max = float(df_21['High'].max())
                l_min = float(df_21['Low'].min())
                fvg = 1 if (len(df_21) > 3 and df_21['Low'].iloc[-1] > df_21['High'].iloc[-3]) else 0
                open_p = float(df_21['Open'].iloc[-1])
                
                storage.append([sym, name, curr, h_max, l_min, fvg, open_p, datetime.now()])
                # إضافة فترة راحة بسيطة جداً لتجنب البلوك
                time.sleep(0.2)
        except Exception as e:
            continue
        progress_bar.progress((idx + 1) / len(tickers))
    
    if storage:
        pd.DataFrame(storage, columns=['Symbol', 'Name', 'Price', 'High', 'Low', 'FVG', 'Open', 'LastUpdate']).to_csv(DATA_FILE, index=False)
        st.success("✅ تم تحديث ملف البيانات بنجاح! يمكنك البدء بالمسح الآن.")
        time.sleep(1)
        st.rerun()

# --- [3. محرك الاستراتيجية (القراءة من الملف المحلي)] ---
def analyze_from_cache(symbol):
    if not os.path.exists(DATA_FILE): return None
    try:
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
    except: return None

# --- [4. الواجهة والتحكم] ---
st.title("🦅 رادار زارا الاحترافي - نسخة الملف الذكي")

# منطق الملف والتحديث التلقائي/اليدوي
if os.path.exists(DATA_FILE):
    last_mod = datetime.fromtimestamp(os.path.getmtime(DATA_FILE))
    st.sidebar.info(f"📅 تحديث الملف: {last_mod.strftime('%H:%M:%S')}")
    if st.sidebar.button("🔄 تحديث البيانات (Refresh)"):
        refresh_database()
else:
    st.warning("⚠️ ملف البيانات غير موجود.")
    if st.button("🆕 إنشاء وتأسيس قاعدة البيانات"):
        refresh_database()

tab1, tab2 = st.tabs(["🚀 مسح الـ 50 الأوائل (EGX 70/100)", "🔍 تقرير خريطة الطريق التفصيلي"])

with tab1:
    if st.button("🏁 ابدأ المسح والترتيب التنازلي"):
        if not os.path.exists(DATA_FILE):
            st.error("يرجى إنشاء ملف البيانات أولاً.")
        else:
            results = []
            for sym in TICKER_DB.keys():
                res = analyze_from_cache(sym)
                if res: results.append(res)
            
            if results:
                df = pd.DataFrame(results).sort_values(by="القوة", ascending=False).reset_index(drop=True)
                df.insert(0, 'الترتيب', range(1, len(df) + 1))
                st.subheader("📊 قائمة النخبة المرتبة بدقة")
                st.table(df[["الترتيب", "الرمز", "الاسم", "القوة", "السعر", "م:ع", "SMC"]].head(50))

with tab2:
    code = st.text_input("أدخل رمز السهم (مثال: ARCC):").upper().strip()
    if st.button("📊 توليد تقرير خريطة الطريق") and code:
        res = analyze_from_cache(f"{code}.CA")
        if res:
            st.markdown(f"### 📽️ خريطة الطريق لـ {res['الاسم']}")
            st.write("---")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("السعر الحالي", f"{res['السعر']} ج.م")
            c2.metric("المستهدف الرئيسي", f"{res['Target']} ج.م")
            c3.metric("وقف الخسارة", f"{res['Stop']} ج.م")
            c4.metric("هدف بعيد", f"{res['T3']} ج.م")
            
            st.info(f"بصمة السيولة: {res['SMC']} | منطقة الخصم: تحت {res['Fib']}")
            st.success(f"قوة الاستراتيجية: {res['القوة']}% | جودة الصفقة: {res['م:ع']}")
        else:
            st.error("السهم غير مسجل في قاعدة البيانات الحالية.")
