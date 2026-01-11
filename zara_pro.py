import streamlit as st
import yfinance as yf
import pandas as pd
import os
import time
from datetime import datetime, timedelta
import pytz # مكتبة التوقيتات لضبط توقيت القاهرة

# --- [1. إعدادات المنظومة والقاموس] ---
st.set_page_config(page_title="Zara Pro - Cairo Sync", layout="wide")

# تحديد توقيت القاهرة
CAIRO_TZ = pytz.timezone('Africa/Cairo')

# قاموس الـ 200 سهم (نموذج مكثف)
TICKER_DB = {
    "ARCC.CA": "العربية للأسمنت", "UNIT.CA": "المتحدة للإسكان", "LCSW.CA": "ليسكو مصر",
    "ACGC.CA": "حليج الأقطان", "ASCM.CA": "أسيك للتعدين", "AJWA.CA": "أجواء",
    "RMDA.CA": "راميدا", "ISPH.CA": "ابن سينا فارما", "EGAL.CA": "مصر للألومنيوم",
    "CCAP.CA": "القلعة", "RAYA.CA": "راية القابضة", "TAQA.CA": "طاقة عربية",
    "ALCN.CA": "الاسكندرية للحاويات", "DSMC.CA": "الدلتا للسكر", "MPRC.CA": "مدينة الإنتاج الإعلامي",
    "ATQA.CA": "مصر الوطنية للصلب", "DAPH.CA": "مطاحن وسط وغرب", "AMER.CA": "عامر جروب",
    "PORT.CA": "بورتو جروب", "ELSH.CA": "الشمس للإسكان", "EEII.CA": "المصرية للاستثمار",
    "ORWE.CA": "النساجون الشرقيون", "NAPT.CA": "النصر للأعمال المدنية", "MICH.CA": "مصر للكيماويات",
    "MCQE.CA": "أسمنت قنا", "SVCE.CA": "جنوب الوادي للأسمنت", "ANBK.CA": "الاسكندرية للأدوية",
    "SKPC.CA": "سيدي كرير", "AMOC.CA": "أموك", "IFAP.CA": "الدولية للأسمدة",
    "ELKA.CA": "القاهرة للاستثمار", "MBSC.CA": "مصر بني سويف للأسمنت", "IRAX.CA": "إيراك"
}

EGX30_LIST = ["COMI.CA", "FWRY.CA", "SWDY.CA", "TMGH.CA", "ABUK.CA", "MFPC.CA", "ETEL.CA"]
DATA_FILE = "zara_cairo_db.csv"

# --- [2. وظيفة التحديث مع مزامنة توقيت القاهرة] ---
def refresh_database():
    all_stocks = {**TICKER_DB, **{k: "قيادي (EGX30)" for k in EGX30_LIST}}
    storage = []
    
    st.write(f"### 🕒 جاري التحديث بتوقيت القاهرة: {datetime.now(CAIRO_TZ).strftime('%H:%M:%S')}")
    progress_bar = st.progress(0)
    
    tickers = list(all_stocks.items())
    for idx, (sym, name) in enumerate(tickers):
        try:
            # جلب بيانات 21 يوم عمل
            df = yf.download(sym, period="1mo", interval="1h", progress=False)
            if not df.empty and len(df) >= 21:
                if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                df_21 = df.tail(21 * 7)
                
                curr = float(df_21['Close'].iloc[-1])
                h_max = float(df_21['High'].max())
                l_min = float(df_21['Low'].min())
                fvg = 1 if (len(df_21) > 3 and df_21['Low'].iloc[-1] > df_21['High'].iloc[-3]) else 0
                open_p = float(df_21['Open'].iloc[-1])
                
                # تسجيل وقت التحديث بتوقيت القاهرة
                update_time = datetime.now(CAIRO_TZ).strftime('%Y-%m-%d %H:%M:%S')
                storage.append([sym, name, curr, h_max, l_min, fvg, open_p, update_time])
                time.sleep(0.1) # حماية من البلوك
        except: continue
        progress_bar.progress((idx + 1) / len(tickers))
    
    if storage:
        pd.DataFrame(storage, columns=['Symbol', 'Name', 'Price', 'High', 'Low', 'FVG', 'Open', 'LastUpdate']).to_csv(DATA_FILE, index=False)
        st.success("✅ تم تحديث المخزن الرقمي بنجاح!")
        time.sleep(1)
        st.rerun()

# --- [3. محرك الاستراتيجية والواجهة] ---
def get_data_from_cache(symbol):
    if not os.path.exists(DATA_FILE): return None
    db = pd.read_csv(DATA_FILE)
    row = db[db['Symbol'] == symbol]
    if row.empty: return None
    r = row.iloc[0]
    
    # حسابات فيبوناتشي والسيولة (نفس الاستراتيجية الصارمة)
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

st.title("🛡️ منظومة زارا - نسخة توقيت القاهرة")

if os.path.exists(DATA_FILE):
    # قراءة وقت التحديث من الملف نفسه لضمان المزامنة
    df_temp = pd.read_csv(DATA_FILE)
    last_update = df_temp['LastUpdate'].iloc[0]
    st.sidebar.info(f"🕒 توقيت القاهرة: {last_update.split(' ')[1]}")
    if st.sidebar.button("🔄 تحديث شامل"): refresh_database()
else:
    if st.button("🆕 تأسيس قاعدة البيانات (توقيت القاهرة)"): refresh_database()

tab1, tab2 = st.tabs(["🚀 مسح الـ 50 الأقوى", "🔍 خريطة الطريق"])

with tab1:
    if st.button("🏁 تشغيل المسح والترتيب"):
        results = [get_data_from_cache(sym) for sym in TICKER_DB.keys() if get_data_from_cache(sym)]
        if results:
            df_res = pd.DataFrame(results).sort_values(by="القوة", ascending=False).reset_index(drop=True)
            df_res.insert(0, 'الترتيب', range(1, len(df_res) + 1))
            st.table(df_res[["الترتيب", "الرمز", "الاسم", "القوة", "السعر", "م:ع", "SMC"]].head(50))

with tab2:
    code = st.text_input("أدخل الرمز (مثال: ARCC):").upper().strip()
    if st.button("📊 تقرير التداول") and code:
        res = get_data_from_cache(f"{code}.CA")
        if res:
            st.markdown(f"### 🖋️ خريطة الطريق لـ {res['الاسم']}")
            st.success(f"المستهدف: {res['Target']} | الوقف: {res['Stop']} | القوة: {res['القوة']}%")
        else: st.error("السهم غير موجود.")
