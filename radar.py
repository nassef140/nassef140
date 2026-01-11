import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- [1. إعدادات المنظومة والفلترة] ---
st.set_page_config(page_title="Zara AI - EGX 70/100 Sniper", layout="wide")

# قائمة الاستبعاد التام (EGX 30) - لن يتم مسحها نهائياً
EGX30_EXCLUDE = [
    "COMI.CA", "FWRY.CA", "SWDY.CA", "TMGH.CA", "ABUK.CA", "MFPC.CA", "ETEL.CA", 
    "CIEB.CA", "ADIB.CA", "HRHO.CA", "BTEL.CA", "ESRS.CA", "IRAX.CA", "EKHO.CA", 
    "AMOC.CA", "SKPC.CA", "ORAS.CA", "EMFD.CA", "HELI.CA", "MNHD.CA", "PHDC.CA",
    "CANA.CA", "QNBA.CA", "SAUD.CA", "EXPA.CA", "EGBE.CA", "JUFO.CA", "ORWE.CA"
]

# قاموس أسهم الفرص (EGX 70 & 100) - قائمة غنية وشاملة
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
    "REAC.CA": "رياكت للأدوية", "BIOC.CA": "جلوبال تليكوم", "ALUM.CA": "العربية للألومنيوم"
    # القائمة تدعم إضافة حتى 200 سهم من خارج الـ 30
}

# --- [2. محرك التحليل الاحترافي (SMC Strategy)] ---
def zara_pro_analyzer(ticker, name):
    try:
        # استبعاد صارم قبل بدء الاتصال بالبيانات
        if ticker in EGX30_EXCLUDE:
            return None

        df = yf.download(ticker, period="30d", interval="1h", progress=False)
        if df.empty or len(df) < 10: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        curr = df['Close'].iloc[-1]
        h_max, l_min = df['High'].max(), df['Low'].min()
        
        # استراتيجية SMC & Fibonacci
        fib_618 = l_min + (h_max - l_min) * 0.618
        fvg = (df['Low'].iloc[-1] > df['High'].iloc[-3])
        
        # إدارة المخاطر (R/R)
        target = h_max
        stop_loss = l_min * 0.982
        rr_ratio = round((target - curr) / (curr - stop_loss), 2) if (curr - stop_loss) > 0 else 0

        # نظام التنقيط (Scoring) لضمان الترتيب الصحيح
        score = 0
        if curr <= fib_618: score += 40      # السعر في منطقة خصم
        if rr_ratio >= 2: score += 30         # مخاطرة لعائد ممتازة
        if fvg: score += 20                   # وجود سيولة مؤسسية
        if curr > df['Open'].iloc[-1]: score += 10 # زخم اللحظة الأخيرة

        return {
            "symbol": ticker.split(".")[0],
            "full_name": f"{ticker.split('.')[0]} ({name})",
            "score": score, "price": round(curr, 2), "target": round(target, 2),
            "stop": round(stop_loss, 2), "rr": rr_ratio, "fvg": fvg, "fib": round(fib_618, 2)
        }
    except: return None

# --- [3. الواجهة الرسومية] ---
st.title("🦅 رادار زارا الذكي: الـ 50 الأوائل (بدون EGX 30)")
st.markdown("---")

tab1, tab2 = st.tabs(["🎯 ماسح نخبة الـ 50 سهم", "🖋️ تقرير خريطة الطريق التفصيلي"])

with tab1:
    if st.button("🚀 ابدأ المسح الشامل لأسهم EGX 70/100"):
        results = []
        progress_bar = st.progress(0)
        items = list(TICKER_DB.items())
        
        for idx, (sym, name) in enumerate(items):
            res = zara_pro_analyzer(sym, name)
            if res: results.append(res)
            progress_bar.progress((idx + 1) / len(items))
        
        # الترتيب التنازلي الصارم لضمان ظهور ARCC وغيره في مكانهم الصحيح
        top_50 = sorted(results, key=lambda x: x['score'], reverse=True)[:50]
        
        if top_50:
            df_display = pd.DataFrame([
                {
                    "الترتيب": i+1,
                    "السهم": r['full_name'],
                    "قوة الاستراتيجية": f"{r['score']}%",
                    "السعر الآن": r['price'],
                    "مخاطرة : عائد": f"1 : {r['rr']}",
                    "بصمة SMC": "قوية ✅" if r['fvg'] else "محتملة ⚠️",
                    "الحالة": "دخول ذهبي 🚀" if r['score'] >= 85 else "مراقبة 🔵"
                } for i, r in enumerate(top_50)
            ])
            st.table(df_display)

with tab2:
    st.subheader("🖋️ تقرير خريطة الطريق (على نهج كريدي أجريكول)")
    search_ticker = st.text_input("أدخل رمز السهم (مثال: ARCC):").upper().strip()
    if st.button("🔍 عرض التقرير المعمق"):
        res = zara_pro_analyzer(f"{search_ticker}.CA", TICKER_DB.get(f"{search_ticker}.CA", "سهم خارج القائمة"))
        if res:
            st.markdown(f"## تقرير السهم: {res['full_name']}")
            col1, col2, col3 = st.columns(3)
            col1.metric("السعر الحالي", f"{res['price']} ج.م")
            col2.metric("المستهدف الرئيسي", f"{res['target']} ج.م")
            col3.metric("وقف الخسارة", f"{res['stop']} ج.م")
            
            st.info(f"بصمة السيولة (SMC): {'إيجابية ✅' if res['fvg'] else '⚠️'} | منطقة الخصم الذهبية: تحت {res['fib']}")
            
            st.success(f"""
            **تحليل زارا للقرار:**
            - حصل السهم على قوة تجميع **{res['score']}%**.
            - نسبة المخاطرة للعائد **1:{res['rr']}** تجعل الصفقة احترافية.
            - **التوصية:** تجميع في الأسعار الحالية طالما السهم يحافظ على مستوى {res['stop']}.
            """)
        else:
            st.error("السهم غير موجود أو ينتمي لقائمة EGX 30 المستبعدة.")
