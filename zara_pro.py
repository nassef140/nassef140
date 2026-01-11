import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- [1. إعدادات المنظومة] ---
st.set_page_config(page_title="Zara Pro - Ultimate Fix", layout="wide")

# قائمة الاستبعاد الصارمة (EGX 30)
EXCLUDE_LIST = ["COMI.CA", "FWRY.CA", "SWDY.CA", "TMGH.CA", "ABUK.CA", "MFPC.CA", "ETEL.CA", "CIEB.CA", "ADIB.CA", "HRHO.CA"]

# القاموس الموسع (تأكد من وجود ARCC هنا دائماً)
TICKER_DB = {
    "ARCC.CA": "العربية للأسمنت", "LCSW.CA": "ليسكو مصر", "ACGC.CA": "حليج الأقطان",
    "ASCM.CA": "أسيك للتعدين", "AJWA.CA": "أجواء", "AFMC.CA": "الاسكندرية للزيوت",
    "ATQA.CA": "مصر الوطنية للصلب", "DAPH.CA": "مطاحن وسط وغرب", "MPRC.CA": "مدينة الإنتاج الإعلامي",
    "UNIT.CA": "المتحدة للإسكان", "PORT.CA": "بورتو جروب", "ELSH.CA": "الشمس للإسكان",
    "RMDA.CA": "راميدا للأدوية", "ISPH.CA": "ابن سينا فارما", "EGAL.CA": "مصر للألومنيوم",
    "CCAP.CA": "القلعة", "RAYA.CA": "راية القابضة", "TAQA.CA": "طاقة عربية",
    "DOMT.CA": "دومتي", "OBRI.CA": "عبور لاند", "ALCN.CA": "الاسكندرية للحاويات",
    "DSMC.CA": "الدلتا للسكر", "MCQE.CA": "أسمنت قنا", "SVCE.CA": "جنوب الوادي للأسمنت",
    "MICH.CA": "مصر للكيماويات", "ANBK.CA": "الاسكندرية للأدوية", "EEII.CA": "المصرية للاستثمار",
    "AMER.CA": "عامر جروب", "NAPT.CA": "النصر للأعمال المدنية", "ORWE.CA": "النساجون الشرقيون"
}

# --- [2. محرك الاستراتيجية (21 يوم)] ---
def run_zara_engine(ticker, name):
    try:
        if ticker in EXCLUDE_LIST: return None
        
        # جلب البيانات (آخر 21 يوم تداول فعلي)
        df = yf.download(ticker, period="1mo", interval="1h", progress=False)
        if df.empty or len(df) < 21: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df_21 = df.tail(21 * 7) # تحليل آخر 21 يوم عمل

        curr = df_21['Close'].iloc[-1]
        h_max, l_min = df_21['High'].max(), df_21['Low'].min()
        
        # الاستراتيجية: الخصم + السيولة
        fib_618 = l_min + (h_max - l_min) * 0.618
        fvg = (df_21['Low'].iloc[-1] > df_21['High'].iloc[-3])
        
        stop = l_min * 0.985
        target = h_max
        rr = round((target - curr) / (curr - stop), 2) if (curr - stop) > 0 else 0

        # نظام التنقيط
        score = 0
        if curr <= fib_618: score += 40
        if rr >= 2: score += 30
        if fvg: score += 20
        if curr > df_21['Open'].iloc[-1]: score += 10

        return {
            "Symbol": ticker.split(".")[0],
            "Name": name,
            "Price": round(curr, 2),
            "Score": score,
            "RR": rr,
            "SMC": "✅" if fvg else "⚠️",
            "Target": round(target, 2),
            "Stop": round(stop, 2),
            "Fib": round(fib_618, 2)
        }
    except: return None

# --- [3. الواجهة الذكية] ---
st.title("🦅 منظومة زارا برو - الإصدار المصلح كلياً")

tab1, tab2 = st.tabs(["🚀 المسح الشامل والترتيب", "🔍 التحليل التفصيلي"])

with tab1:
    if st.button("🏁 ابدأ المسح (21 يوم)"):
        raw_results = []
        bar = st.progress(0)
        tickers = list(TICKER_DB.items())
        
        for idx, (sym, name) in enumerate(tickers):
            res = run_zara_engine(sym, name)
            if res: raw_results.append(res)
            bar.progress((idx + 1) / len(tickers))
        
        # --- الفرز البرمجي الصارم (Pandas) ---
        if raw_results:
            full_df = pd.DataFrame(raw_results)
            # ترتيب تنازلي حسب القوة (Score)
            full_df = full_df.sort_values(by="Score", ascending=False).reset_index(drop=True)
            # إعادة بناء الترقيم من 1
            full_df.index += 1
            full_df.index.name = "الترتيب"
            
            st.subheader("📊 قائمة الـ 50 الأوائل (بدون تناقض)")
            st.table(full_df[["Symbol", "Name", "Score", "Price", "RR", "SMC"]].head(50))
        else:
            st.warning("لم يتم العثور على نتائج.")

with tab2:
    code = st.text_input("أدخل رمز السهم (مثال: ARCC):").upper().strip()
    if st.button("📊 إصدار تقرير خريطة الطريق"):
        res = run_zara_engine(f"{code}.CA", TICKER_DB.get(f"{code}.CA", "سهم خارج القائمة"))
        if res:
            st.markdown(f"### 🖋️ تقرير: {res['Symbol']} ({res['Name']})")
            c1, c2, c3 = st.columns(3)
            c1.metric("السعر", res['Price'])
            c2.metric("المستهدف الرئيسي", res['Target'])
            c3.metric("وقف الخسارة", res['Stop'])
            st.success(f"قوة الاستراتيجية: {res['Score']}% | RR: 1:{res['RR']} | المنطقة الذهبية: تحت {res['Fib']}")
