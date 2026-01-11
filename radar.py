import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- [1. إعدادات المنظومة] ---
st.set_page_config(page_title="Zara AI - EGX 200 Pro", layout="wide")

# القائمة الكاملة (تم وضع أهم 50 سهم كمثال، ويمكنك نسخ باقي الـ 200 في هذه القائمة)
EGX_FULL_LIST = [
    "CIEB.CA", "ADIB.CA", "FWRY.CA", "SWDY.CA", "PHDC.CA", "TMGH.CA", "COMI.CA", "ABUK.CA", "MFPC.CA", "LCSW.CA",
    "ETEL.CA", "AMOC.CA", "JUFO.CA", "HELI.CA", "MNHD.CA", "SKPC.CA", "CCAP.CA", "EGAL.CA", "EMFD.CA", "GBCO.CA",
    "ISPH.CA", "RMDA.CA", "TAQA.CA", "RAYA.CA", "ASCM.CA", "EKHO.CA", "ESRS.CA", "ORAS.CA", "CANA.CA", "BTEL.CA",
    "DOMT.CA", "BTEL.CA", "UNIT.CA", "DESC.CA", "MICH.CA", "ALCN.CA", "AJWA.CA", "AFMC.CA", "ATQA.CA", "DAPH.CA"
]

# --- [2. محرك التحليل الموحد (SMC Engine)] ---
def run_zara_engine(ticker):
    try:
        # جلب بيانات الساعة لآخر 20 يوم (الفريم الأمثل للمضاربة)
        df = yf.download(ticker, period="20d", interval="1h", progress=False)
        if df.empty or len(df) < 5: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        current_price = df['Close'].iloc[-1]
        h_max, l_min = df['High'].max(), df['Low'].min()
        
        # 1. حساب منطقة الخصم (Discount Zone)
        fib_618 = l_min + (h_max - l_min) * 0.618
        
        # 2. بصمة المؤسسات (Bullish FVG)
        # فحص وجود فجوة سعرية إيجابية في آخر 3 شموع
        fvg = (df['Low'].iloc[-1] > df['High'].iloc[-3])
        
        # 3. حساب المخاطرة والعائد
        potential_profit = h_max - current_price
        potential_loss = current_price - (l_min * 0.98)
        rr_ratio = round(potential_profit / potential_loss, 2) if potential_loss > 0 else 0

        # 4. نظام التنقيط الاحترافي (Score)
        score = 0
        if current_price <= fib_618: score += 40  # جودة السعر
        if rr_ratio >= 2: score += 30             # جودة الربح
        if fvg: score += 20                       # سيولة مؤسسية
        if current_price > df['Close'].shift(1).iloc[-1]: score += 10 # زخم لحظي

        return {
            "symbol": ticker.split(".")[0],
            "price": round(current_price, 2),
            "score": score,
            "target": round(h_max, 2),
            "stop": round(l_min * 0.98, 2),
            "rr": rr_ratio,
            "fvg": fvg,
            "fib": round(fib_618, 2)
        }
    except: return None

# --- [3. واجهة المستخدم الرسومية] ---
st.title("🦅 منظومة زارا الذكية - إدارة وتحليل المضاربة")
st.write(f"التاريخ: **{pd.Timestamp.now().strftime('%Y-%m-%d')}** | الفريم: **ساعة واحدة (1H)**")

tab1, tab2 = st.tabs(["🎯 قناص النخبة (مسح 200 سهم)", "🔍 المحلل التفصيلي (خريطة الطريق)"])

# --- التبويب الأول: الماسح الجماعي ---
with tab1:
    st.subheader("أفضل 25 فرصة في السوق حالياً")
    if st.button("🚀 ابدأ المسح الشامل للبورصة المصرية"):
        results = []
        progress_bar = st.progress(0)
        status = st.empty()
        
        for idx, t in enumerate(EGX_FULL_LIST):
            status.text(f"جاري فحص: {t}")
            res = run_zara_engine(t)
            if res: results.append(res)
            progress_bar.progress((idx + 1) / len(EGX_FULL_LIST))
        
        status.text("تم اكتمال المسح!")
        
        # ترتيب النتائج من الأعلى نقاطاً للأقل
        top_25 = sorted(results, key=lambda x: x['score'], reverse=True)[:25]
        
        if top_25:
            df_final = pd.DataFrame([
                {
                    "الترتيب": i+1,
                    "السهم": r['symbol'],
                    "النقاط": r['score'],
                    "السعر الآن": r['price'],
                    "مخاطرة:عائد": f"1:{r['rr']}",
                    "بصمة SMC": "قوية ✅" if r['fvg'] else "محتملة ⚠️",
                    "الحالة": "دخول ذهبي 🚀" if r['score'] >= 85 else "تجميع 🔵"
                } for i, r in enumerate(top_25)
            ])
            st.table(df_final)
        else:
            st.warning("لا توجد أسهم تطابق الشروط حالياً.")

# --- التبويب الثاني: المحلل التفصيلي (طريقة كريدي أجريكول) ---
with tab2:
    st.subheader("استخراج تقرير خريطة الطريق")
    c_in, c_bt = st.columns([3, 1])
    with c_in:
        user_ticker = st.text_input("أدخل رمز السهم المراد تحليله (مثال: ADIB):", "").upper().strip()
    with c_bt:
        st.write(" ")
        analyze_btn = st.button("🔍 إنشاء التقرير التفصيلي")

    if analyze_btn and user_ticker:
        with st.spinner(f"جاري تحليل {user_ticker}..."):
            r = run_zara_engine(f"{user_ticker}.CA")
            
            if r:
                st.markdown(f"### 🖋️ تقرير خريطة الطريق: {r['symbol']}")
                st.write("---")
                
                # عرض المؤشرات الرئيسية
                col1, col2, col3 = st.columns(3)
                col1.metric("السعر الحالي", f"{r['price']} ج.م")
                col2.metric("المستهدف الرئيسي", f"{r['target']} ج.م")
                col3.metric("وقف الخسارة 🛡️", f"{r['stop']} ج.م")
                
                # تفاصيل SMC
                st.info(f"**بصمة السيولة (SMC):** {'إيجابية جداً ✅' if r['fvg'] else 'تحتاج تأكيد ⚠️'} | **منطقة الخصم:** تحت {r['fib']}")
                
                # التحليل النصي (بأسلوب كريدي أجريكول)
                quality = "احترافية عالية" if r['rr'] >= 2 else "متوسطة الجودة"
                st.success(f"""
                **القرار الفني من زارا AI:**
                * السهم يمتلك قوة تجميع رقمية قدرها **{r['score']}%**.
                * نسبة المخاطرة للعائد هي **1:{r['rr']}**، مما يجعل هذه الصفقة **{quality}**.
                * **الاستراتيجية:** يُنصح بتجميع المراكز في المنطقة السعرية الحالية، مع الالتزام التام بوقف الخسارة عند {r['stop']} لضمان حماية رأس المال.
                """)
            else:
                st.error("لم نتمكن من العثور على بيانات لهذا السهم، يرجى التأكد من الرمز.")
