import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- [1. إعدادات الاستبعاد والقاموس] ---
# استبعاد أسهم EGX 30 تماماً لضمان التركيز على أسهم النمو (EGX 70/100)
EGX30_EXCLUDE = [
    "COMI.CA", "FWRY.CA", "SWDY.CA", "TMGH.CA", "ABUK.CA", "MFPC.CA", "ETEL.CA", 
    "CIEB.CA", "ADIB.CA", "HRHO.CA", "BTEL.CA", "ESRS.CA", "IRAX.CA", "EKHO.CA", 
    "AMOC.CA", "SKPC.CA", "ORAS.CA", "EMFD.CA", "HELI.CA", "MNHD.CA", "PHDC.CA"
]

# قاموس الأسهم المستهدفة (تم إعداد الهيكل لـ 200 سهم)
TICKER_DB = {
    "ARCC.CA": "العربية للأسمنت", "LCSW.CA": "ليسكو مصر", "ACGC.CA": "حليج الأقطان",
    "ASCM.CA": "أسيك للتعدين", "AJWA.CA": "أجواء", "AFMC.CA": "الاسكندرية للزيوت",
    "ATQA.CA": "مصر الوطنية للصلب", "DAPH.CA": "مطاحن وسط وغرب", "MPRC.CA": "مدينة الإنتاج الإعلامي",
    "UNIT.CA": "المتحدة للإسكان", "PORT.CA": "بورتو جروب", "ELSH.CA": "الشمس للإسكان",
    "RMDA.CA": "راميدا للأدوية", "ISPH.CA": "ابن سينا فارما", "EGAL.CA": "مصر للألومنيوم",
    "CCAP.CA": "القلعة", "RAYA.CA": "راية القابضة", "TAQA.CA": "طاقة عربية",
    "DOMT.CA": "دومتي", "OBRI.CA": "عبور لاند", "ALCN.CA": "الاسكندرية للحاويات",
    "DSMC.CA": "الدلتا للسكر", "MCQE.CA": "أسمنت قنا", "SVCE.CA": "جنوب الوادي للأسمنت",
    "MICH.CA": "مصر للكيماويات", "ANBK.CA": "الاسكندرية للأدوية", "EEII.CA": "المصرية للاستثمار"
}

# --- [2. محرك الاستراتيجية المتكامل (21 يوم)] ---
def zara_strategy_engine(ticker, name):
    try:
        if ticker in EGX30_EXCLUDE: return None
        
        # جلب بيانات كافية لتغطية 21 يوم تداول بدقة
        df = yf.download(ticker, period="40d", interval="1h", progress=False)
        if df.empty or len(df) < 21: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # حصر التحليل في آخر 21 يوم عمل (الاستراتيجية المتفق عليها)
        df_21 = df.tail(21 * 7) 

        curr = df_21['Close'].iloc[-1]
        h_max, l_min = df_21['High'].max(), df_21['Low'].min()
        
        # 1. حساب منطقة الخصم (Discount Zone)
        fib_618 = l_min + (h_max - l_min) * 0.618
        
        # 2. رصد بصمة السيولة (Fair Value Gap - FVG)
        # مقارنة السعر الحالي بالفجوات السعرية في آخر 3 شموع
        fvg = (df_21['Low'].iloc[-1] > df_21['High'].iloc[-3])
        
        # 3. إدارة المخاطر والأهداف
        stop_loss = l_min * 0.985 # وقف خسارة 1.5% تحت القاع
        target_main = h_max
        rr_ratio = round((target_main - curr) / (curr - stop_loss), 2) if (curr - stop_loss) > 0 else 0

        # 4. نظام التنقيط (Scoring System)
        score = 0
        if curr <= fib_618: score += 40      # السعر رخيص (Discount)
        if rr_ratio >= 2: score += 30         # عائد مجزي جداً
        if fvg: score += 20                   # سيولة مؤسسية مكتشفة
        if curr > df_21['Open'].iloc[-1]: score += 10 # زخم إيجابي

        return {
            "symbol": ticker.split(".")[0], "name": name, "price": round(curr, 2),
            "score": score, "t1": round(curr + (h_max - curr) * 0.5, 2), 
            "t2": round(h_max, 2), "t3": round(h_max * 1.15, 2),
            "stop": round(stop_loss, 2), "rr": rr_ratio, "fvg": fvg, "fib": round(fib_618, 2)
        }
    except: return None

