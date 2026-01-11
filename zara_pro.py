import streamlit as st
import yfinance as yf
import pandas as pd
import os
import time
from datetime import datetime, timedelta
import pytz

# --- [1. إعدادات المنظومة] ---
st.set_page_config(page_title="Zara Pro - Safe Sync Edition", layout="wide")
CAIRO_TZ = pytz.timezone('Africa/Cairo')
DATA_FILE = "zara_market_db.csv"

# القائمة الشاملة (مثال للتشغيل - يمكنك توسيعها لـ 200 سهم)
TICKER_DB = {
    "ARCC.CA": "العربية للأسمنت", "UNIT.CA": "المتحدة للإسكان", "LCSW.CA": "ليسكو مصر",
    "ACGC.CA": "حليج الأقطان", "ASCM.CA": "أسيك للتعدين", "AJWA.CA": "أجواء",
    "RMDA.CA": "راميدا", "ISPH.CA": "ابن سينا فارما", "EGAL.CA": "مصر للألومنيوم",
    "CCAP.CA": "القلعة", "RAYA.CA": "راية القابضة", "TAQA.CA": "طاقة عربية",
    "ALCN.CA": "الاسكندرية للحاويات", "DSMC.CA": "الدلتا للسكر", "MPRC.CA": "مدينة الإنتاج الإعلامي",
    "ATQA.CA": "مصر الوطنية للصلب", "DAPH.CA": "مطاحن وسط وغرب", "AMER.CA": "عامر جروب",
    "PORT.CA": "بورتو جروب", "ELSH.CA": "الشمس للإسكان", "EEII.CA": "المصرية للاستثمار"
}

EGX30_LIST = ["COMI.CA", "FWRY.CA", "SWDY.CA", "TMGH.CA", "ABUK.CA", "MFPC.CA", "ETEL.CA"]

# --- [2. محرك التحديث بنظام المجموعات والراحة 30 ثانية] ---
def refresh_database_safe():
    all_stocks = {**TICKER_DB, **{k: "قيادي" for k in EGX30_LIST}}
    storage = []
    
    st.write("### 🛠️ بدأت المزامنة الآمنة... (مجموعات 30 سهم | راحة 30 ثانية)")
    progress_bar = st.progress(0)
    status_text = st.empty()
    timer_text = st.empty()
    
    tickers = list(all_stocks.items())
    total = len(tickers)
    batch_size = 30 
    
    for i in range(0, total, batch_size):
        batch = tickers[i:i + batch_size]
        for idx, (sym, name) in enumerate(batch):
            current_idx = i + idx
            status_text.text(f"⏳ جاري معالجة: {sym} ({name}) - {current_idx + 1}/{total}")
            try:
                # جلب بيانات 21 يوم تداول (نطلب شهر لضمان الاكتمال)
                df = yf.download(sym, period="1mo", interval="1h", progress=False)
                if not df.empty and len(df) >= 21:
                    if isinstance(df.columns, pd.MultiIndex): 
                        df.columns = df.columns.get_level_values(0)
                    
                    df_calc = df.tail(21 * 7) # تحليل 21 يوم عمل
                    
                    curr = float(df_calc['Close'].iloc[-1])
                    h_max = float(df_calc['High'].max())
                    l_min = float(df_calc['Low'].min())
                    fvg = 1 if (len(df_calc) > 3 and df_calc['Low'].iloc[-1] > df_calc['High'].iloc[-3]) else 0
                    open_p = float(df_calc['Open'].iloc[-1])
                    
                    update_ts = datetime.now(CAIRO_TZ).strftime('%Y-%m-%d %H:%M:%S')
                    storage.append([sym, name, curr, h_max, l_min, fvg, open_p, update_ts])
                    time.sleep(0.3)
            except: continue
            progress_bar.progress((current_idx + 1) / total)
        
        # تنفيذ التوقف لمدة 30 ثانية بين كل مجموعة (إلا المجموعة الأخيرة)
        if i + batch_size < total:
            for remaining in range(30, 0, -1):
                timer_text.warning(f"☕ استراحة أمان للسيرفر.. سنكمل بعد {remaining} ثانية...")
                time.sleep(1)
            timer_text.empty()

    if storage:
        pd.DataFrame(storage, columns=['Symbol', 'Name', 'Price', 'High', 'Low', 'FVG', 'Open', 'LastUpdate']).to_csv(DATA_FILE, index=False)
        st.success("✅ تمت المزامنة بنجاح! تم حفظ البيانات وتحديث خريطة التداول.")
        time.sleep(2)
        st.rerun()

# --- [3. محرك التحليل والواجهة] ---
def get_analysis(symbol):
    if not os.path.exists(DATA_FILE): return None
    try:
        db = pd.read_csv(DATA_FILE)
        row = db[db['Symbol'] == symbol]
        if row.empty: return None
        r = row.iloc[0]
        
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
        
        return {"الترتيب": 0, "الرمز": r['Symbol'].split(".")[0], "الاسم": r['Name'], "القوة": score, "السعر": curr, "م:ع": f"1:{rr}", "SMC": "✅" if bool(r['FVG']) else "⚠️", "Target": target, "Stop": stop, "Fib": round(fib_618, 2)}
    except: return None

# الواجهة الرئيسية
st.title("🛡️ منظومة زارا برو - رادار الأمان والاستقرار")

if os.path.exists(DATA_FILE):
    df_temp = pd.read_csv(DATA_FILE)
    if not df_temp.empty:
        last_up = df_temp['LastUpdate'].iloc[0].split(' ')[1]
        st.sidebar.info(f"🕒 آخر مزامنة (القاهرة): {last_up}")
    if st.sidebar.button("🔄 تحديث شامل (نظام الدفعات)"):
        refresh_database_safe()
else:
    st.warning("⚠️ قاعدة البيانات غير موجودة. اضغط للتأسيس.")
    if st.button("🆕 تأسيس قاعدة البيانات (Safe Sync)"):
        refresh_database_safe()

tab1, tab2 = st.tabs(["🚀 مسح الـ 50 الأقوى (EGX 70/100)", "🔍 تقرير خريطة الطريق التفصيلي"])

with tab1:
    if st.button("🏁 تشغيل المسح والترتيب التنازلي"):
        results = [get_analysis(s) for s in TICKER_DB.keys() if get_analysis(s)]
        if results:
            df_final = pd.DataFrame(results).sort_values(by="القوة", ascending=False).reset_index(drop=True)
            df_final.insert(0, 'الترتيب', range(1, len(df_final) + 1))
            st.subheader("📊 قائمة النخبة المرتبة (أعلى 50 سهم)")
            st.table(df_final[["الترتيب", "الرمز", "الاسم", "القوة", "السعر", "م:ع", "SMC"]].head(50))
        else:
            st.error("لا توجد بيانات للتحليل. يرجى المزامنة أولاً.")

with tab2:
    code = st.text_input("أدخل رمز السهم (مثال: UNIT):").upper().strip()
    if st.button("📊 توليد التقرير") and code:
        res = get_analysis(f"{code}.CA")
        if res:
            st.markdown(f"### 🖋️ خريطة الطريق لـ {res['الاسم']}")
            st.success(f"المستهدف الرئيسي: {res['Target']} | وقف الخسارة: {res['Stop']} | القوة: {res['القوة']}%")
        else:
            st.error("السهم غير موجود في قاعدة البيانات الحالية.")
