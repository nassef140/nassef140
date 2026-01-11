import streamlit as st
import yfinance as yf
import pandas as pd

# --- [1. إعدادات المنظومة] ---
st.set_page_config(page_title="Zara Pro - Sniper 50", layout="wide")

# قائمة الاستبعاد التام (EGX 30)
EGX30_EXCLUDE = [
    "COMI.CA", "FWRY.CA", "SWDY.CA", "TMGH.CA", "ABUK.CA", "MFPC.CA", "ETEL.CA", 
    "CIEB.CA", "ADIB.CA", "HRHO.CA", "BTEL.CA", "ESRS.CA", "IRAX.CA", "EKHO.CA", 
    "AMOC.CA", "SKPC.CA", "ORAS.CA", "EMFD.CA", "HELI.CA", "MNHD.CA", "PHDC.CA"
]

# قاموس الأسهم (EGX 70 & 100) - يرجى التأكد من إضافة كافة الأسهم المستهدفة هنا
TICKER_DB = {
    "ARCC.CA": "العربية للأسمنت", "LCSW.CA": "ليسكو مصر", "ACGC.CA": "حليج الأقطان",
    "ASCM.CA": "أسيك للتعدين", "AJWA.CA": "أجواء", "AFMC.CA": "الاسكندرية للزيوت",
    "ATQA.CA": "مصر الوطنية للصلب", "DAPH.CA": "مطاحن وسط وغرب", "MPRC.CA": "مدينة الإنتاج الإعلامي",
    "UNIT.CA": "المتحدة للإسكان", "PORT.CA": "بورتو جروب", "ELSH.CA": "الشمس للإسكان",
    "RMDA.CA": "راميدا للأدوية", "ISPH.CA": "ابن سينا فارما", "EGAL.CA": "مصر للألومنيوم",
    "CCAP.CA": "القلعة", "RAYA.CA": "راية القابضة", "TAQA.CA": "طاقة عربية",
    "DOMT.CA": "دومتي", "OBRI.CA": "عبور لاند", "ALCN.CA": "الاسكندرية للحاويات"
}

# --- [2. محرك التحليل - تحديث لـ 21 يوم] ---
def zara_pro_engine(ticker, name):
    try:
        if ticker in EGX30_EXCLUDE: return None

        # المسح بناءً على آخر 21 يوم عمل كما طلبت
        df = yf.download(ticker, period="30d", interval="1h", progress=False)
        if df.empty or len(df) < 21: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # أخذ آخر 21 يوم فقط للتحليل
        df = df.tail(21 * 7) # تقريباً 7 ساعات تداول يومياً

        curr = df['Close'].iloc[-1]
        h_max, l_min = df['High'].max(), df['Low'].min()
        
        # الاستراتيجية
        fib_618 = l_min + (h_max - l_min) * 0.618
        fvg = (df['Low'].iloc[-1] > df['High'].iloc[-3])
        stop_loss = l_min * 0.985
        rr_ratio = round((h_max - curr) / (curr - stop_loss), 2) if (curr - stop_loss) > 0 else 0

        # نظام النقاط
        score = 0
        if curr <= fib_618: score += 40
        if rr_ratio >= 2: score += 30
        if fvg: score += 20
        if curr > df['Open'].iloc[-1]: score += 10

        return {
            "رمز السهم": ticker.split(".")[0],
            "الاسم": name,
            "قوة الاستراتيجية": score,
            "السعر": round(curr, 2),
            "مخاطرة:عائد": f"1:{rr_ratio}",
            "بصمة SMC": "قوية ✅" if fvg else "⚠️"
        }
    except: return None

# --- [3. واجهة العرض والترتيب المصلح] ---
st.title("🎯 قناص زارا: الـ 50 الأوائل (فرز دقيق - 21 يوم)")

if st.button("🚀 ابدأ المسح الشامل والترتيب"):
    all_data = []
    progress = st.progress(0)
    items = list(TICKER_DB.items())
    
    for idx, (sym, name) in enumerate(items):
        res = zara_pro_engine(sym, name)
        if res: all_data.append(res)
        progress.progress((idx + 1) / len(items))
    
    if all_data:
        # 1. تحويل للبيانات لجدول
        df_results = pd.DataFrame(all_data)
        
        # 2. الفرز التنازلي الصارم حسب القوة (Score)
        df_results = df_results.sort_values(by="قوة الاستراتيجية", ascending=False).reset_index(drop=True)
        
        # 3. إصلاح الترقيم ليبدأ من 1 لأعلى سهم نسبة
        df_results.insert(0, 'الترتيب', range(1, len(df_results) + 1))
        
        # 4. تحسين شكل العرض (إضافة علامة % للنسبة)
        df_results['قوة الاستراتيجية'] = df_results['قوة الاستراتيجية'].astype(str) + "%"
        
        st.subheader("📊 قائمة الأفضلية (مرتبة آلياً من 1 إلى 50)")
        st.table(df_results.head(50))
    else:
        st.error("لم يتم العثور على نتائج، تأكد من تحديث القائمة.")