# --- [3. الواجهة الاحترافية والتقارير] ---
st.set_page_config(page_title="Zara AI - Pro Version", layout="wide")
st.title("🦅 منظومة زارا الاحترافية | الإصدار النهائي الكامل")

tab1, tab2 = st.tabs(["🚀 ماسح الـ 50 الأقوى (EGX 70/100)", "🔍 المحلل الاستراتيجي (التقرير الغني)"])

with tab1:
    if st.button("🏁 تشغيل المسح الشامل والترتيب (بناءً على 21 يوم)"):
        results = []
        bar = st.progress(0)
        items_list = list(TICKER_DB.items())
        
        for idx, (sym, name) in enumerate(items_list):
            res = zara_strategy_engine(sym, name)
            if res: results.append(res)
            bar.progress((idx + 1) / len(items_list))
        
        # الترتيب الصارم: الأعلى نسبة يأخذ رقم 1
        sorted_data = sorted(results, key=lambda x: x['score'], reverse=True)[:50]
        
        if sorted_data:
            final_df = pd.DataFrame([
                {
                    "الترتيب": i+1,
                    "السهم": f"{r['symbol']} ({r['name']})",
                    "قوة الاستراتيجية": f"{r['score']}%",
                    "السعر": r['price'],
                    "مخاطرة:عائد": f"1:{r['rr']}",
                    "بصمة SMC": "مكتشفة ✅" if r['fvg'] else "⚠️",
                    "الحالة": "دخول ذهبي 🚀" if r['score'] >= 80 else "مراقبة 🔵"
                } for i, r in enumerate(sorted_data)
            ])
            st.table(final_df)

with tab2:
    st.subheader("🖋️ تقرير خريطة الطريق (التحليل الاستراتيجي)")
    user_ticker = st.text_input("أدخل رمز السهم للتحليل المعمق (مثال: ARCC):").upper().strip()
    
    if st.button("📊 إصدار التقرير الكامل") and user_ticker:
        full_sym = f"{user_ticker}.CA"
        res = zara_strategy_engine(full_sym, TICKER_DB.get(full_sym, "سهم من القائمة"))
        
        if res:
            st.markdown(f"## 📽️ تقرير خريطة الطريق: {res['symbol']} ({res['name']})")
            st.write("---")
            # مستويات السعر
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("السعر الحالي", f"{res['price']} ج.م")
            c2.metric("المستهدف مضاربي", f"{res['t1']} ج.م")
            c3.metric("المستهدف الرئيسي", f"{res['t2']} ج.م")
            c4.metric("وقف الخسارة 🛡️", f"{res['stop']} ج.م")
            
            # تفاصيل الاستراتيجية
            st.info(f"""
            * **بصمة السيولة والمؤسسات:** {'رصد سيولة ذكية قوية ✅' if res['fvg'] else 'تجميع هادئ ⚠️'}
            * **منطقة الخصم الذهبية:** السهم في وضعية شراء مثالية تحت **{res['fib']}**
            * **المستهدف الاستثماري (البعيد):** في حال استمرار الزخم يستهدف مستوى **{res['t3']}**
            """)
            
            # القرار النهائي
            st.success(f"""
            **الخلاصة الفنية:**
            السهم حصل على **{res['score']}%** توافق مع استراتيجية زارا. نسبة الربح المتوقع للمخاطرة هي **1:{res['rr']}**. 
            القرار: يُنصح بالتجميع طالما السعر أعلى من {res['stop']}.
            """)
        else:
            st.error("السهم غير موجود أو مستبعد من المسح.")
