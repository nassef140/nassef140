import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- [1. قاعدة بيانات الأسهم الشاملة] ---
TICKER_DB = {
    "CIEB.CA": "كريدي أجريكول", "LCSW.CA": "ليسكو مصر", "ABUK.CA": "أبو قير للأسمدة",
    "ADIB.CA": "مصرف أبوظبي الإسلامي", "FWRY.CA": "فوري", "SWDY.CA": "السويدي إليكتريك",
    "PHDC.CA": "بالم هيلز", "TMGH.CA": "طلعت مصطفى", "COMI.CA": "التجاري الدولي",
    "MFPC.CA": "موبكو للأسمدة", "ETEL.CA": "المصرية للاتصالات", "AMOC.CA": "أموك للزيوت",
    "HELI.CA": "مصر الجديدة", "MNHD.CA": "مدينة مصر", "SKPC.CA": "سيدي كرير",
    "CCAP.CA": "القلعة", "EGAL.CA": "مصر للألومنيوم", "EMFD.CA": "إعمار مصر",
    "GBCO.CA": "جي بي أوتو", "ISPH.CA": "ابن سينا فارما", "RMDA.CA": "راميدا",
    "TAQA.CA": "طاقة عربية", "RAYA.CA": "راية القابضة", "ASCM.CA": "أسيك للتعدين",
    "EKHO.CA": "القابضة الكويتية", "ESRS.CA": "عز الدخيلة", "ORAS.CA": "أوراسكوم للإنشاء"
    # القائمة تدعم حتى 200 سهم بنفس النمط
}

# --- [2. محرك التحليل الاحترافي] ---
def run_zara_engine(ticker, name):
    try:
        df = yf.download(ticker, period="30d", interval="1h", progress=False)
        if df.empty or len(df) < 10: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        curr = df['Close'].iloc[-1]
        h_max, l_min = df['High'].max(), df['Low'].min()
        
        # استراتيجية SMC & Fibonacci
        fib_618 = l_min + (h_max - l_min) * 0.618
        fvg_detected = (df['Low'].iloc[-1] > df['High'].iloc[-3])
        
        # الأهداف الاستراتيجية
        target_1 = curr + (h_max - curr) * 0.5
        target_2 = h_max
        target_3 = h_max * 1.15 # مستهدف امتداد
        stop_loss = l_min * 0.982
        
        rr_ratio = round((target_2 - curr) / (curr - stop_loss), 2) if (curr - stop_loss) > 0 else 0

        # نظام التنقيط
        score = 0
        if curr <= fib_618: score += 40
        if rr_ratio >= 2: score += 30
        if fvg_detected: score += 20
        if curr > df['Open'].iloc[-1]: score += 10

        return {
            "symbol": ticker.split(".")[0], "name": name, "price": round(curr, 2),
            "score": score, "target1": round(target_1, 2), "target2": round(target_2, 2),
            "target3": round(target_3, 2), "stop": round(stop_loss, 2),
            "rr": rr_ratio, "fvg": fvg_detected, "fib": round(fib_618, 2),
            "volatility": "عالية" if (h_max/l_min) > 1.1 else "مستقرة"
        }
    except: return None

# --- [3. الواجهة الرسومية الغنية بالمعلومات] ---
st.set_page_config(page_title="Zara AI - Pro Analysis", layout="wide")
st.title("🦅 منظومة زارا للتحليل الاستراتيجي | EGX 200")

t1, t2 = st.tabs(["🎯 قناص النخبة (ترتيب الأفضلية)", "🖋️ تقرير خريطة الطريق التفصيلي"])

with t1:
    st.subheader("أفضل 25 سهم متوافق مع الاستراتيجية")
    if st.button("🚀 بدء المسح الشامل والترتيب"):
        results = []
        bar = st.progress(0)
        items = list(TICKER_DB.items())
        for idx, (sym, name) in enumerate(items):
            res = run_zara_engine(sym, name)
            if res: results.append(res)
            bar.progress((idx + 1) / len(items))
        
        top_25 = sorted(results, key=lambda x: x['score'], reverse=True)[:25]
        if top_25:
            st.table(pd.DataFrame([{
                "الترتيب": i+1, "السهم": f"{r['symbol']} ({r['name']})", 
                "القوة": f"{r['score']}%", "السعر": r['price'], "م:ع": f"1:{r['rr']}",
                "الحالة": "دخول ذهبي 🚀" if r['score'] >= 85 else "تجميع 🔵"
            } for i, r in enumerate(top_25)]))

with t2:
    st.subheader("🔍 استخراج تقرير معمق للسهم")
    col_search, _ = st.columns([2, 2])
    with col_search:
        code = st.text_input("أدخل رمز السهم (مثال: LCSW):").upper().strip()
    
    if st.button("📊 إنشاء التقرير الغني") and code:
        res = run_zara_engine(f"{code}.CA", TICKER_DB.get(f"{code}.CA", "سهم مصري"))
        if res:
            st.markdown(f"## 🖋️ تقرير خريطة الطريق: {res['symbol']} ({res['name']})")
            st.markdown("---")
            
            # قسم 1: الأرقام الاستراتيجية
            st.markdown("### 1️⃣ الأرقام الاستراتيجية (بالقرش)")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("السعر الحالي", f"{res['price']} ج.م")
            c2.metric("المستهدف الأول", f"{res['target1']} ج.م")
            c3.metric("المستهدف الرئيسي", f"{res['target2']} ج.م")
            c4.metric("وقف الخسارة 🛡️", f"{res['stop']} ج.م")
            
            # قسم 2: بصمة السيولة
            st.markdown("### 2️⃣ بصمة السيولة والمؤسسات (SMC Insight)")
            fvg_status = "إيجابية جداً ✅ (دخول حيتان)" if res['fvg'] else "تحتاج تأكيد ⚠️ (سيولة أفراد)"
            st.info(f"""
            * **سلوك السيولة:** {fvg_status}
            * **منطقة الخصم (المنطقة الذهبية):** تحت مستويات **{res['fib']}**
            * **حالة التذبذب:** السهم في حالة حركة **{res['volatility']}**
            """)
            
            # قسم 3: تحليل زارا للقرار
            st.markdown("### 3️⃣ تحليل زارا للقرار (الخلاصة الاستراتيجية)")
            quality = "عالية الجودة (احترافية)" if res['rr'] >= 2 else "متوسطة الجودة"
            st.success(f"""
            * **قوة التجميع:** حصل السهم على تقييم **{res['score']}%** بناءً على الاستراتيجية.
            * **نسبة المخاطرة للعائد:** **1:{res['rr']}** (كل جنيه مخاطرة يقابله {res['rr']} جنيه ربح متوقع).
            * **الخلاصة:** السهم في منطقة {'مثالية للشراء' if res['score'] >= 80 else 'تحتاج مراقبة'} مع الالتزام التام بمستويات وقف الخسارة المذكورة أعلاه.
            """)
        else:
            st.error("الرمز غير موجود أو البيانات غير كافية.")
